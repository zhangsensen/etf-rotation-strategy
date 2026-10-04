from __future__ import annotations

from pathlib import Path
import runpy
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml

from etf_strategy.core.etf_daily_structure_factor_space import (
    build_daily_structure_factor_space,
)
from etf_strategy.core.etf_family_catalog import (
    blocked_family_reasons,
    load_family_catalog,
)
from etf_strategy.core.family_registry import (
    load_builtin_families,
    resolve_family,
)
from etf_strategy.core.etf_lead_lag_factor_space import build_lead_lag_factor_space
from etf_strategy.core.etf_benchmark_factor_space import build_benchmark_factor_space
from etf_strategy.core.etf_range_memory_factor_space import (
    build_range_memory_factor_space,
)
from etf_strategy.core.etf_gap_volatility_factor_space import (
    build_gap_volatility_factor_space,
)
from etf_strategy.core.etf_liquidity_variability_factor_space import (
    build_liquidity_variability_factor_space,
)
from etf_strategy.core.etf_gap_response_factor_space import (
    build_gap_response_factor_space,
)
from etf_strategy.core.etf_data_provenance import hash_config_dependencies


ROOT = Path(__file__).resolve().parents[1]


def test_ranked_sources_reuses_declared_shared_family_space(tmp_path, monkeypatch) -> None:
    namespace = runpy.run_path(
        str(ROOT / "scripts/research/evaluate_all_etf_daily.py"),
        run_name="shared_family_space_test",
    )
    calls = 0
    index = pd.date_range("2025-01-02", periods=2, freq="B")
    panel = pd.DataFrame([[1.0, 2.0], [2.0, 1.0]], index=index, columns=["A", "B"])

    def builder(panels, eligibility, data_root, config):
        nonlocal calls
        calls += 1
        return {"ATOM_A": panels["close"], "ATOM_B": -panels["close"]}

    builder.family_space_cache_key = "shared_test_space"
    function_globals = namespace["_ranked_sources"].__globals__
    monkeypatch.setitem(function_globals, "load_builtin_families", lambda: None)
    monkeypatch.setitem(
        function_globals,
        "resolve_family",
        lambda _source: SimpleNamespace(builder=builder),
    )
    catalog = {}
    for source, atom in (("source_a", "ATOM_A"), ("source_b", "ATOM_B")):
        path = tmp_path / f"{source}.yaml"
        path.write_text(yaml.safe_dump({"frequency": "1d", "atoms": [{"name": atom}]}))
        catalog[source] = path

    atoms = namespace["_ranked_sources"](
        {"source_a", "source_b"},
        catalog=catalog,
        panels={"close": panel},
        eligibility=pd.DataFrame(True, index=index, columns=panel.columns),
        data_root=tmp_path,
        needed_atoms={"ATOM_A", "ATOM_B"},
    )

    assert calls == 1
    assert set(atoms) == {"ATOM_A", "ATOM_B"}


def test_secondary_family_configs_are_content_pinned() -> None:
    dependencies = hash_config_dependencies(
        ROOT, [ROOT / "configs/family_category_state_v1.yaml"]
    )
    assert set(dependencies) == {"configs/etf_asset_classes_current20_v1.yaml"}
    assert len(next(iter(dependencies.values()))) == 64


def _synthetic_ohlc(periods: int = 100) -> dict[str, pd.DataFrame]:
    index = pd.date_range("2020-01-01", periods=periods, freq="B")
    columns = ["A", "B", "C"]
    base = np.arange(periods, dtype=float)[:, None] + np.array([[100.0, 120.0, 140.0]])
    close = pd.DataFrame(base, index=index, columns=columns)
    open_ = close * 0.997
    high = pd.DataFrame(
        np.maximum(open_.to_numpy(), close.to_numpy()) * 1.01,
        index=index,
        columns=columns,
    )
    low = pd.DataFrame(
        np.minimum(open_.to_numpy(), close.to_numpy()) * 0.99,
        index=index,
        columns=columns,
    )
    return {"open": open_, "high": high, "low": low, "close": close}


def test_breadth_catalog_is_one_source_per_information_family() -> None:
    load_builtin_families()
    paths = load_family_catalog(ROOT / "configs/family_catalog_v1.yaml", ROOT)
    assert len(paths) == 25
    sources = []
    families = []
    for path in paths:
        import yaml

        config = yaml.safe_load(path.read_text())
        sources.append(config["factor_source"])
        families.append(resolve_family(config["factor_source"]).information_family)
    assert len(set(sources)) == len(sources)
    assert len(set(families)) == len(families)
    raw_catalog = __import__("yaml").safe_load(
        (ROOT / "configs/family_catalog_v1.yaml").read_text()
    )
    assert not set(sources) & set(raw_catalog["retired_sources"])


def test_unavailable_etf_native_families_are_explicitly_blocked() -> None:
    reasons = blocked_family_reasons(ROOT / "configs/family_catalog_v1.yaml")
    assert reasons["share_creation_redemption_flow"] == "daily_fund_share"
    assert reasons["nav_premium_discount"] == "point_in_time_iopv_or_nav"
    assert len(reasons) == 5


def test_daily_structure_atoms_do_not_change_when_future_row_changes() -> None:
    panels = _synthetic_ohlc()
    baseline = build_daily_structure_factor_space(panels)
    cutoff = panels["close"].index[-2]
    changed = {name: frame.copy() for name, frame in panels.items()}
    for frame in changed.values():
        frame.iloc[-1] *= 100.0
    perturbed = build_daily_structure_factor_space(changed)
    for name in baseline:
        pd.testing.assert_frame_equal(
            baseline[name].loc[:cutoff], perturbed[name].loc[:cutoff]
        )


def test_path_efficiency_is_bounded() -> None:
    factors = build_daily_structure_factor_space(_synthetic_ohlc())
    for window in (10, 20, 60):
        values = factors[f"PATH_EFFICIENCY_{window}"].stack().dropna()
        assert values.between(0.0, 1.0).all()


def test_range_memory_is_causal_and_exposes_one_new_atom() -> None:
    panels = _synthetic_ohlc(100)
    baseline = build_range_memory_factor_space(panels)
    assert set(baseline) == {"RANGE_ACF1_20"}
    changed = {name: frame.copy() for name, frame in panels.items()}
    for frame in changed.values():
        frame.iloc[-1] *= 100.0
    perturbed = build_range_memory_factor_space(changed)
    pd.testing.assert_frame_equal(
        baseline["RANGE_ACF1_20"].iloc[:-1],
        perturbed["RANGE_ACF1_20"].iloc[:-1],
    )
    load_builtin_families()
    assert resolve_family("range_memory").information_family == "range_memory"


def test_gap_volatility_and_liquidity_variability_are_causal() -> None:
    panels = _synthetic_ohlc(140)
    panels["amount"] = panels["close"].mul(
        pd.Series(np.linspace(1.0, 2.0, 140), index=panels["close"].index), axis=0
    )
    gap = build_gap_volatility_factor_space(panels["open"], panels["close"])
    liquidity = build_liquidity_variability_factor_space(panels["amount"])
    assert set(gap) == {"GAP_VOL_RATIO_20"}
    assert set(liquidity) == {"LOG_AMOUNT_VOL_20"}
    changed = {name: frame.copy() for name, frame in panels.items()}
    for frame in changed.values():
        frame.iloc[-1] *= 10.0
    changed_gap = build_gap_volatility_factor_space(changed["open"], changed["close"])
    changed_liquidity = build_liquidity_variability_factor_space(changed["amount"])
    pd.testing.assert_frame_equal(gap["GAP_VOL_RATIO_20"].iloc[:-1], changed_gap["GAP_VOL_RATIO_20"].iloc[:-1])
    pd.testing.assert_frame_equal(liquidity["LOG_AMOUNT_VOL_20"].iloc[:-1], changed_liquidity["LOG_AMOUNT_VOL_20"].iloc[:-1])


def test_gap_response_is_causal_and_exposes_one_new_atom() -> None:
    panels = _synthetic_ohlc(100)
    baseline = build_gap_response_factor_space(panels)
    assert set(baseline) == {"GAP_SESSION_CORR_20"}
    changed = {name: frame.copy() for name, frame in panels.items()}
    for frame in changed.values():
        frame.iloc[-1] *= 100.0
    perturbed = build_gap_response_factor_space(changed)
    pd.testing.assert_frame_equal(
        baseline["GAP_SESSION_CORR_20"].iloc[:-1],
        perturbed["GAP_SESSION_CORR_20"].iloc[:-1],
    )
    load_builtin_families()
    assert resolve_family("gap_response").information_family == "gap_response"




def test_tail_quantiles_are_available_and_causal() -> None:
    factors = build_daily_structure_factor_space(_synthetic_ohlc(140))
    for window in (20, 60):
        values = factors[f"TAIL_Q10_{window}"]
        assert values.notna().any().any()
    panels = _synthetic_ohlc(140)
    baseline = build_daily_structure_factor_space(panels)
    changed = {name: frame.copy() for name, frame in panels.items()}
    for frame in changed.values():
        frame.iloc[-1] *= 100.0
    perturbed = build_daily_structure_factor_space(changed)
    for window in (20, 60):
        name = f"TAIL_Q10_{window}"
        pd.testing.assert_frame_equal(
            baseline[name].iloc[:-1], perturbed[name].iloc[:-1]
        )


def test_closed_redundant_family_cannot_reenter_catalog(tmp_path) -> None:
    load_builtin_families()
    raw = yaml.safe_load((ROOT / "configs/family_catalog_v1.yaml").read_text())
    raw["available_families"].append(
        {
            "source": "within_category_selection",
            "config": "configs/family_within_category_selection_v1.yaml",
            "data": "daily_close_classification",
        }
    )
    path = tmp_path / "catalog.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match="retired ETF sources cannot be available"):
        load_family_catalog(path, ROOT)


def test_lead_lag_uses_only_current_and_past_returns() -> None:
    index = pd.date_range("2020-01-01", periods=100, freq="B")
    market_return = pd.Series(np.linspace(-0.01, 0.01, len(index)), index=index)
    benchmark = (1.0 + market_return).cumprod() * 100.0
    delayed = (1.0 + market_return.shift(1).fillna(0.0) * 2.0).cumprod() * 80.0
    close = pd.DataFrame({"BENCH": benchmark, "ASSET": delayed}, index=index)
    factors = build_lead_lag_factor_space(close, ["BENCH"])
    assert factors["MARKET_LEAD_CORR_20"].loc[index[-2], "ASSET"] > 0.99
    changed = close.copy()
    changed.iloc[-1] *= 10.0
    changed_factors = build_lead_lag_factor_space(changed, ["BENCH"])
    for name, frame in factors.items():
        pd.testing.assert_frame_equal(frame.iloc[:-1], changed_factors[name].iloc[:-1])


def test_peer_diffusion_atoms_are_leave_one_out_and_causal() -> None:
    index = pd.date_range("2020-01-01", periods=100, freq="B")
    base = pd.Series(np.linspace(-0.01, 0.01, len(index)), index=index)
    close = pd.DataFrame(
        {
            "A": (1 + base).cumprod() * 100,
            "B": (1 + base.shift(1).fillna(0)).cumprod() * 90,
            "C": (1 - base).cumprod() * 80,
            "BENCH": (1 + base).cumprod() * 110,
        },
        index=index,
    )
    factors = build_lead_lag_factor_space(close, ["BENCH"], ["A", "B", "C"])
    assert {"PEER_LEAD_BETA_20", "PEER_LEAD_CORR_20", "PEER_LEAD_NETWORK_CORR_20"} <= set(factors)
    changed = close.copy()
    changed.iloc[-1, changed.columns.get_loc("C")] *= 10.0
    changed_factors = build_lead_lag_factor_space(changed, ["BENCH"], ["A", "B", "C"])
    for name in factors:
        pd.testing.assert_frame_equal(factors[name].iloc[:-1], changed_factors[name].iloc[:-1])


def test_market_sensitivity_adds_upside_beta_without_relative_return_subtraction() -> None:
    index = pd.date_range("2020-01-01", periods=100, freq="B")
    close = pd.DataFrame(
        {
            "A": np.linspace(100, 130, len(index)),
            "B": np.linspace(80, 110, len(index)),
            "510300.SH": np.linspace(100, 120, len(index)),
            "510500.SH": np.linspace(90, 115, len(index)),
        },
        index=index,
    )
    factors = build_benchmark_factor_space(close, ["510300.SH", "510500.SH"])
    assert {"UPSIDE_BETA_20", "UPSIDE_BETA_60"} <= set(factors)


def test_cross_etf_peer_config_matches_the_fourteen_candidate_codes() -> None:
    universe = yaml.safe_load((Path(__file__).resolve().parents[3] / "config/etf_rotation_universe_v1.json").read_text())
    candidate_codes = {row["ts_code"] for row in universe["etfs"] if row["role"] == "candidate"}
    config_path = Path(__file__).resolve().parents[1] / "configs/family_cross_etf_lead_lag_v1.yaml"
    config = yaml.safe_load(config_path.read_text())
    assert set(config["peer_symbols"]) == candidate_codes
    assert len(config["peer_symbols"]) == 14
    assert all(symbol.endswith((".SH", ".SZ")) for symbol in config["peer_symbols"])


def test_adjudication_rejects_legacy_source_config_bypass() -> None:
    source_paths = runpy.run_path(
        str(ROOT / "scripts/run_family_adjudication.py"), run_name="catalog_guard_test"
    )["_source_paths"]
    with pytest.raises(ValueError, match="source_configs is retired"):
        source_paths(
            {"source_configs": ["configs/automated_mining_current20_v1.yaml"]},
            ROOT / "configs/family_adjudication_v1.yaml",
        )


def test_ic_shelf_candidate_order_is_stable_when_key_is_also_the_index() -> None:
    namespace = runpy.run_path(
        str(ROOT / "scripts/build_ic_factor_shelf.py"), run_name="shelf_order_test"
    )
    order = namespace["_deterministic_candidate_order"]
    summary = pd.DataFrame(
        {
            "expression_key": ["family:z", "family:a", "family:m"],
            "discovery_ic": [-0.03, 0.03, 0.04],
        }
    ).set_index("expression_key", drop=False)
    assert order(summary, set(summary.index)) == [
        "family:m",
        "family:a",
        "family:z",
    ]
    mechanism = namespace["_mechanism_id"]
    assert mechanism("tail", "RETURN_SKEW_20", {}) == "tail:RETURN_SKEW"
    assert mechanism("tail", "RETURN_SKEW_60", {}) == "tail:RETURN_SKEW"
    assert mechanism("category", "CATEGORY_VOL_60", {"CATEGORY_VOL_60": "volatility"}) == "volatility"


def test_ic_shelf_requires_mechanism_and_identity_breadth() -> None:
    config = yaml.safe_load((ROOT / "configs/ic_factor_shelf_v1.yaml").read_text())
    assert config["target_factor_count"] >= 15
    assert config["min_axis_count"] >= 7
    assert config["min_effective_factor_count"] >= 9.0
    assert config["min_family_count"] >= 12
    assert config["max_selected_per_family"] <= 2
    assert config["require_identity_gate_pass"] is True
    assert config["min_discovery_days"] >= 360
    assert config["min_abs_discovery_ic"] >= 0.01
    assert config["mechanism_limits"]["intraday_turnover_composition"]["max_selected"] == 1
