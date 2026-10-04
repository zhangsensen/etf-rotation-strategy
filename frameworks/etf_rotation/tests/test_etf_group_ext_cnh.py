"""Synthetic USDCNH source chronology and frozen D-1 exposure checks."""
from __future__ import annotations

import numpy as np
import pandas as pd

from etf_strategy.core import etf_group_ext_cnh as cnh


def test_cnh_source_is_strictly_prior_and_at_most_five_calendar_days() -> None:
    fx = pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-10"])
    mid = pd.Series([7.0, 7.7, 8.47], index=fx)
    china = pd.DatetimeIndex(pd.to_datetime(["2025-01-03", "2025-01-06",
                                             "2025-01-09", "2025-01-10", "2025-01-13"]))
    shock = cnh.align_cnh_shock(mid, china)
    assert np.isnan(shock.loc["2025-01-03"])
    assert np.isclose(shock.loc["2025-01-06"], np.log(1.1))
    assert np.isnan(shock.loc["2025-01-09"])
    assert np.isnan(shock.loc["2025-01-10"])
    assert np.isclose(shock.loc["2025-01-13"], np.log(1.1))


def test_all_three_d_scores_use_d_minus_one_exposure() -> None:
    rng = np.random.default_rng(43)
    dates = pd.bdate_range("2025-01-01", periods=150)
    names = sorted(cnh.CANDIDATES)
    returns = rng.normal(0, 0.01, (len(dates), len(names)))
    close = pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), index=dates, columns=names)
    shock = pd.Series(rng.normal(0, 0.002, len(dates)), index=dates)
    d = dates[110]
    base = cnh.score_atoms(close, shock)
    changed_close = close.copy()
    changed_close.loc[d, names[0]] *= 1.8
    moved_close = cnh.score_atoms(changed_close, shock)
    for name in base:
        pd.testing.assert_series_equal(base[name].loc[d], moved_close[name].loc[d])
    changed_shock = shock.copy()
    changed_shock.loc[d] *= 1.1
    moved_shock = cnh.score_atoms(close, changed_shock)
    for name in base:
        np.testing.assert_allclose(moved_shock[name].loc[d].to_numpy(),
                                   base[name].loc[d].to_numpy() * 1.1, rtol=1e-10, atol=1e-10)
