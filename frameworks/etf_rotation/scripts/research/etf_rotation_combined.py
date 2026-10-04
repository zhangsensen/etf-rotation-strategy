#!/usr/bin/env python3
"""Combined ETF rotation for a 1m CNY long-only account (2026-09-24).

Layer 1: inverse 60d-vol weights across the 8 groups, 20-session rebalance, costs 20/50 bp
(etf_group_allocation_longhistory.py). Layer 2: in us_large_growth and hk_technology, hold
the lowest-premium ETF of the same index instead of the pool ETF (qdii_premium_rotation.py,
THETA 1%); its daily excess over the pool ETF is added with the layer-1 weight of that group.
Compared with EW8 buy-and-rebalance. Proxies before 2021-08 carry no overlay.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import etf_group_regime_longhistory as base, etf_group_allocation_longhistory as al, qdii_premium_rotation as qp

OUT = ROOT / 'runtime_outputs/etf_rotation_research/combined_20260924'


def overlay_excess(index, bench):
    qp.THETA = 0.01
    close, adjc, amt = qp.prices(pd.read_csv(qp.Q / 'universe.csv').query('idx == @index').ts_code.tolist())
    res, sw = qp.run(index, bench)
    # rebuild daily strategy returns to get excess series
    return res


def main():
    g = base.build(); r_ew, _ = al.backtest(g, 'EW8'); r_iv, _ = al.backtest(g, 'IVOL')
    w = al.weights(g, 'IVOL')
    held_w = w.where(pd.Series(np.arange(len(g)) % 20 == 0, index=g.index), np.nan).ffill().shift(1).fillna(0)
    out = {}
    ex = {}
    for idx, bench, grp in (('NDX', '513100.SH', 'us_large_growth'), ('HST', '513130.SH', 'hk_technology')):
        qp.THETA = 0.01
        res, _ = qp.run(idx, bench)
        y = pd.Series(res['yearly']['strat']) - pd.Series(res['yearly']['bench'])
        ex[grp] = y
    # annual overlay contribution = group weight (mean over year) x yearly excess
    yrs = sorted(set(r_iv.index.year))
    wy = held_w.groupby(held_w.index.year).mean()
    rows = []
    for yv in yrs:
        seg = lambda r: float((1 + r[r.index.year == yv]).prod() - 1)
        add = sum(float(wy.loc[yv, grp]) * float(ex[grp].get(yv, 0.0)) for grp in ex) if yv in wy.index else 0.0
        rows.append(dict(year=yv, EW8=round(seg(r_ew), 3), IVOL=round(seg(r_iv), 3), overlay_add=round(add, 4), COMBINED=round(seg(r_iv) + add, 3)))
    df = pd.DataFrame(rows).set_index('year')
    out['yearly'] = df.to_dict(orient='index')
    for seg, a, b in (('2016_2024', 2016, 2024), ('2025_2026', 2025, 2026)):
        d = df.loc[a:b]; n = len(d)
        out[seg] = {k: round(float((1 + d[k]).prod() ** (1 / n) - 1), 3) for k in ('EW8', 'IVOL', 'COMBINED')}
    out['risk_2016_cold'] = {'EW8': al.stats(r_ew, '2016-01-01', base.COLD, r_ew * 0), 'IVOL': al.stats(r_iv, '2016-01-01', base.COLD, r_iv * 0)}
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'results.json').write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    print(df.to_string()); print({k: v for k, v in out.items() if k != 'yearly'})


if __name__ == '__main__':
    main()
