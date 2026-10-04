#!/usr/bin/env python3
"""Independently recompute US real-rate round-9 saved H5 labels, daily IC and HAC t."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))
from etf_strategy.canonical_data import load_canonical_daily

RUN = ROOT / "runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r09_ext_realrate_20260926"
PRE = ROOT / "runtime_outputs/etf_rotation_research/preflight_ext_realrate_r09_draft_20260926"
CONFIG = ETF / "configs/group_ic_campaign20_r09_ext_realrate_20260926.yaml"
DATA = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))


def hac_t_calendar(values: pd.Series, calendar: pd.DatetimeIndex, lag: int) -> float:
    grid = values.reindex(calendar).to_numpy(dtype=float)
    keep = np.isfinite(grid)
    n = int(keep.sum())
    mean = float(np.mean(grid[keep]))
    demeaned = np.zeros(len(grid))
    demeaned[keep] = grid[keep] - mean
    variance = float(np.dot(demeaned, demeaned) / n)
    for j in range(1, lag + 1):
        variance += 2 * (1 - j / (lag + 1)) * float(np.dot(demeaned[j:], demeaned[:-j]) / n)
    return float(mean / np.sqrt(variance / n))


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    cfg = yaml.safe_load(CONFIG.read_text())
    groups = yaml.safe_load((ROOT / cfg["groups"]).read_text())["groups"]
    universe = ROOT / cfg["universe"]
    panels = load_canonical_daily(DATA, universe, as_of=cfg["as_of"], roles=("candidate",))
    calendar = panels["open"].index
    open_price = panels["open"].reindex(calendar)
    member_h5 = open_price.shift(-7).div(open_price.shift(-2)).sub(1)
    group_h5 = pd.DataFrame({name: member_h5[item["members"]].mean(axis=1).where(
        member_h5[item["members"]].notna().all(axis=1)) for name, item in groups.items()})
    saved_group = pd.read_csv(RUN / "group_labels.csv", index_col=0, parse_dates=True)
    common_group = group_h5.index.intersection(saved_group.index)
    label_error = float((group_h5.loc[common_group, list(groups)] -
                         saved_group.loc[common_group, list(groups)]).abs().max().max())
    if label_error > 1e-12:
        raise ValueError(f"independent H5 group label mismatch: {label_error}")

    metrics = pd.read_csv(RUN / "daily_metrics.csv", parse_dates=["signal_date", "entry_date", "exit_date"])
    summary = pd.read_csv(RUN / "summary.csv").set_index("candidate")
    yearly = pd.read_csv(RUN / "yearly.csv").set_index(["candidate", "year"])
    results = {}
    for name in summary.index:
        score = pd.read_csv(RUN / f"scores_{name}.csv", index_col=0, parse_dates=True,
                            float_precision="round_trip")[list(groups)]
        pre = pd.read_csv(PRE / f"scores_{name}.csv", index_col=0, parse_dates=True,
                          float_precision="round_trip")[list(groups)]
        common = score.index.intersection(pre.index)
        score_error = float((score.loc[common] - pre.loc[common]).abs().max().max())
        if score_error > 1e-10 or len(common) != len(pre):
            raise ValueError(f"formal score differs from prelabel score: {name}")
        rows = metrics[metrics.candidate.eq(name)].set_index("signal_date").sort_index()
        valid = rows[rows.ic.notna()]
        independent = {}
        for d, row in valid.iterrows():
            loc = calendar.get_loc(d)
            if (row.entry_date != calendar[loc + 2] or row.exit_date != calendar[loc + 7]
                    or row.exit_date > pd.Timestamp(cfg["as_of"])):
                raise ValueError(f"D+2/H5 timing mismatch: {name} {d}")
            a = score.loc[d].to_numpy(dtype=float)
            b = group_h5.loc[d, list(groups)].to_numpy(dtype=float)
            if not np.isfinite(a).all() or not np.isfinite(b).all():
                raise ValueError("saved IC exists on incomplete eight-group date")
            rounded = np.array([float(f"{value:.12g}") for value in a])
            independent[d] = float(spearmanr(rounded, b).statistic)
        ic = pd.Series(independent, dtype=float).sort_index()
        daily_error = float((ic - valid.ic).abs().max())
        full_t = hac_t_calendar(ic, calendar[(calendar >= pd.Timestamp(cfg["evaluation_start"])) &
                                                (calendar <= pd.Timestamp(cfg["as_of"]))], 10)
        full_row = summary.loc[name]
        if (len(ic) != int(full_row.n) or daily_error > 1e-12 or
                abs(float(ic.mean()) - full_row.ic_mean) > 1e-12 or
                abs(full_t - full_row.ic_hac_t) > 1e-10):
            raise ValueError(f"independent daily IC/HAC mismatch: {name}")
        annual = {}
        for year in (2025, 2026):
            sub = ic[(ic.index.year == year) &
                     (valid.loc[ic.index, "exit_date"].dt.year.to_numpy() == year)]
            annual[year] = {"n": len(sub), "ic": float(sub.mean())}
            saved = yearly.loc[(name, year)]
            if len(sub) != int(saved.n) or abs(float(sub.mean()) - saved.ic_mean) > 1e-12:
                raise ValueError(f"independent annual IC mismatch: {name} {year}")
        results[name] = {"prelabel_common_dates": len(common), "max_prelabel_score_abs_diff": score_error,
                         "n": len(ic), "full_ic": float(ic.mean()), "full_hac_t": full_t,
                         "max_daily_ic_abs_diff": daily_error,
                         "annual_purged": annual,
                         "unmatured_tail_score_dates": int((score.loc[pd.Timestamp(cfg["evaluation_start"]):].notna().all(axis=1)).sum() - len(ic)),
                         "timing_order_on_valid_ic_dates": True}
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"status": "INDEPENDENT_RECOMPUTATION_MATCHES", "as_of": cfg["as_of"],
               "group_label_max_abs_diff": label_error, "results": results,
               "note": "27 evaluation dates have x_D exactly zero (unchanged 10y real yield), constant eight-group scores and undefined rank IC; they are excluded from n by the frozen engine, not dropped post hoc",
               "source_sha256": {str(path): sha256(path.read_bytes()).hexdigest() for path in
                                 [Path(__file__), CONFIG, RUN / "PLAN.json", RUN / "summary.csv",
                                  RUN / "daily_metrics.csv", PRE / "manifest.json"]},
               "command": [sys.executable, *sys.argv]}
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RUN / "independent_check.json")
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({"output": str(args.output), "status": result["status"],
                      "results": result["results"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
