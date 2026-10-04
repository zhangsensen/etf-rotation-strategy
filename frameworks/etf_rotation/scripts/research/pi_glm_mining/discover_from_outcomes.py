#!/usr/bin/env python3
"""Discover ETF factor candidates from historical winner/loser differences.

The ``discover`` command builds causal atom ranks, uses only the configured
discovery surface to profile future H5 winners versus losers, and writes a
bounded candidate proposal.  The ``plan`` command validates that proposal and
hands it to the existing v4.3 engine's immutable PLAN writer.  Evaluation is
still performed by the existing engine; this script does not contain a second
referee.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import math
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd
import yaml

ETF_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ETF_ROOT / "src"))

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core.etf_data_provenance import hash_research_inputs
from etf_strategy.core.etf_factor_grammar import build_pit_eligibility, cross_sectional_rank
from etf_strategy.core.etf_outcome_discovery import (
    DiscoveryAtom,
    DiscoverySettings,
    distill_candidates,
    profile_atoms,
)
from etf_strategy.core.family_registry import load_builtin_families, resolve_family


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        return numeric if np.isfinite(numeric) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2) + "\n")


def _load_engine(workspace: Path | None = None, engine_path: Path | None = None) -> tuple[ModuleType, Path]:
    if engine_path is not None:
        path = engine_path.resolve()
    elif workspace is not None:
        path = (
            workspace.resolve()
            / "frameworks/etf_rotation/scripts/research/pi_round002_mine.py"
        )
    else:
        path = (
            ETF_ROOT
            / "scripts/research/pi_glm_mining/round_drivers/pi_round002_mine.py"
        ).resolve()
    if not path.exists():
        raise FileNotFoundError(f"v4.3 engine not found: {path}")
    if workspace is None and engine_path is None:
        parsed = ast.parse(path.read_text(), filename=str(path))
        version = ""
        for node in parsed.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not any(isinstance(target, ast.Name) and target.id == "REFEREE_VERSION" for target in targets):
                continue
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                version = value.value
                break
        if not version.startswith("v4.3_"):
            raise ValueError(f"tracked outcome discovery requires v4.3 engine, got {version!r}")
        identity = ModuleType("etf_v43_tracked_identity")
        identity.REFEREE_VERSION = version
        return identity, path
    spec = importlib.util.spec_from_file_location("etf_v43_discovery_bridge", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load engine: {path}")
    module = importlib.util.module_from_spec(spec)
    original_argv = sys.argv
    try:
        sys.argv = [str(path)]
        spec.loader.exec_module(module)
    finally:
        sys.argv = original_argv
    version = str(getattr(module, "REFEREE_VERSION", ""))
    if not version.startswith("v4.3_"):
        raise ValueError(f"outcome discovery requires v4.3 engine, got {version!r}")
    return module, path


def _resolve_catalog(config: dict[str, Any]) -> tuple[Path, list[dict[str, Any]]]:
    value = Path(str(config["family_catalog"]))
    catalog_path = value if value.is_absolute() else (ETF_ROOT / value).resolve()
    catalog = yaml.safe_load(catalog_path.read_text())
    rows = list(catalog.get("available_families", []))
    if not rows:
        raise ValueError("family catalog is empty")
    return catalog_path, rows


def _settings(config: dict[str, Any]) -> DiscoverySettings:
    discovery = config["discovery"]
    execution = config["execution"]
    distillation = config["distillation"]
    return DiscoverySettings(
        top_k=int(discovery["top_k"]),
        min_names=int(discovery["min_names"]),
        horizon=int(execution["horizon"]),
        entry_lag=int(execution["entry_lag_sessions"]),
        min_days=int(discovery["min_days"]),
        min_year_days=int(discovery["min_year_days"]),
        min_eligible_years=int(discovery["min_eligible_years"]),
        min_year_direction_agreement=float(discovery["min_year_direction_agreement"]),
        direction_fit_end=(
            str(discovery["direction_fit_end"])
            if discovery.get("direction_fit_end") is not None
            else None
        ),
        min_direction_fit_days=int(discovery.get("min_direction_fit_days", 120)),
        max_atomic_candidates=int(distillation["max_atomic_candidates"]),
        max_candidates_per_family=int(distillation["max_candidates_per_family"]),
        pair_pool_size=int(distillation["pair_pool_size"]),
        max_pair_candidates=int(distillation["max_pair_candidates"]),
        max_abs_leg_rank_corr=float(distillation["max_abs_leg_rank_corr"]),
        min_pair_score_gain=float(distillation["min_pair_score_gain"]),
    )


def _build_ranked_atoms(
    config: dict[str, Any],
    data_root: Path,
    panels: dict[str, pd.DataFrame],
    eligibility_all: pd.DataFrame,
    symbols: list[str],
    selected_sources: set[str] | None,
) -> tuple[dict[str, pd.DataFrame], dict[str, DiscoveryAtom], dict[str, str], set[str]]:
    catalog_path, rows = _resolve_catalog(config)
    load_builtin_families()
    ranked: dict[str, pd.DataFrame] = {}
    definitions: dict[str, DiscoveryAtom] = {}
    config_hashes: dict[str, str] = {str(catalog_path): _sha256(catalog_path)}
    frequencies: set[str] = set()
    for catalog_row in rows:
        source = str(catalog_row["source"])
        if selected_sources is not None and source not in selected_sources:
            continue
        print(f"[materialize] {source}", flush=True)
        config_value = Path(str(catalog_row["config"]))
        source_path = (
            config_value if config_value.is_absolute() else (ETF_ROOT / config_value).resolve()
        )
        source_config = yaml.safe_load(source_path.read_text())
        if str(source_config["factor_source"]) != source:
            raise ValueError(f"catalog/config source mismatch: {source}")
        frequency = str(source_config.get("frequency", ""))
        if frequency and frequency not in {"1d", "adj_factor"}:
            frequencies.add(frequency)
        provider = resolve_family(source)
        space = provider.builder(
            panels, eligibility_all, data_root, source_config
        )
        config_hashes[str(source_path)] = _sha256(source_path)
        for atom_row in source_config["atoms"]:
            name = str(atom_row["name"])
            family = str(atom_row["family"])
            if name in definitions:
                raise ValueError(f"duplicate atom name across sources: {name}")
            if name not in space:
                raise ValueError(f"{source} did not materialize atom {name}")
            definitions[name] = DiscoveryAtom(
                name=name,
                source=source,
                family=family,
                config=str(source_path),
            )
            ranked[name] = cross_sectional_rank(
                space[name].reindex(index=eligibility_all.index, columns=symbols),
                eligibility_all[symbols],
            )
    if not ranked:
        raise ValueError("source filter produced no atoms")
    return ranked, definitions, config_hashes, frequencies


def _control_frames(
    config: dict[str, Any],
    ranked: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], list[dict[str, str]]]:
    controls: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, str]] = []
    for row in config.get("controls", []):
        source, atom = str(row["source"]), str(row["atom"])
        if atom not in ranked:
            raise ValueError(
                f"control {source}:{atom} is not materialized; include its source in --sources"
            )
        controls[atom] = ranked[atom]
        rows.append({"source": source, "atom": atom})
    if not controls:
        raise ValueError("formal outcome discovery requires at least one baseline control")
    return controls, rows


def _new_output(path: Path) -> Path:
    output = path.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"output directory must be new and empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    return output


def _raw_forward(open_prices: pd.DataFrame, horizon: int, lag: int) -> pd.DataFrame:
    """Executable label: enter open(D+lag), leave open(D+lag+horizon)."""
    entry = open_prices.shift(-lag)
    exit_price = open_prices.shift(-(lag + horizon))
    return (exit_price / entry - 1.0).where((entry > 0.0) & (exit_price > 0.0))


def _load_discovery_context(
    config: dict[str, Any],
) -> tuple[Path, dict[str, pd.DataFrame], pd.DataFrame, list[str], dict[int, pd.DataFrame]]:
    data = config["data"]
    data_root = Path(str(data["canonical_data_root"])).expanduser().resolve()
    universe_value = Path(str(data["universe_config"]))
    universe_path = (
        universe_value
        if universe_value.is_absolute()
        else (ETF_ROOT.parents[1] / universe_value).resolve()
    )
    panels = load_canonical_daily(data_root, universe_path, as_of=str(data["as_of"]))
    eligibility_all = build_pit_eligibility(
        panels,
        int(config["population"]["min_history_sessions"]),
        bool(config["population"]["require_positive_volume"]),
    )
    roles = set(config["population"]["ranking_roles"])
    universe = json.loads(universe_path.read_text())["etfs"]
    symbols = [row["ts_code"] for row in universe if row["role"] in roles]
    expected = int(config["population"]["expected_symbols"])
    if len(symbols) != expected:
        raise ValueError(f"expected {expected} symbols, got {len(symbols)}")
    settings = _settings(config)
    eligibility = eligibility_all[symbols]
    forward = {
        settings.horizon: _raw_forward(
            panels["open"][symbols], settings.horizon, settings.entry_lag
        ).where(eligibility)
    }
    return data_root, panels, eligibility_all, symbols, forward


def cmd_discover(args: argparse.Namespace) -> None:
    output = _new_output(args.output)
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text())
    settings = _settings(config)
    settings.validate()
    engine, engine_path = _load_engine(args.workspace, args.engine)
    data_root, panels, eligibility_all, symbols, forward = _load_discovery_context(config)
    source_filter = set(args.sources.split(",")) if args.sources else None
    required_control_sources = {str(row["source"]) for row in config.get("controls", [])}
    if source_filter is not None:
        source_filter |= required_control_sources
    ranked, definitions, config_hashes, frequencies = _build_ranked_atoms(
        config,
        data_root,
        panels,
        eligibility_all,
        symbols,
        source_filter,
    )
    controls, control_rows = _control_frames(config, ranked)
    discovery = config["discovery"]
    profiles = profile_atoms(
        ranked,
        definitions,
        forward[settings.horizon],
        eligibility_all[symbols],
        controls=controls,
        settings=settings,
        discovery_start=discovery["start"],
        discovery_end=discovery["end"],
    )
    candidates, pair_profiles = distill_candidates(
        profiles,
        ranked,
        definitions,
        forward[settings.horizon],
        eligibility_all[symbols],
        controls=controls,
        settings=settings,
        discovery_start=discovery["start"],
        discovery_end=discovery["end"],
    )
    profiles.to_csv(output / "atom_profiles.csv", index=False)
    pair_profiles.to_csv(output / "pair_profiles.csv", index=False)
    proposal = {
        "schema_version": "etf_outcome_candidate_proposal_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_role": "discovery_only",
        "strategy_usable": False,
        "candidate_generation": "same_date_future_winner_loser_profile_after_controls",
        "engine_referee_version": engine.REFEREE_VERSION,
        "signal_time": config["execution"]["signal_time"],
        "entry_time": f"open(D+{settings.entry_lag})",
        "exit_time": f"open(D+{settings.entry_lag + settings.horizon})",
        "return_label": (
            f"open(D+{settings.entry_lag + settings.horizon})/"
            f"open(D+{settings.entry_lag})-1"
        ),
        "discovery_surface": {
            "start": str(discovery["start"]),
            "end": str(discovery["end"]),
        },
        "population": {"symbols": symbols, "count": len(symbols)},
        "controls": control_rows,
        "settings": settings.__dict__,
        "n_atoms_profiled": int(len(profiles)),
        "n_stable_atoms": int(profiles["stable_lead"].sum()),
        "hypothesis_search_upper_bound": int(
            len(profiles)
            + math.comb(min(int(profiles["stable_lead"].sum()), settings.pair_pool_size), 2)
        ),
        "n_candidates": len(candidates),
        "candidates": candidates,
    }
    proposal_path = output / "CANDIDATE_PROPOSAL.json"
    _write_json(proposal_path, proposal)
    input_hashes = hash_research_inputs(data_root, symbols, frequencies)
    manifest = {
        "schema_version": "etf_outcome_discovery_run_v1",
        "command": sys.argv,
        "config": str(config_path),
        "config_sha256": _sha256(config_path),
        "engine": str(engine_path),
        "engine_sha256": _sha256(engine_path),
        "discovery_entry_sha256": _sha256(Path(__file__).resolve()),
        "discovery_core_sha256": _sha256(
            ETF_ROOT / "src/etf_strategy/core/etf_outcome_discovery.py"
        ),
        "referee_version": engine.REFEREE_VERSION,
        "source_config_hashes": config_hashes,
        "input_hashes": input_hashes,
        "proposal": str(proposal_path),
        "proposal_sha256": _sha256(proposal_path),
        "outcomes_are_features": False,
        "candidate_formula_inputs": "causal atom ranks only",
    }
    _write_json(output / "run_manifest.json", manifest)
    print(
        f"Outcome discovery complete: atoms={len(profiles)} "
        f"stable={int(profiles['stable_lead'].sum())} candidates={len(candidates)}"
    )
    for candidate in candidates:
        left = candidate["left"]["name"]
        right = candidate["right"]["name"]
        print(
            candidate["id"], candidate["operator"], left,
            right if right != left else "", "sign", candidate["expected_sign"],
        )
    print(f"Wrote proposal to {proposal_path}")


def cmd_plan(args: argparse.Namespace) -> None:
    proposal_path = args.proposal.resolve()
    proposal = json.loads(proposal_path.read_text())
    if proposal.get("schema_version") != "etf_outcome_candidate_proposal_v1":
        raise ValueError("unsupported candidate proposal schema")
    candidates = proposal.get("candidates") or []
    if not candidates:
        raise ValueError("candidate proposal is empty; valid zero results cannot be planned")
    engine, _ = _load_engine(args.workspace.resolve())
    if proposal.get("engine_referee_version") != engine.REFEREE_VERSION:
        raise ValueError("proposal/engine referee version mismatch")
    campaign_root = args.output.resolve().parent
    if campaign_root not in engine.CAMPAIGN_OUTPUT_ROOTS:
        engine.CAMPAIGN_OUTPUT_ROOTS = (*engine.CAMPAIGN_OUTPUT_ROOTS, campaign_root)
    engine.CANDIDATES = candidates
    engine.ROUND_ID = str(args.round_id)
    engine.cmd_plan(SimpleNamespace(output=args.output.resolve()))
    plan_path = args.output.resolve() / "PLAN.json"
    locked_plan = json.loads(plan_path.read_text())
    locked_plan["miner"] = "openai/gpt-5.6-luna-assisted_outcome_discovery"
    locked_plan["candidate_generation"] = proposal["candidate_generation"]
    locked_plan["candidate_proposal_sha256"] = _sha256(proposal_path)
    locked_plan["candidate_generation_search_upper_bound"] = int(
        proposal["hypothesis_search_upper_bound"]
    )
    locked_plan["preregistration_note"] = (
        "Candidates and signs were generated on the sealed outcome-discovery surfaces; "
        "this PLAN was written before v4.3 evaluation and is immutable after sealing."
    )
    for candidate in locked_plan["candidates"]:
        candidate["novelty"] = "bounded outcome-profile proposal; see candidate_proposal_sha256"
    _write_json(plan_path, locked_plan)
    engine.write_plan_seal(plan_path)
    metadata = {
        "proposal": str(proposal_path),
        "proposal_sha256": _sha256(proposal_path),
        "round_id": str(args.round_id),
    }
    _write_json(args.output.resolve() / "DISCOVERY_PROPOSAL_REF.json", metadata)
    print(f"Locked v4.3 plan from outcome proposal: {args.output.resolve()}")


def cmd_freeze_pairs(args: argparse.Namespace) -> None:
    """Materialize a previously frozen pair list without touching audit results."""
    base_path = args.base_proposal.resolve()
    profiles_path = args.atom_profiles.resolve()
    pairs_path = args.pairs.resolve()
    base = json.loads(base_path.read_text())
    profiles = pd.read_csv(profiles_path).set_index("name", drop=False)
    specification = yaml.safe_load(pairs_path.read_text())
    if specification.get("selection_surface") != "discovery_only_before_v43_evaluation":
        raise ValueError("frozen pairs must declare a discovery-only pre-evaluation surface")
    candidates: list[dict[str, Any]] = []
    seen: set[frozenset[str]] = set()
    for index, pair in enumerate(specification.get("pairs", []), start=1):
        left_name, right_name = str(pair["left"]), str(pair["right"])
        key = frozenset((left_name, right_name))
        if len(key) != 2 or key in seen:
            raise ValueError(f"duplicate or degenerate frozen pair: {left_name}, {right_name}")
        seen.add(key)
        left, right = profiles.loc[left_name], profiles.loc[right_name]
        if not bool(left["stable_lead"]) or not bool(right["stable_lead"]):
            raise ValueError(f"frozen pair uses an unstable discovery leg: {left_name}, {right_name}")
        if int(left["direction"]) != 1 or int(right["direction"]) != -1:
            raise ValueError(f"frozen rank spread must be positive-minus-negative: {left_name}, {right_name}")
        if str(left["family"]) == str(right["family"]):
            raise ValueError(f"frozen pair must be cross-family: {left_name}, {right_name}")

        def leg(row: pd.Series) -> dict[str, str]:
            return {
                "name": str(row["name"]),
                "source": str(row["source"]),
                "family": str(row["family"]),
                "config": str(row["config"]),
            }

        candidates.append(
            {
                "id": f"LUNA{index:03d}",
                "operator": "rank_spread",
                "left": leg(left),
                "right": leg(right),
                "mechanism": f"luna_frozen:{left['family']}_minus_{right['family']}",
                "hypothesis": (
                    f"Discovery-only Luna review predicted high {left_name} and low "
                    f"{right_name}; the signed cross-family spread was frozen before "
                    "the first v4.3 batch evaluation."
                ),
                "expected_sign": 1,
                "discovery_evidence": {
                    "left_controlled_mean_ic": float(left["controlled_mean_ic"]),
                    "right_controlled_mean_ic": float(right["controlled_mean_ic"]),
                    "selection_surface": specification["selection_surface"],
                },
            }
        )
    if not candidates:
        raise ValueError("frozen pair list is empty")
    proposal = {
        **{key: value for key, value in base.items() if key != "candidates"},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_generation": "luna_frozen_mechanism_pairs_before_round_215_audit",
        "selection_author": str(specification["selection_author"]),
        "selection_surface": specification["selection_surface"],
        "frozen_pair_spec_sha256": _sha256(pairs_path),
        "base_proposal_sha256": _sha256(base_path),
        "n_candidates": len(candidates),
        "candidates": candidates,
    }
    args.output.resolve().mkdir(parents=True, exist_ok=False)
    _write_json(args.output.resolve() / "CANDIDATE_PROPOSAL.json", proposal)
    _write_json(
        args.output.resolve() / "run_manifest.json",
        {
            "base_proposal": str(base_path),
            "base_proposal_sha256": _sha256(base_path),
            "atom_profiles": str(profiles_path),
            "atom_profiles_sha256": _sha256(profiles_path),
            "frozen_pairs": str(pairs_path),
            "frozen_pairs_sha256": _sha256(pairs_path),
            "outcomes_are_features": False,
        },
    )
    print(f"Frozen Luna proposal complete: candidates={len(candidates)} output={args.output.resolve()}")


def cmd_evaluate(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    plan = json.loads((output / "PLAN.json").read_text())
    engine, _ = _load_engine(args.workspace.resolve())
    if plan.get("engine_referee_version", engine.REFEREE_VERSION) != engine.REFEREE_VERSION:
        raise ValueError("PLAN/engine referee version mismatch")
    engine.ROUND_ID = str(plan["round_id"])
    engine.cmd_evaluate(
        SimpleNamespace(output=output, mode=str(args.mode), only=args.only)
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    discover = sub.add_parser("discover")
    discover.add_argument(
        "--workspace",
        type=Path,
        help="legacy runtime workspace; only used to locate its v4.3 engine copy",
    )
    discover.add_argument(
        "--engine",
        type=Path,
        help="explicit v4.3 engine; defaults to the tracked source entry",
    )
    discover.add_argument("--config", type=Path, required=True)
    discover.add_argument("--output", type=Path, required=True)
    discover.add_argument(
        "--sources",
        help="comma-separated bounded source subset; configured control sources are always added",
    )
    plan = sub.add_parser("plan")
    plan.add_argument("--workspace", type=Path, required=True)
    plan.add_argument("--proposal", type=Path, required=True)
    plan.add_argument("--round-id", required=True)
    plan.add_argument("--output", type=Path, required=True)
    freeze = sub.add_parser("freeze-pairs")
    freeze.add_argument("--base-proposal", type=Path, required=True)
    freeze.add_argument("--atom-profiles", type=Path, required=True)
    freeze.add_argument("--pairs", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--workspace", type=Path, required=True)
    evaluate.add_argument("--output", type=Path, required=True)
    evaluate.add_argument("--mode", choices=["validate", "batch"], default="batch")
    evaluate.add_argument("--only")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "discover":
        cmd_discover(args)
    elif args.command == "freeze-pairs":
        cmd_freeze_pairs(args)
    elif args.command == "plan":
        cmd_plan(args)
    else:
        cmd_evaluate(args)


if __name__ == "__main__":
    main()
