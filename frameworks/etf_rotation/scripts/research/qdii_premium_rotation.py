#!/usr/bin/env python3
"""Same-index QDII ETF premium rotation (2026-09-24).

Small-capital edge: several listed ETFs track the same index (Nasdaq-100: 12, S&P 500: 4)
but trade at different premiums to NAV because QDII quota limits creations. Pre-registered:
  eligible   listed >= 60 sessions, trailing 60-session median turnover >= 10m CNY
  premium    close_t / unit_nav of the latest nav_date whose ann_date < t (same nav_date
             across ETFs of one index; the common index move cancels in the ranking)
  rule       hold the eligible ETF with the lowest premium; switch only when the holding's
             premium exceeds the minimum by more than THETA (1%); signal at close t,
             trade at close t+1; one-way cost 10 bp per switch leg
  benchmark  hold 513100.SH (NDX) / 513500.SH (SPX); equal weight of eligible ETFs
Return = adjusted close-to-close of the ETF held. Data read to the latest available date
(execution-level rule, not a factor: the cold-line rule governs factor mining).
"""
from __future__ import annotations
import glob, json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[4]
Q = ROOT / 'runtime_outputs/etf_rotation_research/qdii_premium'
RAW = Path(str(Path(__file__).resolve().parents[4] / "data/etf_all_daily_v1/raw"))
THETA, COST = 0.01, 0.001


def prices(codes):
    fs = sorted(glob.glob(str(RAW / 'fund_daily/*.parquet')))
    d = pd.concat([pd.read_parquet(f, columns=['ts_code', 'trade_date', 'close', 'amount']) for f in fs])
    d = d[d.ts_code.isin(codes)]
    a = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(RAW / 'fund_adj/*.parquet')))]); a = a[a.ts_code.isin(codes)]
    d = d.merge(a, on=['ts_code', 'trade_date'], how='left'); d['trade_date'] = pd.to_datetime(d.trade_date)
    close = d.pivot(index='trade_date', columns='ts_code', values='close').sort_index()
    adj = d.pivot(index='trade_date', columns='ts_code', values='adj_factor').sort_index().ffill()
    amt = d.pivot(index='trade_date', columns='ts_code', values='amount').sort_index() * 1000   # 千元 -> 元
    return close, close * adj, amt


def navs(codes, cal):
    out = {}
    for c in codes:
        n = pd.read_parquet(Q / 'nav' / f'{c}.parquet')
        n['nav_date'] = pd.to_datetime(n.nav_date); n['ann_date'] = pd.to_datetime(n.ann_date)
        n = n.dropna(subset=['unit_nav']).sort_values(['nav_date', 'ann_date']).drop_duplicates('nav_date', keep='first')
        rows = []
        for t in cal:
            k = n[n.ann_date < t]
            rows.append((k.nav_date.iloc[-1], float(k.unit_nav.iloc[-1])) if len(k) else (pd.NaT, np.nan))
        out[c] = pd.DataFrame(rows, index=cal, columns=['nav_date', 'nav'])
    return out


def run(index_name, bench):
    u = pd.read_csv(Q / 'universe.csv'); codes = [c for c in u[u.idx == index_name].ts_code if c not in ('501312.SH', '159529.SZ')]
    close, adjc, amt = prices(codes); cal = close.index
    codes = [c for c in codes if c in close.columns and (Q / 'nav' / f'{c}.parquet').exists()]
    nv = navs(codes, cal)
    prem = pd.DataFrame({c: close[c] / nv[c]['nav'] - 1 for c in codes})
    navd = pd.DataFrame({c: nv[c]['nav_date'] for c in codes})
    listed = close.notna().cumsum() >= 60
    liq = amt.rolling(60, min_periods=20).median() >= 1e7
    elig = listed & liq & prem.notna()
    common = navd.where(elig).max(axis=1)                      # compare only ETFs on the latest common nav_date
    elig &= navd.eq(common, axis=0)
    ret = adjc.pct_change(fill_method=None)
    hold, held, rows = None, [], []
    for i, t in enumerate(cal[:-1]):
        e = elig.loc[t]
        if e.sum() < 2:
            held.append(hold); continue
        p = prem.loc[t][e]; best = p.idxmin()
        if hold is None or hold not in p.index or p[hold] - p.min() > THETA:
            if hold != best:
                rows.append(dict(date=t, frm=hold, to=best, gap=float(p[hold] - p.min()) if hold in p.index else np.nan))
            hold = best
        held.append(hold)
    held = pd.Series(held + [hold], index=cal).shift(1)          # trade at next close
    r = pd.Series([ret.at[d, h] if isinstance(h, str) else np.nan for d, h in held.items()], index=cal)
    sw = pd.Series(0.0, index=cal)
    for x in rows:
        pos = cal.get_loc(x['date']) + 1
        if pos < len(cal): sw.iloc[pos] += COST * (2 if x['frm'] else 1)
    strat = (r - sw).dropna()
    b = ret[bench].reindex(strat.index)
    ew = ret.where(elig.shift(1)).mean(axis=1).reindex(strat.index)
    def s(x):
        x = x.dropna(); yrs = len(x) / 252; return dict(ann=round(float((1 + x).prod() ** (1 / yrs) - 1), 4), n=len(x))
    yearly = pd.DataFrame({'strat': strat, 'bench': b, 'ew': ew}).groupby(strat.index.year).apply(lambda d: (1 + d).prod() - 1).round(4)
    res = dict(index=index_name, start=str(strat.index[0].date()), end=str(strat.index[-1].date()), strat=s(strat), bench=s(b), ew=s(ew),
               switches=len(rows), switches_per_year=round(len(rows) / (len(strat) / 252), 1),
               mean_prem_held=round(float(prem.stack().reindex(list(zip(held.dropna().index, held.dropna().values))).mean()), 4),
               mean_prem_bench=round(float(prem[bench].mean()), 4), yearly=yearly.to_dict())
    return res, pd.DataFrame(rows)


def main():
    out = {}
    for idx, bench in (('NDX', '513100.SH'), ('SPX', '513500.SH')):
        res, sw = run(idx, bench); out[idx] = res; sw.to_csv(Q / f'switches_{idx}.csv', index=False)
        print(json.dumps(res, ensure_ascii=False, default=str)[:1200])
    (Q / 'results.json').write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))


if __name__ == '__main__':
    main()
