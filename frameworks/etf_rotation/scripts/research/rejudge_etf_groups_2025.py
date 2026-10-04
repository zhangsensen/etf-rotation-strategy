#!/usr/bin/env python3
"""Replay frozen 80 group scores/labels on the user-specified 2025+ surface."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'frameworks/etf_rotation/src'))
from etf_strategy.core import etf_group_discovery as engine
from etf_strategy.core import etf_group_interactions as interaction
from etf_strategy.core import etf_mining_referee as referee

START = '2025-01-01'
END = '2026-09-17'
RUNS = ['group_daily_v1_batch_20260922', 'group_minute_v1_batch_20260922',
        'group_share_v1_loaderfix_20260922', 'group_self_state_v1_batch_20260922',
        'group_nav_v1_loaderfix_20260922', 'group_interaction_v1_batch_20260922']
VALUE_COLS = ['ic', 'selected', 'b8', 'b14', 'excess8', 'excess14', 'allocation_effect']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def window(frame, start, end):
    """Keep full calendar; purge labels exiting beyond the window end."""
    out = frame.loc[start:end].copy()
    invalid = out.exit_date.isna() | out.exit_date.gt(pd.Timestamp(end))
    out.loc[invalid, [c for c in VALUE_COLS if c in out]] = np.nan
    return out


def score_metrics(score, labels, reference, k):
    """Same-date comparisons; original batch coverage remains binding."""
    score = score.reindex(index=reference.index, columns=labels.columns)
    labels = labels.reindex(reference.index)
    valid = reference.ic.notna() & score.notna().all(axis=1) & labels.notna().all(axis=1)
    weights = referee.fractional_topk_weights(score, k, min_names=len(labels.columns)) / k
    selected = (weights * labels.fillna(0)).sum(axis=1)
    return pd.DataFrame({
        'ic': score.rank(axis=1).corrwith(labels.rank(axis=1), axis=1).where(valid),
        'excess8': (selected - labels.mean(axis=1)).where(valid)}, index=reference.index)


def layers(row, screens, cap):
    coverage = row['n'] >= screens['min_days']
    gates = {'ic': row['ic_mean'] >= screens['min_ic'],
             'hac': row['ic_hac_t'] >= screens['min_ic_hac_t'],
             'block': row['ic_block_t'] >= screens['min_ic_block_t'],
             'years': row['all_eligible_years_positive'] and row['positive_years'] >= screens['min_positive_years'],
             'leave_group': row['min_leave_group_ic'] > 0}
    return {'coverage_status': 'SUFFICIENT' if coverage else 'INSUFFICIENT',
            'ranking_metrics_pass': all(gates.values()),
            'ranking_supported': coverage and all(gates.values()),
            'ranking_failures': ','.join(k for k, v in gates.items() if not v),
            'economic_metrics_pass': row['excess8_mean'] > 0 and row['excess8_hac_t'] >= screens['min_excess8_hac_t'],
            'budget_diagnostic_pass': row['ic_p_normal_one_sided'] <= screens['alpha'] / cap}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id', required=True)
    args = ap.parse_args()
    if not args.run_id.replace('_', '').isalnum():
        raise ValueError('invalid run-id')
    base = ROOT / 'runtime_outputs/etf_rotation_research'
    out = base / 'rejudgments' / args.run_id
    inputs, plans = {}, {}
    for name in RUNS:
        run = base / 'runs' / name
        plan = json.loads((run / 'PLAN.json').read_text())
        cfg = plan['config']
        assert (cfg['horizon'], cfg['entry_lag'], cfg['top_k'], cfg['as_of']) == (5, 2, 2, END)
        assert cfg['budget_cap'] == 96
        assert json.loads((run / 'future_leak_check.json').read_text())['all_pass']
        for filename, digest in plan['source_hashes'].items():
            assert sha(run / 'source' / Path(filename).name) == digest
        paths = list(run.glob('scores_*.csv')) + [run / p for p in (
            'PLAN.json', 'daily_metrics.csv', 'coverage.csv', 'group_labels.csv',
            'summary.csv', 'future_leak_check.json', 'source/etf_candidate14_economic_groups_v1.yaml')]
        for path in paths:
            inputs[str(path)] = sha(path)
        plans[name] = plan
    assert sum(len(p['evaluated_ids']) for p in plans.values()) == 80
    out.mkdir(parents=True, exist_ok=False)
    sources = [Path(__file__), Path(engine.__file__), Path(interaction.__file__), Path(referee.__file__)]
    for path in sources:
        (out / path.name).write_bytes(path.read_bytes())
    manifest = {'start': START, 'end': END, 'scope': 'fixed14/eight_groups/H5/K2',
                'purpose': 'USER_WINDOW_CORRECTION_SEEN_HISTORY_NOT_CONFIRMATION',
                'new_formulas': 0, 'evaluated': 80, 'budget_diagnostic_denominator': 96,
                'primary_return_benchmark': 'B8', 'mandatory_comparator': 'B14',
                'coverage_rule': 'unchanged 360 days; insufficient is not mechanism failure',
                'search_note': 'Surface reuse recorded; no new formula budget. Prior adaptive search not erased.',
                'input_hashes': inputs, 'source_hashes': {str(p): sha(p) for p in sources},
                'command': sys.argv}
    (out / 'PLAN.json').write_text(json.dumps(manifest, indent=2) + '\n')
    rows, years, omissions, pairs, profiles = [], [], [], [], []
    for name, plan in plans.items():
        run = base / 'runs' / name
        cfg = plan['config']
        groups = yaml.safe_load((run / 'source/etf_candidate14_economic_groups_v1.yaml').read_text())['groups']
        assert len(groups) == 8 and len({s for g in groups.values() for s in g['members']}) == 14
        labels = pd.read_csv(run / 'group_labels.csv', index_col=0, parse_dates=True, float_precision='round_trip')
        metrics = pd.read_csv(run / 'daily_metrics.csv', parse_dates=['signal_date', 'entry_date', 'exit_date'], float_precision='round_trip')
        old = pd.read_csv(run / 'summary.csv', float_precision='round_trip').set_index('candidate')
        calendar = pd.DatetimeIndex(pd.read_csv(run / 'coverage.csv', parse_dates=['signal_date']).signal_date)
        eval_calendar = calendar[(calendar >= START) & (calendar <= END)]
        assert set(metrics.candidate) == set(plan['evaluated_ids']) == set(old.index)
        for candidate in plan['evaluated_ids']:
            frame = metrics.loc[metrics.candidate.eq(candidate)].set_index('signal_date').reindex(calendar)
            valid = frame.ic.notna()
            assert ((frame.loc[valid].index < frame.loc[valid, 'entry_date']) &
                    (frame.loc[valid, 'entry_date'] < frame.loc[valid, 'exit_date'])).all()
            assert np.allclose(frame.loc[valid, 'excess8'] + frame.loc[valid, 'allocation_effect'], frame.loc[valid, 'excess14'])
            score = pd.read_csv(run / f'scores_{candidate}.csv', index_col=0, parse_dates=True, float_precision='round_trip')
            replay = score_metrics(score, labels, frame, cfg['top_k'])
            np.testing.assert_allclose(replay.ic, frame.ic, atol=1e-12, equal_nan=True)
            np.testing.assert_allclose(replay.excess8, frame.excess8, atol=1e-12, equal_nan=True)
            # Prove the unchanged summary primitives reproduce the old evaluation.
            old_calendar = calendar[calendar >= cfg['start']]
            old_stats = engine.summarize(frame.reindex(old_calendar), old_calendar, cfg['hac_lag'])
            for key in ('n', 'ic_mean', 'ic_hac_t', 'ic_block_t', 'excess8_hac_t'):
                np.testing.assert_allclose(old_stats[key], old.loc[candidate, key], atol=1e-10)
            new = window(frame, START, END)
            row = {'candidate': candidate, 'run': name, 'source_type': cfg.get('source_type', 'daily'),
                   **engine.summarize(new, eval_calendar, cfg['hac_lag'])}
            dates = new.index[new.ic.notna()]
            row.update(first_signal=str(dates.min().date()), last_signal=str(dates.max().date()))
            year_stats = []
            for year in (2025, 2026):
                part = window(new, f'{year}-01-01', f'{year}-12-31')
                stats = engine.summarize(part, part.index, cfg['hac_lag'])
                years.append({'candidate': candidate, 'year': year, **stats})
                if stats['n'] >= cfg['screens']['min_year_days']:
                    year_stats.append(stats)
            row['positive_years'] = sum(s['ic_mean'] > 0 for s in year_stats)
            row['all_eligible_years_positive'] = bool(year_stats) and all(s['ic_mean'] > 0 for s in year_stats)
            profile = window(frame, cfg['start'], '2024-12-31')
            profiles.append({'candidate': candidate, **engine.summarize(profile, profile.index, cfg['hac_lag'])})
            parent_scores = {}
            if cfg.get('source_type') == 'interaction':
                mechanism = candidate.removesuffix('_1')
                for side in ('left', 'right'):
                    definition = cfg['mechanisms'][mechanism][side]
                    path = base / 'runs' / definition['parent_run'] / f"scores_{definition['parent_candidate']}.csv"
                    assert str(path) in inputs
                    # Match the frozen interaction loader's parser when reconstructing its legs.
                    parent = pd.read_csv(path, index_col=0, parse_dates=True).reindex(calendar)
                    # Reproduce the original expand-then-aggregate arithmetic too:
                    # a six-member mean can alter machine-precision near ties.
                    expanded = pd.DataFrame({s: parent[g] for g, d in groups.items() for s in d['members']})
                    parent_scores[mechanism + '__' + side] = engine.aggregate(expanded, groups)
                    leg = score_metrics(parent_scores[mechanism + '__' + side], labels, new, cfg['top_k'])
                    pairs.append({'candidate': candidate, 'side': side, **interaction.paired_increment(new, leg, eval_calendar, cfg['hac_lag'])})
                composed = (parent_scores[mechanism+'__left'].rank(axis=1, pct=True) *
                            parent_scores[mechanism+'__right'].rank(axis=1, pct=True))
                expanded = pd.DataFrame({s: composed[g] for g, d in groups.items() for s in d['members']})
                reconstructed = engine.aggregate(expanded, groups).where(
                    parent_scores[mechanism+'__left'].notna().all(axis=1) &
                    parent_scores[mechanism+'__right'].notna().all(axis=1), axis=0)
                np.testing.assert_allclose(reconstructed.reindex_like(score), score, atol=1e-14, equal_nan=True)
                pp = pairs[-2:]
                row['paired_metrics_pass'] = all(p[m+'_increment_mean'] > 0 and p[m+'_increment_hac_t'] >= cfg['paired_min_hac_t'] for p in pp for m in ('ic', 'excess8'))
                row['paired_coverage_pass'] = all(p[m+'_n'] >= cfg['screens']['min_days'] for p in pp for m in ('ic', 'excess8'))
            else:
                row.update(paired_metrics_pass=True, paired_coverage_pass=True)
            means = []
            for group in groups:
                reduced = interaction.leave_group_score(parent_scores, mechanism, group) if parent_scores else score.drop(columns=group)
                ic = reduced.reindex(eval_calendar).rank(axis=1).corrwith(labels.drop(columns=group).reindex(eval_calendar).rank(axis=1), axis=1).where(new.ic.notna())
                means.append(float(ic.mean()))
                omissions.append({'candidate': candidate, 'omitted_group': group, 'n': int(ic.notna().sum()), 'ic_mean': float(ic.mean()), 'ic_hac_t': referee.newey_west_t_calendar(ic, eval_calendar, cfg['hac_lag'])})
            row['min_leave_group_ic'] = min(means)
            row.update(layers(row, cfg['screens'], cfg['budget_cap']))
            row['ranking_and_economic_supported'] = row['ranking_supported'] and row['economic_metrics_pass'] and row['paired_metrics_pass'] and row['paired_coverage_pass']
            row['all_layers_supported'] = row['ranking_and_economic_supported'] and row['budget_diagnostic_pass']
            row['evidence_status'] = 'INSUFFICIENT_COVERAGE' if row['coverage_status'] == 'INSUFFICIENT' else ('LEAD_ONLY' if row['ranking_supported'] else 'NOT_SUPPORTED_THIS_SCREEN')
            for key in ('n', 'ic_mean', 'ic_hac_t', 'ic_block_t', 'excess8_mean', 'excess8_hac_t', 'excess14_mean', 'excess14_hac_t', 'failed_screens'):
                row['old_' + key] = old.loc[candidate, key]
            rows.append(row)
        print(f'{name}: {len(plan["evaluated_ids"])} replayed', flush=True)
    assert {p: sha(Path(p)) for p in inputs} == inputs
    summary = pd.DataFrame(rows)
    summary.to_csv(out / 'comparison.csv', index=False)
    for filename, records in [('yearly', years), ('leave_group', omissions), ('paired_increment', pairs), ('profile_2023_2024', profiles)]:
        pd.DataFrame(records).to_csv(out / f'{filename}.csv', index=False)
    verdict = {'evaluated': len(rows), 'insufficient_coverage': int(summary.coverage_status.eq('INSUFFICIENT').sum()),
               **{key: int(summary[key].sum()) for key in ('ranking_metrics_pass', 'ranking_supported', 'economic_metrics_pass', 'ranking_and_economic_supported', 'budget_diagnostic_pass', 'all_layers_supported')},
               'certified_factors': 0, 'old_metrics_reproduced': True, 'scores_and_inputs_unchanged': True,
               'source_vintages': 'NOT_CERTIFIED', 'external_shelf_increment': 'NOT_TESTED'}
    (out / 'verdict.json').write_text(json.dumps(verdict, indent=2) + '\n')
    lines = ['# 80条八组因子：2025起历史重判', '',
             '固定14只ETF／八组，信号2025-01-01起，标签退出不晚于2026-09-17；D+2→D+7，K=2。',
             'B8为收益主基准，B14并列；全部是已见历史，不是独立确认。公式、方向和历史覆盖掩码不变。',
             '2023–24只画像，年度统计按退出日剔除跨年标签。覆盖门360日不变。',
             '排序、经济增量、96预算校正分层报告；交互额外要求对两腿的配对增量。',
             '排序支持不等于最终短名单：跨批货架去重、增量与来源PIT认证仍未完成。',
             '不同批次有效日期不同，不用跨批t大小代替配对比较。', '',
             '```json', json.dumps(verdict, indent=2), '```', '',
             '|候选|N|块数|IC|HAC t|B8超额bp|B8 t|B14超额bp|覆盖|排序门|预算校正|',
             '|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|']
    for r in rows:
        lines.append(f"|{r['candidate']}|{r['n']}|{r['ic_blocks']}|{r['ic_mean']:.4f}|{r['ic_hac_t']:.2f}|{r['excess8_mean']*1e4:.1f}|{r['excess8_hac_t']:.2f}|{r['excess14_mean']*1e4:.1f}|{r['coverage_status']}|{r['ranking_metrics_pass']}|{r['budget_diagnostic_pass']}|")
    lines += ['', '复现：`uv run --no-sync python frameworks/etf_rotation/scripts/research/rejudge_etf_groups_2025.py --run-id <new-id>`',
              '证据：PLAN.json、comparison.csv、yearly.csv、leave_group.csv、paired_increment.csv、profile_2023_2024.csv。']
    (out / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(verdict, indent=2))


if __name__ == '__main__':
    main()
