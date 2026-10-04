#!/usr/bin/env python3
"""Valuation (value/carry) across the A-share groups, 2012..cold line (2026-03-24).

Pre-registered: group earnings yield EY = sum_i w_i / pe_ttm_i (loss makers enter with
negative yield; pe_ttm missing -> excluded, weights renormalised), dividend yield DY =
sum_i w_i * dv_ttm, weights = latest index_weight on or before the month end. Groups:
cn_technology_manufacturing = mean over its 5 indices; innovative_pharma = 931152 (A-share
leg); metals 000819; dividend_low_vol H30269; electric_power H30199.
Signals (direction +): V1 = percentile of EY within the group's own trailing 60 months
(min 36); V2 = same for DY. Target: next 6 / 12 month group return (proxy indices) minus the
mean of the 5 A-share groups; monthly samples, rank IC pooled over groups and time-series
per group, Newey-West lag = horizon months. Portfolio: IVOL60 over 8 groups with the 5
A-share weights tilted by (1 + 0.25 * score), score = V1 rank among the 5 mapped to
[-1, 1], renormalised; drift ledger; paired monthly excess vs IVOL with block bootstrap.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import etf_group_regime_longhistory as base, etf_group_allocation_ledger as al

V = ROOT / 'runtime_outputs/etf_rotation_research/valuation'
OUT = ROOT / 'runtime_outputs/etf_rotation_research/valuation_test_20260924'
GROUPS = {'cn_technology_manufacturing': ['H30184.CSI', '931160.CSI', '930601.CSI', 'H30590.CSI', '931494.CSI'],
          'innovative_pharma': ['931152.CSI'], 'metals_equity': ['000819.SH'], 'dividend_low_vol': ['H30269.CSI'], 'electric_power': ['H30199.CSI']}


def valuation_panel():
    db = {pd.Timestamp(f.stem): pd.read_parquet(f).set_index('ts_code') for f in sorted((V / 'daily_basic').glob('*.parquet'))}
    months = sorted(db)
    rows = {}
    for g, codes in GROUPS.items():
        ey_i, dy_i = [], []
        for code in codes:
            wf = V / 'index_weight' / f'{code}.parquet'
            if not wf.exists(): continue
            w = pd.read_parquet(wf); w['trade_date'] = pd.to_datetime(w.trade_date)
            dates = sorted(w.trade_date.unique()); e, dv = {}, {}
            for m in months:
                past = [d for d in dates if d <= m]
                if not past: continue
                ww = w[w.trade_date == past[-1]].set_index('con_code')['weight']; b = db[m].reindex(ww.index)
                ok = b.pe_ttm.notna(); wv = ww[ok] / ww[ok].sum()
                e[m] = float((wv / b.pe_ttm[ok]).sum()); dd = b.dv_ttm.fillna(0); dv[m] = float((ww / ww.sum() * dd).sum() / 100)
            ey_i.append(pd.Series(e)); dy_i.append(pd.Series(dv))
        if ey_i:
            rows[(g, 'EY')] = pd.concat(ey_i, axis=1).mean(axis=1); rows[(g, 'DY')] = pd.concat(dy_i, axis=1).mean(axis=1)
    return pd.DataFrame(rows)


def pct_own(s, win=60, minp=36):
    return s.rolling(win, min_periods=minp).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)


def nw_t(x, lag):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n < 12: return np.nan
    xc = x - x.mean(); s = xc @ xc / n
    for j in range(1, lag + 1): s += 2 * (1 - j / (lag + 1)) * (xc[j:] @ xc[:-j] / n)
    return x.mean() / np.sqrt(s / n)


def main():
    val = valuation_panel(); g = base.build()
    ga = g[list(GROUPS)]; lvl = (1 + ga).cumprod()
    mlev = lvl.resample('ME').last()
    V1 = pd.DataFrame({k: pct_own(val[(k, 'EY')]) for k in GROUPS if (k, 'EY') in val}); V2 = pd.DataFrame({k: pct_own(val[(k, 'DY')]) for k in GROUPS if (k, 'DY') in val})
    V1.index = V1.index.to_period('M').to_timestamp('M'); V2.index = V2.index.to_period('M').to_timestamp('M')
    res = {'coverage': {k: str(val[(k, 'EY')].dropna().index.min().date()) for k in GROUPS if (k, 'EY') in val}}
    for H in (6, 12):
        fwd = mlev.shift(-H) / mlev - 1; rel = fwd.sub(fwd.mean(axis=1), axis=0)
        for name, S in (('V1_EY_own_pct', V1), ('V2_DY_own_pct', V2)):
            for seg, a, b in (('2016_2024', '2016-01-01', '2024-12-31'), ('2025_cold', '2025-01-01', base.COLD)):
                s = S.loc[a:b]; r = rel.reindex(s.index)
                ics = [s.loc[t].rank().corr(r.loc[t].rank()) for t in s.index if s.loc[t].notna().sum() >= 4 and r.loc[t].notna().sum() >= 4]
                pooled = pd.concat([s.stack(), r.stack()], axis=1).dropna()
                ts_ = {k: round(float(s[k].corr(r[k], method='spearman')), 3) for k in s.columns}
                res.setdefault(f'H{H}', {}).setdefault(name, {})[seg] = dict(xs_ic=round(float(np.nanmean(ics)), 3) if ics else None, xs_t=round(float(nw_t(ics, H)), 2) if ics else None,
                                                                            n_months=len(ics), per_group_ts_corr=ts_)
    # portfolio tilt on IVOL
    V1d = V1.reindex(g.index, method='ffill').shift(1)   # month-end valuation usable next session
    orig = al.target
    def tilt(gg, kind, i):
        w = orig(gg, 'IVOL', i)
        if kind != 'VTILT': return orig(gg, kind, i)
        s = V1d.iloc[i]
        if s.notna().sum() < 5: return w
        sc = (s.rank() - 1) / (len(s) - 1) * 2 - 1
        w = w.copy(); w[sc.index] = w[sc.index] * (1 + 0.25 * sc); return w / w.sum()
    al.target = tilt
    r_t, con_t, turn_t = al.ledger(g, 'VTILT'); r_i, _, turn_i = al.ledger(g, 'IVOL'); al.target = orig
    port = {}
    for seg, a, b in (('2016_2024', '2016-01-01', '2024-12-31'), ('2025_cold', '2025-01-01', base.COLD)):
        d = (r_t - r_i).loc[a:b]; m = d.groupby(d.index.to_period('M')).sum().values
        rng = np.random.default_rng(0); bo = [m[rng.integers(0, len(m) - 3, len(m) // 3)[:, None] + np.arange(3)].mean() for _ in range(2000)]
        port[seg] = dict(tilt=al.stats(r_t, a, b), ivol=al.stats(r_i, a, b), monthly_excess_bp=round(float(m.mean() * 1e4), 1),
                         ci95_bp=[round(float(np.percentile(bo, 2.5) * 1e4), 1), round(float(np.percentile(bo, 97.5) * 1e4), 1)], months=len(m))
    res['portfolio_V1_tilt_vs_IVOL'] = port; res['turnover'] = dict(tilt=round(turn_t, 2), ivol=round(turn_i, 2))
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str)[:4000])


if __name__ == '__main__':
    main()
