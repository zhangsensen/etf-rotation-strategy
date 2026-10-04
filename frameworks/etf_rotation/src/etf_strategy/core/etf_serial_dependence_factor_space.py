"""ETF return-sequence memory atoms available at the D close.

This is an isolated discovery dimension for serial dependence.  It uses only
same-ETF close-to-close returns observed through D and does not read labels,
the entry price, or any cross-asset/volume field.  The atoms describe whether
recent returns tend to continue, reverse, or aggregate more (or less) than a
random walk would imply.
"""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def _rolling_autocorr(
    values: pd.DataFrame,
    lag: int,
    window: int,
) -> pd.DataFrame:
    """Lag autocorrelation using observations no later than the row date."""
    if lag < 1 or window <= lag:
        raise ValueError("lag must be positive and smaller than window")
    return values.rolling(window, min_periods=window).corr(values.shift(lag))


def _rolling_variance_ratio(
    returns: pd.DataFrame,
    aggregation: int,
    window: int,
) -> pd.DataFrame:
    """Variance ratio of aggregation-period returns versus one-day returns."""
    if aggregation < 2 or window <= aggregation:
        raise ValueError("aggregation must be >=2 and smaller than window")
    aggregated = returns.rolling(aggregation, min_periods=aggregation).sum()
    numerator = aggregated.rolling(window, min_periods=window).var(ddof=1)
    denominator = aggregation * returns.rolling(window, min_periods=window).var(ddof=1)
    return numerator.div(denominator.replace(0.0, np.nan))


def build_serial_dependence_factor_space(
    ohlcv: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Build preregistered return-memory atoms from close prices only.

    Every rolling operation is right aligned.  Thus the value at D can depend
    on returns through D and their lagged values, while a change at D+1 cannot
    alter the factor already materialized for D.
    """
    if "close" not in ohlcv:
        raise ValueError("ETF serial-dependence space requires close")
    close = ohlcv["close"].astype(float)
    returns = close.pct_change(fill_method=None)
    signs = np.sign(returns)
    factors: dict[str, pd.DataFrame] = {}

    for window in (5, 20, 60):
        factors[f"RET_ACF1_{window}"] = _rolling_autocorr(returns, lag=1, window=window)
        factors[f"SIGN_ACF1_{window}"] = _rolling_autocorr(signs, lag=1, window=window)

    for window in (20, 60):
        factors[f"RET_ACF2_{window}"] = _rolling_autocorr(returns, lag=2, window=window)

    factors["VAR_RATIO_5_60"] = _rolling_variance_ratio(returns, aggregation=5, window=60)
    factors["VAR_RATIO_20_120"] = _rolling_variance_ratio(returns, aggregation=20, window=120)

    return {
        name: frame.replace([np.inf, -np.inf], np.nan)
        for name, frame in factors.items()
    }
