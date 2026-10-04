import csv
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research"
sys.path.insert(0, str(SCRIPT))
from etf_autoresearch_library import rebuild_library, context_for_proposer


def test_rebuild_indexes_all_trials_and_context_hides_formal_metrics(tmp_path):
    root = tmp_path / "runs"
    round_dir = root / "campaigns" / "c1" / "r01"
    round_dir.mkdir(parents=True)
    source = "FAMILY = 'trend'\n"
    (round_dir / "candidate.py").write_text(source)
    (root / "campaigns" / "c1" / "summary.json").write_text(json.dumps({
        "campaign_id": "c1", "rounds": [
            {"run_id": "c1_r01", "round": 1, "status": "COMPLETED", "candidate": "x", "family": "trend", "ic": 0.02, "hac_t": 2.2, "n": 300, "source_path": str(round_dir / "candidate.py"), "mode": "explore", "input_profile": "fixed14"},
            {"run_id": "c1_r02", "round": 2, "status": "FAILED", "candidate": "y", "family": "trend", "error": "timeout", "error_type": "TimeoutError"},
        ]
    }))
    # Same run appears in result and summary; retain one record.
    result_dir = root / "c1_r01"
    result_dir.mkdir(parents=True)
    (result_dir / "result.json").write_text(json.dumps({"run_id": "c1_r01", "candidate": "x", "family": "trend", "ic": 0.02, "hac_t": 2.2, "n": 300, "yearly": {"2025": {"ic": 0.02, "missing": float("nan")}}}))
    formal = tmp_path / "formal.csv"
    formal.write_text("candidate,family,description,full_ic_mean\nold,flow,Definition only,0.8\n")

    result = rebuild_library(root, formal)
    rows = json.loads((root / "library/library.json").read_text())
    assert result["local_trial_count"] == 2
    assert [r["run_id"] for r in rows["local_trials"]] == ["c1_r01", "c1_r02"]
    assert rows["local_trials"][0]["ic_category"] == "POSITIVE_IC"
    assert rows["local_trials"][0]["source_sha256"]
    assert rows["local_trials"][0]["yearly"]["2025"]["missing"] is None
    assert rows["local_trials"][1]["error"] == "timeout"
    assert "full_ic_mean" not in rows["formal_definitions"][0]
    context = context_for_proposer(root, formal)
    assert context["local_family_trial_counts"]["trend"] == 2
    assert context["recent_failures"][0]["error"] == "timeout"
    assert context["local_completed_candidates"][0]["input_profile"] == "fixed14"
    assert context["local_completed_candidates"][0]["mode"] == "explore"
    assert context["local_completed_candidates"][0]["code_path"] == str(round_dir / "candidate.py")
    assert "full_ic_mean" not in json.dumps(context)
    with (root / "library/library.csv").open() as stream:
        assert len(list(csv.DictReader(stream))) == 2


def test_signed_bands_and_precycle_failure(tmp_path):
    root = tmp_path / "runs"
    attempt = root / "attempts"
    attempt.mkdir(parents=True)
    (attempt / "bad.json").write_text(json.dumps({"run_id": "bad", "status": "FAILED", "stage": "preflight", "error": "stale inventory", "error_type": "ValueError"}))
    rounds = root / "campaigns/c/r01"
    rounds.mkdir(parents=True)
    (rounds / "candidate.py").write_text("source")
    for round_number in (2, 3):
        source_dir = root / "campaigns/c" / f"r{round_number:02d}"
        source_dir.mkdir()
        (source_dir / "candidate.py").write_text(f"source {round_number}")
    (root / "campaigns/c/summary.json").write_text(json.dumps({"campaign_id": "c", "rounds": [
        {"run_id": "neg", "round": 1, "status": "COMPLETED", "ic": -0.01, "family": "f"},
        {"run_id": "zero", "round": 2, "status": "COMPLETED", "ic": 0.009, "family": "g"},
        {"run_id": "nan", "round": 3, "status": "COMPLETED", "ic": "nan", "family": "h"},
    ]}))
    rebuild_library(root, tmp_path / "missing.csv")
    rows = {r["run_id"]: r for r in json.loads((root / "library/library.json").read_text())["local_trials"]}
    assert rows["neg"]["ic_category"] == "NEGATIVE_IC"
    assert rows["zero"]["ic_category"] == "NEAR_ZERO"
    assert rows["nan"]["ic_category"] == "UNCOMPUTABLE"
    assert rows["bad"]["error"] == "stale inventory"


def test_reference_exclusion_and_failed_pipeline_keeps_evaluation(tmp_path):
    root = tmp_path / "runs"
    ref = root / "seed"
    ref.mkdir(parents=True)
    (ref / "result.json").write_text(json.dumps({"run_id": "seed", "candidate": "seed", "family": "base", "ic": 0.04, "n": 100}))
    (ref / "reference_seed.json").write_text("{}")
    failed = root / "postfail"
    failed.mkdir(parents=True)
    (failed / "result.json").write_text(json.dumps({"run_id": "postfail", "candidate": "x", "family": "flow", "ic": 0.015, "n": 30}))
    attempts = root / "attempts"
    attempts.mkdir()
    (attempts / "postfail.json").write_text(json.dumps({"run_id": "postfail", "status": "FAILED", "stage": "novelty", "error": "audit error"}))
    result = rebuild_library(root, tmp_path / "no-formal.csv")
    payload = json.loads(result["library_json"].read_text())
    assert result["local_trial_count"] == 1
    assert result["reference_count"] == 1
    row = payload["local_trials"][0]
    assert row["status"] == "FAILED"
    assert row["evaluation_status"] == "EVALUATED"
    assert row["ic"] == 0.015
    assert row["parent_eligible"] is False


def test_novelty_is_retained_and_exact_duplicate_is_distinct_from_overlap(tmp_path):
    root = tmp_path / "runs"
    campaign = root / "campaigns" / "novelty"
    campaign.mkdir(parents=True)
    (campaign / "summary.json").write_text(json.dumps({"campaign_id": "novelty", "rounds": [
        {"run_id": "exact", "status": "COMPLETED", "candidate": "a", "family": "one", "ic": 0.02,
         "nearest": {"candidate": "formal_a", "mean_abs_daily_rank_corr": 1.0}},
        {"run_id": "overlap", "status": "COMPLETED", "candidate": "b", "family": "two", "ic": 0.03,
         "nearest": {"candidate": "formal_b", "mean_abs_daily_rank_corr": 0.82}},
    ]}))
    payload = rebuild_library(root, tmp_path / "no-formal.csv")
    indexed = {row["run_id"]: row for row in json.loads(payload["library_json"].read_text())["local_trials"]}
    context = context_for_proposer(root, tmp_path / "no-formal.csv")
    candidates = {row["run_id"]: row for row in context["local_completed_candidates"]}
    assert indexed["exact"]["novelty_diagnostic"] == "EXACT_RANK_DUPLICATE"
    assert indexed["overlap"]["novelty_diagnostic"] == "HIGH_SCORE_OVERLAP"
    assert indexed["exact"]["nearest"]["candidate"] == "formal_a"
    assert candidates["overlap"]["nearest"]["mean_abs_daily_rank_corr"] == 0.82


def test_positive_ic_survives_unchanged_parent_and_revision_audit(tmp_path):
    root = tmp_path / 'runs'
    campaign = root / 'campaigns' / 'v6'
    campaign.mkdir(parents=True)
    source_dir = campaign / 'r01'
    source_dir.mkdir()
    (source_dir / 'candidate.py').write_text('trial source')
    (campaign / 'summary.json').write_text(json.dumps({'rounds': [{
        'run_id': 'trial', 'round': 1, 'status': 'COMPLETED', 'mode': 'refine',
        'family': 'flow', 'ic': 0.021, 'keep': False, 'outcome_opened': True,
        'revisions': [{'source_path': 'original.py'}, {'source_path': 'repair.py'}],
        'reason_code': 'PARENT_RETAINED',
    }]}))
    paths = rebuild_library(root, tmp_path / 'absent.csv')
    row = json.loads(paths['library_json'].read_text())['local_trials'][0]
    assert row['ic_recorded'] is True and row['ic'] == 0.021
    assert row['parent_replaced'] is False and row['ic_category'] == 'POSITIVE_IC'
    assert row['outcome_opened'] is True and len(row['revisions']) == 2
    with paths['library_csv'].open() as stream:
        assert next(csv.DictReader(stream))['reason_code'] == 'PARENT_RETAINED'


def test_frozen_source_mismatch_preserves_raw_ic_without_trusting_it(tmp_path):
    import hashlib
    root = tmp_path / 'runs'
    directory = root / 'campaigns/c'
    directory.mkdir(parents=True)
    code = directory / 'candidate.py'
    code.write_text('modified source')
    (directory / 'summary.json').write_text(json.dumps({'rounds': [{
        'round': 1, 'run_id': 'r', 'status': 'COMPLETED', 'source_path': str(code),
        'candidate_sha256': hashlib.sha256(b'original source').hexdigest(),
        'ic': -.05, 'hac_t': -2., 'n': 287, 'keep': True,
        'family_plan': {'formula': 'frozen', 'direction': -1}}]}))
    paths = rebuild_library(root, tmp_path / 'absent.csv')
    row = json.loads(paths['library_json'].read_text())['local_trials'][0]
    assert row['source_integrity'] == 'MISMATCH' and row['ic'] == -.05
    assert row['ic_category'] == 'UNCOMPUTABLE' and not row['parent_eligible']
    with paths['library_csv'].open() as stream:
        indexed = next(csv.DictReader(stream))
    assert indexed['formula'] == 'frozen' and indexed['direction'] == '-1'


def test_unknown_source_preserves_ic_but_marks_evidence_uncomputable(tmp_path):
    root = tmp_path / 'runs'
    campaign = root / 'campaigns/c'
    campaign.mkdir(parents=True)
    (campaign / 'summary.json').write_text(json.dumps({'rounds': [{
        'round': 1, 'run_id': 'unknown', 'status': 'COMPLETED',
        'source_path': str(campaign / 'missing_candidate.py'),
        'candidate_sha256': 'a' * 64, 'ic': 0.031, 'hac_t': 2.4,
        'n': 300, 'keep': True,
    }]}))
    paths = rebuild_library(root, tmp_path / 'absent.csv')
    row = json.loads(paths['library_json'].read_text())['local_trials'][0]
    assert row['source_integrity'] == 'UNKNOWN'
    assert row['ic'] == 0.031 and row['ic_recorded'] is True
    assert row['evidence_valid'] is False
    assert row['ic_category'] == 'UNCOMPUTABLE'
    assert row['parent_eligible'] is False
