from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_market_state_space import build_market_state_space, past_zscore
from etf_strategy.core.etf_regime_label import BasketSpec, DEFENSIVE_SYMBOLS, build_regime_labels
from etf_strategy.core.etf_regime_referee import (
    directional_signature,
    hierarchical_family_holm,
    negative_effect_pvalue,
)


def _opens(n: int = 40) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    values = {symbol: np.arange(n, dtype=float) + 100.0 for symbol in ("A", "B", *DEFENSIVE_SYMBOLS)}
    return pd.DataFrame(values, index=dates)


def test_label_starts_at_d_plus_two_open_and_proves_clock() -> None:
    dates = pd.date_range("2020-01-01", periods=40, freq="B")
    opens = _opens()
    basket = BasketSpec(("A", "B"), min_attack_members=2, min_defensive_members=4)
    labels = build_regime_labels(opens, basket, horizons=(5,), entry_lag=2)[5]
    valid = labels.dropna(subset=["basket_spread"])
    assert (valid.entry_date > valid.signal_date).all()
    assert (valid.exit_date > valid.entry_date).all()
    assert valid.iloc[0].entry_date == dates[2]
    assert valid.iloc[0].exit_date == dates[7]


def test_basket_members_are_fixed_and_missing_minimum_is_fail_closed() -> None:
    opens = _opens()
    basket = BasketSpec(("A", "B"), min_attack_members=2, min_defensive_members=4)
    # A missing fixed member is a configuration error, never a silent fill.
    pytest.raises(ValueError, build_regime_labels, opens.drop(columns=["B"]), basket, horizons=(5,), entry_lag=2)
    assert set(basket.defensive_symbols) == set(DEFENSIVE_SYMBOLS)


def test_future_listing_cannot_enter_signal_date_basket() -> None:
    opens = _opens()
    opens.loc[opens.index[:5], "B"] = np.nan
    basket = BasketSpec(("A", "B"), min_attack_members=2, min_defensive_members=4)
    labels = build_regime_labels(opens, basket, horizons=(5,), entry_lag=2)[5]
    assert labels.loc[:4, "basket_spread"].isna().all()


def test_state_atoms_do_not_change_when_future_rows_are_appended() -> None:
    dates = pd.date_range("2020-01-01", periods=90, freq="B")
    close = pd.DataFrame({s: np.linspace(100, 140, len(dates)) for s in ("A", "B", "510300.SH", "510500.SH", *DEFENSIVE_SYMBOLS)}, index=dates)
    first = build_market_state_space(close.iloc[:60], candidate_symbols=("A", "B"))
    all_rows = build_market_state_space(close, candidate_symbols=("A", "B"))
    for name in first:
        pd.testing.assert_series_equal(first[name], all_rows[name].iloc[:60], check_names=True)


def test_past_zscore_tolerates_isolated_gap_without_looking_forward() -> None:
    index = pd.bdate_range("2020-01-01", periods=320)
    source = pd.Series(np.linspace(-1.0, 2.0, len(index)), index=index, name="state")
    source.iloc[180] = np.nan

    normalized = past_zscore(source, window=252, min_observations=240)
    assert normalized.iloc[260:].notna().all()

    cutoff = index[270]
    changed = source.copy()
    changed.loc[changed.index > cutoff] *= -100.0
    rerun = past_zscore(changed, window=252, min_observations=240)
    pd.testing.assert_series_equal(normalized.loc[:cutoff], rerun.loc[:cutoff])


def test_attack_atoms_are_past_only_and_use_the_label_basket_minimum() -> None:
    dates = pd.date_range("2020-01-01", periods=90, freq="B")
    symbols = ("A", "B", "C", "D", *DEFENSIVE_SYMBOLS, "510300.SH", "510500.SH")
    close = pd.DataFrame(
        {symbol: np.linspace(100.0, 140.0, len(dates)) for symbol in symbols}, index=dates
    )
    close.loc[dates[:25], "D"] = np.nan
    first = build_market_state_space(
        close.iloc[:70],
        candidate_symbols=("A", "B", "C", "D"),
        min_attack_members=3,
        min_defensive_members=4,
    )
    all_rows = build_market_state_space(
        close,
        candidate_symbols=("A", "B", "C", "D"),
        min_attack_members=3,
        min_defensive_members=4,
    )
    expected = {
        "ATTACK_RET_20",
        "ATTACK_RET_60",
        "ATTACK_REL_DEFENSIVE_20",
        "ATTACK_REL_DEFENSIVE_60",
        "ATTACK_DD_20",
        "ATTACK_DD_60",
    }
    assert expected <= set(first)
    assert first["ATTACK_RET_20"].notna().any()
    for name in expected:
        pd.testing.assert_series_equal(first[name], all_rows[name].iloc[:70], check_names=True)


def test_directional_signature_excludes_neutral_cells() -> None:
    cells = {
        "down_2022_h5": 0.1,
        "down_2022_h10": 0.2,
        "down_2022_h20": 0.3,
        "current_2025_2026_h5": 0.1,
        "current_2025_2026_h10": 0.2,
        "current_2025_2026_h20": 0.3,
        "sideways_2023_2024_h5": -100.0,
    }
    direction, passed, signed = directional_signature(
        cells,
        directional_blocks=("down_2022", "current_2025_2026"),
        horizons=(5, 10, 20),
    )
    assert direction == 1
    assert passed
    assert signed["down_2022_h5"] > 0


def test_runner_directional_columns_are_named_without_mean_suffix() -> None:
    stored = {"down_2022_h5_mean": 0.1, "current_2025_2026_h5_mean": 0.2}
    referee_inputs = {
        key.removesuffix("_mean"): value for key, value in stored.items()
    }
    direction, passed, signed = directional_signature(
        referee_inputs,
        directional_blocks=("down_2022", "current_2025_2026"),
        horizons=(5,),
    )
    assert direction == 1
    assert passed
    assert signed == {"down_2022_h5": 0.1, "current_2025_2026_h5": 0.2}


def test_neutral_harm_uses_one_sided_negative_test() -> None:
    pvalue, count, _ = negative_effect_pvalue(pd.Series([-1.0] * 80))
    assert count == 4
    assert pvalue < 0.05


def test_benchmark_is_state_input_and_not_label_member() -> None:
    close = _opens(80).rename(columns={"A": "510300.SH", "B": "510500.SH"})
    state = build_market_state_space(close, candidate_symbols=("510300.SH",), benchmark_symbols=("510300.SH", "510500.SH"))
    assert state
    # The label module receives an explicit attack basket; the runner never
    # passes benchmark-role symbols into it.
    basket = BasketSpec(("A",), min_attack_members=1, min_defensive_members=4)
    assert "510300.SH" not in basket.attack_symbols


def test_hierarchical_holm_gates_families_and_uses_prior_attempts() -> None:
    pvalues = pd.Series([0.001, 0.20, 0.40], index=["a", "b", "c"])
    families = pd.Series(["trend", "trend", "breadth"], index=pvalues.index)
    fresh, family_table = hierarchical_family_holm(pvalues, families, 0.05)
    assert fresh.loc["a"]
    assert family_table.set_index("family").loc["trend", "family_pass"]
    prior_attempts = pd.DataFrame(
        {"pvalue": np.repeat(0.5, 100), "family": np.repeat("trend", 100)}
    )
    with_prior, _ = hierarchical_family_holm(
        pvalues, families, 0.05, prior_attempts
    )
    assert not with_prior.loc["a"]
