"""Synthetic timing checks for proposed SOX-specific ETF score generation."""
from __future__ import annotations

import numpy as np
import pandas as pd

from etf_strategy.core import etf_group_us_sector as sector


def test_us_source_must_precede_china_date_and_be_fresh() -> None:
    us = pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-10"])
    sox = pd.Series([100.0, 110.0, 121.0], index=us)
    ndx = pd.Series([100.0, 105.0, 110.25], index=us)
    china = pd.DatetimeIndex(pd.to_datetime(["2025-01-03", "2025-01-06", "2025-01-09",
                                               "2025-01-10", "2025-01-13"]))
    score = sector.align_specific_shock(sox, ndx, china)
    assert np.isnan(score.loc["2025-01-03"])
    assert np.isclose(score.loc["2025-01-06"], 0.05)
    assert np.isnan(score.loc["2025-01-09"])
    assert np.isnan(score.loc["2025-01-10"])  # Same US calendar date is forbidden.
    assert np.isclose(score.loc["2025-01-13"], 0.05)


def test_all_three_d_scores_use_beta_fitted_through_d_minus_one() -> None:
    rng = np.random.default_rng(31)
    dates = pd.bdate_range("2025-01-01", periods=150)
    names = sorted(sector.CANDIDATES)
    returns = rng.normal(0, 0.01, (len(dates), len(names)))
    close = pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), index=dates, columns=names)
    shock = pd.Series(rng.normal(0, 0.02, len(dates)), index=dates)
    d = dates[110]
    base = sector.score_atoms(close, shock)

    changed_close = close.copy()
    changed_close.loc[d, names[0]] *= 1.8
    moved_close = sector.score_atoms(changed_close, shock)
    for name in base:
        pd.testing.assert_series_equal(base[name].loc[d], moved_close[name].loc[d])

    changed_shock = shock.copy()
    changed_shock.loc[d] *= 1.1  # Keep sign so the asymmetry branch is unchanged.
    moved_shock = sector.score_atoms(close, changed_shock)
    for name in base:
        np.testing.assert_allclose(moved_shock[name].loc[d].to_numpy(),
                                   base[name].loc[d].to_numpy() * 1.1, rtol=1e-10, atol=1e-10)
