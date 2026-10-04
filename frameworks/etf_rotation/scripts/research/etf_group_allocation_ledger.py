#!/usr/bin/env python3
"""Allocation study with a real daily holdings ledger (rewrite after GPT-6-Sol review, 2026-09-24).

Holdings drift with returns between 20-session rebalances; costs are charged on the value
actually traded at each rebalance (one-way 20 bp A-share, 50 bp QDII-heavy groups); weights
decided at close D, traded at close D+1. Cash earns 2%/yr.
Variants: EW8; IVOL (inverse 60d vol); IVOL windows 20/120/250; ERC (equal risk
contribution with 120d covariance); IVOL_EX3 (IVOL without gold, dividend_low_vol,
electric_power); EW8_CASH_MATCH (EW8 scaled to IVOL's trailing-60d realized vol, rest cash);
FIXED_LOWVOL (constant weights = full-period average IVOL weights; hindsight, reference only).
Outputs segment stats, yearly returns, paired monthly excess vs EW8 with 95% block-bootstrap
interval, Sharpe-difference bootstrap, and per-group return contribution.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import etf_group_regime_longhistory as base

OUT = ROOT / 'runtime_outputs/etf_rotation_research/allocation_ledger_20260924'
CASH = 0.02 / 252; STEP = 20
COST = pd.Series(base.COST)


def erc(cov, iters=200):
    n = len(cov); w = np.ones(n) / n
    for _ in range(iters):
        rc = w * (cov @ w); w = w * (rc.mean() / np.maximum(rc, 1e-12)) ** 0.5; w /= w.sum()
    return w


def target(g, kind, i):
    r = g.iloc[:i + 1]
    if kind == 'EW8': return pd.Series(1 / 8, index=g.columns)
    if kind.startswith('IVOL'):
        win = {'IVOL': 60, 'IVOL20': 20, 'IVOL120': 120, 'IVOL250': 250, 'IVOL_EX3': 60}[kind]
        v = r.tail(win).std(); cols = g.columns
        if kind == 'IVOL_EX3': cols = [c for c in cols if c not in ('gold', 'dividend_low_vol', 'electric_power')]
        iv = 1 / v[cols]; w = pd.Series(0.0, index=g.columns); w[cols] = iv / iv.sum(); return w
    if kind == 'ERC':
        c = r.tail(120).cov().values; return pd.Series(erc(c), index=g.columns)
    if kind == 'EW8_CASH_MATCH':
        ew = r.tail(60).mean(axis=1).std(); iv = target(g, 'IVOL', i); ivv = (r.tail(60) @ iv).std()
        return pd.Series(min(1.0, ivv / ew) / 8, index=g.columns)
    raise ValueError(kind)


def ledger(g, kind, fixed=None):
    idx = g.index; n = len(idx); w = pd.Series(0.0, index=g.columns); cash = 1.0
    nav = np.empty(n); nav[0] = 1.0; pending = None; contrib = pd.DataFrame(0.0, index=idx, columns=g.columns); turn = 0.0
    start = 250
    for t in range(1, n):
        # apply today's returns to yesterday's holdings (weights are value fractions of NAV)
        grow = w * (1 + g.iloc[t]); c = cash * (1 + CASH); tot = grow.sum() + c
        contrib.iloc[t] = (w * g.iloc[t]).values
        nav[t] = nav[t - 1] * tot; w = grow / tot; cash = c / tot
        if pending is not None:                     # trade at today's close
            tgt = pending; trade = (tgt - w).abs(); cost = float((trade * COST).sum()); turn += float(trade.sum())
            nav[t] *= (1 - cost); w = tgt.copy(); cash = 1 - tgt.sum(); pending = None
        if t >= start and (t - start) % STEP == 0:
            pending = fixed if fixed is not None else target(g, kind, t)
    s = pd.Series(nav, index=idx).pct_change().fillna(0)
    return s.iloc[start:], contrib.iloc[start:], turn / ((n - start) / 252)


def stats(r, a, b):
    x = r.loc[a:b]; navx = (1 + x).cumprod(); yrs = len(x) / 252
    ann = navx.iloc[-1] ** (1 / yrs) - 1; vol = x.std() * np.sqrt(252)
    return dict(ann=round(float(ann), 4), vol=round(float(vol), 4), sharpe=round(float((ann - .02) / vol), 3), maxdd=round(float((navx / navx.cummax() - 1).min()), 4))


def main():
    g = base.build(); res = {}; rets = {}
    kinds = ['EW8', 'IVOL', 'IVOL20', 'IVOL120', 'IVOL250', 'ERC', 'IVOL_EX3', 'EW8_CASH_MATCH']
    for k in kinds:
        r, con, turn = ledger(g, k); rets[k] = r
        res[k] = dict(turnover_per_yr=round(turn, 2), s2016_2024=stats(r, '2016-01-01', '2024-12-31'), s2025_cold=stats(r, '2025-01-01', base.COLD),
                      contrib_2016_2024_ann={c: round(float(con.loc['2016':'2024', c].sum() / 9), 4) for c in g.columns})
    # hindsight constant weights (reference only)
    ivw = pd.concat([target(g, 'IVOL', i) for i in range(250, len(g), STEP)], axis=1).mean(axis=1)
    r, _, turn = ledger(g, 'FIXED', fixed=ivw); rets['FIXED_LOWVOL'] = r
    res['FIXED_LOWVOL'] = dict(weights=ivw.round(3).to_dict(), s2016_2024=stats(r, '2016-01-01', '2024-12-31'), s2025_cold=stats(r, '2025-01-01', base.COLD), note='hindsight weights, reference only')
    rng = np.random.default_rng(0); pair = {}
    for k in [k for k in rets if k != 'EW8']:
        d = (rets[k] - rets['EW8']).loc['2016-01-01':'2024-12-31']; m = d.groupby(d.index.to_period('M')).sum().values
        boots = [m[rng.integers(0, len(m) - 3, len(m) // 3)[:, None] + np.arange(3)].mean() for _ in range(2000)]
        x = pd.concat([rets[k], rets['EW8']], axis=1).loc['2016':'2024'].values; T = len(x); sd = []
        for _ in range(1000):
            ii = np.concatenate([np.arange(s, s + 20) for s in rng.integers(0, T - 20, T // 20)]); y = x[ii]
            sh = (y.mean(0) * 252 - .02) / (y.std(0) * np.sqrt(252)); sd.append(sh[0] - sh[1])
        pair[k] = dict(monthly_excess_bp=round(float(m.mean() * 1e4), 1), ci95_bp=[round(float(np.percentile(boots, 2.5) * 1e4), 1), round(float(np.percentile(boots, 97.5) * 1e4), 1)],
                       sharpe_diff=round(float(np.mean(sd)), 3), p_sharpe_diff_gt0=round(float((np.array(sd) > 0).mean()), 3))
    res['paired_vs_EW8_2016_2024'] = pair
    res['yearly'] = {k: {int(y): round(float(v), 4) for y, v in (1 + r).groupby(r.index.year).prod().sub(1).items()} for k, r in rets.items()}
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    for k in list(rets):
        v = res[k]; print(f"{k:15s} 16-24 {v['s2016_2024']} | 25-cold {v['s2025_cold']} | turn {v.get('turnover_per_yr')}")
    for k, v in pair.items(): print('pair', k, v)


if __name__ == '__main__':
    main()
