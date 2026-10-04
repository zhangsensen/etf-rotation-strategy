"""Synthetic coal source chronology and frozen D-1 exposure checks."""
from __future__ import annotations

import numpy as np
import pandas as pd

from etf_strategy.core import etf_group_ext_coal as coal


def test_coal_shock_is_same_calendar_date_close_information() -> None:
    fut = pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-10"])
    settle = pd.Series([1200.0, 1320.0, 1452.0], index=fut)
    china = pd.DatetimeIndex(pd.to_datetime(["2025-01-03", "2025-01-06",
                                             "2025-01-09", "2025-01-10", "2025-01-13"]))
    shock = coal.align_coal_shock(settle, china)
    assert np.isclose(shock.loc["2025-01-03"], np.log(1.1))
    assert np.isnan(shock.loc["2025-01-06"])
    assert np.isnan(shock.loc["2025-01-09"])
    # The 2025-01-10 session carries the cumulative change over the gap.
    assert np.isclose(shock.loc["2025-01-10"], np.log(1452.0 / 1320.0))
    assert np.isnan(shock.loc["2025-01-13"])


def test_all_three_d_scores_use_d_minus_one_exposure() -> None:
    rng = np.random.default_rng(46)
    dates = pd.bdate_range("2025-01-01", periods=150)
    names = sorted(coal.CANDIDATES)
    returns = rng.normal(0, 0.01, (len(dates), len(names)))
    close = pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), index=dates, columns=names)
    shock = pd.Series(rng.normal(0, 0.02, len(dates)), index=dates)
    d = dates[110]
    base = coal.score_atoms(close, shock)
    changed_close = close.copy()
    changed_close.loc[d, names[0]] *= 1.8
    moved_close = coal.score_atoms(changed_close, shock)
    for name in base:
        pd.testing.assert_series_equal(base[name].loc[d], moved_close[name].loc[d])
    changed_shock = shock.copy()
    changed_shock.loc[d] *= 1.1
    moved_shock = coal.score_atoms(close, changed_shock)
    for name in base:
        np.testing.assert_allclose(moved_shock[name].loc[d].to_numpy(),
                                   base[name].loc[d].to_numpy() * 1.1, rtol=1e-10, atol=1e-10)
