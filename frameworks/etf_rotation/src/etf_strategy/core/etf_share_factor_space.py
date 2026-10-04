"""ETF primary-market share-flow atoms with explicit availability lag outside this module."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_change(share: pd.DataFrame, sessions: int) -> pd.DataFrame:
    lagged = share.shift(sessions)
    return (share / lagged - 1.0).where(lagged > 0).replace([np.inf, -np.inf], np.nan)


def build_share_factor_space(share_panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build dimensionless ETF creation/redemption candidate atoms."""
    if share_panel.empty:
        raise ValueError("share_panel must be non-empty")
    share = share_panel.astype(float).where(share_panel.astype(float) > 0)
    changes = {window: _safe_change(share, window) for window in (1, 5, 10, 20, 60)}
    daily_sign = np.sign(changes[1])
    results = {
        **{f"SHARE_CHG_{window}": frame for window, frame in changes.items()},
        "SHARE_ACCEL_5_20": changes[5] - changes[20],
        "SHARE_ACCEL_10_60": changes[10] - changes[60],
        "SHARE_PERSISTENCE_20": daily_sign.rolling(20, min_periods=20).mean(),
        "SHARE_PERSISTENCE_60": daily_sign.rolling(60, min_periods=60).mean(),
        "SHARE_FLOW_VOL_20": changes[1].rolling(20, min_periods=20).std(ddof=1),
        "SHARE_FLOW_VOL_60": changes[1].rolling(60, min_periods=60).std(ddof=1),
    }
    for history in (60, 120):
        baseline_mean = changes[5].shift(1).rolling(history, min_periods=history).mean()
        baseline_std = changes[5].shift(1).rolling(history, min_periods=history).std(ddof=1)
        results[f"SHARE_SURPRISE_5_{history}"] = (
            (changes[5] - baseline_mean) / baseline_std.replace(0.0, np.nan)
        )
    return {name: frame.replace([np.inf, -np.inf], np.nan) for name, frame in results.items()}


def apply_share_availability_lag(
    factors: dict[str, pd.DataFrame],
    sessions: int,
) -> dict[str, pd.DataFrame]:
    if not isinstance(sessions, int) or isinstance(sessions, bool) or sessions < 1:
        raise ValueError("fund_share factors require a positive conservative availability lag")
    return {name: frame.shift(sessions) for name, frame in factors.items()}
