#!/usr/bin/env python3
"""Bounded agent proposal -> fixed ETF IC -> keep/revert discovery loop."""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import fcntl
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import signal
import sys

from etf_autoresearch_context import compact_proposal_context
from cycle_etf_autoresearch import compare, cycle
from run_etf_autoresearch_ic import CANDIDATE, ROOT


SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["rationale", "source_code"],
    "properties": {
        "rationale": {"type": "string"},
        "source_code": {"type": "string"},
    },
}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "__import__", "getattr",
                   "setattr", "globals", "locals", "vars", "input"}
ALLOWED_IMPORTS = {"pandas", "numpy", "math"}
UNSUPPORTED_SYNTAX = (ast.Global, ast.Nonlocal, ast.Delete, ast.With, ast.AsyncWith,
                      ast.Try, ast.Raise, ast.Lambda, ast.ClassDef, ast.Await, ast.Yield, ast.YieldFrom)
SCORE_CONTRACT = {
    "version": 1,
    "module_metadata": "The ONLY allowed top-level assignments are CANDIDATE_ID, FAMILY, DIRECTION, DESCRIPTION. "
                       "required_panels belongs to the frozen JSON plan, NOT a REQUIRED_PANELS Python assignment. "
                       "Put working constants inside score(panels).",
    "direction": "score(panels) returns the RAW economic measurement; evaluator multiplies by DIRECTION exactly once. "
                 "For a negative hypothesis return positive raw intensity and set DIRECTION=-1; do not negate it again in score.",
    "refinement": "Preserve the parent's EFFECTIVE mapping DIRECTION * parent.score, not just its DIRECTION constant. "
                  "A parent's RAW definition may itself be negative (e.g. selling pressure = -CLV). "
                  "Do not strip that minus while keeping DIRECTION unchanged. Explain the effective orientation in the rationale.",
    "shape": "Return a numeric DataFrame with exactly panels['close'].index and columns, including on each date prefix. "
             "Elementwise ETF operations must not reduce or concatenate across ETF columns into a single Series.",
    "unsupported_syntax": [node.__name__ for node in UNSUPPORTED_SYNTAX],
    "forbidden_calls": sorted(FORBIDDEN_CALLS),
    "implementation": "No raise/try/lambda or rolling.apply(lambda ...). Inputs are already DataFrames; "
                      "use numeric masks for invalid cells. Prefer vectorized arithmetic, shifts and rolling aggregates; "
                      "for finite weighted windows use a sum of shifted DataFrames, preserving complete-window missingness. "
                      "Use pct_change(fill_method=None); do not fill expired inputs.",
    "rolling_moments": "For an exact complete window use cov0(x,y)=mean(x*y)-mean(x)*mean(y). "
                       "Do not roll products centered by time-varying rolling means. For residualizing a on r "
                       "then regressing on RAW x: beta=(cov(a,x)-cov(a,r)*cov(r,x)/var(r))/var(x). "
                       "This differs from multiple regression, which also residualizes x. Implement only "
                       "the assigned formula, including its complete-pair and zero-variance rules.",
}


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def validate_source(source: str) -> dict:
    """Keep proposals to a pure score module; the runtime causality check is separate."""
    if len(source) > 20000:
        raise ValueError("candidate source exceeds 20 KB")
    tree = ast.parse(source)
    metadata = {}
    score_found = False
    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.name not in ALLOWED_IMPORTS for alias in node.names):
                raise ValueError("candidate imports outside the numeric allowlist")
        elif isinstance(node, ast.ImportFrom):
            if node.module != "__future__" or [alias.name for alias in node.names] != ["annotations"]:
                raise ValueError("candidate imports outside the numeric allowlist")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if isinstance(node, ast.AsyncFunctionDef):
                raise ValueError("async candidate functions are not allowed")
            score_found |= node.name == "score"
        elif isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                raise ValueError("candidate top-level assignment must be simple")
            name = node.targets[0].id
            if name not in {"CANDIDATE_ID", "FAMILY", "DIRECTION", "DESCRIPTION"}:
                raise ValueError("candidate top-level assignment is not metadata")
            metadata[name] = ast.literal_eval(node.value)
        elif not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                  and isinstance(node.value.value, str)):
            raise ValueError("candidate has unsupported top-level code")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name not in ALLOWED_IMPORTS for alias in node.names):
            raise ValueError("candidate imports outside the numeric allowlist")
        if isinstance(node, ast.ImportFrom) and (node.module != "__future__" or
                                                  [alias.name for alias in node.names] != ["annotations"]):
            raise ValueError("candidate imports outside the numeric allowlist")
        if isinstance(node, UNSUPPORTED_SYNTAX):
            raise ValueError(f"candidate contains unsupported control or side-effect syntax: {type(node).__name__}")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in FORBIDDEN_CALLS:
                raise ValueError("candidate contains forbidden call")
            if isinstance(func, ast.Attribute) and (func.attr.startswith("read_") or
                    (func.attr.startswith("to_") and func.attr not in {"to_numpy", "to_frame", "to_list", "to_datetime", "to_numeric", "to_timedelta"}) or
                    func.attr in {"eval", "query", "pipe", "load", "save", "savez", "savez_compressed",
                                  "loadtxt", "savetxt", "fromfile", "tofile", "memmap", "dump", "dumps"}):
                raise ValueError("candidate contains I/O or dynamic call")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError("candidate cannot access runtime internals")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise ValueError("candidate cannot access runtime internals")
    if (not score_found or set(metadata) != {"CANDIDATE_ID", "FAMILY", "DIRECTION", "DESCRIPTION"}
            or not isinstance(metadata["CANDIDATE_ID"], str)
            or not metadata["CANDIDATE_ID"].startswith("autoresearch_")
            or not isinstance(metadata["FAMILY"], str)
            or not isinstance(metadata["DESCRIPTION"], str)
            or metadata["DIRECTION"] not in (-1, 1)):
        raise ValueError("candidate metadata or score function invalid")
    return metadata


def model_json(prompt: str, schema_object: dict, directory: Path, model: str, role: str) -> dict:
    """Persist bounded transport attempts; successful responses are immutable."""
    from etf_autoresearch_recovery import atomic
    import time
    expected_model = {'review': 'gpt-5.6-sol', 'plan_review': 'gpt-5.6-sol',
                      'family_plan': 'gpt-6-luna', 'proposal': 'gpt-6-luna'}.get(role)
    if expected_model is None or model != expected_model:
        raise ValueError(f'ETF model role {role} requires {expected_model}')
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    if len(prompt) > 900000:
        atomic(directory / f'{role}_request_error.json', {
            'error_type': 'REQUEST_TOO_LARGE', 'characters': len(prompt), 'limit': 900000,
            'prompt_sha256': digest(prompt.encode()), 'model_called': False})
        raise ValueError(f'model request too large: {len(prompt)} characters; limit 900000')
    request_key = sha256(json.dumps([model, role, prompt, schema_object], sort_keys=True).encode()).hexdigest()
    request_dir = directory / (role + '_requests') / request_key
    request_dir.mkdir(parents=True, exist_ok=True)
    state_path = request_dir / 'state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {'attempts': []}
    success_path = request_dir / 'success.json'
    if success_path.exists():
        return json.loads(success_path.read_text())
    if state['attempts'] and state['attempts'][-1].get('status') == 'STARTED':
        pending_reply = request_dir / f"attempt_{len(state['attempts'])}" / 'reply.json'
        if pending_reply.exists():
            try:
                value = json.loads(pending_reply.read_text())
            except json.JSONDecodeError:
                pass
            else:
                atomic(success_path, value)
                state['attempts'][-1]['status'] = 'COMPLETED'
                atomic(state_path, state)
                return value
    if state['attempts'] and state['attempts'][-1].get('status') == 'FAILED' and not state['attempts'][-1].get('retryable'):
        raise ValueError('non-retryable model request failure: ' + state['attempts'][-1]['error'])
    schema = directory / f'{role}_schema.json'
    schema.write_text(json.dumps(schema_object) + '\n')
    (directory / f'{role}_prompt.txt').write_text(prompt)
    (request_dir / 'prompt.txt').write_text(prompt)
    for index in range(len(state['attempts']), 3):
        attempt_dir = request_dir / f'attempt_{index + 1}'
        attempt_dir.mkdir(exist_ok=True)
        if index:
            time.sleep((30, 120)[index - 1])
        reply = attempt_dir / 'reply.json'
        entry = {'attempt': index + 1, 'status': 'STARTED'}
        state['attempts'].append(entry)
        atomic(state_path, state)
        transient = False
        try:
            with subprocess.Popen(
                ['codex', 'exec', '--ephemeral', '--sandbox', 'read-only', '--model', model,
                 '--output-schema', str(schema), '--output-last-message', str(reply), '-C', str(ROOT), '-'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, start_new_session=True,
            ) as process:
                try:
                    stdout, stderr = process.communicate(prompt, timeout=180)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    stdout, stderr = process.communicate()
                    transient = True
                    raise TimeoutError('model transport timeout after 180 seconds')
                except BaseException:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
                    raise
                (attempt_dir / 'stderr.txt').write_text(stderr[-12000:])
                (directory / f'{role}_stderr.txt').write_text(stderr[-12000:])
                if process.returncode != 0 or not reply.exists():
                    error = stderr[-1500:]
                    transient = any(token in error.lower() for token in
                                    ('429', 'rate limit', '503', '502', 'connection reset', 'temporarily unavailable', 'timed out'))
                    raise RuntimeError(f'{role} failed (exit={process.returncode}): {error}')
            value = json.loads(reply.read_text())
            atomic(success_path, value)
            atomic(directory / f'{role}_reply.json', value)
            entry['status'] = 'COMPLETED'
            atomic(state_path, state)
            return value
        except Exception as exc:
            entry.update(status='FAILED', error=str(exc), retryable=transient)
            atomic(state_path, state)
            if not transient:
                raise
    raise RuntimeError(f'model transport retry budget exhausted: {request_dir}')


def propose_with_codex(context: dict, round_dir: Path, model: str) -> dict:
    """The model can read context but cannot edit the repository."""
    from etf_autoresearch_implementation import kernel_contract
    kind = (context.get('assigned_family_plan') or {}).get('math_kernel', 'custom')
    context = compact_proposal_context({**context, "score_contract": SCORE_CONTRACT,
                                       "math_kernel_contract": kernel_contract(kind)})
    prompt = (
        "You propose exactly one ETF factor candidate for an adaptive discovery experiment. "
        "Return JSON matching the schema, with complete Python source_code and a short economic rationale. "
        "Do not edit files, inspect market files, or run evaluations. Use only the approved D-close-known "
        "input panels named in the context; base panels are close/open/high/low/amount/volume. "
        "No outcome labels, unapproved external inputs, I/O, future shifts, or automatic direction flips. "
        "Prepared input panels already enforce availability and staleness: do not forward-fill expired or unavailable inputs. "
        "Follow the frozen plan. In open mode, implement its hypothesis regardless of whether its family is old or new. In refine mode preserve the assigned parent contract. "
        "Implement the assigned frozen formula, direction and required_panels; explore FAMILY must equal its family_key. "
        "Do not replace the formula with a sibling mechanism. Feature diagnostics describe availability, not outcomes. "
        "If repair_only is true, repair only the reported implementation defect in original_source. "
        "Preserve the economic formula, window, direction, population and input profile; do not optimize or replace the hypothesis. "
        "The original and revised code will be independently reviewed against the same frozen plan before any labels open. "
        "Follow score_contract exactly, including RAW score, one direction application, allowed syntax and DataFrame shape. "
        "When the suggested template exactly matches the frozen formula, call it without redefining it. Otherwise implement the unchanged formula as custom code and explain the mismatch; do not change the regression to fit a template. "
        "The controller will embed its exact implementation. Apply the planned mask and lag explicitly. "
        "Use vectorized operations: score is recomputed for every date prefix, so avoid per-date Python loops. "
        "Use a unique autoresearch_ candidate identifier and an economic rationale; unused combinations alone are not rationale. "
        "Preserve CANDIDATE_ID/FAMILY/DIRECTION/DESCRIPTION and score(panels). "
        "Only pandas/numpy/math imports are allowed. Diversify mechanisms when prior trials are close variants. "
        "The fixed signed Rank IC is the objective; this seen history is discovery, not confirmation.\n\n"
        + json.dumps(context, ensure_ascii=False)
    )
    proposal = model_json(prompt, SCHEMA, round_dir, model, "proposal")
    if set(proposal) != {"rationale", "source_code"}:
        raise ValueError("proposer response does not match required fields")
    return proposal


@contextmanager
def campaign_lock(output_root: Path):
    output_root.mkdir(parents=True, exist_ok=True)
    with (output_root / ".campaign.lock").open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def run_campaign(campaign_id: str, rounds: int, baseline: Path, inventory: Path,
                 runs_root: Path, output_root: Path, parent_candidate: str | None,
                 model: str = "gpt-6-luna", propose=propose_with_codex,
                 evaluate=cycle, parent_seed: Path | None = None) -> dict:
    if rounds < 1 or rounds > 100:
        raise ValueError("rounds must be 1..100")
    if not campaign_id.replace("_", "").replace("-", "").isalnum():
        raise ValueError("campaign-id must be alphanumeric with underscores/hyphens")
    with campaign_lock(output_root):
        seed = json.loads((baseline / "result.json").read_text())
        champion_source = CANDIDATE.read_bytes()
        validate_source(champion_source.decode())
        if digest(champion_source) != seed["candidate_sha256"]:
            raise ValueError("candidate file does not match baseline result; restore the seed source")
        campaign_dir = output_root / "campaigns" / campaign_id
        campaign_dir.mkdir(parents=True, exist_ok=False)
        champion_dir = baseline
        rows: list[dict] = []
        summary = {"campaign_id": campaign_id, "model": model, "baseline": str(baseline),
                   "parent_seed": str(parent_seed or baseline),
                   "inventory": str(inventory), "parent_candidate": parent_candidate,
                   "requested_rounds": rounds, "rounds": rows,
                   "formal_registration": False, "evidence": "adaptive seen-history discovery only"}

        def save():
            summary["champion_run"] = champion_dir.name
            summary["champion_sha256"] = digest(champion_source)
            (campaign_dir / "summary.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n")

        save()
        failures = 0
        try:
            for number in range(1, rounds + 1):
                round_id = f"{campaign_id}_r{number:02d}"
                round_dir = campaign_dir / f"r{number:02d}"
                round_dir.mkdir()
                (round_dir / "parent.py").write_bytes(champion_source)
                row = {"round": number, "run_id": round_id, "status": "STARTED",
                       "parent_run": champion_dir.name, "parent_sha256": digest(champion_source)}
                rows.append(row)
                save()
                try:
                    context = {"round": number, "current_source": champion_source.decode(),
                               "prior_trials": [{key: r.get(key) for key in
                                                 ("run_id", "candidate", "family", "ic", "hac_t",
                                                  "keep", "reason")}
                                                for r in rows[:-1]]}
                    context["champion"] = {key: json.loads((champion_dir / "result.json").read_text()).get(key)
                                           for key in ("candidate", "family", "ic", "n")}
                    proposal = propose(context, round_dir, model)
                    source = proposal["source_code"]
                    metadata = validate_source(source)
                    row.update({"rationale": proposal["rationale"], "candidate": metadata["CANDIDATE_ID"],
                                "family": metadata["FAMILY"], "candidate_sha256": digest(source.encode())})
                    (round_dir / "candidate.py").write_text(source)
                    if source.encode() == champion_source:
                        raise ValueError("proposal duplicates current champion source")
                    CANDIDATE.write_text(source)
                    decision = evaluate(round_id, output_root, parent_seed or baseline, inventory, runs_root,
                                        parent_candidate)
                    trial_dir = output_root / round_id
                    paired = compare(champion_dir, trial_dir)
                    trial = json.loads((trial_dir / "result.json").read_text())
                    incumbent = json.loads((champion_dir / "result.json").read_text())
                    coverage_equal = paired["n"] == trial["n"] == incumbent["n"]
                    keep = (coverage_equal and math.isfinite(trial["ic"])
                            and paired["delta_ic"] > 1e-12)
                    reason = ("higher paired signed IC on identical valid dates" if keep else
                              "coverage differs" if not coverage_equal else
                              "paired signed IC did not improve")
                    row.update({"status": "COMPLETED", "ic": trial["ic"], "hac_t": trial["hac_t"],
                                "n": trial["n"], "decision": decision["decision"],
                                "paired_to_champion": paired, "keep": keep, "reason": reason})
                    if keep:
                        champion_source = source.encode()
                        champion_dir = trial_dir
                    failures = 0
                except Exception as exc:
                    row.update({"status": "FAILED", "error_type": type(exc).__name__,
                                "error": str(exc), "keep": False})
                    failures += 1
                finally:
                    CANDIDATE.write_bytes(champion_source)
                    save()
                    print(json.dumps(row, ensure_ascii=False), flush=True)
                if failures >= 2:
                    summary["stop_reason"] = "two consecutive failed rounds"
                    break
        finally:
            CANDIDATE.write_bytes(champion_source)
            summary.setdefault("stop_reason", "requested rounds complete")
            save()
        return summary


if __name__ == "__main__":
    from etf_autoresearch_workflow import main
    main()
