#!/usr/bin/env python3
"""Append matured monthly IC for five saved leads already present in v4 panels.

This is an observation-only sidecar. It never selects candidates, edits the v4
contract, or turns a historical lead into a certified factor.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / "frameworks/etf_rotation/configs/etf_ic_lead_watch_v1.yaml"
PANEL_ROOT = ROOT / "runtime_outputs/etf_rotation_research/monthly_factory/panels"
LEDGER = ROOT / "runtime_outputs/etf_rotation_research/ic_lead_watch_monthly.jsonl"


def monthly_rows(config: dict, daily_ic: pd.DataFrame, dates: pd.DataFrame,
                 month: str, as_of: str) -> list[dict] | None:
    """Return None until the full month's H5 labels have matured."""
    period = pd.Period(month, freq="M")
    if period < pd.Period(config["first_month"], freq="M"):
        return None
    cutoff = pd.Timestamp(as_of)
    if cutoff <= period.end_time.normalize():
        return None
    ids = config["candidate_catalog"]
    if not set(ids) <= set(daily_ic.columns):
        raise ValueError("v4 panel is missing a watched lead")
    if not daily_ic.index.equals(dates.index):
        raise ValueError("IC and timing panels have different calendars")
    mask = daily_ic.index.to_period("M") == period
    if not mask.any():
        raise ValueError("closed month has no signal dates in panel")
    timing = dates.loc[mask]
    entry = pd.to_datetime(timing["entry_date"])
    exit_ = pd.to_datetime(timing["exit_date"])
    if exit_.isna().any() or (exit_ > cutoff).any():
        return None
    if not ((entry > timing.index) & (exit_ > entry)).all():
        raise ValueError("signal < entry < exit timing contract failed")
    from etf_strategy.core.etf_mining_referee import newey_west_t_calendar
    calendar = daily_ic.index[mask]
    rows = []
    for candidate in ids:
        series = daily_ic.loc[mask, candidate]
        t = newey_west_t_calendar(series, calendar, 10)
        rows.append({
            "version": config["version"], "month": str(period),
            "candidate": candidate, "as_of": as_of,
            "n": int(series.notna().sum()),
            "ic": float(series.mean()) if series.notna().any() else None,
            "hac_t": float(t) if pd.notna(t) else None,
            "evidence": "FORWARD_MONTH_DESCRIPTIVE_NOT_CERTIFIED",
        })
    return rows


def append_once(path: Path, rows: list[dict]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"version": rows[0]["version"], "month": rows[0]["month"],
              "config_sha256": rows[0]["config_sha256"],
              "parent_contract_sha256": rows[0]["parent_contract_sha256"],
              "candidates": rows}
    with path.open("a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        old = [json.loads(line) for line in handle if line.strip()]
        key = (record["version"], record["month"])
        same = [row for row in old if (row["version"], row["month"]) == key]
        if same and any(row.get("config_sha256") != record["config_sha256"] or
                        row.get("parent_contract_sha256") != record["parent_contract_sha256"]
                        for row in same):
            raise ValueError("same watchlist version/month has a different contract hash")
        if same:
            return False
        handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
        handle.flush()
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--panel-root", type=Path, default=PANEL_ROOT)
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    parent_path = ROOT / config["parent_contract"]
    parent = yaml.safe_load(parent_path.read_text())
    if (config["entry_lag"], config["horizon"], config["signal_time"]) != (2, 5, "close_D"):
        raise ValueError("watchlist timing changed")
    if not set(config["candidate_catalog"]) <= set(parent["candidate_catalog"]):
        raise ValueError("watchlist is not a subset of the frozen v4 catalog")
    if len(set(config["candidate_catalog"])) != len(config["candidate_catalog"]):
        raise ValueError("duplicate watch candidate")
    panels = sorted(p for p in args.panel_root.iterdir() if p.is_dir() and
                    (p / "daily_ic.csv").is_file() and (p / "label_dates.csv").is_file())
    if not panels:
        raise FileNotFoundError("no complete v4 daily panel")
    panel = panels[-1]
    as_of = panel.name
    daily_ic = pd.read_csv(panel / "daily_ic.csv", index_col=0, parse_dates=True)
    dates = pd.read_csv(panel / "label_dates.csv", index_col=0, parse_dates=True)
    if daily_ic.index.max() != pd.Timestamp(as_of):
        raise ValueError("panel as_of does not match panel index")
    month = str(pd.Period(as_of, freq="M") - 1)
    rows = monthly_rows(config, daily_ic, dates, month, as_of)
    if rows is None:
        print(f"NOOP: {month} labels not mature or before first month")
        return
    digest = hashlib.sha256(args.config.read_bytes()).hexdigest()
    parent_digest = hashlib.sha256(parent_path.read_bytes()).hexdigest()
    for row in rows:
        row["config_sha256"] = digest
        row["parent_contract_sha256"] = parent_digest
        row["panel_dir"] = str(panel)
    print("APPENDED" if append_once(args.ledger, rows) else "NOOP: month already recorded")


if __name__ == "__main__":
    main()
