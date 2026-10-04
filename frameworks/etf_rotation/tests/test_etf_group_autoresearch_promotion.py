"""A frozen experimental candidate enters the original discovery contract."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/research"))
from prepare_etf_autoresearch_promotion import build_config
from discover_etf_groups import definition_keys
from build_ic_inventory import classify, descriptive_classification, planned_definitions, registration_index
from etf_strategy.core import etf_group_autoresearch as adapter
from etf_strategy.core import etf_group_run_rules as rules


def sample_result(digest: str) -> dict:
    return {"candidate": "autoresearch_example_20", "family": "example",
            "direction": 1, "description": "two-day adjusted-close trend",
            "status": "SEEN_HISTORY_DISCOVERY_ONLY", "cold_cutoff": "2026-03-24",
            "candidate_sha256": digest}


def test_frozen_candidate_uses_original_candidate_id_and_hash(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    relative = adapter.FROZEN / "autoresearch_example_20_abcd.py"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text("CANDIDATE_ID='autoresearch_example_20'\nDIRECTION=1\n"
                    "def score(panels):\n    return panels['close'].pct_change(2, fill_method=None)\n")
    digest = sha256(path.read_bytes()).hexdigest()
    config = build_config(sample_result(digest), str(relative), 554)
    assert rules.candidate_ids(config) == ["autoresearch_example_20"]
    assert config["evidence_policy"] == "SEEN_2026_ADAPTIVE_NOT_CONFIRMATION"
    dates = pd.bdate_range("2025-01-01", periods=8)
    close = pd.DataFrame({"a": np.arange(1, 9, dtype=float)}, index=dates)
    atoms = adapter.build_atoms({"close": close}, config)
    assert list(atoms) == ["autoresearch_example_20"]
    assert adapter.leakage_checks({"close": close}, config, dates[5])
    plan = {"config": config, "source_hashes": {str(path): digest}}
    assert len(definition_keys(plan)) == 1
    plan["candidate_ids"] = rules.candidate_ids(config)
    runs = tmp_path / "runs"
    one = runs / "one"
    one.mkdir(parents=True)
    (one / "PLAN.json").write_text(json.dumps(plan))
    definitions = planned_definitions(runs)
    registrations = registration_index(runs, [])
    assert [row["candidate"] for row in definitions.values()] == ["autoresearch_example_20"]
    assert [row["candidate"] for row in registrations] == ["autoresearch_example_20"]
    path.write_text(path.read_text() + "# tampered\n")
    with pytest.raises(ValueError, match="hash changed"):
        adapter.build_atoms({"close": close}, config)


def test_adaptive_policy_cannot_silently_become_prior_direction() -> None:
    config = build_config(sample_result("a" * 64),
                          str(adapter.FROZEN / "autoresearch_example_20_aaaaaaaaaaaa.py"), 554)
    config["evidence_policy"] = "PRIOR_DIRECTION_FULL_WINDOW"
    with pytest.raises(ValueError, match="adaptive evidence"):
        rules.validate_ic_discovery_config(config)


def test_inventory_shows_adaptive_ic_without_claiming_confirmation() -> None:
    row = {"evidence_policy": "SEEN_2026_ADAPTIVE_NOT_CONFIRMATION",
           "data_quality_status": "CLEAN_FOR_CURRENT_REJUDGE",
           "source_label_artifact_matches": True,
           "full_n": 287, "full_ic_mean": 0.08, "_screens_version": "cold_250_v1"}
    assert classify(row) == ("PENDING", "ADAPTIVE_HISTORY_NOT_BASIC_IC_CONFIRMATION")
    assert descriptive_classification(row) == ("POSITIVE_IC", "COVERAGE_SUFFICIENT")
