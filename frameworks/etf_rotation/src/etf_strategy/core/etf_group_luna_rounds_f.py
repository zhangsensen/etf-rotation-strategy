"""Daily OHLC and amount-state atoms proposed for bounded Luna rounds 71+."""
from __future__ import annotations

import numpy as np
import pandas as pd


WINDOW = 20
POOL_SIZE = 14
DIRECTIONS = {
    "l71_range_lag1_autocorrelation": -1,
    "l71_amount_anomaly_lag1_autocorrelation": 1,
}


def _clean(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.astype(float).replace([np.inf, -np.inf], np.nan)


def _valid_ohlc(open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    return (
        open_.gt(0.0) & high.gt(0.0) & low.gt(0.0) & close.gt(0.0)
        & high.ge(open_) & high.ge(close)
        & low.le(open_) & low.le(close)
    )


def _range_lag1_autocorrelation(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """20 adjacent (R_t, R_{t-1}) pairs need 21 ranges and 22 closes."""
    required = ("open", "high", "low", "close")
    missing = set(required) - set(panels)
    if missing:
        raise KeyError(f"missing daily OHLC panels: {sorted(missing)}")
    open_, high, low, close = (_clean(panels[key]) for key in required)
    if any(not frame.index.equals(close.index) or not frame.columns.equals(close.columns)
           for frame in (open_, high, low)):
        raise ValueError("daily OHLC panels must have identical axes")
    if (not isinstance(close.index, pd.DatetimeIndex)
            or not close.index.is_monotonic_increasing
            or close.index.has_duplicates):
        raise ValueError("daily OHLC index must be a unique increasing DatetimeIndex")
    if close.shape[1] != POOL_SIZE or close.columns.has_duplicates:
        raise ValueError("range lag-1 autocorrelation requires the fixed 14-member pool")

    valid = _valid_ohlc(open_, high, low, close)
    prior_close = close.shift(1)
    daily_range = ((high - low) / prior_close.where(prior_close.gt(0.0))).where(valid & prior_close.gt(0.0))
    pair_valid = daily_range.notna() & daily_range.shift(1).notna()
    score = daily_range.rolling(WINDOW, min_periods=WINDOW).corr(daily_range.shift(1))
    return score.where(pair_valid.rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW))


def _amount_anomaly_lag1_autocorrelation(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """20 adjacent anomaly pairs use 21 anomalies and 41 amount observations."""
    if "amount" not in panels:
        raise KeyError("missing daily amount panel")
    amount = _clean(panels["amount"])
    if not isinstance(amount.index, pd.DatetimeIndex) or not amount.index.is_monotonic_increasing or amount.index.has_duplicates:
        raise ValueError("daily amount index must be a unique increasing DatetimeIndex")
    if amount.shape[1] != POOL_SIZE or amount.columns.has_duplicates:
        raise ValueError("amount anomaly autocorrelation requires the fixed 14-member pool")
    if any(not amount.index.equals(panels[key].index) or not amount.columns.equals(panels[key].columns)
           for key in ("open", "high", "low", "close")):
        raise ValueError("daily OHLC and amount panels must have identical axes")

    log_amount = np.log(amount.where(amount.gt(0.0)))
    prior_mean = log_amount.shift(1).rolling(WINDOW, min_periods=WINDOW).mean()
    prior_complete = log_amount.shift(1).notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW)
    anomaly = (log_amount - prior_mean).where(log_amount.notna() & prior_complete)
    pair_valid = anomaly.notna() & anomaly.shift(1).notna()
    score = anomaly.rolling(WINDOW, min_periods=WINDOW).corr(anomaly.shift(1))
    return score.where(pair_valid.rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW))


def build_atoms(panels: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    """Return the signed member score using only OHLC through the signal close."""
    if tuple(cfg.get("windows", (WINDOW,))) != (WINDOW,):
        raise ValueError("Luna round-F atoms are frozen to window 20")
    mechanisms = cfg.get("mechanisms", {})
    if not mechanisms or set(mechanisms) - set(DIRECTIONS):
        raise ValueError("mechanisms must be a nonempty subset of approved round-F candidates")
    mismatches = [name for name, entry in mechanisms.items() if entry.get("direction") != DIRECTIONS[name]]
    if mismatches:
        raise ValueError(f"frozen direction mismatch: {mismatches}")
    raw = {}
    if "l71_range_lag1_autocorrelation" in mechanisms:
        raw["l71_range_lag1_autocorrelation"] = _range_lag1_autocorrelation(panels)
    if "l71_amount_anomaly_lag1_autocorrelation" in mechanisms:
        raw["l71_amount_anomaly_lag1_autocorrelation"] = _amount_anomaly_lag1_autocorrelation(panels)
    return {
        f"{name}_20": raw[name].mul(DIRECTIONS[name]).replace([np.inf, -np.inf], np.nan)
        for name in mechanisms
    }
