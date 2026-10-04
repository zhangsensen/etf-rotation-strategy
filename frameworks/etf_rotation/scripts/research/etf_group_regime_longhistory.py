#!/usr/bin/env python3
"""Can the 8-group momentum/reversal regime be identified in advance? (2026-09-24)

USER approved long-history judging for quarter-horizon ETF rotation. Proxies (price
indices; HK in HKD, 513100/518880 are the ETFs themselves), 2015-01 .. cold line:
  cn_tech = EW(H30184 semis, 931160 comm equip, 930601 software, H30590 robots, 931494 consumer elec)
  hk_tech = HKTECH; us_growth = 513100.SH; pharma = EW(931152, 931250 from 2017)
  gold = 518880.SH; metals = 000819.SH; dividend_low_vol = H30269; electric = H30199
Target at each 20-session rebalance t: Y = cross-sectional rank corr(past 60d return,
next 60d return) (>0 momentum regime, <0 reversal).  Pre-registered states known at t:
  S1 dispersion expansion = xs-std(ret t-60..t) / xs-std(ret t-120..t-60) - 1   (+)
  S2 volatility level = pct rank of mean 20d vol vs trailing 750 sessions         (-)
  S3 last regime = rank corr(ret t-120..t-60, ret t-60..t)                       (+)
Tests: corr(S, Y) with Newey-West (lag 3) on all rebalances, plus sign hit rate;
strategy = MOM60 if state predicts momentum else REV60 (S3: sign; S1/S2: vs trailing
median), 60-session tranches, top-2, costs 20/50 bp, vs EW8 and static MOM60/REV60.
Periods reported separately: 2015-2024 and 2025-01..cold line.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[4]
PX = ROOT / 'runtime_outputs/etf_rotation_research/long_history_proxies'
ETF = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1/1d_qfq"))
OUT = ROOT / 'runtime_outputs/etf_rotation_research/regime_longhistory_20260924'
COLD = '2026-03-24'; STEP, HOLD, K = 20, 60, 2
COST = {'cn_technology_manufacturing': .002, 'hk_technology': .005, 'us_large_growth': .005, 'innovative_pharma': .0035,
        'gold': .002, 'metals_equity': .002, 'dividend_low_vol': .002, 'electric_power': .002}


def lvl(code):
    return pd.read_parquet(PX / f'{code}.parquet')['close']


def etf(code):
    f = ETF / f'{code}.parquet'
    if not f.exists():
        f = ETF.parent / '1d' / f'{code}.parquet'
    d = pd.read_parquet(f)
    tcol = 'trade_date' if 'trade_date' in d else d.columns[0]
    d[tcol] = pd.to_datetime(d[tcol]); return d.set_index(tcol)['close'].astype(float)


def build():
    cal = lvl('H30269.CSI').loc['2014-06-01':COLD].index
    def ret(s): return s.reindex(cal.union(s.index)).ffill().reindex(cal).pct_change(fill_method=None)
    g = pd.DataFrame({
        'cn_technology_manufacturing': pd.concat([ret(lvl(c)) for c in ['H30184.CSI', '931160.CSI', '930601.CSI', 'H30590.CSI', '931494.CSI']], axis=1).mean(axis=1),
        'hk_technology': ret(lvl('HKTECH')),
        'us_large_growth': ret(etf('513100.SH')),
        'innovative_pharma': pd.concat([ret(lvl('931152.CSI')), ret(lvl('931250.CSI'))], axis=1).mean(axis=1),
        'gold': ret(etf('518880.SH')),
        'metals_equity': ret(lvl('000819.SH')),
        'dividend_low_vol': ret(lvl('H30269.CSI')),
        'electric_power': ret(lvl('H30199.CSI')),
    })
    return g.loc['2015-01-05':COLD].dropna()


def rc(a, b):
    return a.rank().corr(b.rank())


def nw_t(x, lag=3):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x); xc = x - x.mean(); s = xc @ xc / n
    for j in range(1, lag + 1): s += 2 * (1 - j / (lag + 1)) * (xc[j:] @ xc[:-j] / n)
    return x.mean() / np.sqrt(s / n)


def main():
    g = build(); L = (1 + g).cumprod(); idx = g.index
    vol = g.rolling(20).std().mean(axis=1)
    rows = []
    for i in range(120, len(idx) - HOLD - 1, STEP):
        t = idx[i]
        p60 = L.iloc[i] / L.iloc[i - 60] - 1; p_prev = L.iloc[i - 60] / L.iloc[i - 120] - 1
        nxt = L.iloc[i + 1 + HOLD] / L.iloc[i + 1] - 1
        v = vol.iloc[max(0, i - 750):i + 1]
        rows.append(dict(date=t, Y=rc(p60, nxt), S1=p60.std() / p_prev.std() - 1, S2=(v < v.iloc[-1]).mean(), S3=rc(p_prev, p60),
                         mom_ret=float(nxt[p60.nlargest(K).index].mean() - nxt.mean()), rev_ret=float(nxt[p60.nsmallest(K).index].mean() - nxt.mean()),
                         cost=float(np.mean([COST[c] for c in p60.nlargest(K).index]))))
    df = pd.DataFrame(rows).set_index('date')
    df['S1_med'] = df.S1.expanding(12).median().shift(1); df['S2_med'] = df.S2.expanding(12).median().shift(1)
    pred = {'S1': np.sign(df.S1 - df.S1_med), 'S2': -np.sign(df.S2 - df.S2_med), 'S3': np.sign(df.S3)}
    res = {}
    for seg, a, b in (('2015_2024', '2015-01-01', '2024-12-31'), ('2025_cold', '2025-01-01', COLD), ('all', '2015-01-01', COLD)):
        d = df.loc[a:b]; out = {'n_rebalances': len(d), 'mean_Y': round(d.Y.mean(), 3), 'share_momentum_regime': round((d.Y > 0).mean(), 2)}
        for s in ('S1', 'S2', 'S3'):
            sgn = {'S1': 1, 'S2': -1, 'S3': 1}[s]
            c = d[s].corr(d.Y) * sgn
            prod = ((d[s] - d[s].mean()) / d[s].std() * (d.Y - d.Y.mean()) / d.Y.std() * sgn)
            p = pred[s].loc[a:b]
            hit = ((p > 0) == (d.Y > 0))[p != 0].mean()
            # switch strategy: excess over EW per 60d tranche (overlapping every 20 sessions), cost on both legs
            sw = np.where(p > 0, d.mom_ret, d.rev_ret) - 2 * d.cost
            out[s] = dict(corr_signed=round(float(c), 3), nw_t=round(float(nw_t(prod.dropna())), 2), hit=round(float(hit), 3),
                          switch_excess_per60d_bp=round(float(np.nanmean(sw)) * 1e4, 1))
        out['static_MOM60_bp'] = round(float((d.mom_ret - 2 * d.cost).mean()) * 1e4, 1)
        out['static_REV60_bp'] = round(float((d.rev_ret - 2 * d.cost).mean()) * 1e4, 1)
        res[seg] = out
    yr = df.Y.groupby(df.index.year).mean().round(3).to_dict()
    res['Y_by_year'] = {int(k): v for k, v in yr.items()}
    OUT.mkdir(parents=True, exist_ok=True); df.to_csv(OUT / 'rebalances.csv')
    (OUT / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))


if __name__ == '__main__':
    main()
