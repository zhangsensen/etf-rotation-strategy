"""ETF label maturity and current-pool reporting contracts (no outcome selection)."""
from __future__ import annotations

import pandas as pd


def label_calendar(index: pd.DatetimeIndex, horizon: int, lag: int) -> pd.DataFrame:
    index = pd.DatetimeIndex(index)
    if horizon < 1 or lag < 1:
        raise ValueError('horizon and entry lag must be positive')
    if not index.is_unique or not index.is_monotonic_increasing or index.hasnans:
        raise ValueError('trading calendar must be unique, sorted and nonmissing')
    dates = pd.Series(index, index=index)
    # Forward shifts describe LABEL endpoints, never feature availability.
    return pd.DataFrame({'entry_date': dates.shift(-lag), 'exit_date': dates.shift(-(lag + horizon))})


def mature_surface(calendar: pd.DataFrame, start, end) -> pd.Series:
    end = pd.Timestamp(end)
    dates = calendar.index
    mask = calendar.exit_date.notna() & calendar.entry_date.notna()
    mask &= calendar.entry_date.gt(dates) & calendar.exit_date.ge(calendar.entry_date)
    mask &= (dates <= end) & calendar.exit_date.le(end)
    if start is not None:
        if pd.Timestamp(start) > end:
            raise ValueError('surface start is after end')
        mask &= dates >= pd.Timestamp(start)
    return mask.astype(bool)


def research_surfaces(index, horizons, lag, surfaces):
    discovery_end = pd.Timestamp(surfaces['discovery_end'])
    audit_start = pd.Timestamp(surfaces['seen_audit_start'])
    audit_end = pd.Timestamp(surfaces['seen_audit_end'])
    if not discovery_end < audit_start <= audit_end:
        raise ValueError('discovery and audit surfaces must be ordered and disjoint')
    calendars, discovery, audit = {}, {}, {}
    for horizon in horizons:
        calendars[horizon] = label_calendar(index, horizon, lag)
        discovery[horizon] = mature_surface(calendars[horizon], None, discovery_end)
        audit[horizon] = mature_surface(calendars[horizon], audit_start, audit_end)
    return calendars, discovery, audit


def consumption_contract(calendars, discovery, audit):
    result = {}
    for h, calendar in calendars.items():
        row = {}
        for name, mask in [('discovery', discovery[h]), ('seen_audit', audit[h])]:
            selected = calendar.loc[mask]
            row[name] = {
                'calendar_signal_days': int(mask.sum()),
                'first_signal_date': None if selected.empty else str(selected.index.min().date()),
                'last_signal_date': None if selected.empty else str(selected.index.max().date()),
                'label_consumption_end': None if selected.empty else str(selected.exit_date.max().date()),
            }
        result[str(h)] = row
    return result


def population_report(eligibility, universe, discovery_mask, audit_mask):
    rows = []
    metadata = {row['ts_code']: row for row in universe['etfs']}
    for symbol in eligibility:
        valid = eligibility[symbol].fillna(False)
        selected = valid.index[valid]
        row = metadata[symbol]
        rows.append({
            'symbol': symbol,
            'first_eligible_date': None if selected.empty else str(selected.min().date()),
            'discovery_eligible_days': int((valid & discovery_mask).sum()),
            'seen_audit_eligible_days': int((valid & audit_mask).sum()),
            'risk_family': row.get('risk_family'),
            'known_overlap_with': row.get('known_overlap_with', []),
        })
    return {
        'historical_population_kind': 'current_pool_retrospective_not_pit_membership',
        'classification_effective_from': universe.get('classification_effective_from'),
        'classification_revision': universe.get('classification_revision'),
        'maintenance_count': len(universe['etfs']),
        'ranking_symbol_count': len(eligibility.columns),
        'symbol_eligibility': rows,
        'eligibility_counts_are_not_label_pair_counts': True,
        'holdings_overlap_is_not_independence': True,
    }


def width_diagnostics(ic, pairs, eligibility_counts, masks, *, min_pairs=8, ranking_size=14):
    rows = []
    buckets = {str(min_pairs): eligibility_counts.eq(min_pairs)}
    if ranking_size > min_pairs + 1:
        buckets[f'{min_pairs+1}-{ranking_size-1}'] = eligibility_counts.between(min_pairs+1, ranking_size-1)
    if ranking_size > min_pairs:
        buckets[str(ranking_size)] = eligibility_counts.eq(ranking_size)
    for surface, mask in masks.items():
        for bucket, width_mask in buckets.items():
            values = ic.where(mask & width_mask).dropna()
            rows.append({'surface': surface, 'eligible_width_bucket': bucket,
                         'valid_ic_days': len(values), 'mean_ic': float(values.mean()),
                         'mean_actual_pairs': float(pairs.reindex(values.index).mean())})
    return rows
