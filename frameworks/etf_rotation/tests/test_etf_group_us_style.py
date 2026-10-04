"""Synthetic chronology and D-1 beta checks for US value-growth style scores."""
from __future__ import annotations

import numpy as np
import pandas as pd

from etf_strategy.core import etf_group_us_style as style


def test_us_style_common_date_close_strictly_precedes_china_d() -> None:
    us = pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-10"])
    value = pd.Series([100.0, 110.0, 121.0], index=us)
    growth = pd.Series([100.0, 105.0, 110.25], index=us)
    china = pd.DatetimeIndex(pd.to_datetime(["2025-01-03", "2025-01-06", "2025-01-09",
                                               "2025-01-10", "2025-01-13"]))
    shock = style.align_style_shock(value, growth, china)
    assert np.isnan(shock.loc["2025-01-03"])
    assert np.isclose(shock.loc["2025-01-06"], 0.05)
    assert np.isnan(shock.loc["2025-01-09"])
    assert np.isnan(shock.loc["2025-01-10"])
    assert np.isclose(shock.loc["2025-01-13"], 0.05)


def test_r03_beta_excludes_d_close_for_all_three_candidates() -> None:
    rng = np.random.default_rng(41)
    dates = pd.bdate_range("2025-01-01", periods=150)
    names = sorted(style.CANDIDATES)
    returns = rng.normal(0, 0.01, (len(dates), len(names)))
    close = pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), index=dates, columns=names)
    shock = pd.Series(rng.normal(0, 0.02, len(dates)), index=dates)
    d = dates[110]
    base = style.score_atoms(close, shock)
    moved_close = close.copy()
    moved_close.loc[d, names[0]] *= 1.8
    changed = style.score_atoms(moved_close, shock)
    for name in base:
        pd.testing.assert_series_equal(base[name].loc[d], changed[name].loc[d])
    moved_shock = shock.copy()
    moved_shock.loc[d] *= 1.1
    changed = style.score_atoms(close, moved_shock)
    for name in base:
        np.testing.assert_allclose(changed[name].loc[d].to_numpy(),
                                   base[name].loc[d].to_numpy() * 1.1, rtol=1e-10, atol=1e-10)
