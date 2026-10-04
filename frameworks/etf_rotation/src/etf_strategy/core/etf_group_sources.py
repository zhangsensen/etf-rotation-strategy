"""Causal minute aggregates and explicitly assumed-availability share features."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


MINUTE_NAMES = (
    'minute_late_return', 'minute_late_volume_share', 'minute_signed_volume',
    'minute_downside_ratio', 'minute_close_vwap', 'minute_path_efficiency',
    'minute_impact_asymmetry', 'minute_volume_entropy', 'minute_return_ar1_beta',
    'minute_range_persistence', 'minute_signed_flow_persistence', 'minute_range_skew',
    'minute_signed_flow_return_lead', 'minute_phase_return_curvature',
    'minute_turnover_return_corr', 'minute_range_turnover_corr',
    'minute_range_sign_asymmetry', 'minute_amount_sign_imbalance',
    'minute_amount_abs_return_concentration',
    'minute_early_daily_mean_return', 'minute_late_daily_mean_return',
    'minute_phase_range_migration', 'minute_phase_amount_migration',
    'minute_phase_abs_return_migration', 'minute_phase_return_path_persistence',
    'minute_phase_return_reversal', 'minute_phase_range_curvature',
    'minute_phase_amount_curvature', 'minute_phase_amount_abs_return_migration',
    'minute_phase_return_range_absorption', 'minute_phase_directional_range_shift',
    'minute_phase_directional_amount_shift', 'minute_gap_repair_phase',
    'minute_amount_price_impact', 'minute_amount_signed_impact',
    'minute_amount_directional_consistency', 'minute_amount_impact_late_share',
    'minute_amount_impact_phase_shift', 'minute_amount_impact_sign_transition',
    'minute_amount_reversal_impact_share', 'minute_amount_range_pressure',
    'minute_amount_return_range_absorption', 'minute_amount_impact_time_position',
    # Round2 (Batch24): finer intraday volume-shape states than the existing
    # 60/120/60 phase split or the single volume-entropy scalar. Bucket
    # boundaries are fixed bar timestamps (see minute_daily): opening 30
    # minutes = 09:31-10:00, closing 30 minutes = 14:31-15:00, midday =
    # 11:01-11:30 + 13:01-13:30. 'minute_volume_opening_share' and
    # 'minute_volume_closing_session_abs_return' are helper columns used only
    # by the return_concentration_lead cross-panel correlation below; they
    # are not separately registered as their own candidates in this batch.
    'minute_volume_u_shape_ratio', 'minute_volume_gini',
    'minute_volume_opening_absorption_speed', 'minute_volume_opening_share',
    'minute_volume_closing_session_abs_return', 'minute_volume_midday_share',
)
_BATCH14_MINUTE_ALIASES = {
    'd2025_minute_turnover_return_corr': ('minute_turnover_return_corr', 1),
    'd2025_minute_range_turnover_corr': ('minute_range_turnover_corr', 1),
}
_BATCH15_MINUTE_ALIASES = {
    'd2025_minute_range_sign_asymmetry': ('minute_range_sign_asymmetry', 1),
    'd2025_minute_amount_sign_imbalance': ('minute_amount_sign_imbalance', 1),
    'd2025_minute_amount_abs_return_concentration': (
        'minute_amount_abs_return_concentration', 1
    ),
    'd2025_minute_phase_signed_return_corr': ('minute_phase_signed_return_corr', 1),
}
_ALL_MINUTE_ALIASES = {**_BATCH14_MINUTE_ALIASES, **_BATCH15_MINUTE_ALIASES}
_BATCH16_MINUTE_ALIASES = {
    'd2025_minute_phase_range_migration': ('minute_phase_range_migration', -1),
    'd2025_minute_phase_amount_migration': ('minute_phase_amount_migration', -1),
    'd2025_minute_phase_abs_return_migration': ('minute_phase_abs_return_migration', -1),
    'd2025_minute_phase_return_path_persistence': ('minute_phase_return_path_persistence', 1),
    'd2025_minute_phase_return_reversal': ('minute_phase_return_reversal', 1),
    'd2025_minute_phase_range_curvature': ('minute_phase_range_curvature', -1),
    'd2025_minute_phase_amount_curvature': ('minute_phase_amount_curvature', -1),
    'd2025_minute_phase_amount_abs_return_migration': ('minute_phase_amount_abs_return_migration', -1),
    'd2025_minute_phase_return_range_absorption': ('minute_phase_return_range_absorption', 1),
    'd2025_minute_phase_directional_range_shift': ('minute_phase_directional_range_shift', -1),
    'd2025_minute_phase_directional_amount_shift': ('minute_phase_directional_amount_shift', -1),
    'd2025_minute_gap_repair_phase': ('minute_gap_repair_phase', 1),
}
_ALL_MINUTE_ALIASES = {**_ALL_MINUTE_ALIASES, **_BATCH16_MINUTE_ALIASES}
_BATCH17_MINUTE_ALIASES = {
    'd2025_minute_amount_price_impact': ('minute_amount_price_impact', 1),
    'd2025_minute_amount_signed_impact': ('minute_amount_signed_impact', 1),
    'd2025_minute_amount_directional_consistency': ('minute_amount_directional_consistency', 1),
    'd2025_minute_amount_impact_late_share': ('minute_amount_impact_late_share', -1),
    'd2025_minute_amount_impact_phase_shift': ('minute_amount_impact_phase_shift', -1),
    'd2025_minute_amount_impact_sign_transition': ('minute_amount_impact_sign_transition', 1),
    'd2025_minute_amount_reversal_impact_share': ('minute_amount_reversal_impact_share', -1),
    'd2025_minute_amount_range_pressure': ('minute_amount_range_pressure', 1),
    'd2025_minute_amount_return_range_absorption': ('minute_amount_return_range_absorption', 1),
    'd2025_minute_amount_impact_time_position': ('minute_amount_impact_time_position', -1),
}
_ALL_MINUTE_ALIASES = {**_ALL_MINUTE_ALIASES, **_BATCH17_MINUTE_ALIASES}
_BATCH24_MINUTE_ALIASES = {
    # Round2 (Batch24) Stage2: direction taken mechanically from the Stage1
    # 2025 IC sign (all three were negative), not from an independently
    # argued economic direction. See group_ic20_batch24_stage2_minute
    # config notes.
    'd2025_minute_volume_return_concentration_lead': ('minute_volume_return_concentration_lead', -1),
    'd2025_minute_volume_shape_persistence': ('minute_volume_shape_persistence', -1),
    'd2025_minute_volume_midday_share': ('minute_volume_midday_share', -1),
}
_ALL_MINUTE_ALIASES = {**_ALL_MINUTE_ALIASES, **_BATCH24_MINUTE_ALIASES}


# Round2 (Batch24): 20-calendar-day rolling window tolerance for halt-day
# gaps in the volume-shape family (see minute_daily's halted_open masking
# and build_atoms' minute branch below). Fixed by master's pre-label rule,
# not tuned after seeing any result.
_HALT_TOLERANT_MIN_PERIODS = 15


# Batch23 share-amount cross family (see build_atoms' share branch below).
_SHARE_AMOUNT_MECHANISMS = {
    'share_amount_flow_divergence_corr',
    'share_amount_tail_mismatch_rate',
    'share_flow_amount_signed_alignment',
    'share_lag_amount_abs_corr',
    'share_amount_ratio_dispersion',
    'share_flow_amount_conditional_asymmetry',
}


def minute_daily(raw, calendar):
    """Require all 240 right-edge bars; never pad or carry incomplete sessions."""
    f = raw.copy()
    f['datetime'] = pd.to_datetime(f.datetime)
    f = f.loc[f.datetime.dt.normalize().isin(calendar)].sort_values('datetime')
    if f.datetime.duplicated().any():
        raise ValueError('duplicate minute timestamps')
    if f.empty:
        return pd.DataFrame(index=calendar, columns=MINUTE_NAMES, dtype=float), {'complete_days':0}
    dates = f.datetime.dt.normalize()
    counts = dates.value_counts()
    f = f.loc[dates.map(counts).eq(240)]
    if f.empty:
        return pd.DataFrame(index=calendar, columns=MINUTE_NAMES, dtype=float), {
            'observed_days': int(len(counts)), 'complete_days': 0,
            'incomplete_or_invalid_days': int(len(counts)),
        }
    dates = f.datetime.dt.normalize()
    days = pd.DatetimeIndex(dates.drop_duplicates())
    fields = ['open','high','low','close','volume','turnover']
    x = f[fields].to_numpy(float).reshape(-1,240,6)
    times = (f.datetime.dt.hour*60+f.datetime.dt.minute).to_numpy().reshape(-1,240)
    expected = np.r_[np.arange(571,691),np.arange(781,901)]
    valid = (times==expected).all(axis=1) & np.isfinite(x).all(axis=(1,2))
    valid &= (x[:,:,:4]>0).all(axis=(1,2)) & (x[:,:,4:]>=0).all(axis=(1,2))
    valid &= (x[:,:,1]>=x[:,:,:4].max(axis=2)).all(axis=1)
    valid &= (x[:,:,2]<=x[:,:,:4].min(axis=2)).all(axis=1)
    o,h,l,c,v,a = [x[:,:,i] for i in range(6)]
    total_v, total_a = v.sum(axis=1), a.sum(axis=1)
    valid &= (total_v>0) & (total_a>0)
    with np.errstate(divide='ignore',invalid='ignore'):
        r = c/o-1
        rv = (r*r).sum(axis=1)
        downside = np.divide((np.minimum(r,0)**2).sum(axis=1), rv,
                             out=np.full(len(days),.5), where=rv>0)
        vwap = total_a/total_v
        valid &= (vwap>=l.min(axis=1)*.98) & (vwap<=h.max(axis=1)*1.02)
        path = np.abs(r).sum(axis=1)
        efficiency = np.divide(c[:,-1]/o[:,0]-1, path, out=np.zeros(len(days)), where=path>0)
        up = (r>0) & (a>0)
        down = (r<0) & (a>0)
        impact = np.divide(np.abs(r),a,out=np.zeros_like(r),where=a>0)
        up_i = np.divide((impact*up).sum(axis=1), up.sum(axis=1),out=np.zeros(len(days)),where=up.sum(axis=1)>0)
        down_i = np.divide((impact*down).sum(axis=1), down.sum(axis=1),out=np.zeros(len(days)),where=down.sum(axis=1)>0)
        denom = up_i+down_i
        asym = np.divide(up_i-down_i,denom,out=np.zeros(len(days)),where=denom>0)
        lagged = r[:, :-1]
        current = r[:, 1:]
        lagged_centered = lagged - lagged.mean(axis=1, keepdims=True)
        current_centered = current - current.mean(axis=1, keepdims=True)
        ar1_numerator = (lagged_centered * current_centered).sum(axis=1)
        ar1_denominator = (lagged_centered ** 2).sum(axis=1)
        ar1_beta = np.divide(
            ar1_numerator,
            ar1_denominator,
            out=np.full(len(days), np.nan),
            where=ar1_denominator > 0,
        )
        minute_range = (h-l)/c

        def lag1_corr(series):
            lag = series[:, :-1]
            now = series[:, 1:]
            lag_centered = lag - lag.mean(axis=1, keepdims=True)
            now_centered = now - now.mean(axis=1, keepdims=True)
            numerator = (lag_centered * now_centered).sum(axis=1)
            denominator = np.sqrt(
                (lag_centered ** 2).sum(axis=1)
                * (now_centered ** 2).sum(axis=1)
            )
            return np.divide(
                numerator,
                denominator,
                out=np.full(len(days), np.nan),
                where=denominator > 0,
            )

        def lead_corr(lagged_series, current_series):
            lag = lagged_series[:, :-1]
            now = current_series[:, 1:]
            lag_centered = lag - lag.mean(axis=1, keepdims=True)
            now_centered = now - now.mean(axis=1, keepdims=True)
            numerator = (lag_centered * now_centered).sum(axis=1)
            denominator = np.sqrt(
                (lag_centered ** 2).sum(axis=1)
                * (now_centered ** 2).sum(axis=1)
            )
            return np.divide(
                numerator,
                denominator,
                out=np.full(len(days), np.nan),
                where=denominator > 0,
            )

        range_persistence = lag1_corr(minute_range)
        signed_flow = np.sign(r) * a / total_a[:, None]
        signed_flow_persistence = lag1_corr(signed_flow)
        signed_flow_return_lead = lead_corr(signed_flow, r)
        range_mean = minute_range.mean(axis=1)
        range_centered = minute_range - range_mean[:, None]
        range_variance = (range_centered ** 2).mean(axis=1)
        range_third = (range_centered ** 3).mean(axis=1)
        range_skew = np.divide(
            range_third,
            range_variance ** 1.5,
            out=np.full(len(days), np.nan),
            where=range_variance > 0,
        )
        # Fixed 60/120/60 early/mid/late phases.  This is a shape state,
        # not a resampled or searched window.
        phase_early = r[:, :60].mean(axis=1)
        phase_middle = r[:, 60:180].mean(axis=1)
        phase_late = r[:, 180:].mean(axis=1)
        phase_return_curvature = 2.0 * phase_middle - phase_early - phase_late
        p = v/total_v[:,None]
        plogp = np.zeros_like(p)
        np.log(p,out=plogp,where=p>0)
        entropy = -(p*plogp).sum(axis=1)/np.log(240)

        # Batch 14 raw-library states use canonical turnover (amount), not
        # volume.  Both are complete-day states and use the exact 240 bars.
        amount_share = a/total_a[:, None]

        def full_day_corr(left, right):
            left_centered = left - left.mean(axis=1, keepdims=True)
            right_centered = right - right.mean(axis=1, keepdims=True)
            numerator = (left_centered * right_centered).sum(axis=1)
            denominator = np.sqrt(
                (left_centered ** 2).sum(axis=1)
                * (right_centered ** 2).sum(axis=1)
            )
            return np.divide(
                numerator,
                denominator,
                out=np.full(len(days), np.nan),
                where=denominator > 0,
            )

        turnover_return_corr = full_day_corr(amount_share, r)
        range_turnover_corr = full_day_corr(minute_range, amount_share)
        positive = r > 0
        nonpositive = ~positive
        range_sign_asymmetry = (
            np.divide((minute_range * positive).sum(axis=1), positive.sum(axis=1),
                      out=np.full(len(days), np.nan), where=positive.sum(axis=1) > 0)
            - np.divide((minute_range * nonpositive).sum(axis=1), nonpositive.sum(axis=1),
                        out=np.full(len(days), np.nan), where=nonpositive.sum(axis=1) > 0)
        )
        amount_sign_imbalance = (amount_share * positive).sum(axis=1) - (amount_share * nonpositive).sum(axis=1)
        amount_abs_return = amount_share * np.abs(r)
        amount_abs_return_total = amount_abs_return.sum(axis=1)
        amount_abs_return_concentration = np.divide(
            (amount_abs_return ** 2).sum(axis=1), amount_abs_return_total ** 2,
            out=np.full(len(days), np.nan), where=amount_abs_return_total > 0,
        )
        amount_price_impact = np.divide(
            amount_abs_return_total, np.ones(len(days)),
            out=np.zeros(len(days)), where=np.isfinite(amount_abs_return_total),
        )
        amount_signed_impact = np.divide(
            (amount_share * r).sum(axis=1), np.ones(len(days)),
            out=np.zeros(len(days)), where=np.isfinite((amount_share * r).sum(axis=1)),
        )
        amount_directional_consistency = np.divide(
            (amount_share * np.sign(r) * np.abs(r)).sum(axis=1),
            amount_abs_return_total,
            out=np.zeros(len(days)), where=amount_abs_return_total > 0,
        )
        phase_amount_abs_return = np.column_stack((
            amount_abs_return[:, :60].sum(axis=1),
            amount_abs_return[:, 60:180].sum(axis=1),
            amount_abs_return[:, 180:].sum(axis=1),
        ))
        impact_phase_share = np.divide(
            phase_amount_abs_return,
            amount_abs_return_total[:, None],
            out=np.zeros((len(days), 3)), where=amount_abs_return_total[:, None] > 0,
        )
        impact_late_share = impact_phase_share[:, 2]
        impact_phase_shift = impact_phase_share[:, 2] - impact_phase_share[:, 0]
        prior_sign = np.sign(r[:, :-1])
        current_sign = np.sign(r[:, 1:])
        sign_transition = (prior_sign != current_sign).astype(float)
        transition_amount = np.divide(
            (a[:, 1:] * sign_transition).sum(axis=1), total_a,
            out=np.zeros(len(days)), where=total_a > 0,
        )
        reversal_impact_share = np.divide(
            (a[:, 1:] * np.abs(r[:, 1:]) * sign_transition).sum(axis=1),
            (a * np.abs(r)).sum(axis=1),
            out=np.zeros(len(days)), where=(a * np.abs(r)).sum(axis=1) > 0,
        )
        amount_range_pressure = np.divide(
            (amount_share * minute_range).sum(axis=1), np.ones(len(days)),
            out=np.zeros(len(days)), where=np.isfinite((amount_share * minute_range).sum(axis=1)),
        )
        amount_return_range_absorption = np.divide(
            amount_abs_return_total, (amount_share * minute_range).sum(axis=1),
            out=np.zeros(len(days)), where=(amount_share * minute_range).sum(axis=1) > 0,
        )
        impact_time_position = np.divide(
            (amount_abs_return * np.arange(240)).sum(axis=1),
            amount_abs_return_total * 239.0,
            out=np.zeros(len(days)), where=amount_abs_return_total > 0,
        )
        phase_range = np.column_stack((
            minute_range[:, :60].mean(axis=1),
            minute_range[:, 60:180].mean(axis=1),
            minute_range[:, 180:].mean(axis=1),
        ))
        phase_amount = np.column_stack((
            amount_share[:, :60].sum(axis=1),
            amount_share[:, 60:180].sum(axis=1),
            amount_share[:, 180:].sum(axis=1),
        ))
        phase_abs_return = np.column_stack((
            np.abs(r[:, :60]).mean(axis=1),
            np.abs(r[:, 60:180]).mean(axis=1),
            np.abs(r[:, 180:]).mean(axis=1),
        ))
        phase_return = np.column_stack((
            r[:, :60].mean(axis=1),
            r[:, 60:180].mean(axis=1),
            r[:, 180:].mean(axis=1),
        ))
        phase_amount_abs_return = np.column_stack((
            amount_abs_return[:, :60].sum(axis=1),
            amount_abs_return[:, 60:180].sum(axis=1),
            amount_abs_return[:, 180:].sum(axis=1),
        ))
        with np.errstate(divide='ignore', invalid='ignore'):
            range_migration = np.divide(
                phase_range[:, 2] - phase_range[:, 0],
                phase_range[:, 2] + phase_range[:, 0],
                out=np.full(len(days), np.nan),
                where=(phase_range[:, 2] + phase_range[:, 0]) > 0,
            )
            abs_return_migration = np.divide(
                phase_abs_return[:, 2] - phase_abs_return[:, 0],
                phase_abs_return[:, 2] + phase_abs_return[:, 0],
                out=np.full(len(days), np.nan),
                where=(phase_abs_return[:, 2] + phase_abs_return[:, 0]) > 0,
            )
            amount_abs_return_migration = np.divide(
                phase_amount_abs_return[:, 2] - phase_amount_abs_return[:, 0],
                phase_amount_abs_return.sum(axis=1),
                out=np.full(len(days), np.nan),
                where=phase_amount_abs_return.sum(axis=1) > 0,
            )
            return_range_absorption = np.divide(
                phase_abs_return[:, 2], phase_abs_return[:, 2] + phase_range[:, 2],
                out=np.zeros(len(days)),
                where=(phase_abs_return[:, 2] + phase_range[:, 2]) > 0,
            ) - np.divide(
                phase_abs_return[:, 0], phase_abs_return[:, 0] + phase_range[:, 0],
                out=np.zeros(len(days)),
                where=(phase_abs_return[:, 0] + phase_range[:, 0]) > 0,
            )
        phase_sign = np.sign(phase_return)
        path_persistence = (phase_sign[:, 0] * phase_sign[:, 1]
                            + phase_sign[:, 1] * phase_sign[:, 2]) / 2.0
        # Zero phase means are a valid neutral path state, not missing data.
        reversal = ((phase_sign[:, 0] * phase_sign[:, 2]) < 0).astype(float)
        phase_range_curvature = 2.0 * phase_range[:, 1] - phase_range[:, 0] - phase_range[:, 2]
        phase_amount_curvature = 2.0 * phase_amount[:, 1] - phase_amount[:, 0] - phase_amount[:, 2]
        def directional_range(phase):
            ranges = minute_range[:, phase[0]:phase[1]]
            return np.divide(
                (ranges * np.sign(r[:, phase[0]:phase[1]])).sum(axis=1),
                ranges.sum(axis=1), out=np.zeros(len(days)),
                where=ranges.sum(axis=1) > 0,
            )
        def directional_amount(phase):
            up = r[:, phase[0]:phase[1]] > 0
            nonpositive = ~up
            shares = amount_share[:, phase[0]:phase[1]]
            return (shares * up).sum(axis=1) - (shares * nonpositive).sum(axis=1)
        early_directional_range = directional_range((0, 60))
        late_directional_range = directional_range((180, 240))
        directional_range_shift = late_directional_range - early_directional_range
        early_directional_amount = directional_amount((0, 60))
        late_directional_amount = directional_amount((180, 240))
        directional_amount_shift = late_directional_amount - early_directional_amount
        previous_close = np.r_[np.nan, c[:-1, -1]]
        gap = o[:, 0] / previous_close - 1.0
        previous_valid = np.r_[False, valid[:-1]]
        gap[~previous_valid] = np.nan
        cumulative = gap[:, None] + np.cumsum(phase_return, axis=1)
        repaired = (np.sign(gap)[:, None] * cumulative) <= 0
        # 0 denotes a valid no-gap day; nonzero gaps receive the first
        # repaired phase (1..3), or 4 when no fixed phase repairs it.
        repair_phase = np.full(len(days), np.nan)
        repair_phase[previous_valid & np.isfinite(gap)] = 0.0
        valid_gap = previous_valid & np.isfinite(gap) & (gap != 0)
        repair_phase[valid_gap] = 4.0
        has_repair = repaired.any(axis=1) & valid_gap
        repair_phase[has_repair] = repaired[has_repair].argmax(axis=1) + 1

        # Round2 (Batch24) intraday volume-shape states. Bucket boundaries
        # are selected by actual bar timestamp (HH:MM), not by an assumed
        # array position, and asserted against the canonical 240-bar grid:
        # opening 30min = 09:31-10:00, closing 30min = 14:31-15:00,
        # midday = 11:01-11:30 union 13:01-13:30.
        opening_bucket = (times >= 571) & (times <= 600)
        closing_bucket = (times >= 871) & (times <= 900)
        midday_bucket = ((times >= 661) & (times <= 690)) | ((times >= 781) & (times <= 810))
        grid_days = (times == expected).all(axis=1)
        if grid_days.any():
            if not (opening_bucket[grid_days].sum(axis=1) == 30).all():
                raise ValueError('opening 09:31-10:00 bucket must be exactly 30 bars')
            if not (closing_bucket[grid_days].sum(axis=1) == 30).all():
                raise ValueError('closing 14:31-15:00 bucket must be exactly 30 bars')
            if not (midday_bucket[grid_days].sum(axis=1) == 60).all():
                raise ValueError('midday 11:01-11:30+13:01-13:30 bucket must be exactly 60 bars')
        # A halt-to-10:30 day (opening-auction suspension) makes the first
        # 09:31-10:30 hour mechanically all-zero volume, not a genuine "no
        # early trading" state; the shape it produces is a data artifact.
        # Applied uniformly to every member, not just a known-thin one.
        opening_hour_bucket = (times >= 571) & (times <= 630)
        halted_open = (v * opening_hour_bucket).sum(axis=1) <= 0.0

        opening_volume = (v * opening_bucket).sum(axis=1)
        closing_volume = (v * closing_bucket).sum(axis=1)
        midday_volume = (v * midday_bucket).sum(axis=1)
        volume_u_shape_ratio = np.divide(
            opening_volume + closing_volume, total_v,
            out=np.full(len(days), np.nan), where=total_v > 0,
        )
        volume_midday_share = np.divide(
            midday_volume, total_v, out=np.full(len(days), np.nan), where=total_v > 0,
        )
        volume_opening_share = np.divide(
            opening_volume, total_v, out=np.full(len(days), np.nan), where=total_v > 0,
        )
        opening_5min_bucket = (times >= 571) & (times <= 575)
        opening_5min_volume = (v * opening_5min_bucket).sum(axis=1)
        volume_opening_absorption_speed = np.divide(
            opening_5min_volume, opening_volume,
            out=np.full(len(days), np.nan), where=opening_volume > 0,
        )
        closing_open_index = np.argmax(closing_bucket, axis=1)
        closing_session_open = o[np.arange(len(days)), closing_open_index]
        volume_closing_session_abs_return = np.abs(c[:, -1] / closing_session_open - 1.0)
        # Gini coefficient of the 240 per-bar volumes (population definition,
        # sorted ascending). total_v > 0 is already required by `valid` above.
        sorted_v = np.sort(v, axis=1)
        rank_weight = np.arange(1, 241, dtype=float)
        gini_numerator = 2.0 * (rank_weight[None, :] * sorted_v).sum(axis=1) - 241.0 * total_v
        volume_gini = np.divide(
            gini_numerator, 240.0 * total_v,
            out=np.full(len(days), np.nan), where=total_v > 0,
        )
        for halt_sensitive in (
            volume_u_shape_ratio, volume_midday_share, volume_opening_share,
            volume_opening_absorption_speed, volume_closing_session_abs_return,
            volume_gini,
        ):
            halt_sensitive[halted_open] = np.nan

        result = pd.DataFrame({
            'minute_late_return':c[:,-1]/o[:,180]-1,
            'minute_late_volume_share':v[:,180:].sum(axis=1)/total_v,
            'minute_signed_volume':(np.sign(r)*v).sum(axis=1)/total_v,
            'minute_downside_ratio':downside,
            'minute_close_vwap':c[:,-1]/vwap-1,
            'minute_path_efficiency':efficiency,
            'minute_impact_asymmetry':asym,
            'minute_volume_entropy':entropy,
            'minute_return_ar1_beta':ar1_beta,
            'minute_range_persistence': range_persistence,
            'minute_signed_flow_persistence': signed_flow_persistence,
            'minute_range_skew': range_skew,
            'minute_signed_flow_return_lead': signed_flow_return_lead,
            'minute_phase_return_curvature': phase_return_curvature,
            'minute_turnover_return_corr': turnover_return_corr,
            'minute_range_turnover_corr': range_turnover_corr,
            'minute_range_sign_asymmetry': range_sign_asymmetry,
            'minute_amount_sign_imbalance': amount_sign_imbalance,
            'minute_amount_abs_return_concentration': amount_abs_return_concentration,
            'minute_early_daily_mean_return': r[:, :60].mean(axis=1),
            'minute_late_daily_mean_return': r[:, 180:].mean(axis=1),
            'minute_phase_range_migration': range_migration,
            'minute_phase_amount_migration': phase_amount[:, 2] - phase_amount[:, 0],
            'minute_phase_abs_return_migration': abs_return_migration,
            'minute_phase_return_path_persistence': path_persistence,
            'minute_phase_return_reversal': reversal,
            'minute_phase_range_curvature': phase_range_curvature,
            'minute_phase_amount_curvature': phase_amount_curvature,
            'minute_phase_amount_abs_return_migration': amount_abs_return_migration,
            'minute_phase_return_range_absorption': return_range_absorption,
            'minute_phase_directional_range_shift': directional_range_shift,
            'minute_phase_directional_amount_shift': directional_amount_shift,
            'minute_gap_repair_phase': repair_phase,
            'minute_amount_price_impact': amount_price_impact,
            'minute_amount_signed_impact': amount_signed_impact,
            'minute_amount_directional_consistency': amount_directional_consistency,
            'minute_amount_impact_late_share': impact_late_share,
            'minute_amount_impact_phase_shift': impact_phase_shift,
            'minute_amount_impact_sign_transition': transition_amount,
            'minute_amount_reversal_impact_share': reversal_impact_share,
            'minute_amount_range_pressure': amount_range_pressure,
            'minute_amount_return_range_absorption': amount_return_range_absorption,
            'minute_amount_impact_time_position': impact_time_position,
            'minute_volume_u_shape_ratio': volume_u_shape_ratio,
            'minute_volume_gini': volume_gini,
            'minute_volume_opening_absorption_speed': volume_opening_absorption_speed,
            'minute_volume_opening_share': volume_opening_share,
            'minute_volume_closing_session_abs_return': volume_closing_session_abs_return,
            'minute_volume_midday_share': volume_midday_share,
        },index=days)
    result.loc[~valid] = np.nan
    result = result.reindex(calendar).replace([np.inf,-np.inf],np.nan)
    return result, {'observed_days':int(len(counts)), 'complete_days':int(valid.sum()),
                    'incomplete_or_invalid_days':int(len(counts)-valid.sum())}


def _minute_returns_by_day(raw, calendar):
    """Return validated 240-bar C/O returns for the cross-member minute atom."""
    f = raw.copy()
    f['datetime'] = pd.to_datetime(f.datetime)
    f = f.loc[f.datetime.dt.normalize().isin(calendar)].sort_values('datetime')
    if f.datetime.duplicated().any():
        raise ValueError('duplicate minute timestamps')
    if f.empty:
        return {}
    dates = f.datetime.dt.normalize()
    counts = dates.value_counts()
    f = f.loc[dates.map(counts).eq(240)]
    dates = f.datetime.dt.normalize()
    if f.empty:
        return {}
    days = pd.DatetimeIndex(dates.drop_duplicates())
    fields = ['open', 'high', 'low', 'close', 'volume', 'turnover']
    x = f[fields].to_numpy(float).reshape(-1, 240, 6)
    times = (f.datetime.dt.hour * 60 + f.datetime.dt.minute).to_numpy().reshape(-1, 240)
    expected = np.r_[np.arange(571, 691), np.arange(781, 901)]
    valid = (times == expected).all(axis=1) & np.isfinite(x).all(axis=(1, 2))
    valid &= (x[:, :, :4] > 0).all(axis=(1, 2)) & (x[:, :, 4:] >= 0).all(axis=(1, 2))
    valid &= (x[:, :, 1] >= x[:, :, :4].max(axis=2)).all(axis=1)
    valid &= (x[:, :, 2] <= x[:, :, :4].min(axis=2)).all(axis=1)
    o, h, l, c, v, a = [x[:, :, i] for i in range(6)]
    total_v, total_a = v.sum(axis=1), a.sum(axis=1)
    valid &= (total_v > 0) & (total_a > 0)
    with np.errstate(divide='ignore', invalid='ignore'):
        vwap = total_a / total_v
        valid &= (vwap >= l.min(axis=1) * .98) & (vwap <= h.max(axis=1) * 1.02)
        returns = c / o - 1.0
    return {
        day: row for day, row, ok in zip(days, returns, valid) if bool(ok)
    }


def _minute_market_residual_abs_cluster(raw_by_symbol, symbols, calendar):
    """Build daily states from complete 14-member minute return panels."""
    panel = pd.DataFrame(index=calendar, columns=symbols, dtype=float)
    if not raw_by_symbol or any(symbol not in raw_by_symbol for symbol in symbols):
        return panel
    common = set.intersection(*(set(raw_by_symbol[symbol]) for symbol in symbols))
    for day in sorted(common):
        matrix = np.column_stack([raw_by_symbol[symbol][day] for symbol in symbols])
        residual = matrix - matrix.mean(axis=1, keepdims=True)
        z = np.abs(residual)
        lag, now = z[:-1], z[1:]
        lag_centered = lag - lag.mean(axis=0, keepdims=True)
        now_centered = now - now.mean(axis=0, keepdims=True)
        numerator = (lag_centered * now_centered).sum(axis=0)
        denominator = np.sqrt(
            (lag_centered ** 2).sum(axis=0) * (now_centered ** 2).sum(axis=0)
        )
        state = np.divide(
            numerator, denominator, out=np.full(len(symbols), np.nan), where=denominator > 0
        )
        panel.loc[day, symbols] = state
    return panel


def share_daily(raw, calendar, max_stale_days=7):
    """Use recorded next-session convention, NOT a verified publication timestamp."""
    f=raw.copy()
    for col in ('trade_date','usable_from_date'):
        f[col]=pd.to_datetime(f[col])
        if f[col].isna().any():
            raise ValueError('missing share dates')
    if not (f.usable_from_date>f.trade_date).all():
        raise ValueError('share availability must follow source date')
    if f.trade_date.duplicated().any():
        raise ValueError('ambiguous share source dates')
    if not np.isfinite(f.fund_shares).all() or not f.fund_shares.gt(0).all():
        raise ValueError('nonpositive/invalid shares')
    # Weekend/holiday observations can legitimately become available on the same
    # next session. Under the recorded convention, use its latest source date.
    collisions=int(f.usable_from_date.duplicated().sum())
    f=f.sort_values(['usable_from_date','trade_date']).drop_duplicates('usable_from_date',keep='last')
    merged=pd.merge_asof(pd.DataFrame({'date':calendar}), f,
                         left_on='date',right_on='usable_from_date',direction='backward')
    age=(merged.date-merged.usable_from_date).dt.days
    s=pd.Series(merged.fund_shares.where(age<=max_stale_days).to_numpy(),index=calendar)
    return s, {'stale_or_missing_days':int(s.isna().sum()),
               'same_availability_date_collisions':collisions,
               'collision_policy':'LATEST_SOURCE_DATE_WITH_SAME_RECORDED_AVAILABILITY',
               'availability_status':'NEXT_SESSION_ASSUMPTION_NOT_PUBLICATION_PROOF',
               'max_stale_calendar_days':max_stale_days}


def nav_daily(raw, prices, calendar, max_stale_days=7):
    """Match valuation-date raw close to NAV, then wait until recorded availability.

    For QDII this remains a reported-NAV basis, not synchronous fair-value premium.
    """
    f=raw.copy()
    for col in ('nav_date','ann_date','usable_from_date'):
        f[col]=pd.to_datetime(f[col])
    if f.nav_date.duplicated().any():
        raise ValueError('duplicate NAV valuation dates')
    if f[['nav_date','ann_date','usable_from_date']].isna().any().any():
        raise ValueError('NAV publication timing missing; no fallback assumption')
    if not ((f.ann_date>=f.nav_date)&(f.usable_from_date>f.ann_date)).all():
        raise ValueError('NAV publication/availability ordering invalid')
    if not np.isfinite(f.unit_nav).all() or not f.unit_nav.gt(0).all():
        raise ValueError('invalid unit NAV')
    p=prices.copy()
    p['trade_date']=pd.to_datetime(p.trade_date)
    if p.trade_date.duplicated().any() or not p.price_basis.eq('unadjusted').all():
        raise ValueError('invalid raw daily prices for NAV matching')
    p=p.set_index('trade_date').close
    f['premium']=p.reindex(pd.DatetimeIndex(f.nav_date)).to_numpy()/f.unit_nav-1
    # Weekend NAV without an ETF closing price is not paired to a different date.
    unmatched=int(f.premium.isna().sum())
    f=f.dropna(subset=['premium']).sort_values(['usable_from_date','nav_date'])
    collisions=int(f.usable_from_date.duplicated().sum())
    f=f.drop_duplicates('usable_from_date',keep='last')
    # Latest known valuation, not latest publication: a late quarterly NAV
    # must not roll the currently known daily valuation backwards in time.
    superseded=f.nav_date<f.nav_date.cummax()
    late_old_count=int(superseded.sum())
    f=f.loc[~superseded]
    merged=pd.merge_asof(pd.DataFrame({'date':calendar}),f,
                         left_on='date',right_on='usable_from_date',direction='backward')
    age=(merged.date-merged.nav_date).dt.days
    s=pd.Series(merged.premium.where(age<=max_stale_days).to_numpy(),index=calendar)
    return s,{'availability_status':'AFTER_RECORDED_ANN_DATE_NOT_VINTAGE_CERTIFIED',
              'unmatched_valuation_price_rows':unmatched,'same_availability_collisions':collisions,
              'late_older_valuations_ignored':late_old_count,
              'stale_or_missing_days':int(s.isna().sum()),'max_nav_age_calendar_days':max_stale_days,
              'qdii_caveat':'reported NAV basis; ETF and underlying valuation clocks can differ'}


def load_source(root, symbols, calendar, cfg):
    kind=cfg['source_type']
    folder={'minute':'1m','share':'fund_share','nav':'nav'}[kind]
    outputs, audits, checks = {}, {}, {}
    minute_returns = {} if (
        kind == 'minute' and 'minute_market_residual_abs_cluster' in cfg.get('mechanisms', {})
    ) else None
    for symbol in symbols:
        raw=pd.read_parquet(root/folder/f'{symbol}.parquet')
        if not raw.ts_code.eq(symbol).all():
            raise ValueError(f'identity mismatch {symbol}')
        if kind=='minute' and not raw.price_basis.eq('unadjusted').all():
            raise ValueError('minute price basis mismatch')
        if kind=='minute':
            calculate=minute_daily
        elif kind=='nav':
            prices=pd.read_parquet(root/'1d'/f'{symbol}.parquet')
            if not prices.ts_code.eq(symbol).all():
                raise ValueError('NAV price identity mismatch')
            calculate=lambda r,c:nav_daily(r,prices.loc[pd.to_datetime(prices.trade_date)<=c.max()],c,cfg['max_stale_calendar_days'])
        else:
            calculate=lambda r,c:share_daily(r,c,cfg['max_stale_calendar_days'])
        full, audits[symbol]=calculate(raw,calendar)
        if minute_returns is not None:
            minute_returns[symbol] = _minute_returns_by_day(raw, calendar)
        # Full raw transform is tested, not just rolling over precomputed summaries.
        timestamp='datetime' if kind=='minute' else 'usable_from_date'
        raw_time=pd.to_datetime(raw[timestamp]).dt.normalize()
        for cut in ('2024-12-31','2025-12-31'):
            cutoff=pd.Timestamp(cut)
            cal=calendar[calendar<=cutoff]
            prefix,_=calculate(raw.loc[raw_time<=cutoff],cal)
            mutated=raw.copy()
            cols=['open','high','low','close','volume','turnover'] if kind=='minute' else (['unit_nav'] if kind=='nav' else ['fund_shares'])
            mutated.loc[raw_time>cutoff,cols]*=1.71
            changed,_=calculate(mutated,calendar)
            assertion=pd.testing.assert_frame_equal if kind=='minute' else pd.testing.assert_series_equal
            assertion(full.loc[:cut],prefix,check_exact=False,rtol=1e-9,atol=1e-12)
            assertion(full.loc[:cut],changed.loc[:cut],check_exact=False,rtol=1e-9,atol=1e-12)
            checks[f'{symbol}:{cut}']=True
        outputs[symbol]=full
        print(f'[source] {kind} {symbol}: {audits[symbol]}',flush=True)
    if kind=='minute':
        panels={n:pd.DataFrame({s:d[n] for s,d in outputs.items()}) for n in MINUTE_NAMES}
        if minute_returns is not None:
            panels['minute_market_residual_abs_cluster'] = _minute_market_residual_abs_cluster(
                minute_returns, symbols, calendar
            )
    elif kind=='nav':
        panels={'premium':pd.DataFrame(outputs)}
    else:
        panels={'shares':pd.DataFrame(outputs)}
    return panels,audits,checks


def parent_artifacts(repo, cfg):
    base=repo/'runtime_outputs/etf_rotation_research/runs'
    files=set()
    for definition in cfg['mechanisms'].values():
        run=(base/definition['parent_run']).resolve()
        if not run.is_relative_to(base.resolve()):
            raise ValueError('parent path outside group research runs')
        candidate=definition['parent_candidate']
        if not candidate.replace('_','').isalnum():
            raise ValueError('invalid parent candidate name')
        files.update(run/name for name in ['PLAN.json','coverage.csv','group_labels.csv',
                     'future_leak_check.json',f'scores_{candidate}.csv'])
    return sorted(files)


def load_parent_source(repo, groups, calendar, cfg):
    """Reuse frozen scores, expanding each group score to its member ETF columns."""
    panels,audits={},{}
    for mechanism,definition in cfg['mechanisms'].items():
        run=repo/'runtime_outputs/etf_rotation_research/runs'/definition['parent_run']
        parent=definition['parent_candidate']
        plan=json.loads((run/'PLAN.json').read_text())
        if (plan['config']['entry_lag'],plan['config']['horizon'],plan['config']['top_k'])!=(2,5,2):
            raise ValueError('incompatible parent contract')
        if parent not in plan['evaluated_ids']:
            raise ValueError('parent was not evaluated')
        if not json.loads((run/'future_leak_check.json').read_text())['all_pass']:
            raise ValueError('parent lacks tested feature causality')
        score=pd.read_csv(run/f'scores_{parent}.csv',index_col=0,parse_dates=True)
        if set(score.columns)!=set(groups) or score.index.has_duplicates or not score.index.is_monotonic_increasing:
            raise ValueError('parent group/score index mismatch')
        # Raw group scores are already causal and complete-member aggregates.
        # A different parent candidate's NaN must not erase this group's history.
        # Current-date complete-14 and common-new-candidate masks are applied by
        # the runner. No parent outcome/label availability enters this feature.
        score=score.reindex(calendar)
        panels[mechanism]=pd.DataFrame({s:score[g] for g,v in groups.items() for s in v['members']})
        audits[mechanism]={'parent_run':definition['parent_run'],'parent_candidate':parent,
                          'direction':'INHERITED_NO_FLIP','normalization':'current minus prior-only mean over prior-only std',
                          'availability_status':plan.get('availability_status','SOURCE_VINTAGE_NOT_CERTIFIED')}
    return panels,audits


def build_atoms(panels,cfg):
    result={}
    for w in cfg['windows']:
        for mechanism,definition in cfg['mechanisms'].items():
            if cfg['source_type']=='self_state':
                x=panels[mechanism]
                prior=x.shift(1)
                raw=(x-prior.rolling(w,min_periods=w).mean())/prior.rolling(w,min_periods=w).std().replace(0,np.nan)
            elif cfg['source_type']=='nav':
                p=panels['premium']
                if mechanism=='nav_basis_discount':
                    raw=p.rolling(w,min_periods=w).mean()
                elif mechanism=='nav_basis_change':
                    raw=p-p.shift(w)
                elif mechanism=='nav_basis_volatility':
                    raw=p.rolling(w,min_periods=w).std()
                elif mechanism=='nav_basis_persistence':
                    raw=np.sign(p).rolling(w,min_periods=w).mean()
                else:
                    raise ValueError('unknown NAV mechanism')
            elif cfg['source_type']=='minute':
                raw_mechanism = _ALL_MINUTE_ALIASES.get(
                    mechanism, (mechanism, 1)
                )[0]
                source_name = ('minute_late_return'
                               if raw_mechanism == 'reverse_minute_late_return'
                               else raw_mechanism)
                if raw_mechanism == 'minute_phase_signed_return_corr':
                    if 'minute_early_daily_mean_return' not in panels or 'minute_late_daily_mean_return' not in panels:
                        raise KeyError('minute_phase_signed_return_corr requires early/late return panels')
                    early = panels['minute_early_daily_mean_return']
                    late = panels['minute_late_daily_mean_return']
                    complete = early.notna() & late.notna()
                    raw = early.rolling(w, min_periods=w).corr(late)
                    raw = raw.where(complete.astype(float).rolling(w, min_periods=w).sum().eq(w))
                elif raw_mechanism == 'minute_orderflow_return_lead':
                    if 'close' not in panels:
                        raise KeyError('minute_orderflow_return_lead requires close panel')
                    orderflow = panels['minute_signed_volume'].shift(1)
                    returns = panels['close'].pct_change(fill_method=None)
                    complete = orderflow.notna() & returns.notna()
                    raw = orderflow.rolling(w,min_periods=w).corr(returns)
                    raw = raw.where(complete.astype(float).rolling(w,min_periods=w).sum().eq(w))
                elif raw_mechanism == 'minute_volume_return_concentration_lead':
                    # Same-day cross: opening-session volume concentration
                    # versus closing-session |return|, both derived from the
                    # same D-close-available 240 bars. Not a two-leg
                    # composite of an existing candidate; both legs are new
                    # helper scalars introduced for this mechanism only.
                    # Halt-to-10:30 days are NaN in the opening-share leg
                    # (see minute_daily); the 20-calendar-day window tolerates
                    # up to 5 such gaps (min_periods=15) rather than requiring
                    # all 20 complete, per master's pre-label halt-day rule.
                    if 'minute_volume_opening_share' not in panels or \
                       'minute_volume_closing_session_abs_return' not in panels:
                        raise KeyError(
                            'minute_volume_return_concentration_lead requires '
                            'opening-share/closing-abs-return panels'
                        )
                    opening_share = panels['minute_volume_opening_share']
                    closing_abs_return = panels['minute_volume_closing_session_abs_return']
                    complete = opening_share.notna() & closing_abs_return.notna()
                    min_periods = _HALT_TOLERANT_MIN_PERIODS if w == 20 else w
                    raw = opening_share.rolling(w, min_periods=min_periods).corr(closing_abs_return)
                    raw = raw.where(complete.astype(float).rolling(w, min_periods=1).sum().ge(min_periods))
                elif raw_mechanism == 'minute_volume_shape_persistence':
                    # Day-over-day autocorrelation of the U-shape ratio
                    # itself: is the intraday volume shape a stable regime or
                    # a noisy one-off, not a level-based factor. Same
                    # halt-day tolerance as minute_volume_return_concentration_lead.
                    shape = panels['minute_volume_u_shape_ratio']
                    lagged_shape = shape.shift(1)
                    complete = shape.notna() & lagged_shape.notna()
                    min_periods = _HALT_TOLERANT_MIN_PERIODS if w == 20 else w
                    raw = shape.rolling(w, min_periods=min_periods).corr(lagged_shape)
                    raw = raw.where(complete.astype(float).rolling(w, min_periods=1).sum().ge(min_periods))
                elif raw_mechanism == 'minute_volume_midday_share':
                    # Level-based candidate but still halt-sensitive (a halt
                    # day's midday bucket is unaffected in isolation, but the
                    # member-day is marked fully missing upstream in
                    # minute_daily for uniform treatment); same tolerance.
                    # The relaxed threshold only applies at the registered
                    # w=20; any other window keeps the strict full-window
                    # default rather than raising on min_periods > window.
                    raw = panels[source_name].rolling(
                        w, min_periods=(_HALT_TOLERANT_MIN_PERIODS if w == 20 else w)
                    ).mean()
                else:
                    raw=panels[source_name].rolling(w,min_periods=w).mean()
            else:
                s=panels['shares']
                daily=s.pct_change(fill_method=None)
                if mechanism == 'share_flow_return_lead':
                    if 'close' not in panels:
                        raise KeyError('share_flow_return_lead requires close panel')
                    flow = np.log(s.where(s > 0)).diff().shift(1)
                    returns = panels['close'].pct_change(fill_method=None)
                    complete = flow.notna() & returns.notna()
                    raw = flow.rolling(w,min_periods=w).corr(returns)
                    raw = raw.where(complete.astype(float).rolling(w,min_periods=w).sum().eq(w))
                elif mechanism=='share_redemption':
                    raw=s.pct_change(w,fill_method=None)
                elif mechanism=='share_persistence':
                    raw=np.sign(daily).rolling(w,min_periods=w).mean()
                elif mechanism=='share_acceleration':
                    change=s.pct_change(w,fill_method=None)
                    raw=change-change.shift(w)
                elif mechanism=='share_volatility':
                    raw=daily.rolling(w,min_periods=w).std()
                elif mechanism in _SHARE_AMOUNT_MECHANISMS:
                    # Batch23: cross fund-share creation/redemption flow with
                    # canonical daily turnover amount. Neither family reads the
                    # other's raw series anywhere else; this is a new source
                    # cross, not a variant of an existing amount-only or
                    # share-only template.
                    if 'amount' not in panels:
                        raise KeyError(f'{mechanism} requires amount panel')
                    amount = panels['amount']
                    flow = np.log(s.where(s > 0)).diff()
                    innovation = np.log(amount.where(amount > 0)).diff()
                    complete = flow.notna() & innovation.notna()
                    complete_count = complete.astype(float).rolling(w, min_periods=w).sum()
                    if mechanism == 'share_amount_flow_divergence_corr':
                        raw = flow.rolling(w, min_periods=w).corr(innovation)
                        raw = raw.where(complete_count.eq(w))
                    elif mechanism == 'share_amount_tail_mismatch_rate':
                        flow_abs, innovation_abs = flow.abs(), innovation.abs()
                        flow_tail = flow_abs > flow_abs.rolling(w, min_periods=w).mean()
                        innovation_tail = innovation_abs > innovation_abs.rolling(w, min_periods=w).mean()
                        mismatch = (flow_tail ^ innovation_tail).astype(float)
                        raw = mismatch.where(complete).rolling(w, min_periods=w).mean()
                        raw = raw.where(complete_count.eq(w))
                    elif mechanism == 'share_flow_amount_signed_alignment':
                        alignment = np.sign(flow) * np.sign(innovation)
                        raw = alignment.where(complete).rolling(w, min_periods=w).mean()
                        raw = raw.where(complete_count.eq(w))
                    elif mechanism == 'share_lag_amount_abs_corr':
                        lagged_flow = flow.shift(1)
                        lag_complete = lagged_flow.notna() & innovation.notna()
                        lag_complete_count = lag_complete.astype(float).rolling(w, min_periods=w).sum()
                        raw = lagged_flow.rolling(w, min_periods=w).corr(innovation.abs())
                        raw = raw.where(lag_complete_count.eq(w))
                    elif mechanism == 'share_amount_ratio_dispersion':
                        # A raw |flow|/|innovation| ratio explodes whenever the
                        # amount-innovation denominator is near zero (pre-run
                        # structural diagnostic on 513100.SH found this before
                        # any label was read). Redefine as the rolling std of
                        # the in-window percentile-rank gap between the two
                        # magnitudes: bounded, scale-free, never divides.
                        flow_pct = flow.abs().rolling(w, min_periods=w).rank(pct=True)
                        innovation_pct = innovation.abs().rolling(w, min_periods=w).rank(pct=True)
                        rank_gap = (flow_pct - innovation_pct).where(complete)
                        raw = rank_gap.rolling(w, min_periods=w).std()
                        raw = raw.where(complete_count.eq(w))
                    elif mechanism == 'share_flow_amount_conditional_asymmetry':
                        positive = innovation.gt(0).where(innovation.notna())
                        positive_bool = positive.astype('boolean').fillna(False)
                        valid = flow.notna() & positive.notna()
                        pos_mask = positive_bool & valid
                        neg_mask = (~positive_bool) & valid
                        pos_count = pos_mask.astype(float).rolling(w, min_periods=1).sum()
                        neg_count = neg_mask.astype(float).rolling(w, min_periods=1).sum()
                        pos_mean = flow.abs().where(pos_mask).rolling(w, min_periods=1).sum().div(
                            pos_count.where(pos_count.gt(0))
                        )
                        neg_mean = flow.abs().where(neg_mask).rolling(w, min_periods=1).sum().div(
                            neg_count.where(neg_count.gt(0))
                        )
                        window_complete = complete_count.eq(w)
                        raw = (pos_mean - neg_mean).where(
                            window_complete & pos_count.gt(0) & neg_count.gt(0)
                        )
                    else:
                        raise ValueError(f'unhandled share-amount mechanism: {mechanism}')
                else:
                    raise ValueError(f'unknown share mechanism {mechanism}')
            result[f'{mechanism}_{w}']=(raw*definition['direction']).replace([np.inf,-np.inf],np.nan)
    return result


def leakage_checks(panels,cfg,cut):
    full=build_atoms(panels,cfg)
    prefix=build_atoms({k:v.loc[:cut] for k,v in panels.items()},cfg)
    mutated={k:v.copy() for k,v in panels.items()}
    for v in mutated.values():
        v.loc[v.index>cut]*=1.71
    changed=build_atoms(mutated,cfg)
    checks={}
    for name in full:
        pd.testing.assert_frame_equal(full[name].loc[:cut],prefix[name],check_exact=False,rtol=1e-9,atol=1e-12)
        pd.testing.assert_frame_equal(full[name].loc[:cut],changed[name].loc[:cut],check_exact=False,rtol=1e-9,atol=1e-12)
        checks[name]=True
    return checks
