"""Shared causal capital-gains-overhang calculations."""

from __future__ import annotations

import numpy as np

TURNOVER_CLIP = 0.99


def cgo_stats(
    price: np.ndarray,
    turnover: np.ndarray,
    window: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return reference price, gain overhang and loss overhang arrays."""
    length = len(price)
    reference = np.full(length, np.nan)
    gain_result = np.full(length, np.nan)
    loss_result = np.full(length, np.nan)
    if length <= window:
        return reference, gain_result, loss_result

    clipped = np.clip(turnover, 0.0, TURNOVER_CLIP)
    valid_count = length - window
    turnover_lags = np.empty((valid_count, window))
    price_lags = np.empty((valid_count, window))
    for offset in range(window):
        turnover_lags[:, offset] = clipped[window - 1 - offset : length - 1 - offset]
        price_lags[:, offset] = price[window - 1 - offset : length - 1 - offset]

    survival = np.cumprod(1.0 - turnover_lags, axis=1)
    weights = np.empty_like(turnover_lags)
    weights[:, 0] = turnover_lags[:, 0]
    weights[:, 1:] = turnover_lags[:, 1:] * survival[:, :-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        weights = weights / weights.sum(axis=1, keepdims=True)
    weights = np.where(np.isfinite(weights), weights, np.nan)

    reference[window:] = np.nansum(weights * price_lags, axis=1)
    current = price[window:]
    difference = current[:, None] - price_lags
    with np.errstate(invalid="ignore", divide="ignore"):
        gain_result[window:] = (
            np.nansum(weights * np.where(difference > 0, difference, 0.0), axis=1)
            / current
        )
        loss_result[window:] = (
            np.nansum(weights * np.where(difference < 0, -difference, 0.0), axis=1)
            / current
        )
    return reference, gain_result, loss_result
