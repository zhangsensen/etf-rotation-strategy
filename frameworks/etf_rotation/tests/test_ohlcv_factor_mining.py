import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.ohlcv_factor_mining import (
    build_ohlcv_factor_space,
    factor_family,
    forward_open_return,
)


def _ohlcv(periods=150, symbols=6):
    dates = pd.bdate_range("2025-01-02", periods=periods)
    columns = [f"E{i}" for i in range(symbols)]
    base = np.arange(periods, dtype=float)[:, None] + np.arange(symbols)[None, :] + 100.0
    close = pd.DataFrame(base, index=dates, columns=columns)
    return {
        "open": close * 0.999,
        "high": close * 1.01,
        "low": close * 0.99,
        "close": close,
        "volume": close * 1000,
    }


def test_forward_return_uses_configured_d_plus_two_entry():
    dates = pd.bdate_range("2026-01-05", periods=6)
    opens = pd.DataFrame({"A": [10.0, 20.0, 30.0, 60.0, 120.0, 240.0]}, index=dates)
    result = forward_open_return(opens, horizon=2, entry_lag=2)
    assert result.iloc[0, 0] == pytest.approx(120.0 / 30.0 - 1.0)
    assert result.iloc[-4:, 0].isna().all()


def test_factor_space_is_fixed_and_point_in_time():
    data = _ohlcv()
    factors = build_ohlcv_factor_space(data)
    assert len(factors) == 40
    assert {factor_family(name) for name in factors} == {"trend", "breakout", "risk"}
    before = factors["RET_20"].iloc[-2, 0]
    data["close"].iloc[-1, 0] *= 100.0
    after = build_ohlcv_factor_space(data)["RET_20"].iloc[-2, 0]
    assert before == after
