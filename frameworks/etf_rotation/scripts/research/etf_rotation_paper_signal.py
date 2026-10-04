#!/usr/bin/env python3
"""Monthly paper signal for the 1m ETF rotation (read-only, no orders). 2026-09-24.

Layer 1: inverse 60d-vol weights across the 8 groups (pool ETFs, members equal weight
within a group). Layer 2: us_large_growth / hk_technology sleeves use the lowest-premium
eligible ETF of the same index (latest NAV with ann_date < today). Appends one JSON line
to runtime_outputs/etf_rotation_research/paper_ledger/signals.jsonl; skips if this month
already has a line. Evaluation of each month's line is done after the month ends.
"""
from __future__ import annotations
import datetime as dt, json, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'frameworks/etf_rotation/src'))
from etf_strategy.canonical_data import load_canonical_daily

DATA = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
LEDGER = ROOT / 'runtime_outputs/etf_rotation_research/paper_ledger/signals.jsonl'
Q = ROOT / 'runtime_outputs/etf_rotation_research/qdii_premium'
SLEEVE = {'us_large_growth': 'NDX', 'hk_technology': 'HST'}


def latest_premiums(index):
    import tushare as ts, time
    pro = ts.pro_api(); u = pd.read_csv(Q / 'universe.csv')
    u = u[(u.idx == index) & ~u.name.str.contains('LOF|联接')]
    listed_before = (dt.date.today() - dt.timedelta(days=90)).strftime('%Y%m%d')   # >= ~60 sessions listed
    codes = u[u.list_date.astype(str) <= listed_before].ts_code.tolist()
    end = dt.date.today().strftime('%Y%m%d'); start = (dt.date.today() - dt.timedelta(days=20)).strftime('%Y%m%d')
    out = {}
    for c in codes:
        try:
            n = pro.fund_nav(ts_code=c, start_date=start, end_date=end); time.sleep(0.4)
            p = pro.fund_daily(ts_code=c, start_date=start, end_date=end); time.sleep(0.4)
            if n is None or p is None or not len(n) or not len(p): continue
            n = n[pd.to_datetime(n.ann_date) < pd.Timestamp(dt.date.today())].sort_values('nav_date')
            p = p.sort_values('trade_date')
            if not len(n): continue
            amt = float(p.amount.tail(20).median()) * 1000
            if amt < 1e7: continue
            out[c] = dict(navs=dict(zip(n.nav_date.astype(str), n.unit_nav.astype(float))), close=float(p.close.iloc[-1]), price_date=str(p.trade_date.iloc[-1]))
        except Exception as e:
            print('skip', c, str(e)[:60])
    if not out: return out
    pdate = max(v['price_date'] for v in out.values())
    out = {c: v for c, v in out.items() if v['price_date'] == pdate}            # same price date
    d = min(max(v['navs']) for v in out.values())                               # common NAV date
    return {c: dict(premium=v['close'] / v['navs'][d] - 1, nav_date=d, price_date=pdate) for c, v in out.items() if d in v['navs']}


def last_pick(group):
    if not LEDGER.exists(): return None
    for l in reversed([json.loads(x) for x in LEDGER.read_text().splitlines() if x.strip()]):
        h = l['holdings'].get(group, {})
        if h.get('overlay_etfs'): return next(iter(h['overlay_etfs']))
    return None


def evaluate_previous():
    """Fill realized return for ledger lines whose holding month has ended (EW8 comparison)."""
    import tushare as ts, time
    if not LEDGER.exists(): return
    lines = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    pro = ts.pro_api(); changed = False
    for i, rec in enumerate(lines):
        if 'realized' in rec: continue
        start = pd.Timestamp(rec['signal_date']) + pd.Timedelta(days=1)
        end = (start + pd.offsets.MonthEnd(1)) if start.day > 1 else start + pd.offsets.MonthEnd(0)
        if pd.Timestamp(dt.date.today()) <= end: continue
        def ret(code):
            d = pro.fund_daily(ts_code=code, start_date=(start - pd.Timedelta(days=7)).strftime('%Y%m%d'), end_date=end.strftime('%Y%m%d')); time.sleep(0.4)
            a = pro.fund_adj(ts_code=code, start_date=(start - pd.Timedelta(days=7)).strftime('%Y%m%d'), end_date=end.strftime('%Y%m%d')); time.sleep(0.4)
            d = d.merge(a, on=['ts_code', 'trade_date']).sort_values('trade_date'); d['v'] = d.close * d.adj_factor
            after = d[pd.to_datetime(d.trade_date) > pd.Timestamp(rec['signal_date'])]   # entry = next session close
            return float(d.v.iloc[-1] / after.v.iloc[0] - 1) if len(after) > 1 else np.nan
        grp = {g: sum(wt * ret(c) for c, wt in h['etfs'].items()) for g, h in rec['holdings'].items()}
        strat = sum(rec['holdings'][g]['weight'] * grp[g] for g in grp); ew = float(np.mean(list(grp.values())))
        ov = dict(grp)
        for g, h in rec['holdings'].items():
            if h.get('overlay_etfs'): ov[g] = sum(wt * ret(c) for c, wt in h['overlay_etfs'].items())
        strat_ov = sum(rec['holdings'][g]['weight'] * ov[g] for g in ov)
        cost_g = {g: (0.005 if g in SLEEVE else 0.002) for g in rec['holdings']}
        prev = lines[i - 1] if i > 0 else None
        def tc(wmap, pmap):
            return sum(abs(wmap[g] - (pmap or {}).get(g, 0.0)) * cost_g[g] for g in wmap)
        w_main = {g: h['weight'] for g, h in rec['holdings'].items()}
        p_main = {g: h['weight'] for g, h in prev['holdings'].items()} if prev else None
        tilt = rec.get('weights_betatilt'); p_tilt = prev.get('weights_betatilt') if prev else None
        strat_tilt = sum(tilt[g] * grp[g] for g in grp) - tc(tilt, p_tilt) if tilt else None
        lines[i]['realized'] = dict(end=str(end.date()), entry='next session close', note='fixed entry weights, buy-and-hold within the month (drift implied); costs = |weight change| x one-way cost',
                                    ivol_pool_etfs_net=round(strat - tc(w_main, p_main), 5), ivol_betatilt_net=round(strat_tilt, 5) if strat_tilt is not None else None,
                                    ivol_pool_etfs=round(strat, 5), ivol_with_premium_overlay=round(strat_ov, 5),
                                    ew8_pool_etfs=round(ew, 5), group=grp); changed = True
    if changed:
        LEDGER.write_text(''.join(json.dumps(l, ensure_ascii=False) + '\n' for l in lines))


def main():
    evaluate_previous()
    month = dt.date.today().strftime('%Y-%m')
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    if LEDGER.exists() and any(json.loads(l).get('month') == month for l in LEDGER.read_text().splitlines() if l.strip()):
        print('NOOP: signal for', month, 'already recorded'); return
    p = load_canonical_daily(DATA, ROOT / 'config/etf_rotation_universe_v1.json', as_of=dt.date.today().isoformat(), roles=('candidate',))
    groups = yaml.safe_load((ROOT / 'frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml').read_text())['groups']
    r = p['close'].pct_change(fill_method=None)
    gr = pd.DataFrame({g: r[v['members']].mean(axis=1) for g, v in groups.items()}).dropna()
    vol = gr.tail(60).std(); w = (1 / vol) / (1 / vol).sum()
    x = gr.tail(60); m = x.mean(axis=1)
    def beta(mask):
        mm = m[mask]; return x[mask].apply(lambda s: np.cov(s, mm)[0, 1] / np.var(mm, ddof=1))
    ba = beta(m < 0) - beta(m > 0); score = ((-ba).rank() - 1) / 7 * 2 - 1
    w_tilt = w * (1 + 0.25 * score); w_tilt = w_tilt / w_tilt.sum()
    holdings = {}
    for g, v in groups.items():
        if g in SLEEVE:
            prem = latest_premiums(SLEEVE[g])
            prev = last_pick(g)
            best = min(prem, key=lambda c: prem[c]['premium']) if prem else None
            if prev in prem and best and prem[prev]['premium'] - prem[best]['premium'] <= 0.01:
                pick = prev
            else:
                pick = best or v['members'][0]
            holdings[g] = dict(weight=round(float(w[g]), 4), etfs={m: round(1 / len(v['members']), 4) for m in v['members']},
                               overlay_etfs={pick: 1.0}, premiums=prem)
        else:
            holdings[g] = dict(weight=round(float(w[g]), 4), etfs={m: round(1 / len(v['members']), 4) for m in v['members']})
    rec = dict(weights_betatilt={g: round(float(w_tilt[g]), 4) for g in w.index}, month=month, signal_date=str(gr.index[-1].date()), rule='main: IVOL60 across 8 groups on pool ETFs; tracked variant: lowest-premium sleeves (1% hysteresis)', capital=1_000_000,
               holdings=holdings, created_at=dt.datetime.now().isoformat(timespec='seconds'))
    with LEDGER.open('a') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(json.dumps({g: (h['weight'], list(h['etfs'])) for g, h in holdings.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
