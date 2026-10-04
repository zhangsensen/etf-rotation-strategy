#!/usr/bin/env python3
"""Frozen candidate-1 weekly account mapping, regardless of its IC result."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explore_etf_personal_strategy_v1 as account
import run_etf_personal_paper_v1 as paper
from etf_strategy.core import etf_group_discovery as discovery
from etf_strategy.core import etf_group_domestic_benchmark as domestic

ROOT, ETF = paper.ROOT, paper.ETF
CONFIG = ETF / "configs/group_ic_cn_benchmark_aux_20260925.yaml"
CONFIG_SHA256 = "54a8bcd0534cc1263ae9e6d1875ec2ee8d6d58c806882e737b18d07af199b926"
RUN = ROOT / "runtime_outputs/etf_rotation_research/runs/group_ic_cn_benchmark_aux_20260925"
PREFLIGHT = ROOT / "runtime_outputs/etf_rotation_research/preflight_domestic_benchmark_20260925"
OUTPUT = ROOT / "runtime_outputs/etf_rotation_research/domestic_benchmark_weekly_20260925"
CANDIDATE = "cn_mid_large_style_transmission_60"
RULE = "cn_mid_large_style_weekly_top2"


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    if paper._digest(CONFIG) != CONFIG_SHA256:
        raise ValueError("candidate and strategy mapping spec changed")
    cfg = yaml.safe_load(CONFIG.read_text())
    if cfg["notes"]["strategy_mapping"].find(CANDIDATE) < 0:
        raise ValueError("strategy candidate not present in frozen mapping")
    plan = json.loads((RUN / "PLAN.json").read_text())
    if plan["config"] != cfg or CANDIDATE not in plan["evaluated_ids"]:
        raise ValueError("strategy score does not belong to frozen IC run")
    groups = yaml.safe_load((ROOT / cfg["groups"]).read_text())["groups"]
    universe = json.loads((ROOT / cfg["universe"]).read_text())["etfs"]
    symbols = [row["ts_code"] for row in universe if row["role"] == "candidate"]
    discovery.validate_groups(groups, symbols)
    cutoff = pd.Timestamp(cfg["as_of"])
    panels = paper.load_canonical_daily(paper.DATA_ROOT, paper.UNIVERSE,
                                        as_of=cfg["as_of"], roles=("candidate",))
    benchmark = paper.load_canonical_daily(paper.DATA_ROOT, paper.UNIVERSE,
                                           as_of=cfg["as_of"], roles=("benchmark",))
    cd = pd.read_parquet(paper.DATA_ROOT / "1d/510300.SH.parquet",
                         columns=["trade_date"], filters=[("trade_date", "<=", cutoff)])
    calendar = pd.DatetimeIndex(pd.to_datetime(cd.trade_date)).sort_values()
    calendar = calendar[(calendar >= pd.Timestamp(cfg["start"])) & (calendar <= cutoff)]
    feature = {"close": panels["close"].reindex(calendar),
               "benchmark_close": benchmark["close"][cfg["auxiliary_symbols"]].reindex(calendar)}
    atom = domestic.build_atoms(feature, cfg)[CANDIDATE]
    score = discovery.aggregate(atom, groups)[list(groups)]
    saved = pd.read_csv(RUN / f"scores_{CANDIDATE}.csv", index_col=0,
                        parse_dates=True, float_precision="round_trip")
    common = score.index.intersection(saved.index)
    a, b = score.loc[common], saved.loc[common, list(groups)]
    mismatch = a.isna().ne(b.isna()) | ((a - b).abs() > 1e-9 * b.abs().clip(lower=1e-12))
    count = int(mismatch.to_numpy().sum())
    if count or len(common) < 250:
        raise ValueError(f"formal frozen score mismatch: {count} cells, {len(common)} dates")
    first = pd.Timestamp("2024-01-01")
    intervals, decisions = account.schedule_weekly(calendar, score, groups, first)
    for item in intervals:
        item["rule"] = RULE
    for item in decisions:
        item["rule"] = RULE
    raw_open, raw_volume, first_volume = paper._raw_prices_and_opening_volume(symbols, cutoff, calendar)
    study_calendar = calendar[calendar >= first]
    all_daily, all_events = [], []
    for portfolio in account.BENCHMARKS:
        for cost in (0, 10):
            for fill_aware in (False, True):
                daily, events = account.simulate(intervals, portfolio, study_calendar,
                                                  panels["open"], panels["close"],
                                                  raw_open, raw_volume, first_volume,
                                                  cost, fill_aware)
                daily.insert(0, "rule", RULE)
                events.insert(0, "rule", RULE)
                all_daily.append(daily)
                all_events.append(events)
    daily = pd.concat(all_daily, ignore_index=True)
    events = pd.concat(all_events, ignore_index=True)
    summary = account.summarize_nav(RULE, daily, events)
    break_even = account.break_even_costs({RULE: (intervals, decisions)}, study_calendar,
                                           panels["open"], panels["close"],
                                           raw_open, raw_volume, first_volume)
    output.mkdir(parents=True, exist_ok=False)
    summary.to_csv(output / "summary.csv", index=False)
    daily.to_csv(output / "daily_nav.csv", index=False)
    events.to_csv(output / "events.csv", index=False)
    break_even.to_csv(output / "break_even.csv", index=False)
    pd.DataFrame(decisions).to_csv(output / "decisions.csv", index=False)
    pd.DataFrame([{key: value for key, value in item.items() if not key.endswith("weights")}
                  for item in intervals]).to_csv(output / "intervals.csv", index=False)
    source_paths = [Path(__file__), Path(account.__file__), Path(paper.__file__),
                    Path(domestic.__file__), CONFIG, RUN / "PLAN.json",
                    RUN / f"scores_{CANDIDATE}.csv", PREFLIGHT / "manifest.json",
                    ROOT / cfg["groups"], ROOT / cfg["universe"]]
    manifest = {"status": "DESCRIPTIVE_SEEN_HISTORY_NOT_OOS_NOT_TRADE_AUTHORITY",
                "rule": RULE, "candidate": CANDIDATE,
                "run_even_if_ic_fails": True,
                "frozen_config_sha256": CONFIG_SHA256,
                "as_of": cfg["as_of"], "population": "fixed14_eight_groups",
                "timing": "first ISO-week exchange session close(D), D+2 adjusted open entry, D+7 adjusted open exit; skip overlapping new entries",
                "2026_status": "COLD_PARTIAL_MARKED_AT_ADJUSTED_CLOSE_NOT_COMPLETED_EXIT",
                "cost": "10bp per side illustrative, not actual account fees",
                "fill": "09:31 positive-volume proxy, not proof of exact daily-open fill",
                "benchmark": "same ranked intervals and cash gaps B8/B14 with equal net-order cost convention",
                "score_reproducibility": {"compared_dates": len(common), "mismatch_cells": count},
                "source_sha256": {str(path): paper._digest(path) for path in source_paths},
                "filtered_input_sha256": {key: account._filtered_sha(value) for key, value in {
                    **feature, "adjusted_open": panels["open"].reindex(calendar),
                    "adjusted_close": panels["close"].reindex(calendar),
                    "raw_open": raw_open, "raw_volume": raw_volume,
                    "first_0931_volume": first_volume}.items()},
                "command": [sys.executable, *sys.argv]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False,
                                                    indent=2, allow_nan=False) + "\n")
    return {"output": str(output), "intervals": len(intervals),
            "overlap_skips": sum(row["status"] == "SKIPPED_ACTIVE_SLEEVE" for row in decisions),
            "score_reproducibility": manifest["score_reproducibility"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
