"""ETF daily-range memory atoms available at D close."""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def build_range_memory_factor_space(
    ohlcv: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Build volatility-clustering features without future rows or labels."""
    required = {"high", "low", "close"}
    missing = required - set(ohlcv)
    if missing:
        raise ValueError(f"ETF range-memory space missing fields: {sorted(missing)}")
    close = ohlcv["close"].astype(float)
    high = ohlcv["high"].reindex_like(close).astype(float)
    low = ohlcv["low"].reindex_like(close).astype(float)
    previous_close = close.shift(1)
    range_pct = (high - low).div(previous_close)
    result = {
        "RANGE_ACF1_20": range_pct.rolling(20, min_periods=20).corr(
            range_pct.shift(1)
        )
    }
    return {
        name: frame.replace([np.inf, -np.inf], np.nan)
        for name, frame in result.items()
    }
