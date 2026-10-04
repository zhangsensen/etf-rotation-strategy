#!/usr/bin/env python3
"""Hypothesis from GPT-6-Sol round 2 (2026-09-24): does beta_asymmetry_60 add net value on top of IVOL60?

Frozen before computing: every 20 sessions at close D, beta_asym_g = beta(r_g | r_m<0, 60d) -
beta(r_g | r_m>0, 60d), r_m = equal-weight of the 8 groups; frozen direction -1 (lower
downside asymmetry preferred). Cross-sectional rank mapped linearly to [-1, +1] (best = +1).
Weight = IVOL60 * (1 + 0.25 * score), renormalised to 100% long. Same daily drift ledger,
D+1 close trade, costs as etf_group_allocation_ledger. Comparison: paired monthly excess
over IVOL60 on the same dates. Historical run = feasibility diagnostic only (the factor was
found on 2025+ ETF data; proxies 2016-2024 are profile); the gate is 24 forward months with
block-bootstrap 95% lower bound > 0 and no single group contributing more than half.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import etf_group_regime_longhistory as base, etf_group_allocation_ledger as al

OUT = ROOT / 'runtime_outputs/etf_rotation_research/ivol_betatilt_20260924'
TILT = 0.25


def beta_asym(r, w=60):
    x = r.tail(w); m = x.mean(axis=1); dn, up = m < 0, m > 0
    def beta(mask):
        mm = m[mask]; return x[mask].apply(lambda s: np.cov(s, mm)[0, 1] / np.var(mm, ddof=1) if mask.sum() >= 15 else np.nan)
    return beta(dn) - beta(up)


def target_tilt(g, i):
    base_w = al.target(g, 'IVOL', i); ba = beta_asym(g.iloc[:i + 1])
    if ba.isna().any(): return base_w
    rank = (-ba).rank(); score = (rank - 1) / (len(rank) - 1) * 2 - 1
    w = base_w * (1 + TILT * score); return w / w.sum()


def main():
    g = base.build()
    orig = al.target
    al.target = lambda gg, kind, i: target_tilt(gg, i) if kind == 'TILT' else orig(gg, kind, i)
    r_t, con_t, turn_t = al.ledger(g, 'TILT'); r_i, con_i, turn_i = al.ledger(g, 'IVOL')
    al.target = orig
    res = {}
    for seg, a, b in (('profile_2016_2024', '2016-01-01', '2024-12-31'), ('2025_cold', '2025-01-01', base.COLD)):
        d = (r_t - r_i).loc[a:b]; m = d.groupby(d.index.to_period('M')).sum().values
        rng = np.random.default_rng(0); boots = [m[rng.integers(0, len(m) - 3, len(m) // 3)[:, None] + np.arange(3)].mean() for _ in range(2000)]
        gc = (con_t - con_i).loc[a:b].sum(); share = float(gc.abs().max() / gc.abs().sum()) if gc.abs().sum() > 0 else np.nan
        res[seg] = dict(tilt=al.stats(r_t, a, b), ivol=al.stats(r_i, a, b), monthly_excess_bp=round(float(m.mean() * 1e4), 1),
                        ci95_bp=[round(float(np.percentile(boots, 2.5) * 1e4), 1), round(float(np.percentile(boots, 97.5) * 1e4), 1)],
                        months=len(m), max_group_share=round(share, 2), group_contrib=gc.round(4).to_dict())
    res['turnover_per_yr'] = dict(tilt=round(turn_t, 2), ivol=round(turn_i, 2))
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    for k, v in res.items(): print(k, v if k == 'turnover_per_yr' else {x: v[x] for x in ('tilt', 'ivol', 'monthly_excess_bp', 'ci95_bp', 'months', 'max_group_share')})


if __name__ == '__main__':
    main()
