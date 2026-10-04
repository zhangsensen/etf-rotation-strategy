"""Synthetic point-in-time checks for the NASDAQ100 beta exposure atom."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


MODULE = (Path(__file__).resolve().parents[1] / "src/etf_strategy/core/etf_group_us_index.py")
spec = importlib.util.spec_from_file_location("etf_group_us_index", MODULE)
us_factor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(us_factor)

SYMBOLS = [
    "159995.SZ", "159516.SZ", "515880.SH", "159852.SZ", "562500.SH",
    "159732.SZ", "513130.SH", "159992.SZ", "513120.SH", "518880.SH",
    "512400.SH", "512890.SH", "159611.SZ", "513100.SH",
]
CONFIG = {
    "source_type": "us_index",
    "series": "NASDAQ100",
    "windows": [60],
    "mechanisms": {"us_lagged_transmission": {"direction": 1}},
}


def synthetic_panels(n=90):
    index = pd.bdate_range("2025-01-01", periods=n)
    us = pd.Series((np.arange(n) % 7 - 3) * 0.001, index=index, name="NASDAQ100")
    # Own return at s is 2 * the US return aligned to the prior A-share session.
    own_return = us.shift(1).fillna(0.0) * 2.0
    close = pd.DataFrame(index=index, columns=SYMBOLS, dtype=float)
    for i, symbol in enumerate(SYMBOLS):
        close[symbol] = 100.0 * (1.0 + own_return * (1.0 + i / 100.0)).cumprod()
    return {"close": close, "us_return": us.to_frame()}


def test_uses_prior_session_beta_and_current_latest_known_us_return():
    panels = synthetic_panels()
    scores = us_factor.build_atoms(panels, CONFIG)[us_factor.ATOM]
    date = panels["close"].index[61]
    # The 60 pairs s=1..60 have slope 2 (up to floating point close-return error).
    assert scores.loc[date, SYMBOLS[0]] == pytest.approx(2.0 * panels["us_return"].iloc[61, 0], rel=2e-4)

    changed = {key: value.copy() for key, value in panels.items()}
    changed["close"].loc[date, SYMBOLS[0]] *= 1.5
    score_after_same_day_close_change = us_factor.build_atoms(changed, CONFIG)[us_factor.ATOM]
    assert score_after_same_day_close_change.loc[date, SYMBOLS[0]] == pytest.approx(
        scores.loc[date, SYMBOLS[0]], rel=1e-10, abs=1e-12
    )


def test_missing_current_us_return_stays_missing_and_beta_uses_60_valid_pairs():
    panels = synthetic_panels()
    missing_date = panels["close"].index[70]
    panels["us_return"].loc[missing_date, "NASDAQ100"] = np.nan
    score = us_factor.build_atoms(panels, CONFIG)[us_factor.ATOM]
    assert score.loc[missing_date].isna().all()
    # The current return is available next day; a later beta window fails closed
    # because the missing pair remains inside its fixed 60-session window.
    next_date = panels["close"].index[71]
    assert score.loc[next_date].notna().all()
    assert score.loc[panels["close"].index[72]].isna().all()


def test_prefix_and_future_perturbation_invariance():
    panels = synthetic_panels()
    cut = panels["close"].index[72]
    checks = us_factor.leakage_checks(panels, CONFIG, cut)
    assert checks == {f"{us_factor.ATOM}:prefix_and_future_perturbation": True}


def test_rejects_changed_direction_or_non_fixed_input():
    panels = synthetic_panels()
    invalid = {**CONFIG, "mechanisms": {us_factor.MECHANISM: {"direction": -1}}}
    with pytest.raises(ValueError, match=r"fixed \+1"):
        us_factor.build_atoms(panels, invalid)
    with pytest.raises(ValueError, match="fixed 14"):
        us_factor.build_atoms(
        {**panels, "close": panels["close"].iloc[:, :-1]}, CONFIG
        )
