#!/usr/bin/env python3
"""Daily refresh of Tushare fund_share / fund_nav for the 14 candidate ETFs into
data/etf_rotation_v1/{fund_share,nav}/ with PIT column usable_from_date.
Idempotent full overwrite per symbol (tables are small). Linux-side ETF data,
outside the QMT-only stock K-line rule. Row cap: Tushare returns at most 2000
rows per fund_share call; for 518880/512400/513100 that starts 2018-07, which
still covers the 2021+ research windows."""
import sys, time, json, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[6]))
from data.downloaders.credentials import tushare_token  # noqa: E402
import tushare as ts, pandas as pd  # noqa: E402
pro = ts.pro_api(tushare_token())
ROOT = Path(str(Path(__file__).resolve().parents[6] / "data/etf_rotation_v1"))
cal = pd.read_parquet(ROOT / 'metadata/trade_calendar.parquet')
dcol = [c for c in cal.columns if 'date' in c.lower()][0]
days = pd.to_datetime(cal[dcol].astype(str)).sort_values().unique()
def next_td(d):
    # beyond the local calendar's end fall back to the next business day, so no row is ever left NaT
    d = pd.Timestamp(d); i = days.searchsorted(d, side='right')
    return pd.Timestamp(days[i]) if i < len(days) else (d + pd.offsets.BDay(1)).normalize()
uni = json.loads((Path(str(Path(__file__).resolve().parents[6] / "config/etf_rotation_universe_v1.json"))).read_text())
cand = [r['ts_code'] for r in uni['etfs'] if r['role'] == 'candidate']
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
man = {'created_at_utc': now, 'source': 'tushare pro fund_share/fund_nav', 'status': 'updating',
       'pit_rule': {'fund_share': 'usable_from_date = next trading day after trade_date',
                    'nav': 'usable_from_date = next trading day after ann_date'}, 'files': {}}
for c in cand:
    fs = pro.fund_share(ts_code=c); time.sleep(0.35)
    fs['trade_date'] = pd.to_datetime(fs.trade_date); fs = fs.sort_values('trade_date').drop_duplicates('trade_date')
    fs['fund_shares'] = fs.fd_share * 1e4; fs['usable_from_date'] = fs.trade_date.map(next_td); fs['downloaded_at'] = now
    fs[['ts_code', 'trade_date', 'fd_share', 'fund_shares', 'usable_from_date', 'downloaded_at']].to_parquet(ROOT / 'fund_share' / f'{c}.parquet', index=False)
    nv = pro.fund_nav(ts_code=c); time.sleep(0.35)
    nv['nav_date'] = pd.to_datetime(nv.nav_date); nv['ann_date'] = pd.to_datetime(nv.ann_date)
    nv = nv.sort_values('nav_date').drop_duplicates('nav_date')
    nv['usable_from_date'] = nv.ann_date.fillna(nv.nav_date.map(next_td)).map(next_td); nv['downloaded_at'] = now
    keep = [k for k in ['ts_code', 'nav_date', 'ann_date', 'usable_from_date', 'unit_nav', 'accum_nav', 'adj_nav', 'net_asset', 'total_netasset', 'downloaded_at'] if k in nv.columns]
    nv[keep].to_parquet(ROOT / 'nav' / f'{c}.parquet', index=False)
    man['files'][c] = {'fund_share_rows': len(fs), 'fund_share_last': str(fs.trade_date.max().date()), 'nav_rows': len(nv), 'nav_last': str(nv.nav_date.max().date())}
man['status'] = 'ready'
for sub in ('fund_share', 'nav'):
    json.dump(man, open(ROOT / sub / 'manifest.json', 'w'), ensure_ascii=False, indent=2)
print('ready', {c: (v['fund_share_last'], v['nav_last']) for c, v in list(man['files'].items())[:3]}, '...')
