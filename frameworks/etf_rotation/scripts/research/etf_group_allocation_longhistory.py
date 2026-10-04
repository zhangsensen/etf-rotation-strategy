#!/usr/bin/env python3
"""Allocation-side value on the 8 groups, 2015-01..cold line (2026-03-24).

Pre-registered variants, monthly (20-session) rebalance, one-session lag, costs 20/50 bp
on weight changes, cash earns 2%/yr when not invested:
  EW8     equal weight 8 groups (baseline)
  IVOL    inverse 60d-volatility weights (risk parity without correlations)
  TREND   each group held at 1/8 if its price > its 200-session average, else that 1/8 in cash
          (time-series momentum per asset; this is timing, reported as such)
  IVOL_TREND  inverse-vol weights among groups in uptrend, remaining weight in cash
Reported per segment: annual return, vol, Sharpe (rf 2%), max drawdown, turnover.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import etf_group_regime_longhistory as base

OUT = ROOT / 'runtime_outputs/etf_rotation_research/allocation_longhistory_20260924'
CASH = 0.02 / 252


def weights(g, kind):
    lvl = (1 + g).cumprod(); vol = g.rolling(60).std(); up = lvl > lvl.rolling(200).mean()
    if kind == 'EW8': w = pd.DataFrame(1 / 8, index=g.index, columns=g.columns)
    elif kind == 'IVOL': iv = 1 / vol; w = iv.div(iv.sum(axis=1), axis=0)
    elif kind == 'TREND': w = up.astype(float) / 8
    elif kind == 'IVOL_TREND':
        iv = (1 / vol).where(up, 0.0); tot = (1 / vol).sum(axis=1); w = iv.div(tot, axis=0)
    return w


def backtest(g, kind):
    w = weights(g, kind); cost = pd.Series(base.COST)
    reb = np.zeros(len(g), bool); reb[::20] = True
    held = w.where(pd.Series(reb, index=g.index), np.nan).ffill().shift(1).fillna(0)   # signal at close, hold from next session
    # drift between rebalances ignored for weights (approx), costs on rebalance changes
    chg = held.diff().abs().sum(axis=1).fillna(0)
    tc = (held.diff().abs() * cost).sum(axis=1).fillna(0)
    r = (held * g).sum(axis=1) + (1 - held.sum(axis=1)) * CASH - tc
    return r, chg


def stats(r, a, b, turn):
    x = r.loc[a:b]; nav = (1 + x).cumprod(); yrs = len(x) / 252
    ann = nav.iloc[-1] ** (1 / yrs) - 1; vol = x.std() * np.sqrt(252)
    return dict(ann=round(ann, 3), vol=round(vol, 3), sharpe=round((ann - 0.02) / vol, 2), maxdd=round(float((nav / nav.cummax() - 1).min()), 3),
                turnover_yr=round(float(turn.loc[a:b].sum() / yrs), 2))


def main():
    g = base.build(); res = {}
    for kind in ('EW8', 'IVOL', 'TREND', 'IVOL_TREND'):
        r, t = backtest(g, kind)
        res[kind] = {seg: stats(r, a, b, t) for seg, a, b in (('2016_2024', '2016-01-01', '2024-12-31'), ('2025_cold', '2025-01-01', base.COLD), ('all', '2016-01-01', base.COLD))}
    yearly = {}
    for kind in ('EW8', 'IVOL', 'TREND', 'IVOL_TREND'):
        r, _ = backtest(g, kind); yearly[kind] = (1 + r.loc['2016':]).groupby(r.loc['2016':].index.year).prod().sub(1).round(3).to_dict()
    res['yearly'] = yearly
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    for k in ('EW8', 'IVOL', 'TREND', 'IVOL_TREND'):
        print(k, res[k])
    print(pd.DataFrame(yearly).to_string())


if __name__ == '__main__':
    main()
