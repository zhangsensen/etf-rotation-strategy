#!/usr/bin/env python3
"""Freeze one adaptive ETF trial as a reviewable formal-discovery draft."""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))
from etf_strategy.core import etf_group_run_rules as rules
from etf_strategy.core import etf_group_autoresearch as adapter
from audit_etf_autoresearch_novelty import require_latest_inventory

CANDIDATE_RELPATH = Path("frameworks/etf_rotation/scripts/research/etf_autoresearch_candidate.py")
SCREEN = {**rules.FIXED_SCREENS, "min_days": 250}


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def prior_count(runs_root: Path) -> int:
    counts = []
    for path in runs_root.glob("*/PLAN.json"):
        plan = json.loads(path.read_text())
        count = plan.get("cumulative_registered_definitions")
        if type(count) is int:
            counts.append(count)
    if not counts:
        raise ValueError("persistent formal PLAN ledger is absent")
    return max(counts)


def build_config(result: dict, module_path: str, prior: int,
                 source_description: str = "one immutable candidate module copied from the local git experiment commit") -> dict:
    candidate = result["candidate"]
    if (not re.fullmatch(r"autoresearch_[a-z0-9_]+", candidate)
            or result["direction"] not in (-1, 1)
            or result.get("status") != "SEEN_HISTORY_DISCOVERY_ONLY"
            or result.get("cold_cutoff") != "2026-03-24"):
        raise ValueError("trial does not match frozen adaptive ETF scope")
    config = {
        "version": f"group_ic_{candidate}_{result['candidate_sha256'][:8]}",
        "status": "PROPOSED_NOT_APPROVED_NO_FORMAL_H5_LABELS_READ",
        "source_type": "autoresearch", "purpose": "seen_history_discovery_only",
        "campaign_extension": True, "discovery_surface": "IC_DISCOVERY_ONLY",
        "screens_version": "cold_250_v1",
        "evidence_policy": "SEEN_2026_ADAPTIVE_NOT_CONFIRMATION",
        "data_root": str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"),
        "as_of": "2026-03-24", "start": "2023-07-27", "evaluation_start": "2025-01-01",
        "groups": "frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml",
        "universe": "config/etf_rotation_universe_v1.json", "calendar_symbol": "510300.SH",
        "candidate_module": module_path, "candidate_sha256": result["candidate_sha256"],
        "entry_lag": 2, "horizon": 5, "top_k": 2, "warmup": 60,
        "hac_lag": 10, "max_leads": 1,
        "external_registered_definitions": 8, "prior_registered": prior,
        "new_definitions": 1, "budget_cap": prior + 1,
        "windows": [1], "screens": SCREEN,
        "mechanisms": {candidate: {
            "direction": result["direction"], "family": result["family"],
            "hypothesis": result["description"], "raw_formula": result["description"],
        }},
        "notes": {
            "selection": "adaptive code iteration on already seen 2025+ IC; no independent historical holdout",
            "source": source_description,
            "confirmation": "monthly forward process remains separate",
        },
    }
    rules.validate_ic_discovery_config(config)
    if rules.candidate_ids(config) != [candidate]:
        raise ValueError("promoted candidate id changed")
    return config


def prepare(run_dir: Path, commit: str | None, runs_root: Path, inventory: Path,
            source_snapshot: Path | None = None) -> dict:
    if (commit is None) == (source_snapshot is None):
        raise ValueError("provide exactly one of an experiment commit or source snapshot")
    if commit is not None and not re.fullmatch(r"[0-9a-f]{7,40}", commit):
        raise ValueError("experiment commit must be a git hash")
    require_latest_inventory(inventory, runs_root)
    result = json.loads((run_dir / "result.json").read_text())
    input_profile = result.get("input_profile", "daily")
    if input_profile != "daily":
        raise ValueError(
            f"formal promotion is unavailable for input profile {input_profile!r}; "
            "formal runner does not yet record and reproduce the trial input manifest"
        )
    novelty = json.loads((run_dir / "novelty.json").read_text())
    decision = json.loads((run_dir / "decision.json").read_text())
    if (decision.get("candidate") != result.get("candidate")
            or decision.get("decision") != "positive_ic_review"):
        raise ValueError("trial has no positive IC review record")
    if novelty.get("scope") != "score overlap only; no IC labels read":
        raise ValueError("full old-score novelty audit is missing")
    if Path(novelty["inventory"]).resolve() != inventory.resolve():
        raise ValueError("reviewed inventory differs from novelty audit")
    if source_snapshot is not None:
        source_snapshot = Path(source_snapshot)
        if source_snapshot.is_symlink() or not source_snapshot.is_file():
            raise FileNotFoundError("candidate source snapshot is missing or symlinked")
        source_snapshot = source_snapshot.resolve()
        raw = source_snapshot.read_bytes()
        source_description = f"immutable candidate source snapshot {source_snapshot}"
    else:
        raw = subprocess.run(["git", "show", f"{commit}:{CANDIDATE_RELPATH}"],
                             cwd=ROOT, check=True, capture_output=True).stdout
        source_description = f"immutable candidate module copied from git experiment commit {commit}"
    if sha256(raw).hexdigest() != result["candidate_sha256"]:
        raise ValueError("candidate source bytes differ from evaluated trial hash")
    count = prior_count(runs_root)
    safe = result["candidate"]
    filename = f"{safe}_{result['candidate_sha256'][:12]}.py"
    module_relative = adapter.FROZEN / filename
    module_path = ROOT / module_relative
    config = build_config(result, str(module_relative), count, source_description)
    if decision.get("parent"):
        config["notes"]["parent_factor"] = decision["parent"]
    config_path = ETF / "configs" / f"{config['version']}.yaml"
    if module_path.exists() or config_path.exists():
        raise FileExistsError("frozen source or config already exists")
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_bytes(raw)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    adapter.frozen_source(config)
    attempts_file = run_dir.parent / "results.tsv"
    with attempts_file.open(newline="") as handle:
        attempts = list(csv.DictReader(handle, delimiter="\t"))
    attempt_ids = {row["run_id"] for row in attempts}
    attempt_ids.update(path.stem for path in (run_dir.parent / "attempts").glob("*.json"))
    packet = {
        "status": "REVIEW_REQUIRED_NO_FORMAL_REGISTRATION",
        "candidate": safe, "trial_run": str(run_dir),
        "git_commit": commit, "source_snapshot": str(source_snapshot) if source_snapshot else None,
        "input_profile": input_profile,
        "known_local_attempt_rows": len(attempt_ids), "global_search_count_known": False,
        "trial_result": result, "novelty": novelty,
        "parent": decision.get("parent"),
        "nearest_overlap": novelty["nearest"][0] if novelty["nearest"] else None,
        "frozen_module": str(module_relative), "frozen_module_sha256": sha(module_path),
        "config": str(config_path.relative_to(ROOT)), "config_sha256": sha(config_path),
        "inventory": str(inventory), "inventory_sha256": sha(inventory),
        "prior_registered_draft": count, "budget_cap_draft": count + 1,
        "next_step": "master reviews draft, refreshes prior count if ledger advanced, then issues the existing source-hash-bound approval and runs discover_etf_groups.py once",
        "command": [sys.executable, *sys.argv],
    }
    (run_dir / "promotion_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    return packet


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--commit")
    source.add_argument("--source-snapshot", type=Path)
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.run_dir, args.commit, args.runs_root, args.inventory,
                             args.source_snapshot), ensure_ascii=False))
