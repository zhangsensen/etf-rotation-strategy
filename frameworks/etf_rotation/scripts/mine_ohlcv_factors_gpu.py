#!/usr/bin/env python3
"""Mine the fixed ETF OHLCV factor space with GPU cross-sectional IC."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from etf_strategy.core.data_loader import DataLoader
from etf_strategy.core.ohlcv_factor_mining import (
    build_ohlcv_factor_space,
    factor_family,
    forward_open_return,
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--discovery-end", default="2025-04-30")
    parser.add_argument("--entry-lag", type=int, default=2)
    parser.add_argument("--horizons", type=int, nargs="+", default=[5, 10, 20])
    parser.add_argument("--min-pairs", type=int, default=20)
    parser.add_argument("--redundancy-threshold", type=float, default=0.80)
    parser.add_argument(
        "--legacy-replay",
        action="store_true",
        help="explicitly replay this retired OHLCV-only screen",
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gpu_daily_corr(left: pd.DataFrame, right: pd.DataFrame, min_pairs: int):
    import cupy as cp

    x = cp.asarray(left.to_numpy(dtype=np.float32))
    y = cp.asarray(right.to_numpy(dtype=np.float32))
    valid = cp.isfinite(x) & cp.isfinite(y)
    n = valid.sum(axis=1).astype(cp.float32)
    x0 = cp.where(valid, x, 0.0)
    y0 = cp.where(valid, y, 0.0)
    sx = x0.sum(axis=1)
    sy = y0.sum(axis=1)
    numerator = (x0 * y0).sum(axis=1) - sx * sy / cp.maximum(n, 1.0)
    vx = (x0 * x0).sum(axis=1) - sx * sx / cp.maximum(n, 1.0)
    vy = (y0 * y0).sum(axis=1) - sy * sy / cp.maximum(n, 1.0)
    denominator = cp.sqrt(cp.maximum(vx * vy, 0.0))
    corr = cp.where((n >= min_pairs) & (denominator > 0), numerator / denominator, cp.nan)
    return cp.asnumpy(corr), cp.asnumpy(n).astype(int)


def _rank(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rank(axis=1, pct=True, method="average", na_option="keep")


def _stats(values: pd.Series) -> dict:
    values = values.dropna()
    if values.empty:
        return {"days": 0, "mean_ic": np.nan, "icir_ann": np.nan, "positive_rate": np.nan}
    std = float(values.std(ddof=1))
    return {
        "days": int(len(values)),
        "mean_ic": float(values.mean()),
        "icir_ann": float(values.mean() / std * np.sqrt(252)) if std > 0 else np.nan,
        "positive_rate": float((values > 0).mean()),
    }


def _rolling_stability(values: pd.Series, direction: int, window=180, step=60):
    signs = []
    for start in range(0, max(0, len(values) - window + 1), step):
        chunk = values.iloc[start : start + window].dropna()
        if len(chunk) >= window // 2:
            signs.append(np.sign(chunk.mean()))
    return (float(np.mean(np.asarray(signs) == direction)), len(signs)) if signs else (np.nan, 0)


def _mean_abs_daily_corr(left: pd.DataFrame, right: pd.DataFrame, min_pairs: int) -> float:
    corr, _ = _gpu_daily_corr(left, right, min_pairs)
    return float(np.nanmean(np.abs(corr)))


def main():
    args = parse_args()
    if not args.legacy_replay:
        raise SystemExit(
            "retired OHLCV-only candidate screen: use "
            "scripts/research/pi_glm_mining/discover_from_outcomes.py discover; "
            "pass --legacy-replay only for historical reproduction"
        )
    if args.entry_lag <= 0 or any(h <= 0 for h in args.horizons):
        raise ValueError("entry lag and horizons must be positive")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty output directory")
    output.mkdir(parents=True, exist_ok=True)

    import cupy as cp

    if cp.cuda.runtime.getDeviceCount() < 1:
        raise RuntimeError("GPU factor mining requires an available CUDA device")
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text())
    data_cfg = config["data"]
    loader = DataLoader(data_dir=data_cfg["data_dir"], cache_dir=data_cfg.get("cache_dir"))
    ohlcv = loader.load_ohlcv(
        etf_codes=data_cfg["symbols"],
        start_date=data_cfg["start_date"],
        end_date=data_cfg["end_date"],
        use_cache=True,
    )
    factors = build_ohlcv_factor_space(ohlcv)
    dates = ohlcv["close"].index
    symbols = list(ohlcv["close"].columns)
    ranks = {name: _rank(frame.reindex(index=dates, columns=symbols)) for name, frame in factors.items()}
    labels = {
        horizon: _rank(forward_open_return(ohlcv["open"], horizon, args.entry_lag))
        for horizon in args.horizons
    }
    boundary = pd.Timestamp(args.discovery_end)
    daily_rows = []
    metrics: dict[tuple[str, int], dict] = {}
    daily_map: dict[tuple[str, int], pd.Series] = {}
    pair_map: dict[tuple[str, int], pd.Series] = {}
    for name in sorted(ranks):
        for horizon in args.horizons:
            corr, pairs = _gpu_daily_corr(ranks[name], labels[horizon], args.min_pairs)
            series = pd.Series(corr, index=dates, name="ic")
            pair_series = pd.Series(pairs, index=dates, name="pair_count")
            daily_map[(name, horizon)] = series
            pair_map[(name, horizon)] = pair_series
            discovery = series.loc[series.index <= boundary]
            seen = series.loc[series.index > boundary]
            metrics[(name, horizon)] = _stats(discovery)
            for date, ic, pair_count in zip(dates, corr, pairs):
                daily_rows.append(
                    {"signal_date": date, "factor": name, "horizon": horizon,
                     "ic": ic, "pair_count": pair_count}
                )
            metrics[(name, horizon)]["seen_mean_ic"] = _stats(seen)["mean_ic"]

    primary = args.horizons[0]
    summary_rows = []
    for name in sorted(ranks):
        stat = metrics[(name, primary)]
        direction = 1 if stat["mean_ic"] >= 0 else -1
        discovery_daily = daily_map[(name, primary)].loc[:boundary]
        stability, rolling_windows = _rolling_stability(discovery_daily, direction)
        horizon_signs = [np.sign(metrics[(name, h)]["mean_ic"]) for h in args.horizons]
        yearly = discovery_daily.groupby(discovery_daily.index.year).mean().dropna()
        year_agreement = float((np.sign(yearly) == direction).mean()) if len(yearly) else np.nan
        median_pairs = float(pair_map[(name, primary)].loc[:boundary].median())
        screen_pass = bool(
            stat["days"] >= 500
            and median_pairs >= 30
            and abs(stat["mean_ic"]) >= 0.015
            and all(sign == direction for sign in horizon_signs)
            and np.isfinite(stability) and stability >= 0.65
            and np.isfinite(year_agreement) and year_agreement >= 0.67
        )
        summary_rows.append(
            {
                "factor": name,
                "family": factor_family(name),
                "direction": direction,
                "discovery_mean_ic_5d": stat["mean_ic"],
                "discovery_icir_ann_5d": stat["icir_ann"],
                "seen_mean_ic_5d": stat["seen_mean_ic"],
                "discovery_days": stat["days"],
                "median_pairs": median_pairs,
                "rolling_direction_stability": stability,
                "rolling_windows": rolling_windows,
                "year_direction_agreement": year_agreement,
                "all_horizons_same_direction": all(sign == direction for sign in horizon_signs),
                "screen_pass": screen_pass,
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values(
        ["screen_pass", "discovery_mean_ic_5d"], ascending=[False, False]
    )

    passed = summary.loc[summary["screen_pass"]].copy()
    passed["abs_ic"] = passed["discovery_mean_ic_5d"].abs()
    passed = passed.sort_values(["abs_ic", "factor"], ascending=[False, True])
    selected: list[str] = []
    redundancy_rows = []
    for name in passed["factor"]:
        blocker = None
        blocker_corr = np.nan
        for kept in selected:
            corr = _mean_abs_daily_corr(ranks[name].loc[:boundary], ranks[kept].loc[:boundary], args.min_pairs)
            if corr >= args.redundancy_threshold:
                blocker, blocker_corr = kept, corr
                break
        keep = blocker is None
        if keep:
            selected.append(name)
        redundancy_rows.append(
            {"factor": name, "selected": keep, "blocked_by": blocker,
             "mean_abs_daily_rank_corr": blocker_corr}
        )

    daily = pd.DataFrame(daily_rows)
    summary.to_csv(output / "factor_summary.csv", index=False)
    daily.to_parquet(output / "daily_ic.parquet", index=False)
    pd.DataFrame(redundancy_rows).to_csv(output / "redundancy_screen.csv", index=False)
    selected_payload = {
        "selected_factors": selected,
        "directions": {
            row.factor: int(row.direction)
            for row in summary.itertuples()
            if row.factor in selected
        },
        "selection_is_discovery_evidence_only": True,
    }
    (output / "selected_factors.json").write_text(
        json.dumps(selected_payload, ensure_ascii=False, indent=2)
    )
    source_path = ROOT / "src/etf_strategy/core/ohlcv_factor_mining.py"
    manifest = {
        "config": str(config_path),
        "config_sha256": _sha256(config_path),
        "factor_source_sha256": _sha256(source_path),
        "window": [str(dates.min().date()), str(dates.max().date())],
        "discovery_end": args.discovery_end,
        "post_discovery_is_seen_data": True,
        "symbols": len(symbols),
        "candidate_count": len(factors),
        "candidate_names": sorted(factors),
        "label_contract": (
            f"signal after D close; entry open D+{args.entry_lag}; "
            f"exit after fixed horizon {args.horizons}"
        ),
        "screen_rule": (
            "days>=500; median_pairs>=30; abs(mean_ic_5d)>=0.015; "
            "5/10/20 directions agree; rolling stability>=0.65; year agreement>=0.67"
        ),
        "redundancy_rule": f"greedy abs daily rank correlation < {args.redundancy_threshold}",
        "gpu": {
            "backend": "cupy",
            "cupy_version": cp.__version__,
            "device": cp.cuda.runtime.getDeviceProperties(0)["name"].decode(),
        },
        "command": sys.argv,
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(summary.to_string(index=False))
    print(f"\nPassed={len(passed)}/{len(summary)}; selected_after_redundancy={len(selected)}")
    print("Selected:", ", ".join(selected) if selected else "NONE")
    print(f"Wrote GPU factor discovery to {output}")


if __name__ == "__main__":
    main()
