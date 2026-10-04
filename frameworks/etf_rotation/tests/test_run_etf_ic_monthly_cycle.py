"""Synthetic-only tests for the idempotent monthly-factory cycle wrapper's
freeze/evaluate/NOOP branches and its no-backdating rule. Loads the script by
file path (it is not an installed package module), same pattern as
test_etf_all_daily_engine.py's downloader test.
"""
from __future__ import annotations

from dataclasses import asdict
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def _load_cycle_module():
    entry = Path(__file__).parents[1] / "scripts/research/run_etf_ic_monthly_cycle.py"
    spec = importlib.util.spec_from_file_location("etf_ic_monthly_cycle_under_test", entry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cycle = _load_cycle_module()


def _contract(**overrides):
    base = {
        "process_version": "test_cycle_v1",
        "project": "etf_rotation_fixed14_eight_groups",
        "candidate_catalog": ["a_5", "b_5"],
        "training_window_sessions": 60,
        "max_selected": 1,
        "selection": {"min_mean_ic": 0.01, "min_hac_t": 2.0, "hac_lag": 5},
        "first_freeze_month": "2025-11",
        "freeze_requires_month_closed": True,
        "halt_window_diagnostic": {"status": "REPORT_ONLY_REQUIRED"},
    }
    base.update(overrides)
    return base


def _inputs(start="2025-08-01", periods=260):
    dates = pd.bdate_range(start, periods=periods)
    wave = np.sin(np.arange(len(dates)) / 7) * 0.01
    ic = pd.DataFrame({"a_5": 0.05 + wave, "b_5": -0.03 + wave}, index=dates)
    entry = pd.Series(pd.NaT, index=dates, dtype="datetime64[ns]")
    exit_ = entry.copy()
    for i in range(len(dates) - 7):
        entry.iloc[i] = dates[i + 2]
        exit_.iloc[i] = dates[i + 7]
    labels = pd.DataFrame({"entry_date": entry, "exit_date": exit_}, index=dates)
    return ic, labels


def _halt_minute(tmp_path):
    # No halted dates: 09:31-10:30 has nonzero volume every day used below.
    rows = [{"datetime": pd.Timestamp("2025-08-04 09:31"), "volume": 1.0, "ts_code": "513100.SH"}]
    path = tmp_path / "halt.parquet"
    pd.DataFrame(rows).to_parquet(path)
    return path


def test_find_freeze_candidate_requires_closed_month(monkeypatch, tmp_path):
    monkeypatch.setattr(cycle, "FREEZES_ROOT", tmp_path / "freezes")
    contract = _contract(first_freeze_month="2025-11")

    # Mid-November: the target month itself has not closed yet -- no backdating.
    target, reason = cycle.find_freeze_candidate(contract, pd.Timestamp("2025-11-15"))
    assert target is None
    assert "no closed month" in reason

    # The day November closes: eligible.
    target, reason = cycle.find_freeze_candidate(contract, pd.Timestamp("2025-11-30"))
    assert target == "2025-11"


def test_find_freeze_candidate_catches_up_one_month_at_a_time(monkeypatch, tmp_path):
    freezes_root = tmp_path / "freezes"
    monkeypatch.setattr(cycle, "FREEZES_ROOT", freezes_root)
    (freezes_root / "2025-11").mkdir(parents=True)
    (freezes_root / "2025-11" / "freeze.json").write_text("{}")
    contract = _contract(first_freeze_month="2025-11")

    # Both November and December are closed; November is already frozen, so
    # the next candidate is December, not (silently) skipping ahead.
    target, reason = cycle.find_freeze_candidate(contract, pd.Timestamp("2026-01-05"))
    assert target == "2025-12"


def test_find_freeze_candidate_none_when_everything_up_to_date(monkeypatch, tmp_path):
    freezes_root = tmp_path / "freezes"
    monkeypatch.setattr(cycle, "FREEZES_ROOT", freezes_root)
    (freezes_root / "2025-11").mkdir(parents=True)
    (freezes_root / "2025-11" / "freeze.json").write_text("{}")
    contract = _contract(first_freeze_month="2025-11")
    target, reason = cycle.find_freeze_candidate(contract, pd.Timestamp("2025-12-15"))
    assert target is None
    assert "pending" in reason


def test_do_freeze_then_find_and_do_evaluate_end_to_end(monkeypatch, tmp_path):
    freezes_root = tmp_path / "freezes"
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(cycle, "FREEZES_ROOT", freezes_root)
    monkeypatch.setattr(cycle, "LEDGER_PATH", ledger_path)
    monkeypatch.setattr(cycle, "HALT_MINUTE_PATH", _halt_minute(tmp_path))

    contract = _contract(first_freeze_month="2025-11")
    digest = "test-digest"
    ic, labels = _inputs()

    as_of_freeze = pd.Timestamp("2025-11-30")
    frozen_dict = cycle.do_freeze(contract, digest, "2025-11", ic, labels, as_of_freeze)
    assert frozen_dict["evaluation_month"] == "2025-12"
    assert (freezes_root / "2025-11" / "freeze.json").exists()
    assert (freezes_root / "2025-11" / "selection.csv").exists()

    # Evaluation month labels not yet matured: nothing ready.
    ready = cycle.find_evaluate_candidates(contract, digest, labels, pd.Timestamp("2025-12-05"))
    assert ready == []

    # After every December signal's D+7 exit has passed: ready.
    as_of_eval = labels.loc[
        (labels.index >= pd.Period("2025-12", freq="M").start_time)
        & (labels.index <= pd.Period("2025-12", freq="M").end_time),
        "exit_date",
    ].max()
    ready = cycle.find_evaluate_candidates(contract, digest, labels, as_of_eval)
    assert len(ready) == 1
    frozen_obj, _dir = ready[0]
    assert frozen_obj.freeze_month == "2025-11"

    record = cycle.do_evaluate(frozen_obj, ic, labels, ic.abs(), as_of_eval, hac_lag=5)
    assert record["status"] == "EVALUATED"
    ledger_rows = json.loads(ledger_path.read_text().splitlines()[0])
    assert ledger_rows["freeze_month"] == "2025-11"

    # Idempotent: the same month must not be offered again once ledgered.
    ready_again = cycle.find_evaluate_candidates(contract, digest, labels, as_of_eval)
    assert ready_again == []


def test_find_evaluate_rejects_partial_month_and_middle_nat(monkeypatch, tmp_path):
    freezes_root = tmp_path / "freezes"
    monkeypatch.setattr(cycle, "FREEZES_ROOT", freezes_root)
    monkeypatch.setattr(cycle, "LEDGER_PATH", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(cycle, "HALT_MINUTE_PATH", _halt_minute(tmp_path))
    contract = _contract(first_freeze_month="2025-11")
    ic, labels = _inputs()
    cycle.do_freeze(contract, "d1", "2025-11", ic, labels, pd.Timestamp("2025-11-30"))

    dec = labels.index[(labels.index >= "2025-12-01") & (labels.index <= "2025-12-31")]
    # Exits may all be mature before the calendar month has closed; that is
    # still only a partial month and cannot be entered in the forward ledger.
    assert cycle.find_evaluate_candidates(contract, "d1", labels, pd.Timestamp("2025-12-30")) == []

    # A NaT in the middle must not be ignored by Series.max() after month end.
    labels.loc[dec[len(dec) // 2], "exit_date"] = pd.NaT
    as_of = labels.loc[dec, "exit_date"].dropna().max() + pd.Timedelta(days=20)
    assert cycle.find_evaluate_candidates(contract, "d1", labels, as_of) == []


def test_do_freeze_refuses_to_overwrite_existing_freeze_dir(monkeypatch, tmp_path):
    freezes_root = tmp_path / "freezes"
    monkeypatch.setattr(cycle, "FREEZES_ROOT", freezes_root)
    monkeypatch.setattr(cycle, "HALT_MINUTE_PATH", _halt_minute(tmp_path))
    contract = _contract(first_freeze_month="2025-11")
    ic, labels = _inputs()
    as_of_freeze = pd.Timestamp("2025-11-30")
    cycle.do_freeze(contract, "d1", "2025-11", ic, labels, as_of_freeze)
    with pytest.raises(FileExistsError):
        cycle.do_freeze(contract, "d1", "2025-11", ic, labels, as_of_freeze)


def test_find_freeze_candidate_rejects_contract_without_month_closed_rule():
    contract = _contract()
    del contract["freeze_requires_month_closed"]
    with pytest.raises(ValueError, match="freeze_requires_month_closed"):
        cycle.find_freeze_candidate(contract, pd.Timestamp("2026-01-01"))
