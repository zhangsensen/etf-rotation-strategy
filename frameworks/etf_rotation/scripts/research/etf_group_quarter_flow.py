#!/usr/bin/env python3
"""Quarter-horizon rotation driven by ETF share flows (2026-09-24).

Pre-registered before computing: signal = contrarian net share flow (Brown, Davies &
Ringgenberg 2021: ETF flows predict reversals; 09-22 local lead: share decline x range
contraction outperformed in 2025 and 2026). Flow rate over L sessions =
sum(delta shares * close) / (shares * close at t-L), group = sum over members.
Share of trade date T is usable at T+1 (usable_from_date), so the signal at close D
uses shares up to D-1. us_large_growth (513100, shares frozen by QDII quota) is
excluded -> 7 groups, top-2 held. Same tranche engine, costs, windows and null as
etf_group_quarter_reversal.py. Data read only to the cold line 2026-03-24.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'frameworks/etf_rotation/src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from etf_strategy.canonical_data import load_canonical_daily
import etf_group_quarter_reversal as q

COLD = q.COLD
OUT = ROOT / 'runtime_outputs/etf_rotation_research/quarter_flow_20260924'
EXCLUDE = 'us_large_growth'
PREREG = ('CFLOW20', 'CFLOW60')          # contrarian flow, the tested hypothesis
INFO = ('PFLOW20', 'PFLOW60')            # same flow, pro-cyclical sign, reported only


def load():
    p = load_canonical_daily(q.DATA, ROOT / 'config/etf_rotation_universe_v1.json', as_of=COLD, roles=('candidate',))
    groups = yaml.safe_load((ROOT / 'frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml').read_text())['groups']
    groups = {g: v for g, v in groups.items() if g != EXCLUDE}
    close = p['close']
    sh = {}
    for m in close.columns:
        d = pd.read_parquet(q.DATA / 'fund_share' / f'{m}.parquet')
        s = d.set_index(pd.to_datetime(d['usable_from_date']))['fd_share'].astype(float)
        sh[m] = s[~s.index.duplicated(keep='last')]
    shares = pd.DataFrame(sh).reindex(close.index).ffill().loc[:COLD]   # known at date = usable_from_date
    r = close.pct_change(fill_method=None)
    gr = pd.DataFrame({g: r[v['members']].mean(axis=1) for g, v in groups.items()})
    flows = {}
    for L in (20, 60):
        dflow = shares.diff() * close          # yuan flow per day (shares known that day)
        aum0 = (shares * close).shift(L)
        f = {g: dflow[v['members']].rolling(L, min_periods=L).sum().sum(axis=1, min_count=len(v['members'])) /
                aum0[v['members']].sum(axis=1, min_count=len(v['members'])) for g, v in groups.items()}
        flows[L] = pd.DataFrame(f)
    ok = gr.notna().all(axis=1)
    gr = gr.loc[ok].loc['2022-01-10':]
    cost = pd.Series({g: np.mean([0.005 if m in q.QDII else 0.002 for m in v['members']]) for g, v in groups.items()})
    scores = {'CFLOW20': -flows[20], 'CFLOW60': -flows[60], 'PFLOW20': flows[20], 'PFLOW60': flows[60]}
    return gr, cost, {k: v.reindex(gr.index) for k, v in scores.items()}


def simulate(gr, cost, score):
    idx = gr.index; tranches = []
    for i in range(0, len(idx) - 1, q.STEP):
        s = score.iloc[i]
        if s.isna().any():
            continue
        top = s.sort_values(ascending=False).index[:q.K]
        w = pd.Series(0.0, index=gr.columns); w[top] = 1.0 / q.K
        tranches.append((i + 1, min(i + 1 + q.HOLD, len(idx)), w))
    port = pd.Series(0.0, index=idx); tc = pd.Series(0.0, index=idx); live = pd.Series(0, index=idx)
    for a, b, w in tranches:
        port.iloc[a:b] += (gr.iloc[a:b] * w).sum(axis=1).values; live.iloc[a:b] += 1
        tc.iloc[a] += float((w * cost).sum())
        if b < len(idx):
            tc.iloc[b - 1] += float((w * cost).sum())
    ok = live > 0
    return (port / live.where(ok) - tc / live.where(ok)).where(ok)


def main():
    gr, cost, scores = load()
    ew = gr.mean(axis=1); res = {}
    for k, sc in scores.items():
        d = simulate(gr, cost, sc)
        res[k] = {'profile_2022_2024': q.stats(d, ew, '2022-02-01', '2024-12-31'), 'judged_2025_cold': q.stats(d, ew, '2025-01-01', COLD),
                  'role': 'preregistered' if k in PREREG else 'info_only'}
    rng = np.random.default_rng(0); T = len(gr); null = []
    for _ in range(200):
        bl = [np.arange(i, min(i + q.STEP, T)) for i in range(0, T, q.STEP)]; rng.shuffle(bl); order = np.concatenate(bl)
        gs = pd.DataFrame(gr.values[order], index=gr.index, columns=gr.columns)
        null.append(q.stats(simulate(gs, cost, scores['CFLOW60']), gs.mean(axis=1), '2025-01-01', COLD)['excess_ann'])
    res['null_CFLOW60_excess_ann_judged'] = dict(mean=round(float(np.mean(null)), 3), sd=round(float(np.std(null)), 3), p95=round(float(np.percentile(null, 95)), 3))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for k, v in res.items():
        if 'judged_2025_cold' in v:
            pr, jd = v['profile_2022_2024'], v['judged_2025_cold']
            print(f"{k:8s} [{v['role'][:6]}] profile ex {pr['excess_ann']:+.3f} (t {pr['t_20d_blocks']}) | judged ex {jd['excess_ann']:+.3f} (ann {jd['ann']:+.3f} vs EW7 {jd['ew_ann']:+.3f}, t {jd['t_20d_blocks']}, n {jd['n_blocks']}, dd {jd['maxdd']})")
    print('null', res['null_CFLOW60_excess_ann_judged'])


if __name__ == '__main__':
    main()
