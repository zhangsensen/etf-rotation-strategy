#!/usr/bin/env python3
"""Run the purged walk-forward protocol-robustness evaluator over frozen ETF atoms.

Reads precomputed long-format daily IC and label dates, replays every fold with a
train-only direction, and writes descriptive fold metrics plus a manifest into a
new immutable output directory.  The result is protocol robustness over seen
history, not an independent out-of-sample verdict.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from etf_strategy.core.etf_factor_wfo import DEFAULT_MIN_TRAIN_DAYS, evaluate_factor_wfo

RUN_STATUS = "protocol_robustness_seen_history_not_independent_oos"

IC_COLUMNS = ("horizon", "signal_date", "expression_key", "ic")
LABEL_COLUMNS = ("horizon", "signal_date", "entry_date", "exit_date")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daily-ic", type=Path, required=True, help="parquet: horizon,signal_date,expression_key,ic")
    parser.add_argument("--label-dates", type=Path, required=True, help="parquet: horizon,signal_date,entry_date,exit_date")
    parser.add_argument("--fold-config", type=Path, required=True, help="YAML with folds and optional min_train_days")
    parser.add_argument("--eligibility-counts", type=Path, required=True, help="CSV: signal_date,eligible_count")
    parser.add_argument("--output", type=Path, required=True, help="new empty directory")
    return parser.parse_args()


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
    missing = [name for name in columns if name not in frame.columns]
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def _validate_horizon_column(frame: pd.DataFrame) -> None:
    values = pd.to_numeric(frame['horizon'], errors='raise')
    if not (np.isfinite(values).all() and values.gt(0).all() and values.eq(np.floor(values)).all()):
        raise ValueError('horizon must contain finite positive integers')


def load_daily_ic(path: Path) -> dict[int, pd.DataFrame]:
    """Pivot long IC rows into one wide frame per horizon."""
    frame = pd.read_parquet(path)
    _require_columns(frame, IC_COLUMNS, "daily-ic")
    _validate_horizon_column(frame)
    keys = ["horizon", "signal_date", "expression_key"]
    if frame.duplicated(subset=keys).any():
        raise ValueError("daily-ic has duplicate (horizon, signal_date, expression_key) rows")
    frame = frame.assign(signal_date=pd.to_datetime(frame["signal_date"]))
    result: dict[int, pd.DataFrame] = {}
    for horizon, block in frame.groupby("horizon", sort=True):
        wide = block.pivot(index="signal_date", columns="expression_key", values="ic")
        wide.columns.name = None
        result[int(horizon)] = wide.sort_index()
    if not result:
        raise ValueError("daily-ic is empty")
    return result


def load_label_dates(path: Path) -> dict[int, pd.DataFrame]:
    frame = pd.read_parquet(path)
    _require_columns(frame, LABEL_COLUMNS, "label-dates")
    _validate_horizon_column(frame)
    if frame.duplicated(subset=["horizon", "signal_date"]).any():
        raise ValueError("label-dates has duplicate (horizon, signal_date) rows")
    frame = frame.assign(
        signal_date=pd.to_datetime(frame["signal_date"]),
        entry_date=pd.to_datetime(frame["entry_date"]),
        exit_date=pd.to_datetime(frame["exit_date"]),
    )
    return {
        int(horizon): block.set_index("signal_date")[["entry_date", "exit_date"]].sort_index()
        for horizon, block in frame.groupby("horizon", sort=True)
    }


def load_eligibility_counts(path: Path) -> pd.Series:
    frame = pd.read_csv(path)
    _require_columns(frame, ("signal_date", "eligible_count"), "eligibility-counts")
    if frame["signal_date"].duplicated().any():
        raise ValueError("eligibility-counts has duplicate signal_date rows")
    index = pd.to_datetime(frame["signal_date"])
    return pd.Series(frame["eligible_count"].to_numpy(dtype=float), index=index, name="eligible_count")


def load_fold_config(path: Path) -> tuple[list[dict[str, object]], int]:
    """Read folds and the run's min_train_days, which the CLI floors at 360."""
    config = yaml.safe_load(path.read_text())
    if not isinstance(config, dict):
        raise ValueError("fold-config must be a mapping")
    folds = config.get("folds")
    if not isinstance(folds, list) or not folds:
        raise ValueError("fold-config must define a non-empty folds list")
    min_train_days = int(config.get("min_train_days", DEFAULT_MIN_TRAIN_DAYS))
    if min_train_days < DEFAULT_MIN_TRAIN_DAYS:
        raise ValueError(
            f"min_train_days must be >= {DEFAULT_MIN_TRAIN_DAYS} for a CLI run, got {min_train_days}"
        )
    return [dict(fold) for fold in folds], min_train_days


def main() -> None:
    args = _args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"output directory must be new and empty: {output}")

    daily_ic = load_daily_ic(args.daily_ic)
    label_dates = load_label_dates(args.label_dates)
    eligibility_counts = load_eligibility_counts(args.eligibility_counts)
    folds, min_train_days = load_fold_config(args.fold_config)

    metrics = evaluate_factor_wfo(
        daily_ic,
        label_dates,
        eligibility_counts,
        folds,
        min_train_days=min_train_days,
    )

    output.mkdir(parents=True, exist_ok=True)
    metrics_path = output / "fold_metrics.csv"
    metrics.to_csv(metrics_path, index=False)

    manifest = {
        "status": RUN_STATUS,
        "run_kind": "DIAGNOSTIC",
        "runner_hash": _hash(Path(__file__)),
        "engine_source_hash": _hash(Path(evaluate_factor_wfo.__code__.co_filename)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "min_train_days": min_train_days,
        "horizons": sorted(daily_ic),
        "fold_ids": [str(fold["fold_id"]) for fold in folds],
        "catalog_size": int(metrics["expression_key"].nunique()),
        "rows": int(len(metrics)),
        "status_counts": {str(key): int(value) for key, value in metrics["status"].value_counts().items()},
        "inputs": {
            "daily_ic": {"path": str(args.daily_ic.resolve()), "sha256": _hash(args.daily_ic)},
            "label_dates": {"path": str(args.label_dates.resolve()), "sha256": _hash(args.label_dates)},
            "fold_config": {"path": str(args.fold_config.resolve()), "sha256": _hash(args.fold_config)},
            "eligibility_counts": {
                "path": str(args.eligibility_counts.resolve()),
                "sha256": _hash(args.eligibility_counts),
            },
        },
        "outputs": {metrics_path.name: _hash(metrics_path)},
        "command": sys.argv,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"ETF factor WFO complete: rows={len(metrics)} status={RUN_STATUS}")
    print(f"output={output}")


if __name__ == "__main__":
    main()
