import importlib.util
import csv
import json
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/build_ic_inventory.py"
SPEC = importlib.util.spec_from_file_location("ic_inventory", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence(**updates):
    row = {
        "data_quality_status": "CLEAN_FOR_CURRENT_REJUDGE",
        "source_label_artifact_matches": "True",
        "evidence_policy": "PRIOR_DIRECTION_FULL_WINDOW",
        "full_n": "400", "full_ic_mean": "0.04", "full_ic_hac_t": "2.5",
        "full_ic_block_t": "2.2", "historical_metrics_pass": "True",
        "paired_increment_pass": "False", "conditional_budget_pass": "False",
        "factor_evidence_pass": "False",
    }
    row.update(updates)
    return row


def test_basic_ic_survives_legacy_increment_budget_failure():
    assert MODULE.classify(evidence())[0] == "HAS_IC"


def test_missing_or_invalid_evidence_is_not_a_negative_finding():
    for row in ({}, evidence(full_n="100"), evidence(data_quality_status="DEGRADED"),
                evidence(full_ic_hac_t="nan"), evidence(source_label_artifact_matches="False")):
        assert MODULE.classify(row)[0] == "PENDING"


def test_failed_basic_ic_is_retained_as_negative_result():
    assert MODULE.classify(evidence(historical_metrics_pass="False", full_ic_mean="-0.04"))[0] == "NO_IC"


def test_explicit_cold_250_version_keeps_a_287_day_failed_screen_out_of_pending():
    old = evidence(full_n="287", historical_metrics_pass="False", full_ic_mean="-0.017")
    assert MODULE.classify(old)[0] == "PENDING"
    current = {**old, "_screens_version": "cold_250_v1"}
    assert MODULE.classify(current)[0] == "NO_IC"
    assert MODULE.descriptive_classification(current)[1] == "COVERAGE_SUFFICIENT"


def test_descriptive_signed_ic_is_separate_from_legacy_screen_and_coverage():
    cases = [
        (evidence(full_ic_mean="0.075", full_ic_hac_t="1.96", historical_metrics_pass="False"), "POSITIVE_IC", "COVERAGE_SUFFICIENT"),
        (evidence(full_ic_mean="-0.099", full_ic_hac_t="-3", historical_metrics_pass="True"), "NEGATIVE_IC", "COVERAGE_SUFFICIENT"),
        (evidence(full_n="20", full_ic_mean="0.02"), "POSITIVE_IC", "COVERAGE_INSUFFICIENT"),
        (evidence(full_ic_mean="0.009999"), "NEAR_ZERO", "COVERAGE_SUFFICIENT"),
        (evidence(full_ic_mean=""), "UNCOMPUTABLE", "MISSING_OR_INVALID_NUMERIC_IC"),
        (evidence(data_quality_status="DEGRADED", full_ic_mean="0.07"), "UNCOMPUTABLE", "DATA_QUALITY"),
        (evidence(source_label_artifact_matches="False", full_ic_mean="-0.07"), "UNCOMPUTABLE", "LABEL_MISMATCH"),
        (evidence(evidence_policy="UNKNOWN", full_ic_mean="0.07"), "UNCOMPUTABLE", "INVALID_OR_UNSUPPORTED_TIMING_SURFACE"),
    ]
    for row, expected, reason in cases:
        assert MODULE.descriptive_classification(row) == (expected, reason)


def test_2025_direction_uses_only_2026_evidence():
    row = evidence(evidence_policy="2025_DIRECTION_2026_HISTORICAL_SEGMENT",
                   y2026_n="150", y2026_ic_mean="0.005", y2026_ic_hac_t="0.1",
                   y2026_ic_block_t="0.1", historical_2026_metrics_pass="False")
    assert MODULE.classify(row)[0] == "NO_IC"
    row["y2026_n"] = "111"
    assert MODULE.classify(row)[0] == "PENDING"
    assert MODULE.descriptive_classification(row)[0] == "NEAR_ZERO"
    assert MODULE.descriptive_classification(row)[1] == "COVERAGE_INSUFFICIENT"


def test_inventory_deduplicates_plans_retains_uncomputed_and_excludes_other_pools(tmp_path):
    cfg = {"groups": MODULE.GROUPS, "windows": [20], "source_type": "daily",
           "mechanisms": {"example": {"direction": 1}}, "evaluation_start": "2025-01-01",
           "as_of": "2026-09-17"}
    runs = tmp_path / "runs"
    for name, group in (("first", MODULE.GROUPS), ("rerun", MODULE.GROUPS), ("other", "other_pool")):
        path = runs / name
        path.mkdir(parents=True)
        (path / "PLAN.json").write_text(json.dumps({
            "config": {**cfg, "groups": group}, "candidate_ids": ["example_20", "uncomputed_20"],
            "created_utc": name,
        }))
    definitions = MODULE.planned_definitions(runs)
    assert len(definitions) == 2
    key = next(k for k, v in definitions.items() if v["candidate"] == "example_20")
    row = {**evidence(), "definition_id": key, "candidate": "example_20"}
    summary = tmp_path / "summary.csv"
    with summary.open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    records = MODULE.build_records(summary, runs)
    assert len(records) == 2
    assert {r["candidate"]: r["status"] for r in records} == {
        "example_20": "HAS_IC", "uncomputed_20": "PENDING",
    }


def test_registration_versions_map_to_one_semantic_definition(tmp_path):
    cfg = {"groups": MODULE.GROUPS, "source_type": "daily", "windows": [20],
           "mechanisms": {"example": {"direction": 1}}}
    for name in ("original", "new_implementation"):
        path = tmp_path / name
        path.mkdir()
        (path / "PLAN.json").write_text(json.dumps({
            "config": cfg, "candidate_ids": ["example_20"],
            "source_hashes": {"/synthetic/etf_group_discovery.py": name},
        }))
    records = MODULE.planned_definitions(tmp_path)
    registrations = MODULE.registration_index(tmp_path, [])
    assert len(records) == 1
    assert len(registrations) == 2
    assert {r["definition_id"] for r in registrations} == set(records)


def test_formula_text_does_not_become_family_name(tmp_path):
    path = tmp_path / "run"
    path.mkdir()
    (path / "PLAN.json").write_text(json.dumps({
        "config": {"groups": MODULE.GROUPS, "source_type": "daily_rounds", "windows": [20],
                   "mechanisms": {"underwater_time_share": {"direction": -1, "raw_formula": "mean(1[close < peak])"}}},
        "candidate_ids": ["underwater_time_share_20"],
    }))
    record = next(iter(MODULE.planned_definitions(tmp_path).values()))
    assert record["family"] == "daily_rounds:underwater_time_share"


def test_external_redundancy_does_not_erase_ic_but_invalid_design_stays_pending(tmp_path):
    cfg = {"groups": MODULE.GROUPS, "entry_lag": 2, "horizon": 5, "windows": [20],
           "mechanisms": {"breadth": {"direction": 1}, "entropy": {"direction": 1}},
           "screens": {"min_days": 360, "min_ic": 0.01, "min_ic_hac_t": 2,
                       "min_ic_block_t": 2, "min_positive_years": 2}}
    (tmp_path / "PLAN.json").write_text(json.dumps({"config": cfg}))
    (tmp_path / "MASTER_VERDICT.json").write_text(json.dumps({
        "signal_before_entry_before_exit_verified": True,
        "design_rejected": ["entropy_20"], "redundant_historical_leads": ["breadth_20"],
    }))
    (tmp_path / "future_leak_check.json").write_text(json.dumps({"all_pass": True}))
    (tmp_path / "yearly.csv").write_text("candidate,year,n,ic_mean,ic_hac_t,ic_block_t\nbreadth_20,2025,220,0.05,1.4,1.5\n")
    row = {"candidate": "breadth_20", "n": 400, "ic_mean": .08, "ic_hac_t": 2.5,
           "ic_block_t": 2.4, "positive_years": 2, "all_eligible_years_positive": True,
           "min_leave_group_ic": .02}
    with (tmp_path / "summary.csv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
        writer.writerow({**row, "candidate": "entropy_20"})
    imported = list(MODULE.external_evidence(tmp_path))
    assert [MODULE.classify(r)[0] for r in imported] == ["HAS_IC", "PENDING"]
    assert imported[0]["y2025_n"] == "220"
    assert imported[0]["y2025_ic_mean"] == "0.05"


def test_declared_family_groups_distinct_candidates(tmp_path):
    run = tmp_path / 'run'
    run.mkdir()
    (run / 'PLAN.json').write_text(json.dumps({
        'config': {'groups': MODULE.GROUPS, 'source_type': 'daily_rounds', 'windows': [20],
                   'mechanisms': {name: {'direction': 1, 'family': 'tail_response'}
                                  for name in ('tail_mean', 'tail_frequency')}},
        'candidate_ids': ['tail_mean_20', 'tail_frequency_20'],
    }))
    records = list(MODULE.planned_definitions(tmp_path).values())
    assert len(records) == 2
    assert {r['family'] for r in records} == {'daily_rounds:tail_response'}
    assert {r['family_basis'] for r in records} == {'declared_mechanism_family'}


def test_structural_precheck_rejection_is_indexed_without_market_evidence(tmp_path):
    cfg = {"groups": MODULE.GROUPS, "windows": [20], "source_type": "daily_rounds",
           "mechanisms": {"candidate": {"direction": 1, "family": "precheck_family"}}}
    rejection = tmp_path / "precheck.json"
    rejection.write_text(json.dumps({
        "config": cfg, "candidate_ids": ["candidate_20"], "created_utc": "2026-09-23T00:00:00Z",
        "rejections": {"candidate_20": {"reason": "NO_COMMON_RANKABLE_DATES",
                                         "complete_8group_dates": 0, "rankable_8group_dates": 0}},
    }))
    summary = tmp_path / "empty.csv"
    summary.write_text("definition_id,candidate\n")
    records = MODULE.build_records(summary, tmp_path / "empty_runs", structural_rejections=[rejection])
    assert len(records) == 1
    assert records[0]["status"] == "PENDING"
    assert records[0]["reason"] == "PRECHECK_NO_COMMON_RANKABLE_DATES"
    assert records[0]["directional_classification"] == "UNCOMPUTABLE"
    assert records[0]["directional_reason"] == "PRECHECK_NO_COMMON_RANKABLE_DATES"
    assert json.loads(records[0]["structural_rejection"])["rankable_8group_dates"] == 0


def test_saved_evidence_survives_stale_structural_rejection(tmp_path):
    cfg = {"groups": MODULE.GROUPS, "windows": [20], "source_type": "daily_rounds",
           "mechanisms": {"candidate": {"direction": 1, "family": "precheck_family"}}}
    rejection = tmp_path / "precheck.json"
    rejection.write_text(json.dumps({
        "config": cfg, "candidate_ids": ["candidate_20"], "created_utc": "2026-09-23T00:00:00Z",
        "rejections": {"candidate_20": {"reason": "NO_COMMON_RANKABLE_DATES", "rankable_8group_dates": 0}},
    }))
    key = MODULE.semantic_id(cfg, "candidate_20")
    row = {**evidence(), "definition_id": key, "candidate": "candidate_20"}
    summary = tmp_path / "summary.csv"
    with summary.open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    records = MODULE.build_records(summary, tmp_path / "empty_runs", structural_rejections=[rejection])
    assert records[0]["status"] == "HAS_IC"
    assert records[0]["directional_classification"] == "POSITIVE_IC"
    assert "structural_rejection" in records[0]


def synthetic_inventory(tmp_path, budget):
    runs = tmp_path / 'runs'
    run = runs / 'example'
    run.mkdir(parents=True)
    cfg = {'groups': MODULE.GROUPS, 'source_type': 'daily', 'windows': [20],
           'evaluation_start': '2025-01-01', 'as_of': '2026-09-17',
           'mechanisms': {'example': {'direction': 1, 'raw_formula': 'synthetic formula'}}}
    (run / 'PLAN.json').write_text(json.dumps({'config': cfg, 'candidate_ids': ['example_20'],
        'source_hashes': {'/synthetic/etf_group_discovery.py': 'synthetic-hash'}}))
    row = {**evidence(evidence_policy='2025_DIRECTION_2026_HISTORICAL_SEGMENT',
                     y2025_n='220', y2025_ic_mean='-0.04', y2026_n='160', y2026_ic_mean='0.06',
                     y2026_ic_hac_t='2.1', y2026_ic_block_t='2.2', y2026_min_loso_ic='0.02',
                     historical_2026_metrics_pass='True'),
           'candidate': 'example_20', 'definition_id': MODULE.semantic_id(cfg, 'example_20')}
    summary = tmp_path / 'summary.csv'
    MODULE.write_csv(summary, [row], list(row))
    (tmp_path / 'verdict.json').write_text(json.dumps({'conditionally_registered_definitions': budget}))
    return runs, summary


def test_enrichment_preserves_selected_surface_and_missing_diagnostics(tmp_path):
    runs, summary = synthetic_inventory(tmp_path, 1)
    row, = MODULE.build_records(summary, runs)
    assert row['ic'] == '0.06'
    assert row['n'] == '160'
    assert row['ic_window_start'] == '2026-01-01'
    assert row['y2025_role'] == 'DIRECTION_SELECTION_ONLY'
    assert row['y2025_ic_mean'] == '-0.04'
    assert row['y2025_ic_hac_t'] == ''  # never invent a zero diagnostic
    assert row['min_leave_group_ic'] == '0.02'
    assert json.loads(row['stability_diagnostics'])['y2026_ic_mean'] == '0.06'
    assert row['basic_screen_status'] == row['status'] == 'HAS_IC'


def test_stale_budget_cannot_replace_latest_snapshot(tmp_path, monkeypatch):
    runs, summary = synthetic_inventory(tmp_path, 384)
    pointer = tmp_path / 'IC_INVENTORY_LATEST.json'
    pointer.write_text('{"snapshot":"previous"}')
    output = tmp_path / 'new_snapshot'
    monkeypatch.setattr(MODULE.sys, 'argv', ['build_ic_inventory.py', '--summary', str(summary),
        '--runs-root', str(runs), '--output', str(output)])
    with pytest.raises(ValueError, match='registration mismatch'):
        MODULE.main()
    assert not output.exists()
    assert pointer.read_text() == '{"snapshot":"previous"}'


def test_clean_snapshot_writes_explicit_leads_and_balanced_counts(tmp_path, monkeypatch):
    runs, summary = synthetic_inventory(tmp_path, 1)
    output = tmp_path / 'new_snapshot'
    monkeypatch.setattr(MODULE.sys, 'argv', ['build_ic_inventory.py', '--summary', str(summary),
        '--runs-root', str(runs), '--output', str(output)])
    MODULE.main()
    with (output / 'basic_ic_leads.csv').open() as f:
        row, = list(csv.DictReader(f))
    assert row['ic'] == '0.06' and row['y2025_role'] == 'DIRECTION_SELECTION_ONLY'
    manifest = json.loads((output / 'manifest.json').read_text())
    assert manifest['unreconciled_registered_count'] == 0
    assert manifest['directional_counts']['POSITIVE_IC'] == 1
