"""Synthetic-only tests for the ETF monthly factor-process ledger."""
import json

import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_ic_monthly_factory import (
    append_ledger,
    candidate_halt_window_mask,
    candidate_lookback,
    evaluate_next_month,
    freeze_month,
    load_contract,
    open_halt_dates,
    read_version,
    verify_contract_files,
)


def _contract():
    return {
        "process_version": "test_v1",
        "candidate_catalog": ["a", "b"],
        "training_window_sessions": 120,
        "max_selected": 1,
        "selection": {"min_mean_ic": 0.01, "min_hac_t": 2.0, "hac_lag": 5},
    }


def _inputs():
    dates = pd.bdate_range("2025-01-02", "2026-02-20")
    wave = np.sin(np.arange(len(dates)) / 7) * 0.01
    ic = pd.DataFrame({"a": 0.05 + wave, "b": -0.03 + wave}, index=dates)
    positions = np.arange(len(dates))
    entry = pd.Series(pd.NaT, index=dates, dtype="datetime64[ns]")
    exit_ = entry.copy()
    for i in range(len(dates) - 7):
        entry.iloc[i] = dates[i + 2]
        exit_.iloc[i] = dates[i + 7]
    labels = pd.DataFrame({"entry_date": entry, "exit_date": exit_}, index=dates)
    return ic, labels


def test_freeze_uses_only_matured_training_labels_and_next_month():
    ic, labels = _inputs()
    frozen, table = freeze_month(_contract(), "abc", ic, labels, "2025-12")
    assert frozen.evaluation_month == "2026-01"
    assert frozen.selected_candidates == ("a",)
    assert table.loc[table.candidate.eq("a"), "train_n"].item() == 120
    record = evaluate_next_month(
        frozen, ic, labels, as_of="2026-02-15", turnover=ic.abs()
    )
    assert record["status"] == "EVALUATED"
    assert record["ic_mean"] > 0
    assert record["mean_turnover"] is not None
    assert record["cost_gate_applied"] is False


def test_evaluation_refuses_unmatured_next_month_labels():
    ic, labels = _inputs()
    frozen, _ = freeze_month(_contract(), "abc", ic, labels, "2025-12")
    with pytest.raises(ValueError, match="calendar month has not closed"):
        evaluate_next_month(frozen, ic, labels, as_of="2026-01-15")


def test_evaluation_requires_closed_month_and_every_exit_date():
    ic, labels = _inputs()
    frozen, _ = freeze_month(_contract(), "abc", ic, labels, "2025-12")
    # The latest non-null exit is already past, but a middle-of-month NaT
    # must not disappear from max() and make the month look mature.
    eval_dates = labels.index[(labels.index >= "2026-01-01") & (labels.index <= "2026-01-31")]
    labels.loc[eval_dates[len(eval_dates) // 2], "exit_date"] = pd.NaT
    with pytest.raises(ValueError, match="not all matured"):
        evaluate_next_month(frozen, ic, labels, as_of="2026-02-28")


def test_evaluation_requires_calendar_month_end_even_when_current_rows_mature():
    ic, labels = _inputs()
    frozen, _ = freeze_month(_contract(), "abc", ic, labels, "2025-12")
    with pytest.raises(ValueError, match="not all matured"):
        evaluate_next_month(frozen, ic, labels, as_of="2026-01-31")


def test_evaluation_succeeds_after_full_month_and_all_labels_mature():
    ic, labels = _inputs()
    frozen, _ = freeze_month(_contract(), "abc", ic, labels, "2025-12")
    record = evaluate_next_month(frozen, ic, labels, as_of="2026-02-20")
    assert record["status"] == "EVALUATED"
    assert record["ic_n"] > 0


def test_evaluation_rejects_daily_ic_truncated_before_late_month_dates():
    ic, labels = _inputs()
    frozen, _ = freeze_month(_contract(), "abc", ic, labels, "2025-12")
    # A silent index intersection would drop the late January signals and
    # could let the remaining, already-mature labels settle as a full month.
    truncated = ic.drop(ic.index[(ic.index >= "2026-01-26") & (ic.index <= "2026-01-31")])
    with pytest.raises(ValueError, match="same signal dates"):
        evaluate_next_month(frozen, truncated, labels, as_of="2026-02-20")


def test_ledger_rejects_duplicate_key_and_never_merges_versions(tmp_path):
    path = tmp_path / "ledger.jsonl"
    row = {
        "process_version": "v1", "contract_sha256": "h1",
        "freeze_month": "2025-12", "evaluation_month": "2026-01",
    }
    append_ledger(path, row)
    with pytest.raises(ValueError, match="already exists"):
        append_ledger(path, row)
    append_ledger(path, {**row, "process_version": "v2", "contract_sha256": "h2"})
    assert read_version(path, "v1", "h1") == [row]


def test_repository_contract_is_etf_only_and_hash_bound():
    path = "frameworks/etf_rotation/configs/etf_ic_monthly_factory_v3.yaml"
    cfg, digest = load_contract(path)
    assert len(digest) == 64
    verify_contract_files(cfg, ".")
    assert cfg["project"] == "etf_rotation_fixed14_eight_groups"
    assert cfg["cost_policy"] == "record_turnover_only_not_a_factor_gate"
    assert len(cfg["candidate_catalog"]) == 20
    assert "d2025_minute_amount_abs_return_concentration_20" in cfg["candidate_catalog"]
    assert "reverse_minute_late_return_5" in cfg["candidate_catalog"]
    assert cfg["halt_window_diagnostic"]["never_a_selection_gate"] is True


def test_halt_window_diagnostic_uses_each_candidate_lookback_and_never_changes_gate():
    dates = pd.bdate_range("2025-01-02", periods=130)
    minute_dates = [dates[3], dates[50]]
    rows = []
    for date in minute_dates:
        for stamp in pd.date_range(date + pd.Timedelta(hours=9, minutes=31), periods=60, freq="min"):
            rows.append({"datetime": stamp, "volume": 0.0})
    halted = open_halt_dates(pd.DataFrame(rows))
    assert halted.equals(pd.DatetimeIndex(minute_dates))
    mask = candidate_halt_window_mask(dates, ["factor_5", "factor_20"], halted)
    assert candidate_lookback("factor_20") == 20
    assert int(mask["factor_5"].sum()) == 10
    assert int(mask["factor_20"].sum()) == 40

    contract = {**_contract(), "halt_window_diagnostic": {"status": "REPORT_ONLY_REQUIRED"}}
    ic, labels = _inputs()
    halt_mask = candidate_halt_window_mask(ic.index, ["a_5", "b_20"], pd.DatetimeIndex([]))
    contract["candidate_catalog"] = ["a_5", "b_20"]
    renamed = ic.rename(columns={"a": "a_5", "b": "b_20"})
    frozen, table = freeze_month(
        contract, "abc", renamed, labels, "2025-12", halt_window_mask=halt_mask
    )
    assert frozen.selected_candidates == ("a_5",)
    assert table["halt_window_diagnostic_only"].all()
    assert (table["halt_window_excluded_n"] == 0).all()


def test_monthly_v3_requires_report_only_halt_diagnostic():
    contract = {**_contract(), "halt_window_diagnostic": {"status": "REPORT_ONLY_REQUIRED"}}
    ic, labels = _inputs()
    with pytest.raises(ValueError, match="requires the report-only"):
        freeze_month(contract, "abc", ic, labels, "2025-12")


def test_monthly_process_cannot_be_backdated_or_frozen_before_month_end():
    ic, labels = _inputs()
    contract = {
        **_contract(),
        "first_freeze_month": "2025-12",
        "freeze_requires_month_closed": True,
    }
    with pytest.raises(ValueError, match="backdated"):
        freeze_month(contract, "abc", ic, labels, "2025-11", as_of="2025-12-01")
    with pytest.raises(ValueError, match="month has closed"):
        freeze_month(contract, "abc", ic, labels, "2025-12", as_of="2025-12-30")
    frozen, _ = freeze_month(contract, "abc", ic, labels, "2025-12", as_of="2025-12-31")
    assert frozen.freeze_month == "2025-12"
