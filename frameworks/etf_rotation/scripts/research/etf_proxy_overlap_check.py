#!/usr/bin/env python3
"""Proxy vs ETF overlap diagnostic (2023-08-01..cold line): per-group vol, daily corr,
annual return and average IVOL60 weight, proxies (etf_group_regime_longhistory.build) vs
pool ETFs. Written to runtime_outputs/etf_rotation_research/proxy_overlap_20260924/."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'frameworks/etf_rotation/src')); sys.path.insert(0, str(Path(__file__).resolve().parent))
import etf_group_regime_longhistory as base
from etf_strategy.canonical_data import load_canonical_daily


def main():
    gp = base.build()
    p = load_canonical_daily(Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1")), ROOT / 'config/etf_rotation_universe_v1.json', as_of=base.COLD, roles=('candidate',))
    groups = yaml.safe_load((ROOT / 'frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml').read_text())['groups']
    r = p['close'].pct_change(fill_method=None); ge = pd.DataFrame({g: r[v['members']].mean(axis=1) for g, v in groups.items()}).dropna()
    ix = gp.loc['2023-08-01':base.COLD].index.intersection(ge.index); x, y = gp.loc[ix], ge.loc[ix]
    w = lambda d: (1 / d.tail(60).std()) / (1 / d.tail(60).std()).sum()
    out = pd.DataFrame({'proxy_vol': x.std() * np.sqrt(252), 'etf_vol': y.std() * np.sqrt(252), 'daily_corr': x.corrwith(y),
                        'proxy_ann': (1 + x).prod() ** (252 / len(x)) - 1, 'etf_ann': (1 + y).prod() ** (252 / len(y)) - 1,
                        'ivol_w_proxy': pd.concat([w(x.iloc[:i]) for i in range(60, len(x), 20)], axis=1).mean(axis=1),
                        'ivol_w_etf': pd.concat([w(y.iloc[:i]) for i in range(60, len(y), 20)], axis=1).mean(axis=1)}).round(4)
    o = ROOT / 'runtime_outputs/etf_rotation_research/proxy_overlap_20260924'; o.mkdir(parents=True, exist_ok=True)
    out.to_csv(o / 'overlap.csv'); (o / 'meta.json').write_text(json.dumps({'start': str(ix[0].date()), 'end': str(ix[-1].date()), 'days': len(ix)}))
    print(out.to_string())


if __name__ == '__main__':
    main()
