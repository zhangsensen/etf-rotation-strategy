#!/usr/bin/env python3
"""Build a de-duplicated ETF IC candidate shelf from a completed adjudication run."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core.etf_factor_grammar import (
    build_pit_eligibility,
    cross_sectional_rank,
    enumerate_expressions,
    parse_atoms,
)
from etf_strategy.core.etf_data_provenance import hash_config_dependencies, hash_research_inputs
from etf_strategy.core.etf_family_catalog import load_family_catalog
from etf_strategy.core.family_registry import load_builtin_families, resolve_family


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-data-root", type=Path, required=True)
    parser.add_argument("--universe-config", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--adjudication-output", type=Path, required=True)
    parser.add_argument("--shelf-config", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _deterministic_candidate_order(summary: pd.DataFrame, keys: set[str]) -> list[str]:
    """Order candidates by absolute IC and use the key as a stable tie-break."""
    ordered = summary.loc[sorted(keys)].copy().reset_index(drop=True)
    ordered["abs_discovery_ic"] = ordered["discovery_ic"].abs()
    return ordered.sort_values(
        ["abs_discovery_ic", "expression_key"],
        ascending=[False, True],
        kind="mergesort",
    )["expression_key"].tolist()


def _mechanism_id(family: str, expression: str, explicit: dict[str, str]) -> str:
    """Collapse pure lookback variants unless an explicit cross-family group exists."""
    if expression in explicit:
        return explicit[expression]
    base = re.sub(r"_(?:\d+)(?:_\d+)*$", "", expression)
    return f"{family}:{base}"


def _load_axis_map(config: dict[str, object]) -> tuple[dict[str, str], Path]:
    value = Path(str(config["economic_axis_taxonomy"]))
    path = value if value.is_absolute() else (ROOT / value).resolve()
    raw = yaml.safe_load(path.read_text())
    mapping: dict[str, str] = {}
    for axis, row in raw["axes"].items():
        for family in row["families"]:
            family = str(family)
            if family in mapping:
                raise ValueError(f"family assigned to multiple economic axes: {family}")
            mapping[family] = str(axis)
    return mapping, path


def _effective_factor_count(correlation: pd.DataFrame) -> float:
    if correlation.empty:
        return 0.0
    eigenvalues = np.linalg.eigvalsh(correlation.fillna(0.0).to_numpy())
    eigenvalues = np.clip(eigenvalues, 0.0, None)
    denominator = float(np.square(eigenvalues).sum())
    return float(eigenvalues.sum() ** 2 / denominator) if denominator > 0.0 else 0.0


def main() -> None:
    args = _args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory must be new and empty")
    output.mkdir(parents=True, exist_ok=True)
    config_path = args.shelf_config.resolve()
    config = yaml.safe_load(config_path.read_text())
    family_axis, taxonomy_path = _load_axis_map(config)
    run = args.adjudication_output.resolve()
    summary = pd.read_csv(run / "expression_decomposition.csv").set_index(
        "expression_key", drop=False
    )
    missing_axis = sorted(set(summary["true_family"].astype(str)) - set(family_axis))
    if missing_axis:
        raise ValueError(f"families missing from economic-axis taxonomy: {missing_axis}")
    raw_ic = pd.read_parquet(run / "daily_raw_ic.parquet")
    direction = np.sign(summary["discovery_ic"]).replace(0.0, np.nan)
    eligible = (
        summary["discovery_days"].ge(int(config["min_discovery_days"]))
        & summary["discovery_ic"].abs().ge(float(config["min_abs_discovery_ic"]))
        & summary["seen_audit_ic"].mul(direction).ge(
            float(config["min_abs_seen_audit_ic"])
        )
    )
    if bool(config["require_all_horizons_same_direction"]):
        eligible &= summary["all_horizons_same_direction"]
    if bool(config.get("require_identity_gate_pass", False)):
        eligible &= summary["identity_gate_pass"]

    year_columns: list[str] = []
    year_start = int(config["year_start"])
    year_end = int(config["year_end"])
    for year in range(year_start, year_end + 1):
        column = f"ic_{year}"
        year_columns.append(column)
        year_rows = raw_ic.loc[raw_ic.index.year == year]
        summary[column] = year_rows.mean().reindex(summary.index)
    year_signs = summary[year_columns].apply(np.sign)
    year_matches = year_signs.eq(direction, axis=0)
    summary["year_direction_count"] = year_matches.sum(axis=1)
    summary["year_direction_agreement"] = year_matches.mean(axis=1)
    eligible &= summary["year_direction_count"].ge(
        int(config["min_year_direction_count"])
    )
    candidate_keys = set(summary.index[eligible])

    load_builtin_families()
    universe_path = args.universe_config.resolve()
    universe = json.loads(universe_path.read_text())["etfs"]
    symbols = [row["ts_code"] for row in universe if row["role"] == "candidate"]
    panels = load_canonical_daily(
        args.canonical_data_root.resolve(), universe_path, as_of=args.as_of
    )
    all_eligibility = build_pit_eligibility(panels, 120, True)
    rank_eligibility = all_eligibility[symbols]
    catalog_path = args.catalog.resolve()
    vectors: dict[str, pd.Series] = {}
    scores: dict[str, pd.DataFrame] = {}
    intraday_frequencies: set[str] = set()
    discovery_end = pd.Timestamp(
        json.loads((run / "run_manifest.json").read_text())["surfaces"]["discovery_end"]
    )
    stride = int(config["rank_correlation_sample_stride"])
    source_paths = load_family_catalog(catalog_path, ROOT)
    for source_path in source_paths:
        mining = yaml.safe_load(source_path.read_text())
        if mining.get("frequency"):
            intraday_frequencies.add(str(mining["frequency"]))
        source = str(mining["factor_source"])
        provider = resolve_family(source)
        factor_space = provider.builder(
            panels, all_eligibility, args.canonical_data_root.resolve(), mining
        )
        for atom in parse_atoms(mining["atoms"]):
            expression = enumerate_expressions([atom], ["atomic"])[0]
            key = f"{source}:{expression.expression_id}"
            if key not in candidate_keys:
                continue
            score = cross_sectional_rank(
                factor_space[atom.name][symbols], rank_eligibility
            )
            scores[key] = score
            vectors[key] = score.loc[:discovery_end].iloc[::stride].stack(
                future_stack=True
            )
    missing = sorted(candidate_keys - set(vectors))
    if missing:
        raise ValueError(f"candidate scores not materialized: {missing}")

    signed_correlation = pd.DataFrame(vectors).corr(min_periods=500)
    correlation = signed_correlation.abs()
    ordered = _deterministic_candidate_order(summary, candidate_keys)
    expression_mechanism: dict[str, str] = {}
    mechanism_maximum: dict[str, int] = {}
    for mechanism, row in config.get("mechanism_limits", {}).items():
        mechanism_maximum[str(mechanism)] = int(row["max_selected"])
        for expression in row["expressions"]:
            expression = str(expression)
            if expression in expression_mechanism:
                raise ValueError(f"expression assigned to multiple mechanisms: {expression}")
            expression_mechanism[expression] = str(mechanism)
    unknown_mechanism_expressions = sorted(
        set(expression_mechanism) - set(summary["expression"].astype(str))
    )
    if unknown_mechanism_expressions:
        raise ValueError(
            f"mechanism expressions absent from adjudication: {unknown_mechanism_expressions}"
        )
    selected: list[str] = []
    mechanism_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    rejection_rows: list[dict[str, str]] = []
    threshold = float(config["max_abs_factor_rank_corr"])
    family_maximum = int(config.get("max_selected_per_family", len(candidate_keys)))
    for key in ordered:
        expression = str(summary.loc[key, "expression"])
        family = str(summary.loc[key, "true_family"])
        mechanism = _mechanism_id(family, expression, expression_mechanism)
        mechanism_limit = mechanism_maximum.get(mechanism, 1)
        if mechanism_counts.get(mechanism, 0) >= mechanism_limit:
            rejection_rows.append({"expression_key": key, "reason": f"mechanism_limit:{mechanism}"})
            continue
        if family_counts.get(family, 0) >= family_maximum:
            rejection_rows.append({"expression_key": key, "reason": f"family_limit:{family}"})
            continue
        pair_values = correlation.loc[key, selected] if selected else pd.Series(dtype=float)
        if pair_values.isna().any():
            rejection_rows.append({"expression_key": key, "reason": "insufficient_rank_correlation_pairs"})
            continue
        if not all(float(value) < threshold for value in pair_values):
            blocker = str(pair_values.idxmax())
            rejection_rows.append({"expression_key": key, "reason": f"rank_correlation:{blocker}"})
            continue
        selected.append(key)
        family_counts[family] = family_counts.get(family, 0) + 1
        mechanism_counts[mechanism] = mechanism_counts.get(mechanism, 0) + 1
    shelf = summary.loc[selected, [
        "expression_key", "true_family", "expression",
        "h5_discovery_ic", "h10_discovery_ic", "h20_discovery_ic",
        "discovery_ic", *year_columns, "year_direction_count",
        "year_direction_agreement",
        "seen_audit_ic", "timing_r2", "pooled_maxstat_pvalue",
        "within_family_maxstat_pvalue", "family_gate_pass",
    ]].copy()
    shelf.insert(0, "shelf_rank", np.arange(1, len(shelf) + 1))
    shelf.insert(
        3,
        "mechanism_id",
        [_mechanism_id(family, expression, expression_mechanism)
         for family, expression in zip(shelf["true_family"], shelf["expression"], strict=True)],
    )
    shelf.insert(3, "economic_axis", shelf["true_family"].map(family_axis))
    shelf["evidence_status"] = str(config["evidence_status"])
    if shelf["mechanism_id"].duplicated().any():
        raise AssertionError("selected shelf contains duplicate mechanisms")
    shelf.to_csv(output / "IC_FACTOR_SHELF.csv", index=False)
    pd.DataFrame(rejection_rows, columns=["expression_key", "reason"]).to_csv(
        output / "candidate_rejections.csv", index=False
    )
    selected_correlation = signed_correlation.loc[selected, selected]
    selected_correlation.to_csv(output / "selected_factor_rank_correlation.csv")

    score_rows = []
    for key in selected:
        stacked = scores[key].stack(future_stack=True).dropna().rename("score").reset_index()
        stacked.columns = ["signal_date", "symbol", "score"]
        stacked.insert(0, "expression_key", key)
        score_rows.append(stacked)
    selected_scores = (
        pd.concat(score_rows, ignore_index=True)
        if score_rows
        else pd.DataFrame(columns=["expression_key", "signal_date", "symbol", "score"])
    )
    selected_scores.to_parquet(output / "selected_factor_scores.parquet", index=False)

    family_count = int(shelf["true_family"].nunique())
    axis_count = int(shelf["economic_axis"].nunique())
    mechanism_count = int(shelf["mechanism_id"].nunique())
    effective_factor_count = _effective_factor_count(selected_correlation)
    target_met = len(shelf) >= int(config["target_factor_count"])
    diversity_met = family_count >= int(config["min_family_count"])
    axis_diversity_met = axis_count >= int(config["min_axis_count"])
    effective_count_met = effective_factor_count >= float(config["min_effective_factor_count"])
    status = "PASS" if target_met and diversity_met and axis_diversity_met and effective_count_met else "FAIL"
    manifest = {
        "status": status,
        "evidence_status": config["evidence_status"],
        "factor_count": len(shelf),
        "family_count": family_count,
        "economic_axis_count": axis_count,
        "submechanism_count": mechanism_count,
        "effective_factor_count": effective_factor_count,
        "target_factor_count": int(config["target_factor_count"]),
        "min_family_count": int(config["min_family_count"]),
        "min_axis_count": int(config["min_axis_count"]),
        "min_effective_factor_count": float(config["min_effective_factor_count"]),
        "candidate_count_before_redundancy": len(candidate_keys),
        "max_abs_factor_rank_corr": threshold,
        "max_selected_per_family": family_maximum,
        "mechanism_counts": mechanism_counts,
        "family_counts": family_counts,
        "as_of": args.as_of,
        "signal_time": "D_CLOSE",
        "entry_time": "D_PLUS_2_OPEN",
        "horizons": [5, 10, 20],
        "selection_surfaces": [f"{year_start}-{year_end}", "seen_audit_2024-01_to_2025-04"],
        "independent_oos": False,
        "config_hash": _hash(config_path),
        "catalog_hash": _hash(catalog_path),
        "source_dependency_hashes": hash_config_dependencies(ROOT, source_paths),
        "economic_axis_taxonomy_hash": _hash(taxonomy_path),
        "adjudication_manifest_hash": _hash(run / "run_manifest.json"),
        "canonical_data_hash": _hash(ROOT / "src/etf_strategy/canonical_data.py"),
        "data_inputs": hash_research_inputs(
            args.canonical_data_root.resolve(), panels["close"].columns, intraday_frequencies
        ),
        "shelf_script_hash": _hash(Path(__file__).resolve()),
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    lines = [
        "# ETF IC factor shelf",
        "",
        f"状态：{status}；入架因子：{len(shelf)}；经济轴：{axis_count}；覆盖家族：{family_count}。",
        f"相关矩阵有效因子数：{effective_factor_count:.2f}；子机制标签数：{mechanism_count}。",
        f"去重前候选：{len(candidate_keys)}；因子排序相关阈值：{threshold:.2f}。",
        "",
        "这是发现层候选，不是 pooled max-stat 认证，也没有独立样本外许可。",
        "全部因子使用 D 收盘可得信息，标签从 D+2 开盘开始。",
    ]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(f"ETF IC shelf complete: status={status} factors={len(shelf)} families={family_count}")
    print(f"output={output}")
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
