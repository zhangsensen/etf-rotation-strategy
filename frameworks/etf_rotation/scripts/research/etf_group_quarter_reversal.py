#!/usr/bin/env python3
"""Quarter-horizon rotation on the fixed 14 ETF / 8 group frame (2026-09-24).

Question: is the 8-group dispersion capturable at a 60-day horizon with price-only
reversal/momentum rules? Data is read only up to the cold line (2026-03-24).
Group return = mean of available members' close-to-close returns (groups complete
from 2022-01-07). Signal at close D, position from close D+1 (one-day lag).
Rebalance every 20 sessions; each rebalance opens a 60-session tranche holding the
top-2 groups; portfolio = equal weight of live tranches (3). Costs: one-way 20 bp
A-share, 50 bp QDII, on tranche turnover. Profile = 2022-02..2024-12 (not a gate);
judged window = 2025-01-01..cold line. WFO picks the rule with the best trailing
12-rebalance net excess over EW8 using completed tranches only. Null = 20-session
block shuffle of the group return panel.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'frameworks/etf_rotation/src'))
from etf_strategy.canonical_data import load_canonical_daily

COLD = '2026-03-24'
DATA = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
OUT = ROOT / 'runtime_outputs/etf_rotation_research/quarter_reversal_20260924'
QDII = {'513100.SH', '513130.SH', '513120.SH'}
STEP, HOLD, K = 20, 60, 2
RULES = {f'{kind}{L}': (kind, L) for kind in ('REV', 'MOM') for L in (20, 60, 120)}


def load():
    p = load_canonical_daily(DATA, ROOT / 'config/etf_rotation_universe_v1.json', as_of=COLD, roles=('candidate',))
    groups = yaml.safe_load((ROOT / 'frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml').read_text())['groups']
    r = p['close'].pct_change(fill_method=None)
    gr = pd.DataFrame({g: r[v['members']].mean(axis=1) for g, v in groups.items()})
    gr = gr.loc[gr.notna().all(axis=1)]
    gr = gr.loc['2022-01-10':]
    cost = pd.Series({g: np.mean([0.005 if m in QDII else 0.002 for m in v['members']]) for g, v in groups.items()})
    return gr, cost


def simulate(gr, cost, rule):
    kind, L = RULES[rule]
    lvl = (1 + gr).cumprod()
    past = lvl / lvl.shift(L) - 1
    score = -past if kind == 'REV' else past
    idx = gr.index
    reb = list(range(max(L, 1), len(idx) - 1, STEP))
    tranches = []  # (start_pos, end_pos, weights)
    for i in reb:
        s = score.iloc[i]
        if s.isna().any():
            continue
        top = s.sort_values(ascending=False).index[:K]
        w = pd.Series(0.0, index=gr.columns); w[top] = 1.0 / K
        tranches.append((i + 1, min(i + 1 + HOLD, len(idx)), w, idx[i]))
    port = pd.Series(0.0, index=idx); turn_cost = pd.Series(0.0, index=idx); live = pd.Series(0, index=idx)
    prev_w = {}
    tr_rows = []
    for k, (a, b, w, d) in enumerate(tranches):
        seg = gr.iloc[a:b]
        port.iloc[a:b] += (seg * w).sum(axis=1).values
        live.iloc[a:b] += 1
        turn_cost.iloc[a] += float((w * cost).sum())            # buy
        if b < len(idx):
            turn_cost.iloc[b - 1] += float((w * cost).sum())    # sell
        tr_rows.append(dict(signal_date=d, start=idx[a], end=idx[b - 1],
                            net=float((1 + seg @ w).prod() - 1 - 2 * (w * cost).sum()),
                            ew=float((1 + seg.mean(axis=1)).prod() - 1), picks=','.join(w[w > 0].index)))
    ok = live > 0
    daily = (port / live.where(ok) - turn_cost / live.where(ok)).where(ok)
    return daily, pd.DataFrame(tr_rows)


def stats(daily, ew, a, b):
    d = daily.loc[a:b].dropna(); e = ew.loc[d.index]
    ex = d - e
    ann = lambda x: (1 + x).prod() ** (252 / len(x)) - 1
    blocks = ex.groupby(np.arange(len(ex)) // STEP).sum()
    t = blocks.mean() / blocks.std(ddof=1) * np.sqrt(len(blocks)) if len(blocks) > 2 else np.nan
    nav = (1 + d).cumprod()
    return dict(ann=round(ann(d), 3), ew_ann=round(ann(e), 3), excess_ann=round(ann(d) - ann(e), 3),
                t_20d_blocks=round(float(t), 2), n_blocks=len(blocks), maxdd=round(float((nav / nav.cummax() - 1).min()), 3))


def wfo(gr, cost, lookback_tranches=12):
    sims = {r: simulate(gr, cost, r) for r in RULES}
    idx = gr.index; ew = gr.mean(axis=1)
    reb_dates = sims['REV60'][1].signal_date.tolist()
    chosen = pd.Series(np.nan, index=idx, dtype=object); out = pd.Series(np.nan, index=idx)
    picks = []
    for d in reb_dates:
        best, best_v = None, -np.inf
        for r, (_, tr) in sims.items():
            done = tr[(tr.end < d)].tail(lookback_tranches)   # completed tranches only
            if len(done) < 6:
                continue
            v = (done.net - done.ew).mean()
            if v > best_v:
                best, best_v = r, v
        if best is None:
            continue
        pos = idx.get_loc(d) + 1
        end = min(pos + STEP, len(idx))
        out.iloc[pos:end] = sims[best][0].iloc[pos:end].values
        picks.append((str(d.date()), best))
    return out, picks, sims


def main():
    gr, cost = load()
    ew = gr.mean(axis=1)
    res = {}
    wo, picks, sims = wfo(gr, cost)
    for r, (daily, _) in sims.items():
        res[r] = {'profile_2022_2024': stats(daily, ew, '2022-02-01', '2024-12-31'), 'judged_2025_cold': stats(daily, ew, '2025-01-01', COLD)}
    res['WFO'] = {'profile_2022_2024': stats(wo, ew, '2022-02-01', '2024-12-31'), 'judged_2025_cold': stats(wo, ew, '2025-01-01', COLD)}
    # null: block-shuffle 20-session blocks of the group panel
    rng = np.random.default_rng(0); T = len(gr); null = {'REV60': [], 'WFO': []}
    for _ in range(100):
        order = np.concatenate(rng.permutation([np.arange(i, min(i + STEP, T)) for i in range(0, T, STEP)], axis=0) if False else
                               [b for b in (lambda bl: (rng.shuffle(bl), bl)[1])([np.arange(i, min(i + STEP, T)) for i in range(0, T, STEP)])])
        gs = pd.DataFrame(gr.values[order], index=gr.index, columns=gr.columns)
        ews = gs.mean(axis=1)
        d, _ = simulate(gs, cost, 'REV60'); null['REV60'].append(stats(d, ews, '2025-01-01', COLD)['excess_ann'])
        w, _, _ = wfo(gs, cost); null['WFO'].append(stats(w, ews, '2025-01-01', COLD)['excess_ann'])
    res['null_excess_ann_judged'] = {k: dict(mean=round(float(np.mean(v)), 3), sd=round(float(np.std(v)), 3),
                                             p95=round(float(np.percentile(v, 95)), 3)) for k, v in null.items()}
    res['wfo_picks'] = picks
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    sims['REV60'][1].to_csv(OUT / 'tranches_REV60.csv', index=False)
    rows = [(k, v['profile_2022_2024'], v['judged_2025_cold']) for k, v in res.items() if isinstance(v, dict) and 'judged_2025_cold' in v]
    for k, pr, jd in rows:
        print(f"{k:7s} profile ex {pr['excess_ann']:+.3f} (ann {pr['ann']:+.3f}, t {pr['t_20d_blocks']}) | judged ex {jd['excess_ann']:+.3f} (ann {jd['ann']:+.3f} vs EW {jd['ew_ann']:+.3f}, t {jd['t_20d_blocks']}, n {jd['n_blocks']}, dd {jd['maxdd']})")
    print('null', res['null_excess_ann_judged']); print('WFO picks', picks[-16:])


if __name__ == '__main__':
    main()
