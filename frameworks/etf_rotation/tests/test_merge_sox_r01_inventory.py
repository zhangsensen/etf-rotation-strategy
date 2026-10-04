"""Synthetic checks for the local SOX round-1 inventory append."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/merge_sox_r01_inventory.py"
SPEC = importlib.util.spec_from_file_location("merge_sox_r01_inventory", SCRIPT)
assert SPEC and SPEC.loader
merge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(merge)


def _inputs():
    names = ["one", "two", "three"]
    cfg = {"candidates": [{"name": name} for name in names]}
    old = pd.DataFrame({"definition_id": ["old"], "candidate": ["old"]})
    current = pd.DataFrame({"candidate": names, "n": [287] * 3,
                            "ic_mean": [0.04, 0.01, 0.0],
                            "ic_hac_t": [1.7, 0.7, 0.0],
                            "ic_block_t": [1.5, 0.7, 0.0],
                            "ic_blocks": [58] * 3,
                            "ic_p_normal_one_sided": [0.04, 0.24, 0.5],
                            "min_leave_group_ic": [0.01] * 3,
                            "historical_2026_min_leave_group_ic": [-0.01] * 3,
                            "historical_ic_supported": [False] * 3,
                            "historical_2026_metrics_pass": [False] * 3,
                            "factor_evidence_supported": [False] * 3,
                            "ic_budget_supported": [False] * 3})
    annual = pd.DataFrame([{"candidate": name, "year": year,
                            "n": 236 if year == 2025 else 44,
                            "ic_mean": 0.01, "ic_hac_t": 0.1,
                            "ic_block_t": 0.1, "ic_blocks": 9,
                            "ic_p_normal_one_sided": 0.46}
                           for name in names for year in (2025, 2026)])
    return old, current, annual, cfg


def test_append_keeps_all_three_and_prior_row(monkeypatch):
    old, current, annual, cfg = _inputs()
    monkeypatch.setattr(merge.rules, "candidate_ids", lambda _: ["one", "two", "three"])
    monkeypatch.setattr(merge, "semantic_id", lambda _, name: f"new_{name}")
    merged = merge.append_rows(old, current, annual, cfg)
    assert len(merged) == 4
    assert merged.definition_id.tolist() == ["old", "new_one", "new_two", "new_three"]
    assert merged.candidate.tolist() == ["old", "one", "two", "three"]


def test_append_rejects_missing_candidate_or_year(monkeypatch):
    old, current, annual, cfg = _inputs()
    monkeypatch.setattr(merge.rules, "candidate_ids", lambda _: ["one", "two", "three"])
    monkeypatch.setattr(merge, "semantic_id", lambda _, name: f"new_{name}")
    with pytest.raises(ValueError, match="three-candidate"):
        merge.append_rows(old, current.iloc[:2], annual, cfg)
    with pytest.raises(ValueError, match="annual evidence missing"):
        merge.append_rows(old, current, annual[~((annual.candidate == "three") &
                                                  (annual.year == 2026))], cfg)


def test_append_rejects_duplicate_prior_identity(monkeypatch):
    old, current, annual, cfg = _inputs()
    monkeypatch.setattr(merge.rules, "candidate_ids", lambda _: ["one", "two", "three"])
    with pytest.raises(ValueError, match="duplicate semantic IDs"):
        merge.append_rows(pd.concat([old, old], ignore_index=True), current, annual, cfg)
