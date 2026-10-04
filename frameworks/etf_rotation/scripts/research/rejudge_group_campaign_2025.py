#!/usr/bin/env python3
"""Re-judge the bounded eight-group campaign on the 2025-onward evaluation window.

No new candidate, formula, direction or threshold is introduced. The stored
per-date metrics of the existing runs are re-summarized on the window the user
fixed on 2026-09-21 (judge only from 2025; 2021-2024 is profiling, not a gate).
Mechanism screens and the multiple-testing screen are reported as separate
layers so a candidate that only fails Bonferroni stays visible.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT/'frameworks/etf_rotation'
sys.path.insert(0, str(ETF/'src'))
from etf_strategy.core import etf_group_discovery as engine  # noqa: E402

RUNS = ROOT/'runtime_outputs/etf_rotation_research/runs'


def loso_2025(run: Path, name: str, calendar: pd.DatetimeIndex, ic_valid: pd.Series) -> float:
    """Recompute leave-one-group-out mean IC on the restricted window."""
    score = pd.read_csv(run/f'scores_{name}.csv', index_col=0, parse_dates=True)
    labels = pd.read_csv(run/'group_labels.csv', index_col=0, parse_dates=True)
    labels = labels.reindex(score.index)
    out = []
    for g in score.columns:
        ss, yy = score.drop(columns=g), labels.drop(columns=g)
        ic = ss.rank(axis=1).corrwith(yy.rank(axis=1), axis=1)
        ic = ic.reindex(calendar).where(ic_valid.reindex(calendar).notna())
        out.append(float(ic.mean()))
    return min(out)


def main() -> None:
    raise SystemExit(
        'SUPERSEDED: this historical entry omitted coverage and paired-increment gates. '
        'Use rejudge_etf_groups_2025.py --run-id <new-id>; frozen80 v3 is authoritative. '
        'Original code below is retained for provenance, not execution.'
    )
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--start', default='2025-01-01')
    ap.add_argument('--config', default=str(ETF/'configs/group_discovery_daily_v1.yaml'))
    ap.add_argument('--out', default=str(ROOT/'runtime_outputs/etf_rotation_research/rejudge_2025'))
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    s, lag = cfg['screens'], cfg['hac_lag']
    start = pd.Timestamp(args.start)

    rows = []
    for run in sorted(RUNS.glob('*/daily_metrics.csv')):
        run = run.parent
        dm = pd.read_csv(run/'daily_metrics.csv', parse_dates=['signal_date', 'exit_date'])
        dm = dm[dm.signal_date >= start]
        if dm.empty:
            continue
        for name, frame in dm.groupby('candidate', sort=False):
            frame = frame.set_index('signal_date').sort_index()
            cal = frame.index
            row = {'candidate': name, 'run': run.name, **engine.summarize(frame, cal, lag)}
            valid = frame.ic.dropna()
            row['first_signal'] = str(valid.index.min().date()) if len(valid) else None
            row['last_signal'] = str(valid.index.max().date()) if len(valid) else None
            years = []
            for year in sorted(set(cal.year)):
                part = frame.loc[frame.index.year == year].copy()
                part.loc[part.exit_date.dt.year.ne(year),
                         ['ic', 'excess8', 'excess14', 'allocation_effect']] = pd.NA
                part[['ic', 'excess8', 'excess14', 'allocation_effect']] = part[
                    ['ic', 'excess8', 'excess14', 'allocation_effect']].astype(float)
                ys = engine.summarize(part, part.index, lag)
                if ys['n'] >= s['min_year_days']:
                    years.append(ys)
            row['eligible_years'] = len(years)
            row['positive_years'] = sum(y['ic_mean'] > 0 for y in years)
            row['all_eligible_years_positive'] = bool(years) and all(y['ic_mean'] > 0 for y in years)
            row['min_leave_group_ic'] = loso_2025(run, name, cal, frame.ic) \
                if (run/f'scores_{name}.csv').exists() else float('nan')
            rows.append(row)

    df = pd.DataFrame(rows)
    # A pilot replay re-evaluates a batch candidate unchanged; it is one hypothesis,
    # not two, so it must not inflate the multiple-testing denominator.
    dup = df.duplicated('candidate', keep=False)
    for name, part in df[dup].groupby('candidate'):
        if part.ic_hac_t.nunique() != 1 or part['n'].nunique() != 1:
            raise ValueError(f'duplicate candidate {name} differs between runs; cannot dedupe')
    df['replay_of_earlier_run'] = df.duplicated('candidate', keep='first')
    evaluated = int((~df.replay_of_earlier_run).sum())
    mech = {
        'ic': df.ic_mean >= s['min_ic'],
        'hac': df.ic_hac_t >= s['min_ic_hac_t'],
        'block': df.ic_block_t >= s['min_ic_block_t'],
        'economic': (df.excess8_mean > 0) & (df.excess8_hac_t >= s['min_excess8_hac_t']),
        'years': df.all_eligible_years_positive & (df.positive_years >= s['min_positive_years']),
        'leave_group': df.min_leave_group_ic > 0,
    }
    for k, v in mech.items():
        df['gate_'+k] = v
    df['mechanism_pass'] = pd.concat(mech.values(), axis=1).all(axis=1)
    df['failed_mechanism'] = [','.join(k for k, v in mech.items() if not v.iloc[i])
                              for i in range(len(df))]
    df['bonferroni_threshold'] = s['alpha']/evaluated
    df['multiple_testing_pass'] = df.ic_p_normal_one_sided <= df.bonferroni_threshold
    df['coverage_days'] = df['n']
    df['coverage_note'] = ['short_window' if n < s['min_days'] else 'ok' for n in df['n']]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df.sort_values('ic_hac_t', ascending=False).to_csv(out/'rejudged_candidates.csv', index=False)
    summary = {
        'evaluation_start': args.start,
        'evaluated_candidates': evaluated,
        'rows_including_replays': len(df),
        'mechanism_pass': int(df.mechanism_pass[~df.replay_of_earlier_run].sum()),
        'mechanism_and_multiple_testing_pass': int(
            (df.mechanism_pass & df.multiple_testing_pass)[~df.replay_of_earlier_run].sum()),
        'bonferroni_threshold': s['alpha']/evaluated,
        'window_rule': 'USER 2026-09-21: judge only from 2025; 2021-2024 profiling only',
        'changed_vs_original': 'evaluation window only; no new candidate, formula, direction or threshold',
        'coverage_note': 'min_days screen reported, not applied: the shorter window cannot meet a 360-day rule',
    }
    (out/'SUMMARY.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    cols = ['candidate', 'run', 'n', 'ic_mean', 'ic_hac_t', 'ic_block_t', 'excess8_mean',
            'excess8_hac_t', 'excess14_hac_t', 'positive_years', 'eligible_years',
            'min_leave_group_ic', 'mechanism_pass', 'multiple_testing_pass', 'failed_mechanism']
    print('\n=== ic_hac_t 前 15 ===')
    print(df.nlargest(15, 'ic_hac_t')[cols].to_string(index=False))


if __name__ == '__main__':
    main()
