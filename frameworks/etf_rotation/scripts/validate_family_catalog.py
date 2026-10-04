#!/usr/bin/env python3
"""Materialize every ETF family atom without reading return labels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
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
    parse_atoms,
)
from etf_strategy.core.etf_family_catalog import blocked_family_reasons, load_family_catalog
from etf_strategy.core.family_registry import load_builtin_families, resolve_family


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-data-root", type=Path, required=True)
    parser.add_argument("--universe-config", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--min-history-sessions", type=int, default=120)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _args()
    cutoff = pd.Timestamp(args.as_of)
    load_builtin_families()
    catalog_path = args.catalog.resolve()
    config_paths = load_family_catalog(catalog_path, ROOT)
    panels = load_canonical_daily(
        args.canonical_data_root.resolve(), args.universe_config.resolve(), as_of=args.as_of
    )
    all_eligibility = build_pit_eligibility(panels, args.min_history_sessions, True)
    universe = json.loads(args.universe_config.resolve().read_text())["etfs"]
    ranking_symbols = [row["ts_code"] for row in universe if row["role"] == "candidate"]
    eligibility = all_eligibility[ranking_symbols]
    denominator = int(eligibility.to_numpy().sum())
    rows: list[dict[str, object]] = []
    rank_vectors: dict[str, pd.Series] = {}
    vector_families: dict[str, str] = {}
    for config_path in config_paths:
        config = yaml.safe_load(config_path.read_text())
        provider = resolve_family(str(config["factor_source"]))
        factor_space = provider.builder(
            panels, all_eligibility, args.canonical_data_root.resolve(), config
        )
        atoms = parse_atoms(config["atoms"])
        missing = sorted({atom.name for atom in atoms} - set(factor_space))
        if missing:
            raise ValueError(f"{provider.source_name} missing configured atoms: {missing}")
        finite = 0
        atom_coverage = []
        for atom in atoms:
            raw_frame = factor_space[atom.name]
            if len(raw_frame.index) and raw_frame.index.max() > cutoff:
                raise ValueError(f"{provider.source_name}:{atom.name} contains future rows")
            frame = raw_frame.reindex(index=eligibility.index, columns=ranking_symbols)
            atom_finite = int(np.isfinite(frame.where(eligibility).to_numpy()).sum())
            if atom_finite == 0:
                raise ValueError(f"{provider.source_name}:{atom.name} has no eligible values")
            finite += atom_finite
            finite_mask = np.isfinite(frame) & eligibility
            rankable_days = eligibility.sum(axis=1).ge(8)
            rankable_denominator = int(eligibility.loc[rankable_days].to_numpy().sum())
            atom_coverage.append({
                "atom": atom.name,
                "eligible_finite_values": atom_finite,
                "eligible_coverage": atom_finite / denominator,
                "coverage_on_days_with_at_least_8_eligible": (
                    int(finite_mask.loc[rankable_days].to_numpy().sum()) / rankable_denominator
                    if rankable_denominator else None
                ),
                "days_with_at_least_8_finite": int(finite_mask.sum(axis=1).ge(8).sum()),
            })
            key = f"{provider.information_family}:{atom.name}"
            rank_vectors[key] = cross_sectional_rank(frame, eligibility).iloc[::5].stack(
                future_stack=True
            )
            vector_families[key] = provider.information_family
        rows.append(
            {
                "family": provider.information_family,
                "source": provider.source_name,
                "atoms": len(atoms),
                "eligible_finite_values": finite,
                "mean_atom_coverage": finite / (denominator * len(atoms)),
                "atom_coverage": atom_coverage,
            }
        )
    rank_correlation = pd.DataFrame(rank_vectors).corr(min_periods=500).abs()
    overlaps: list[dict[str, object]] = []
    exact_aliases: list[dict[str, object]] = []
    within_family_overlaps: list[dict[str, object]] = []
    keys = list(rank_correlation)
    for index, left in enumerate(keys):
        for right in keys[index + 1 :]:
            value = float(rank_correlation.loc[left, right])
            if np.isfinite(value) and value >= 0.999999:
                exact_aliases.append({"left": left, "right": right, "abs_rank_corr": value})
            if vector_families[left] != vector_families[right] and np.isfinite(value) and value >= 0.98:
                overlaps.append({"left": left, "right": right, "abs_rank_corr": value})
            if vector_families[left] == vector_families[right] and np.isfinite(value) and value >= 0.95:
                within_family_overlaps.append({"left": left, "right": right, "abs_rank_corr": value})
    if exact_aliases:
        raise ValueError(f"exact rank aliases in ETF catalog: {exact_aliases[:5]}")
    if overlaps:
        raise ValueError(f"cross-family rank redundancy >=0.98: {overlaps[:5]}")

    result = {
        "as_of": args.as_of,
        "ranking_population": "candidate",
        "ranking_symbol_count": len(ranking_symbols),
        "available_family_count": len(rows),
        "atom_count": sum(int(row["atoms"]) for row in rows),
        "blocked_families": blocked_family_reasons(catalog_path),
        "cross_family_redundancy_threshold": 0.98,
        "cross_family_pairs_at_or_above_threshold": overlaps,
        "exact_rank_aliases": exact_aliases,
        "within_family_pairs_at_or_above_0_95_reporting_only": within_family_overlaps,
        "families": rows,
        "status": "PASS",
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
