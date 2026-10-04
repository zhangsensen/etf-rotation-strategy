from pathlib import Path

import numpy as np
import pandas as pd
import importlib.util
import pytest

from etf_strategy.core.etf_factor_grammar import (
    AtomSpec,
    active_forward_return,
    build_pit_eligibility,
    enumerate_expressions,
    expression_source_is_etf_only,
    materialize_expression,
)
from etf_strategy.core.etf_share_factor_space import (
    apply_share_availability_lag,
    build_share_factor_space,
)
from etf_strategy.core.etf_cross_asset_factor_space import (
    build_cross_asset_factor_space,
    parse_asset_classes,
)
from etf_strategy.core.etf_liquidity_factor_space import build_liquidity_factor_space
from etf_strategy.core.etf_benchmark_factor_space import build_benchmark_factor_space
from etf_strategy.core.etf_serial_dependence_factor_space import (
    build_serial_dependence_factor_space,
)


def test_etf_grammar_is_deterministic_unique_and_cross_family():
    atoms = [AtomSpec("B", "risk"), AtomSpec("A", "trend"), AtomSpec("C", "trend")]
    first = enumerate_expressions(atoms, ["atomic", "rank_mean", "rank_spread"])
    second = enumerate_expressions(reversed(atoms), ["rank_spread", "atomic", "rank_mean"])
    assert first == second
    assert len({item.expression_id for item in first}) == len(first)
    pair_rows = [item for item in first if item.right]
    assert all(item.family == "risk+trend" for item in pair_rows)


def test_rank_expression_has_no_outcome_input():
    dates = pd.bdate_range("2026-01-05", periods=2)
    left = pd.DataFrame([[0.2, 0.8], [0.4, 0.6]], index=dates, columns=["A", "B"])
    right = 1.0 - left
    expression = next(
        item
        for item in enumerate_expressions(
            [AtomSpec("left", "trend"), AtomSpec("right", "risk")], ["rank_mean"]
        )
        if item.operator == "rank_mean"
    )
    result = materialize_expression(expression, {"left": left, "right": right})
    assert result.eq(0.5).all().all()


def test_pit_population_enters_only_after_minimum_history():
    dates = pd.bdate_range("2026-01-05", periods=4)
    close = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0], "B": [np.nan, 2.0, 3.0, 4.0]}, index=dates)
    ohlcv = {field: close.copy() for field in ("open", "high", "low", "close", "volume")}
    eligible = build_pit_eligibility(ohlcv, min_history_sessions=2)
    assert eligible["A"].tolist() == [False, True, True, True]
    assert eligible["B"].tolist() == [False, False, True, True]


def test_active_label_uses_d_plus_two_and_same_day_eligible_pool():
    dates = pd.bdate_range("2026-01-05", periods=5)
    opens = pd.DataFrame(
        {"A": [10.0, 10.0, 10.0, 20.0, 20.0], "B": [10.0, 10.0, 10.0, 10.0, 10.0]},
        index=dates,
    )
    eligible = pd.DataFrame(True, index=dates, columns=opens.columns)
    result = active_forward_return(opens, eligible, horizon=1, entry_lag=2)
    assert result.iloc[0].tolist() == [0.5, -0.5]


def test_etf_miner_sources_do_not_import_stock_factor_or_referee_modules():
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "src/etf_strategy/core/etf_factor_grammar.py",
        root / "src/etf_strategy/core/etf_factor_referee.py",
        root / "src/etf_strategy/core/etf_share_factor_space.py",
        root / "src/etf_strategy/core/etf_cross_asset_factor_space.py",
        root / "src/etf_strategy/core/etf_liquidity_factor_space.py",
        root / "src/etf_strategy/core/etf_benchmark_factor_space.py",
        root / "src/etf_strategy/core/etf_serial_dependence_factor_space.py",
        root / "scripts/run_automated_factor_mining.py",
    ]
    forbidden = (
        "all_candidate_factors",
        "factor_library",
        "state_ruler_v1",
        "state_grammar_v1",
        "ashare",
    )
    text = "\n".join(path.read_text() for path in paths if path.exists())
    assert expression_source_is_etf_only()
    assert all(token not in text for token in forbidden)


def test_share_space_uses_only_past_values_and_moves_to_available_date():
    dates = pd.bdate_range("2025-01-02", periods=130)
    share = pd.DataFrame({"A": np.arange(130, dtype=float) + 100.0}, index=dates)
    before = build_share_factor_space(share)
    value_before = before["SHARE_CHG_20"].iloc[-2, 0]
    share.iloc[-1, 0] *= 10.0
    after = build_share_factor_space(share)
    assert after["SHARE_CHG_20"].iloc[-2, 0] == value_before
    lagged = apply_share_availability_lag(before, 1)
    assert np.isnan(lagged["SHARE_CHG_5"].iloc[0, 0])
    assert lagged["SHARE_CHG_5"].iloc[-1, 0] == before["SHARE_CHG_5"].iloc[-2, 0]


def test_cross_asset_space_separates_category_and_within_category_information():
    dates = pd.bdate_range("2025-01-02", periods=80)
    close = pd.DataFrame(
        {
            "EQ1": np.linspace(100, 180, 80),
            "EQ2": np.linspace(100, 140, 80),
            "BOND": np.linspace(100, 108, 80),
        },
        index=dates,
    )
    eligible = pd.DataFrame(True, index=dates, columns=close.columns)
    mapping = parse_asset_classes({"equity": ["EQ1", "EQ2"], "bond": ["BOND"]}, list(close.columns))
    factors = build_cross_asset_factor_space(close, eligible, mapping)
    assert factors["CATEGORY_MOM_20"].loc[dates[-1], "EQ1"] == factors[
        "CATEGORY_MOM_20"
    ].loc[dates[-1], "EQ2"]
    assert factors["WITHIN_CATEGORY_MOM_20"].loc[dates[-1], "EQ1"] > factors[
        "WITHIN_CATEGORY_MOM_20"
    ].loc[dates[-1], "EQ2"]
    old_value = factors["CATEGORY_MOM_20"].iloc[-2, 0]
    close.iloc[-1, 0] *= 10
    changed = build_cross_asset_factor_space(close, eligible, mapping)
    assert changed["CATEGORY_MOM_20"].iloc[-2, 0] == old_value


def test_population_median_excludes_dates_the_referee_did_not_score():
    runner_path = Path(__file__).resolve().parents[1] / "scripts/run_automated_factor_mining.py"
    spec = importlib.util.spec_from_file_location("etf_automated_miner", runner_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    dates = pd.bdate_range("2026-01-05", periods=4)
    daily_ic = pd.Series([np.nan, np.nan, 0.1, 0.2], index=dates)
    pairs = pd.Series([0, 5, 10, 12], index=dates)
    assert module._median_pairs_on_scored_days(daily_ic, pairs) == 11.0


def test_liquidity_space_uses_real_amount_and_has_no_future_dependency():
    dates = pd.bdate_range("2025-01-02", periods=80)
    close = pd.DataFrame({"A": np.linspace(10, 18, 80), "B": np.linspace(20, 16, 80)}, index=dates)
    panels = {
        "close": close.copy(),
        "high": close + 0.5,
        "low": close - 0.5,
        "volume": pd.DataFrame(1000.0, index=dates, columns=close.columns),
        "amount": pd.DataFrame(
            {"A": np.linspace(10_000, 30_000, 80), "B": np.linspace(30_000, 10_000, 80)},
            index=dates,
        ),
    }
    before = build_liquidity_factor_space(panels)
    prior = before["AMOUNT_Z_20"].iloc[-2].copy()
    panels["amount"].iloc[-1, 0] *= 100
    after = build_liquidity_factor_space(panels)
    pd.testing.assert_series_equal(after["AMOUNT_Z_20"].iloc[-2], prior)
    assert after["AMOUNT_Z_20"].iloc[-1, 0] != before["AMOUNT_Z_20"].iloc[-1, 0]


def test_liquidity_space_refuses_amount_proxy():
    frame = pd.DataFrame({"A": [1.0, 2.0]})
    with pytest.raises(ValueError, match="amount"):
        build_liquidity_factor_space(
            {"close": frame, "high": frame, "low": frame, "volume": frame}
        )


def test_benchmark_space_is_causal_and_requires_declared_benchmarks():
    dates = pd.bdate_range("2025-01-02", periods=150)
    close = pd.DataFrame(
        {
            "ETF": np.linspace(10, 19, 150),
            "510300.SH": np.linspace(4, 5, 150),
            "510500.SH": np.linspace(6, 8, 150),
        },
        index=dates,
    )
    before = build_benchmark_factor_space(close, ["510300.SH", "510500.SH"])
    prior = before["REL_MARKET_MOM_20"].iloc[-2].copy()
    close.iloc[-1, 1] *= 2
    after = build_benchmark_factor_space(close, ["510300.SH", "510500.SH"])
    pd.testing.assert_series_equal(after["REL_MARKET_MOM_20"].iloc[-2], prior)
    with pytest.raises(ValueError, match="missing"):
        build_benchmark_factor_space(close, ["MISSING"])


def test_serial_dependence_space_is_causal_and_close_only():
    dates = pd.bdate_range("2025-01-02", periods=180)
    close = pd.DataFrame(
        {
            "A": 100.0 * np.cumprod(1.0 + 0.002 * np.sin(np.arange(180))),
            "B": 80.0 * np.cumprod(1.0 + 0.003 * np.cos(np.arange(180))),
        },
        index=dates,
    )
    factors_before = build_serial_dependence_factor_space({"close": close})
    prior = {name: frame.iloc[-2].copy() for name, frame in factors_before.items()}
    close.iloc[-1, 0] *= 2.0
    factors_after = build_serial_dependence_factor_space({"close": close})
    for name, expected in prior.items():
        pd.testing.assert_series_equal(factors_after[name].iloc[-2], expected)
    assert set(factors_before) == {
        "RET_ACF1_5", "RET_ACF1_20", "RET_ACF1_60",
        "RET_ACF2_20", "RET_ACF2_60", "SIGN_ACF1_5", "SIGN_ACF1_20",
        "SIGN_ACF1_60", "VAR_RATIO_5_60", "VAR_RATIO_20_120",
    }
