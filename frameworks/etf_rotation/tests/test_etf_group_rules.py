"""Synthetic boundary tests for the independent ETF-group evidence rules."""

import importlib.util
import math
from pathlib import Path


_PATH = Path(__file__).resolve().parents[1] / "src/etf_strategy/core/etf_group_evidence.py"
_SPEC = importlib.util.spec_from_file_location("etf_group_evidence", _PATH)
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
    "paired_min_hac_t": 2.0,
    "alpha": 0.05,
}


def _row(**updates):
    value = {
        "n": 360,
        "ic_mean": 0.01,
        "ic_hac_t": 2.0,
        "ic_block_t": 2.0,
        "positive_years": 2,
        "all_eligible_years_positive": True,
        "min_leave_group_ic": 0.000001,
        "ic_p_normal_one_sided": 0.05 / 96,
        "excess8_mean": 0.01,
        "excess8_hac_t": 2.0,
    }
    value.update(updates)
    return value


def test_exact_ic_thresholds_and_coverage_boundary_are_inclusive_then_fail_below():
    exact = evidence_layers(_row(), SCREENS, 96)
    assert exact["coverage_sufficient"] is True
    assert exact["ic_metrics_pass"] is True
    assert exact["ic_supported"] is True
    assert exact["ic_budget_pass"] is True

    short = evidence_layers(_row(n=359), SCREENS, 96)
    assert short["coverage_sufficient"] is False
    assert short["ic_metrics_pass"] is True
    assert short["ic_supported"] is False


def test_economic_failure_does_not_remove_ic_support_and_negative_ic_is_not_positive():
    economic_fail = evidence_layers(
        _row(excess8_mean=0.0, excess8_hac_t=2.0), SCREENS, 96
    )
    assert economic_fail["ic_supported"] is True
    assert economic_fail["economic_metrics_pass"] is False
    assert economic_fail["economic_supported"] is False

    negative = evidence_layers(_row(ic_mean=-0.01), SCREENS, 96)
    assert negative["ic_supported"] is False
    assert negative["reverse_watch"] is False

    reverse = evidence_layers(
        _row(ic_mean=-0.01, ic_hac_t=-2.0, ic_block_t=-2.0), SCREENS, 96
    )
    assert reverse["ic_supported"] is False
    assert reverse["reverse_watch"] is True


def test_nan_none_and_non_boolean_year_gate_fail_closed():
    for field in ("ic_mean", "ic_hac_t", "ic_block_t", "min_leave_group_ic"):
        result = evidence_layers(_row(**{field: math.nan}), SCREENS, 96)
        assert result["ic_supported"] is False
    assert evidence_layers(_row(ic_mean=None), SCREENS, 96)["ic_supported"] is False
    assert evidence_layers(_row(all_eligible_years_positive=1), SCREENS, 96)[
        "ic_supported"
    ] is False


def test_paired_none_is_not_applicable_and_both_ic_legs_are_required():
    base = _row()
    not_interaction = evidence_layers(base, SCREENS, 96, paired_ic=None)
    assert not_interaction["paired_ic_supported"] is None

    passing = [
        {"ic_n": 360, "ic_increment_mean": 0.001, "ic_increment_hac_t": 2.0},
        {"ic_n": 360, "ic_increment_mean": 0.002, "ic_increment_hac_t": 2.0},
    ]
    assert evidence_layers(base, SCREENS, 96, paired_ic=passing)[
        "paired_ic_supported"
    ] is True

    one_leg_fails = [*passing[:-1], {**passing[-1], "ic_increment_hac_t": 1.999}]
    assert evidence_layers(base, SCREENS, 96, paired_ic=one_leg_fails)[
        "paired_ic_supported"
    ] is False


def test_paired_ic_pass_does_not_imply_paired_economic_pass():
    paired_ic = [
        {"ic_n": 360, "ic_increment_mean": 0.001, "ic_increment_hac_t": 2.0},
        {"ic_n": 360, "ic_increment_mean": 0.002, "ic_increment_hac_t": 2.1},
    ]
    paired_economic = [
        {"excess8_n": 360, "excess8_increment_mean": 0.001, "excess8_increment_hac_t": 2.0},
        {"excess8_n": 360, "excess8_increment_mean": -0.001, "excess8_increment_hac_t": 3.0},
    ]
    result = evidence_layers(
        _row(), SCREENS, 96, paired_ic=paired_ic, paired_economic=paired_economic
    )
    assert result["paired_ic_supported"] is True
    assert result["paired_economic_supported"] is False
