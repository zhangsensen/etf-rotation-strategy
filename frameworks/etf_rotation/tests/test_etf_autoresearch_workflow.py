import hashlib
import json
from pathlib import Path
import sys
import ast

import pytest

RESEARCH = Path(__file__).resolve().parents[1] / "scripts/research"
sys.path.insert(0, str(RESEARCH))
import etf_autoresearch_workflow as workflow_module


def _source(candidate, family, window):
    return f'''from __future__ import annotations
import pandas as pd
CANDIDATE_ID = "{candidate}"
FAMILY = "{family}"
DIRECTION = 1
DESCRIPTION = "Causal rolling return {window}."
def score(panels):
    return panels["close"].pct_change({window}, fill_method=None)
'''


def test_batch_review_precedes_evaluation_and_keeps_all_signed_results(tmp_path, monkeypatch):
    root = tmp_path / "autoresearch"
    inventory = tmp_path / "formal.csv"
    runs = tmp_path / "formal-runs"
    inventory.write_text("candidate,family\n")
    runs.mkdir()
    from run_etf_autoresearch_ic import CANDIDATE
    baseline_candidate = CANDIDATE
    before_sha = hashlib.sha256(baseline_candidate.read_bytes()).hexdigest()
    events = []
    proposal_contexts = []
    review_payloads = []
    planning_calls = []

    monkeypatch.setattr(workflow_module, "require_latest_inventory", lambda *_: None)
    monkeypatch.setattr(workflow_module, "describe_profiles", lambda *_: {
        "daily": {"available": True, "panels": ["close"]}})

    def planner(context, directory, model):
        planning_calls.append(context["campaign_id"])
        names = ["trend_a", "trend_b", "flow_c", "range_d"]
        return [{"family_key": name, "mechanism": name, "distinct_from": "other mechanisms",
                 "why_distinct": "different data-generating mechanism", "input_profile": "daily"}
                for name in names[:context["requested_count"]]]

    def proposer(context, directory, model):
        events.append(("proposal", context["round"]))
        proposal_contexts.append(context)
        run_id = directory.name
        campaign = directory.parent.name
        slot = int(run_id.rsplit("c", 1)[1])
        windows = [11, 13, 17, 19]
        window = windows[slot - 1]
        family = context["assigned_family_plan"]["family_key"]
        return {"rationale": "Fixed D-close rolling mechanism.",
                "source_code": _source(f"autoresearch_{campaign}_{slot}", family, window)}

    def reviewer(items, directory, model):
        events.append(("review", directory.name))
        review_payloads.extend(items)
        assert all("ic" not in item and "yearly" not in item for item in items)
        return {item["run_id"]: {"run_id": item["run_id"], "approved": True,
                                 "reason": "causal proposal accepted",
                                 "canonical_family": item["planned_family"]} for item in items}


    def evaluate(run_id, output_root, baseline, inventory_path, runs_root,
                 candidate_path=None, input_profile=None):
        events.append(("evaluate", run_id))
        values = [0.02, 0.03, -0.02, 0.04]
        slot = int(run_id.rsplit("c", 1)[1])
        module = ast.parse(Path(candidate_path).read_text())
        metadata = {target.id: ast.literal_eval(node.value)
                    for node in module.body if isinstance(node, ast.Assign)
                    for target in node.targets if isinstance(target, ast.Name)}
        result = {"run_id": run_id, "candidate": metadata["CANDIDATE_ID"],
                  "family": metadata["FAMILY"], "ic": values[slot - 1], "hac_t": 1.2,
                  "n": 200, "yearly": {"2025": {"ic": values[slot - 1]}}}
        out = output_root / run_id
        out.mkdir(parents=True)
        (out / "result.json").write_text(json.dumps(result))
        return {"decision": "positive_ic_review" if result["ic"] > 0 else "negative_ic_watch"}

    first = workflow_module.workflow(
        "first", 1, 4, ["daily"], root, inventory, runs, mode="open",
        propose=proposer, review=reviewer, evaluate=evaluate, planner=planner)
    first_rows = first["rounds"]
    assert len(first_rows) == 4
    assert [row["ic"] for row in first_rows] == [0.02, 0.03, -0.02, 0.04]
    assert [row["keep"] for row in first_rows] == [True, True, False, True]
    assert all(row["status"] == "COMPLETED" for row in first_rows)
    # Approval happens after all proposals are frozen and before the first label read.
    review_index = next(i for i, event in enumerate(events) if event[0] == "review")
    first_eval_index = next(i for i, event in enumerate(events) if event[0] == "evaluate")
    assert review_index < first_eval_index
    assert len(review_payloads) == 4
    assert planning_calls == ["first"]
    assert hashlib.sha256(baseline_candidate.read_bytes()).hexdigest() == before_sha

    library = json.loads((root / "library/library.json").read_text())
    first_library = [row for row in library["local_trials"] if row.get("campaign_id") == "first"]
    assert len(first_library) == 4
    assert sum(row["ic_category"] == "NEGATIVE_IC" for row in first_library) == 1
    assert sum(row["ic_category"] == "POSITIVE_IC" for row in first_library) == 3


def test_resume_reuses_frozen_proposals_after_reviewer_failure(tmp_path, monkeypatch):
    root = tmp_path / "autoresearch"
    inventory = tmp_path / "formal.csv"
    runs = tmp_path / "formal-runs"
    inventory.write_text("candidate,family\n")
    runs.mkdir()
    from run_etf_autoresearch_ic import CANDIDATE
    baseline_candidate = CANDIDATE
    before_sha = hashlib.sha256(baseline_candidate.read_bytes()).hexdigest()
    proposals = []
    reviews = []
    evaluations = []
    planning_calls = []

    monkeypatch.setattr(workflow_module, "require_latest_inventory", lambda *_: None)
    monkeypatch.setattr(workflow_module, "describe_profiles", lambda *_: {
        "daily": {"available": True, "panels": ["close"]}})

    def planner(context, directory, model):
        planning_calls.append(context["campaign_id"])
        return [{"family_key": f"resume_family_{slot}", "mechanism": "rolling return",
                 "distinct_from": "other families", "why_distinct": "synthetic plan",
                 "input_profile": "daily"}
                for slot in range(1, context["requested_count"] + 1)]

    def proposer(context, directory, model):
        proposals.append(directory.name)
        slot = int(directory.name.rsplit("c", 1)[1])
        return {"rationale": "Resume-safe deterministic proposal.",
                "source_code": _source(f"autoresearch_resume_{slot}", f"resume_family_{slot}", 41 + slot)}

    def reject_batch(items, directory, model):
        reviews.append([item["run_id"] for item in items])
        raise RuntimeError("review service unavailable")

    def approve_batch(items, directory, model):
        reviews.append([item["run_id"] for item in items])
        return {item["run_id"]: {"run_id": item["run_id"], "approved": True,
                                 "reason": "reviewed after resume",
                                 "canonical_family": item["planned_family"]} for item in items}


    def evaluate(run_id, output_root, baseline, inventory_path, runs_root,
                 candidate_path=None, input_profile=None):
        evaluations.append(run_id)
        module = ast.parse(Path(candidate_path).read_text())
        metadata = {target.id: ast.literal_eval(node.value)
                    for node in module.body if isinstance(node, ast.Assign)
                    for target in node.targets if isinstance(target, ast.Name)}
        result = {"run_id": run_id, "candidate": metadata["CANDIDATE_ID"],
                  "family": metadata["FAMILY"], "ic": 0.02, "hac_t": 1.1,
                  "n": 200, "yearly": {"2025": {"ic": 0.02}}}
        out = output_root / run_id
        out.mkdir()
        (out / "result.json").write_text(json.dumps(result))
        return {"decision": "positive_ic_review"}

    with pytest.raises(RuntimeError, match="review service unavailable"):
        workflow_module.workflow(
            "resume_case", 1, 4, ["daily"], root, inventory, runs, mode="open",
            propose=proposer, review=reject_batch, evaluate=evaluate, planner=planner)
    interrupted = json.loads((root / "campaigns/resume_case/summary.json").read_text())
    assert interrupted["status"] == "INTERRUPTED"
    assert all(row["status"] == "FROZEN" for row in interrupted["rounds"])
    assert len(proposals) == 4
    assert evaluations == []

    resumed = workflow_module.workflow(
        "resume_case", 1, 4, ["daily"], root, inventory, runs, mode="open",
        propose=proposer, review=approve_batch, evaluate=evaluate, resume=True, planner=planner)
    assert resumed["status"] == "COMPLETED"
    assert len(proposals) == 4, "resume must reuse frozen source snapshots"
    assert reviews[0] == reviews[1]
    assert len(evaluations) == 4
    assert all(row["status"] == "COMPLETED" for row in resumed["rounds"])
    assert hashlib.sha256(baseline_candidate.read_bytes()).hexdigest() == before_sha
    assert planning_calls == ["resume_case"], "resume must reuse the saved family plan"


def test_resume_preserves_oversize_attempt_and_advances_after_repeated_failure(tmp_path, monkeypatch):
    root = tmp_path / "autoresearch"
    inventory = tmp_path / "formal.csv"
    runs = tmp_path / "formal-runs"
    inventory.write_text("candidate,family\n")
    runs.mkdir()
    monkeypatch.setattr(workflow_module, "require_latest_inventory", lambda *_: None)
    monkeypatch.setattr(workflow_module, "describe_profiles", lambda *_: {
        "daily": {"available": True, "panels": ["close"]}})

    campaign_dir = root / "campaigns" / "oversize_resume"
    first_dir = campaign_dir / "planning_r01_attempt1"
    first_dir.mkdir(parents=True)
    (first_dir / "started.json").write_text('{"attempt": 1}\n')
    (first_dir / "planning_context.json").write_text('{"historical_identity": "frozen"}\n')
    first_error = {"error_type": "REQUEST_TOO_LARGE", "characters": 901820,
                   "limit": 900000, "prompt_sha256": "a" * 64, "model_called": False}
    (first_dir / "family_plan_request_error.json").write_text(json.dumps(first_error))
    first_result = {"specs": [], "error": "model request too large: 901820 characters; limit 900000",
                    "error_type": "ValueError", "error_kind": "SYSTEM_ERROR", "service_error": True}
    (first_dir / "result.json").write_text(json.dumps(first_result, indent=2) + "\n")
    original_attempt1 = {p.name: p.read_bytes() for p in first_dir.iterdir()}

    # Minimal valid persisted campaign envelope at the failed round boundary.
    campaign_dir.mkdir(exist_ok=True)
    summary = {"schema_version": "unified_etf_autoresearch_v6",
        "campaign_id": "oversize_resume", "requested_rounds": 1,
        "candidates_per_round": 1, "profiles": ["daily"], "mode": "open",
        "model": "gpt-6-luna", "reviewer": "gpt-6.1-sol", "rounds": [],
        "scheduling_policy": workflow_module.POLICY,
        "round_records": [{"round": 1, "status": "PLANNING_FAILED", "attempt": 1,
                           "path": str(first_dir), "error": first_result["error"],
                           "preserved_proposals": 0}],
        "completed_rounds": 0, "event_sequence": 1, "reopen_records": [],
        "status": "PAUSED_SYSTEM_ERROR"}
    (campaign_dir / "summary.json").write_text(json.dumps(summary))

    planning_calls = []

    def planner(context, directory, model):
        attempt = context["planning_attempt"]
        planning_calls.append(attempt)
        if attempt == 2:
            error = {**first_error, "prompt_sha256": "b" * 64}
            (directory / "family_plan_request_error.json").write_text(json.dumps(error))
            raise ValueError("model request too large: second attempt still exceeds limit")
        return [{"family_key": "resume_flow", "input_profile": "daily",
                 "formula": "close.pct_change(20)", "direction": 1,
                 "required_panels": ["close"], "mode": "open", "parent": None,
                 "math_kernel": "custom"}]

    def proposer(context, directory, model):
        return {"rationale": "Frozen causal daily trend proposal.",
                "source_code": _source("autoresearch_resume_flow", "resume_flow", 20)}

    def reviewer(items, directory, model):
        return {item["run_id"]: {"run_id": item["run_id"], "approved": True,
            "reason": "valid under frozen timing", "canonical_family": item["planned_family"]}
            for item in items}

    def evaluate(run_id, output_root, baseline, inventory_path, runs_root,
                 candidate_path=None, input_profile=None):
        module = ast.parse(Path(candidate_path).read_text())
        metadata = {target.id: ast.literal_eval(node.value)
                    for node in module.body if isinstance(node, ast.Assign)
                    for target in node.targets if isinstance(target, ast.Name)}
        out = output_root / run_id
        out.mkdir(parents=True)
        (out / "result.json").write_text(json.dumps({"run_id": run_id,
            "candidate": metadata["CANDIDATE_ID"], "family": metadata["FAMILY"],
            "ic": .02, "hac_t": 1.2, "n": 200, "yearly": {}}))
        return {"decision": "positive_ic_review"}

    # The pre-existing attempt1 is replayed as evidence only; attempt2 is a new
    # planner invocation. Its second size rejection remains immutable on disk.
    with pytest.raises(RuntimeError, match="PAUSED_SYSTEM_ERROR"):
        workflow_module.workflow("oversize_resume", 1, 1, ["daily"], root, inventory, runs,
            mode="open", propose=proposer, review=reviewer, evaluate=evaluate,
            resume=True, planner=planner)
    assert planning_calls == [2]
    attempt2 = campaign_dir / "planning_r01_attempt2"
    assert (attempt2 / "result.json").exists()
    attempt2_bytes = {p.name: p.read_bytes() for p in attempt2.iterdir()}
    assert {p.name: p.read_bytes() for p in first_dir.iterdir()} == original_attempt1

    # A later explicit resume allocates attempt3 instead of sealing the old
    # planning failure. No proposal/result exists before this fresh success.
    completed = workflow_module.workflow("oversize_resume", 1, 1, ["daily"], root, inventory, runs,
        mode="open", propose=proposer, review=reviewer, evaluate=evaluate,
        resume=True, planner=planner)
    assert planning_calls == [2, 3]
    assert completed["status"] == "COMPLETED"
    assert completed["rounds"][0]["status"] == "COMPLETED"
    assert {p.name: p.read_bytes() for p in first_dir.iterdir()} == original_attempt1
    assert {p.name: p.read_bytes() for p in attempt2.iterdir()} == attempt2_bytes
