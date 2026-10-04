#!/usr/bin/env python3
"""Rejudge frozen ETF mining rounds under referee v4.

The program reconstructs every signal with that round's engine and config
snapshots.  It compares the reconstructed discovery IC with the frozen metric
before calculating a v4 verdict.  Any mismatch makes the run fail closed.

This is inventory cleanup.  Reusing discovery/audit data cannot certify a
factor; a passing row remains a lead for a future confirmation surface.
"""

from __future__ import annotations

import argparse
import importlib
import json
import pkgutil
import re
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[6]
ETF_ROOT = REPO / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF_ROOT / "src"))

from etf_strategy.core.etf_mining_referee import (
    block_t,
    campaign_bonferroni_pass,
    newey_west_t,
    paired_increment_stats,
    topk_series,
)

ROUND_RE = re.compile(r"round_\d+$")
DISCOVERY_END = pd.Timestamp("2023-12-31")
AUDIT_START = pd.Timestamp("2024-01-01")
AUDIT_END = pd.Timestamp("2025-04-30")
PRIMARY = 5
CAMPAIGN_ALPHA = 0.05
CAMPAIGN_BUDGET = 6000
PAIR_OPERATORS = {"rank_spread", "rank_interaction", "rank_ratio", "rank_product"}


def frozen_rounds(workspace: Path, selected: set[str] | None = None) -> list[Path]:
    """Return canonical numeric rounds; replay and rescore directories are excluded."""
    rounds = []
    for path in (workspace / "outputs").iterdir():
        if not path.is_dir() or not ROUND_RE.fullmatch(path.name):
            continue
        if selected and path.name not in selected:
            continue
        if all((path / name).exists() for name in ("PLAN.json", "STATUS.json", "candidate_metrics.csv")):
            rounds.append(path)
    return sorted(rounds, key=lambda path: int(path.name.split("_")[1]))


def load_snapshot_engine(round_dir: Path, workspace: Path) -> types.ModuleType:
    """Execute frozen engine text with the original workspace path semantics."""
    frozen_source_root = round_dir / "snapshots/source"
    if not (frozen_source_root / "etf_strategy").exists():
        frozen_source_root = workspace / "frameworks/etf_rotation/src"
    frozen_family_path = frozen_source_root / "etf_strategy/core/families"
    # The v4 statistic functions imported by this audit module remain bound.
    # Signal construction imports are reset and loaded from the frozen tree.
    for name in [name for name in sys.modules if name == "etf_strategy" or name.startswith("etf_strategy.")]:
        del sys.modules[name]
    sys.path.insert(0, str(frozen_source_root))
    snapshot = round_dir / "snapshots/pi_round002_mine.py"
    if not snapshot.exists():
        raise FileNotFoundError(f"missing engine snapshot: {snapshot}")
    live_path = workspace / "frameworks/etf_rotation/scripts/research/pi_round002_mine.py"
    module = types.ModuleType(f"frozen_{round_dir.name}")
    module.__file__ = str(live_path)
    module.__dict__["__name__"] = module.__name__
    exec(compile(snapshot.read_text(), str(live_path), "exec"), module.__dict__)

    def load_frozen_families() -> None:
        prefix = "etf_strategy.core.families."
        for item in pkgutil.iter_modules([str(frozen_family_path)], prefix):
            importlib.import_module(item.name)

    module.load_builtin_families = load_frozen_families
    return module


def bind_snapshot_configs(engine: types.ModuleType, round_dir: Path, plan: dict) -> None:
    mapping: dict[str, Path] = {}
    for candidate in plan.get("candidates", []):
        for side in ("left", "right"):
            leg = candidate.get(side)
            if not isinstance(leg, dict) or not leg.get("source") or not leg.get("config"):
                continue
            frozen = round_dir / "snapshots" / Path(leg["config"]).name
            if not frozen.exists():
                raise FileNotFoundError(f"missing config snapshot: {frozen}")
            mapping[str(leg["source"])] = frozen

    def snapshot_config(source: str) -> Path:
        if source not in mapping:
            raise KeyError(f"source has no config snapshot: {source}")
        return mapping[source]

    engine._config_path = snapshot_config


def topk_metrics(signal, forward, eligibility, direction: float, min_pairs: int) -> dict:
    series = topk_series(
        signal,
        forward,
        eligibility,
        direction=direction,
        k=3,
        min_names=max(min_pairs, 4),
    )
    discovery = series.excess.loc[:DISCOVERY_END].dropna()
    audit = series.excess.loc[AUDIT_START:AUDIT_END].dropna()
    t_disc_block, _ = block_t(discovery, PRIMARY)
    t_audit_block, _ = block_t(audit, PRIMARY)
    t_disc_hac = newey_west_t(discovery, PRIMARY - 1)
    t_audit_hac = newey_west_t(audit, PRIMARY - 1)
    campaign_pass, pvalue = campaign_bonferroni_pass(
        t_disc_hac, alpha=CAMPAIGN_ALPHA, hypothesis_budget=CAMPAIGN_BUDGET
    )
    disc_precision = series.precision.loc[discovery.index].dropna()
    audit_precision = series.precision.loc[audit.index].dropna()
    disc_baseline = (3 / series.eligible_count.loc[discovery.index]).mean()
    audit_baseline = (3 / series.eligible_count.loc[audit.index]).mean()
    return {
        "series": series.excess,
        "discovery_bp": float(discovery.mean() * 1e4),
        "discovery_t_block": t_disc_block,
        "discovery_t_hac": t_disc_hac,
        "audit_bp": float(audit.mean() * 1e4),
        "audit_t_block": t_audit_block,
        "audit_t_hac": t_audit_hac,
        "discovery_precision": float(disc_precision.mean()),
        "audit_precision": float(audit_precision.mean()),
        "discovery_precision_baseline": float(disc_baseline),
        "audit_precision_baseline": float(audit_baseline),
        "campaign_p": pvalue,
        "campaign_pass": campaign_pass,
    }


def base_shadow_corr(engine, signal, panels, eligibility, symbols, signal_index) -> tuple[float, str]:
    close = panels["close"][symbols].where(eligibility)
    high = panels["high"][symbols].where(eligibility)
    low = panels["low"][symbols].where(eligibility)
    ret1 = close / close.shift(1) - 1.0
    market = ret1.mean(axis=1)
    references = {
        "RET1": ret1,
        "RET20": close / close.shift(20) - 1.0,
        "PRICE_POS_20": (close - low.rolling(20, min_periods=10).min())
        / (high.rolling(20, min_periods=10).max() - low.rolling(20, min_periods=10).min()),
        "PRICE_POS_250": (close - low.rolling(250, min_periods=120).min())
        / (high.rolling(250, min_periods=120).max() - low.rolling(250, min_periods=120).min()),
        "BETA_60": ret1.rolling(60, min_periods=40).cov(market).div(
            market.rolling(60, min_periods=40).var(), axis=0
        ),
    }
    vector = engine._stride_vector(signal)
    correlations = {}
    for name, reference in references.items():
        ranked = reference.rank(axis=1, pct=True).reindex(index=signal_index, columns=symbols)
        correlations[name] = engine._pairwise_pearson(vector, engine._stride_vector(ranked))
    finite = {name: value for name, value in correlations.items() if np.isfinite(value)}
    if len(finite) != len(references):
        return float("nan"), "missing"
    worst = max(finite, key=lambda name: abs(finite[name]))
    return abs(float(finite[worst])), worst


def rejudge_round(round_dir: Path, workspace: Path, context: tuple | None) -> tuple[list[dict], tuple]:
    plan = json.loads((round_dir / "PLAN.json").read_text())
    status = json.loads((round_dir / "STATUS.json").read_text())
    metrics = pd.read_csv(round_dir / "candidate_metrics.csv").set_index("candidate_id")
    engine = load_snapshot_engine(round_dir, workspace)
    bind_snapshot_configs(engine, round_dir, plan)
    engine.load_builtin_families()
    if context is None:
        panels, eligibility_all, symbols, forward = engine._load_context()
        context = panels, eligibility_all, symbols, forward
    panels, eligibility_all, symbols, forward = context
    eligibility = eligibility_all[symbols]
    ranked = engine._build_atoms(panels, eligibility_all, symbols, plan)
    signal_index = ranked[next(iter(ranked))].index
    old = {str(row["id"]): row for row in status.get("candidates", [])}
    rows = []
    for candidate in plan.get("candidates", []):
        candidate_id = str(candidate["id"])
        direction = float(candidate.get("expected_sign", 0))
        if direction not in (-1.0, 1.0):
            raise ValueError(f"{round_dir.name}:{candidate_id}: missing preregistered direction")
        spec = engine._expression_spec(candidate)
        signal = engine.materialize_expression(spec, ranked)
        daily_ic, _ = engine.common_sample_spearman(
            signal, forward[PRIMARY], eligibility, engine.MIN_PAIRS
        )
        reconstructed_ic = float(daily_ic.loc[:DISCOVERY_END].dropna().mean())
        recorded_ic = float(metrics.loc[candidate_id, "discovery_ic"])
        fidelity_error = abs(reconstructed_ic - recorded_ic)
        result = {
            "round": round_dir.name,
            "candidate_id": candidate_id,
            "expression": spec.readable,
            "operator": candidate.get("operator", ""),
            "expected_sign": direction,
            "old_gate_pass": bool(old.get(candidate_id, {}).get("gate_pass", False)),
            "recorded_discovery_ic": recorded_ic,
            "reconstructed_discovery_ic": reconstructed_ic,
            "fidelity_error": fidelity_error,
            "fidelity_pass": bool(fidelity_error <= 1e-10),
        }
        if not result["fidelity_pass"]:
            result["v4_statistical_pass"] = False
            result["error"] = "snapshot_fidelity_mismatch"
            rows.append(result)
            continue

        top = topk_metrics(signal, forward[PRIMARY], eligibility, direction, engine.MIN_PAIRS)
        result.update({key: value for key, value in top.items() if key != "series"})
        result["signed_discovery_ic"] = reconstructed_ic * direction
        audit_ic = daily_ic.loc[AUDIT_START:AUDIT_END].dropna()
        result["signed_audit_ic"] = float(audit_ic.mean()) * direction
        result["leg_increment_pass"] = True
        if candidate.get("operator") in PAIR_OPERATORS:
            leg_passes = []
            for side in ("left", "right"):
                name = (candidate.get(side) or {}).get("name")
                if name not in ranked:
                    leg_passes.append(False)
                    continue
                leg_metrics = {
                    leg_direction: topk_metrics(
                        ranked[name], forward[PRIMARY], eligibility, leg_direction, engine.MIN_PAIRS
                    )
                    for leg_direction in (1.0, -1.0)
                }
                best_direction = max(
                    leg_metrics,
                    key=lambda leg_direction: np.nan_to_num(
                        leg_metrics[leg_direction]["discovery_t_hac"], nan=-np.inf
                    ),
                )
                increment = paired_increment_stats(
                    top["series"], leg_metrics[best_direction]["series"],
                    discovery_end=DISCOVERY_END, audit_start=AUDIT_START,
                    audit_end=AUDIT_END, horizon=PRIMARY,
                )
                for key, value in increment.items():
                    result[f"leg_{side}_{key}"] = value
                leg_passes.append(bool(
                    increment["discovery_t_hac"] >= 2.0
                    and increment["audit_t_hac"] >= 1.5
                    and increment["audit_bp"] > 0.0
                ))
            result["leg_increment_pass"] = len(leg_passes) == 2 and all(leg_passes)

        base_corr, base_name = base_shadow_corr(
            engine, signal, panels, eligibility, symbols, signal_index
        )
        result["base_max_abs_corr"] = base_corr
        result["base_max_vs"] = base_name
        base_limit = 0.60 if candidate.get("operator") in PAIR_OPERATORS else 0.70
        result["v4_statistical_pass"] = bool(
            result["signed_discovery_ic"] >= 0.01
            and result["signed_audit_ic"] >= 0.01
            and top["campaign_pass"]
            and top["discovery_t_block"] >= 2.0
            and top["audit_bp"] >= 5.0
            and top["audit_t_block"] >= 2.0
            and top["audit_t_hac"] >= 2.0
            and top["discovery_precision"] > top["discovery_precision_baseline"]
            and top["audit_precision"] > top["audit_precision_baseline"]
            and result["leg_increment_pass"]
            and np.isfinite(base_corr)
            and base_corr < base_limit
        )
        result["evidence_status"] = "historical_lead_not_certified"
        rows.append(result)
    return rows, context


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--round", action="append", dest="rounds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = set(args.rounds) if args.rounds else None
    round_dirs = frozen_rounds(args.workspace, selected)
    if not round_dirs:
        raise SystemExit("no canonical frozen rounds found")
    rows: list[dict] = []
    context = None
    for round_dir in round_dirs:
        round_rows, context = rejudge_round(round_dir, args.workspace, context)
        rows.extend(round_rows)
        print(
            round_dir.name,
            "candidates", len(round_rows),
            "fidelity_fail", sum(not row["fidelity_pass"] for row in round_rows),
            "v4_pass", sum(bool(row.get("v4_statistical_pass")) for row in round_rows),
            flush=True,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output, index=False)
    failures = [row for row in rows if not row["fidelity_pass"]]
    if failures:
        print(f"FAIL CLOSED: {len(failures)} snapshot fidelity mismatches", file=sys.stderr)
        return 2
    print(
        "DONE", "candidates", len(rows),
        "v4_statistical_pass", sum(bool(row.get("v4_statistical_pass")) for row in rows),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
