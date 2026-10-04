#!/usr/bin/env python3
"""Same-index QDII ETF premium rotation, v2 after GPT-6-Sol review (2026-09-24).

Changes vs v1: premiums of all eligible ETFs are computed on ONE common NAV date d_t =
min over eligible ETFs of their latest NAV date with ann_date < t (every ETF valued on
the same d); holding that leaves the eligible set is switched to the cheapest; trades at
close t+1 with one-way cost in {10, 20, 30} bp; excess vs the pool ETF on common dates;
segments <= cold line (2026-03-24) and after (post-cold marked as already seen);
participation = 1m CNY / 20-session median turnover of the ETF held.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import qdii_premium_rotation as v1

Q = v1.Q; OUT = Q / 'v2'; COLD = '2026-03-24'; THETA = 0.01


def nav_table(codes):
    t = {}
    for c in codes:
        n = pd.read_parquet(Q / 'nav' / f'{c}.parquet'); n['nav_date'] = pd.to_datetime(n.nav_date); n['ann_date'] = pd.to_datetime(n.ann_date)
        t[c] = n.dropna(subset=['unit_nav']).sort_values(['nav_date', 'ann_date']).drop_duplicates('nav_date', keep='first')
    return t


def run(index, bench, cost):
    u = pd.read_csv(Q / 'universe.csv'); u = u[(u.idx == index) & ~u.name.str.contains('LOF|联接')]
    close, adjc, amt = v1.prices(u.ts_code.tolist()); codes = [c for c in u.ts_code if c in close.columns and (Q / 'nav' / f'{c}.parquet').exists()]
    close, adjc, amt = close[codes], adjc[codes], amt[codes]; cal = close.index; nav = nav_table(codes)
    listed = close.notna().cumsum() >= 60; liq = amt.rolling(60, min_periods=20).median() >= 1e7
    ret = adjc.pct_change(fill_method=None); amt20 = amt.rolling(20, min_periods=5).median()
    hold = None; held = []; switches = []; prem_log = []
    for t in cal:
        e = [c for c in codes if listed.at[t, c] and liq.at[t, c] and pd.notna(close.at[t, c])]
        latest = {c: nav[c][nav[c].ann_date < t].nav_date.max() for c in e}
        e = [c for c in e if pd.notna(latest[c])]
        if len(e) < 2:
            held.append(hold); continue
        d = min(latest[c] for c in e)
        prem = {}
        for c in e:
            row = nav[c][(nav[c].nav_date == d) & (nav[c].ann_date < t)]
            if len(row): prem[c] = close.at[t, c] / float(row.unit_nav.iloc[0]) - 1
        if len(prem) < 2:
            held.append(hold); continue
        best = min(prem, key=prem.get)
        if hold not in prem or prem[hold] - prem[best] > THETA:
            if hold != best: switches.append(dict(date=t, frm=hold, to=best, gap=(prem[hold] - prem[best]) if hold in prem else None, nav_date=d))
            hold = best
        prem_log.append(dict(date=t, held=hold, prem_held=prem.get(hold), prem_bench=prem.get(bench), prem_min=prem[best]))
        held.append(hold)
    held = pd.Series(held, index=cal).shift(2)   # decided at close t, bought at close t+1, earns t+1 -> t+2
    r = pd.Series([ret.at[dd, h] if isinstance(h, str) else np.nan for dd, h in held.items()], index=cal)
    sw = pd.Series(0.0, index=cal)
    for x in switches:
        pos = cal.get_loc(x['date']) + 2          # cost booked on the first return day of the new holding
        if pos < len(cal): sw.iloc[pos] += cost * (2 if x['frm'] else 1)
    strat = r - sw; b = ret[bench]
    both = strat.notna() & b.notna(); ex = (strat - b)[both]
    part = pd.Series([1e6 / amt20.at[dd, h] if isinstance(h, str) and amt20.at[dd, h] > 0 else np.nan for dd, h in held.items()], index=cal)
    def seg(a, z):
        e = ex.loc[a:z]; s_ = strat[both].loc[a:z]; bb = b[both].loc[a:z]; yrs = len(e) / 252
        if len(e) < 20: return None
        m = e.groupby(e.index.to_period('M')).sum()
        return dict(days=len(e), strat_ann=round(float((1 + s_).prod() ** (1 / yrs) - 1), 4), bench_ann=round(float((1 + bb).prod() ** (1 / yrs) - 1), 4),
                    excess_ann=round(float((1 + e).prod() ** (1 / yrs) - 1), 4), monthly_t=round(float(m.mean() / m.std() * np.sqrt(len(m))), 2), pos_months=round(float((m > 0).mean()), 2))
    pl = pd.DataFrame(prem_log).set_index('date')
    res = dict(index=index, bench=bench, cost_bp=cost * 1e4, first=str(ex.index[0].date()), to_cold=seg('2000-01-01', COLD), post_cold_seen=seg('2026-03-25', '2099-01-01'),
               switches=len(switches), switches_per_year=round(len(switches) / (len(ex) / 252), 1),
               mean_prem_held=round(float(pl.prem_held.mean()), 4), mean_prem_bench=round(float(pl.prem_bench.mean()), 4),
               participation_median=round(float(part.median()), 4), participation_p95=round(float(part.quantile(.95)), 4),
               yearly_excess={int(y): round(float(v), 4) for y, v in (1 + ex).groupby(ex.index.year).prod().sub(1).items()})
    return res, pd.DataFrame(switches)


def main():
    OUT.mkdir(parents=True, exist_ok=True); allr = {}
    for idx, bench in (('NDX', '513100.SH'), ('HST', '513130.SH'), ('SPX', '513500.SH')):
        for cost in (0.001, 0.002, 0.003):
            res, sw = run(idx, bench, cost); allr[f'{idx}_{int(cost*1e4)}bp'] = res
            if cost == 0.001: sw.to_csv(OUT / f'switches_{idx}.csv', index=False)
            print(f"{idx} {int(cost*1e4)}bp to_cold {res['to_cold']} | post {res['post_cold_seen']} | sw/yr {res['switches_per_year']} prem held {res['mean_prem_held']} vs {res['mean_prem_bench']} | part med {res['participation_median']} p95 {res['participation_p95']}")
        print('  yearly', allr[f'{idx}_10bp']['yearly_excess'])
    (OUT / 'results.json').write_text(json.dumps(allr, ensure_ascii=False, indent=1, default=str))


if __name__ == '__main__':
    main()
