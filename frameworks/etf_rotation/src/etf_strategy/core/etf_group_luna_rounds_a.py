"""Price-path and daily range atoms for Luna multi-candidate rounds 36–40.

All outputs use only canonical daily OHLC through the current close.  The
ordinary atoms need 20 complete rows.  Tail-event response atoms need 41
complete returns (42 closes): 20 prior returns for each event threshold, 20
event dates ending at D-1, and responses no later than D.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


WINDOW = 20
DIRECTIONS = {
    "l36_max_close_drawdown_depth": -1,
    "l36_max_close_runup_depth": 1,
    "l36_drawdown_recovery_fraction": 1,
    "l36_drawdown_depth_concentration": 1,
    "l37_upper_tail_mean_excess": 1,
    "l37_lower_tail_mean_excess": -1,
    "l37_tail_magnitude_asymmetry": 1,
    "l37_central_return_bias": 1,
    "l38_open_excursion_balance_mean": 1,
    "l38_open_excursion_imbalance_magnitude": -1,
    "l38_open_excursion_balance_ar1": 1,
    "l38_open_excursion_sign_switch_rate": -1,
    "l39_upper_tail_nextday_followthrough": 1,
    "l39_lower_tail_nextday_rebound": 1,
    "l39_tail_event_nextday_absvol_ratio": -1,
    "l39_tail_event_response_consistency": 1,
    "l40_gap_range_absorption": 1,
    "l40_gap_range_extension": 1,
    "l40_gap_fill_fraction_capped": 1,
    "l40_gap_overshoot_frequency": -1,
}


def _frame(values: np.ndarray, index: pd.Index, columns: pd.Index) -> pd.DataFrame:
    return pd.DataFrame(values, index=index, columns=columns).replace(
        [np.inf, -np.inf], np.nan
    )


def _complete_window(values: np.ndarray, end: int, width: int) -> np.ndarray | None:
    start = end - width + 1
    if start < 0:
        return None
    window = values[start : end + 1]
    if window.shape[0] != width or not np.isfinite(window).all():
        return None
    return window


def _drawdown_stats(x: np.ndarray) -> tuple[float, float, float, float]:
    # First occurrence wins for equal running peaks and equal maximum drawdowns.
    peak = x[0]
    peak_i = 0
    depths = np.zeros(len(x), dtype=float)
    max_depth = 0.0
    selected_peak = 0
    selected_trough = 0
    for i, value in enumerate(x):
        if value > peak:
            peak, peak_i = value, i
        depth = max(0.0, (peak - value) / peak) if peak != 0 else np.nan
        depths[i] = depth
        if depth > max_depth:
            max_depth, selected_peak, selected_trough = depth, peak_i, i
    runup = 0.0
    trough = x[0]
    for value in x:
        if value < trough:
            trough = value
        if trough != 0:
            runup = max(runup, (value - trough) / trough)
    concentration = max_depth / depths.sum() if depths.sum() > 0 else np.nan
    if max_depth > 0:
        recovery = (x[-1] - x[selected_trough]) / (x[selected_peak] - x[selected_trough])
    else:
        recovery = 0.0
    return max_depth, runup, recovery, concentration


def _rolling_close_stats(close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    arr = close.to_numpy(dtype=float)
    result = {k: np.full(arr.shape, np.nan) for k in (
        "l36_max_close_drawdown_depth", "l36_max_close_runup_depth",
        "l36_drawdown_recovery_fraction", "l36_drawdown_depth_concentration",
    )}
    for j in range(arr.shape[1]):
        for i in range(WINDOW - 1, arr.shape[0]):
            w = _complete_window(arr[:, j], i, WINDOW)
            if w is None or (w <= 0).any():
                continue
            vals = _drawdown_stats(w)
            for name, value in zip(result, vals):
                result[name][i, j] = value
    return {k: _frame(v, close.index, close.columns) for k, v in result.items()}


def _rolling_return_distribution(close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    r = close.pct_change(fill_method=None).to_numpy(dtype=float)
    result = {k: np.full(r.shape, np.nan) for k in (
        "l37_upper_tail_mean_excess", "l37_lower_tail_mean_excess",
        "l37_tail_magnitude_asymmetry", "l37_central_return_bias",
    )}
    for j in range(r.shape[1]):
        for i in range(WINDOW, r.shape[0]):
            w = _complete_window(r[:, j], i, WINDOW)
            if w is None:
                continue
            q90, q10 = np.quantile(w, [0.9, 0.1], method="linear")
            upper, lower = w[w >= q90], w[w <= q10]
            mean_abs = np.mean(np.abs(w))
            if upper.size:
                result["l37_upper_tail_mean_excess"][i, j] = upper.mean() - q90
            if lower.size:
                result["l37_lower_tail_mean_excess"][i, j] = q10 - lower.mean()
            if upper.size and lower.size and mean_abs > 0:
                result["l37_tail_magnitude_asymmetry"][i, j] = (upper.mean() + lower.mean()) / mean_abs
            med_abs = np.median(np.abs(w))
            if med_abs > 0:
                result["l37_central_return_bias"][i, j] = (np.median(w) - w.mean()) / med_abs
    return {k: _frame(v, close.index, close.columns) for k, v in result.items()}


def _rolling_open_geometry(open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    valid = (
        open_.gt(0) & high.gt(0) & low.gt(0) & close.gt(0)
        & high.ge(pd.concat([open_, close], axis=0).groupby(level=0).max())
        & low.le(pd.concat([open_, close], axis=0).groupby(level=0).min())
    )
    # Treat only near-symmetric OHLC ties as zero using a relative price-scale
    # tolerance. This is invariant to a common adjustment factor and prevents
    # canonical reload noise from changing the sign of a mathematically zero
    # open-centered excursion.
    numerator = high + low - 2.0 * open_
    price_scale = pd.concat([open_.abs(), high.abs(), low.abs(), close.abs()]).groupby(level=0).max()
    numerator = numerator.mask(numerator.abs() <= 1e-12 * price_scale, 0.0).where(valid)
    b = numerator.div((high - low).where(high > low)).where(valid)
    arr = b.to_numpy(dtype=float)
    result = {k: np.full(arr.shape, np.nan) for k in (
        "l38_open_excursion_balance_mean", "l38_open_excursion_imbalance_magnitude",
        "l38_open_excursion_balance_ar1", "l38_open_excursion_sign_switch_rate",
    )}
    for j in range(arr.shape[1]):
        for i in range(WINDOW - 1, arr.shape[0]):
            w = _complete_window(arr[:, j], i, WINDOW)
            if w is None:
                continue
            result["l38_open_excursion_balance_mean"][i, j] = w.mean()
            result["l38_open_excursion_imbalance_magnitude"][i, j] = np.abs(w).mean()
            if np.std(w[:-1]) > 0 and np.std(w[1:]) > 0:
                result["l38_open_excursion_balance_ar1"][i, j] = np.corrcoef(w[:-1], w[1:])[0, 1]
            signs = np.sign(w)
            pairs = (signs[:-1] != 0) & (signs[1:] != 0)
            if pairs.any():
                result["l38_open_excursion_sign_switch_rate"][i, j] = np.mean(signs[:-1][pairs] != signs[1:][pairs])
    return {k: _frame(v, open_.index, open_.columns) for k, v in result.items()}


def _tail_event_response(close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    returns = close.pct_change(fill_method=None).to_numpy(dtype=float)
    result = {k: np.full(returns.shape, np.nan) for k in (
        "l39_upper_tail_nextday_followthrough", "l39_lower_tail_nextday_rebound",
        "l39_tail_event_nextday_absvol_ratio", "l39_tail_event_response_consistency",
    )}
    for j in range(returns.shape[1]):
        for i in range(40, returns.shape[0]):
            # Strict contiguous data from the 20 threshold observations before
            # the first event through the latest response at D.
            history = _complete_window(returns[:, j], i, 41)
            if history is None:
                continue
            up_responses: list[float] = []
            down_responses: list[float] = []
            event_responses: list[float] = []
            ordinary_responses: list[float] = []
            direction_matches: list[float] = []
            # Event dates D-20,...,D-1; every response is observed by D.
            for t in range(i - 20, i):
                prior = returns[t - 20 : t, j]
                event_return, response = returns[t, j], returns[t + 1, j]
                if prior.size != 20 or not np.isfinite(prior).all():
                    break
                q90, q10 = np.quantile(prior, [0.9, 0.1], method="linear")
                if event_return > q90:
                    up_responses.append(response)
                    event_responses.append(response)
                    direction_matches.append(float(np.sign(response) == np.sign(event_return)))
                elif event_return < q10:
                    down_responses.append(response)
                    event_responses.append(response)
                    direction_matches.append(float(np.sign(response) == np.sign(event_return)))
                else:
                    ordinary_responses.append(response)
            if len(up_responses) >= 2:
                result["l39_upper_tail_nextday_followthrough"][i, j] = np.mean(up_responses)
            if len(down_responses) >= 2:
                result["l39_lower_tail_nextday_rebound"][i, j] = np.mean(down_responses)
            if len(event_responses) >= 2 and len(ordinary_responses) >= 2 and np.mean(np.abs(ordinary_responses)) > 0:
                result["l39_tail_event_nextday_absvol_ratio"][i, j] = np.mean(np.abs(event_responses)) / np.mean(np.abs(ordinary_responses))
            if len(direction_matches) >= 2:
                result["l39_tail_event_response_consistency"][i, j] = np.mean(direction_matches)
    return {k: _frame(v, close.index, close.columns) for k, v in result.items()}


def _gap_geometry(open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    previous = close.shift(1)
    gap = open_ - previous
    candle_range = high - low
    body = close - open_
    signed_absorption = np.sign(gap) * body.div(candle_range.where(candle_range > 0))
    extension = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    up = gap > 0
    down = gap < 0
    extension = extension.mask(up, (high - open_).clip(lower=0).div(gap.abs().where(gap.ne(0))))
    extension = extension.mask(down, (open_ - low).clip(lower=0).div(gap.abs().where(gap.ne(0))))
    fill = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    fill = fill.mask(up, (open_ - low).clip(lower=0).div(gap.where(gap > 0)).clip(0, 1))
    fill = fill.mask(down, (high - open_).clip(lower=0).div(gap.abs().where(gap < 0)).clip(0, 1))
    overshoot = ((up & (low < previous)) | (down & (high > previous))).astype(float).where(gap.notna())
    valid_ohlc = (
        open_.gt(0) & high.gt(0) & low.gt(0) & close.gt(0) & previous.gt(0)
        & high.ge(pd.concat([open_, close], axis=0).groupby(level=0).max())
        & low.le(pd.concat([open_, close], axis=0).groupby(level=0).min())
    )
    complete = gap.notna() & candle_range.gt(0) & valid_ohlc
    signed_absorption = signed_absorption.where(valid_ohlc)
    extension = extension.where(valid_ohlc)
    fill = fill.where(valid_ohlc)
    overshoot = overshoot.where(valid_ohlc)
    return {
        "l40_gap_range_absorption": signed_absorption.where(complete).rolling(WINDOW, min_periods=WINDOW).mean().where(complete.rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW)),
        "l40_gap_range_extension": extension.rolling(WINDOW, min_periods=WINDOW).mean().where(extension.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW)),
        "l40_gap_fill_fraction_capped": fill.rolling(WINDOW, min_periods=WINDOW).mean().where(fill.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW)),
        "l40_gap_overshoot_frequency": overshoot.rolling(WINDOW, min_periods=WINDOW).mean().where(overshoot.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW)),
    }


def build_atoms(panels: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    """Return signed D-close member scores for the configured l36–l40 names."""
    mechanisms = cfg.get("mechanisms", {})
    unknown = set(mechanisms) - set(DIRECTIONS)
    if unknown:
        raise ValueError(f"unsupported Luna round-A mechanisms: {sorted(unknown)}")
    close = panels["close"]
    open_, high, low = panels["open"], panels["high"], panels["low"]
    raw: dict[str, pd.DataFrame] = {}
    selected = set(mechanisms)
    if any(name.startswith("l36_") for name in selected):
        raw.update(_rolling_close_stats(close))
    if any(name.startswith("l37_") for name in selected):
        raw.update(_rolling_return_distribution(close))
    if any(name.startswith("l38_") for name in selected):
        raw.update(_rolling_open_geometry(open_, high, low, close))
    if any(name.startswith("l39_") for name in selected):
        raw.update(_tail_event_response(close))
    if any(name.startswith("l40_") for name in selected):
        raw.update(_gap_geometry(open_, high, low, close))
    result = {}
    for name, settings in mechanisms.items():
        direction = settings.get("direction", DIRECTIONS[name]) if isinstance(settings, dict) else DIRECTIONS[name]
        if direction != DIRECTIONS[name]:
            raise ValueError(f"frozen direction mismatch for {name}")
        result[f"{name}_20"] = raw[name] * direction
    return result
