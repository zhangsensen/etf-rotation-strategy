"""Persistent local index for adaptive ETF autoresearch trials.

This is a read-only indexer: it reads saved trials and formal definition
summaries, then atomically writes a separate library under ``output_root``.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any


def _read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _number(value: Any) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _sha(path: Path | None) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest() if path and path.is_file() else None
    except OSError:
        return None


def _atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _resolve_code(value: Any, root: Path) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    # Paths in campaign summaries are often cwd-relative (already include
    # output_root); root-relative is the fallback for compact manifests.
    if path.is_file():
        return path.resolve()
    candidate = root / path
    return candidate.resolve() if candidate.is_file() else candidate


def _classify(ic: float | None) -> str:
    if ic is None:
        return "UNCOMPUTABLE"
    if ic >= 0.01:
        return "POSITIVE_IC"
    if ic <= -0.01:
        return "NEGATIVE_IC"
    return "NEAR_ZERO"


def _novelty_label(nearest: Any, supplied: Any) -> Any:
    corr = _number(nearest.get("mean_abs_daily_rank_corr")) if isinstance(nearest, dict) else None
    if corr is None:
        return supplied
    if corr >= 1.0 - 1e-10:
        return "EXACT_RANK_DUPLICATE"
    if corr >= 0.7:
        return "HIGH_SCORE_OVERLAP"
    return "NO_HIGH_OVERLAP"


def _formal_rows(path: Path) -> list[dict]:
    """Read definition metadata only; deliberately discard all result metrics."""
    sources = [path] if path.is_file() else [path / "positive_ic.csv", path / "negative_ic.csv",
              path / "near_zero.csv", path / "uncomputable.csv", path / "basic_ic_leads.csv"]
    rows: dict[tuple[str, str], dict] = {}
    for source in sources:
        if not source.is_file() or source.suffix.lower() != ".csv":
            continue
        try:
            with source.open(encoding="utf-8-sig", newline="") as stream:
                for row in csv.DictReader(stream):
                    candidate = row.get("candidate") or row.get("candidate_id")
                    if not candidate:
                        continue
                    family = row.get("family") or row.get("mechanism") or ""
                    rows[(str(candidate), str(row.get("definition_id", "")))] = {
                        "candidate": str(candidate), "family": str(family),
                        "definition_id": row.get("definition_id"),
                        "description": row.get("description") or row.get("formula") or row.get("definition"),
                        "raw_formula": row.get("raw_formula") or row.get("formula"),
                        "hypothesis": row.get("hypothesis"),
                        "source_type": row.get("source_type"), "source_run": row.get("source_run"),
                        "evidence_policy": row.get("evidence_policy"),
                    }
        except OSError:
            continue
    if path.is_file() and path.suffix.lower() == ".json":
        payload = _read(path)
        candidates = payload.get("records", payload.get("candidates", [])) if isinstance(payload, dict) else []
        for row in candidates if isinstance(candidates, list) else []:
            if isinstance(row, dict) and row.get("candidate"):
                rows[(str(row["candidate"]), str(row.get("definition_id", "")))] = {
                    key: row.get(key) for key in ("candidate", "family", "definition_id", "description", "formula", "raw_formula", "hypothesis", "source_type", "source_run", "evidence_policy")
                }
    return list(rows.values())


def _local_trials(root: Path) -> list[dict]:
    by_run: dict[str, dict] = {}
    # Campaign rounds contain proposal metadata, source snapshots, and often
    # fail before a result directory can be created.
    for summary_path in sorted((root / "campaigns").glob("*/summary.json")):
        summary = _read(summary_path)
        if not isinstance(summary, dict):
            continue
        campaign = summary.get("campaign_id", summary_path.parent.name)
        for item in summary.get("rounds", []):
            if not isinstance(item, dict):
                continue
            run_id = str(item.get("run_id") or f"{campaign}_r{item.get('round', '')}")
            source_value = item.get("source_path")
            code = _resolve_code(source_value, root) if source_value else (summary_path.parent / f"r{int(item['round']):02d}" / "candidate.py" if str(item.get("round", "")).isdigit() else None)
            if code is None or not code.is_file():
                code = summary_path.parent / f"r{item.get('round')}" / "candidate.py"
            row = {"run_id": run_id, "campaign_id": campaign, "status": item.get("status", "UNKNOWN"),
                   "evaluation_status": "EVALUATED" if _number(item.get("ic")) is not None else None,
                   "candidate": item.get("candidate"), "family": item.get("family"), "planned_family": item.get("planned_family"),
                   "canonical_family": item.get("canonical_family"),
                   **{key: (item.get("family_plan") or {}).get(key) for key in
                      ("formula", "direction", "mechanism", "required_panels", "search_focus", "novelty_basis", "new_information")},
                   "parent_run": item.get("parent_run"), "parent_candidate": item.get("parent_candidate", summary.get("parent_candidate")),
                   "parent_sha256": item.get("parent_sha256"), "ic": _number(item.get("ic")),
                   "hac_t": _number(item.get("hac_t")), "n": item.get("n"),
                   "yearly": item.get("yearly"), "error_type": item.get("error_type"),
                   "error": item.get("error"), "reason": item.get("reason"),
                   "mode": item.get("mode"), "input_profile": item.get("input_profile"),
                   "keep": item.get("keep"), "is_reference": False,
                   "parent_replaced": item.get("parent_replaced", item.get("mode") == "refine" and item.get("keep") is True),
                   "reason_code": item.get("reason_code"), "repairable": item.get("repairable"),
                   "outcome_opened": item.get("outcome_opened"), "revisions": item.get("revisions"),
                   "code_path": str(code) if code and code.is_file() else None,
                   "source_sha256": item.get("candidate_sha256") or _sha(code), "source": "campaign",
                   "duplicate_of": item.get("duplicate_of"),
                   "score_sha256": item.get("score_sha256"),
                   "score_preflight_path": item.get("score_preflight_path"),
                   "nearest": item.get("nearest"),
                   "novelty_diagnostic": _novelty_label(item.get("nearest"), item.get("novelty_diagnostic"))}
            _add(by_run, row)

    # Standalone cycles: root/run_id/result.json plus decision.json; attempts
    # records preserve failures that happen before a result directory exists.
    for result_path in sorted(root.glob("*/result.json")):
        if result_path.parent.name in {"library", "attempts"} or result_path.parent.parent != root:
            continue
        result = _read(result_path)
        if not isinstance(result, dict):
            continue
        reference = (result_path.parent / "reference_seed.json").is_file()
        run_id = str(result.get("run_id", result_path.parent.name))
        decision = _read(result_path.parent / "decision.json") or {}
        source_value = result.get("code_path") or result.get("source_path")
        code = _resolve_code(source_value, root)
        attempt = _read(root / "attempts" / f"{run_id}.json") or {}
        pipeline_status = attempt.get("status")
        row = {"run_id": run_id, "status": pipeline_status if pipeline_status in {"FAILED", "REJECTED", "DUPLICATE", "DIVERSITY_SKIPPED"} else "EVALUATED",
               "evaluation_status": "EVALUATED", "candidate": result.get("candidate"),
               "family": result.get("family"), "parent_run": (decision.get("parent") or {}).get("source_run") if isinstance(decision.get("parent"), dict) else None,
               "parent_candidate": (decision.get("parent") or {}).get("candidate") if isinstance(decision.get("parent"), dict) else None,
               "ic": _number(result.get("ic")), "hac_t": _number(result.get("hac_t")), "n": result.get("n"),
               "yearly": result.get("yearly") or result.get("yearly_metrics"),
               **{key: result.get(key) for key in ('direction', 'description', 'first_signal',
                   'last_signal', 'signal_time', 'entry', 'exit', 'cold_cutoff', 'block_t', 'command')},
               "result_path": str(result_path),
               "reason": decision.get("reason"), "decision": decision.get("decision"),
               "nearest": decision.get("nearest"),
               "novelty_diagnostic": _novelty_label(decision.get("nearest"), decision.get("novelty_diagnostic")),
               "code_path": str(code) if code and code.is_file() else None,
               "source_sha256": result.get("candidate_sha256") or _sha(code), "source": "cycle",
               "is_reference": reference}
        _add(by_run, row)
    for attempt_path in sorted((root / "attempts").glob("*.json")):
        attempt = _read(attempt_path)
        if not isinstance(attempt, dict) or not attempt.get("run_id"):
            continue
        run_id = str(attempt["run_id"])
        if run_id in by_run and by_run[run_id].get("status") == "COMPLETED":
            continue
        code = root / f"{run_id}" / "candidate.py"
        if not code.is_file():
            code = None
        _add(by_run, {"run_id": run_id, "status": attempt.get("status", "UNKNOWN"),
               "candidate": attempt.get("candidate"), "family": attempt.get("family"),
               "parent_run": None, "parent_candidate": None, "ic": None, "hac_t": None,
               "n": None, "yearly": None, "error_type": attempt.get("error_type"),
               "error": attempt.get("error"), "reason": attempt.get("stage"),
               "code_path": str(code) if code else None, "source_sha256": _sha(code), "source": "attempt"})
    return sorted(by_run.values(), key=lambda row: row["run_id"])


def _add(index: dict, row: dict) -> None:
    old = index.get(row["run_id"])
    # Prefer completed result evidence while retaining diagnostics from an
    # attempt/summary when the result is incomplete.
    if old:
        merged = {**old, **{k: v for k, v in row.items() if v is not None}}
        # A result artifact proves evaluation happened, not that downstream
        # novelty/comparison/decision stages succeeded.
        for candidate in (old, row):
            if candidate.get("status") in {"PAUSED_SYSTEM_ERROR", "FAILED", "REJECTED", "DUPLICATE", "DIVERSITY_SKIPPED"}:
                merged["status"] = candidate["status"]
                break
        else:
            # The campaign summary is the reviewed workflow record. A raw
            # result.json proves evaluation, but cannot erase its final status.
            if old.get("source") == "campaign":
                merged["status"] = old.get("status")
                merged["source"] = "campaign"
            elif row.get("status"):
                merged["status"] = row["status"]
        if old.get("evaluation_status") or row.get("evaluation_status"):
            merged["evaluation_status"] = "EVALUATED"
        index[row["run_id"]] = merged
    else:
        index[row["run_id"]] = row


def rebuild_library(output_root: Path, formal_inventory: Path) -> dict:
    """Rebuild output_root/library from saved trials and formal definitions."""
    root = Path(output_root)
    trials = _local_trials(root)
    for row in trials:
        current_hash = _sha(Path(row['code_path'])) if row.get('code_path') else None
        row['current_source_sha256'] = current_hash
        row['source_integrity'] = ('UNKNOWN' if not current_hash or not row.get('source_sha256') else
                                   'MATCH' if current_hash == row['source_sha256'] else 'MISMATCH')
        # An absent/unreadable source is not provenance. Keep its numeric IC
        # for audit, but only trust evidence whose exact saved SHA is present.
        row['evidence_valid'] = row['source_integrity'] == 'MATCH' and row.get('status') != 'PAUSED_SYSTEM_ERROR'
        row["ic_category"] = _classify(row.get("ic")) if row['evidence_valid'] else 'UNCOMPUTABLE'
        row["parent_replaced"] = bool(row.get("parent_replaced", False))
        row["ic_recorded"] = _number(row.get("ic")) is not None
        row["parent_eligible"] = (row.get("status") == "COMPLETED" and row.get("keep") is True
                                  and row.get("evaluation_status") == "EVALUATED"
                                  and row['evidence_valid']
                                  and not row.get("is_reference"))
    formal = _formal_rows(Path(formal_inventory))
    reference_count = sum(bool(row.get("is_reference")) for row in trials)
    local_trials = [row for row in trials if not row.get("is_reference")]
    payload = {"schema_version": "etf_autoresearch_library_v1", "local_trial_count": len(local_trials),
               "reference_count": reference_count,
               "formal_definition_count": len(formal), "formal_is_context_only": True,
               "local_trials": _json_safe(local_trials), "formal_definitions": formal}
    from collections import Counter
    payload['directional_counts'] = dict(Counter(row['ic_category'] for row in local_trials))
    payload['numeric_ic_count'] = sum(row['ic_recorded'] for row in local_trials)
    from etf_autoresearch_status import campaign_progress
    payload['campaign_progress'] = [
        {'campaign_id': p.parent.name, **campaign_progress(_read(p), p.parent)}
        for p in sorted((root / 'campaigns').glob('*/summary.json')) if isinstance(_read(p), dict)]
    library = root / "library"
    _atomic(library / "library.json", (json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode())
    columns = ["run_id", "campaign_id", "status", "candidate", "family", "canonical_family", "planned_family", "parent_run", "parent_candidate", "parent_sha256", "ic", "ic_category", "hac_t", "n", "yearly", "code_path", "source_sha256", "error_type", "error", "reason", "decision", "source", "mode", "input_profile", "keep", "parent_replaced", "ic_recorded", "reason_code", "repairable", "outcome_opened", "revisions", "is_reference", "nearest", "novelty_diagnostic"]
    columns += ['formula', 'direction', 'mechanism', 'required_panels', 'first_signal', 'last_signal',
                'signal_time', 'entry', 'exit', 'cold_cutoff', 'block_t', 'result_path', 'command',
                'source_integrity', 'current_source_sha256', 'evidence_valid']
    import io
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in local_trials:
        if row.get("is_reference"):
            continue
        writer.writerow({k: json.dumps(_json_safe(v), ensure_ascii=False, allow_nan=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    _atomic(library / "library.csv", stream.getvalue().encode("utf-8"))
    return {"library_json": library / "library.json", "library_csv": library / "library.csv",
            "local_trial_count": len(local_trials), "reference_count": reference_count,
            "formal_definition_count": len(formal)}


def context_for_proposer(output_root: Path, formal_inventory: Path) -> dict:
    """Return seen-history context; formal input contributes definitions only."""
    root = Path(output_root)
    trials = _local_trials(root)
    formal = _formal_rows(Path(formal_inventory))
    counts: dict[str, int] = {}
    for row in trials:
        if row.get("is_reference"):
            continue
        family = str(row.get("canonical_family") or row.get("family") or "(unknown)")
        counts[family] = counts.get(family, 0) + 1
    failures = [{k: row.get(k) for k in ("run_id", "candidate", "family", "status", "error_type", "error", "reason")}
                for row in trials if row.get("status") in {"FAILED", "REJECTED", "DUPLICATE", "DIVERSITY_SKIPPED"} or row.get("error")]
    completed = [{**{k: row.get(k) for k in ("run_id", "candidate", "family", "canonical_family", "ic", "hac_t", "n", "yearly", "code_path", "source_sha256", "parent_run", "parent_candidate", "mode", "input_profile", "keep", "nearest", "novelty_diagnostic")},
                  "parent_eligible": (row.get("status") == "COMPLETED" and row.get("keep") is True and row.get("evaluation_status") == "EVALUATED")}
                 for row in trials if row.get("ic") is not None and not row.get("is_reference")]
    return _json_safe({"local_family_trial_counts": counts, "recent_failures": failures[-20:],
                       "local_trial_definitions": [
                           {k: row.get(k) for k in ("run_id", "candidate", "family", "canonical_family",
                            "status", "input_profile", "formula", "direction", "mechanism", "required_panels", "search_focus",
                            "nearest", "duplicate_of", "reason_code")}
                           for row in trials if not row.get("is_reference")],
                       "historical_formal_definitions": formal,
                       "local_completed_candidates": completed})
