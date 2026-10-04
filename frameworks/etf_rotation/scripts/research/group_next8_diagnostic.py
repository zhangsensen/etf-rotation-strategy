#!/usr/bin/env python3
"""Reproduce breadth-only diagnostics without evaluating or changing formulas."""
from __future__ import annotations

import argparse
from functools import partial
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'frameworks/etf_rotation/src'))
from etf_strategy.core.etf_mining_referee import newey_west_t_calendar

read_csv = partial(pd.read_csv, float_precision='round_trip')
RUN_NAMES = (
    'group_daily_v1_batch_20260922', 'group_minute_v1_batch_20260922',
    'group_share_v1_loaderfix_20260922', 'group_self_state_v1_batch_20260922',
    'group_nav_v1_loaderfix_20260922', 'group_interaction_v1_batch_20260922',
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default='runtime_outputs/etf_rotation_research/group_next8_20260922_v4/diagnostics')
    args = ap.parse_args()
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=False)
    v4 = ROOT / 'runtime_outputs/etf_rotation_research/group_next8_20260922_v4'
    runs = ROOT / 'runtime_outputs/etf_rotation_research/runs'
    new_metrics = read_csv(v4/'daily_metrics.csv', parse_dates=['signal_date']).set_index('signal_date')
    new_scores = {n: read_csv(v4/f'scores_{n}.csv', index_col=0, parse_dates=True)
                  for n in ('breadth_5', 'breadth_20')}
    new_valid = {n: new_metrics.loc[new_metrics.candidate.eq(n), 'ic'].notna()
                 for n in new_scores}
    old_files = []
    for metrics_path in (runs / name / 'daily_metrics.csv' for name in RUN_NAMES):
        run = metrics_path.parent
        if 'pilot' in run.name:
            continue
        metrics = read_csv(metrics_path, parse_dates=['signal_date']).set_index('signal_date')
        for candidate in metrics.candidate.drop_duplicates():
            score_path = run / f'scores_{candidate}.csv'
            if score_path.exists():
                old_files.append((run.name, candidate, metrics[metrics.candidate.eq(candidate)], score_path))
    assert len(old_files) == 80, 'frozen reference must contain exactly80 candidates'
    corr_rows = []
    for new_name, new_score in new_scores.items():
        for run_name, candidate, old_metric, score_path in old_files:
            old_score = read_csv(score_path, index_col=0, parse_dates=True)
            common = new_score.index.intersection(old_score.index)
            mask = new_valid[new_name].reindex(common, fill_value=False) & old_metric['ic'].reindex(common).notna()
            common = common[mask.reindex(common, fill_value=False)]
            row_corr = new_score.loc[common].rank(axis=1).corrwith(
                old_score.loc[common].rank(axis=1), axis=1)
            corr_rows.append({'breadth_candidate': new_name, 'old_run': run_name,
                              'old_candidate': candidate, 'n_common_metric': len(common),
                              'rank_corr_mean': float(row_corr.mean()) if len(row_corr) else None,
                              'rank_corr_abs_mean': float(row_corr.abs().mean()) if len(row_corr) else None,
                              'dedup_fail_abs_mean_ge_0.7': bool(len(row_corr) and row_corr.abs().mean() >= .7)})
    pd.DataFrame(corr_rows).sort_values(['breadth_candidate', 'rank_corr_abs_mean'], ascending=[True, False]).to_csv(out/'breadth_vs_existing80_rank_corr.csv', index=False)

    baselines = ['momentum_5', 'efficiency_5', 'range_expansion_5']
    base_run = runs/'group_daily_v1_batch_20260922'
    old_metrics = read_csv(base_run/'daily_metrics.csv', parse_dates=['signal_date']).set_index('signal_date')
    calendar = pd.DatetimeIndex(read_csv(v4/'coverage.csv', parse_dates=['signal_date']).signal_date)
    calendar = calendar[(calendar >= '2025-01-01') & (calendar <= '2026-09-17')]
    rows = []
    for breadth in ('breadth_5', 'breadth_20'):
        a = new_metrics[new_metrics.candidate.eq(breadth)]
        for baseline in baselines:
            b = old_metrics[old_metrics.candidate.eq(baseline)]
            common = a.index.intersection(b.index)
            mask = a['ic'].reindex(common).notna() & b['ic'].reindex(common).notna()
            common = common[mask]
            for metric in ('ic', 'excess8'):
                diff = (a.loc[common, metric] - b.loc[common, metric]).dropna()
                aligned = diff.reindex(calendar)
                rows.append({'breadth_candidate': breadth, 'baseline': baseline, 'metric': metric,
                             'n_common_metric': int(diff.notna().sum()), 'mean': float(diff.mean()),
                             'hac_t': float(newey_west_t_calendar(aligned, calendar, 10))})
    pd.DataFrame(rows).to_csv(out/'breadth_vs_baselines_paired.csv', index=False)
    print(f'wrote {out}/breadth_vs_existing80_rank_corr.csv and breadth_vs_baselines_paired.csv')


if __name__ == '__main__':
    main()
