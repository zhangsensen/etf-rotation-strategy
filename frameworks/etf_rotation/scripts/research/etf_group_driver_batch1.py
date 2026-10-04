#!/usr/bin/env python3
"""Driver batch 1 (2026-09-24): each group's own upstream driver leads its relative return.

Pre-registered (direction fixed before computing):
  metals_equity   <- mean 20d return of CU/AL/ZN/NI futures      (+)
  dividend_low_vol<- 20d return of TL (30y CGB) futures           (+, yields down)
  electric_power  <- 20d return of JM (coking coal) futures       (-, fuel cost)
  cn_technology_manufacturing <- 20d return of ^SOX, US date < D  (+)
Label: group return minus 8-group EW, close D+1 -> close D+21. Time-series rank IC per
group with Newey-West t (lag 20) and a 20-session block-shuffle null of the driver.
Windows: profile 2022-02..2024-12 (SOX only from 2024-07), judged 2025-01-01..labels
exiting by the cold line 2026-03-24. Composite: z-scored driver signals (others 0),
top-2 groups, 20-session hold, costs 20/50 bp, vs EW8.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'frameworks/etf_rotation/src')); sys.path.insert(0, str(Path(__file__).resolve().parent))
from etf_strategy.canonical_data import load_canonical_daily
import etf_group_quarter_reversal as q

COLD = '2026-03-24'; H = 20; L = 20
D = Path(str(Path(__file__).resolve().parents[4] / "data"))
OUT = ROOT / 'runtime_outputs/etf_rotation_research/driver_batch1_20260924'
SPEC = {'metals_equity': (['CU', 'AL', 'ZN', 'NI'], +1), 'dividend_low_vol': (['TL'], +1),
        'electric_power': (['JM'], -1), 'cn_technology_manufacturing': (['^SOX'], +1)}


def fut(code):
    d = pd.read_parquet(D / f'futures/1d/{code}.parquet'); d['trade_date'] = pd.to_datetime(d['trade_date'])
    return d.set_index('trade_date')['close'].astype(float)


def load():
    p = load_canonical_daily(q.DATA, ROOT / 'config/etf_rotation_universe_v1.json', as_of=COLD, roles=('candidate',))
    groups = yaml.safe_load((ROOT / 'frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml').read_text())['groups']
    r = p['close'].pct_change(fill_method=None)
    gr = pd.DataFrame({g: r[v['members']].mean(axis=1) for g, v in groups.items()})
    gr = gr.loc[gr.notna().all(axis=1)].loc['2022-01-10':]
    cal = gr.index
    sig = {}
    for g, (codes, sgn) in SPEC.items():
        parts = []
        for cde in codes:
            if cde == '^SOX':
                s = pd.read_parquet(D / 'global_ai/cache/_idx_SOX.parquet')['close'].astype(float)
                s.index = pd.to_datetime(s.index).tz_localize(None)
                known = s.reindex(cal - pd.Timedelta(days=1), method='ffill')   # US close before A-share D
                known.index = cal
            else:
                known = fut(cde).reindex(cal, method='ffill')
            parts.append(known / known.shift(L) - 1)
        sig[g] = sgn * pd.concat(parts, axis=1).mean(axis=1)
    sig = pd.DataFrame(sig)
    lvl = (1 + gr).cumprod()
    fwd = lvl.shift(-1 - H) / lvl.shift(-1) - 1
    rel = fwd.sub(fwd.mean(axis=1), axis=0)
    cost = pd.Series({g: np.mean([0.005 if m in q.QDII else 0.002 for m in v['members']]) for g, v in groups.items()})
    return gr, sig, rel, cost


def nw_t(x, lag=H):
    x = np.asarray(x); x = x[~np.isnan(x)]; n = len(x)
    if n < 30: return np.nan
    xc = x - x.mean(); s = xc @ xc / n
    for j in range(1, lag + 1): s += 2 * (1 - j / (lag + 1)) * (xc[j:] @ xc[:-j] / n)
    return x.mean() / np.sqrt(s / n)


def ts_ic(sig, rel, a, b):
    s, r = sig.loc[a:b], rel.loc[a:b]; ok = s.notna() & r.notna()
    s, r = s[ok], r[ok]
    if len(s) < 60: return dict(n=len(s))
    rs, rr = s.rank(), r.rank(); prod = (rs - rs.mean()) * (rr - rr.mean()) / (rs.std() * rr.std())
    return dict(n=len(s), ic=round(float(prod.mean()), 3), t=round(float(nw_t(prod.values)), 2))


def main():
    gr, sig, rel, cost = load()
    out = {}; rng = np.random.default_rng(0)
    lastsig = rel.loc[:COLD].dropna(how='all').index[-1]
    for g in SPEC:
        prof = ts_ic(sig[g], rel[g], '2022-02-01', '2024-12-31'); jud = ts_ic(sig[g], rel[g], '2025-01-01', lastsig)
        s = sig[g].loc['2025-01-01':lastsig]; T = len(s); null = []
        for _ in range(300):
            bl = [np.arange(i, min(i + H, T)) for i in range(0, T, H)]; rng.shuffle(bl)
            sh = pd.Series(s.values[np.concatenate(bl)], index=s.index)
            null.append(ts_ic(sh, rel[g], '2025-01-01', lastsig).get('ic', np.nan))
        jud['null_ic_p95'] = round(float(np.nanpercentile(null, 95)), 3); jud['pct_in_null'] = round(float((np.array(null) < jud.get('ic', np.nan)).mean()), 3)
        out[g] = dict(profile=prof, judged=jud)
        print(f"{g:28s} profile {prof} | judged {jud}")
    z = sig.sub(sig.rolling(250, min_periods=120).mean()).div(sig.rolling(250, min_periods=120).std())
    score = pd.DataFrame(0.0, index=gr.index, columns=gr.columns); score[z.columns] = z
    score = score.where(z.notna().all(axis=1).reindex(gr.index), np.nan)
    import etf_group_quarter_flow as f
    q.HOLD = H
    d = f.simulate(gr, cost, score); ew = gr.mean(axis=1)
    out['composite'] = {'judged': q.stats(d, ew, '2025-01-01', COLD)}
    print('composite judged', out['composite'])
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'results.json').write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))


if __name__ == '__main__':
    main()
