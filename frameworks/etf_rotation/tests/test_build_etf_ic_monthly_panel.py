"""Synthetic-only tests for the monthly-factory panel builder's layered
reproducibility gate (layer1_check / layer2_check / run_reproducibility_gate)
and the no-panel-on-failure guarantee. Loads the script by file path (it is
not an installed package module), same pattern as
test_etf_all_daily_engine.py's downloader test and
test_run_etf_ic_monthly_cycle.py.

Exercises the gate functions directly against fabricated PLAN.json/scores/
group_labels/coverage artifacts under a monkeypatched RUNS_DIR; never touches
real data/ or runtime_outputs/etf_rotation_research/runs.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def _load_panel_module():
    entry = Path(__file__).parents[1] / "scripts/research/build_etf_ic_monthly_panel.py"
    spec = importlib.util.spec_from_file_location("etf_ic_monthly_panel_under_test", entry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


panel = _load_panel_module()

GROUPS = ["g1", "g2", "g3"]
CANDIDATE = "cand_a"
RUN_ID = "run_a"


def _dates(n=15, start="2025-01-02"):
    return pd.bdate_range(start, periods=n)


def _write_input_file(tmp_path: Path, name: str, content: bytes = b"canonical-input-v1") -> Path:
    path = tmp_path / "data_inputs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _setup_run(
    tmp_path,
    monkeypatch,
    *,
    score: pd.DataFrame,
    group_labels: pd.DataFrame,
    known: pd.Series,
    revise_input: bool = False,
):
    """Fabricate one PLAN.json + scores_<candidate>.csv + group_labels.csv +
    coverage.csv + daily_metrics.csv run directory, and point RUNS_DIR /
    CANDIDATE_SOURCE_RUN at it. Returns the input file's path so a caller can
    mutate it to simulate a post-run data revision.
    """
    runs_dir = tmp_path / "runs"
    monkeypatch.setattr(panel, "RUNS_DIR", runs_dir)
    monkeypatch.setattr(panel, "CANDIDATE_SOURCE_RUN", {CANDIDATE: RUN_ID})

    input_path = _write_input_file(tmp_path, "some_source.parquet")
    input_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()

    run_dir = runs_dir / RUN_ID
    run_dir.mkdir(parents=True)
    plan = {
        "config": {"source_type": "daily_rounds"},
        "input_hashes": {str(input_path): input_hash},
    }
    (run_dir / "PLAN.json").write_text(json.dumps(plan))
    score.to_csv(run_dir / f"scores_{CANDIDATE}.csv")
    group_labels.to_csv(run_dir / "group_labels.csv")
    coverage = pd.DataFrame({
        "signal_date": known.index, "known_complete": known.to_numpy(),
    })
    coverage.to_csv(run_dir / "coverage.csv", index=False)
    # daily_metrics.csv (the stale, report-only column) can be anything with
    # the right shape; layer2 never gates on it.
    stale = pd.DataFrame({
        "candidate": CANDIDATE, "signal_date": known.index, "ic": np.nan,
    })
    stale.to_csv(run_dir / "daily_metrics.csv", index=False)

    if revise_input:
        input_path.write_bytes(b"revised-content-after-run")

    return input_path


def _clean_scenario():
    """A small, fully self-consistent scenario: 3 groups, 15 business days,
    all known, deterministic scores/labels so the reference IC is well
    defined (no ties, no zero-variance rows).
    """
    dates = _dates()
    rng = np.random.default_rng(7)
    score = pd.DataFrame(rng.normal(size=(len(dates), 3)), index=dates, columns=GROUPS)
    group_labels = pd.DataFrame(rng.normal(size=(len(dates), 3)), index=dates, columns=GROUPS)
    known = pd.Series(True, index=dates)
    return dates, score, group_labels, known


def _built_from(dates, score, group_returns, base_known, daily_ic_values):
    daily_ic = pd.DataFrame({CANDIDATE: daily_ic_values}, index=dates)
    return {
        "scores": {CANDIDATE: score.copy()},
        "known": {CANDIDATE: base_known.copy()},
        "group_returns": group_returns.copy(),
        "base_known": base_known.copy(),
        "daily_ic": daily_ic,
    }


# --- layer1 ---------------------------------------------------------------

def test_layer1_passes_when_rebuild_matches_saved_artifacts(tmp_path, monkeypatch):
    dates, score, group_labels, known = _clean_scenario()
    _setup_run(tmp_path, monkeypatch, score=score, group_labels=group_labels, known=known)
    built = _built_from(dates, score, group_labels, known, daily_ic_values=np.nan)

    result = panel.layer1_check(built, [CANDIDATE])
    row = result.iloc[0]
    assert row.status == "OK"
    assert row.n_mismatch_dates == 0
    assert row.input_data_revised_since_run == False  # noqa: E712


def test_layer1_fails_on_unrevised_score_mismatch(tmp_path, monkeypatch):
    dates, score, group_labels, known = _clean_scenario()
    _setup_run(tmp_path, monkeypatch, score=score, group_labels=group_labels, known=known)
    rebuilt_score = score.copy()
    rebuilt_score.iloc[3, 0] += 0.5  # well beyond the rtol=1e-9 gate
    built = _built_from(dates, rebuilt_score, group_labels, known, daily_ic_values=np.nan)

    result = panel.layer1_check(built, [CANDIDATE])
    row = result.iloc[0]
    assert row.status == "LAYER1_FAILED"
    assert row.n_mismatch_dates >= 1
    assert row.input_data_revised_since_run == False  # noqa: E712

    with pytest.raises(ValueError, match="layer1"):
        panel.run_reproducibility_gate(built, [CANDIDATE])


def test_layer1_input_hash_changed_is_revised_not_blocking(tmp_path, monkeypatch):
    dates, score, group_labels, known = _clean_scenario()
    _setup_run(
        tmp_path, monkeypatch, score=score, group_labels=group_labels, known=known,
        revise_input=True,
    )
    rebuilt_score = score.copy()
    rebuilt_score.iloc[3, 0] += 0.5  # a real mismatch, but data was revised since the run
    built = _built_from(dates, rebuilt_score, group_labels, known, daily_ic_values=np.nan)

    result = panel.layer1_check(built, [CANDIDATE])
    row = result.iloc[0]
    assert row.input_data_revised_since_run == True  # noqa: E712
    assert row.n_changed_input_files == 1
    assert row.status == "DATA_REVISED_SINCE_RUN"
    assert row.n_mismatch_dates >= 1  # still reported, just not gating

    # A revised-only candidate must not appear in the raising failure list.
    layer1_failed = result.loc[result.status == "LAYER1_FAILED", "candidate"].tolist()
    assert layer1_failed == []


# --- layer2 -----------------------------------------------------------------

def test_layer2_passes_when_rebuild_matches_reference(tmp_path, monkeypatch):
    dates, score, group_labels, known = _clean_scenario()
    _setup_run(tmp_path, monkeypatch, score=score, group_labels=group_labels, known=known)
    reference = panel._reference_ic(score, group_labels, known)
    built = _built_from(dates, score, group_labels, known, daily_ic_values=reference)

    result = panel.layer2_check(built, [CANDIDATE], revised={CANDIDATE: False})
    row = result.iloc[0]
    assert bool(row["pass"]) is True
    assert row.nan_pattern_mismatch == 0
    assert row.max_abs_diff_vs_reference == 0.0

    layer1, layer2 = panel.run_reproducibility_gate(built, [CANDIDATE])
    assert layer2.iloc[0]["pass"]


def test_layer2_fails_when_reference_valid_but_rebuild_differs_numerically(tmp_path, monkeypatch):
    dates, score, group_labels, known = _clean_scenario()
    _setup_run(tmp_path, monkeypatch, score=score, group_labels=group_labels, known=known)
    reference = panel._reference_ic(score, group_labels, known)
    assert reference.notna().all()  # sanity: this scenario has no NaN reference days
    rebuilt_ic = reference.copy()
    rebuilt_ic.iloc[5] += 0.2  # reference is valid here; rebuild now disagrees
    built = _built_from(dates, score, group_labels, known, daily_ic_values=rebuilt_ic)

    result = panel.layer2_check(built, [CANDIDATE], revised={CANDIDATE: False})
    row = result.iloc[0]
    assert bool(row["pass"]) is False
    assert row.max_abs_diff_vs_reference > 1e-9

    with pytest.raises(ValueError, match="layer2"):
        panel.run_reproducibility_gate(built, [CANDIDATE])


def test_layer2_fails_when_reference_valid_but_rebuild_is_nan(tmp_path, monkeypatch):
    dates, score, group_labels, known = _clean_scenario()
    _setup_run(tmp_path, monkeypatch, score=score, group_labels=group_labels, known=known)
    reference = panel._reference_ic(score, group_labels, known)
    rebuilt_ic = reference.copy()
    rebuilt_ic.iloc[5] = np.nan  # reference valid, rebuild silently missing
    built = _built_from(dates, score, group_labels, known, daily_ic_values=rebuilt_ic)

    result = panel.layer2_check(built, [CANDIDATE], revised={CANDIDATE: False})
    row = result.iloc[0]
    assert bool(row["pass"]) is False
    assert row.nan_pattern_mismatch == 1


def test_layer2_does_not_require_rebuild_where_reference_is_nan(tmp_path, monkeypatch):
    dates, score, group_labels, known = _clean_scenario()
    # Make day index 2 legitimately unknown, so the reference is NaN there
    # (mirrors an immature/incomplete date the source run itself couldn't
    # score), independent of anything the rebuild does.
    known = known.copy()
    known.iloc[2] = False
    _setup_run(tmp_path, monkeypatch, score=score, group_labels=group_labels, known=known)
    reference = panel._reference_ic(score, group_labels, known)
    assert pd.isna(reference.iloc[2])

    rebuilt_ic = reference.copy()
    rebuilt_ic.iloc[2] = 0.42  # rebuild has an opinion where the reference has none
    built = _built_from(dates, score, group_labels, known, daily_ic_values=rebuilt_ic)

    result = panel.layer2_check(built, [CANDIDATE], revised={CANDIDATE: False})
    row = result.iloc[0]
    assert bool(row["pass"]) is True
    assert row.nan_pattern_mismatch == 0


# --- no panel written on failure --------------------------------------------

def test_no_panel_files_written_when_gate_fails(tmp_path, monkeypatch):
    dates, score, group_labels, known = _clean_scenario()
    _setup_run(tmp_path, monkeypatch, score=score, group_labels=group_labels, known=known)
    rebuilt_score = score.copy()
    rebuilt_score.iloc[3, 0] += 0.5
    reference = panel._reference_ic(score, group_labels, known)
    built = _built_from(dates, rebuilt_score, group_labels, known, daily_ic_values=reference)

    output_dir = tmp_path / "panels" / "2026-09-17"

    # Mirrors main()'s own order exactly: the gate call happens before any
    # mkdir/to_csv, so a raise here must leave the output directory untouched.
    with pytest.raises(ValueError):
        panel.run_reproducibility_gate(built, [CANDIDATE])
        output_dir.mkdir(parents=True, exist_ok=True)
        built["daily_ic"].to_csv(output_dir / "daily_ic.csv")

    assert not output_dir.exists()


def test_panel_files_are_written_when_gate_passes(tmp_path, monkeypatch):
    dates, score, group_labels, known = _clean_scenario()
    _setup_run(tmp_path, monkeypatch, score=score, group_labels=group_labels, known=known)
    reference = panel._reference_ic(score, group_labels, known)
    built = _built_from(dates, score, group_labels, known, daily_ic_values=reference)

    output_dir = tmp_path / "panels" / "2026-09-17"
    panel.run_reproducibility_gate(built, [CANDIDATE])
    output_dir.mkdir(parents=True, exist_ok=True)
    built["daily_ic"].to_csv(output_dir / "daily_ic.csv")

    assert (output_dir / "daily_ic.csv").exists()
