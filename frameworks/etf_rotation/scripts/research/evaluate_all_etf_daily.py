#!/usr/bin/env python3
"""Preregister and evaluate frozen broad-ETF daily factor candidates.

Protocol:
  1. ``plan`` runs while no forward partitions exist and seals every formula,
     sign, gate, source file and pre-forward data partition.
  2. Forward partitions may then be downloaded.
  3. ``evaluate`` fails closed on any plan/code/config/pre-forward-data change.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd
import yaml

ETF_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ETF_ROOT / "src"))

from etf_strategy.core.etf_all_daily_data import load_all_etf_daily  # noqa: E402
from etf_strategy.core.etf_all_daily_discovery import executable_forward_return  # noqa: E402
from etf_strategy.core.etf_all_daily_factor_engine import (  # noqa: E402
    ForwardGates,
    compose_candidate,
    evaluate_forward_candidate,
    mean_abs_daily_rank_corr,
)
from etf_strategy.core.etf_factor_grammar import cross_sectional_rank  # noqa: E402
from etf_strategy.core.etf_mining_campaign import (  # noqa: E402
    file_sha256,
    verify_plan_seal,
    write_plan_seal,
)
from etf_strategy.core.family_registry import load_builtin_families, resolve_family  # noqa: E402


ENGINE_CORE = ETF_ROOT / "src/etf_strategy/core/etf_all_daily_factor_engine.py"
DATA_CORE = ETF_ROOT / "src/etf_strategy/core/etf_all_daily_data.py"
DISCOVERY_CORE = ETF_ROOT / "src/etf_strategy/core/etf_all_daily_discovery.py"


def _json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _hash_rows(rows: list[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(rows):
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(value.encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _preforward_contract(root: Path, end: str) -> dict[str, Any]:
    end_key = pd.Timestamp(end).strftime("%Y%m%d")
    rows: list[tuple[str, str]] = []
    counts: dict[str, int] = {}
    for endpoint in ("fund_daily", "fund_adj"):
        paths = sorted(
            path for path in (root / "raw" / endpoint).glob("*.parquet")
            if path.stem <= end_key
        )
        if not paths:
            raise ValueError(f"no pre-forward {endpoint} partitions")
        counts[endpoint] = len(paths)
        rows.extend((str(path.relative_to(root)), file_sha256(path)) for path in paths)
    calendar = pd.read_parquet(root / "metadata/trading_sessions.parquet")
    sessions = sorted(value for value in calendar["trade_date"].astype(str) if value <= end_key)
    return {
        "end": end,
        "partition_counts": counts,
        "partition_digest_sha256": _hash_rows(rows),
        "calendar_prefix_count": len(sessions),
        "calendar_prefix_sha256": hashlib.sha256(("\n".join(sessions) + "\n").encode()).hexdigest(),
        "fund_basic_sha256": file_sha256(root / "metadata/fund_basic.parquet"),
    }


def _forward_partitions(root: Path, start: str) -> list[Path]:
    key = pd.Timestamp(start).strftime("%Y%m%d")
    found: list[Path] = []
    for endpoint in ("fund_daily", "fund_adj"):
        found.extend(path for path in (root / "raw" / endpoint).glob("*.parquet") if path.stem >= key)
    return sorted(found)


def _catalog(config: dict[str, Any]) -> dict[str, Path]:
    raw = Path(str(config["family_catalog"]))
    path = raw if raw.is_absolute() else (ETF_ROOT / raw).resolve()
    rows = yaml.safe_load(path.read_text())["available_families"]
    return {
        str(row["source"]): (
            Path(str(row["config"])).resolve()
            if Path(str(row["config"])).is_absolute()
            else (ETF_ROOT / str(row["config"])).resolve()
        )
        for row in rows
    }


def _candidate_sources(candidate_config: dict[str, Any]) -> set[str]:
    sources: set[str] = set()
    for candidate in candidate_config["candidates"]:
        sources.add(str(candidate["left"]["source"]))
        if "right" in candidate:
            sources.add(str(candidate["right"]["source"]))
    return sources


def _candidate_atoms(candidate_config: dict[str, Any]) -> set[str]:
    atoms: set[str] = set()
    for candidate in candidate_config["candidates"]:
        atoms.add(str(candidate["left"]["name"]))
        if "right" in candidate:
            atoms.add(str(candidate["right"]["name"]))
    return atoms


def _file_contract(
    config_path: Path,
    candidate_path: Path,
    catalog: dict[str, Path],
    sources: set[str],
) -> dict[str, str]:
    load_builtin_families()
    provider_paths = {
        Path(str(inspect.getsourcefile(resolve_family(source).builder))).resolve()
        for source in sources
    }
    support_paths = {
        ETF_ROOT / "src/etf_strategy/core/family_registry.py",
        ETF_ROOT / "src/etf_strategy/core/family_provider.py",
        ETF_ROOT / "src/etf_strategy/core/etf_factor_grammar.py",
        ETF_ROOT / "src/etf_strategy/core/etf_family_referee.py",
        ETF_ROOT / "src/etf_strategy/core/etf_marginal_ic.py",
        ETF_ROOT / "src/etf_strategy/core/etf_mining_referee.py",
        ETF_ROOT / "src/etf_strategy/core/etf_mining_campaign.py",
    }
    config_payload = yaml.safe_load(config_path.read_text())
    catalog_value = Path(str(config_payload["family_catalog"]))
    catalog_path = (
        catalog_value if catalog_value.is_absolute() else (ETF_ROOT / catalog_value).resolve()
    )
    paths = [
        Path(__file__).resolve(), ENGINE_CORE, DATA_CORE, DISCOVERY_CORE,
        config_path.resolve(), candidate_path.resolve(), catalog_path,
    ] + sorted(provider_paths | support_paths) + [catalog[source] for source in sorted(sources)]
    return {str(path): file_sha256(path) for path in paths}


def _validate_candidates(payload: dict[str, Any]) -> None:
    rows = payload.get("candidates", [])
    ids = [str(row.get("id", "")) for row in rows]
    if not rows or len(ids) != len(set(ids)) or any(not value for value in ids):
        raise ValueError("candidate IDs must be nonempty and unique")
    for row in rows:
        if row.get("operator") not in ("atomic", "rank_spread"):
            raise ValueError(f"unsupported operator for {row['id']}")
        if int(row.get("expected_sign", 0)) not in (-1, 1):
            raise ValueError(f"expected_sign must be +/-1 for {row['id']}")
        if row["operator"] == "rank_spread" and "right" not in row:
            raise ValueError(f"rank_spread missing right leg for {row['id']}")


def create_plan(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"plan output must be new and empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    config_path = args.config.resolve()
    candidate_path = args.candidates.resolve()
    discovery = args.discovery_output.resolve()
    config = yaml.safe_load(config_path.read_text())
    candidates = yaml.safe_load(candidate_path.read_text())
    _validate_candidates(candidates)
    forward_start = str(config["surfaces"]["forward_start"])
    validation_end = str(config["surfaces"]["validation_end"])
    root = Path(str(config["data"]["cache_root"])).resolve()
    contaminated = _forward_partitions(root, forward_start)
    if contaminated:
        raise ValueError(f"forward data already exists before PLAN; first={contaminated[0]}")
    discovery_files = [discovery / "run_manifest.json", discovery / "atom_profiles.csv"]
    if any(not path.exists() for path in discovery_files):
        raise ValueError("discovery output is incomplete")
    discovery_manifest = json.loads(discovery_files[0].read_text())
    if discovery_manifest.get("forward_surface_downloaded") is not False:
        raise ValueError("discovery manifest does not certify forward isolation")
    for raw, expected in discovery_manifest.get("provider_code_hashes", {}).items():
        path = Path(raw)
        if not path.exists() or file_sha256(path) != expected:
            raise ValueError(f"provider code changed after discovery: {path}")
    catalog = _catalog(config)
    manifest_catalog = Path(str(discovery_manifest.get("family_catalog", "")))
    if (
        not manifest_catalog.exists()
        or file_sha256(manifest_catalog) != discovery_manifest.get("family_catalog_sha256")
    ):
        raise ValueError("family catalog changed after discovery")
    expected_discovery_files = {
        "config_sha256": config_path,
        "entry_sha256": ETF_ROOT / "scripts/research/discover_all_etf_daily.py",
        "data_core_sha256": DATA_CORE,
        "discovery_core_sha256": DISCOVERY_CORE,
    }
    for key, path in expected_discovery_files.items():
        if discovery_manifest.get(key) != file_sha256(path):
            raise ValueError(f"{path} changed after discovery ({key})")
    for raw, expected in discovery_manifest.get("source_config_hashes", {}).items():
        path = Path(raw)
        if not path.exists() or file_sha256(path) != expected:
            raise ValueError(f"source config changed after discovery: {path}")
    sources = _candidate_sources(candidates) | {
        str(row["source"]) for row in config["controls"]
    }
    needed_atoms = _candidate_atoms(candidates) | {
        str(row["atom"]) for row in config["controls"]
    }
    missing = sources - set(catalog)
    if missing:
        raise ValueError(f"catalog is missing candidate sources: {sorted(missing)}")
    gates = candidates["forward_gates"]
    if len(candidates["candidates"]) > int(gates["fixed_campaign_budget"]):
        raise ValueError("candidate count exceeds fixed campaign budget")
    population = config["population"]
    context = load_all_etf_daily(
        root,
        start=str(config["data"]["start"]),
        as_of=validation_end,
        min_history_sessions=int(population["min_history_sessions"]),
        liquidity_window=int(population["liquidity_window"]),
        min_median_amount_thousand=float(population["min_median_amount_thousand"]),
    )
    atoms = _ranked_sources(
        sources,
        catalog=catalog,
        panels=context.panels,
        eligibility=context.eligibility,
        data_root=root,
        needed_atoms=needed_atoms,
    )
    signals = {
        str(spec["id"]): compose_candidate(spec, atoms, context.eligibility)
        for spec in candidates["candidates"]
    }
    preflight = _leak_check(
        signals,
        list(candidates["candidates"]),
        catalog=catalog,
        sources=sources,
        needed_atoms=needed_atoms,
        panels=context.panels,
        eligibility=context.eligibility,
        data_root=root,
        cutoff=str(config["surfaces"]["discovery_end"]),
    )
    preflight_path = output / "preforward_future_leak_check.json"
    _json(preflight_path, preflight)
    if not preflight["all_pass"]:
        raise ValueError("pre-forward future-dependency check failed; PLAN not written")
    plan = {
        "schema_version": "all_etf_daily_forward_plan_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "business_question": "PIT broad ETF cross-sectional factors for D+2 to D+7 relative return",
        "population_contract": config["population"],
        "execution": config["execution"],
        "surfaces": config["surfaces"],
        "forward_gates": gates,
        "candidate_config": str(candidate_path),
        "candidate_config_sha256": file_sha256(candidate_path),
        "candidates": candidates["candidates"],
        "campaign_declared_candidates": len(candidates["candidates"]),
        "campaign_budget": int(gates["fixed_campaign_budget"]),
        "discovery_artifacts": {
            str(path): file_sha256(path) for path in discovery_files
        },
        "preforward_future_leak_artifact": {
            "path": str(preflight_path),
            "sha256": file_sha256(preflight_path),
        },
        "file_contract": _file_contract(config_path, candidate_path, catalog, sources),
        "preforward_cache_contract": _preforward_contract(root, validation_end),
        "forward_absence_checked_from": forward_start,
        "outcomes_are_features": False,
        "direction_source": "frozen expected_sign in candidate config",
    }
    plan_path = output / "PLAN.json"
    _json(plan_path, plan)
    seal = write_plan_seal(plan_path)
    print(
        f"Forward PLAN sealed: candidates={len(candidates['candidates'])} "
        f"plan={plan_path} seal={seal}",
        flush=True,
    )


def _verify_plan(plan_path: Path, plan: dict[str, Any], root: Path) -> None:
    if not verify_plan_seal(plan_path):
        raise ValueError("PLAN seal is missing or invalid")
    for raw, expected in plan["file_contract"].items():
        path = Path(raw)
        if not path.exists() or file_sha256(path) != expected:
            raise ValueError(f"sealed source/config changed: {path}")
    for raw, expected in plan["discovery_artifacts"].items():
        path = Path(raw)
        if not path.exists() or file_sha256(path) != expected:
            raise ValueError(f"sealed discovery artifact changed: {path}")
    preflight = plan["preforward_future_leak_artifact"]
    preflight_path = Path(str(preflight["path"]))
    if (
        not preflight_path.exists()
        or file_sha256(preflight_path) != preflight["sha256"]
        or not json.loads(preflight_path.read_text()).get("all_pass", False)
    ):
        raise ValueError("sealed pre-forward future-dependency audit changed or failed")
    actual = _preforward_contract(root, str(plan["surfaces"]["validation_end"]))
    if actual != plan["preforward_cache_contract"]:
        raise ValueError("pre-forward data contract changed after PLAN")
    if not _forward_partitions(root, str(plan["surfaces"]["forward_start"])):
        raise ValueError("forward data is absent; download it only after sealing PLAN")


def _ranked_sources(
    source_names: set[str],
    *,
    catalog: dict[str, Path],
    panels: dict[str, pd.DataFrame],
    eligibility: pd.DataFrame,
    data_root: Path,
    needed_atoms: set[str] | None = None,
) -> dict[str, pd.DataFrame]:
    load_builtin_families()
    atoms: dict[str, pd.DataFrame] = {}
    shared_spaces: dict[str, dict[str, pd.DataFrame]] = {}
    for number, source in enumerate(sorted(source_names), start=1):
        print(f"[materialize] source={source} {number}/{len(source_names)}", flush=True)
        source_config = yaml.safe_load(catalog[source].read_text())
        frequency = str(source_config.get("frequency", ""))
        if frequency not in ("", "1d", "adj_factor"):
            raise ValueError(f"non-daily source rejected: {source}:{frequency}")
        builder = resolve_family(source).builder
        cache_key = getattr(builder, "family_space_cache_key", None)
        if cache_key is not None and cache_key in shared_spaces:
            space = shared_spaces[cache_key]
        else:
            space = builder(panels, eligibility, data_root, source_config)
            if cache_key is not None:
                shared_spaces[str(cache_key)] = space
        for row in source_config["atoms"]:
            name = str(row["name"])
            if needed_atoms is not None and name not in needed_atoms:
                continue
            if name in atoms:
                raise ValueError(f"duplicate atom name across sources: {name}")
            atoms[name] = cross_sectional_rank(
                space[name].reindex_like(eligibility), eligibility
            ).astype("float32")
    if needed_atoms is not None and set(atoms) != needed_atoms:
        raise ValueError(f"requested atoms were not materialized: {sorted(needed_atoms - set(atoms))}")
    return atoms


def _gates(payload: dict[str, Any]) -> ForwardGates:
    return ForwardGates(
        campaign_budget=int(payload["fixed_campaign_budget"]),
        alpha=float(payload["alpha"]),
        min_names=int(payload["min_names"]),
        min_days=int(payload["min_forward_days"]),
        min_signed_mean_ic=float(payload["min_signed_mean_ic"]),
        min_hac_t=float(payload["min_forward_hac_t"]),
        top_fraction=float(payload["top_fraction"]),
        min_top_label_coverage=float(payload["min_top_label_coverage"]),
        min_top_excess_bp=float(payload["min_top_excess_bp"]),
        min_top_excess_hac_t=float(payload["min_top_excess_hac_t"]),
        max_abs_rank_corr=float(payload["max_abs_rank_corr"]),
        min_residual_mean_ic=float(payload["min_residual_mean_ic"]),
        min_residual_hac_t=float(payload["min_residual_hac_t"]),
    )


def _leak_check(
    candidate_signals: dict[str, pd.DataFrame],
    candidate_specs: list[dict[str, Any]],
    *,
    catalog: dict[str, Path],
    sources: set[str],
    needed_atoms: set[str],
    panels: dict[str, pd.DataFrame],
    eligibility: pd.DataFrame,
    data_root: Path,
    cutoff: str,
) -> dict[str, Any]:
    cutoff_ts = pd.Timestamp(cutoff)
    short_eligibility = eligibility.loc[:cutoff_ts]
    short_panels = {name: frame.loc[:cutoff_ts] for name, frame in panels.items()}
    short_atoms = _ranked_sources(
        sources, catalog=catalog, panels=short_panels,
        eligibility=short_eligibility, data_root=data_root, needed_atoms=needed_atoms,
    )
    perturbed_panels: dict[str, pd.DataFrame] = {}
    for number, (name, frame) in enumerate(panels.items(), start=1):
        changed = frame.copy()
        future = changed.index > cutoff_ts
        # Field-specific positive affine changes preserve valid domains while
        # making accidental future access observable.
        changed.loc[future] = changed.loc[future] * (1.37 + number * 0.03) + number
        perturbed_panels[name] = changed
    perturbed_atoms = _ranked_sources(
        sources, catalog=catalog, panels=perturbed_panels,
        eligibility=eligibility, data_root=data_root, needed_atoms=needed_atoms,
    )
    rows: list[dict[str, Any]] = []
    for spec in candidate_specs:
        cid = str(spec["id"])
        full = candidate_signals[cid].loc[:cutoff_ts]
        short = compose_candidate(spec, short_atoms, short_eligibility).reindex_like(full)
        perturbed = compose_candidate(spec, perturbed_atoms, eligibility).loc[:cutoff_ts].reindex_like(full)
        mask_equal_short = full.isna().equals(short.isna())
        mask_equal_perturbed = full.isna().equals(perturbed.isna())
        short_values = (full - short).abs().to_numpy(dtype=float)
        perturbed_values = (full - perturbed).abs().to_numpy(dtype=float)
        max_short = float(np.nanmax(short_values)) if np.isfinite(short_values).any() else 0.0
        max_perturbed = (
            float(np.nanmax(perturbed_values)) if np.isfinite(perturbed_values).any() else 0.0
        )
        passed = bool(mask_equal_short and mask_equal_perturbed and max_short <= 1e-7 and max_perturbed <= 1e-7)
        rows.append({
            "candidate_id": cid,
            "missing_mask_truncated_equal": mask_equal_short,
            "missing_mask_perturbed_equal": mask_equal_perturbed,
            "max_abs_diff_truncated": max_short,
            "max_abs_diff_future_perturbed": max_perturbed,
            "leak_check_pass": passed,
        })
    return {"cutoff": cutoff, "rows": rows, "all_pass": all(row["leak_check_pass"] for row in rows)}


def evaluate(args: argparse.Namespace) -> None:
    plan_path = args.plan.resolve()
    plan = json.loads(plan_path.read_text())
    if plan.get("schema_version") != "all_etf_daily_forward_plan_v1":
        raise ValueError("unexpected PLAN schema")
    config_path = next(
        Path(raw) for raw in plan["file_contract"]
        if raw.endswith("all_etf_daily_discovery_v1.yaml")
    )
    config = yaml.safe_load(config_path.read_text())
    root = Path(str(config["data"]["cache_root"])).resolve()
    _verify_plan(plan_path, plan, root)
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"evaluation output must be new and empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    population = config["population"]
    surfaces = plan["surfaces"]
    execution = plan["execution"]
    context = load_all_etf_daily(
        root,
        start=str(config["data"]["start"]),
        as_of=str(surfaces["forward_end"]),
        min_history_sessions=int(population["min_history_sessions"]),
        liquidity_window=int(population["liquidity_window"]),
        min_median_amount_thousand=float(population["min_median_amount_thousand"]),
    )
    catalog = _catalog(config)
    candidate_specs = list(plan["candidates"])
    candidate_sources = _candidate_sources({"candidates": candidate_specs})
    candidate_atoms = _candidate_atoms({"candidates": candidate_specs})
    control_sources = {str(row["source"]) for row in config["controls"]}
    control_atoms = {str(row["atom"]) for row in config["controls"]}
    atoms = _ranked_sources(
        candidate_sources | control_sources,
        catalog=catalog,
        panels=context.panels,
        eligibility=context.eligibility,
        data_root=root,
        needed_atoms=candidate_atoms | control_atoms,
    )
    controls = {
        str(row["atom"]): atoms[str(row["atom"])] for row in config["controls"]
    }
    signals = {
        str(spec["id"]): compose_candidate(spec, atoms, context.eligibility)
        for spec in candidate_specs
    }
    leak = _leak_check(
        signals,
        candidate_specs,
        catalog=catalog,
        sources=candidate_sources | control_sources,
        needed_atoms=candidate_atoms | control_atoms,
        panels=context.panels,
        eligibility=context.eligibility,
        data_root=root,
        cutoff=str(surfaces["validation_end"]),
    )
    _json(output / "future_leak_check.json", leak)
    if not leak["all_pass"]:
        raise ValueError("future dependency check failed; no factor verdict produced")
    forward = executable_forward_return(
        context.panels["open"],
        entry_lag=int(execution["entry_lag_sessions"]),
        horizon=int(execution["horizon"]),
    )
    gates = _gates(plan["forward_gates"])
    admitted: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    for spec in candidate_specs:
        cid = str(spec["id"])
        references = {**controls, **admitted}
        row, _ = evaluate_forward_candidate(
            signals[cid],
            forward,
            context.eligibility,
            references,
            candidate_id=cid,
            direction=int(spec["expected_sign"]),
            start=str(surfaces["forward_start"]),
            end=str(surfaces["forward_end"]),
            calendar=context.sessions,
            entry_lag=int(execution["entry_lag_sessions"]),
            horizon=int(execution["horizon"]),
            gates=gates,
        )
        correlations = {
            prior: mean_abs_daily_rank_corr(
                signals[cid], prior_signal, context.eligibility,
                min_names=gates.min_names,
                start=str(surfaces["forward_start"]),
                end=str(surfaces["forward_end"]),
            )
            for prior, prior_signal in admitted.items()
        }
        finite = {name: value for name, value in correlations.items() if np.isfinite(value)}
        missing_corr = len(finite) != len(correlations)
        worst = max(finite, key=finite.get) if finite else ""
        max_corr = float(finite[worst]) if worst else 0.0
        redundancy_pass = bool(not missing_corr and max_corr < gates.max_abs_rank_corr)
        if not redundancy_pass:
            failures = [value for value in str(row["gate_failures"]).split(";") if value]
            failures.append("rank_correlation_missing" if missing_corr else "rank_correlation_redundancy")
            row["gate_failures"] = ";".join(failures)
        row["max_abs_rank_corr"] = max_corr
        row["max_abs_rank_corr_vs"] = worst
        row["rank_correlation_pass"] = redundancy_pass
        row["gate_pass"] = bool(row["intrinsic_pass"] and redundancy_pass)
        if row["gate_pass"]:
            admitted[cid] = signals[cid] * float(spec["expected_sign"])
        rows.append(row)
        print(
            f"[referee] {cid} pass={row['gate_pass']} "
            f"IC={row['forward_mean_ic']:.4f} t={row['forward_hac_t']:.2f} "
            f"top={row['top_excess_bp']:.1f}bp failures={row['gate_failures']}",
            flush=True,
        )
    metrics = pd.DataFrame(rows)
    metrics.to_csv(output / "candidate_metrics.csv", index=False)
    admitted_rows = [
        {
            **spec,
            "forward_metrics": next(row for row in rows if row["candidate_id"] == spec["id"]),
        }
        for spec in candidate_specs if spec["id"] in admitted
    ]
    _json(output / "admitted_factors.json", {"count": len(admitted_rows), "factors": admitted_rows})
    report = [
        "# Broad ETF forward factor verdict",
        "",
        f"- Candidates: {len(candidate_specs)}",
        f"- Admitted independent factors: {len(admitted_rows)}",
        f"- Forward window: {surfaces['forward_start']} through {surfaces['forward_end']}",
        "- Benchmark: same-day eligible equal-weight ETF cross-section",
        "- Signal/entry/exit: D close / D+2 open / D+7 open",
        f"- Future-dependency check: {'PASS' if leak['all_pass'] else 'FAIL'}",
        "",
        "## Admitted IDs",
        "",
        ", ".join(admitted) if admitted else "None",
    ]
    (output / "REPORT.md").write_text("\n".join(report) + "\n")
    manifest = {
        "schema_version": "all_etf_daily_forward_evaluation_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": sys.argv,
        "plan": str(plan_path),
        "plan_sha256": file_sha256(plan_path),
        "plan_seal_ok_at_end": verify_plan_seal(plan_path),
        "candidate_count": len(candidate_specs),
        "admitted_count": len(admitted_rows),
        "future_leak_check_pass": leak["all_pass"],
    }
    _json(output / "run_manifest.json", manifest)
    _verify_plan(plan_path, plan, root)
    print(f"Forward evaluation complete: admitted={len(admitted_rows)} output={output}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--config", type=Path, required=True)
    plan.add_argument("--candidates", type=Path, required=True)
    plan.add_argument("--discovery-output", type=Path, required=True)
    plan.add_argument("--output", type=Path, required=True)
    run = sub.add_parser("evaluate")
    run.add_argument("--plan", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    create_plan(arguments) if arguments.mode == "plan" else evaluate(arguments)
