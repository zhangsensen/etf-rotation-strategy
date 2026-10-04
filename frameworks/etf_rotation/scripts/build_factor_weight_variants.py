#!/usr/bin/env python3
"""Build fixed old/equal/corrected-IC weight candidates for paired BT research."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def capped_weights(values: np.ndarray, cap: float) -> np.ndarray:
    """Normalize positive values with a deterministic per-factor cap."""
    if np.any(values < 0) or not np.isfinite(values).all() or values.sum() <= 0:
        raise ValueError("weight inputs must be finite, non-negative, and non-zero")
    if cap <= 0 or cap * len(values) < 1 - 1e-12:
        raise ValueError("cap is infeasible for the number of factors")
    weights = values / values.sum()
    fixed = np.zeros(len(weights), dtype=bool)
    while np.any(weights > cap + 1e-12):
        newly_fixed = weights > cap
        weights[newly_fixed] = cap
        fixed |= newly_fixed
        free = ~fixed
        remaining = 1.0 - weights[fixed].sum()
        if not free.any():
            break
        base = values[free]
        weights[free] = remaining * base / base.sum()
    return weights / weights.sum()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sealed", type=Path, required=True)
    parser.add_argument("--factor-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cap", type=float, default=.30)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")

    sealed = pd.read_parquet(args.sealed)
    audit = pd.read_csv(args.factor_summary).set_index("factor")
    rows = []
    for strategy_index, source in sealed.iterrows():
        factors = [x.strip() for x in source["combo"].split(" + ")]
        missing = sorted(set(factors) - set(audit.index))
        if missing:
            raise ValueError(f"Factors missing from audit: {missing}")
        corrected = audit.loc[factors, "discovery_mean_ic"].abs().to_numpy(float)
        schemes = {
            "old_weight": source["factor_icirs"],
            "equal_weight": ",".join(["1"] * len(factors)),
            "corrected_ic_cap30": ",".join(f"{x:.10f}" for x in capped_weights(corrected, args.cap)),
        }
        for scheme, weight_string in schemes.items():
            row = source.copy()
            row["research_variant"] = f"strategy_{strategy_index + 1}:{scheme}"
            row["factor_icirs"] = weight_string
            rows.append(row)
    result = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(args.output, index=False)
    print(result[["research_variant", "combo", "factor_signs", "factor_icirs"]].to_string(index=False))


if __name__ == "__main__":
    main()
