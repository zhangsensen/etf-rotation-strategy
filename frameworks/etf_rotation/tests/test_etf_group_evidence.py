import math
import ast
import importlib.util
from pathlib import Path

import pandas as pd

_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src/etf_strategy/core/etf_group_evidence.py"
)
_SPEC = importlib.util.spec_from_file_location("etf_group_evidence", _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)
evidence_layers = _MODULE.evidence_layers


SCREENS = {
    "min_days": 360,
    "min_ic": 0.01,
    "min_ic_hac_t": 2.0,
    "min_ic_block_t": 2.0,
    "min_positive_years": 2,
    "min_excess8_hac_t": 2.0,
    "paired_min_hac_t": 1.5,
    "alpha": 0.05,
}


def row(**updates):
    value = {
        "n": 400,
        "ic_mean": 0.02,
        "ic_hac_t": 2.5,
        "ic_block_t": 2.2,
        "positive_years": 3,
        "all_eligible_years_positive": True,
        "min_leave_group_ic": 0.005,
        "ic_p_normal_one_sided": 0.0001,
        "excess8_mean": 0.01,
        "excess8_hac_t": 2.2,
        "screen_pass": False,
        "all_layers": False,
    }
    value.update(updates)
    return value


def test_ic_supported_when_economic_gate_fails():
    out = evidence_layers(row(excess8_mean=-0.01, excess8_hac_t=-2), SCREENS, 96)
    assert out["coverage_sufficient"] is True
    assert out["ic_metrics_pass"] is True
    assert out["ic_supported"] is True
    assert out["ic_budget_supported"] is True
    assert out["economic_metrics_pass"] is False
    assert out["economic_supported"] is False
    assert out["screen_pass"] is False
    assert out["all_layers"] is False


def test_ic_lead_survives_failed_increment_and_budget():
    out = evidence_layers(
        row(ic_p_normal_one_sided=0.02, excess8_mean=-0.01), SCREENS, 384,
        paired_ic=[{"ic_n": 400, "ic_increment_mean": -0.01, "ic_increment_hac_t": -1}],
    )
    assert out["ic_supported"] is True
    assert out["paired_ic_supported"] is False
    assert out["ic_budget_supported"] is False


def test_2025_chosen_direction_is_judged_only_on_2026_confirmation():
    combined = row(ic_hac_t=4.0, ic_block_t=3.5)
    failed_2026 = row(
        n=180,
        ic_mean=0.02,
        ic_hac_t=1.9,
        ic_block_t=2.2,
        min_leave_group_ic=0.003,
    )
    out = evidence_layers(
        combined,
        {**SCREENS, "min_historical_2026_days": 120},
        96,
        historical_2026_row=failed_2026,
        evidence_policy="2025_DIRECTION_2026_HISTORICAL_SEGMENT",
    )
    assert out["historical_ic_supported"] is True
    assert out["historical_2026_metrics_pass"] is False
    assert out["ic_supported"] is False


def test_seen_2026_adaptive_formula_cannot_confirm_on_same_2026_surface():
    strong_2026 = row(n=180, min_leave_group_ic=0.004)
    out = evidence_layers(
        row(),
        {**SCREENS, "min_historical_2026_days": 120},
        96,
        historical_2026_row=strong_2026,
        evidence_policy="SEEN_2026_ADAPTIVE_NOT_CONFIRMATION",
    )
    assert out["historical_2026_metrics_pass"] is True
    assert out["historical_2026_contaminated"] is True
    assert out["historical_2026_supported"] is False
    assert out["ic_supported"] is False


def test_reverse_watch_is_signed_and_not_positive_ic():
    out = evidence_layers(
        row(ic_mean=-0.02, ic_hac_t=-2.1, ic_block_t=-2.0), SCREENS, 96
    )
    assert out["reverse_watch"] is True
    assert out["ic_metrics_pass"] is False
    assert out["ic_supported"] is False


def test_coverage_and_budget_are_separate_failures():
    low_coverage = evidence_layers(row(n=359), SCREENS, 96)
    assert low_coverage["coverage_sufficient"] is False
    assert low_coverage["ic_metrics_pass"] is True
    assert low_coverage["ic_supported"] is False

    over_budget = evidence_layers(row(ic_p_normal_one_sided=0.001), SCREENS, 96)
    assert over_budget["ic_supported"] is True
    assert over_budget["ic_budget_pass"] is False
    assert over_budget["ic_budget_supported"] is False


def test_interaction_ic_and_economic_increment_are_independent():
    paired_ic = [
        {"ic_n": 400, "ic_increment_mean": 0.01, "ic_increment_hac_t": 1.6},
        {"ic_n": 400, "ic_increment_mean": 0.02, "ic_increment_hac_t": 1.8},
    ]
    paired_economic = [
        {"excess8_n": 400, "excess8_increment_mean": -0.01, "excess8_increment_hac_t": -2},
        {"excess8_n": 400, "excess8_increment_mean": -0.02, "excess8_increment_hac_t": -2},
    ]
    out = evidence_layers(row(), SCREENS, 96, paired_ic, paired_economic)
    assert out["paired_ic_supported"] is True
    assert out["paired_economic_supported"] is False


def test_nan_fails_closed_for_all_positive_gates():
    out = evidence_layers(
        row(
            ic_mean=math.nan,
            ic_hac_t=math.nan,
            ic_p_normal_one_sided=math.nan,
            excess8_mean=math.nan,
        ),
        SCREENS,
        96,
    )
    assert out["ic_metrics_pass"] is False
    assert out["ic_supported"] is False
    assert out["ic_budget_pass"] is False
    assert out["ic_budget_supported"] is False
    assert out["economic_metrics_pass"] is False
    assert out["economic_supported"] is False


def test_year_gate_budget_inputs_and_paired_shape_fail_closed():
    assert evidence_layers(row(all_eligible_years_positive=math.nan), SCREENS, 96)[
        "ic_metrics_pass"
    ] is False
    assert evidence_layers(row(all_eligible_years_positive="true"), SCREENS, 96)[
        "ic_metrics_pass"
    ] is False
    assert evidence_layers(row(ic_p_normal_one_sided=-0.1), SCREENS, 96)[
        "ic_budget_pass"
    ] is False
    assert evidence_layers(row(), {**SCREENS, "alpha": math.nan}, 96)[
        "ic_budget_pass"
    ] is False
    assert evidence_layers(row(), SCREENS, 0)["ic_budget_pass"] is False
    assert evidence_layers(row(), SCREENS, 96, {"ic_n": 400})[
        "paired_ic_supported"
    ] is False


def test_discovery_runner_wires_layers_and_snapshots_helper():
    runner = (
        Path(__file__).resolve().parents[1]
        / "scripts/research/discover_etf_groups.py"
    ).read_text()
    assert "etf_group_evidence as evidence_engine" in runner
    assert "Path(evidence_engine.__file__)" in runner
    assert "evidence_engine.evidence_layers(" in runner
    assert "ic_budget_candidates" in runner
    assert "reverse_watch_candidates" in runner
    assert "legacy_combined_shortlisted" in runner


def test_actual_runner_ic_lists_cannot_be_vetoed_by_economics_or_legacy_gates():
    """Execute the runner's real list selectors without reading market data.

    Keeping this test outside the sealed runner avoids changing historical
    source hashes just to test presentation. Missing/renamed selectors fail.
    """
    cases = [
        ("ic_only", row(excess8_mean=-.01, excess8_hac_t=-2,
                        ic_p_normal_one_sided=.01)),
        ("ic_conditional_budget", row(excess8_mean=-.01, excess8_hac_t=-2)),
        ("economic_only", row(ic_mean=0, ic_hac_t=0, ic_block_t=0,
                              screen_pass=True, all_layers=True)),
        ("coverage_insufficient", row(n=359, screen_pass=True, all_layers=True)),
        ("reverse", row(ic_mean=-.02, ic_hac_t=-2.5, ic_block_t=-2.2)),
    ]
    summary = pd.DataFrame([
        {"candidate": name, **evidence_layers(value, SCREENS, 96)}
        for name, value in cases
    ])
    path = Path(__file__).resolve().parents[1] / "scripts/research/discover_etf_groups.py"
    tree = ast.parse(path.read_text())
    names = {"ic_candidates", "ic_budget_candidates", "reverse_watch_candidates",
             "economic_candidates"}
    selectors = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id in names for t in node.targets)]
    assert len(selectors) == len(names)
    namespace = {"summary": summary}
    exec(compile(ast.Module(body=selectors, type_ignores=[]), str(path), "exec"), namespace)
    assert namespace["ic_candidates"] == ["ic_only", "ic_conditional_budget"]
    assert namespace["ic_budget_candidates"] == ["ic_conditional_budget"]
    assert namespace["reverse_watch_candidates"] == ["reverse"]
    assert "economic_only" in namespace["economic_candidates"]
    assert not set(namespace["ic_candidates"]) & set(namespace["economic_candidates"])
