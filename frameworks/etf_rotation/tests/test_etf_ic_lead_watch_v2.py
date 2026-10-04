"""Observation catalog stays separate from the frozen v4 selection catalog."""
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/run_etf_ic_lead_watch_v2.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("run_etf_ic_lead_watch_v2", SCRIPT)
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


def test_catalog_is_all_saved_leads_and_parent_contract_unchanged():
    cfg = yaml.safe_load(watch.CONFIG.read_text())
    parent = yaml.safe_load((watch.ROOT / cfg["parent_contract"]).read_text())
    assert cfg["version"] == "etf_ic_lead_watch_v2"
    assert cfg["first_month"] == "2026-10"
    assert len(cfg["candidate_catalog"]) == len(set(cfg["candidate_catalog"])) == 16
    assert len(set(cfg["candidate_catalog"]) & set(parent["candidate_catalog"])) == 5


def test_merge_requires_same_calendar_and_label_contract():
    idx = pd.bdate_range("2026-10-01", periods=3)
    dates = pd.DataFrame({"entry_date": idx + pd.offsets.BDay(2),
                          "exit_date": idx + pd.offsets.BDay(7)}, index=idx)
    base = pd.DataFrame({"a": [0.1] * 3}, index=idx)
    extra = {"daily_ic": pd.DataFrame({"b": [-0.1] * 3}, index=idx),
             "label_dates": dates.copy()}
    with pytest.raises(ValueError, match="sixteen"):
        watch.merge_panels(["a", "b"], ["a"], base, dates, extra)
    extra["label_dates"].iloc[0, 0] += pd.Timedelta(days=1)
    with pytest.raises(ValueError, match="label dates"):
        watch.merge_panels(["a", "b"], ["a"], base, dates, extra)


def test_all_leads_record_only_after_last_h5_exit():
    from run_etf_ic_lead_watch import monthly_rows

    config = yaml.safe_load(watch.CONFIG.read_text())
    catalog = config["candidate_catalog"]
    parent = yaml.safe_load((watch.ROOT / config["parent_contract"]).read_text())
    parent_catalog = parent["candidate_catalog"]
    idx = pd.bdate_range("2026-10-01", "2026-10-30")
    dates = pd.DataFrame({"entry_date": idx + pd.offsets.BDay(2),
                          "exit_date": idx + pd.offsets.BDay(7)}, index=idx)
    base = pd.DataFrame({name: 0.1 for name in parent_catalog}, index=idx)
    extra_names = [name for name in catalog if name not in parent_catalog]
    extra = {"daily_ic": pd.DataFrame({name: -0.1 for name in extra_names}, index=idx),
             "label_dates": dates.copy()}
    merged = watch.merge_panels(catalog, parent_catalog, base, dates, extra)
    assert monthly_rows(config, merged, dates, "2026-10", "2026-11-02") is None
    rows = monthly_rows(config, merged, dates, "2026-10", "2026-11-12")
    assert len(rows) == 16
    assert rows[0]["candidate"] == catalog[0]
    assert rows[0]["ic"] > 0
    assert rows[1]["ic"] < 0


def test_uncomputable_share_is_explicit_and_month_appends_once(tmp_path):
    from run_etf_ic_lead_watch import append_once, monthly_rows

    config = yaml.safe_load(watch.CONFIG.read_text())
    catalog = config["candidate_catalog"]
    idx = pd.bdate_range("2026-10-01", "2026-10-30")
    dates = pd.DataFrame({"entry_date": idx + pd.offsets.BDay(2),
                          "exit_date": idx + pd.offsets.BDay(7)}, index=idx)
    wave = np.sin(np.arange(len(idx)) / 2) * 0.01
    daily = pd.DataFrame({name: 0.1 + wave for name in catalog}, index=idx)
    daily["beta_asymmetry_60"] = -0.1 + wave
    daily["range_flow_20_40_1"] = float("nan")
    assert monthly_rows(config, daily, dates, "2026-10", "2026-11-02") is None
    rows = monthly_rows(config, daily, dates, "2026-10", "2026-11-12")
    assert len(rows) == len({row["candidate"] for row in rows}) == 16
    for row in rows:
        source = (watch.UNCOMPUTABLE_SHARE_STATUS if row["candidate"] == "range_flow_20_40_1"
                  else "COMPUTABLE")
        row.update(config_sha256="watch", parent_contract_sha256="v4",
                   source_status=source, ic_status=watch.ic_status(source, row["n"]))
    share = next(row for row in rows if row["candidate"] == "range_flow_20_40_1")
    assert (share["n"], share["ic"], share["hac_t"], share["ic_status"]) == (
        0, None, None, "UNCOMPUTABLE_SOURCE"
    )
    assert next(row for row in rows if row["candidate"] == "beta_asymmetry_60")["ic"] < 0
    assert all(row["n"] == len(idx) and row["hac_t"] is not None
               for row in rows if row["candidate"] != "range_flow_20_40_1")
    ledger = tmp_path / "watch_v2.jsonl"
    assert append_once(ledger, rows)
    assert not append_once(ledger, rows)
    records = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert len(records) == 1
    assert len(records[0]["candidates"]) == 16


def test_uncomputable_source_cannot_report_forward_ic():
    with pytest.raises(ValueError, match="uncomputable share source"):
        watch.ic_status(watch.UNCOMPUTABLE_SHARE_STATUS, 1)
