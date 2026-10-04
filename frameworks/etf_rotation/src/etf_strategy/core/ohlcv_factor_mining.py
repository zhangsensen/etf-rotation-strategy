"""Fixed, point-in-time OHLCV factor space for ETF discovery."""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def forward_open_return(
    open_prices: pd.DataFrame,
    horizon: int,
    entry_lag: int = 2,
) -> pd.DataFrame:
    """Open-to-open label indexed by the close-signal date."""
    if horizon <= 0 or entry_lag <= 0:
        raise ValueError("horizon and entry_lag must be positive")
    entry = open_prices.shift(-entry_lag)
    exit_price = open_prices.shift(-(entry_lag + horizon))
    return (exit_price / entry - 1.0).where((entry > 0) & (exit_price > 0))


def _safe_div(numerator: pd.DataFrame, denominator: pd.DataFrame) -> pd.DataFrame:
    return numerator.div(denominator.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)


def _rolling_max_drawdown(close: pd.DataFrame, window: int) -> pd.DataFrame:
    def max_drawdown(values: np.ndarray) -> float:
        if not np.isfinite(values).all() or np.any(values <= 0):
            return np.nan
        running_max = np.maximum.accumulate(values)
        return float(np.min(values / running_max - 1.0))

    return close.rolling(window, min_periods=window).apply(max_drawdown, raw=True)


def build_ohlcv_factor_space(ohlcv: Mapping[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Build the preregistered A/B/C candidate families without future data."""
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(ohlcv)
    if missing:
        raise ValueError(f"OHLCV missing required fields: {sorted(missing)}")

    close = ohlcv["close"].astype(float)
    high = ohlcv["high"].reindex_like(close).astype(float)
    low = ohlcv["low"].reindex_like(close).astype(float)
    log_close = np.log(close.where(close > 0))
    daily_return = close.pct_change(fill_method=None)
    factors: dict[str, pd.DataFrame] = {}

    for window in (5, 10, 20, 60, 120):
        factors[f"RET_{window}"] = close / close.shift(window) - 1.0
    factors["SKIP_RECENT_MOM_20_5"] = close.shift(5) / close.shift(20) - 1.0
    factors["SKIP_RECENT_MOM_60_5"] = close.shift(5) / close.shift(60) - 1.0
    for window in (20, 60):
        momentum = factors[f"RET_{window}"]
        factors[f"REL_MOM_EW_{window}"] = momentum.sub(momentum.mean(axis=1), axis=0)
        realized_vol = daily_return.rolling(window, min_periods=window).std(ddof=1)
        factors[f"TREND_RET_VOLADJ_{window}"] = _safe_div(
            log_close - log_close.shift(window),
            realized_vol * np.sqrt(window),
        )
        factors[f"UP_DAY_RATIO_{window}"] = (
            daily_return.gt(0).where(daily_return.notna()).rolling(window, min_periods=window).mean()
        )

    vol20 = daily_return.rolling(20, min_periods=20).std(ddof=1)
    for short, long in ((5, 20), (20, 60), (20, 120)):
        gap = close.rolling(short, min_periods=short).mean() / close.rolling(
            long, min_periods=long
        ).mean() - 1.0
        factors[f"MA_GAP_{short}_{long}_VOLADJ"] = _safe_div(gap, vol20 * np.sqrt(long))

    prev_close = close.shift(1)
    true_range = pd.DataFrame(
        np.maximum.reduce(
            [
                (high - low).to_numpy(),
                (high - prev_close).abs().to_numpy(),
                (low - prev_close).abs().to_numpy(),
            ]
        ),
        index=close.index,
        columns=close.columns,
    )
    atr20_pct = _safe_div(true_range.rolling(20, min_periods=20).mean(), close)
    for window in (20, 60, 120):
        rolling_low = low.rolling(window, min_periods=window).min()
        rolling_high = high.rolling(window, min_periods=window).max()
        prior_high = rolling_high.shift(1)
        factors[f"PRICE_POSITION_{window}"] = _safe_div(
            close - rolling_low, rolling_high - rolling_low
        )
        factors[f"DIST_HIGH_{window}_VOLADJ"] = _safe_div(
            close / prior_high - 1.0,
            vol20 * np.sqrt(window),
        )
        if window in (20, 60):
            factors[f"BREAKOUT_ATR_{window}"] = _safe_div(close / prior_high - 1.0, atr20_pct)

    downside = daily_return.clip(upper=0.0)
    for window in (10, 20, 60):
        factors[f"REALIZED_VOL_{window}"] = daily_return.rolling(
            window, min_periods=window
        ).std(ddof=1)
    for window in (20, 60):
        factors[f"DOWNSIDE_DEV_{window}"] = np.sqrt(
            downside.pow(2).rolling(window, min_periods=window).mean()
        )
        drawdown = close / close.rolling(window, min_periods=window).max() - 1.0
        factors[f"ULCER_{window}"] = np.sqrt(
            drawdown.pow(2).rolling(window, min_periods=window).mean()
        )
        factors[f"TAIL_Q10_{window}"] = daily_return.rolling(
            window, min_periods=window
        ).quantile(0.10)
    for window in (20, 60, 120):
        factors[f"CURRENT_DD_{window}"] = (
            close / close.rolling(window, min_periods=window).max() - 1.0
        )
        factors[f"MAX_DD_{window}"] = _rolling_max_drawdown(close, window)
    factors["VOL_ACCEL_5_20"] = _safe_div(
        daily_return.rolling(5, min_periods=5).std(ddof=1), vol20
    )

    return {name: frame.replace([np.inf, -np.inf], np.nan) for name, frame in factors.items()}


def factor_family(name: str) -> str:
    if name.startswith(("RET_", "SKIP_", "REL_MOM_", "TREND_", "UP_DAY_", "MA_GAP_")):
        return "trend"
    if name.startswith(("PRICE_POSITION_", "DIST_HIGH_", "BREAKOUT_")):
        return "breakout"
    return "risk"
