"""Outcome-microscope daily atoms for the fixed ETF group campaign.

This module consumes the adjusted research panels produced by
``canonical_data.load_canonical_daily`` (unadjusted ``1d`` plus
``adj_factor``).  It does not load files itself and deliberately has no
direct file-cache, outcome, or historical-runner dependency.

The returned values are raw atoms.  Direction is frozen in the campaign
configuration because these atoms were proposed from a seen 2025 outcome
microscope; they are not presented as mechanism priors or certification.
"""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


WINDOW = 20
CANDIDATE_ATOMS = (
    "VAR_RATIO_5_60",
    "RETURN_AUTOCOV_20",
    "DOWN_UP_ACTIVITY_20",
    "SHOCK_ACTIVITY_RESPONSE_20",
    "RANGE_ACTIVITY_ELASTICITY_20",
    "VOL_RESPONSE_ASYMMETRY_20",
    "RETURN_CONCENTRATION_20",
    "OVERHEAD_TURNOVER_20",
)
EXPECTED_DIRECTIONS = {
    "VAR_RATIO_5_60": 1,
    "RETURN_AUTOCOV_20": 1,
    "DOWN_UP_ACTIVITY_20": -1,
    "SHOCK_ACTIVITY_RESPONSE_20": -1,
    "RANGE_ACTIVITY_ELASTICITY_20": 1,
    "VOL_RESPONSE_ASYMMETRY_20": -1,
    "RETURN_CONCENTRATION_20": 1,
    "OVERHEAD_TURNOVER_20": -1,
}


def _validate_config(config: Mapping[str, object]) -> None:
    if config.get("source_type") != "daily_outcome":
        raise ValueError("outcome campaign requires source_type=daily_outcome")
    if config.get("campaign_extension") is not True:
        raise ValueError("outcome campaign must declare campaign_extension=true")
    prior = config.get("prior_registered")
    cap = config.get("budget_cap")
    expected_cap = prior if config.get("rejudge_of") else (
        prior + len(CANDIDATE_ATOMS) if type(prior) is int else None
    )
    if type(prior) is not int or prior < 117 or cap != expected_cap:
        raise ValueError("outcome campaign budget/rejudge contract mismatch")
    if list(config.get("windows", [])) != [WINDOW]:
        raise ValueError("outcome campaign freezes windows=[20]")
    mechanisms = config.get("mechanisms")
    if not isinstance(mechanisms, Mapping):
        raise ValueError("outcome campaign mechanisms must be a mapping")
    names = list(mechanisms)
    if len(names) != len(CANDIDATE_ATOMS) or tuple(names) != CANDIDATE_ATOMS:
        raise ValueError("candidate whitelist/order does not match the eight outcome atoms")
    if len(set(names)) != len(names):
        raise ValueError("candidate whitelist contains duplicates")
    if any(type(mechanisms[name].get("direction")) is not int
           or mechanisms[name].get("direction") != EXPECTED_DIRECTIONS[name]
           for name in names):
        raise ValueError("outcome campaign direction whitelist mismatch")
    candidates = config.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("outcome campaign candidates must be a list")
    candidate_names = [item.get("name") for item in candidates if isinstance(item, Mapping)]
    if candidate_names != names:
        raise ValueError("explicit candidates whitelist does not match mechanisms")
    if any(type(item.get("direction")) is not int
           or item.get("direction") != EXPECTED_DIRECTIONS[item.get("name")]
           for item in candidates):
        raise ValueError("explicit candidate directions do not match whitelist")


def _validate_panels(panels: Mapping[str, pd.DataFrame]) -> tuple[pd.DataFrame, ...]:
    required = ("open", "high", "low", "close", "amount")
    missing = [name for name in required if name not in panels]
    if missing:
        raise ValueError(f"canonical outcome panels missing fields: {missing}")
    reference = panels["close"]
    if not isinstance(reference, pd.DataFrame):
        raise TypeError("canonical panels must be pandas DataFrames")
    if not reference.index.is_monotonic_increasing or reference.index.has_duplicates:
        raise ValueError("canonical panel index must be sorted and unique")
    if reference.columns.has_duplicates:
        raise ValueError("canonical panel columns must be unique")
    for name in required:
        frame = panels[name]
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"canonical panel {name} must be a DataFrame")
        if not frame.index.equals(reference.index) or not frame.columns.equals(reference.columns):
            raise ValueError(f"canonical panel {name} is not aligned with close")
    return tuple(panels[name].astype(float) for name in required)


def _strict_corr(left: pd.DataFrame, right: pd.DataFrame, window: int) -> pd.DataFrame:
    valid = left.notna() & right.notna()
    out = left.rolling(window, min_periods=window).corr(right)
    complete = valid.rolling(window, min_periods=window).sum().eq(window)
    return out.where(complete)


def _conditional_mean(
    values: pd.DataFrame,
    condition: pd.DataFrame,
    valid: pd.DataFrame,
    window: int,
    minimum_count: int,
) -> pd.DataFrame:
    complete = valid.rolling(window, min_periods=window).sum().eq(window)
    count = condition.astype(float).where(valid).rolling(
        window, min_periods=window
    ).sum()
    total = values.where(condition, 0.0).where(valid).rolling(
        window, min_periods=window
    ).sum()
    return total.div(count.where(count >= minimum_count)).where(complete)


def _overhead_turnover(
    typical: pd.DataFrame,
    close: pd.DataFrame,
    amount: pd.DataFrame,
    window: int,
) -> pd.DataFrame:
    """Turnover fraction at historical typical prices above current close."""
    result = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    for symbol in close.columns:
        tp = typical[symbol].to_numpy(dtype=float)
        cp = close[symbol].to_numpy(dtype=float)
        amt = amount[symbol].to_numpy(dtype=float)
        for end in range(window - 1, len(close.index)):
            start = end - window + 1
            tp_window = tp[start : end + 1]
            amount_window = amt[start : end + 1]
            current_close = cp[end]
            if (
                not np.isfinite(tp_window).all()
                or not np.isfinite(amount_window).all()
                or not np.isfinite(current_close)
                or (amount_window <= 0).any()
            ):
                continue
            denominator = amount_window.sum()
            if denominator <= 0:
                continue
            # Canonical adjusted histories are normalized by the last factor
            # available at each as-of date. Compare in relative units and
            # treat numerical equality as equality so prefix reloads cannot
            # flip an economically zero-distance price bucket.
            relative_price = tp_window / current_close
            above = relative_price > (1.0 + 1e-12)
            result.iat[end, result.columns.get_loc(symbol)] = (
                amount_window[above].sum() / denominator
            )
    return result


def build_outcome_atoms(
    panels: Mapping[str, pd.DataFrame],
    config: Mapping[str, object],
) -> dict[str, pd.DataFrame]:
    """Build the exact eight D-close outcome-microscope atoms.

    All rolling windows are right aligned and require complete observations.
    ``VAR_RATIO_5_60`` first forms rolling five-session return sums and then
    takes their sample variance over the most recent 60 such sums.  Its
    denominator is five times the sample variance of the 60 daily returns.
    """
    _validate_config(config)
    _, high, low, close, amount = _validate_panels(panels)
    returns = close.pct_change(fill_method=None)
    log_amount = np.log(amount.where(amount > 0))
    span = (high - low).div(close.replace(0.0, np.nan))

    rolling_return_sum_5 = returns.rolling(5, min_periods=5).sum()
    # The inner aggregation is fixed at five sessions and the outer sample
    # variance is fixed at sixty observations; campaign ``windows: [20]``
    # governs the other seven atoms only.
    numerator = rolling_return_sum_5.rolling(60, min_periods=60).var(ddof=1)
    denominator = 5.0 * returns.rolling(60, min_periods=60).var(ddof=1)
    var_ratio = numerator.div(denominator.replace(0.0, np.nan))

    return_autocov = returns.rolling(WINDOW, min_periods=WINDOW).cov(returns.shift(1))
    auto_valid = returns.notna() & returns.shift(1).notna()
    return_autocov = return_autocov.where(
        auto_valid.rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW)
    )

    valid_return_amount = returns.notna() & amount.notna() & amount.gt(0)
    down = returns.lt(0).where(valid_return_amount)
    up = returns.gt(0).where(valid_return_amount)
    down_activity = _conditional_mean(
        amount, down, valid_return_amount, WINDOW, minimum_count=3
    )
    up_activity = _conditional_mean(
        amount, up, valid_return_amount, WINDOW, minimum_count=3
    )
    down_up_activity = down_activity.div(up_activity.replace(0.0, np.nan))

    shock_activity_response = _strict_corr(
        log_amount.diff(), returns.abs().shift(1), WINDOW
    )
    range_activity_elasticity = _strict_corr(
        log_amount.diff(), span.diff(), WINDOW
    )

    prior_return = returns.shift(1)
    valid_range_response = span.notna() & prior_return.notna()
    down_range = _conditional_mean(
        span, prior_return.lt(0).where(valid_range_response),
        valid_range_response, WINDOW, minimum_count=5
    )
    up_range = _conditional_mean(
        span, prior_return.gt(0).where(valid_range_response),
        valid_range_response, WINDOW, minimum_count=5
    )
    vol_response_asymmetry = down_range.div(up_range.replace(0.0, np.nan))

    abs_sum = returns.abs().rolling(WINDOW, min_periods=WINDOW).sum()
    return_concentration = returns.pow(2).rolling(
        WINDOW, min_periods=WINDOW
    ).sum().div(abs_sum.pow(2).replace(0.0, np.nan))

    typical = (high + low + close) / 3.0
    overhead_turnover = _overhead_turnover(typical, close, amount, WINDOW)

    result = {
        "VAR_RATIO_5_60": var_ratio,
        "RETURN_AUTOCOV_20": return_autocov,
        "DOWN_UP_ACTIVITY_20": down_up_activity,
        "SHOCK_ACTIVITY_RESPONSE_20": shock_activity_response,
        "RANGE_ACTIVITY_ELASTICITY_20": range_activity_elasticity,
        "VOL_RESPONSE_ASYMMETRY_20": vol_response_asymmetry,
        "RETURN_CONCENTRATION_20": return_concentration,
        "OVERHEAD_TURNOVER_20": overhead_turnover,
    }
    return {name: frame.replace([np.inf, -np.inf], np.nan) for name, frame in result.items()}


def build_directional_outcome_scores(
    panels: Mapping[str, pd.DataFrame],
    config: Mapping[str, object],
) -> dict[str, pd.DataFrame]:
    """Apply the frozen direction signs to raw outcome-microscope atoms."""
    atoms = build_outcome_atoms(panels, config)
    directions = {name: int(spec["direction"]) for name, spec in config["mechanisms"].items()}
    return {name: atoms[name] * directions[name] for name in CANDIDATE_ATOMS}


# The group runner interface uses these names.  The runner-facing builder
# must apply the frozen direction signs; raw atoms remain available through
# ``build_outcome_atoms`` for unit tests and diagnostics.
def build_atoms(
    panels: Mapping[str, pd.DataFrame],
    config: Mapping[str, object],
) -> dict[str, pd.DataFrame]:
    return build_directional_outcome_scores(panels, config)


def leakage_checks(
    panels: Mapping[str, pd.DataFrame],
    config: Mapping[str, object],
    cut: pd.Timestamp,
) -> dict[str, bool]:
    """Check prefix and future-perturbation invariance for every atom."""
    full = build_atoms(panels, config)
    prefix = {name: frame.loc[:cut] for name, frame in panels.items()}
    changed = {name: frame.copy() for name, frame in panels.items()}
    for frame in changed.values():
        frame.loc[frame.index > cut] *= 1.71
    prefix_atoms = build_atoms(prefix, config)
    perturbed = build_atoms(changed, config)
    results: dict[str, bool] = {}
    for name in CANDIDATE_ATOMS:
        pd.testing.assert_frame_equal(
            full[name].loc[:cut], prefix_atoms[name], check_exact=False,
            rtol=1e-9, atol=1e-12
        )
        pd.testing.assert_frame_equal(
            full[name].loc[:cut], perturbed[name].loc[:cut], check_exact=False,
            rtol=1e-9, atol=1e-12
        )
        results[f"{name}:prefix"] = True
        results[f"{name}:future_perturbation"] = True
    return results
