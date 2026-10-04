"""Cross-lane hypothesis-budget reservation for ETF mining."""

from __future__ import annotations

import fcntl
import hashlib
import json
import re
from pathlib import Path


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_plan_seal(plan_path: Path) -> Path:
    """Seal the final PLAN after wrapper metadata hooks return."""
    seal_path = plan_path.with_suffix(".sha256")
    seal_path.write_text(file_sha256(plan_path) + "\n")
    return seal_path


def verify_plan_seal(plan_path: Path) -> bool:
    seal_path = plan_path.with_suffix(".sha256")
    return bool(
        seal_path.exists()
        and seal_path.read_text().strip() == file_sha256(plan_path)
    )


def canonical_plan_count(output_roots: tuple[Path, ...]) -> int:
    total = 0
    seen_plans: set[Path] = set()
    for root in output_roots:
        for plan_path in root.glob("round_*/PLAN.json"):
            if not re.fullmatch(r"round_\d+", plan_path.parent.name):
                continue
            # A research lane may link prior PLANs into its workspace so the
            # novelty checks see the full history.  Overlapping campaign roots
            # must not reserve the same physical hypothesis batch twice.
            physical_plan = plan_path.resolve()
            if physical_plan in seen_plans:
                continue
            seen_plans.add(physical_plan)
            total += len(json.loads(plan_path.read_text()).get("candidates", []))
    return total


def canonical_expression_hashes(output_roots: tuple[Path, ...]) -> set[str]:
    hashes: set[str] = set()
    for root in output_roots:
        for plan_path in root.glob("round_*/PLAN.json"):
            if not re.fullmatch(r"round_\d+", plan_path.parent.name):
                continue
            plan = json.loads(plan_path.read_text())
            hashes.update(str(value) for value in plan.get("expression_hashes", {}).values())
    return hashes


def write_plan_with_budget(
    plan_path: Path,
    plan: dict,
    *,
    output_roots: tuple[Path, ...],
    lock_path: Path,
    budget: int,
) -> int:
    """Atomically count both lanes, reserve tests, and write one immutable plan."""
    if budget < 1:
        raise ValueError("budget must be positive")
    if not any(plan_path.is_relative_to(root) for root in output_roots):
        raise ValueError(f"PLAN path is outside campaign roots: {plan_path}")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        used = canonical_plan_count(output_roots)
        planned = len(plan.get("candidates", []))
        planned_hashes = [str(value) for value in plan.get("expression_hashes", {}).values()]
        if len(planned_hashes) != len(set(planned_hashes)):
            raise RuntimeError("duplicate expression hashes inside PLAN")
        overlap = canonical_expression_hashes(output_roots).intersection(planned_hashes)
        if overlap:
            raise RuntimeError(f"campaign expression already planned: {sorted(overlap)}")
        if used + planned > budget:
            raise RuntimeError(
                f"campaign budget exceeded: used={used} planned={planned} budget={budget}"
            )
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))
        return used + planned
