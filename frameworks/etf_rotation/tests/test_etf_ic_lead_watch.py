"""Maturity and append-only boundaries for the observation-only IC sidecar."""
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/run_etf_ic_lead_watch.py"
spec = importlib.util.spec_from_file_location("run_etf_ic_lead_watch", SCRIPT)
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


def test_month_waits_for_all_labels_then_records_all_frozen_candidates():
    calendar = pd.bdate_range("2026-10-01", "2026-10-30")
    daily_ic = pd.DataFrame({"a": 0.1, "b": -0.1}, index=calendar)
    dates = pd.DataFrame({
        "entry_date": calendar + pd.offsets.BDay(2),
        "exit_date": calendar + pd.offsets.BDay(7),
    }, index=calendar)
    config = {"version": "test_v1", "first_month": "2026-10", "candidate_catalog": ["a", "b"]}
    assert watch.monthly_rows(config, daily_ic, dates, "2026-10", "2026-11-02") is None
    rows = watch.monthly_rows(config, daily_ic, dates, "2026-10", "2026-11-12")
    assert [row["candidate"] for row in rows] == ["a", "b"]
    assert [row["n"] for row in rows] == [len(calendar)] * 2
    assert rows[0]["ic"] > 0 and rows[1]["ic"] < 0


def test_append_once_rejects_contract_rewrite(tmp_path):
    ledger = tmp_path / "watch.jsonl"
    row = {"version": "v1", "month": "2026-10", "candidate": "a",
           "config_sha256": "one", "parent_contract_sha256": "parent"}
    assert watch.append_once(ledger, [row])
    assert not watch.append_once(ledger, [row])
    with pytest.raises(ValueError, match="different contract hash"):
        watch.append_once(ledger, [{**row, "config_sha256": "two"}])
    assert len([json.loads(x) for x in ledger.read_text().splitlines()]) == 1
