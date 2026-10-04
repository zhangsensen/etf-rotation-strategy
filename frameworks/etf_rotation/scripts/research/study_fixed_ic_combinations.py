#!/usr/bin/env python3
"""Separate historical combination study; original IC rules and inventory are read-only."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'frameworks/etf_rotation/src'))
from etf_strategy.core.etf_rank_utils import stable_rank
from etf_strategy.core.etf_mining_referee import newey_west_t_calendar, block_t_calendar

GROUPS = ['cn_technology_manufacturing', 'hk_technology', 'us_large_growth',
          'innovative_pharma', 'gold', 'metals_equity', 'dividend_low_vol', 'electric_power']


def read_prefix(path, cutoff):
    """Read a chronological saved CSV prefix, stopping at its first later date."""
    with Path(path).open() as handle:
        lines = [next(handle)]
        for line in handle:
            date = line.split(',', 1)[0].strip('"')
            if pd.Timestamp(date) > cutoff:
                break
            lines.append(line)
    return pd.read_csv(io.StringIO(''.join(lines)), index_col=0, parse_dates=True, float_precision='round_trip')


def rank_ic(score, labels):
    labels = labels.reindex(index=score.index, columns=score.columns)
    complete = score.notna().all(axis=1) & labels.notna().all(axis=1)
    return stable_rank(score).corrwith(labels.rank(axis=1, method='average'), axis=1).where(complete)


def statistics(values, calendar):
    x = values.reindex(calendar)
    block, blocks = block_t_calendar(x, calendar, 5)
    return {'n': int(x.notna().sum()), 'ic_mean': float(x.mean()),
            'ic_hac_t': newey_west_t_calendar(x, calendar, 10),
            'ic_block_t': block, 'ic_blocks': blocks}


def choose(single_ics, timing, month_start):
    # Selector parameters are specific to this combination study, not factor IC gates.
    mature = (single_ics.index < month_start) & timing.exit_date.reindex(single_ics.index).lt(month_start)
    train = single_ics.loc[mature]
    eligible = [c for c in train if train[c].count() >= 120]
    return sorted(eligible, key=lambda c: (-train[c].mean(), c)), train


def evaluate(scores, labels, timing, eligible_from, start='2026-01-01'):
    single = pd.DataFrame({name: rank_ic(s, labels).where(s.index >= eligible_from[name])
                           for name, s in scores.items()})
    ranks = {name: stable_rank(s) for name, s in scores.items()}
    test_dates = labels.index[labels.index >= pd.Timestamp(start)]
    daily = pd.DataFrame(index=test_dates, columns=['top2_equal_rank', 'training_best_single', 'eligible_pool_equal_rank'], dtype=float)
    selections = []
    score_rows = []
    for month in test_dates.to_period('M').unique():
        month_start = month.start_time
        ordered, train = choose(single, timing, month_start)
        dates = test_dates[test_dates.to_period('M') == month]
        selected = ordered[:2]
        selections.append({'month': str(month), 'selected': selected, 'eligible': ordered,
                           'training_label_max_exit': str(timing.reindex(train.index).exit_date.max()),
                           'training': {c: {'n': int(train[c].count()), 'ic': float(train[c].mean())} for c in ordered}})
        if len(selected) < 2:
            continue
        for method, names in [('top2_equal_rank', selected), ('training_best_single', selected[:1]),
                              ('eligible_pool_equal_rank', ordered)]:
            # No adaptive day-wise reweighting: any missing constituent invalidates the date.
            stacked = np.stack([ranks[c].reindex(dates).to_numpy() for c in names])
            combined = pd.DataFrame(stacked.mean(axis=0), index=dates, columns=GROUPS)
            daily.loc[dates, method] = rank_ic(combined, labels)
            if method == 'top2_equal_rank':
                score_rows.append(combined)
    return daily, selections, pd.concat(score_rows) if score_rows else pd.DataFrame(columns=GROUPS)


def null_labels(labels, seed):
    """Permute group identities per 20-session block, without moving future dates earlier."""
    rng = np.random.default_rng(seed)
    result = labels.copy()
    for left in range(0, len(labels), 20):
        result.iloc[left:left+20] = labels.iloc[left:left+20].to_numpy()[:, rng.permutation(8)]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    calendar_file = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1/1d/510300.SH.parquet"))
    calendar = pd.DatetimeIndex(pd.to_datetime(pd.read_parquet(calendar_file, columns=['trade_date']).trade_date)).sort_values()
    cold_line = calendar[-127]
    leads_file = args.inventory / 'basic_ic_leads.csv'
    leads = pd.read_csv(leads_file)
    protected = [leads_file, args.inventory / 'all_factors.csv', args.inventory / 'manifest.json',
                 args.inventory.parent / 'IC_INVENTORY_LATEST.json',
                 ROOT / 'frameworks/etf_rotation/src/etf_strategy/core/etf_rank_utils.py',
                 ROOT / 'frameworks/etf_rotation/src/etf_strategy/core/etf_mining_referee.py',
                 ROOT / 'frameworks/etf_rotation/src/etf_strategy/core/etf_group_evidence.py']
    protected_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    args.output.mkdir(parents=True, exist_ok=False)
    plan = {'layer': 'FACTOR_COMBINATION_RESEARCH_ONLY', 'user_request': '可以，但是不要改我ic的方式',
            'inventory': str(args.inventory), 'candidates': leads.candidate.tolist(),
            'cold_line': str(cold_line.date()), 'calendar_latest': str(calendar[-1].date()),
            'calendar_columns_read': ['trade_date'], 'training_start': '2025-01-01', 'evaluation_start': '2026-01-01',
            'selection': 'monthly top2 by expanding mature historical signed mean IC, >=120 valid training dates',
            'weights': 'equal weights of constituent cross-sectional ranks; fixed original directions',
            'comparators': ['training_best_single', 'eligible_pool_equal_rank'],
            'metric': 'original eight-group signed Rank IC; score significant digits 12; HAC lag10; calendar block5',
            'label': 'open(D+7)/open(D+2)-1', 'null': '20 fixed seeds; permute group identities in 20-session blocks; repeat selection',
            'pool_selection_bias': 'CURRENT_16_SELECTED_ON_FULL_SEEN_HISTORY; historical replay is not independent OOS',
            'primary_ic_policy_changed': False, 'inventory_writes': False, 'costs': 'not applicable; factor scores only',
            'protected_hashes_before': protected_hashes,
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'command': [sys.executable, *sys.argv]}
    (args.output / 'PLAN.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n')
    scores, eligible_from, provenance = {}, {}, {}
    labels = timing = None
    for row in leads.to_dict('records'):
        run = Path(row['evidence_source_run'])
        if not run.is_absolute():
            run = ROOT / run if len(run.parts) > 1 else ROOT / 'runtime_outputs/etf_rotation_research/runs' / run
        clock = read_prefix(run / 'coverage.csv', cold_line)
        for col in ('entry_date', 'exit_date'):
            clock[col] = pd.to_datetime(clock[col])
        allowed = clock.index[(clock.index >= pd.Timestamp('2025-01-01')) & clock.exit_date.le(cold_line)]
        last_signal = allowed.max()
        current_labels = read_prefix(run / 'group_labels.csv', last_signal).reindex(index=allowed, columns=GROUPS)
        clock = clock.reindex(allowed)
        assert (clock.entry_date > clock.index).all() and (clock.exit_date > clock.entry_date).all()
        if labels is None:
            labels, timing = current_labels, clock
        else:
            pd.testing.assert_frame_equal(labels, current_labels, check_exact=False, rtol=0, atol=1e-12)
            pd.testing.assert_series_equal(timing.exit_date, clock.exit_date)
        score_path = run / f'scores_{row["candidate"]}.csv'
        score = read_prefix(score_path, last_signal).reindex(index=allowed, columns=GROUPS)
        # Match the current saved-score rejudge exactly: complete scores/labels.
        # Legacy run-specific known_complete masks are not part of that IC method.
        scores[row['candidate']] = score
        eligible_from[row['candidate']] = pd.Timestamp('2026-01-01' if row['evidence_policy']=='2025_DIRECTION_2026_HISTORICAL_SEGMENT' else '2025-01-01')
        provenance[row['candidate']] = {'run': str(run), 'last_score_date_loaded': str(last_signal.date()),
                                       'last_label_exit': str(clock.exit_date.max().date()),
                                       'eligible_from': str(eligible_from[row['candidate']].date())}
    daily, selections, combined = evaluate(scores, labels, timing, eligible_from)
    common = daily.notna().all(axis=1)
    summary = []
    for method in daily:
        summary.append({'series': method, 'comparison': 'common_dates', **statistics(daily[method].where(common), daily.index)})
    for other in daily.columns[1:]:
        summary.append({'series': 'top2_minus_'+other, 'comparison': 'paired_common_dates',
                        **statistics((daily.top2_equal_rank-daily[other]).where(common), daily.index)})
    # The all-three common-date surface makes the predeclared comparison fair.
    null_rows = []
    for seed in range(20):
        null_daily, _, _ = evaluate(scores, null_labels(labels, seed), timing, eligible_from)
        null_rows.append({'seed': seed, **statistics(null_daily.top2_equal_rank.where(common), daily.index)})
    daily.to_csv(args.output / 'daily_ic.csv', index_label='signal_date')
    combined.to_csv(args.output / 'combined_scores.csv', index_label='signal_date')
    timing.reindex(daily.index).to_csv(args.output / 'timing.csv', index_label='signal_date')
    pd.DataFrame(summary).to_csv(args.output / 'summary.csv', index=False)
    pd.DataFrame(null_rows).to_csv(args.output / 'null.csv', index=False)
    (args.output / 'selections.json').write_text(json.dumps(selections, ensure_ascii=False, indent=2)+'\n')
    (args.output / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+'\n')
    monthly = []
    for month, part in daily.groupby(daily.index.to_period('M')):
        for method in part:
            monthly.append({'month': str(month), 'series': method, **statistics(part[method].where(common.reindex(part.index)), part.index)})
    pd.DataFrame(monthly).to_csv(args.output / 'monthly.csv', index=False)
    actual = summary[0]['ic_mean']
    null_means = np.array([r['ic_mean'] for r in null_rows])
    report = {**plan, 'first_evaluation_signal': str(daily.index.min().date()), 'last_evaluation_signal': str(daily.index.max().date()),
              'common_days': int(common.sum()), 'summary': summary, 'null_mean': float(null_means.mean()),
              'null_ge_observed_count': int((null_means>=actual).sum()), 'null_count': 20,
              'null_rank_p_diagnostic': float((1+(null_means>=actual).sum())/21),
              'verdict': 'HISTORICAL_EXPLORATORY_ONLY', 'new_factor_definitions_registered': 0}
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in protected_hashes.items())
    report['original_ic_files_and_inventory_unchanged'] = True
    (args.output / 'verdict.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
