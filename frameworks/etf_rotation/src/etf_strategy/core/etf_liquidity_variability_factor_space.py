"""ETF trading-activity variability factors."""
from __future__ import annotations

import numpy as np
import pandas as pd


def build_liquidity_variability_factor_space(
    amount: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build rolling volatility of daily log-turnover changes through D."""
    log_amount = np.log(amount.where(amount > 0.0))
    factor = log_amount.diff().rolling(20, min_periods=20).std()
    return {"LOG_AMOUNT_VOL_20": factor.replace([np.inf, -np.inf], np.nan)}
