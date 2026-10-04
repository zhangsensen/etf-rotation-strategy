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


def _refinement_plan(context, directory, model):
    return [{'family_key': context['assigned_family'], 'input_profile': next(iter(context['allowed_profiles'])),
             'direction': context['parent_contract']['direction'], 'formula': 'synthetic rolling return variant',
             'required_panels': ['close']}]


def test_batch_review_precedes_evaluation_and_memory_drives_refinement(tmp_path, monkeypatch):
    root = tmp_path / "autoresearch"
    inventory = tmp_path / "formal.csv"
    runs = tmp_path / "formal-runs"
    inventory.write_text("candidate,family\n")
    runs.mkdir()
    baseline_candidate = workflow_module.CANDIDATE
    before_sha = hashlib.sha256(baseline_candidate.read_bytes()).hexdigest()
    events = []
    proposal_contexts = []
    review_payloads = []
    ic_by_run = {}
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
        if campaign == "first":
            windows = [11, 13, 17, 19]
            window = windows[slot - 1]
            family = context["assigned_family_plan"]["family_key"]
        else:
            assert context["mode"] == "refine"
            assert context["parent"] is not None
            family = context["assigned_family_plan"]["family_key"]
            window = 23 + slot
        return {"rationale": "Fixed D-close rolling mechanism.",
                "source_code": _source(f"autoresearch_{campaign}_{slot}", family, window)}

    def reviewer(items, directory, model):
        events.append(("review", directory.name))
        review_payloads.extend(items)
        assert all("ic" not in item and "yearly" not in item for item in items)
        return {item["run_id"]: {"run_id": item["run_id"], "approved": True,
                                 "reason": "causal proposal accepted",
                                 "canonical_family": item["planned_family"]} for item in items}

    def seed_run(run_id, output_root, candidate_path, profile):
        events.append(("seed", run_id))
        run_dir = output_root / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "result.json").write_text(json.dumps({
            "run_id": run_id, "candidate": "reference", "family": "seed",
            "ic": 0.1, "hac_t": 4.0, "n": 200, "yearly": {"2025": {"ic": 0.1}}}))
        return {"run_id": run_id}

    def evaluate(run_id, output_root, baseline, inventory_path, runs_root,
                 candidate_path=None, input_profile=None):
        events.append(("evaluate", run_id))
        if run_id.startswith("first_"):
            values = [0.02, 0.03, -0.02, 0.04]
            slot = int(run_id.rsplit("c", 1)[1])
        else:
            values = [0.015, 0.016, 0.017, 0.018]
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

    def compare(_baseline, _trial):
        return {"n": 200, "delta_ic": 0.001}

    monkeypatch.setattr(workflow_module, "compare", compare)
    first = workflow_module.workflow(
        "first", 1, 4, ["daily"], root, inventory, runs, mode="explore",
        propose=proposer, review=reviewer, evaluate=evaluate, seed_run=seed_run, planner=planner)
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

    second = workflow_module.workflow(
        "second", 1, 4, ["daily"], root, inventory, runs, mode="refine",
        propose=proposer, review=reviewer, evaluate=evaluate, seed_run=seed_run, refinement_planner=_refinement_plan)
    assert all(row["status"] == "COMPLETED" for row in second["rounds"])
    assert len(second["rounds"]) == 3
    assert all(row["parent_run"] for row in second["rounds"])
    assert all(row["mode"] == "refine" for row in second["rounds"])
    assert any(context.get("local_completed_candidates") for context in proposal_contexts[4:])
    assert hashlib.sha256(baseline_candidate.read_bytes()).hexdigest() == before_sha


def test_resume_reuses_frozen_proposals_after_reviewer_failure(tmp_path, monkeypatch):
    root = tmp_path / "autoresearch"
    inventory = tmp_path / "formal.csv"
    runs = tmp_path / "formal-runs"
    inventory.write_text("candidate,family\n")
    runs.mkdir()
    baseline_candidate = workflow_module.CANDIDATE
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

    def seed_run(run_id, output_root, candidate_path, profile):
        run_dir = output_root / run_id
        run_dir.mkdir()
        (run_dir / "result.json").write_text(json.dumps({
            "run_id": run_id, "candidate": "reference", "family": "seed", "ic": 0.1,
            "hac_t": 3.0, "n": 200, "yearly": {"2025": {"ic": 0.1}},
            "candidate_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            "input_profile": profile}))
        return {"run_id": run_id}

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
            "resume_case", 1, 4, ["daily"], root, inventory, runs, mode="explore",
            propose=proposer, review=reject_batch, evaluate=evaluate, seed_run=seed_run,
            planner=planner)
    interrupted = json.loads((root / "campaigns/resume_case/summary.json").read_text())
    assert interrupted["status"] == "INTERRUPTED"
    assert all(row["status"] == "FROZEN" for row in interrupted["rounds"])
    assert len(proposals) == 4
    assert evaluations == []

    resumed = workflow_module.workflow(
        "resume_case", 1, 4, ["daily"], root, inventory, runs, mode="explore",
        propose=proposer, review=approve_batch, evaluate=evaluate, seed_run=seed_run,
        resume=True, planner=planner)
    assert resumed["status"] == "COMPLETED"
    assert len(proposals) == 4, "resume must reuse frozen source snapshots"
    assert reviews[0] == reviews[1]
    assert len(evaluations) == 4
    assert all(row["status"] == "COMPLETED" for row in resumed["rounds"])
    assert hashlib.sha256(baseline_candidate.read_bytes()).hexdigest() == before_sha
    assert planning_calls == ["resume_case"], "resume must reuse the saved family plan"


@pytest.mark.parametrize("historical", [False, True])
def test_reviewer_canonical_family_collapses_distinct_labels_before_evaluation(tmp_path, monkeypatch, historical):
    root = tmp_path / "autoresearch"
    inventory = tmp_path / "formal.csv"
    runs = tmp_path / "formal-runs"
    inventory.write_text("candidate,family\n" + ("old,one_canonical_family\n" if historical else ""))
    runs.mkdir()
    calls = []
    monkeypatch.setattr(workflow_module, "require_latest_inventory", lambda *_: None)
    monkeypatch.setattr(workflow_module, "describe_profiles", lambda *_: {
        "daily": {"available": True, "approved": True}})
    monkeypatch.setattr(workflow_module, "family_history", lambda *_: {
        "recent_round_families": [], "family_attempt_counts": {}, "aliases": {},
        "unsuccessful_refinements": {}})

    def planner(context, directory, model):
        return [{"family_key": f"planned_{i}", "mechanism": f"mechanism_{i}",
                 "distinct_from": "other plan labels", "why_distinct": "planner declaration",
                 "nearest_existing_candidate": "old",
                 "input_profile": "daily"} for i in range(context["requested_count"])]

    def proposer(context, directory, model):
        plan = context["assigned_family_plan"]
        slot = context["slot"]
        return {"rationale": "reviewer will canonicalize family",
                "source_code": _source(f"autoresearch_duplicate_{slot}", plan["family_key"], 60 + slot)}

    def review(items, directory, model):
        return {item["run_id"]: {"run_id": item["run_id"], "approved": True,
                                 "reason": "same underlying mechanism",
                                 "canonical_family": "one_canonical_family"} for item in items}

    def seed_run(run_id, output_root, candidate_path, profile):
        out = output_root / run_id
        out.mkdir()
        (out / "result.json").write_text(json.dumps({"run_id": run_id, "candidate_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(), "input_profile": profile, "ic": 0.1, "n": 200}))
        return {}

    def evaluate(run_id, output_root, baseline, inventory_path, runs_root,
                 candidate_path=None, input_profile=None):
        calls.append(run_id)
        source = Path(candidate_path).read_text()
        tree = ast.parse(source)
        metadata = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}
        out = output_root / run_id
        out.mkdir()
        (out / "result.json").write_text(json.dumps({"candidate": metadata["CANDIDATE_ID"], "family": metadata["FAMILY"], "ic": 0.02, "hac_t": 1.0, "n": 200, "yearly": {}}))
        return {"decision": "positive_ic_review"}

    summary = workflow_module.workflow(
        "canonical_test", 1, 4, ["daily"], root, inventory, runs, mode="explore",
        propose=proposer, review=review, evaluate=evaluate, seed_run=seed_run,
        planner=planner)
    assert len(summary["rounds"]) == 4
    assert len(calls) == (0 if historical else 1)
    assert sum(row["status"] == "COMPLETED" for row in summary["rounds"]) == (0 if historical else 1)
    assert sum(row["status"] == "DIVERSITY_SKIPPED" for row in summary["rounds"]) == (4 if historical else 3)


@pytest.mark.parametrize("use_alias", [False, True])
def test_mixed_mode_uses_one_quarter_refinement_quota(tmp_path, monkeypatch, use_alias):
    root = tmp_path / "autoresearch"
    inventory = tmp_path / "formal.csv"
    runs = tmp_path / "formal-runs"
    inventory.write_text("candidate,family\n")
    runs.mkdir()
    monkeypatch.setattr(workflow_module, "require_latest_inventory", lambda *_: None)
    monkeypatch.setattr(workflow_module, "describe_profiles", lambda *_: {
        "daily": {"available": True, "approved": True}})
    monkeypatch.setattr(workflow_module, "family_history", lambda *_: {
        "recent_round_families": [], "family_attempt_counts": {}, "aliases": {"parent_family_0": "canonical_parent_0"} if use_alias else {},
        "unsuccessful_refinements": {}})

    parents = []
    for index in range(3):
        candidate = f"autoresearch_parent_{index}"
        family = f"parent_family_{index}"
        source = _source(candidate, family, 80 + index)
        run_id = f"prior_{index}"
        snapshot_dir = root / "campaigns" / "prior" / run_id
        snapshot_dir.mkdir(parents=True)
        snapshot = snapshot_dir / "candidate.py"
        snapshot.write_text(source)
        result_dir = root / run_id
        result_dir.mkdir(parents=True)
        (result_dir / "result.json").write_text(json.dumps({"candidate_sha256": hashlib.sha256(source.encode()).hexdigest()}))
        parents.append({"run_id": run_id, "candidate": candidate, "family": family,
                        "ic": 0.04 - index * 0.01, "keep": True, "parent_eligible": True,
                        "input_profile": "daily", "code_path": str(snapshot)})
    monkeypatch.setattr(workflow_module, "context_for_proposer", lambda *_: {
        "historical_formal_definitions": [], "local_completed_candidates": parents})
    plan_counts = []

    def planner(context, directory, model):
        plan_counts.append(context["requested_count"])
        return [{"family_key": f"new_family_{i}", "mechanism": "new mechanism",
                 "distinct_from": "every other family", "why_distinct": "synthetic planner",
                 "input_profile": "daily"} for i in range(context["requested_count"])]

    def proposer(context, directory, model):
        spec = context["assigned_family_plan"]
        slot = context["slot"]
        family = spec["family_key"] if context["mode"] == "explore" else context["assigned_family_plan"]["family_key"]
        return {"rationale": "synthetic assigned mechanism", "source_code": _source(
            f"autoresearch_mixed_{slot}", family, 90 + slot)}

    def review(items, directory, model):
        child = next(item for item in items if item['mode'] == 'refine')
        contract = child['parent_contract']
        assert contract['source_code'] == Path(parents[0]['code_path']).read_text()
        assert contract['direction'] == 1
        assert contract['raw_family'] == 'parent_family_0'
        assert contract['planned_canonical_family'] == ('canonical_parent_0' if use_alias else 'parent_family_0')
        assert 'available_inputs' in child
        return {item["run_id"]: {"run_id": item["run_id"], "approved": True,
                                 "reason": "accepted", "canonical_family": item["planned_family"]}
                for item in items}

    def seed_run(run_id, output_root, candidate_path, profile):
        out = output_root / run_id
        out.mkdir()
        (out / "result.json").write_text(json.dumps({"candidate_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(), "input_profile": profile, "n": 200, "ic": 0.1}))
        return {}

    def evaluate(run_id, output_root, baseline, inventory_path, runs_root,
                 candidate_path=None, input_profile=None):
        tree = ast.parse(Path(candidate_path).read_text())
        metadata = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}
        out = output_root / run_id
        out.mkdir()
        (out / "result.json").write_text(json.dumps({"candidate": metadata["CANDIDATE_ID"], "family": metadata["FAMILY"], "ic": 0.02, "hac_t": 1.0, "n": 200, "yearly": {}}))
        return {"decision": "positive_ic_review"}

    monkeypatch.setattr(workflow_module, "compare", lambda *_: {"n": 200, "delta_ic": 0.001})
    summary = workflow_module.workflow(
        "mixed_quota", 1, 4, ["daily"], root, inventory, runs, mode="mixed",
        propose=proposer, review=review, evaluate=evaluate, seed_run=seed_run,
        planner=planner, refinement_planner=_refinement_plan)
    assert all(row["status"] == "COMPLETED" for row in summary["rounds"])
    assert plan_counts == [3]
    assert len(summary["rounds"]) == 4
    assert sum(row["mode"] == "refine" for row in summary["rounds"]) == 1
    assert sum(row["mode"] == "explore" for row in summary["rounds"]) == 3
