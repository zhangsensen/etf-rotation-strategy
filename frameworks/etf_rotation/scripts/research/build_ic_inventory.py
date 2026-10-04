#!/usr/bin/env python3
"""Index saved fixed14/eight-group evidence; never compute new market results.

Output is local research data. Run with explicit --summary and --output.
HAS_IC means the existing basic IC screen, not certification. NO_IC means
not supported on the recorded surface, not a claim that true IC is zero.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
GROUPS = "frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml"
POLICIES = {
    "PRIOR_DIRECTION_FULL_WINDOW": ("full", 360, "2025+ seen history"),
    "2025_DIRECTION_2026_HISTORICAL_SEGMENT": ("y2026", 120, "2026 seen history; direction from 2025"),
    "SEEN_2026_ADAPTIVE_NOT_CONFIRMATION": ("full", 360, "2025+ adaptively searched history"),
}


def yes(value):
    return str(value).lower() == "true"


def number(row, key):
    try:
        value = float(row[key])
        return value if math.isfinite(value) else None
    except (KeyError, ValueError, TypeError):
        return None


def policy_minimum(row, policy):
    prefix, legacy_minimum, _ = policy
    if prefix == "full" and row.get("_screens_version") == "cold_250_v1":
        return 250
    return legacy_minimum


def semantic_id(cfg, candidate):
    """Preserve the join key used by saved v5 rejudgments, including legacy IDs."""
    if cfg.get("source_type") == "autoresearch":
        mechanism, window = candidate, 1
    elif cfg.get("source_type") == "claude_rounds":
        mechanism = next(
            (m for m, d in cfg.get("mechanisms", {}).items()
             if candidate == f"{m}_{d.get('window')}"),
            None,
        )
        window = cfg["mechanisms"][mechanism]["window"] if mechanism else None
    else:
        windows = cfg["windows"]
        window = next((w for w in windows if candidate.endswith(f"_{w}")), windows[0])
        mechanism = candidate.removesuffix(f"_{window}")
    definition = cfg.get("mechanisms", {}).get(mechanism, {})
    payload = [cfg.get("source_type", "daily"), candidate, window, definition]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]


def classify(row):
    """Use only saved basic IC/stability results, availability and coverage."""
    if not row:
        return "PENDING", "NO_SAVED_RESULT"
    if row.get("data_quality_status") not in {"CLEAN_FOR_CURRENT_REJUDGE", "HALT_DIAGNOSTIC_REPORTED"}:
        return "PENDING", "DATA_QUALITY"
    if not yes(row.get("source_label_artifact_matches")):
        return "PENDING", "LABEL_MISMATCH"
    policy = POLICIES.get(row.get("evidence_policy"))
    if not policy:
        return "PENDING", "DIRECTION_DISCOVERY_OR_OTHER_SURFACE"
    if row.get("evidence_policy") == "SEEN_2026_ADAPTIVE_NOT_CONFIRMATION":
        return "PENDING", "ADAPTIVE_HISTORY_NOT_BASIC_IC_CONFIRMATION"
    prefix, _, _ = policy
    minimum = policy_minimum(row, policy)
    n = number(row, prefix + "_n")
    if n is None or n < minimum:
        return "PENDING", "COVERAGE_INSUFFICIENT"
    if any(number(row, prefix + "_" + metric) is None for metric in ("ic_mean", "ic_hac_t", "ic_block_t")):
        return "PENDING", "MISSING_METRICS"
    key = "historical_metrics_pass" if prefix == "full" else "historical_2026_metrics_pass"
    if row.get(key) not in {"True", "False", True, False}:
        return "PENDING", "MISSING_BASIC_SCREEN"
    if yes(row[key]):
        return "HAS_IC", "BASIC_IC_SUPPORTED"
    return "NO_IC", "BASIC_IC_NOT_SUPPORTED_ON_THIS_SURFACE"


def descriptive_classification(row):
    """Signed descriptive IC, independently of coverage and legacy screens."""
    if not row:
        return "UNCOMPUTABLE", "NO_SAVED_RESULT"
    if row.get("data_quality_status") not in {"CLEAN_FOR_CURRENT_REJUDGE", "HALT_DIAGNOSTIC_REPORTED"}:
        return "UNCOMPUTABLE", "DATA_QUALITY"
    if not yes(row.get("source_label_artifact_matches")):
        return "UNCOMPUTABLE", "LABEL_MISMATCH"
    policy = POLICIES.get(row.get("evidence_policy"))
    if not policy:
        return "UNCOMPUTABLE", "INVALID_OR_UNSUPPORTED_TIMING_SURFACE"
    prefix, _, _ = policy
    minimum = policy_minimum(row, policy)
    ic = number(row, prefix + "_ic_mean")
    if ic is None:
        return "UNCOMPUTABLE", "MISSING_OR_INVALID_NUMERIC_IC"
    n = number(row, prefix + "_n")
    if n is None or n <= 0:
        return "UNCOMPUTABLE", "MISSING_OR_NONPOSITIVE_VALID_DAYS"
    return ("POSITIVE_IC" if ic >= 0.01 else "NEGATIVE_IC" if ic <= -0.01 else "NEAR_ZERO"), (
        "COVERAGE_SUFFICIENT" if (number(row, prefix + "_n") or 0) >= minimum
        else "COVERAGE_INSUFFICIENT"
    )


def planned_definitions(runs, extra_plans=()):
    definitions = {}
    for path in sorted([*runs.glob("*/PLAN.json"), *extra_plans]):
        plan = json.loads(path.read_text())
        cfg = plan.get("config", {})
        if cfg.get("groups") != GROUPS:
            continue
        for candidate in plan.get("candidate_ids", []):
            if cfg.get("source_type") == "autoresearch":
                mechanism, window = candidate, 1
            elif cfg.get("source_type") == "claude_rounds":
                # Per-mechanism window (no shared top-level windows list):
                # find the mechanism whose own registered window suffix
                # matches this candidate id.
                mechanism = next(
                    (m for m, d in cfg.get("mechanisms", {}).items()
                     if candidate == f"{m}_{d.get('window')}"),
                    None,
                )
                window = cfg["mechanisms"][mechanism]["window"] if mechanism else None
            else:
                windows = cfg["windows"]
                window = next((w for w in windows if candidate.endswith(f"_{w}")), windows[0])
                mechanism = candidate if cfg.get("source_type") == "daily_outcome" else candidate.removesuffix(f"_{window}")
            definition = cfg.get("mechanisms", {}).get(mechanism, {})
            key = semantic_id(cfg, candidate)
            raw_formula = definition.get("raw_formula", mechanism)
            family = raw_formula if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", raw_formula) else mechanism
            family = family.removesuffix(f"_{window}")
            family = family.removeprefix("d2025_").removeprefix("reverse_")
            declared_family = definition.get("family")
            if declared_family:
                family = declared_family
            record = {
                "definition_id": key, "candidate": candidate,
                "source_type": cfg.get("source_type", "daily"),
                "family": f"{cfg.get('source_type', 'daily')}:{family}",
                "family_basis": "declared_mechanism_family" if declared_family else "mechanism_name_without_window_or_direction_alias",
                "window": window, "direction": definition.get("direction", "UNSPECIFIED"),
                "definition": json.dumps(definition, ensure_ascii=False, sort_keys=True),
                "plan_path": str(path), "source_run": path.parent.name,
                "evaluation_start": cfg.get("evaluation_start", ""),
                "evaluation_end": cfg.get("as_of", ""),
                "created_utc": plan.get("created_utc", ""),
                "screens_version": cfg.get("screens_version", "legacy_360"),
            }
            if key not in definitions or record["created_utc"] > definitions[key]["created_utc"]:
                definitions[key] = record
    return definitions


def external_evidence(run):
    """Import reviewed external8; rejected singleton designs remain invalid."""
    plan = json.loads((run / "PLAN.json").read_text())
    cfg = plan["config"]
    if cfg.get("groups") != GROUPS or (cfg.get("entry_lag"), cfg.get("horizon")) != (2, 5):
        raise ValueError("external run outside inventory scope")
    review = json.loads((run / "MASTER_VERDICT.json").read_text())
    leak = json.loads((run / "future_leak_check.json").read_text())
    if not leak.get("all_pass") or not review.get("signal_before_entry_before_exit_verified"):
        raise ValueError("external run timing not verified")
    screens = cfg["screens"]
    annual = defaultdict(dict)
    annual_path = run / "yearly.csv"
    if annual_path.exists():
        with annual_path.open() as handle:
            for item in csv.DictReader(handle):
                for metric in ("n", "ic_mean", "ic_hac_t", "ic_block_t"):
                    annual[item["candidate"]][f'y{item["year"]}_{metric}'] = item.get(metric, "")
    with (run / "summary.csv").open() as handle:
        for original in csv.DictReader(handle):
            row = {"full_" + k: v for k, v in original.items()}
            row.update(annual[original["candidate"]])
            checks = [("n", "min_days"), ("ic_mean", "min_ic"), ("ic_hac_t", "min_ic_hac_t"),
                      ("ic_block_t", "min_ic_block_t"), ("positive_years", "min_positive_years")]
            passed = all(number(original, k) is not None and number(original, k) >= screens[t] for k, t in checks)
            passed &= yes(original.get("all_eligible_years_positive"))
            passed &= number(original, "min_leave_group_ic") is not None and number(original, "min_leave_group_ic") > 0
            row.update({
                "definition_id": semantic_id(cfg, original["candidate"]), "candidate": original["candidate"],
                "source_run": str(run), "evidence_policy": "PRIOR_DIRECTION_FULL_WINDOW",
                "source_label_artifact_matches": "True", "historical_metrics_pass": str(passed),
                "data_quality_status": "DESIGN_REJECTED_SINGLETON_COMPARABILITY" if original["candidate"] in review["design_rejected"] else "CLEAN_FOR_CURRENT_REJUDGE",
                "import_source_summary": str(run / "summary.csv"),
            })
            yield row


def registration_index(runs, external_runs):
    """Link implementation-version budget entries to semantic inventory records."""
    entries = {}
    for path in sorted(runs.glob("*/PLAN.json")):
        plan = json.loads(path.read_text())
        if plan["config"].get("groups") != GROUPS:
            continue
        if plan["config"].get("rejudge_of"):
            path = runs / plan["config"]["rejudge_of"] / "PLAN.json"
            plan = json.loads(path.read_text())
        cfg = plan["config"]
        kind = cfg.get("source_type", "daily")
        filename = (Path(cfg["candidate_module"]).name if kind == "autoresearch" else
                    {"daily": "etf_group_discovery.py", "daily_mechanisms": "etf_group_daily_mechanisms.py",
                    "daily_rounds": "etf_group_daily_rounds.py", "daily_outcome": "etf_group_daily_outcome.py",
                    "claude_rounds": "etf_group_claude_rounds.py",
                    "auxiliary_bond": "etf_group_aux_bond.py",
                    "us_index": "etf_group_us_index.py",
                    "us_sector": "etf_group_us_sector.py",
                    "us_vix": "etf_group_us_vix.py",
                    "us_style": "etf_group_us_style.py",
                    "ext_gold": "etf_group_ext_gold.py",
                    "ext_copper": "etf_group_ext_copper.py",
                    "ext_crude": "etf_group_ext_crude.py",
                    "ext_cnh": "etf_group_ext_cnh.py",
                    "ext_hktech": "etf_group_ext_hktech.py",
                    "ext_realrate": "etf_group_ext_realrate.py",
                    "ext_coal": "etf_group_ext_coal.py",
                    "domestic_benchmark": "etf_group_domestic_benchmark.py",
                    "interaction": "etf_group_interactions.py"}.get(kind, "etf_group_sources.py"))
        code_hash = next(v for k, v in plan["source_hashes"].items() if Path(k).name == filename)
        if kind == "claude_rounds":
            window_mechanism_pairs = [(d["window"], m, d) for m, d in cfg["mechanisms"].items()]
        else:
            window_mechanism_pairs = [(w, m, d) for w in cfg["windows"] for m, d in cfg["mechanisms"].items()]
        for window, mechanism, definition in window_mechanism_pairs:
            extra = ([{"parent_run": definition["parent_run"], "parent_candidate": definition["parent_candidate"]}]
                     if kind == "self_state" else [definition["left"], definition["right"]] if kind == "interaction" else [])
            key = json.dumps([kind, mechanism, window, definition["direction"], code_hash, "mean_raw_same_units"] + extra, sort_keys=True)
            candidate = mechanism if kind in ("daily_outcome", "autoresearch") else f"{mechanism}_{window}"
            entries[key] = {"registration_id": hashlib.sha256(key.encode()).hexdigest(),
                            "definition_id": semantic_id(cfg, candidate), "candidate": candidate,
                                "plan": str(path), "kind": "MAIN_ENTRY", "code_sha256": code_hash}
    for run in external_runs:
        plan = json.loads((run / "PLAN.json").read_text())
        for candidate in plan["candidate_ids"]:
            key = "EXTERNAL:" + semantic_id(plan["config"], candidate)
            entries[key] = {"registration_id": key, "definition_id": key.removeprefix("EXTERNAL:"),
                            "candidate": candidate, "plan": str(run / "PLAN.json"), "kind": "EXTERNAL", "code_sha256": "SEE_PLAN"}
    return list(entries.values())


def build_records(summary, runs, external_runs=(), structural_rejections=()):
    definitions = planned_definitions(runs, [p / "PLAN.json" for p in external_runs] + list(structural_rejections))
    with summary.open() as handle:
        evidence = list(csv.DictReader(handle))
    if len({r["definition_id"] for r in evidence}) != len(evidence):
        raise ValueError("duplicate semantic definitions in summary")
    saved = {r["definition_id"]: r for r in evidence}
    for run in external_runs:
        for row in external_evidence(run):
            if row["definition_id"] in saved:
                raise ValueError("external run duplicates main evidence")
            saved[row["definition_id"]] = row
    structural_by_key = {}
    for path in structural_rejections:
        payload = json.loads(path.read_text())
        cfg = payload.get("config", {})
        if cfg.get("groups") != GROUPS:
            continue
        for candidate, details in payload.get("rejections", {}).items():
            key = semantic_id(cfg, candidate)
            structural_by_key[key] = {"structural_rejection": json.dumps(details, sort_keys=True), "structural_rejection_path": str(path)}
            saved.setdefault(key, {"definition_id": key, "candidate": candidate,
                                   "data_quality_status": "STRUCTURAL_PRECHECK_REJECTED",
                                   "source_label_artifact_matches": "False", "evidence_policy": ""})
    records = []
    for key in sorted(set(definitions) | set(saved)):
        row = saved.get(key, {})
        record = definitions.get(key, {
            "definition_id": key, "candidate": row.get("candidate", "UNMAPPED"),
            "family": "UNMAPPED", "family_basis": "UNMAPPED",
        }).copy()
        row = {**row, "_screens_version": record.get("screens_version", "legacy_360")}
        state, reason = classify(row)
        precheck_reason = ""
        if key in structural_by_key and row.get("data_quality_status") == "STRUCTURAL_PRECHECK_REJECTED":
            state = "PENDING"
            precheck_reason = "PRECHECK_" + str(json.loads(structural_by_key[key]["structural_rejection"]).get("reason", "REJECTED"))
            reason = precheck_reason
        prefix, _, surface = POLICIES.get(row.get("evidence_policy"), ("y2025", 0, "direction discovery / unresolved"))
        directional, directional_reason = descriptive_classification(row)
        if precheck_reason:
            directional_reason = precheck_reason
        ic_num = number(row, prefix + "_ic_mean")
        n_num = number(row, prefix + "_n")
        directional_valid = directional != "UNCOMPUTABLE"
        stability = {k: v for k, v in row.items() if k.startswith(("y2025_", "y2026_"))
                     or any(token in k.lower() for token in ("stability", "year", "leave_group", "loso"))}
        definition = json.loads(record.get("definition", "{}"))
        record.update({
            "status": state, "reason": reason, "surface": surface,
            "directional_classification": directional,
            "directional_reason": directional_reason,
            "signed_ic": row.get(prefix + "_ic_mean", "") if directional_valid else "",
            "ic_sign": ("positive" if ic_num > 0 else "negative" if ic_num < 0 else "zero") if directional_valid and ic_num is not None else "",
            "coverage_status": "SUFFICIENT" if n_num is not None and n_num >= policy_minimum(
                row, POLICIES.get(row.get("evidence_policy"), (None, 10**9, None))) else "INSUFFICIENT",
            "stability_diagnostics": json.dumps(stability, sort_keys=True),
            **{f"y{year}_{metric}": row.get(f"y{year}_{metric}", "")
               for year in (2025, 2026) for metric in ("n", "ic_mean", "ic_hac_t", "ic_block_t")},
            "min_leave_group_ic": row.get(prefix + "_min_loso_ic", row.get(prefix + "_min_leave_group_ic", "")),
            "ic_window_start": "2026-01-01" if prefix == "y2026" else record.get("evaluation_start", ""),
            "label_exit_cutoff": record.get("evaluation_end", ""),
            "y2025_role": "DIRECTION_SELECTION_ONLY" if prefix == "y2026" else "SEEN_HISTORY_DIAGNOSTIC",
            "y2026_role": "SEEN_HISTORY_NOT_INDEPENDENT_CONFIRMATION",
            "formula": definition.get("raw_formula", "SEE_SAVED_SOURCE"),
            "hypothesis": definition.get("hypothesis", "NOT_RECORDED"),
            "basic_screen_status": state,
            "evidence_policy": row.get("evidence_policy", ""),
            "ic": row.get(prefix + "_ic_mean", ""),
            "hac_t": row.get(prefix + "_ic_hac_t", ""),
            "block_t": row.get(prefix + "_ic_block_t", ""),
            "n": row.get(prefix + "_n", ""),
            "evidence_source_run": row.get("source_run", ""),
            "source_summary": row.get("import_source_summary", str(summary)),
            "data_quality": row.get("data_quality_status", ""),
            "paired_increment_pass_diagnostic": row.get("paired_increment_pass", ""),
            "legacy_factor_evidence_pass": row.get("factor_evidence_pass", ""),
            **structural_by_key.get(key, {}),
            "retry_same_definition": "NO_NEW_INFORMATION_NO_RERUN" if state != "PENDING" else "RESOLVE_REASON_FIRST",
        })
        records.append(record)
    return records


def write_csv(path, rows, fields):
    with path.open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runtime_outputs/etf_rotation_research/runs")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--external-run", type=Path, action="append", default=[])
    parser.add_argument("--structural-rejection", type=Path, action="append", default=[])
    args = parser.parse_args()
    records = build_records(args.summary, args.runs_root, args.external_run, args.structural_rejection)
    registrations = registration_index(args.runs_root, args.external_run)
    indexed = {r["definition_id"] for r in records}
    unlinked = [r for r in registrations if r["definition_id"] not in indexed]
    if not records:
        raise ValueError("no definitions")
    verdict_path = args.summary.parent / "verdict.json"
    verdict = json.loads(verdict_path.read_text()) if verdict_path.exists() else {}
    registered = verdict.get("conditionally_registered_definitions")
    if registered != len(registrations) or unlinked:
        raise ValueError(f"inventory registration mismatch: summary budget={registered}, "
                         f"ledger={len(registrations)}, unlinked={len(unlinked)}; "
                         "use a current full summary with the actual registered budget")
    # Never overwrite an earlier handoff snapshot.
    args.output.mkdir(parents=True, exist_ok=False)
    fields = sorted({k for row in records for k in row})
    write_csv(args.output / "all_factors.csv", records, fields)
    if registrations:
        write_csv(args.output / "registrations.csv", registrations, list(registrations[0]))
    counts = Counter(r["status"] for r in records)
    directional_counts = Counter({state: 0 for state in ("POSITIVE_IC", "NEGATIVE_IC", "NEAR_ZERO", "UNCOMPUTABLE")})
    directional_counts.update(r["directional_classification"] for r in records)
    for state in ("HAS_IC", "NO_IC", "PENDING"):
        write_csv(args.output / f"{state.lower()}.csv", [r for r in records if r["status"] == state], fields)
    write_csv(args.output / "basic_ic_leads.csv", sorted(
        [r for r in records if r["status"] == "HAS_IC"], key=lambda r: float(r["hac_t"]), reverse=True), fields)
    for state, filename in (("POSITIVE_IC", "positive_ic.csv"), ("NEGATIVE_IC", "negative_ic.csv"),
                            ("NEAR_ZERO", "near_zero.csv"), ("UNCOMPUTABLE", "uncomputable.csv")):
        write_csv(args.output / filename, [r for r in records if r["directional_classification"] == state], fields)
    reverse = [r for r in records if r["directional_classification"] == "NEGATIVE_IC"
               and number({"x": r.get("hac_t")}, "x") is not None and float(r["hac_t"]) <= -2
               and number({"x": r.get("block_t")}, "x") is not None and float(r["block_t"]) <= -2]
    write_csv(args.output / "reverse_watch.csv", reverse, fields)
    families = defaultdict(Counter)
    for row in records:
        families[row["family"]][row["status"]] += 1
        families[row["family"]][row["directional_classification"]] += 1
    family_rows = []
    for family, count in sorted(families.items()):
        family_rows.append({
            "family": family, "tested_definitions": count["HAS_IC"] + count["NO_IC"] + count["PENDING"],
            "indexed_definitions": sum(count[s] for s in ("HAS_IC", "NO_IC", "PENDING")),
            "computable_definitions": sum(count[s] for s in ("POSITIVE_IC", "NEGATIVE_IC", "NEAR_ZERO")),
            "has_ic": count["HAS_IC"], "no_ic": count["NO_IC"], "pending": count["PENDING"],
            "positive_ic": count["POSITIVE_IC"],
            "negative_ic": count["NEGATIVE_IC"],
            "near_zero": count["NEAR_ZERO"],
            "uncomputable": count["UNCOMPUTABLE"],
            "action": "HAS_LEADS" if count["HAS_IC"] else (
                "INCOMPLETE_EVIDENCE" if count["PENDING"] else "DO_NOT_REPEAT_TESTED_VARIANTS_WITHOUT_NEW_INFORMATION"),
            "legacy_action": "HAS_LEADS" if count["HAS_IC"] else (
                "INCOMPLETE_EVIDENCE" if count["PENDING"] else "DO_NOT_REPEAT_TESTED_VARIANTS_WITHOUT_NEW_INFORMATION"),
            "directional_action": "HAS_DIRECTIONAL_LEADS" if (count["POSITIVE_IC"] or count["NEGATIVE_IC"]) else "NO_DIRECTIONAL_LEAD",
        })
    write_csv(args.output / "families.csv", family_rows, list(family_rows[0]))
    manifest = {
        "schema_version": "ic_inventory_v4", "counts": dict(counts),
        "primary_classification": "directional_classification",
        "basic_ic_leads_file": "basic_ic_leads.csv",
        "directional_counts": dict(directional_counts),
        "legacy_screen_counts": dict(counts),
        "indexed_definitions": len(records), "registered_budget_count": registered,
        "linked_registration_count": len(registrations) - len(unlinked),
        "unlinked_registration_count": len(unlinked),
        "unreconciled_registered_count": registered - len(registrations) if registered is not None else None,
        "registration_minus_index_count": len(registrations) - len(records),
        "identity_note": "budget counts implementation-version attempts; inventory joins semantic definitions. Counts need not match.",
        "external_runs": [str(p) for p in args.external_run],
        "structural_rejections": [str(p) for p in args.structural_rejection],
        "source_summary": str(args.summary),
        "source_sha256": hashlib.sha256(args.summary.read_bytes()).hexdigest(),
        "additional_source_hashes": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for run in args.external_run
            for path in [run / "PLAN.json", run / "summary.csv", run / "MASTER_VERDICT.json", run / "future_leak_check.json", run / "yearly.csv"]
            if path.exists()
        },
        "structural_rejection_hashes": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in args.structural_rejection},
        "command": [sys.executable, *sys.argv],
        "scope": "fixed14/eight_groups; close(D); open(D+2)->open(D+7); seen history",
        "classification": "descriptive signed IC bands at absolute 0.01; display reference only, coverage annotated separately; legacy basic screen retained separately",
        "family_scope": "mechanism-name grouping, not proof that an entire economic family is exhausted",
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (args.output / "README.md").write_text(
        "# ETF IC 因子库\n\n"
        f"已索引 {len(records)} 条：正向IC {directional_counts['POSITIVE_IC']}，负向IC {directional_counts['NEGATIVE_IC']}，近零 {directional_counts['NEAR_ZERO']}，不可计算 {directional_counts['UNCOMPUTABLE']}。\n\n"
        "主描述视图：positive_ic.csv / negative_ic.csv / near_zero.csv / uncomputable.csv；reverse_watch.csv 保留既有 IC≤-0.01、HAC t≤-2 且块t≤-2 诊断。\n"
        "has_ic.csv / no_ic.csv 是兼容性视图，按 legacy screen_pass/fail 分类；pending.csv 保留旧待判分类。\n\n"
        "basic_ic_leads.csv 是基础筛选线索入口，列出IC、HAC/块t、n、两年诊断、评价面和公式；按t排序仅供浏览，不代表不同评价面可直接比较。\n"
        "y2025_role区分定方向年份与历史诊断；缺失的分年指标留空，不填零。家族表indexed_definitions为索引数，computable_definitions为可计算描述IC数；旧tested_definitions仅为索引数兼容别名。\n"
        "绝对IC 0.01仅为显示分档参考，不是有效因子门槛。弱覆盖有限IC仍显示并标注覆盖不足，不代表有支持或认证。无效质量/标签/时序结果不输出可信signed_ic，但原始IC字段保留。\n"
        "家族按机制名归并；不重复已测变体，不据此永久封禁整个经济机制。弱正/负向IC均保留原值。\n"
        "登记预算按实现版本计数，因子库按语义定义归并；映射见registrations.csv，对账缺口见manifest。\n"
        "本快照由保存结果派生，未重跑行情，未覆盖历史结果。重判或新增批次后以新summary重建新快照。\n"
    )
    pointer = args.output.parent / "IC_INVENTORY_LATEST.json"
    pending_pointer = pointer.with_suffix(".tmp")
    pending_pointer.write_text(json.dumps({
        "snapshot": str(args.output.resolve()), "counts": dict(counts),
        "directional_counts": dict(directional_counts), "legacy_screen_counts": dict(counts),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "registered_budget_count": registered,
    }, ensure_ascii=False, indent=2) + "\n")
    pending_pointer.replace(pointer)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
