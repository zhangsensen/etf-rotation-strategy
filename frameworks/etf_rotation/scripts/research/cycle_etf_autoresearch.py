#!/usr/bin/env python3
"""One-command ETF autoresearch trial: fixed IC, full-library overlap, decision log."""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

import pandas as pd

from audit_etf_autoresearch_novelty import audit, read_prefix, require_latest_inventory
from run_etf_autoresearch_ic import CANDIDATE, ROOT, run
from etf_strategy.core.etf_rank_utils import stable_rank
from etf_autoresearch_recovery import atomic, seal_result


def compare(base_dir: Path, trial_dir: Path) -> dict:
    base = json.loads((base_dir / "result.json").read_text())
    trial = json.loads((trial_dir / "result.json").read_text())
    if (base["evaluator_sha256"] != trial["evaluator_sha256"]
            or base.get("implementation_sha256") != trial.get("implementation_sha256")
            or base.get("python_version") != trial.get("python_version")
            or base.get("pandas_version") != trial.get("pandas_version")
            or base.get("numpy_version") != trial.get("numpy_version")
            or base["input_sha256"] != trial["input_sha256"]
            or base["groups_sha256"] != trial["groups_sha256"]
            or base["universe_sha256"] != trial["universe_sha256"]):
        raise ValueError("baseline and trial do not share fixed evaluation inputs")
    if base.get("input_manifest", {"profile": "daily"}) != trial.get("input_manifest", {"profile": "daily"}):
        raise ValueError("baseline and trial have different input profiles or source hashes")
    left = pd.read_csv(base_dir / "daily_ic.csv", usecols=["signal_date", "ic"])
    right = pd.read_csv(trial_dir / "daily_ic.csv", usecols=["signal_date", "ic"])
    paired = left.merge(right, on="signal_date", suffixes=("_base", "_trial")).dropna()
    if paired.empty:
        raise ValueError("no common valid IC dates")
    return {"n": len(paired), "baseline_ic": float(paired.ic_base.mean()),
            "trial_ic": float(paired.ic_trial.mean()),
            "delta_ic": float((paired.ic_trial - paired.ic_base).mean())}


def choose(trial: dict, novelty: dict, paired: dict) -> tuple[str, str]:
    if not math.isfinite(trial["ic"]):
        return "uncomputable_ic", f"signed IC is not finite; n={trial['n']}"
    if trial["ic"] >= 0.01 and trial["n"] >= 250:
        return "positive_ic_review", f"signed IC={trial['ic']:.6f}; n={trial['n']}"
    if trial["ic"] > 0:
        return "weak_positive_ic", f"signed IC={trial['ic']:.6f}; n={trial['n']}"
    if trial["ic"] < 0:
        return "negative_ic_watch", f"signed IC={trial['ic']:.6f}; n={trial['n']}"
    return "zero_ic", f"signed IC={trial['ic']:.6f}; n={trial['n']}"


def validate_parent_seed(baseline: Path, inventory: Path, runs_root: Path,
                         parent_candidate: str) -> dict:
    """Prove a local frozen seed reproduces the chosen formal factor's ranks."""
    catalog = pd.read_csv(inventory)
    matches = catalog.loc[catalog["candidate"].eq(parent_candidate)]
    if len(matches) != 1:
        raise ValueError("parent candidate must identify exactly one formal definition")
    parent = matches.iloc[0]
    formal_path = runs_root / str(parent["source_run"]) / f"scores_{parent_candidate}.csv"
    seed = read_prefix(baseline / "group_scores.csv")
    formal = read_prefix(formal_path)
    if set(seed.columns) != set(formal.columns):
        raise ValueError("seed and formal parent group populations differ")
    formal = formal[seed.columns]
    dates = seed.index.intersection(formal.index)
    valid = seed.loc[dates].notna().all(axis=1) & formal.loc[dates].notna().all(axis=1)
    if valid.sum() < 40:
        raise ValueError("seed and formal parent lack common complete score dates")
    correlation = stable_rank(seed.loc[dates[valid]]).corrwith(
        stable_rank(formal.loc[dates[valid]]), axis=1).dropna()
    if len(correlation) < 40 or correlation.min() < 0.999999:
        raise ValueError("seed does not reproduce the signed ranks of its formal parent")
    return {"candidate": parent_candidate, "definition_id": str(parent["definition_id"]),
            "family": str(parent["family"]), "source_run": str(parent["source_run"]),
            "seed_common_days": len(correlation), "seed_min_rank_corr": float(correlation.min())}


def cycle(run_id: str, output_root: Path, baseline: Path | None,
          inventory: Path, runs_root: Path, parent_candidate: str | None = None,
          candidate_path: Path | None = None, input_profile: str = "daily") -> dict:
    if not run_id.replace("_", "").replace("-", "").isalnum():
        raise ValueError("run-id must be alphanumeric with underscores/hyphens")
    attempts = output_root / "attempts"
    attempts.mkdir(parents=True, exist_ok=True)
    attempt_path = attempts / f"{run_id}.json"
    if attempt_path.exists() or (output_root / run_id).exists():
        raise FileExistsError(f"experiment run id already exists: {run_id}")
    candidate_path = candidate_path or CANDIDATE
    if parent_candidate and baseline is None:
        raise ValueError('parent comparison requires its frozen baseline')
    attempt = {"run_id": run_id, "candidate_sha256": sha256(candidate_path.read_bytes()).hexdigest(),
               "source_path": str(candidate_path), "input_profile": input_profile,
               "status": "STARTED", "stage": "preflight"}
    atomic(attempt_path, attempt)
    try:
        require_latest_inventory(inventory, runs_root)
        parent = (validate_parent_seed(baseline, inventory, runs_root, parent_candidate)
                  if parent_candidate else None)
        attempt["parent"] = parent
        attempt["stage"] = "evaluation"
        atomic(attempt_path, attempt)
        trial = (run(run_id, output_root) if candidate_path == CANDIDATE and input_profile == "daily"
                 else run(run_id, output_root, candidate_path, input_profile))
        run_dir = output_root / run_id
        seal_result(run_dir)
        attempt["stage"] = "novelty"
        atomic(attempt_path, attempt)
        novelty = audit(run_dir, inventory, runs_root)
        require_latest_inventory(inventory, runs_root)
        attempt["stage"] = "comparison"
        atomic(attempt_path, attempt)
        paired = compare(baseline, run_dir) if baseline is not None else None
        decision, reason = choose(trial, novelty, paired)
        nearest = novelty["nearest"][0] if novelty["nearest"] else None
        record = {"run_id": run_id, "candidate": trial["candidate"],
                  "decision": decision, "reason": reason, "paired": paired,
                  "baseline": str(baseline) if baseline is not None else None, "parent": parent,
                  "ic": trial["ic"], "hac_t": trial["hac_t"], "n": trial["n"],
                  "nearest": nearest,
                  "novelty_diagnostic": ("HIGH_SCORE_OVERLAP" if nearest and
                                         nearest["mean_abs_daily_rank_corr"] >= 0.7
                                         else "NO_HIGH_OVERLAP_AMONG_COMPARABLE"),
                  "inventory": str(inventory), "formal_registration": False,
                  "evidence": "adaptive seen-history discovery only"}
        (run_dir / "decision.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        log = output_root / "decisions.tsv"
        if not log.exists():
            log.write_text("run_id\tcandidate\tdecision\tpaired_n\tpaired_delta_ic\treason\n")
        with log.open("a", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow([run_id, trial["candidate"], decision, paired['n'] if paired else '',
                             f'{paired["delta_ic"]:.9f}' if paired else '', reason])
        attempt.update({"status": "COMPLETED", "stage": "done", "decision": decision})
        return record
    except Exception as exc:
        attempt.update({"status": "FAILED", "error_type": type(exc).__name__,
                        "error": str(exc)})
        raise
    finally:
        atomic(attempt_path, attempt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-root", type=Path,
                        default=ROOT / "runtime_outputs/etf_autoresearch_ic")
    parser.add_argument("--baseline", type=Path, help="optional frozen parent comparison; open discovery needs no seed")
    parser.add_argument("--parent-candidate", help="formal factor whose signed ranks the frozen baseline must reproduce")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    print(json.dumps(cycle(args.run_id, args.output_root, args.baseline,
                           args.inventory, args.runs_root, args.parent_candidate), ensure_ascii=False))
