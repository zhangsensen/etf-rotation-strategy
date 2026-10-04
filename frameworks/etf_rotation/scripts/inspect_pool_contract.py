#!/usr/bin/env python3
"""Inspect the frozen ETF pool and observable history without mining factors."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core.etf_factor_grammar import build_pit_eligibility
from etf_strategy.core.etf_research_contract import research_surfaces, population_report, consumption_contract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--canonical-data-root', type=Path, required=True)
    parser.add_argument('--universe-config', type=Path, required=True)
    parser.add_argument('--adjudication-config', type=Path, required=True)
    parser.add_argument('--as-of', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('output must be a new file')
    universe = json.loads(args.universe_config.read_text())
    config = yaml.safe_load(args.adjudication_config.read_text())
    cutoff = min(pd.Timestamp(args.as_of), pd.Timestamp(config['surfaces']['seen_audit_end']))
    panels = load_canonical_daily(args.canonical_data_root, args.universe_config,
                                 as_of=str(cutoff.date()), allow_future_only_symbols=True)
    all_eligible = build_pit_eligibility(panels, int(config['min_history_sessions']), bool(config['require_positive_volume']))
    symbols = [r['ts_code'] for r in universe['etfs'] if r['role'] in config['ranking_roles']]
    if len(symbols) != int(config['expected_ranking_symbols']):
        raise ValueError('ranking symbol count differs from the frozen contract')
    eligible = all_eligible[symbols]
    horizons = config['execution']['horizons']
    primary = config['execution']['primary_horizon']
    calendars, discovery, audit = research_surfaces(eligible.index, horizons, config['execution']['entry_lag_sessions'], config['surfaces'])
    report = population_report(eligible, universe, discovery[primary], audit[primary])
    report['effective_data_as_of'] = str(cutoff.date())
    report['label_consumption_calendar_only'] = consumption_contract(calendars, discovery, audit)
    report['maintained_symbol_coverage'] = []
    for row in universe['etfs']:
        prices = panels['close'][row['ts_code']].dropna()
        report['maintained_symbol_coverage'].append({
            'symbol': row['ts_code'], 'role': row['role'], 'observed_days': len(prices),
            'first_observed_date': None if prices.empty else str(prices.index.min().date()),
            'last_observed_date': None if prices.empty else str(prices.index.max().date()),
            'first_observed_is_not_inception_certificate': True,
        })
    report['input_config_hashes'] = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in [args.universe_config, args.adjudication_config]}
    report['status'] = 'pool_observation_only_no_factors_no_returns_no_ledger_write'
    report['command'] = sys.argv
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(f'ETF pool contract written: {args.output}')


if __name__ == '__main__':
    main()
