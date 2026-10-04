from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_family_referee import (
    common_sample_spearman,
    effective_test_count,
    maxstat_block_signflip,
    resolve_permutation_draws,
    timing_exposure_diagnostic,
)
from etf_strategy.core.etf_intraday_factor_space import (
    FREQUENCY_SPECS,
    build_intraday_factor_space,
    expected_intraday_times,
    inspect_intraday_coverage,
)
from etf_strategy.core.etf_cumulative_ledger import ETFCumulativeLedger, alpha_spending
from etf_strategy.core.family_registry import load_builtin_families, registered_sources, resolve_family
from etf_strategy.core.etf_identity import identity_gate
from etf_strategy.core.etf_marginal_ic import residualize_scores


def test_common_sample_spearman_reranks_after_intersection() -> None:
    dates = pd.date_range("2024-01-01", periods=2)
    columns = list("ABCD")
    signal = pd.DataFrame([[1, 2, 100, np.nan], [4, 3, 2, 1]], index=dates, columns=columns)
    label = pd.DataFrame([[1, 2, np.nan, 3], [1, 2, 3, 4]], index=dates, columns=columns)
    eligible = pd.DataFrame(True, index=dates, columns=columns)
    ic, count = common_sample_spearman(signal, label, eligible, min_pairs=2)
    assert count.tolist() == [2, 4]
    assert np.allclose(ic.to_numpy(), [1.0, -1.0])


def test_timing_exposure_is_diagnostic_only() -> None:
    index = pd.date_range("2020-01-01", periods=100)
    basket = pd.Series(np.linspace(-0.1, 0.1, 100), index=index)
    ic = 0.03 + 2.0 * basket
    beta, r2 = timing_exposure_diagnostic(ic, basket, index[-1])
    assert np.isclose(beta, 2.0)
    assert np.isclose(r2, 1.0)


def test_maxstat_and_effective_count_detect_duplicate_signal() -> None:
    rng = np.random.default_rng(7)
    index = pd.date_range("2020-01-01", periods=500)
    common = pd.Series(0.05 + rng.normal(0, 0.05, len(index)), index=index)
    matrix = pd.DataFrame({"a": common, "b": common, "null": rng.normal(0, 0.05, len(index))})
    _, pvalue = maxstat_block_signflip(matrix, block_sessions=20, draws=199, seed=3)
    assert pvalue["a"] <= 0.05
    assert pvalue["b"] <= 0.05
    assert effective_test_count(matrix) < 2.5


def test_permutation_draws_reach_generation_alpha_resolution() -> None:
    draws = resolve_permutation_draws(100, 0.0008, multiplicity=10)
    assert draws >= 12_500
    assert 1.0 / (draws + 1.0) < 0.0008 / 10
    with pytest.raises(ValueError, match="unreachable"):
        resolve_permutation_draws(10, 1e-8, max_draws=100_000)


def test_intraday_atoms_use_complete_day_only(tmp_path) -> None:
    folder = tmp_path / "60m"
    folder.mkdir()
    frame = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                ["2024-01-02 10:30", "2024-01-02 11:30", "2024-01-02 14:00", "2024-01-02 15:00"]
            ),
            "open": [100.0, 101.0, 102.0, 103.0],
            "high": [102.0, 103.0, 104.0, 105.0],
            "low": [99.0, 100.0, 101.0, 102.0],
            "close": [101.0, 102.0, 103.0, 104.0],
            "turnover": [40.0, 30.0, 20.0, 10.0],
            "volume": [4.0, 3.0, 2.0, 1.0],
        }
    )
    frame.to_parquet(folder / "A.parquet")
    factors = build_intraday_factor_space(tmp_path, ["A"])
    date = pd.Timestamp("2024-01-02")
    assert np.isclose(factors["FIRST_HOUR_RET"].loc[date, "A"], 0.01)
    assert np.isclose(factors["FIRST_HOUR_TURNOVER_SHARE"].loc[date, "A"], 0.4)
    assert np.isclose(factors["LAST_HOUR_TURNOVER_SHARE"].loc[date, "A"], 0.1)
    assert np.isclose(
        factors["MORNING_TURNOVER_SHARE"].loc[date, "A"], (40.0 + 30.0) / 100.0
    )
    assert np.isclose(
        factors["AFTERNOON_TURNOVER_SHARE"].loc[date, "A"], (20.0 + 10.0) / 100.0
    )
    assert 0.0 <= factors["INTRADAY_PATH_EFFICIENCY"].loc[date, "A"] <= 1.0
    assert -1.0 <= factors["INTRADAY_TAIL_JUMP_ASYMMETRY"].loc[date, "A"] <= 1.0
    assert 0.0 <= factors["INTRADAY_JUMP_INTENSITY"].loc[date, "A"] <= 1.0
    assert np.isfinite(factors["INTRADAY_RETURN_SKEW"].loc[date, "A"])
    assert np.isfinite(factors["INTRADAY_RETURN_KURTOSIS"].loc[date, "A"])
    assert np.isfinite(factors["SIGNED_TURNOVER_SHOCK"].loc[date, "A"])
    assert np.isfinite(factors["TAIL_TURNOVER_PRICE_IMPACT"].loc[date, "A"])


def test_intraday_builder_honors_as_of(tmp_path) -> None:
    folder = tmp_path / "60m"
    folder.mkdir()
    rows = []
    for date in ("2024-01-02", "2024-01-03"):
        for time, value in zip(("10:30", "11:30", "14:00", "15:00"), (100, 101, 102, 103)):
            rows.append(
                {
                    "datetime": pd.Timestamp(f"{date} {time}"),
                    "open": value,
                    "high": value + 2,
                    "low": value - 1,
                    "close": value + 1,
                    "turnover": float((value + 1) * 10),
                    "volume": 10.0,
                }
            )
    pd.DataFrame(rows).to_parquet(folder / "A.parquet")
    factors = build_intraday_factor_space(tmp_path, ["A"], as_of="2024-01-02")
    assert factors["FIRST_HOUR_RET"].index.max() == pd.Timestamp("2024-01-02")
    expected_daily_vwap = sum((value + 1) * 10 for value in (100, 101, 102, 103)) / 40
    assert np.isclose(
        factors["CLOSE_VWAP_DEVIATION"].loc[pd.Timestamp("2024-01-02"), "A"],
        104 / expected_daily_vwap - 1,
    )


def test_intraday_vwap_rejects_turnover_volume_unit_break(tmp_path) -> None:
    folder = tmp_path / "60m"
    folder.mkdir()
    pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                ["2024-01-02 10:30", "2024-01-02 11:30", "2024-01-02 14:00", "2024-01-02 15:00"]
            ),
            "open": [100.0] * 4,
            "high": [102.0] * 4,
            "low": [99.0] * 4,
            "close": [101.0] * 4,
            "turnover": [1_000_000.0] * 4,
            "volume": [10.0] * 4,
        }
    ).to_parquet(folder / "A.parquet")
    factors = build_intraday_factor_space(tmp_path, ["A"])
    assert np.isnan(factors["CLOSE_VWAP_DEVIATION"].iloc[0, 0])


def test_intraday_frequency_contract_accepts_all_five_complete_schedules(tmp_path) -> None:
    for frequency in FREQUENCY_SPECS:
        folder = tmp_path / frequency
        folder.mkdir()
        times = expected_intraday_times(pd.Timestamp("2024-01-02"), frequency)
        values = np.linspace(100.0, 104.0, len(times))
        pd.DataFrame(
            {
                "datetime": times,
                "open": values,
                "high": values + 0.2,
                "low": values - 0.2,
                "close": values + 0.1,
                "turnover": np.full(len(times), 1000.0),
                "volume": np.full(len(times), 10.0),
            }
        ).to_parquet(folder / "A.parquet")
    coverage = inspect_intraday_coverage(tmp_path, ["A"])
    assert coverage.complete_days.tolist() == [1] * len(FREQUENCY_SPECS)
    assert coverage.incomplete_days.tolist() == [0] * len(FREQUENCY_SPECS)
    for frequency in FREQUENCY_SPECS:
        factors = build_intraday_factor_space(tmp_path, ["A"], frequency=frequency)
        assert factors["INTRADAY_TREND_CONSISTENCY"].notna().any().any()
        assert factors["MORNING_VOL_SHARE"].notna().any().any()
        assert factors["INTRADAY_PV_RETURN_TURNOVER_CORR"].shape == (1, 1)


def test_intraday_incomplete_day_is_excluded_and_future_bar_does_not_rewrite_prior_day(tmp_path) -> None:
    folder = tmp_path / "5m"
    folder.mkdir()
    rows = []
    for date in ("2024-01-02", "2024-01-03"):
        times = expected_intraday_times(pd.Timestamp(date), "5m")
        for i, timestamp in enumerate(times):
            value = 100.0 + i * 0.01
            rows.append(
                {
                    "datetime": timestamp,
                    "open": value,
                    "high": value + 0.1,
                    "low": value - 0.1,
                    "close": value + 0.05,
                    "turnover": 1000.0 + i,
                    "volume": 10.0,
                }
            )
    frame = pd.DataFrame(rows).drop(index=3)
    frame.to_parquet(folder / "A.parquet")
    coverage = inspect_intraday_coverage(tmp_path, ["A"], frequencies=("5m",))
    assert coverage.complete_days.tolist() == [1]
    assert coverage.incomplete_days.tolist() == [1]
    factors = build_intraday_factor_space(tmp_path, ["A"], frequency="5m")
    assert factors["INTRADAY_NET_RET"].index.tolist() == [pd.Timestamp("2024-01-03")]


def test_etf_family_plugins_resolve_without_stock_engine() -> None:
    load_builtin_families()
    expected = {
        "directional_trend", "price_location", "downside_risk", "daily_candle",
        "path_efficiency", "return_tail_shape", "trading_activity",
        "price_volume_coupling", "market_sensitivity", "category_state",
        "serial_dependence", "cross_etf_lead_lag", "intraday_return_path",
        "intraday_turnover_shape", "intraday_vwap_position",
        "intraday_trend_consistency", "intraday_volatility_structure",
        "intraday_price_volume_shock", "intraday_tail_reversal_jump",
        "intraday_return_distribution", "intraday_turnover_asymmetry",
    }
    assert expected <= set(registered_sources())
    retired = {"ohlcv", "cross_asset", "benchmark_relative", "liquidity", "intraday_path"}
    assert not retired & set(registered_sources())
    assert resolve_family("intraday_return_path").information_family == "intraday_return_path"


def test_cumulative_ledger_and_alpha_spending(tmp_path) -> None:
    ledger = ETFCumulativeLedger(tmp_path / "etf.duckdb")
    assert ledger.prior_generation_count() == 0
    assert np.isclose(alpha_spending(0.05, 1), 0.025)
    summary = pd.DataFrame(
        [{
            "expression_key": "synthetic:x",
            "true_family": "synthetic",
            "expression": "X",
            "pooled_maxstat_pvalue": 0.5,
            "family_gate_pass": False,
        }]
    )
    ledger.record("g1", "hash", str(tmp_path), 0.025, summary)
    assert ledger.prior_generation_count() == 1
    assert ledger.has_generation("g1")
    ledger.close()


def test_identity_gate_fails_when_one_symbol_breaks_audit() -> None:
    table = pd.DataFrame(
        {
            "discovery_ic": [-0.05, -0.04],
            "seen_audit_ic": [-0.02, -0.001],
        }
    )
    assert not identity_gate(table, direction=-1.0, min_audit_ic=0.01)


def test_marginal_scores_remove_admitted_cross_section() -> None:
    index = pd.date_range("2024-01-01", periods=2)
    columns = list("ABCDE")
    admitted = pd.DataFrame([np.arange(5), np.arange(5)], index=index, columns=columns)
    candidate = admitted * 3.0 + 7.0
    residual = residualize_scores(candidate, {"existing": admitted})
    assert np.nanmax(np.abs(residual.to_numpy())) < 1e-10


def test_common_sample_spearman_excludes_infinite_inputs():
    signal=pd.DataFrame([[1,2,np.inf,4]])
    label=pd.DataFrame([[1,2,3,-np.inf]])
    eligible=pd.DataFrame(True,index=signal.index,columns=signal.columns)
    ic,count=common_sample_spearman(signal,label,eligible,2)
    assert count.iloc[0]==2
    assert np.isclose(ic.iloc[0],1)


def test_common_sample_accepts_numeric_object_frames():
    signal=pd.DataFrame([[1.,2.,np.inf,4.]],dtype=object)
    label=pd.DataFrame([[1.,2.,3.,np.nan]],dtype=object)
    eligible=pd.DataFrame(True,index=signal.index,columns=signal.columns)
    ic,count=common_sample_spearman(signal,label,eligible,2)
    assert count.iloc[0]==2 and np.isclose(ic.iloc[0],1)
