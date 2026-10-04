#!/usr/bin/env python3
"""Report overlap of saved basic IC leads; never remove a lead or refit a factor."""
import argparse
from itertools import combinations
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'frameworks/etf_rotation/src'))
from etf_strategy.core.etf_rank_utils import stable_rank


def resolve_run(value):
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path if len(path.parts) > 1 else ROOT / 'runtime_outputs/etf_rotation_research/runs' / path


def compare_scores(left, right):
    if set(left.columns) != set(right.columns) or len(left.columns) != 8:
        raise ValueError('both scores must contain the same fixed eight groups')
    dates = left.index.intersection(right.index).sort_values()
    a, b = left.reindex(dates), right.reindex(index=dates, columns=left.columns)
    complete = a.notna().all(axis=1) & b.notna().all(axis=1)
    correlation = stable_rank(a.loc[complete]).corrwith(stable_rank(b.loc[complete]), axis=1).dropna()
    return {'common_rankable_days': len(correlation),
            'first_signal': str(correlation.index.min().date()) if len(correlation) else '',
            'last_signal': str(correlation.index.max().date()) if len(correlation) else '',
            'mean_abs_daily_rank_corr': float(correlation.abs().mean()) if len(correlation) else None,
            'mean_signed_daily_rank_corr': float(correlation.mean()) if len(correlation) else None,
            'redundancy_annotation': bool(len(correlation) and correlation.abs().mean() >= .7)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    leads_path = args.snapshot / 'basic_ic_leads.csv'
    leads = pd.read_csv(leads_path)
    frames, hashes = {}, {}
    for path in (leads_path, args.snapshot / 'manifest.json'):
        hashes[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
    for row in leads.to_dict('records'):
        run = resolve_run(row['evidence_source_run'])
        score_path = run / f'scores_{row["candidate"]}.csv'
        metrics_path = run / 'daily_metrics.csv'
        for path in (score_path, metrics_path):
            hashes[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
        scores = pd.read_csv(score_path, index_col=0, parse_dates=True)
        metrics = pd.read_csv(metrics_path, parse_dates=['signal_date'])
        valid_dates = metrics.loc[metrics.candidate.eq(row['candidate']) & metrics.ic.notna(), 'signal_date']
        if row['evidence_policy'] == '2025_DIRECTION_2026_HISTORICAL_SEGMENT':
            valid_dates = valid_dates[valid_dates.dt.year.eq(2026)]
        elif row['evidence_policy'] != 'PRIOR_DIRECTION_FULL_WINDOW':
            raise ValueError('unrecognized evaluation surface')
        frames[row['definition_id']] = scores.loc[scores.index.intersection(valid_dates)]
    pairs = []
    for left, right in combinations(leads.to_dict('records'), 2):
        pairs.append({'left_id': left['definition_id'], 'right_id': right['definition_id'],
                      'left': left['candidate'], 'right': right['candidate'],
                      **compare_scores(frames[left['definition_id']], frames[right['definition_id']])})
    pair_table = pd.DataFrame(pairs)
    notes = []
    for row in leads.to_dict('records'):
        linked = [p for p in pairs if row['definition_id'] in (p['left_id'], p['right_id'])
                  and p['mean_abs_daily_rank_corr'] is not None]
        nearest = max(linked, key=lambda p: p['mean_abs_daily_rank_corr']) if linked else None
        notes.append({**row, 'max_abs_rank_corr_with_basic_leads': nearest['mean_abs_daily_rank_corr'] if nearest else None,
                      'nearest_basic_lead': (nearest['right'] if nearest['left_id'] == row['definition_id'] else nearest['left']) if nearest else '',
                      'nearest_pair_days': nearest['common_rankable_days'] if nearest else 0,
                      'high_correlation_peer_count': sum(p['redundancy_annotation'] for p in linked),
                      'incremental_ic_status': 'NOT_TESTED', 'action': 'RETAIN_IC_REPORT_REDUNDANCY'})
    for path, digest in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError(f'saved input changed: {path}')
    args.output.mkdir(parents=True, exist_ok=False)
    pair_table.to_csv(args.output / 'pairs.csv', index=False)
    pd.DataFrame(notes).to_csv(args.output / 'leads.csv', index=False)
    manifest = {'scope': 'fixed14/eight_groups; saved basic IC leads only', 'leads': len(leads),
                'pairs': len(pairs), 'high_correlation_pairs': sum(p['redundancy_annotation'] for p in pairs),
                'threshold': .7, 'metric': 'mean(abs(per-date cross-sectional signed-score rank correlation))',
                'gate': 'REPORT_ONLY', 'removed_leads': 0, 'incremental_ic': 'NOT_TESTED',
                'input_hashes': hashes, 'command': [sys.executable, *sys.argv]}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    (args.output / 'README.md').write_text(
        f'# 基础IC线索重复性诊断\n\n{len(leads)}条线索，{len(pairs)}对比较，'
        f'{manifest["high_correlation_pairs"]}对平均绝对每日排名相关达到0.7。删除0条。\n\n'
        'leads.csv保留逐条IC、样本数、分年诊断和最近邻；pairs.csv保存每对共同日期数和相关性。'
        '按各自有效IC日期取交集，2025定向候选仅用2026。'
        '相关性用于注记，不代表组合增益、独立家族数量或实盘许可。\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='input_hashes'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
