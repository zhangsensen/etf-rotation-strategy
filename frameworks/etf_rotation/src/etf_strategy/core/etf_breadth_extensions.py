"""Additional ETF mechanisms using trailing daily observations only.

These are price/turnover proxies, never fund subscriptions, NAV or order flow.
All windows count exchange-session rows; missing observations are not filled.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def build_breadth_extensions(panels: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    close = panels["close"]
    ret = close.pct_change(fill_method=None)
    amount = panels["amount"].where(panels["amount"] > 0)
    log_amount = np.log(amount)
    span = (panels["high"] - panels["low"]) / close
    valid = ret.notna()
    result = {}
    for w in (20, 60):
        # Negative return autocovariance as a transaction-friction proxy.
        result[f"RETURN_REVERSAL_COV_{w}"] = -ret.rolling(w).cov(ret.shift(1))
        # Whether downside sessions require more turnover than upside sessions.
        down = (ret < 0).where(valid)
        up = (ret > 0).where(valid)
        down_amount = amount.where(ret < 0, 0).where(valid).rolling(w).sum()
        up_amount = amount.where(ret > 0, 0).where(valid).rolling(w).sum()
        down_n = down.rolling(w).sum()
        up_n = up.rolling(w).sum()
        result[f"DOWN_UP_ACTIVITY_{w}"] = (
            (down_amount / down_n.where(down_n >= 3)) /
            (up_amount / up_n.where(up_n >= 3))
        )
        # Return concentration measures reliance on a few large sessions.
        abs_sum = ret.abs().rolling(w).sum()
        result[f"RETURN_CONCENTRATION_{w}"] = (
            ret.pow(2).rolling(w).sum() / abs_sum.pow(2).replace(0, np.nan)
        )
        # Continuity of auction price discovery: overlap of adjacent daily ranges.
        overlap = (
            np.minimum(panels["high"], panels["high"].shift(1)) -
            np.maximum(panels["low"], panels["low"].shift(1))
        ).clip(lower=0)
        union = (
            np.maximum(panels["high"], panels["high"].shift(1)) -
            np.minimum(panels["low"], panels["low"].shift(1))
        ).replace(0, np.nan)
        result[f"RANGE_OVERLAP_{w}"] = (overlap / union).rolling(w).mean()
        # Lagged activity response measures whether trading follows price shocks.
        result[f"SHOCK_ACTIVITY_RESPONSE_{w}"] = (
            log_amount.diff().rolling(w).corr(ret.abs().shift(1))
        )
        # Sensitivity of liquidity to uncertainty, distinct from signed return/volume.
        result[f"RANGE_ACTIVITY_ELASTICITY_{w}"] = (
            log_amount.diff().rolling(w).corr(span.diff()).where(
                span.diff().rolling(w).std() > 1e-12
            )
        )
    return {k: v.replace([np.inf, -np.inf], np.nan) for k, v in result.items()}
