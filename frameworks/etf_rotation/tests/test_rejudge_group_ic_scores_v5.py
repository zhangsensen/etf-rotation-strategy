import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/research/rejudge_group_ic_scores_v5.py"
)
SPEC = importlib.util.spec_from_file_location("rejudge_group_ic_scores_v5", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_reviewed_source_quality_states_keep_halt_as_diagnostic_only():
    assert MODULE.data_quality_status("share", "share_redemption_40") == (
        "DEGRADED_513100_SHARE_STAGNATION"
    )
    assert MODULE.data_quality_status("nav", "nav_basis_change_5") == (
        "DATA_QUALITY_PENDING_NAV_OUTLIERS"
    )
    assert MODULE.data_quality_status(
        "minute", "d2025_minute_amount_abs_return_concentration_20"
    ) == "HALT_DIAGNOSTIC_REPORTED"
    assert MODULE.data_quality_status("minute", "reverse_minute_late_return_5") == (
        "CLEAN_FOR_CURRENT_REJUDGE"
    )


def test_rejudge_default_budget_is_current_384():
    source = SCRIPT.read_text()
    assert 'default=384' in source
    assert '2025_DIRECTION_2026_HISTORICAL_SEGMENT' in source
