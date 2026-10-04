"""ETF overnight-versus-session volatility allocation factors."""
from __future__ import annotations

import numpy as np
import pandas as pd


def build_gap_volatility_factor_space(
    open_price: pd.DataFrame,
    close: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build D-close-known gap/session volatility ratios."""
    gap = open_price / close.shift(1) - 1.0
    session = close / open_price - 1.0
    denominator = session.rolling(20, min_periods=20).std().replace(0.0, np.nan)
    ratio = gap.rolling(20, min_periods=20).std() / denominator
    return {"GAP_VOL_RATIO_20": ratio.replace([np.inf, -np.inf], np.nan)}
