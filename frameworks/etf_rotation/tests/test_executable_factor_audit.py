import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.executable_factor_audit import (
    apply_availability_lag,
    daily_cross_sectional_ic,
    forward_open_return,
    rolling_direction_stability,
)


def test_availability_lag_moves_value_to_later_signal_session():
    dates = pd.bdate_range("2026-01-05", periods=3)
    signal = pd.DataFrame({"A": [1.0, 2.0, 3.0]}, index=dates)
    result = apply_availability_lag(signal, 1)
    assert np.isnan(result.iloc[0, 0])
    assert result.iloc[1:, 0].tolist() == [1.0, 2.0]


@pytest.mark.parametrize("sessions", [-1, 1.5, True])
def test_availability_lag_rejects_invalid_sessions(sessions):
    signal = pd.DataFrame({"A": [1.0]})
    with pytest.raises(ValueError):
        apply_availability_lag(signal, sessions)


def test_forward_label_starts_at_next_open_and_ends_after_horizon():
    dates = pd.bdate_range("2026-01-05", periods=5)
    opens = pd.DataFrame({"A": [10., 20., 30., 60., 120.]}, index=dates)
    result = forward_open_return(opens, 2)
    assert result.loc[dates[0], "A"] == pytest.approx(60. / 20. - 1.)
    assert result.loc[dates[1], "A"] == pytest.approx(120. / 30. - 1.)
    assert result.iloc[-2:].isna().all().all()


def test_cross_sectional_ic_uses_same_signal_date_without_fill():
    dates = pd.bdate_range("2026-01-05", periods=2)
    columns = list("ABCDE")
    signal = pd.DataFrame([[1, 2, 3, 4, 5], [1, np.nan, 3, 4, 5]], index=dates, columns=columns)
    returns = pd.DataFrame([[10, 20, 30, 40, 50], [50, 40, 30, 20, 10]], index=dates, columns=columns)
    daily = daily_cross_sectional_ic(signal, returns, min_pairs=5)
    assert daily.loc[dates[0], "ic"] == pytest.approx(1.)
    assert np.isnan(daily.loc[dates[1], "ic"])
    assert daily.loc[dates[1], "pair_count"] == 4


def test_rolling_direction_stability_uses_fixed_windows():
    dates = pd.bdate_range("2025-01-01", periods=360)
    daily = pd.DataFrame({"ic": np.r_[np.full(180, .1), np.full(180, -.1)],
                          "pair_count": 20}, index=dates)
    stability, windows = rolling_direction_stability(daily, 1, window=180, step=180)
    assert windows == 2
    assert stability == pytest.approx(.5)
