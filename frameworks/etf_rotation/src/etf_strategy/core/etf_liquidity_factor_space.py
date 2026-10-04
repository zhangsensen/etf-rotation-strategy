"""ETF amount, liquidity and price-volume atoms using information available by D close."""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def _safe_div(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    return left.div(right.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)


def build_liquidity_factor_space(
    ohlcv: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Build preregistered ETF liquidity atoms without share-flow impersonation."""
    required = {"high", "low", "close", "volume", "amount"}
    missing = required - set(ohlcv)
    if missing:
        raise ValueError(f"ETF liquidity space missing fields: {sorted(missing)}")
    close = ohlcv["close"].astype(float)
    high = ohlcv["high"].reindex_like(close).astype(float)
    low = ohlcv["low"].reindex_like(close).astype(float)
    volume = ohlcv["volume"].reindex_like(close).astype(float).where(lambda x: x > 0)
    amount = ohlcv["amount"].reindex_like(close).astype(float).where(lambda x: x > 0)
    ret = close.pct_change(fill_method=None)
    log_amount = np.log(amount)
    log_volume = np.log(volume)
    factors: dict[str, pd.DataFrame] = {}

    for short, long in ((5, 20), (20, 60)):
        factors[f"AMOUNT_RATIO_{short}_{long}"] = _safe_div(
            amount.rolling(short, min_periods=short).mean(),
            amount.rolling(long, min_periods=long).mean(),
        ) - 1.0
        factors[f"VOLUME_RATIO_{short}_{long}"] = _safe_div(
            volume.rolling(short, min_periods=short).mean(),
            volume.rolling(long, min_periods=long).mean(),
        ) - 1.0
    for window in (20, 60):
        amount_mean = log_amount.rolling(window, min_periods=window).mean()
        amount_std = log_amount.rolling(window, min_periods=window).std(ddof=1)
        volume_mean = log_volume.rolling(window, min_periods=window).mean()
        volume_std = log_volume.rolling(window, min_periods=window).std(ddof=1)
        factors[f"AMOUNT_Z_{window}"] = _safe_div(log_amount - amount_mean, amount_std)
        factors[f"VOLUME_Z_{window}"] = _safe_div(log_volume - volume_mean, volume_std)
        factors[f"AMIHUD_{window}"] = _safe_div(
            ret.abs().rolling(window, min_periods=window).mean(),
            amount.rolling(window, min_periods=window).mean(),
        )
        factors[f"PRICE_AMOUNT_CORR_{window}"] = ret.rolling(
            window, min_periods=window
        ).corr(log_amount.diff())

    price_location = _safe_div(2.0 * close - high - low, high - low).clip(-1.0, 1.0)
    signed_amount = price_location * amount
    for window in (5, 20, 60):
        factors[f"MONEY_PRESSURE_{window}"] = _safe_div(
            signed_amount.rolling(window, min_periods=window).sum(),
            amount.rolling(window, min_periods=window).sum(),
        )

    return {
        name: frame.where(np.isfinite(frame))
        for name, frame in factors.items()
    }
