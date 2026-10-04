#!/usr/bin/env python3
"""Recalculate existing ETF factors against executable forward-open returns."""
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
from etf_strategy.core.executable_factor_audit import (
    apply_availability_lag,
    daily_cross_sectional_ic,
    forward_open_return,
    rolling_direction_stability,
    summarize_ic,
)
from etf_strategy.core.factor_cache import FactorCache


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--horizons", type=int, nargs="+", default=[5, 10, 20])
    parser.add_argument("--discovery-end", default=None)
    parser.add_argument("--min-pairs", type=int, default=5)
    parser.add_argument(
        "--factor-lag",
        action="append",
        default=[],
        metavar="FACTOR=SESSIONS",
        help="Conservative availability lag applied before labeling; repeatable",
    )
    return parser.parse_args()


def _parse_factor_lags(values: list[str], active: list[str]) -> dict[str, int]:
    lags: dict[str, int] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid --factor-lag {value!r}; expected FACTOR=SESSIONS")
        factor, raw_sessions = value.split("=", 1)
        if factor not in active:
            raise ValueError(f"Lag requested for inactive factor: {factor}")
        if factor in lags:
            raise ValueError(f"Duplicate lag for factor: {factor}")
        try:
            sessions = int(raw_sessions)
        except ValueError as exc:
            raise ValueError(f"Invalid lag sessions for {factor}: {raw_sessions}") from exc
        if sessions < 0:
            raise ValueError(f"Lag sessions must be non-negative for {factor}")
        lags[factor] = sessions
    return lags


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _period_rows(factor, horizon, daily, discovery_end):
    periods = {"full_seen": daily}
    if discovery_end is not None:
        boundary = pd.Timestamp(discovery_end)
        periods["discovery"] = daily.loc[daily.index <= boundary]
        periods["post_discovery_seen"] = daily.loc[daily.index > boundary]
    rows = []
    for period, frame in periods.items():
        rows.append({"factor": factor, "horizon": horizon, "period": period, **summarize_ic(frame)})
    return rows


def main():
    args = parse_args()
    if len(set(args.horizons)) != len(args.horizons) or any(h <= 0 for h in args.horizons):
        raise ValueError("horizons must be unique positive integers")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty output directory")
    output.mkdir(parents=True, exist_ok=True)

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
    cache = FactorCache(cache_dir=Path(data_cfg["cache_dir"]))
    factor_data = cache.get_or_compute(ohlcv=ohlcv, config=config, data_dir=loader.data_dir)
    active = list(config["active_factors"])
    factor_lags = _parse_factor_lags(args.factor_lag, active)
    missing = sorted(set(active) - set(factor_data["std_factors"]))
    if missing:
        raise ValueError(f"Active factors missing from cache: {missing}")

    opens = ohlcv["open"].reindex(factor_data["dates"]).reindex(columns=factor_data["etf_codes"])
    closes = ohlcv["close"].reindex_like(opens)
    # Reproduce the old pandas default exactly for diagnosis. This comparator is
    # deliberately invalid and is never used as the corrected label or a filter.
    legacy_same_day_return = closes.pct_change(fill_method="pad")
    discovery_end = args.discovery_end or data_cfg.get("training_end_date")
    period_rows = []
    yearly_rows = []
    daily_frames = []
    discovery_metrics = {}

    for horizon in args.horizons:
        label = forward_open_return(opens, horizon)
        for factor in active:
            signal = factor_data["std_factors"][factor].reindex_like(opens)
            signal = apply_availability_lag(signal, factor_lags.get(factor, 0))
            daily = daily_cross_sectional_ic(signal, label, min_pairs=args.min_pairs)
            daily_out = daily.assign(factor=factor, horizon=horizon).reset_index()
            daily_frames.append(daily_out)
            period_rows.extend(_period_rows(factor, horizon, daily, discovery_end))
            for year, frame in daily.groupby(daily.index.year):
                yearly_rows.append({
                    "factor": factor,
                    "horizon": horizon,
                    "year": int(year),
                    **summarize_ic(frame),
                })
            discovery_frame = daily if discovery_end is None else daily.loc[daily.index <= pd.Timestamp(discovery_end)]
            discovery_metrics[(factor, horizon)] = (discovery_frame, summarize_ic(discovery_frame))

    summary_rows = []
    primary_horizon = args.horizons[0]
    for factor in active:
        primary_daily, primary = discovery_metrics[(factor, primary_horizon)]
        direction = 1 if primary["mean_ic"] >= 0 else -1
        stability, window_count = rolling_direction_stability(primary_daily, direction)
        signal = factor_data["std_factors"][factor].reindex_like(opens)
        signal = apply_availability_lag(signal, factor_lags.get(factor, 0))
        legacy_daily = daily_cross_sectional_ic(signal, legacy_same_day_return, min_pairs=args.min_pairs)
        legacy_discovery = (legacy_daily if discovery_end is None else
                            legacy_daily.loc[legacy_daily.index <= pd.Timestamp(discovery_end)])
        legacy = summarize_ic(legacy_discovery)
        legacy_direction = 1 if legacy["mean_ic"] >= 0 else -1
        horizon_signs = [
            np.sign(discovery_metrics[(factor, horizon)][1]["mean_ic"])
            for horizon in args.horizons
        ]
        consistent = bool(all(sign == direction for sign in horizon_signs))
        screen_pass = bool(
            primary["days"] >= 252
            and primary["median_pairs"] >= 10
            and abs(primary["mean_ic"]) >= 0.02
            and consistent
            and np.isfinite(stability)
            and stability >= 0.60
        )
        summary_rows.append({
            "factor": factor,
            "availability_lag_sessions": factor_lags.get(factor, 0),
            "primary_horizon": primary_horizon,
            "direction": direction,
            "discovery_mean_ic": primary["mean_ic"],
            "legacy_same_day_mean_ic": legacy["mean_ic"],
            "mean_ic_change_from_legacy": primary["mean_ic"] - legacy["mean_ic"],
            "direction_changed_from_legacy": direction != legacy_direction,
            "discovery_icir_ann": primary["icir_ann"],
            "discovery_days": primary["days"],
            "median_pairs": primary["median_pairs"],
            "rolling_direction_stability": stability,
            "rolling_windows": window_count,
            "all_horizons_same_direction": consistent,
            "screen_pass": screen_pass,
        })

    summary = pd.DataFrame(summary_rows).sort_values(
        ["screen_pass", "discovery_mean_ic"], ascending=[False, False]
    )
    periods = pd.DataFrame(period_rows)
    yearly = pd.DataFrame(yearly_rows)
    daily_all = pd.concat(daily_frames, ignore_index=True)
    summary.to_csv(output / "factor_summary.csv", index=False)
    periods.to_csv(output / "factor_ic_by_period.csv", index=False)
    yearly.to_csv(output / "factor_ic_by_year.csv", index=False)
    daily_all.to_parquet(output / "daily_ic.parquet", index=False)

    manifest = {
        "config": str(config_path),
        "config_sha256": _sha256(config_path),
        "data_dir": str(loader.data_dir),
        "window": [str(opens.index.min().date()), str(opens.index.max().date())],
        "symbols": len(opens.columns),
        "active_factors": active,
        "factor_availability_lag_sessions": {
            factor: factor_lags.get(factor, 0) for factor in active
        },
        "horizons": args.horizons,
        "label_contract": "signal at D close; entry D+1 open; exit D+1+horizon open",
        "legacy_comparator": "invalid same-date close(D-1)-to-close(D) return, retained only to quantify label impact",
        "discovery_end": discovery_end,
        "post_discovery_is_seen_data": True,
        "screen_rule": "days>=252, median_pairs>=10, abs(primary mean IC)>=0.02, same direction all horizons, 180d/60d rolling direction stability>=0.60",
        "screen_is_discovery_evidence_only": True,
        "command": sys.argv,
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(summary.to_string(index=False))
    print(f"\nWrote executable factor audit to {output}")


if __name__ == "__main__":
    main()
