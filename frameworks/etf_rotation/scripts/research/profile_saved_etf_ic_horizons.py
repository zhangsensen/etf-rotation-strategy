#!/usr/bin/env python3
"""Describe H1/H5/H10/H20 IC for saved ETF leads without registering definitions.

This reads score/label CSV rows only through the fixed cold cutoff and loads
raw ETF data with the same as_of filter. It is a historical sensitivity table,
not a new screen, confirmation, or change to the frozen H5 judge.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "frameworks/etf_rotation/src"))

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core.etf_group_discovery import aggregate, labels
from etf_strategy.core.etf_mining_referee import newey_west_t_calendar
from etf_strategy.core.etf_rank_utils import stable_rank

GROUPS_PATH = ROOT / "frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml"
UNIVERSE_PATH = ROOT / "config/etf_rotation_universe_v1.json"
DATA_ROOT = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
RUNS_ROOT = ROOT / "runtime_outputs/etf_rotation_research"
GROUP_COLUMNS = [
    "cn_technology_manufacturing", "hk_technology", "us_large_growth",
    "innovative_pharma", "gold", "metals_equity", "dividend_low_vol",
    "electric_power",
]


def read_csv_through(path: Path, calendar: pd.DatetimeIndex, cutoff: str) -> pd.DataFrame:
    """Read exactly the pre-cutoff session count; never load a cold CSV row."""
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if header[0] not in {"signal_date", "trade_date", ""}:
            raise ValueError(f"unexpected date column in {path}: {header[0]}")
        first = next(reader)[0]
    expected = calendar[(calendar >= pd.Timestamp(first)) & (calendar <= pd.Timestamp(cutoff))]
    frame = pd.read_csv(path, nrows=len(expected)).set_index(header[0])
    frame.index = pd.to_datetime(frame.index)
    if not frame.index.equals(expected):
        raise ValueError(f"saved CSV is not one row per reference session through cutoff: {path}")
    return frame.apply(pd.to_numeric, errors="coerce")


def score_path(candidate: str, source_run: str) -> Path:
    choices = [
        RUNS_ROOT / "runs" / source_run / f"scores_{candidate}.csv",
        RUNS_ROOT / source_run / f"scores_{candidate}.csv",
    ]
    found = [path for path in choices if path.exists()]
    if len(found) != 1:
        raise ValueError(f"expected one saved score for {candidate}: {found}")
    return found[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--as-of", default="2026-03-24")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    cutoff = pd.Timestamp(args.as_of)
    if cutoff != cutoff.normalize():
        raise ValueError("as_of must be a full trading date")
    leads = pd.read_csv(args.snapshot / "basic_ic_leads.csv")
    panels = load_canonical_daily(DATA_ROOT, UNIVERSE_PATH, as_of=args.as_of, roles=("candidate",))
    reference = pd.read_parquet(
        DATA_ROOT / "1d/510300.SH.parquet",
        columns=["trade_date"],
        filters=[("trade_date", "<=", cutoff)],
    )
    calendar = pd.DatetimeIndex(pd.to_datetime(reference.trade_date)).sort_values()
    if len(panels["open"].index.difference(calendar)):
        raise ValueError("candidate session missing from reference calendar")
    panels = {name: panel.reindex(calendar) for name, panel in panels.items()}
    if cutoff not in calendar:
        raise ValueError("as_of not in ETF trading calendar")
    groups = yaml.safe_load(GROUPS_PATH.read_text())["groups"]
    group_labels = {}
    timing = {}
    for horizon in (1, 5, 10, 20):
        member_return, dates = labels(panels, lag=2, horizon=horizon)
        mature = dates["exit_date"].le(cutoff)
        if not ((dates.loc[mature, "entry_date"] > dates.index[mature]) &
                (dates.loc[mature, "exit_date"] > dates.loc[mature, "entry_date"])).all():
            raise ValueError(f"invalid signal/entry/exit timing for H{horizon}")
        group_labels[horizon] = aggregate(member_return, groups)[GROUP_COLUMNS]
        timing[horizon] = dates
    rows = []
    for lead in leads.itertuples(index=False):
        path = score_path(lead.candidate, lead.source_run)
        score = read_csv_through(path, calendar, args.as_of)[GROUP_COLUMNS].reindex(calendar)
        saved_h5_path = path.parent / "group_labels.csv"
        saved_h5 = read_csv_through(saved_h5_path, calendar, args.as_of)[GROUP_COLUMNS]
        comparable_dates = group_labels[5].index.intersection(saved_h5.index)
        current_h5 = group_labels[5].reindex(comparable_dates)
        saved_h5 = saved_h5.reindex(comparable_dates)
        comparable = current_h5.notna() & saved_h5.notna()
        if comparable.sum().sum() == 0:
            raise ValueError(f"no H5 source-label comparison for {lead.candidate}")
        label_max_diff = float((current_h5 - saved_h5).abs().where(comparable).max().max())
        if label_max_diff > 1e-10:
            raise ValueError(f"H5 source-label mismatch for {lead.candidate}: {label_max_diff}")
        score_rank = stable_rank(score)
        policy = lead.evidence_policy
        if policy == "2025_DIRECTION_2026_HISTORICAL_SEGMENT":
            start = pd.Timestamp("2026-01-01")
        else:
            start = pd.Timestamp("2025-01-01")
        for horizon in (1, 5, 10, 20):
            label = group_labels[horizon]
            dates = timing[horizon]
            valid = (
                score.notna().all(axis=1)
                & label.notna().all(axis=1)
                & dates["exit_date"].le(cutoff)
                & (calendar >= start)
            )
            ic = score_rank.corrwith(label.rank(axis=1, method="average"), axis=1).where(valid)
            lag = max(2, horizon * 2)
            rows.append({
                "candidate": lead.candidate,
                "source_run": lead.source_run,
                "evidence_policy": policy,
                "horizon": horizon,
                "label": f"open(D+2)->open(D+{horizon + 2})",
                "as_of": args.as_of,
                "start": start.date().isoformat(),
                "n": int(ic.notna().sum()),
                "ic": float(ic.mean()) if ic.notna().any() else np.nan,
                "hac_lag": lag,
                "hac_t": newey_west_t_calendar(ic, calendar, lag),
                "h5_saved_label_max_abs_diff": label_max_diff,
            })
    args.output.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(args.output / "horizon_ic.csv", index=False)
    (args.output / "README.md").write_text(
        "Historical sensitivity only. Same 16 H5-selected definitions and frozen directions; "
        "no new definitions, selection, or certification. Raw data and saved score rows stop "
        f"at {args.as_of}. H1/H5/H10/H20 labels use open(D+2)->open(D+2+H); "
        "only labels exited by the cutoff are counted. Original 2025-direction candidates "
        "use 2026 only; other candidates use 2025+. Adj-open labels are research prices, "
        "not execution proof. Overlapping-label HAC lag = max(2, 2H). "
        "The H5 historical lead list was selected on a longer, already seen sample, so "
        "these results are descriptive and do not create independent evidence.\n"
    )


if __name__ == "__main__":
    main()
