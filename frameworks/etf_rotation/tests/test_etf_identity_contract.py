"""Contract tests for date-matched leave-one-symbol-out identity diagnostics.

All fixtures are synthetic and constructed in-process; no market data is read.

The panel below is built so that *no symbol carries any signal*: every wide day
is a perfect cross-sectional reversal and every thin day a perfect alignment.
Any difference between exclusions can therefore only come from which days each
exclusion was able to score - exactly the time-selection artefact the matched
API exists to remove.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_identity import (
    MATCHED_LOSO_COLUMNS,
    identity_gate,
    leave_one_symbol_out,
    matched_leave_one_symbol_out,
)

SYMBOLS = list("ABCDE")
MIN_PAIRS = 4

WIDE_SIGNAL = [1.0, 2.0, 3.0, 4.0, 5.0]
WIDE_NEGATIVE_RETURN = [5.0, 4.0, 3.0, 2.0, 1.0]
WIDE_POSITIVE_RETURN = [1.0, 2.0, 3.0, 4.0, 5.0]
THIN_SIGNAL = [1.0, 2.0, 3.0, 4.0, np.nan]
THIN_POSITIVE_RETURN = [1.0, 2.0, 3.0, 4.0, 9.0]

# day: 0-3 wide/IC=-1, 4-5 thin/IC=+1, 6 wide/IC=+1 (purged), 7-8 wide/IC=-1,
# 9 thin/IC=+1
_LAYOUT = [
    ("wide", WIDE_NEGATIVE_RETURN),
    ("wide", WIDE_NEGATIVE_RETURN),
    ("wide", WIDE_NEGATIVE_RETURN),
    ("wide", WIDE_NEGATIVE_RETURN),
    ("thin", THIN_POSITIVE_RETURN),
    ("thin", THIN_POSITIVE_RETURN),
    ("wide", WIDE_POSITIVE_RETURN),
    ("wide", WIDE_NEGATIVE_RETURN),
    ("wide", WIDE_NEGATIVE_RETURN),
    ("thin", THIN_POSITIVE_RETURN),
]


@pytest.fixture()
def panel() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    dates = pd.date_range("2024-01-01", periods=len(_LAYOUT), freq="D")
    signal = pd.DataFrame(
        [WIDE_SIGNAL if kind == "wide" else THIN_SIGNAL for kind, _ in _LAYOUT],
        index=dates,
        columns=SYMBOLS,
    )
    forward = pd.DataFrame(
        [returns for _, returns in _LAYOUT], index=dates, columns=SYMBOLS
    )
    eligibility = pd.DataFrame(True, index=dates, columns=SYMBOLS)
    discovery_mask = pd.Series(False, index=dates)
    discovery_mask.iloc[0:6] = True
    audit_mask = pd.Series(False, index=dates)
    audit_mask.iloc[7:10] = True
    return signal, forward, eligibility, discovery_mask, audit_mask


def _matched(panel, **overrides):
    signal, forward, eligibility, discovery_mask, audit_mask = panel
    kwargs = {
        "min_pairs": MIN_PAIRS,
        "discovery_mask": discovery_mask,
        "audit_mask": audit_mask,
    }
    kwargs.update(overrides)
    return matched_leave_one_symbol_out(signal, forward, eligibility, **kwargs)


def test_returned_tables_carry_the_documented_columns(panel) -> None:
    shared, paired = _matched(panel)
    assert list(shared.columns) == list(MATCHED_LOSO_COLUMNS)
    assert list(paired.columns) == list(MATCHED_LOSO_COLUMNS)
    assert sorted(shared["excluded_symbol"]) == SYMBOLS
    assert sorted(paired["excluded_symbol"]) == SYMBOLS


def test_naive_full_mask_comparison_is_time_selection_biased(panel) -> None:
    """The legacy table scores each exclusion on its own calendar.

    Excluding ``E`` keeps the thin days (E is already missing there, so the pair
    count stays at ``min_pairs``); excluding ``A`` loses them. The legacy means
    therefore disagree even though the panel contains no symbol-specific effect
    at all - a naive read would call ``A`` the fragile symbol.
    """
    signal, forward, eligibility, _, _ = panel
    legacy = leave_one_symbol_out(
        signal,
        forward,
        eligibility,
        min_pairs=MIN_PAIRS,
        discovery_end=signal.index[6],
        audit_start=signal.index[7],
        audit_end=signal.index[9],
    ).set_index("excluded_symbol")

    assert legacy.loc["E", "discovery_days"] == 7
    assert legacy.loc["A", "discovery_days"] == 5
    assert legacy.loc["E", "discovery_ic"] == pytest.approx(-1.0 / 7.0)
    assert legacy.loc["A", "discovery_ic"] == pytest.approx(-0.6)
    assert legacy.loc["E", "discovery_ic"] != pytest.approx(
        legacy.loc["A", "discovery_ic"]
    )

    shared, _ = _matched(panel)
    shared = shared.set_index("excluded_symbol")
    assert shared["discovery_ic"].nunique() == 1
    assert shared.loc["E", "discovery_ic"] == pytest.approx(-1.0)
    assert shared.loc["A", "discovery_ic"] == pytest.approx(-1.0)


def test_shared_check_dates_are_identical_across_exclusions(panel) -> None:
    shared, _ = _matched(panel)
    assert shared["discovery_days"].nunique() == 1
    assert shared["audit_days"].nunique() == 1
    # Thin days (4, 5) fall below min_pairs once any of A-D is removed, so the
    # shared discovery calendar is the four wide discovery days; day 6 is purged.
    assert int(shared["discovery_days"].iloc[0]) == 4
    assert int(shared["audit_days"].iloc[0]) == 2


def test_min_pairs_is_never_reduced_to_rescue_a_date(panel) -> None:
    shared, _ = _matched(panel)
    shared = shared.set_index("excluded_symbol")
    # E's own finite discovery days are 0-5; two of them are outside the shared
    # calendar because the A-D exclusions could not score them at min_pairs=4.
    assert int(shared.loc["E", "discovery_dates_dropped"]) == 2
    assert int(shared.loc["A", "discovery_dates_dropped"]) == 0
    assert int(shared.loc["E", "audit_dates_dropped"]) == 1
    # Every scored day used exactly four ranked names, never three.
    assert shared["discovery_symbol_pairs"].eq(4.0).all()
    assert shared["audit_symbol_pairs"].eq(4.0).all()


def test_baseline_is_averaged_over_the_same_dates_as_the_row(panel) -> None:
    shared, paired = _matched(panel)
    shared = shared.set_index("excluded_symbol")
    paired = paired.set_index("excluded_symbol")

    assert shared["baseline_discovery_ic"].eq(-1.0).all()
    assert shared["discovery_delta"].abs().max() == pytest.approx(0.0)
    assert shared["audit_delta"].abs().max() == pytest.approx(0.0)

    # The paired table keeps more days per row, so its rows are NOT comparable
    # with one another - but each row's baseline still matches its own calendar,
    # so every delta remains zero.
    assert int(paired.loc["E", "discovery_days"]) == 6
    assert int(paired.loc["A", "discovery_days"]) == 4
    assert paired.loc["E", "discovery_ic"] == pytest.approx(-1.0 / 3.0)
    assert paired.loc["E", "baseline_discovery_ic"] == pytest.approx(-1.0 / 3.0)
    assert paired["discovery_delta"].abs().max() == pytest.approx(0.0)
    assert paired["audit_delta"].abs().max() == pytest.approx(0.0)


def test_masks_are_honored_and_purged_days_stay_out(panel) -> None:
    signal, forward, eligibility, discovery_mask, audit_mask = panel
    # Day 6 is a wide day with IC = +1. It sits between the two masks.
    leaked = discovery_mask.copy()
    leaked.iloc[6] = True
    shared_purged, _ = _matched(panel)
    shared_leaked, _ = _matched(panel, discovery_mask=leaked)

    assert shared_purged["discovery_ic"].eq(-1.0).all()
    assert int(shared_leaked["discovery_days"].iloc[0]) == 5
    assert shared_leaked["discovery_ic"].iloc[0] == pytest.approx(-0.6)


def test_mask_outside_the_panel_index_selects_nothing(panel) -> None:
    signal, forward, eligibility, _, audit_mask = panel
    foreign = pd.Series(True, index=pd.date_range("2030-01-01", periods=3, freq="D"))
    shared, paired = _matched(panel, discovery_mask=foreign)
    assert shared["discovery_days"].eq(0).all()
    assert shared["discovery_ic"].isna().all()
    assert paired["discovery_days"].eq(0).all()


def test_group_without_common_dates_reports_nan_and_zero_never_a_pass(panel) -> None:
    signal, forward, eligibility, discovery_mask, audit_mask = panel
    # Restrict discovery to the thin days only: A-D exclusions fall below
    # min_pairs there, so no date survives the shared intersection.
    thin_only = pd.Series(False, index=signal.index)
    thin_only.iloc[4:6] = True
    shared, _ = _matched(panel, discovery_mask=thin_only)

    assert shared["discovery_days"].eq(0).all()
    assert shared["discovery_ic"].isna().all()
    assert shared["baseline_discovery_ic"].isna().all()
    assert shared["discovery_delta"].isna().all()
    assert shared["discovery_symbol_pairs"].isna().all()
    assert not identity_gate(shared, direction=-1.0, min_audit_ic=0.0)


def test_empty_panel_returns_empty_tables_with_columns() -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    empty = pd.DataFrame(index=dates)
    mask = pd.Series(True, index=dates)
    shared, paired = matched_leave_one_symbol_out(
        empty, empty, empty, min_pairs=4, discovery_mask=mask, audit_mask=mask
    )
    assert shared.empty and paired.empty
    assert list(shared.columns) == list(MATCHED_LOSO_COLUMNS)
    assert not identity_gate(shared, direction=1.0, min_audit_ic=0.0)


def test_legacy_leave_one_symbol_out_signature_is_unchanged(panel) -> None:
    signal, forward, eligibility, _, _ = panel
    legacy = leave_one_symbol_out(
        signal,
        forward,
        eligibility,
        min_pairs=MIN_PAIRS,
        discovery_end=signal.index[5],
        audit_start=signal.index[7],
        audit_end=signal.index[9],
    )
    assert list(legacy.columns) == [
        "excluded_symbol",
        "discovery_days",
        "discovery_ic",
        "seen_audit_ic",
    ]
    assert len(legacy) == len(SYMBOLS)


def test_identity_gate_behavior_is_backwards_compatible() -> None:
    table = pd.DataFrame(
        {"discovery_ic": [-0.05, -0.04], "seen_audit_ic": [-0.02, -0.001]}
    )
    assert not identity_gate(table, direction=-1.0, min_audit_ic=0.01)
    passing = pd.DataFrame(
        {"discovery_ic": [-0.05, -0.04], "seen_audit_ic": [-0.02, -0.03]}
    )
    assert identity_gate(passing, direction=-1.0, min_audit_ic=0.01)


def test_matched_shared_table_is_accepted_by_identity_gate(panel) -> None:
    shared, _ = _matched(panel)
    assert identity_gate(shared, direction=-1.0, min_audit_ic=0.5)
    assert not identity_gate(shared, direction=1.0, min_audit_ic=0.5)
