#!/usr/bin/env python3
"""Macro drivers vs 8-group relative returns, 2015-01..cold line (2026-03-24).

Pre-registered (sign fixed before computing): 20-session change of
  gold <- US 10y real yield (-); us_large_growth <- US 10y nominal (-);
  hk_technology <- USDCNH (-); metals_equity <- CU main (+);
  dividend_low_vol <- T (10y CGB future) main (+); electric_power <- JM main (-);
  cn_technology_manufacturing, innovative_pharma: no driver (score 0).
US/FX data dated t is used on the next A-share session (time zone). Label: group
return minus EW8, close D+1 -> D+1+H, H in {20, 60}. Time-series rank IC per group
(Newey-West, lag H/20+2 steps on 20-session sampling), segments 2015-2024 and
2025..cold. Composite: z-score (trailing 250) of signed signals, monthly (20-session)
rebalance, top-2 held 20 sessions, costs 20/50 bp, vs EW8; 20-session block-shuffle
null of the signal panel.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import etf_group_regime_longhistory as base

M = ROOT / 'runtime_outputs/etf_rotation_research/long_history_proxies/macro'
OUT = ROOT / 'runtime_outputs/etf_rotation_research/macro_longhistory_20260924'
COLD = base.COLD; L = 20


def series(name, col, datecol):
    d = pd.read_parquet(M / f'{name}.parquet'); d[datecol] = pd.to_datetime(d[datecol])
    s = d.drop_duplicates(datecol).set_index(datecol).sort_index()[col].astype(float)
    return s


def signals(cal):
    def on_cal(s, lag_day):
        if lag_day:   # foreign data of date t usable from next A-share session
            k = s.reindex(cal - pd.Timedelta(days=1), method='ffill'); k.index = cal; return k
        return s.reindex(cal, method='ffill')
    chg = lambda s: s - s.shift(L)
    ret = lambda s: s / s.shift(L) - 1
    sig = pd.DataFrame(index=cal)
    sig['gold'] = -chg(on_cal(series('us_trycr', 'y10', 'date'), True))
    sig['us_large_growth'] = -chg(on_cal(series('us_tycr', 'y10', 'date'), True))
    sig['hk_technology'] = -ret(on_cal(series('USDCNH', 'bid_close', 'trade_date'), True))
    sig['metals_equity'] = ret(on_cal(series('CU', 'close', 'trade_date'), False))
    sig['dividend_low_vol'] = ret(on_cal(series('T', 'close', 'trade_date'), False))
    sig['electric_power'] = -ret(on_cal(series('JM', 'close', 'trade_date'), False))
    return sig


def nw_t(x, lag):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n < 20: return np.nan
    xc = x - x.mean(); s = xc @ xc / n
    for j in range(1, lag + 1): s += 2 * (1 - j / (lag + 1)) * (xc[j:] @ xc[:-j] / n)
    return x.mean() / np.sqrt(s / n)


def main():
    g = base.build(); cal = g.index; lvl = (1 + g).cumprod()
    sig = signals(cal); res = {}
    samp = cal[::20]
    for H in (20, 60):
        fwd = lvl.shift(-1 - H) / lvl.shift(-1) - 1; rel = fwd.sub(fwd.mean(axis=1), axis=0)
        for grp in sig.columns:
            for seg, a, b in (('2015_2024', '2015-01-01', '2024-12-31'), ('2025_cold', '2025-01-01', COLD)):
                s = sig[grp].reindex(samp).loc[a:b]; r = rel[grp].reindex(samp).loc[a:b]; ok = s.notna() & r.notna()
                s, r = s[ok], r[ok]
                if len(s) < 8: continue
                rs, rr = s.rank(), r.rank(); prod = (rs - rs.mean()) * (rr - rr.mean()) / (rs.std() * rr.std())
                res.setdefault(f'H{H}', {}).setdefault(grp, {})[seg] = dict(n=len(s), ic=round(float(prod.mean()), 3), t=round(float(nw_t(prod.values, H // 20 + 1)), 2))
    # composite rotation
    z = sig.sub(sig.rolling(250, min_periods=120).mean()).div(sig.rolling(250, min_periods=120).std())
    score = pd.DataFrame(0.0, index=cal, columns=g.columns); score[z.columns] = z
    score = score.where(z.notna().all(axis=1), np.nan)
    def run(gret, sc):
        L_ = (1 + gret).cumprod(); rows = []
        for i in range(0, len(cal) - 21, 20):
            s = sc.iloc[i]
            if s.isna().any(): continue
            top = s.sort_values(ascending=False).index[:2]
            nxt = L_.iloc[i + 21] / L_.iloc[i + 1] - 1
            c = np.mean([base.COST[x] for x in top]) * 2
            rows.append(dict(date=cal[i], ex=float(nxt[top].mean() - nxt.mean() - c)))
        return pd.DataFrame(rows).set_index('date').ex
    ex = run(g, score)
    comp = {}
    for seg, a, b in (('2015_2024', '2015-01-01', '2024-12-31'), ('2025_cold', '2025-01-01', COLD)):
        e = ex.loc[a:b]; comp[seg] = dict(n=len(e), excess_per20d_bp=round(e.mean() * 1e4, 1), t=round(e.mean() / e.std() * np.sqrt(len(e)), 2), hit=round((e > 0).mean(), 2))
    rng = np.random.default_rng(0); T = len(cal); null = []
    for _ in range(200):
        bl = [np.arange(i, min(i + 20, T)) for i in range(0, T, 20)]; rng.shuffle(bl); o = np.concatenate(bl)
        sc = pd.DataFrame(score.values[o], index=cal, columns=score.columns)
        null.append(run(g, sc).loc['2015-01-01':'2024-12-31'].mean())
    comp['null_2015_2024_bp'] = dict(mean=round(np.mean(null) * 1e4, 1), p95=round(np.percentile(null, 95) * 1e4, 1))
    res['composite'] = comp
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    for H in ('H20', 'H60'):
        print(H); [print(f'  {k:18s}', v) for k, v in res[H].items()]
    print('composite', comp)


if __name__ == '__main__':
    main()
