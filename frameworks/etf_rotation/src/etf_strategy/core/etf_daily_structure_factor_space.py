"""ETF daily candle, path-efficiency and tail-shape atoms known by D close."""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def _safe_div(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    return left.div(right.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)


def build_daily_structure_factor_space(
    ohlcv: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Build complementary OHLC path features without using outcomes or future rows."""
    required = {"open", "high", "low", "close"}
    missing = required - set(ohlcv)
    if missing:
        raise ValueError(f"ETF daily structure space missing fields: {sorted(missing)}")

    close = ohlcv["close"].astype(float)
    open_ = ohlcv["open"].reindex_like(close).astype(float)
    high = ohlcv["high"].reindex_like(close).astype(float)
    low = ohlcv["low"].reindex_like(close).astype(float)
    previous_close = close.shift(1)
    daily_return = close.pct_change(fill_method=None)
    intraday_range = high - low
    upper_wick = high - pd.DataFrame(
        np.maximum(open_.to_numpy(), close.to_numpy()),
        index=close.index,
        columns=close.columns,
    )
    lower_wick = pd.DataFrame(
        np.minimum(open_.to_numpy(), close.to_numpy()),
        index=close.index,
        columns=close.columns,
    ) - low

    factors: dict[str, pd.DataFrame] = {
        "OVERNIGHT_GAP": _safe_div(open_, previous_close) - 1.0,
        "SESSION_RETURN": _safe_div(close, open_) - 1.0,
        "DAILY_RANGE_PCT": _safe_div(high - low, previous_close),
        "CLOSE_LOCATION_DAILY": _safe_div(close - low, intraday_range),
        "BODY_TO_RANGE": _safe_div((close - open_).abs(), intraday_range),
        "WICK_IMBALANCE": _safe_div(upper_wick - lower_wick, intraday_range),
    }

    log_return = np.log(close.where(close > 0)).diff()
    for window in (10, 20, 60):
        net_move = np.log(close.where(close > 0) / close.shift(window).where(lambda x: x > 0))
        travelled = log_return.abs().rolling(window, min_periods=window).sum()
        factors[f"PATH_EFFICIENCY_{window}"] = _safe_div(net_move.abs(), travelled).clip(0.0, 1.0)
    for window in (20, 60):
        rolling = daily_return.rolling(window, min_periods=window)
        downside = daily_return.clip(upper=0.0).abs().rolling(
            window, min_periods=window
        ).mean()
        upside = daily_return.clip(lower=0.0).rolling(
            window, min_periods=window
        ).mean()
        # Some pandas versions center rolling skew using the entire input.
        # Compute each window independently so future outliers cannot change
        # historical values through floating-point cancellation.
        factors[f"RETURN_SKEW_{window}"] = rolling.apply(
            lambda values: pd.Series(values).skew(), raw=True
        )
        factors[f"WORST_DAY_{window}"] = rolling.min()
        # Robust lower-tail severity: unlike WORST_DAY, this is not determined
        # by a single observation, while remaining available at D close.
        factors[f"TAIL_Q10_{window}"] = rolling.quantile(0.10)
        factors[f"DOWNSIDE_UPSIDE_RATIO_{window}"] = _safe_div(downside, upside)
        factors[f"GAP_MEAN_{window}"] = factors["OVERNIGHT_GAP"].rolling(
            window, min_periods=window
        ).mean()
        factors[f"SESSION_MEAN_{window}"] = factors["SESSION_RETURN"].rolling(
            window, min_periods=window
        ).mean()

    return {
        name: frame.where(np.isfinite(frame))
        for name, frame in factors.items()
    }
