"""Approved fixed-window OHLCV atoms for bounded ETF IC rounds."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import (
    etf_group_luna_rounds_a, etf_group_luna_rounds_b, etf_group_luna_rounds_c,
    etf_group_luna_rounds_d, etf_group_luna_rounds_e, etf_group_luna_rounds_f,
)

LUNA_MODULES = (
    etf_group_luna_rounds_a, etf_group_luna_rounds_b, etf_group_luna_rounds_c,
    etf_group_luna_rounds_d, etf_group_luna_rounds_e, etf_group_luna_rounds_f,
)


WINDOW = 20
_DIRECTIONS = {
    # IC20 batch 25: frozen economic direction; fewer underwater closes imply
    # more persistent relative strength.
    "underwater_time_share": -1,
    # IC20 rounds 26-35: ten single-mechanism OHLCV discovery definitions.
    "bipower_jump_share": -1,
    "market_coskewness": 1,
    "ohlc_range_overlap": -1,
    "intraday_body_utilization": 1,
    "downside_semivariance_share": -1,
    "squared_return_ar1": -1,
    "overnight_variance_share": -1,
    "close_extrema_time_order": 1,
    "downside_price_impact_share": -1,
    "peer_lag_return_beta": 1,
    # Historical rounds retained for reproducibility.
    "wick_demand": 1,
    "clv_volume_pressure": 1,
    "lagged_volume_return_corr": 1,
    # IC20 batch 6 approved definitions.
    "market_residual_downside": -1,
    "body_transition_asymmetry": 1,
    "realized_vol_term_structure_5": -1,
    # Explicit post-result direction hypothesis.  This is deliberately a
    # separate name/config entry; it must not relabel the batch-6 result.
    "reverse_realized_vol_term_structure_5": 1,
    "amount_signed_imbalance": 1,
    "amount_return_asymmetry": 1,
    "return_acceleration_5": 1,
    # IC20 batch 7 approved definitions.
    "market_residual_skew": 1,
    "direction_range_coupling": 1,
    "amount_concentration": -1,
    "amount_innovation_return_beta": 1,
    # IC20 batch 13: explicit 2025 post-outcome discovery.
    "gap_body_magnitude_coupling": -1,
    "amount_gap_shock_response_corr": -1,
    "range_body_absorption_corr": -1,
    # IC20 batch 14 raw library; implementation direction is frozen at +1.
    "gap_excess_kurtosis": 1,
    "clv_autocorr": 1,
    "gap_abs_change": 1,
    "range_gap_abs_corr": 1,
    "amount_abs_body_corr": 1,
    "amount_clv_abs_corr": 1,
    "clv_excess_kurtosis": 1,
    "wick_abs_kurtosis": 1,
    "wick_abs_change": 1,
    "amount_innovation_excess_kurtosis": 1,
    "amount_innovation_abs_change": 1,
    "body_wick_abs_corr": 1,
    "gap_signed_body_corr": 1,
    "range_body_ratio_dispersion": 1,
    # IC20 batch 15 raw library; implementation direction is frozen at +1.
    "gap_lag_body_corr": 1,
    "gap_lag_abs_body_corr": 1,
    "range_lag_abs_body_corr": 1,
    "amount_lag_abs_body_corr": 1,
    "gap_conditional_body_asymmetry": 1,
    "amount_conditional_body_asymmetry": 1,
    "clv_abs_tail_share": 1,
    "body_sign_entropy": 1,
    "gap_sign_entropy": 1,
    "clv_sign_transition_rate": 1,
    "amount_innovation_sign_entropy": 1,
    "range_share_entropy": 1,
    # IC20 batch 9 approved definitions.
    "market_residual_abs_cluster": -1,
    "range_to_return_lead": 1,
    # IC20 batch 10 approved definitions.
    "market_residual_downshock_recovery": 1,
    "market_residual_range_return_lead": 1,
    "market_residual_amount_beta": 1,
    # IC20 batch 11: explicit 2025 post-outcome discovery.
    "intraday_body_ar1": 1,
    "wick_body_coupling": -1,
    "close_location_dispersion": -1,
    # IC20 batch 16 raw library; Stage1 direction is fixed at +1.
    "overnight_intraday_switch_rate": 1,
    "gap_repair_signed_magnitude": 1,
    "gap_repair_completion_rate": 1,
    "body_wick_rejection_rate": 1,
    # IC20 batch 17 raw library; Stage1 direction is fixed at +1.
    "amount_shock_body_efficiency": 1,
    "amount_shock_wick_rejection": 1,
    "amount_shock_direction_alignment": 1,
    "amount_shock_close_location_alignment": 1,
    "amount_shock_gap_repair": 1,
    "amount_shock_close_extremity": 1,
    # IC20 batch 18 raw relative-residual library; Stage1 direction +1.
    "market_residual_mean": 1,
    "market_residual_upside_mean": 1,
    "market_residual_downside_mean": 1,
    "market_residual_sign_imbalance": 1,
    "market_residual_path_efficiency": 1,
    "market_residual_sign_persistence": 1,
    "market_residual_turning_rate": 1,
    "market_residual_tail_share": 1,
    "market_residual_market_beta": 1,
    "market_residual_range_absorption": 1,
    # IC20 batch 19 tail-event/state-persistence raw library; Stage1 +1.
    "body_positive_run_mean": 1,
    "body_negative_run_mean": 1,
    "gap_positive_run_mean": 1,
    "gap_negative_run_mean": 1,
    "clv_extreme_recovery_rate": 1,
    "range_shock_compression_rate": 1,
    "amount_price_tail_mismatch_rate": 1,
    "gap_body_tail_direction_asymmetry": 1,
    "range_shock_body_absorption": 1,
    "amount_tail_clv_alignment": 1,
    # IC20 batch 20 event-to-next-day state-machine raw library; Stage1 +1.
    "gap_shock_range_recovery": 1,
    "gap_shock_clv_recovery": 1,
    "amount_shock_range_contraction": 1,
    "wick_rejection_body_continuation": 1,
    "range_shock_gap_absorption": 1,
    "range_shock_clv_absorption": 1,
    "extreme_body_amount_normalization": 1,
    "amount_shock_clv_recovery": 1,
    "gap_shock_body_reversal": 1,
    "range_shock_body_recovery": 1,
    "wick_rejection_range_compression": 1,
    "body_shock_amount_normalization": 1,
    # IC20 batch 21 range-shock non-price response raw library; Stage1 +1.
    "range_shock_amount_normalization": 1,
    "range_shock_amount_tail_persistence": 1,
    "range_shock_amount_sign_persistence": 1,
    "range_shock_amount_to_range_ratio": 1,
    "range_shock_wick_rejection": 1,
    "range_shock_direction_efficiency": 1,
    "range_shock_range_persistence": 1,
    "range_shock_wick_absorption": 1,
}
_BATCH14_ALIASES = {
    "d2025_gap_excess_kurtosis": ("gap_excess_kurtosis", -1),
    "d2025_clv_autocorr": ("clv_autocorr", 1),
    "d2025_gap_abs_change": ("gap_abs_change", 1),
    "d2025_range_gap_abs_corr": ("range_gap_abs_corr", -1),
    "d2025_amount_abs_body_corr": ("amount_abs_body_corr", 1),
    "d2025_amount_clv_abs_corr": ("amount_clv_abs_corr", 1),
    "d2025_clv_excess_kurtosis": ("clv_excess_kurtosis", 1),
    "d2025_wick_abs_kurtosis": ("wick_abs_kurtosis", -1),
    "d2025_wick_abs_change": ("wick_abs_change", -1),
    "d2025_amount_innovation_excess_kurtosis": (
        "amount_innovation_excess_kurtosis", -1
    ),
    "d2025_amount_innovation_abs_change": ("amount_innovation_abs_change", 1),
    "d2025_body_wick_abs_corr": ("body_wick_abs_corr", -1),
    "d2025_gap_signed_body_corr": ("gap_signed_body_corr", -1),
    "d2025_range_body_ratio_dispersion": ("range_body_ratio_dispersion", 1),
}
_DIRECTIONS.update({name: sign for name, (_, sign) in _BATCH14_ALIASES.items()})
_BATCH15_ALIASES = {
    "d2025_gap_lag_body_corr": ("gap_lag_body_corr", 1),
    "d2025_gap_lag_abs_body_corr": ("gap_lag_abs_body_corr", -1),
    "d2025_range_lag_abs_body_corr": ("range_lag_abs_body_corr", -1),
    "d2025_amount_lag_abs_body_corr": ("amount_lag_abs_body_corr", -1),
    "d2025_gap_conditional_body_asymmetry": ("gap_conditional_body_asymmetry", 1),
    "d2025_amount_conditional_body_asymmetry": ("amount_conditional_body_asymmetry", 1),
    "d2025_clv_abs_tail_share": ("clv_abs_tail_share", -1),
    "d2025_body_sign_entropy": ("body_sign_entropy", -1),
    "d2025_gap_sign_entropy": ("gap_sign_entropy", -1),
    "d2025_clv_sign_transition_rate": ("clv_sign_transition_rate", -1),
    "d2025_amount_innovation_sign_entropy": ("amount_innovation_sign_entropy", 1),
    "d2025_range_share_entropy": ("range_share_entropy", -1),
}
_ALL_ALIASES = {**_BATCH14_ALIASES, **_BATCH15_ALIASES}
_DIRECTIONS.update({name: sign for name, (_, sign) in _BATCH15_ALIASES.items()})
_BATCH16_ALIASES = {
    "d2025_overnight_intraday_switch_rate": ("overnight_intraday_switch_rate", 1),
    "d2025_gap_repair_signed_magnitude": ("gap_repair_signed_magnitude", 1),
    "d2025_gap_repair_completion_rate": ("gap_repair_completion_rate", 1),
    "d2025_body_wick_rejection_rate": ("body_wick_rejection_rate", 1),
}
_ALL_ALIASES = {**_ALL_ALIASES, **_BATCH16_ALIASES}
_DIRECTIONS.update({name: sign for name, (_, sign) in _BATCH16_ALIASES.items()})
_BATCH17_ALIASES = {
    "d2025_amount_shock_body_efficiency": ("amount_shock_body_efficiency", 1),
    "d2025_amount_shock_wick_rejection": ("amount_shock_wick_rejection", 1),
    "d2025_amount_shock_direction_alignment": ("amount_shock_direction_alignment", 1),
    "d2025_amount_shock_close_location_alignment": ("amount_shock_close_location_alignment", 1),
    "d2025_amount_shock_gap_repair": ("amount_shock_gap_repair", -1),
    "d2025_amount_shock_close_extremity": ("amount_shock_close_extremity", 1),
}
_ALL_ALIASES = {**_ALL_ALIASES, **_BATCH17_ALIASES}
_DIRECTIONS.update({name: sign for name, (_, sign) in _BATCH17_ALIASES.items()})
_BATCH18_ALIASES = {
    "d2025_market_residual_mean": ("market_residual_mean", 1),
    "d2025_market_residual_upside_mean": ("market_residual_upside_mean", 1),
    "d2025_market_residual_downside_mean": ("market_residual_downside_mean", 1),
    "d2025_market_residual_sign_imbalance": ("market_residual_sign_imbalance", 1),
    "d2025_market_residual_path_efficiency": ("market_residual_path_efficiency", 1),
    "d2025_market_residual_sign_persistence": ("market_residual_sign_persistence", -1),
    "d2025_market_residual_turning_rate": ("market_residual_turning_rate", 1),
    "d2025_market_residual_tail_share": ("market_residual_tail_share", 1),
    "d2025_market_residual_market_beta": ("market_residual_market_beta", 1),
    "d2025_market_residual_range_absorption": ("market_residual_range_absorption", -1),
}
_ALL_ALIASES = {**_ALL_ALIASES, **_BATCH18_ALIASES}
_DIRECTIONS.update({name: sign for name, (_, sign) in _BATCH18_ALIASES.items()})
_BATCH19_ALIASES = {
    "d2025_body_positive_run_mean": ("body_positive_run_mean", 1),
    "d2025_body_negative_run_mean": ("body_negative_run_mean", -1),
    "d2025_gap_positive_run_mean": ("gap_positive_run_mean", 1),
    "d2025_gap_negative_run_mean": ("gap_negative_run_mean", 1),
    "d2025_clv_extreme_recovery_rate": ("clv_extreme_recovery_rate", 1),
    "d2025_range_shock_compression_rate": ("range_shock_compression_rate", 1),
    "d2025_amount_price_tail_mismatch_rate": ("amount_price_tail_mismatch_rate", -1),
    "d2025_gap_body_tail_direction_asymmetry": ("gap_body_tail_direction_asymmetry", 1),
    "d2025_range_shock_body_absorption": ("range_shock_body_absorption", 1),
    "d2025_amount_tail_clv_alignment": ("amount_tail_clv_alignment", -1),
}
_ALL_ALIASES = {**_ALL_ALIASES, **_BATCH19_ALIASES}
_DIRECTIONS.update({name: sign for name, (_, sign) in _BATCH19_ALIASES.items()})
_BATCH20_ALIASES = {
    "d2025_gap_shock_range_recovery": ("gap_shock_range_recovery", 1),
    "d2025_gap_shock_clv_recovery": ("gap_shock_clv_recovery", 1),
    "d2025_amount_shock_range_contraction": ("amount_shock_range_contraction", 1),
    "d2025_wick_rejection_body_continuation": ("wick_rejection_body_continuation", 1),
    "d2025_range_shock_gap_absorption": ("range_shock_gap_absorption", 1),
    "d2025_range_shock_clv_absorption": ("range_shock_clv_absorption", 1),
    "d2025_extreme_body_amount_normalization": ("extreme_body_amount_normalization", 1),
    "d2025_amount_shock_clv_recovery": ("amount_shock_clv_recovery", 1),
    "d2025_gap_shock_body_reversal": ("gap_shock_body_reversal", -1),
    "d2025_range_shock_body_recovery": ("range_shock_body_recovery", 1),
    "d2025_wick_rejection_range_compression": ("wick_rejection_range_compression", 1),
    "d2025_body_shock_amount_normalization": ("body_shock_amount_normalization", 1),
}
_ALL_ALIASES = {**_ALL_ALIASES, **_BATCH20_ALIASES}
_DIRECTIONS.update({name: sign for name, (_, sign) in _BATCH20_ALIASES.items()})
_BATCH21_ALIASES = {
    "d2025_range_shock_amount_normalization": ("range_shock_amount_normalization", -1),
    "d2025_range_shock_amount_tail_persistence": ("range_shock_amount_tail_persistence", 1),
    "d2025_range_shock_amount_sign_persistence": ("range_shock_amount_sign_persistence", -1),
    "d2025_range_shock_amount_to_range_ratio": ("range_shock_amount_to_range_ratio", 1),
    "d2025_range_shock_wick_rejection": ("range_shock_wick_rejection", 1),
    "d2025_range_shock_direction_efficiency": ("range_shock_direction_efficiency", 1),
    "d2025_range_shock_range_persistence": ("range_shock_range_persistence", 1),
    "d2025_range_shock_wick_absorption": ("range_shock_wick_absorption", -1),
}
_ALL_ALIASES = {**_ALL_ALIASES, **_BATCH21_ALIASES}
_DIRECTIONS.update({name: sign for name, (_, sign) in _BATCH21_ALIASES.items()})
_DIRECTIONS.update({
    "gap_shock_wick_rejection": 1,
    "amount_shock_wick_absorption": 1,
    "clv_extreme_direction_efficiency": 1,
    "body_shock_wick_repair": 1,
    "gap_shock_direction_efficiency": 1,
    "clv_extreme_wick_rejection": 1,
})
_BATCH22_ALIASES = {
    "d2025_gap_shock_wick_rejection": ("gap_shock_wick_rejection", 1),
    "d2025_amount_shock_wick_absorption": ("amount_shock_wick_absorption", 1),
    "d2025_clv_extreme_direction_efficiency": ("clv_extreme_direction_efficiency", 1),
    "d2025_body_shock_wick_repair": ("body_shock_wick_repair", 1),
    "d2025_gap_shock_direction_efficiency": ("gap_shock_direction_efficiency", -1),
    "d2025_clv_extreme_wick_rejection": ("clv_extreme_wick_rejection", 1),
}
_ALL_ALIASES = {**_ALL_ALIASES, **_BATCH22_ALIASES}
_DIRECTIONS.update({name: sign for name, (_, sign) in _BATCH22_ALIASES.items()})
_AMOUNT_MECHANISMS = {
    "amount_signed_imbalance",
    "amount_return_asymmetry",
    "amount_concentration",
    "amount_innovation_return_beta",
    "market_residual_amount_beta",
    "amount_gap_shock_response_corr",
    "amount_abs_body_corr",
    "amount_clv_abs_corr",
    "amount_innovation_excess_kurtosis",
    "amount_innovation_abs_change",
    "amount_lag_abs_body_corr",
    "amount_conditional_body_asymmetry",
    "amount_innovation_sign_entropy",
    "amount_shock_body_efficiency",
    "amount_shock_wick_rejection",
    "amount_shock_direction_alignment",
    "amount_shock_close_location_alignment",
    "amount_shock_gap_repair",
    "amount_shock_close_extremity",
    "amount_price_tail_mismatch_rate",
    "amount_tail_clv_alignment",
    "downside_price_impact_share",
    # Batch19 was frozen and direction-discovered as one source family whose
    # common validity mask includes canonical amount.  Preserve that exact
    # mask when an OHLC-looking subset is reloaded in Stage2.
    "body_positive_run_mean",
    "body_negative_run_mean",
    "gap_positive_run_mean",
    "gap_negative_run_mean",
    "clv_extreme_recovery_rate",
    "range_shock_compression_rate",
    "gap_body_tail_direction_asymmetry",
    "range_shock_body_absorption",
    "amount_shock_range_contraction",
    "extreme_body_amount_normalization",
    "amount_shock_clv_recovery",
    "body_shock_amount_normalization",
    # Batch20 was frozen as one source family and its common validity mask
    # includes amount innovation, even for response pairs whose readable name
    # mentions only OHLC fields.  Keep single-candidate rejudges identical to
    # the original batch instead of making coverage depend on batch siblings.
    "gap_shock_range_recovery",
    "gap_shock_clv_recovery",
    "wick_rejection_body_continuation",
    "range_shock_gap_absorption",
    "range_shock_clv_absorption",
    "gap_shock_body_reversal",
    "range_shock_body_recovery",
    "wick_rejection_range_compression",
    # Batch21 uses canonical amount for these four response atoms.
    "range_shock_amount_normalization",
    "range_shock_amount_tail_persistence",
    "range_shock_amount_sign_persistence",
    "range_shock_amount_to_range_ratio",
    "amount_shock_wick_absorption",
}
_VOLUME_MECHANISMS = {"wick_demand", "clv_volume_pressure", "lagged_volume_return_corr"}

for _luna_module in LUNA_MODULES:
    _DIRECTIONS.update(_luna_module.DIRECTIONS)


def _validate_config(cfg: dict) -> tuple[str, ...]:
    if tuple(cfg.get("windows", ())) != (WINDOW,):
        raise ValueError("daily rounds are frozen to window 20")
    definitions = cfg.get("mechanisms", {})
    if not 1 <= len(definitions) <= 16:
        raise ValueError("daily rounds require 1..16 approved mechanisms")
    unknown = set(definitions) - set(_DIRECTIONS)
    if unknown:
        raise ValueError(f"unapproved daily-round mechanisms: {sorted(unknown)}")
    bad = [name for name in definitions if definitions[name].get("direction") != _DIRECTIONS[name]]
    if bad:
        raise ValueError(f"daily-round direction mismatch: {bad}")
    return tuple(definitions)


def _panels(panels: dict[str, pd.DataFrame], names: tuple[str, ...]):
    required = {"open", "high", "low", "close"}
    base_names = {_ALL_ALIASES.get(name, (name, 1))[0] for name in names}
    if base_names & _VOLUME_MECHANISMS:
        required.add("volume")
    if base_names & _AMOUNT_MECHANISMS:
        required.add("amount")
    missing = required - set(panels)
    if missing:
        raise KeyError(f"missing daily panels: {sorted(missing)}")
    out = {key: panels[key].astype(float) for key in required}
    first = out["close"]
    if any(not first.index.equals(value.index) or not first.columns.equals(value.columns)
           for value in out.values()):
        raise ValueError("daily panels must have identical member-date axes")
    return out


def _complete_window(complete: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    return complete.astype(float).rolling(window, min_periods=window).sum().eq(window)


def _rolling_sum(value: pd.DataFrame) -> pd.DataFrame:
    return value.rolling(WINDOW, min_periods=WINDOW).sum()


def _rolling_mean(value: pd.DataFrame, complete: pd.DataFrame) -> pd.DataFrame:
    return value.rolling(WINDOW, min_periods=WINDOW).mean().where(
        _complete_window(complete)
    )


def _rolling_std(value: pd.DataFrame, complete: pd.DataFrame) -> pd.DataFrame:
    return value.rolling(WINDOW, min_periods=WINDOW).std().where(
        _complete_window(complete)
    )


def _rolling_binary_entropy(value: pd.DataFrame, complete: pd.DataFrame) -> pd.DataFrame:
    probability = value.astype(float).rolling(WINDOW, min_periods=WINDOW).mean()
    clipped = probability.clip(1e-12, 1.0 - 1e-12)
    entropy = -(clipped * np.log(clipped) + (1.0 - clipped) * np.log(1.0 - clipped))
    return entropy.where(_complete_window(complete))


def _conditional_difference(value: pd.DataFrame, positive: pd.DataFrame) -> pd.DataFrame:
    valid = value.notna() & positive.notna()
    positive_bool = positive.astype("boolean").fillna(False)
    pos = positive_bool & valid
    neg = (~positive_bool) & valid
    pos_count = pos.astype(float).rolling(WINDOW, min_periods=1).sum()
    neg_count = neg.astype(float).rolling(WINDOW, min_periods=1).sum()
    pos_mean = value.where(pos).rolling(WINDOW, min_periods=1).sum().div(
        pos_count.where(pos_count.gt(0))
    )
    neg_mean = value.where(neg).rolling(WINDOW, min_periods=1).sum().div(
        neg_count.where(neg_count.gt(0))
    )
    complete = _complete_window(valid) & pos_count.gt(0) & neg_count.gt(0)
    return (pos_mean - neg_mean).where(complete)


def _rolling_excess_kurtosis(
    value: pd.DataFrame, complete: pd.DataFrame
) -> pd.DataFrame:
    mean = value.rolling(WINDOW, min_periods=WINDOW).mean()
    second = value.pow(2).rolling(WINDOW, min_periods=WINDOW).mean()
    third = value.pow(3).rolling(WINDOW, min_periods=WINDOW).mean()
    fourth = value.pow(4).rolling(WINDOW, min_periods=WINDOW).mean()
    variance = (second - mean.pow(2)).clip(lower=0.0)
    centered_fourth = (
        fourth - 4.0 * mean * third + 6.0 * mean.pow(2) * second
        - 3.0 * mean.pow(4)
    )
    value = centered_fourth.div(variance.pow(2).where(variance.gt(0))).sub(3.0)
    return value.where(_complete_window(complete))


def _rolling_corr(
    left: pd.DataFrame, right: pd.DataFrame, complete: pd.DataFrame
) -> pd.DataFrame:
    """Pearson correlation with complete-window and zero-variance NaNs."""
    mean_left = left.rolling(WINDOW, min_periods=WINDOW).mean()
    mean_right = right.rolling(WINDOW, min_periods=WINDOW).mean()
    covariance = (
        left.mul(right).rolling(WINDOW, min_periods=WINDOW).mean()
        - mean_left * mean_right
    )
    variance_left = (
        left.pow(2).rolling(WINDOW, min_periods=WINDOW).mean()
        - mean_left.pow(2)
    ).clip(lower=0.0)
    variance_right = (
        right.pow(2).rolling(WINDOW, min_periods=WINDOW).mean()
        - mean_right.pow(2)
    ).clip(lower=0.0)
    denominator = (variance_left * variance_right).pow(0.5)
    value = covariance.div(denominator.where(denominator.gt(0)))
    return value.where(_complete_window(complete))


def _daily_gap_body(
    open_: pd.DataFrame, close: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    previous_close = close.shift(1)
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0)
    body = close.div(open_.where(open_.ne(0))).sub(1.0)
    complete = gap.notna() & body.notna()
    return gap, body, complete


def _build_gap_body_magnitude_coupling(
    open_: pd.DataFrame, close: pd.DataFrame
) -> pd.DataFrame:
    gap, body, complete = _daily_gap_body(open_, close)
    return _rolling_corr(gap.abs(), body.abs(), complete)


def _build_amount_gap_shock_response_corr(
    open_: pd.DataFrame, close: pd.DataFrame, amount: pd.DataFrame
) -> pd.DataFrame:
    gap, _, gap_complete = _daily_gap_body(open_, close)
    valid_amount = amount.gt(0)
    innovation = np.log(amount.where(valid_amount)).diff()
    complete = gap_complete & innovation.notna() & valid_amount
    return _rolling_corr(innovation, gap.abs(), complete)


def _build_range_body_absorption_corr(
    open_: pd.DataFrame,
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
) -> pd.DataFrame:
    _, body, body_complete = _daily_gap_body(open_, close)
    previous_close = close.shift(1)
    daily_range = (high - low).div(previous_close.where(previous_close.ne(0)))
    complete = body_complete & daily_range.notna()
    return _rolling_corr(daily_range, body.abs(), complete)


def _daily_shape_atoms(
    open_: pd.DataFrame,
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    amount: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    previous_close = close.shift(1)
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0)
    body = close.div(open_.where(open_.ne(0))).sub(1.0)
    daily_range = (high - low).div(previous_close.where(previous_close.ne(0)))
    price_range = high - low
    clv = (2.0 * close - high - low).div(price_range.where(price_range.gt(0)))
    body_low = pd.DataFrame(
        np.minimum(open_.to_numpy(), close.to_numpy()),
        index=open_.index, columns=open_.columns,
    )
    body_high = pd.DataFrame(
        np.maximum(open_.to_numpy(), close.to_numpy()),
        index=open_.index, columns=open_.columns,
    )
    wick = ((body_low - low) - (high - body_high)).div(
        price_range.where(price_range.gt(0))
    )
    innovation = np.log(amount.where(amount.gt(0))).diff()
    return {
        "gap": gap.replace([np.inf, -np.inf], np.nan),
        "body": body.replace([np.inf, -np.inf], np.nan),
        "range": daily_range.replace([np.inf, -np.inf], np.nan),
        "clv": clv.replace([np.inf, -np.inf], np.nan),
        "wick": wick.replace([np.inf, -np.inf], np.nan),
        "innovation": innovation.replace([np.inf, -np.inf], np.nan),
    }


def _build_batch14_daily(name: str, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    atoms = _daily_shape_atoms(
        panels["open"], panels["high"], panels["low"],
        panels["close"], panels["amount"],
    )
    gap, body = atoms["gap"], atoms["body"]
    daily_range, clv = atoms["range"], atoms["clv"]
    wick, innovation = atoms["wick"], atoms["innovation"]
    complete = {key: value.notna() for key, value in atoms.items()}
    if name == "gap_excess_kurtosis":
        return _rolling_excess_kurtosis(gap, complete["gap"])
    if name == "clv_autocorr":
        previous = clv.shift(1)
        return _rolling_corr(clv, previous, clv.notna() & previous.notna())
    if name == "gap_abs_change":
        change = gap.diff().abs()
        return _rolling_mean(change, change.notna())
    if name == "range_gap_abs_corr":
        return _rolling_corr(daily_range, gap.abs(), complete["range"] & complete["gap"])
    if name == "amount_abs_body_corr":
        return _rolling_corr(innovation, body.abs(), complete["innovation"] & complete["body"])
    if name == "amount_clv_abs_corr":
        return _rolling_corr(innovation, clv.abs(), complete["innovation"] & complete["clv"])
    if name == "clv_excess_kurtosis":
        return _rolling_excess_kurtosis(clv, complete["clv"])
    if name == "wick_abs_kurtosis":
        return _rolling_excess_kurtosis(wick.abs(), complete["wick"])
    if name == "wick_abs_change":
        change = wick.abs().diff().abs()
        return _rolling_mean(change, change.notna())
    if name == "amount_innovation_excess_kurtosis":
        return _rolling_excess_kurtosis(innovation, complete["innovation"])
    if name == "amount_innovation_abs_change":
        change = innovation.diff().abs()
        return _rolling_mean(change, change.notna())
    if name == "body_wick_abs_corr":
        return _rolling_corr(body.abs(), wick.abs(), complete["body"] & complete["wick"])
    if name == "gap_signed_body_corr":
        return _rolling_corr(gap, body, complete["gap"] & complete["body"])
    if name == "range_body_ratio_dispersion":
        ratio = body.abs().div(daily_range.abs().where(daily_range.abs().gt(0)))
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
        return _rolling_std(ratio, ratio.notna())
    raise ValueError(f"unhandled batch-14 mechanism: {name}")


def _build_batch15_daily(name: str, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    amount = panels.get("amount")
    if amount is None:
        amount = pd.DataFrame(
            np.nan, index=panels["close"].index, columns=panels["close"].columns
        )
    atoms = _daily_shape_atoms(
        panels["open"], panels["high"], panels["low"],
        panels["close"], amount,
    )
    gap, body = atoms["gap"], atoms["body"]
    daily_range, clv = atoms["range"], atoms["clv"]
    innovation = atoms["innovation"]
    # Freeze the ratio representation before the two threshold/sign atoms.
    # This removes scale-dependent boundary drift without changing either
    # economic boundary (|CLV| > 0.5 or sign(CLV)).
    clv = clv.round(12)
    if name == "gap_lag_body_corr":
        return _rolling_corr(gap.shift(1), body, gap.shift(1).notna() & body.notna())
    if name == "gap_lag_abs_body_corr":
        return _rolling_corr(gap.abs().shift(1), body.abs(), gap.shift(1).notna() & body.notna())
    if name == "range_lag_abs_body_corr":
        return _rolling_corr(daily_range.shift(1), body.abs(), daily_range.shift(1).notna() & body.notna())
    if name == "amount_lag_abs_body_corr":
        return _rolling_corr(innovation.shift(1), body.abs(), innovation.shift(1).notna() & body.notna())
    if name == "gap_conditional_body_asymmetry":
        return _conditional_difference(body.abs(), gap.gt(0).where(gap.notna()))
    if name == "amount_conditional_body_asymmetry":
        return _conditional_difference(body.abs(), innovation.gt(0).where(innovation.notna()))
    if name == "clv_abs_tail_share":
        return _rolling_mean((clv.abs() > 0.5).astype(float), clv.notna())
    if name == "body_sign_entropy":
        return _rolling_binary_entropy(body.gt(0), body.notna())
    if name == "gap_sign_entropy":
        return _rolling_binary_entropy(gap.gt(0), gap.notna())
    if name == "clv_sign_transition_rate":
        previous = clv.shift(1)
        transition = (np.sign(clv) != np.sign(previous)).astype(float)
        return _rolling_mean(transition, clv.notna() & previous.notna())
    if name == "amount_innovation_sign_entropy":
        return _rolling_binary_entropy(innovation.gt(0), innovation.notna())
    if name == "range_share_entropy":
        def entropy_window(values: np.ndarray) -> float:
            total = values.sum()
            if not np.isfinite(total) or total <= 0:
                return np.nan
            p = values / total
            return float(-(p * np.log(np.where(p > 0, p, 1.0))).sum() / np.log(WINDOW))
        return daily_range.abs().rolling(WINDOW, min_periods=WINDOW).apply(
            entropy_window, raw=True
        )
    raise ValueError(f"unhandled batch-15 mechanism: {name}")


def _build_batch16_daily(name: str, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build Batch16 daily state-transition atoms from D-close OHLC only."""
    open_, high, low, close = (
        panels["open"], panels["high"], panels["low"], panels["close"]
    )
    previous_close = close.shift(1)
    # Canonical prefix reloads can differ by a common adjustment scale.  Round
    # dimensionless states before sign/equality boundaries so a mathematically
    # identical candle cannot switch a binary state through floating noise.
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0).round(12)
    body = close.div(open_.where(open_.ne(0))).sub(1.0).round(12)
    close_return = close.div(previous_close.where(previous_close.ne(0))).sub(1.0).round(12)
    if name == "overnight_intraday_switch_rate":
        complete = close_return.notna() & body.notna()
        state = (np.sign(close_return) != np.sign(body)).astype(float)
        return _rolling_mean(state, complete)
    if name == "gap_repair_signed_magnitude":
        complete = gap.notna() & body.notna()
        state = -np.sign(gap) * body
        return _rolling_mean(state, complete)
    if name == "gap_repair_completion_rate":
        complete = gap.notna() & body.notna()
        state = (gap.ne(0) & (-np.sign(gap) * body >= gap.abs())).astype(float)
        return _rolling_mean(state, complete)
    if name == "body_wick_rejection_rate":
        candle_range = high - low
        wick_imbalance = (
            (np.minimum(open_.to_numpy(), close.to_numpy()) - low.to_numpy())
            - (high.to_numpy() - np.maximum(open_.to_numpy(), close.to_numpy()))
        )
        wick_imbalance = pd.DataFrame(
            wick_imbalance, index=open_.index, columns=open_.columns
        ).div(candle_range.where(candle_range.ne(0))).round(12)
        complete = body.notna() & wick_imbalance.notna()
        state = (np.sign(body) * np.sign(wick_imbalance) < 0).astype(float)
        return _rolling_mean(state, complete)
    raise ValueError(f"unhandled batch-16 daily mechanism: {name}")


def _build_batch17_daily(name: str, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build Batch17 amount-shock absorption atoms from D-close OHLC/amount."""
    open_, high, low, close = (
        panels[key] for key in ("open", "high", "low", "close")
    )
    # Amount is needed only by the two amount-tail definitions.  Keeping it
    # optional lets a sealed subset containing only OHLC atoms reload without
    # silently broadening its declared source fields.
    amount = panels.get("amount")
    previous_close = close.shift(1)
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0).round(12)
    body = close.div(open_.where(open_.ne(0))).sub(1.0).round(12)
    daily_range = (high - low).div(previous_close.where(previous_close.ne(0))).round(12)
    clv = (2.0 * close - high - low).div((high - low).where(high - low > 0)).round(12)
    innovation = np.log(amount.where(amount > 0)).diff().round(12)
    shock = innovation.abs()
    complete = innovation.notna() & body.notna() & daily_range.notna() & amount.gt(0)
    wick = (
        (np.minimum(open_.to_numpy(), close.to_numpy()) - low.to_numpy())
        - (high.to_numpy() - np.maximum(open_.to_numpy(), close.to_numpy()))
    )
    wick = pd.DataFrame(wick, index=open_.index, columns=open_.columns).div(
        (high - low).where((high - low).ne(0))
    ).round(12)
    if name == "amount_shock_body_efficiency":
        denominator = body.abs() + daily_range
        state = shock * body.abs().div(denominator.where(denominator > 0))
    elif name == "amount_shock_wick_rejection":
        state = shock * (np.sign(body) * np.sign(wick) < 0).astype(float)
    elif name == "amount_shock_direction_alignment":
        state = shock * np.sign(innovation) * np.sign(body)
    elif name == "amount_shock_close_location_alignment":
        state = shock * np.sign(innovation) * clv
    elif name == "amount_shock_gap_repair":
        state = shock * (-np.sign(gap) * body)
    elif name == "amount_shock_close_extremity":
        state = shock * clv.abs()
    else:
        raise ValueError(f"unhandled batch-17 daily mechanism: {name}")
    return _rolling_mean(state, complete & state.notna())


def _build_batch18_daily(name: str, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build new fixed-pool relative-residual states, all D-close causal."""
    close, high, low = panels["close"], panels["high"], panels["low"]
    returns = close.pct_change(fill_method=None)
    complete = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(complete)
    residual = returns.sub(market, axis=0).where(complete, axis=0)
    if name == "market_residual_mean":
        value = residual.rolling(WINDOW, min_periods=WINDOW).mean()
    elif name == "market_residual_upside_mean":
        value = residual.clip(lower=0).rolling(WINDOW, min_periods=WINDOW).mean()
    elif name == "market_residual_downside_mean":
        value = residual.clip(upper=0).rolling(WINDOW, min_periods=WINDOW).mean()
    elif name == "market_residual_sign_imbalance":
        value = np.sign(residual).rolling(WINDOW, min_periods=WINDOW).mean()
    elif name == "market_residual_path_efficiency":
        value = residual.rolling(WINDOW, min_periods=WINDOW).sum().div(
            residual.abs().rolling(WINDOW, min_periods=WINDOW).sum().where(
                residual.abs().rolling(WINDOW, min_periods=WINDOW).sum().ne(0)
            )
        )
    elif name == "market_residual_sign_persistence":
        value = (np.sign(residual) * np.sign(residual.shift(1))).rolling(
            WINDOW, min_periods=WINDOW
        ).mean()
    elif name == "market_residual_turning_rate":
        value = (np.sign(residual) != np.sign(residual.shift(1))).astype(float).rolling(
            WINDOW, min_periods=WINDOW
        ).mean()
    elif name == "market_residual_tail_share":
        mean_abs = residual.abs().rolling(WINDOW, min_periods=WINDOW).mean()
        numerator = residual.abs().where(residual.abs() > mean_abs)
        value = numerator.rolling(WINDOW, min_periods=WINDOW).count().div(WINDOW)
    elif name == "market_residual_market_beta":
        market_mean = market.rolling(WINDOW, min_periods=WINDOW).mean()
        covariance = residual.mul(market, axis=0).rolling(WINDOW, min_periods=WINDOW).mean() - residual.rolling(WINDOW, min_periods=WINDOW).mean().mul(market_mean, axis=0)
        variance = market.pow(2).rolling(WINDOW, min_periods=WINDOW).mean() - market_mean.pow(2)
        value = covariance.div(variance.where(variance.ne(0)), axis=0)
    elif name == "market_residual_range_absorption":
        daily_range = (high - low).div(close.shift(1).where(close.shift(1).ne(0)))
        value = residual.div(daily_range.where(daily_range.ne(0)))
    else:
        raise ValueError(f"unhandled batch-18 daily mechanism: {name}")
    return value.where(_complete_window(residual.notna()))


def _run_length(mask: pd.DataFrame) -> pd.DataFrame:
    arr = mask.fillna(False).to_numpy(bool)
    out = np.zeros(arr.shape, dtype=float)
    for j in range(arr.shape[1]):
        run = 0
        for i, flag in enumerate(arr[:, j]):
            run = run + 1 if flag else 0
            out[i, j] = run
    return pd.DataFrame(out, index=mask.index, columns=mask.columns)


def _conditional_rolling_mean(value: pd.DataFrame, condition: pd.DataFrame) -> pd.DataFrame:
    count = condition.astype(float).rolling(WINDOW, min_periods=WINDOW).sum()
    total = value.where(condition).rolling(WINDOW, min_periods=WINDOW).sum()
    return total.div(count.where(count > 0))


def _build_batch19_daily(name: str, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    open_, high, low, close, amount = (
        panels[key] for key in ("open", "high", "low", "close", "amount")
    )
    previous_close = close.shift(1)
    body = close.div(open_.where(open_.ne(0))).sub(1.0).round(12)
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0).round(12)
    daily_range = (high - low).div(previous_close.where(previous_close.ne(0))).round(12)
    clv = (2.0 * close - high - low).div((high - low).where((high - low) > 0)).round(12)
    innovation = np.log(amount.where(amount > 0)).diff().round(12)
    complete = body.notna() & gap.notna() & daily_range.notna() & amount.gt(0)
    if name == "body_positive_run_mean":
        value = _run_length(body > 0)
    elif name == "body_negative_run_mean":
        value = _run_length(body < 0)
    elif name == "gap_positive_run_mean":
        value = _run_length(gap > 0)
    elif name == "gap_negative_run_mean":
        value = _run_length(gap < 0)
    elif name == "clv_extreme_recovery_rate":
        prior_extreme = clv.abs().shift(1) > 0.5
        recovered = prior_extreme & (clv.abs() < clv.abs().shift(1))
        value = recovered.astype(float)
    elif name == "range_shock_compression_rate":
        expansion = daily_range.shift(1) > daily_range.shift(2)
        value = (expansion & (daily_range < daily_range.shift(1))).astype(float)
    elif name == "amount_price_tail_mismatch_rate":
        x_tail = innovation.abs() > innovation.abs().rolling(WINDOW, min_periods=WINDOW).mean()
        b_tail = body.abs() > body.abs().rolling(WINDOW, min_periods=WINDOW).mean()
        value = (x_tail ^ b_tail).astype(float)
    elif name == "gap_body_tail_direction_asymmetry":
        tail = gap.abs() > gap.abs().rolling(WINDOW, min_periods=WINDOW).mean()
        value = tail.astype(float) * body
    elif name == "range_shock_body_absorption":
        shock = daily_range > daily_range.shift(1)
        efficiency = body.abs().div(daily_range.where(daily_range > 0))
        value = shock.astype(float) * efficiency
    elif name == "amount_tail_clv_alignment":
        tail = innovation.abs() > innovation.abs().rolling(WINDOW, min_periods=WINDOW).mean()
        value = (tail.astype(float) * np.sign(innovation) * clv).where(tail | innovation.notna())
    else:
        raise ValueError(f"unhandled batch-19 daily mechanism: {name}")
    return _rolling_mean(value, complete & value.notna())


def _batch20_states(
    name: str, panels: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return event leg, response leg and their common causal availability."""
    open_, high, low, close, amount = (
        panels[key] for key in ("open", "high", "low", "close", "amount")
    )
    previous_close = close.shift(1)
    body = close.div(open_.where(open_.ne(0))).sub(1.0).round(12)
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0).round(12)
    daily_range = (high - low).div(previous_close.where(previous_close.ne(0))).round(12)
    clv = (2.0 * close - high - low).div((high - low).where((high - low) > 0)).round(12)
    innovation = np.log(amount.where(amount > 0)).diff().round(12)
    wick = (
        (np.minimum(open_.to_numpy(), close.to_numpy()) - low.to_numpy())
        - (high.to_numpy() - np.maximum(open_.to_numpy(), close.to_numpy()))
    )
    wick = pd.DataFrame(wick, index=open_.index, columns=open_.columns).div(
        (high - low).where((high - low).ne(0))
    ).round(12)
    body_tail = body.abs() > body.abs().rolling(WINDOW, min_periods=WINDOW).mean()
    gap_tail = gap.abs() > gap.abs().rolling(WINDOW, min_periods=WINDOW).mean()
    range_tail = daily_range > daily_range.rolling(WINDOW, min_periods=WINDOW).mean()
    amount_tail = innovation.abs() > innovation.abs().rolling(WINDOW, min_periods=WINDOW).mean()
    wick_rejection = np.sign(body) * np.sign(wick) < 0
    event = {
        "gap_shock_range_recovery": (gap_tail.shift(1), daily_range < daily_range.shift(1)),
        "gap_shock_clv_recovery": (gap_tail.shift(1), clv.abs() < clv.abs().shift(1)),
        "amount_shock_range_contraction": (amount_tail.shift(1), daily_range < daily_range.shift(1)),
        "wick_rejection_body_continuation": (wick_rejection.shift(1), np.sign(body) == np.sign(body.shift(1))),
        "range_shock_gap_absorption": (range_tail.shift(1), gap.abs() < gap.abs().shift(1)),
        "range_shock_clv_absorption": (range_tail.shift(1), clv.abs() < clv.abs().shift(1)),
        "extreme_body_amount_normalization": (body_tail.shift(1), innovation.abs() < innovation.abs().shift(1)),
        "amount_shock_clv_recovery": (amount_tail.shift(1), clv.abs() < clv.abs().shift(1)),
        "gap_shock_body_reversal": (gap_tail.shift(1), np.sign(body) * np.sign(gap.shift(1)) < 0),
        "range_shock_body_recovery": (range_tail.shift(1), body.abs() < body.abs().shift(1)),
        "wick_rejection_range_compression": (wick_rejection.shift(1), daily_range < daily_range.shift(1)),
        "body_shock_amount_normalization": (body_tail.shift(1), innovation.abs() < innovation.abs().shift(1)),
    }
    if name not in event:
        raise ValueError(f"unhandled batch-20 daily mechanism: {name}")
    event_state, response = event[name]
    complete = body.notna() & gap.notna() & daily_range.notna() & innovation.notna() & clv.notna()
    return event_state.astype(float), response.astype(float), complete


def _build_batch20_daily(name: str, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build causal event-to-next-day recovery/absorption state atoms."""
    event_state, response, complete = _batch20_states(name, panels)
    value = event_state.astype(float) * response.astype(float)
    return _rolling_mean(value, complete & value.notna())


def build_paired_legs(
    panels: dict[str, pd.DataFrame], cfg: dict, candidate: str
) -> dict[str, pd.DataFrame] | None:
    """Materialise auditable standalone legs for supported composite formulas.

    ``None`` means the formula is not declared as a two-leg composite; it does
    not mean that a required increment test passed.
    """
    if not candidate.endswith(f"_{WINDOW}"):
        return None
    mechanism = candidate.removesuffix(f"_{WINDOW}")
    formula_name, alias_sign = _ALL_ALIASES.get(mechanism, (mechanism, 1))
    if formula_name not in {
        "gap_shock_range_recovery", "gap_shock_clv_recovery",
        "amount_shock_range_contraction", "wick_rejection_body_continuation",
        "range_shock_gap_absorption", "range_shock_clv_absorption",
        "extreme_body_amount_normalization", "amount_shock_clv_recovery",
        "gap_shock_body_reversal", "range_shock_body_recovery",
        "wick_rejection_range_compression", "body_shock_amount_normalization",
    }:
        return None
    event_state, response, complete = _batch20_states(formula_name, panels)
    direction = _DIRECTIONS[mechanism]
    if direction != alias_sign:
        raise ValueError("batch-20 alias direction registry mismatch")
    return {
        "event": (_rolling_mean(event_state, complete & event_state.notna()) * direction),
        "response": (_rolling_mean(response, complete & response.notna()) * direction),
    }


def _build_batch21_daily(name: str, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build range-shock responses without using future labels or returns."""
    open_, high, low, close = (
        panels[key] for key in ("open", "high", "low", "close")
    )
    previous_close = close.shift(1)
    body = close.div(open_.where(open_.ne(0))).sub(1.0).round(12)
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0).round(12)
    daily_range = (high - low).div(previous_close.where(previous_close.ne(0))).round(12)
    wick = (
        (np.minimum(open_.to_numpy(), close.to_numpy()) - low.to_numpy())
        - (high.to_numpy() - np.maximum(open_.to_numpy(), close.to_numpy()))
    )
    wick = pd.DataFrame(wick, index=open_.index, columns=open_.columns).div(
        (high - low).where((high - low).ne(0))
    ).round(12)
    range_tail = daily_range > daily_range.rolling(WINDOW, min_periods=WINDOW).mean()
    amount_names = {
        "range_shock_amount_normalization",
        "range_shock_amount_tail_persistence",
        "range_shock_amount_sign_persistence",
        "range_shock_amount_to_range_ratio",
    }
    innovation = None
    amount_tail = None
    if name in amount_names:
        amount = panels["amount"]
        innovation = np.log(amount.where(amount > 0)).diff().round(12)
        amount_tail = innovation.abs() > innovation.abs().rolling(
            WINDOW, min_periods=WINDOW
        ).mean()
    previous_range_event = range_tail.shift(1)
    previous_innovation = innovation.shift(1) if innovation is not None else None
    event = {
        "range_shock_wick_rejection": (
            previous_range_event,
            np.sign(body) * np.sign(wick) < 0,
        ),
        "range_shock_direction_efficiency": (
            previous_range_event,
            body.abs().div(daily_range.where(daily_range > 0)),
        ),
        "range_shock_range_persistence": (
            previous_range_event,
            daily_range > daily_range.shift(1),
        ),
        "range_shock_wick_absorption": (
            previous_range_event,
            wick.abs() < wick.abs().shift(1),
        ),
    }
    if innovation is not None:
        event.update({
            "range_shock_amount_normalization": (
                previous_range_event,
                innovation.abs() < previous_innovation.abs(),
            ),
            "range_shock_amount_tail_persistence": (previous_range_event, amount_tail),
            "range_shock_amount_sign_persistence": (
                previous_range_event,
                np.sign(innovation).eq(np.sign(previous_innovation))
                & np.sign(innovation).ne(0)
                & np.sign(previous_innovation).ne(0),
            ),
            "range_shock_amount_to_range_ratio": (
                previous_range_event,
                innovation.abs().div(daily_range.where(daily_range > 0)),
            ),
        })
    if name not in event:
        raise ValueError(f"unhandled batch-21 daily mechanism: {name}")
    event_state, response = event[name]
    value = event_state.astype(float) * response.astype(float)
    complete = body.notna() & gap.notna() & daily_range.notna() & wick.notna()
    if name in amount_names:
        complete &= innovation.notna()
    return _rolling_mean(value, complete & value.notna())


def _build_batch22_daily(name: str, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build prior-event to wick/efficiency responses using D-close inputs."""
    open_, high, low, close = (
        panels[key] for key in ("open", "high", "low", "close")
    )
    previous_close = close.shift(1)
    body = close.div(open_.where(open_.ne(0))).sub(1.0).round(12)
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0).round(12)
    daily_range = (high - low).div(previous_close.where(previous_close.ne(0))).round(12)
    clv = (2.0 * close - high - low).div((high - low).where(high - low > 0)).round(12)
    wick = (
        (np.minimum(open_.to_numpy(), close.to_numpy()) - low.to_numpy())
        - (high.to_numpy() - np.maximum(open_.to_numpy(), close.to_numpy()))
    )
    wick = pd.DataFrame(wick, index=open_.index, columns=open_.columns).div(
        (high - low).where((high - low).ne(0))
    ).round(12)
    body_tail = body.abs() > body.abs().rolling(WINDOW, min_periods=WINDOW).mean()
    gap_tail = gap.abs() > gap.abs().rolling(WINDOW, min_periods=WINDOW).mean()
    clv_extreme = clv.abs() > 0.5
    wick_rejection = np.sign(body) * np.sign(wick) < 0
    amount_name = name == "amount_shock_wick_absorption"
    innovation = None
    if amount_name:
        amount = panels["amount"]
        innovation = np.log(amount.where(amount > 0)).diff().round(12)
    event = {
        "clv_extreme_direction_efficiency": (
            clv_extreme.shift(1),
            body.abs().div(daily_range.where(daily_range > 0)),
        ),
        "body_shock_wick_repair": (
            body_tail.shift(1),
            wick.abs() < wick.abs().shift(1),
        ),
        "gap_shock_direction_efficiency": (
            gap_tail.shift(1),
            body.abs().div(daily_range.where(daily_range > 0)),
        ),
        "clv_extreme_wick_rejection": (
            clv_extreme.shift(1),
            wick_rejection,
        ),
    }
    event.update({
        "gap_shock_wick_rejection": (
            gap_tail.shift(1),
            wick_rejection,
        ),
        "gap_shock_direction_efficiency": (
            gap_tail.shift(1),
            body.abs().div(daily_range.where(daily_range > 0)),
        ),
        "clv_extreme_wick_rejection": (
            clv_extreme.shift(1),
            wick_rejection,
        ),
    })
    if innovation is not None:
        amount_tail = innovation.abs() > innovation.abs().rolling(
            WINDOW, min_periods=WINDOW
        ).mean()
        event["amount_shock_wick_absorption"] = (
            amount_tail.shift(1),
            wick.abs() < wick.abs().shift(1),
        )
    if name not in event:
        raise ValueError(f"unhandled batch-22 daily mechanism: {name}")
    event_state, response = event[name]
    value = event_state.astype(float) * response.astype(float)
    complete = body.notna() & gap.notna() & daily_range.notna() & clv.notna() & wick.notna()
    if amount_name:
        complete &= innovation.notna()
    return _rolling_mean(value, complete & value.notna())


def _build_market_residual_downside(close: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    # Do not let DataFrame.mean(skipna=True) create a partial market reference.
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    residual = returns.sub(market, axis=0).where(all_members, axis=0)
    value = np.sqrt(residual.clip(upper=0).pow(2).rolling(WINDOW, min_periods=WINDOW).mean())
    return value.where(_complete_window(residual.notna()))


def _market_residuals(close: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    return returns.sub(market, axis=0).where(all_members, axis=0)


def _build_market_residual_skew(close: pd.DataFrame) -> pd.DataFrame:
    residual = _market_residuals(close)
    mean = residual.rolling(WINDOW, min_periods=WINDOW).mean()
    second = residual.pow(2).rolling(WINDOW, min_periods=WINDOW).mean()
    third = residual.pow(3).rolling(WINDOW, min_periods=WINDOW).mean()
    centered_second = (second - mean.pow(2)).clip(lower=0.0)
    centered_third = third - 3.0 * mean * second + 2.0 * mean.pow(3)
    value = centered_third.div(centered_second.pow(1.5).where(centered_second.gt(0)))
    return value.where(_complete_window(residual.notna()))


def _build_market_residual_abs_cluster(close: pd.DataFrame) -> pd.DataFrame:
    residual = _market_residuals(close)
    lagged = residual.abs().shift(1)
    current = residual.abs()
    complete = lagged.notna() & current.notna()
    value = lagged.rolling(WINDOW, min_periods=WINDOW).corr(current)
    return value.where(_complete_window(complete))


def _build_market_residual_downshock_recovery(close: pd.DataFrame) -> pd.DataFrame:
    residual = _market_residuals(close)
    previous_down = residual.shift(1).clip(upper=0).abs()
    complete = previous_down.notna() & residual.notna()
    numerator = _rolling_sum(previous_down * residual)
    denominator = _rolling_sum(previous_down.pow(2))
    value = numerator.div(denominator.where(denominator.ne(0)))
    return value.where(_complete_window(complete))


def _build_market_residual_range_return_lead(
    high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame
) -> pd.DataFrame:
    residual = _market_residuals(close)
    daily_range = (high - low).div(close.shift(1))
    lagged_range = daily_range.shift(1)
    complete = lagged_range.notna() & residual.notna()
    value = lagged_range.rolling(WINDOW, min_periods=WINDOW).corr(residual)
    return value.where(_complete_window(complete))


def _build_market_residual_amount_beta(
    close: pd.DataFrame, amount: pd.DataFrame
) -> pd.DataFrame:
    residual = _market_residuals(close)
    log_amount = np.log(amount.where(amount.gt(0)))
    innovation = log_amount.diff()
    complete = innovation.notna() & residual.notna()
    mean_x = innovation.rolling(WINDOW, min_periods=WINDOW).mean()
    mean_u = residual.rolling(WINDOW, min_periods=WINDOW).mean()
    covariance = (
        innovation.mul(residual).rolling(WINDOW, min_periods=WINDOW).mean()
        - mean_x * mean_u
    )
    variance = (
        innovation.pow(2).rolling(WINDOW, min_periods=WINDOW).mean()
        - mean_x.pow(2)
    )
    value = covariance.div(variance.where(variance.gt(0)))
    return value.where(_complete_window(complete))


def _build_intraday_body_ar1(open_: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    body = close.div(open_).sub(1.0)
    previous = body.shift(1)
    complete = body.notna() & previous.notna()
    value = body.rolling(WINDOW, min_periods=WINDOW).corr(previous)
    return value.where(_complete_window(complete))


def _build_wick_body_coupling(
    open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame
) -> pd.DataFrame:
    body = close.div(open_).sub(1.0)
    wick_imbalance = (
        (np.minimum(open_.to_numpy(), close.to_numpy()) - low.to_numpy())
        - (high.to_numpy() - np.maximum(open_.to_numpy(), close.to_numpy()))
    )
    wick_imbalance = pd.DataFrame(
        wick_imbalance, index=open_.index, columns=open_.columns
    ).div((high - low).where((high - low).ne(0)))
    complete = body.notna() & wick_imbalance.notna()
    value = wick_imbalance.rolling(WINDOW, min_periods=WINDOW).corr(body)
    return value.where(_complete_window(complete))


def _build_close_location_dispersion(
    high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame
) -> pd.DataFrame:
    close_location = (2.0 * close - high - low).div((high - low).where((high - low).ne(0)))
    return close_location.rolling(WINDOW, min_periods=WINDOW).std().where(
        _complete_window(close_location.notna())
    )


def _build_range_to_return_lead(
    high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame
) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    daily_range = (high - low).div(close.shift(1))
    lagged_range = daily_range.shift(1)
    complete = lagged_range.notna() & returns.notna()
    value = lagged_range.rolling(WINDOW, min_periods=WINDOW).corr(returns)
    return value.where(_complete_window(complete))


def _build_direction_range_coupling(
    high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame
) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    previous_close = close.shift(1)
    daily_range = (high - low).div(previous_close.where(previous_close.ne(0)))
    complete = returns.notna() & daily_range.notna()
    value = returns.rolling(WINDOW, min_periods=WINDOW).corr(daily_range)
    return value.where(_complete_window(complete))


def _build_body_transition_asymmetry(open_: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    body = np.sign(close.div(open_).sub(1.0))
    previous = body.shift(1)
    valid_pair = body.notna() & previous.notna()
    neg_prev = previous.eq(-1) & valid_pair
    pos_prev = previous.eq(1) & valid_pair
    neg_to_pos = neg_prev & body.eq(1)
    pos_to_neg = pos_prev & body.eq(-1)
    # A trailing 20-body state block contains exactly 19 adjacent
    # transitions.  Rolling the transition series by 20 would accidentally
    # use 20 transitions after the first mature date and invalidate every
    # subsequent output.
    transition_sum = lambda value: value.rolling(WINDOW - 1, min_periods=WINDOW - 1).sum()
    neg_count = transition_sum(neg_prev.astype(float))
    pos_count = transition_sum(pos_prev.astype(float))
    p_neg_to_pos = transition_sum(neg_to_pos.astype(float)).div(neg_count.where(neg_count.ne(0)))
    p_pos_to_neg = transition_sum(pos_to_neg.astype(float)).div(pos_count.where(pos_count.ne(0)))
    value = p_neg_to_pos - p_pos_to_neg
    return value.where(_complete_window(body.notna()))


def _build_realized_vol_term_structure(close: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    short = returns.rolling(5, min_periods=5).std()
    long = returns.rolling(WINDOW, min_periods=WINDOW).std()
    return short.div(long.where(long.ne(0))).where(_complete_window(returns.notna()))


def _build_amount_signed_imbalance(close: pd.DataFrame, amount: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    complete = close.notna() & amount.gt(0)
    numerator = _rolling_sum(amount * np.sign(returns))
    denominator = _rolling_sum(amount).where(_rolling_sum(amount).ne(0))
    return numerator.div(denominator).where(_complete_window(complete))


def _build_amount_return_asymmetry(close: pd.DataFrame, amount: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    positive = returns.clip(lower=0)
    negative = returns.clip(upper=0).abs()
    complete = close.notna() & amount.gt(0)
    numerator = _rolling_sum(amount * (positive - negative))
    denominator = _rolling_sum(amount * (positive + negative))
    return numerator.div(denominator.where(denominator.ne(0))).where(_complete_window(complete))


def _build_amount_concentration(amount: pd.DataFrame) -> pd.DataFrame:
    complete = amount.gt(0)
    total = _rolling_sum(amount)
    value = _rolling_sum(amount.pow(2)).div(total.pow(2).where(total.ne(0)))
    return value.where(_complete_window(complete))


def _build_amount_innovation_return_beta(
    close: pd.DataFrame, amount: pd.DataFrame
) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    log_amount = np.log(amount.where(amount.gt(0)))
    innovation = log_amount.diff()
    complete = returns.notna() & innovation.notna()
    mean_x = innovation.rolling(WINDOW, min_periods=WINDOW).mean()
    mean_r = returns.rolling(WINDOW, min_periods=WINDOW).mean()
    covariance = (
        innovation.mul(returns).rolling(WINDOW, min_periods=WINDOW).mean()
        - mean_x * mean_r
    )
    variance = (
        innovation.pow(2).rolling(WINDOW, min_periods=WINDOW).mean()
        - mean_x.pow(2)
    )
    value = covariance.div(variance.where(variance.gt(0)))
    return value.where(_complete_window(complete))


def _build_return_acceleration(close: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    short = returns.rolling(5, min_periods=5).mean()
    long = returns.rolling(WINDOW, min_periods=WINDOW).mean()
    return short.sub(long).where(_complete_window(returns.notna()))


def _build_underwater_time_share(close: pd.DataFrame) -> pd.DataFrame:
    """Share of the trailing 20 closes below their own prior 20-session peak.

    For each date t, the reference peak uses close[t-20:t-1] in inclusive
    trading-session terms (20 observations ending at t-1). The output averages
    comparisons for t-19..t, so a complete output requires 40 closes through t.
    """
    prior_peak = close.shift(1).rolling(WINDOW, min_periods=WINDOW).max()
    underwater = close.lt(prior_peak).where(close.notna() & prior_peak.notna())
    value = underwater.astype(float).rolling(WINDOW, min_periods=WINDOW).mean()
    return value.where(_complete_window(close.notna(), 2 * WINDOW))


def _build_bipower_jump_share(close: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    rv = returns.pow(2).rolling(WINDOW, min_periods=WINDOW).sum()
    adjacent_abs_products = returns.abs().mul(returns.shift(1).abs())
    # The 19 adjacent pairs are wholly inside the same 20-return window.
    bv = (np.pi / 2.0) * (WINDOW / (WINDOW - 1.0)) * adjacent_abs_products.rolling(
        WINDOW - 1, min_periods=WINDOW - 1
    ).sum()
    valid = _complete_window(returns.notna())
    value = (rv - bv).clip(lower=0.0).div(rv.where(rv.gt(0.0)))
    return value.where(valid)


def _build_market_coskewness(close: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    returns = returns.where(all_members, axis=0)
    result = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    for symbol in close.columns:
        own = returns[symbol]
        peer = (returns.sum(axis=1) - own) / (len(close.columns) - 1)
        x = own.to_numpy(dtype=float)
        y = peer.to_numpy(dtype=float)
        out = np.full(len(x), np.nan)
        for end in range(WINDOW - 1, len(x)):
            start = end - WINDOW + 1
            xs, ys = x[start : end + 1], y[start : end + 1]
            if not (np.isfinite(xs).all() and np.isfinite(ys).all()):
                continue
            xc, yc = xs - xs.mean(), ys - ys.mean()
            x_sd = np.sqrt(np.mean(xc * xc))
            y_var = np.mean(yc * yc)
            denom = x_sd * y_var
            if denom > 0.0:
                out[end] = np.mean(xc * yc * yc) / denom
        result[symbol] = out
    return result


def _build_ohlc_range_overlap(high: pd.DataFrame, low: pd.DataFrame) -> pd.DataFrame:
    prior_high, prior_low = high.shift(1), low.shift(1)
    # Explicit elementwise bounds avoid alignment ambiguities with duplicate columns.
    overlap_width = pd.DataFrame(
        np.maximum(
            0.0,
            np.minimum(high.to_numpy(), prior_high.to_numpy())
            - np.maximum(low.to_numpy(), prior_low.to_numpy()),
        ),
        index=high.index,
        columns=high.columns,
    )
    union_width = pd.DataFrame(
        np.maximum(high.to_numpy(), prior_high.to_numpy())
        - np.minimum(low.to_numpy(), prior_low.to_numpy()),
        index=high.index,
        columns=high.columns,
    )
    pair = overlap_width.div(union_width.where(union_width.gt(0.0)))
    valid_pair = high.notna() & low.notna() & prior_high.notna() & prior_low.notna()
    pair = pair.where(valid_pair & union_width.gt(0.0))
    return pair.rolling(WINDOW, min_periods=WINDOW).mean().where(
        _complete_window(valid_pair & union_width.gt(0.0))
    )


def _build_intraday_body_utilization(
    open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame
) -> pd.DataFrame:
    span = high - low
    value = (close - open_).abs().div(span.where(span.gt(0.0)))
    valid = open_.notna() & high.notna() & low.notna() & close.notna() & span.gt(0.0)
    return value.rolling(WINDOW, min_periods=WINDOW).mean().where(_complete_window(valid))


def _build_downside_semivariance_share(close: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    down_sq = returns.clip(upper=0.0).pow(2)
    total = returns.pow(2)
    numerator = down_sq.rolling(WINDOW, min_periods=WINDOW).sum()
    denominator = total.rolling(WINDOW, min_periods=WINDOW).sum()
    return numerator.div(denominator.where(denominator.gt(0.0))).where(
        _complete_window(returns.notna())
    )


def _build_squared_return_ar1(close: pd.DataFrame) -> pd.DataFrame:
    returns_sq = close.pct_change(fill_method=None).pow(2)
    lagged = returns_sq.shift(1)
    valid = returns_sq.notna() & lagged.notna()
    value = returns_sq.rolling(WINDOW, min_periods=WINDOW).corr(lagged)
    return value.where(_complete_window(valid))


def _build_overnight_variance_share(
    open_: pd.DataFrame, close: pd.DataFrame
) -> pd.DataFrame:
    gap = np.log(open_.div(close.shift(1).where(close.shift(1).gt(0.0))))
    body = np.log(close.div(open_.where(open_.gt(0.0))))
    valid = gap.notna() & body.notna() & open_.gt(0.0) & close.gt(0.0)
    gap_sq = gap.pow(2).rolling(WINDOW, min_periods=WINDOW).sum()
    total = (gap.pow(2) + body.pow(2)).rolling(WINDOW, min_periods=WINDOW).sum()
    return gap_sq.div(total.where(total.gt(0.0))).where(_complete_window(valid))


def _build_close_extrema_time_order(close: pd.DataFrame) -> pd.DataFrame:
    def order(values: np.ndarray) -> float:
        if not np.isfinite(values).all() or values[-1] == 0.0:
            return np.nan
        relative = values / values[-1]
        high, low = np.max(relative), np.min(relative)
        high_times = np.flatnonzero(np.isclose(relative, high, rtol=1e-12, atol=0.0))
        low_times = np.flatnonzero(np.isclose(relative, low, rtol=1e-12, atol=0.0))
        return (float(high_times.mean()) - float(low_times.mean())) / (WINDOW - 1.0)

    value = close.rolling(WINDOW, min_periods=WINDOW).apply(order, raw=True)
    return value.where(_complete_window(close.notna()))


def _build_downside_price_impact_share(
    close: pd.DataFrame, amount: pd.DataFrame
) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    valid = returns.notna() & amount.gt(0.0)
    down_impact = returns.clip(upper=0.0).abs().div(amount.where(amount.gt(0.0)))
    total_impact = returns.abs().div(amount.where(amount.gt(0.0)))
    numerator = down_impact.rolling(WINDOW, min_periods=WINDOW).sum()
    denominator = total_impact.rolling(WINDOW, min_periods=WINDOW).sum()
    return numerator.div(denominator.where(denominator.gt(0.0))).where(
        _complete_window(valid)
    )


def _build_peer_lag_return_beta(close: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    returns = returns.where(all_members, axis=0)
    result = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    for symbol in close.columns:
        own = returns[symbol]
        peer = (returns.sum(axis=1) - own) / (len(close.columns) - 1)
        peer_lag = peer.shift(1)
        valid = own.notna() & peer_lag.notna()
        cov = own.rolling(WINDOW, min_periods=WINDOW).cov(peer_lag, ddof=0)
        var = peer_lag.rolling(WINDOW, min_periods=WINDOW).var(ddof=0)
        result[symbol] = cov.div(var.where(var.gt(0.0))).where(
            _complete_window(valid)
        )
    return result


def build_atoms(panels: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    """Build selected approved member atoms with complete-window NaN propagation."""
    names = _validate_config(cfg)
    delegated = {}
    for module in LUNA_MODULES:
        selected = {name: cfg['mechanisms'][name] for name in names if name in module.DIRECTIONS}
        if selected:
            delegated.update(module.build_atoms(panels, {**cfg, 'mechanisms': selected}))
    names = [name for name in names if not any(name in m.DIRECTIONS for m in LUNA_MODULES)]
    if not names:
        return delegated
    p = _panels(panels, names)
    open_, high, low, close = (p[key] for key in ("open", "high", "low", "close"))
    if set(names) & {"market_coskewness", "peer_lag_return_beta"} and close.shape[1] != 14:
        raise ValueError("cross-ETF daily mechanisms require the fixed 14-member population")
    volume = p.get("volume")
    amount = p.get("amount")
    complete_ohlc = open_.notna() & high.notna() & low.notna() & close.notna()
    values: dict[str, pd.DataFrame] = dict(delegated)
    with np.errstate(divide="ignore", invalid="ignore"):
        for name in names:
            formula_name = _ALL_ALIASES.get(name, (name, 1))[0]
            if formula_name == "wick_demand":
                body_low = pd.DataFrame(np.minimum(open_.to_numpy(), close.to_numpy()), index=open_.index, columns=open_.columns)
                body_high = pd.DataFrame(np.maximum(open_.to_numpy(), close.to_numpy()), index=open_.index, columns=open_.columns)
                value = ((body_low - low) - (high - body_high)).div(high - low)
                value = value.rolling(WINDOW, min_periods=WINDOW).mean()
                value = value.where(_complete_window(complete_ohlc & volume.notna()))
            elif formula_name == "clv_volume_pressure":
                clv = (2.0 * close - high - low).div((high - low).where(high - low > 0))
                positive_volume = volume.where(volume > 0)
                volume_median = positive_volume.rolling(WINDOW, min_periods=WINDOW).median()
                value = (clv * volume.div(volume_median.where(volume_median > 0))).rolling(WINDOW, min_periods=WINDOW).mean()
                value = value.where(_complete_window(complete_ohlc & volume.notna()))
            elif formula_name == "lagged_volume_return_corr":
                returns = close.pct_change(fill_method=None)
                lagged_volume_change = volume.shift(1).pct_change(fill_method=None)
                value = lagged_volume_change.rolling(WINDOW, min_periods=WINDOW).corr(returns)
                value = value.where(_complete_window(complete_ohlc & volume.notna()))
            elif formula_name == "market_residual_downside":
                value = _build_market_residual_downside(close)
            elif formula_name == "market_residual_skew":
                value = _build_market_residual_skew(close)
            elif formula_name == "market_residual_abs_cluster":
                value = _build_market_residual_abs_cluster(close)
            elif formula_name == "market_residual_downshock_recovery":
                value = _build_market_residual_downshock_recovery(close)
            elif formula_name == "market_residual_range_return_lead":
                value = _build_market_residual_range_return_lead(high, low, close)
            elif formula_name == "market_residual_amount_beta":
                value = _build_market_residual_amount_beta(close, amount)
            elif formula_name == "intraday_body_ar1":
                value = _build_intraday_body_ar1(open_, close)
            elif formula_name == "wick_body_coupling":
                value = _build_wick_body_coupling(open_, high, low, close)
            elif formula_name == "close_location_dispersion":
                value = _build_close_location_dispersion(high, low, close)
            elif formula_name == "range_to_return_lead":
                value = _build_range_to_return_lead(high, low, close)
            elif formula_name == "direction_range_coupling":
                value = _build_direction_range_coupling(high, low, close)
            elif formula_name == "gap_body_magnitude_coupling":
                value = _build_gap_body_magnitude_coupling(open_, close)
            elif formula_name == "amount_gap_shock_response_corr":
                value = _build_amount_gap_shock_response_corr(open_, close, amount)
            elif formula_name == "range_body_absorption_corr":
                value = _build_range_body_absorption_corr(open_, high, low, close)
            elif formula_name.startswith((
                "gap_excess_kurtosis", "clv_autocorr", "gap_abs_change",
                "range_gap_abs_corr", "amount_abs_body_corr",
                "amount_clv_abs_corr", "clv_excess_kurtosis",
                "wick_abs_kurtosis", "wick_abs_change",
                "amount_innovation_excess_kurtosis",
                "amount_innovation_abs_change", "body_wick_abs_corr",
                "gap_signed_body_corr", "range_body_ratio_dispersion",
            )):
                value = _build_batch14_daily(formula_name, p)
            elif formula_name in {
                "overnight_intraday_switch_rate",
                "gap_repair_signed_magnitude",
                "gap_repair_completion_rate",
                "body_wick_rejection_rate",
            }:
                value = _build_batch16_daily(formula_name, p)
            elif formula_name in {
                "amount_shock_body_efficiency",
                "amount_shock_wick_rejection",
                "amount_shock_direction_alignment",
                "amount_shock_close_location_alignment",
                "amount_shock_gap_repair",
                "amount_shock_close_extremity",
            }:
                value = _build_batch17_daily(formula_name, p)
            elif formula_name in {
                "market_residual_mean", "market_residual_upside_mean",
                "market_residual_downside_mean", "market_residual_sign_imbalance",
                "market_residual_path_efficiency", "market_residual_sign_persistence",
                "market_residual_turning_rate", "market_residual_tail_share",
                "market_residual_market_beta", "market_residual_range_absorption",
            }:
                value = _build_batch18_daily(formula_name, p)
            elif formula_name in {
                "body_positive_run_mean", "body_negative_run_mean",
                "gap_positive_run_mean", "gap_negative_run_mean",
                "clv_extreme_recovery_rate", "range_shock_compression_rate",
                "amount_price_tail_mismatch_rate", "gap_body_tail_direction_asymmetry",
                "range_shock_body_absorption", "amount_tail_clv_alignment",
            }:
                value = _build_batch19_daily(formula_name, p)
            elif formula_name in {
                "gap_shock_range_recovery", "gap_shock_clv_recovery",
                "amount_shock_range_contraction", "wick_rejection_body_continuation",
                "range_shock_gap_absorption", "range_shock_clv_absorption",
                "extreme_body_amount_normalization", "amount_shock_clv_recovery",
                "gap_shock_body_reversal", "range_shock_body_recovery",
                "wick_rejection_range_compression", "body_shock_amount_normalization",
            }:
                value = _build_batch20_daily(formula_name, p)
            elif formula_name in {
                "range_shock_amount_normalization",
                "range_shock_amount_tail_persistence",
                "range_shock_amount_sign_persistence",
                "range_shock_amount_to_range_ratio",
                "range_shock_wick_rejection",
                "range_shock_direction_efficiency",
                "range_shock_range_persistence",
                "range_shock_wick_absorption",
            }:
                value = _build_batch21_daily(formula_name, p)
            elif formula_name in {
                "gap_shock_wick_rejection",
                "amount_shock_wick_absorption",
                "clv_extreme_direction_efficiency",
                "body_shock_wick_repair",
                "gap_shock_direction_efficiency",
                "clv_extreme_wick_rejection",
            }:
                value = _build_batch22_daily(formula_name, p)
            elif formula_name.startswith((
                "gap_lag_body_corr", "gap_lag_abs_body_corr",
                "range_lag_abs_body_corr", "amount_lag_abs_body_corr",
                "gap_conditional_body_asymmetry",
                "amount_conditional_body_asymmetry", "clv_abs_tail_share",
                "body_sign_entropy", "gap_sign_entropy",
                "clv_sign_transition_rate", "amount_innovation_sign_entropy",
                "range_share_entropy",
            )):
                value = _build_batch15_daily(formula_name, p)
            elif formula_name == "body_transition_asymmetry":
                value = _build_body_transition_asymmetry(open_, close)
            elif formula_name in {
                "realized_vol_term_structure_5",
                "reverse_realized_vol_term_structure_5",
            }:
                value = _build_realized_vol_term_structure(close)
            elif formula_name == "amount_signed_imbalance":
                value = _build_amount_signed_imbalance(close, amount)
            elif formula_name == "amount_return_asymmetry":
                value = _build_amount_return_asymmetry(close, amount)
            elif formula_name == "amount_concentration":
                value = _build_amount_concentration(amount)
            elif formula_name == "amount_innovation_return_beta":
                value = _build_amount_innovation_return_beta(close, amount)
            elif formula_name == "return_acceleration_5":
                value = _build_return_acceleration(close)
            elif formula_name == "underwater_time_share":
                value = _build_underwater_time_share(close)
            elif formula_name == "bipower_jump_share":
                value = _build_bipower_jump_share(close)
            elif formula_name == "market_coskewness":
                value = _build_market_coskewness(close)
            elif formula_name == "ohlc_range_overlap":
                value = _build_ohlc_range_overlap(high, low)
            elif formula_name == "intraday_body_utilization":
                value = _build_intraday_body_utilization(open_, high, low, close)
            elif formula_name == "downside_semivariance_share":
                value = _build_downside_semivariance_share(close)
            elif formula_name == "squared_return_ar1":
                value = _build_squared_return_ar1(close)
            elif formula_name == "overnight_variance_share":
                value = _build_overnight_variance_share(open_, close)
            elif formula_name == "close_extrema_time_order":
                value = _build_close_extrema_time_order(close)
            elif formula_name == "downside_price_impact_share":
                value = _build_downside_price_impact_share(close, amount)
            elif formula_name == "peer_lag_return_beta":
                value = _build_peer_lag_return_beta(close)
            else:  # guarded by _validate_config; keep fail-closed if edited.
                raise ValueError(f"unhandled daily-round mechanism: {name}")
            values[f"{name}_{WINDOW}"] = (value * _DIRECTIONS[name]).replace([np.inf, -np.inf], np.nan)
    return values


def leakage_checks(panels: dict[str, pd.DataFrame], cfg: dict, cut: str | pd.Timestamp) -> dict[str, bool]:
    """Assert prefix invariance and future-value perturbation invariance."""
    cut = pd.Timestamp(cut)
    full = build_atoms(panels, cfg)
    prefix_panels = {k: v.loc[:cut].copy() for k, v in panels.items()}
    prefix = build_atoms(prefix_panels, cfg)
    perturbed = {k: v.copy() for k, v in panels.items()}
    for value in perturbed.values():
        value.loc[value.index > cut] *= 1.71
    future = build_atoms(perturbed, cfg)
    checks: dict[str, bool] = {}
    for name, atom in full.items():
        pd.testing.assert_frame_equal(atom.loc[:cut], prefix[name].loc[:cut], check_exact=False, rtol=1e-10, atol=1e-12)
        pd.testing.assert_frame_equal(atom.loc[:cut], future[name].loc[:cut], check_exact=False, rtol=1e-10, atol=1e-12)
        checks[f"{name}:prefix"] = True
        checks[f"{name}:future_perturbation"] = True
    return checks
