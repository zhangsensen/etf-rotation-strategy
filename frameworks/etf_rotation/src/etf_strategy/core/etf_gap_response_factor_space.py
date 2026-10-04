"""ETF overnight-gap versus regular-session response atoms."""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def build_gap_response_factor_space(
    ohlcv: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Build the causal gap/session response atom available at D close."""
    required = {"open", "close"}
    missing = required - set(ohlcv)
    if missing:
        raise ValueError(f"ETF gap-response space missing fields: {sorted(missing)}")
    close = ohlcv["close"].astype(float)
    open_ = ohlcv["open"].reindex_like(close).astype(float)
    previous_close = close.shift(1)
    overnight_gap = open_.div(previous_close) - 1.0
    session_return = close.div(open_) - 1.0
    result = {
        "GAP_SESSION_CORR_20": overnight_gap.rolling(
            20, min_periods=20
        ).corr(session_return)
    }
    return {
        name: frame.replace([np.inf, -np.inf], np.nan)
        for name, frame in result.items()
    }
