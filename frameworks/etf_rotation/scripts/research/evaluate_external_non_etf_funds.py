#!/usr/bin/env python3
"""Seal and evaluate five ETF leads on an untouched non-ETF fund population."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd
import yaml

ETF_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ETF_ROOT / "src"))

BASE_ENTRY = Path(__file__).with_name("evaluate_all_etf_daily.py").resolve()
_spec = importlib.util.spec_from_file_location("all_etf_base_evaluator", BASE_ENTRY)
if _spec is None or _spec.loader is None:
    raise RuntimeError("unable to load the sealed all-ETF evaluator")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

from etf_strategy.core.etf_all_daily_discovery import executable_forward_return  # noqa: E402
from etf_strategy.core.etf_all_daily_factor_engine import (  # noqa: E402
    ForwardGates,
    compose_candidate,
    evaluate_forward_candidate,
    mean_abs_daily_rank_corr,
)
from etf_strategy.core.etf_external_fund_data import load_external_non_etf_daily  # noqa: E402
from etf_strategy.core.etf_mining_campaign import (  # noqa: E402
    file_sha256,
    verify_plan_seal,
    write_plan_seal,
)


EXTERNAL_DATA_CORE = ETF_ROOT / "src/etf_strategy/core/etf_external_fund_data.py"
SOURCE_CANDIDATES = ETF_ROOT / "configs/all_etf_daily_luna_candidates_v2.yaml"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _load_context(config: dict[str, Any]):
    data, population = config["data"], config["population"]
    return load_external_non_etf_daily(
        str(data["cache_root"]),
        start=str(data["start"]),
        as_of=str(data["as_of"]),
        allowed_fund_types=tuple(str(value) for value in population["allowed_fund_types"]),
        min_history_sessions=int(population["min_history_sessions"]),
        liquidity_window=int(population["liquidity_window"]),
        min_median_amount_thousand=float(population["min_median_amount_thousand"]),
    )


def _gates(config: dict[str, Any]) -> ForwardGates:
    values = config["gates"]
    return ForwardGates(
        campaign_budget=int(values["fixed_campaign_budget"]),
        alpha=float(values["alpha"]),
        min_names=int(values["min_names"]),
        min_days=int(values["min_confirmation_days"]),
        min_signed_mean_ic=float(values["min_signed_mean_ic"]),
        min_hac_t=float(values["min_hac_t"]),
        top_fraction=float(values["top_fraction"]),
        min_top_label_coverage=float(values["min_top_label_coverage"]),
        min_top_excess_bp=float(values["min_top_excess_bp"]),
        min_top_excess_hac_t=float(values["min_top_excess_hac_t"]),
        max_abs_rank_corr=float(values["max_abs_rank_corr"]),
        min_residual_mean_ic=float(values["min_residual_mean_ic"]),
        min_residual_hac_t=float(values["min_residual_hac_t"]),
    )


def _assert_source_formulas(candidates: dict[str, Any]) -> None:
    source = yaml.safe_load(SOURCE_CANDIDATES.read_text())
    by_id = {row["id"]: row for row in source["candidates"]}
    for row in candidates["candidates"]:
        original = by_id.get(row["source_id"])
        if original is None:
            raise ValueError(f"source candidate missing: {row['source_id']}")
        for key in ("operator", "left", "right", "expected_sign"):
            if row.get(key) != original.get(key):
                raise ValueError(f"external formula changed from {row['source_id']}: {key}")


def _materialize(config: dict[str, Any], candidates: dict[str, Any], context):
    catalog = base._catalog(config)
    sources = base._candidate_sources(candidates) | {
        str(row["source"]) for row in config["controls"]
    }
    atoms_needed = base._candidate_atoms(candidates) | {
        str(row["atom"]) for row in config["controls"]
    }
    atoms = base._ranked_sources(
        sources,
        catalog=catalog,
        panels=context.panels,
        eligibility=context.eligibility,
        data_root=Path(str(config["data"]["cache_root"])).resolve(),
        needed_atoms=atoms_needed,
    )
    controls = {str(row["atom"]): atoms[str(row["atom"])] for row in config["controls"]}
    signals = {
        str(row["id"]): compose_candidate(row, atoms, context.eligibility)
        for row in candidates["candidates"]
    }
    return catalog, sources, atoms_needed, controls, signals


def create_plan(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"plan output must be new and empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    config_path, candidate_path = args.config.resolve(), args.candidates.resolve()
    config, candidates = yaml.safe_load(config_path.read_text()), yaml.safe_load(candidate_path.read_text())
    base._validate_candidates(candidates)
    _assert_source_formulas(candidates)
    if len(candidates["candidates"]) != int(config["gates"]["fixed_campaign_budget"]):
        raise ValueError("external candidate count must consume the declared budget exactly")
    evidence = (ETF_ROOT.parent.parent / str(candidates["selection_evidence"])).resolve()
    if not evidence.exists():
        raise ValueError(f"selection evidence is missing: {evidence}")
    context = _load_context(config)
    counts = context.eligibility.sum(axis=1).loc[
        pd.Timestamp(config["confirmation"]["start"]):pd.Timestamp(config["confirmation"]["end"])
    ]
    if int(counts.min()) < int(config["population"]["minimum_observed_eligible"]):
        raise ValueError("external population does not meet its frozen availability floor")
    catalog, sources, atoms_needed, _, signals = _materialize(config, candidates, context)
    leak = base._leak_check(
        signals,
        list(candidates["candidates"]),
        catalog=catalog,
        sources=sources,
        needed_atoms=atoms_needed,
        panels=context.panels,
        eligibility=context.eligibility,
        data_root=Path(str(config["data"]["cache_root"])).resolve(),
        cutoff="2024-12-31",
    )
    leak_path = output / "preforward_future_leak_check.json"
    _write_json(leak_path, leak)
    if not leak["all_pass"]:
        raise ValueError("external population future-dependency preflight failed")
    file_contract = base._file_contract(config_path, candidate_path, catalog, sources)
    file_contract.update(
        {
            str(Path(__file__).resolve()): file_sha256(Path(__file__).resolve()),
            str(EXTERNAL_DATA_CORE): file_sha256(EXTERNAL_DATA_CORE),
            str(SOURCE_CANDIDATES): file_sha256(SOURCE_CANDIDATES),
        }
    )
    root = Path(str(config["data"]["cache_root"])).resolve()
    plan = {
        "schema_version": "external_non_etf_fund_plan_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "question": "Do five ETF leads transfer to the untouched non-ETF equity/mixed fund population?",
        "config": str(config_path),
        "candidates": candidates["candidates"],
        "population": config["population"],
        "execution": config["execution"],
        "confirmation": config["confirmation"],
        "gates": config["gates"],
        "selection_evidence": str(evidence),
        "selection_evidence_sha256": file_sha256(evidence),
        "file_contract": file_contract,
        "data_contract": base._preforward_contract(root, str(config["data"]["as_of"])),
        "preflight_leak_artifact": {"path": str(leak_path), "sha256": file_sha256(leak_path)},
        "population_summary": {
            "identity_rows": len(context.symbols),
            "eligible_min": int(counts.min()),
            "eligible_median": float(counts.median()),
            "eligible_max": int(counts.max()),
        },
        "external_outcomes_were_not_computed_by_plan": True,
        "deployment_permission": False,
    }
    plan_path = output / "PLAN.json"
    _write_json(plan_path, plan)
    write_plan_seal(plan_path)
    print(
        f"External PLAN sealed: candidates={len(candidates['candidates'])} "
        f"population={len(context.symbols)} eligibility={int(counts.min())}-{int(counts.max())} "
        f"plan={plan_path}",
        flush=True,
    )


def _verify(plan_path: Path, plan: dict[str, Any], root: Path) -> None:
    if not verify_plan_seal(plan_path):
        raise ValueError("external PLAN seal invalid")
    for raw, expected in plan["file_contract"].items():
        path = Path(raw)
        if not path.exists() or file_sha256(path) != expected:
            raise ValueError(f"sealed external file changed: {path}")
    evidence = Path(plan["selection_evidence"])
    if file_sha256(evidence) != plan["selection_evidence_sha256"]:
        raise ValueError("ETF selection evidence changed")
    if base._preforward_contract(root, str(plan["confirmation"]["end"])) != plan["data_contract"]:
        raise ValueError("external validation data changed after PLAN")
    leak = plan["preflight_leak_artifact"]
    leak_path = Path(leak["path"])
    if file_sha256(leak_path) != leak["sha256"] or not json.loads(leak_path.read_text())["all_pass"]:
        raise ValueError("external preflight leak artifact changed or failed")


def evaluate(args: argparse.Namespace) -> None:
    plan_path = args.plan.resolve()
    plan = json.loads(plan_path.read_text())
    config_path = Path(plan["config"])
    config = yaml.safe_load(config_path.read_text())
    candidate_payload = {"candidates": plan["candidates"]}
    root = Path(str(config["data"]["cache_root"])).resolve()
    _verify(plan_path, plan, root)
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"evaluation output must be new and empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    context = _load_context(config)
    catalog, sources, atoms_needed, controls, signals = _materialize(
        config, candidate_payload, context
    )
    leak = base._leak_check(
        signals,
        list(plan["candidates"]),
        catalog=catalog,
        sources=sources,
        needed_atoms=atoms_needed,
        panels=context.panels,
        eligibility=context.eligibility,
        data_root=root,
        cutoff="2024-12-31",
    )
    _write_json(output / "future_leak_check.json", leak)
    if not leak["all_pass"]:
        raise ValueError("external dynamic future-dependency check failed")
    forward = executable_forward_return(
        context.panels["open"],
        entry_lag=int(config["execution"]["entry_lag_sessions"]),
        horizon=int(config["execution"]["horizon"]),
    )
    gates = _gates(config)
    admitted: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    start, end = str(config["confirmation"]["start"]), str(config["confirmation"]["end"])
    for spec in plan["candidates"]:
        cid = str(spec["id"])
        row, _ = evaluate_forward_candidate(
            signals[cid],
            forward,
            context.eligibility,
            {**controls, **admitted},
            candidate_id=cid,
            direction=int(spec["expected_sign"]),
            start=start,
            end=end,
            calendar=context.sessions,
            entry_lag=int(config["execution"]["entry_lag_sessions"]),
            horizon=int(config["execution"]["horizon"]),
            gates=gates,
        )
        correlations = {
            prior: mean_abs_daily_rank_corr(
                signals[cid], prior_signal, context.eligibility,
                min_names=gates.min_names, start=start, end=end,
            )
            for prior, prior_signal in admitted.items()
        }
        finite = {name: value for name, value in correlations.items() if np.isfinite(value)}
        missing_corr = len(finite) != len(correlations)
        worst = max(finite, key=finite.get) if finite else ""
        max_corr = float(finite[worst]) if worst else 0.0
        corr_pass = bool(not missing_corr and max_corr < gates.max_abs_rank_corr)
        if not corr_pass:
            failures = [value for value in str(row["gate_failures"]).split(";") if value]
            failures.append("rank_correlation_missing" if missing_corr else "rank_correlation_redundancy")
            row["gate_failures"] = ";".join(failures)
        row.update(
            {
                "source_id": spec["source_id"],
                "max_abs_rank_corr": max_corr,
                "max_abs_rank_corr_vs": worst,
                "rank_correlation_pass": corr_pass,
                "gate_pass": bool(row["intrinsic_pass"] and corr_pass),
            }
        )
        if row["gate_pass"]:
            admitted[cid] = signals[cid] * float(spec["expected_sign"])
        rows.append(row)
        print(
            f"[external-referee] {cid}/{spec['source_id']} pass={row['gate_pass']} "
            f"IC={row['forward_mean_ic']:.4f} t={row['forward_hac_t']:.2f} "
            f"top={row['top_excess_bp']:.1f}bp failures={row['gate_failures']}",
            flush=True,
        )
    metrics = pd.DataFrame(rows)
    metrics.to_csv(output / "candidate_metrics.csv", index=False)
    factors = [spec for spec in plan["candidates"] if spec["id"] in admitted]
    _write_json(output / "admitted_factors.json", {"count": len(factors), "factors": factors})
    _write_json(
        output / "run_manifest.json",
        {
            "schema_version": "external_non_etf_fund_evaluation_v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "plan": str(plan_path),
            "plan_sha256": file_sha256(plan_path),
            "plan_seal_ok_at_end": verify_plan_seal(plan_path),
            "candidate_count": len(plan["candidates"]),
            "admitted_count": len(factors),
            "all_five_pass": len(factors) == 5,
            "deployment_permission": False,
        },
    )
    _verify(plan_path, plan, root)
    print(f"External evaluation complete: admitted={len(factors)}/5 output={output}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--config", type=Path, required=True)
    plan.add_argument("--candidates", type=Path, required=True)
    plan.add_argument("--output", type=Path, required=True)
    run = sub.add_parser("evaluate")
    run.add_argument("--plan", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    parsed = parse_args()
    create_plan(parsed) if parsed.mode == "plan" else evaluate(parsed)
