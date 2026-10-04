import numpy as np
import pandas as pd

from etf_strategy.core.etf_group_daily_rounds import build_atoms, leakage_checks


def _panels(close):
    close = pd.DataFrame({"a": close}, index=pd.date_range("2025-01-01", periods=len(close)))
    open_ = close * 0.999
    high = pd.concat([open_, close], axis=1).max(axis=1).to_frame("a") * 1.01
    low = pd.concat([open_, close], axis=1).min(axis=1).to_frame("a") * 0.99
    return {"open": open_, "high": high, "low": low, "close": close}


def _cfg():
    return {"windows": [20], "mechanisms": {"underwater_time_share": {"direction": -1}}}


def test_underwater_time_share_uses_current_close_and_prior_20_session_peak():
    close = np.full(42, 100.0)
    close[40:] = [99.0, 98.0]
    panels = _panels(close)
    output = build_atoms(panels, _cfg())["underwater_time_share_20"]["a"]

    # First complete output has 20 comparisons (t=20..39), all at the peak.
    assert pd.isna(output.iloc[38])  # fewer than 40 closes through this date
    assert output.iloc[39] == 0.0
    # D's close is included: one underwater close among the last 20 comparisons.
    assert output.iloc[40] == -1.0 / 20.0
    assert output.iloc[41] == -2.0 / 20.0


def test_underwater_time_share_propagates_incomplete_window_and_is_prefix_safe():
    close = np.linspace(80.0, 120.0, 90)
    panels = _panels(close)
    panels["close"].iloc[35, 0] = np.nan
    output = build_atoms(panels, _cfg())["underwater_time_share_20"]["a"]
    assert pd.isna(output.iloc[40])
    assert pd.notna(output.iloc[75])
    assert all(leakage_checks(panels, _cfg(), panels["close"].index[60]).values())
