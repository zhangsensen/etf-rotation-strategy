#!/usr/bin/env python3
"""Observe all saved H5 IC leads after a full forward month matures.

The v4 panel supplies its five matching definitions. The remaining eleven
are recomputed independently; none enter the v4 monthly selection process.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd
import yaml

import run_etf_ic_lead_watch as watch

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / "frameworks/etf_rotation/configs/etf_ic_lead_watch_v2.yaml"
LEDGER = ROOT / "runtime_outputs/etf_rotation_research/ic_lead_watch_v2_monthly.jsonl"
EXTRA_PANEL_ROOT = ROOT / "runtime_outputs/etf_rotation_research/ic_lead_extra_panels"
UNCOMPUTABLE_SHARE_STATUS = "UNCOMPUTABLE_FORWARD_SHARE_PARENT_VINTAGE"


def ic_status(source_status: str, n: int) -> str:
    """Keep an unavailable source distinct from a computable zero-IC month."""
    if source_status == UNCOMPUTABLE_SHARE_STATUS:
        if n:
            raise ValueError("uncomputable share source has forward IC observations")
        return "UNCOMPUTABLE_SOURCE"
    return "COMPUTED" if n else "NO_COMPLETE_FORWARD_IC_DATE"


def merge_panels(
    catalog: list[str], parent_catalog: list[str], base_ic: pd.DataFrame,
    base_dates: pd.DataFrame, extra: dict,
) -> pd.DataFrame:
    if base_ic.columns.has_duplicates or base_ic.index.has_duplicates:
        raise ValueError("duplicate v4 panel candidate or date")
    if list(extra["daily_ic"].columns) != [c for c in catalog if c not in parent_catalog]:
        raise ValueError("extra panel does not match the frozen lead watch catalog")
    if not extra["daily_ic"].index.equals(base_ic.index):
        raise ValueError("extra panel calendar differs from v4")
    normalized_dates = base_dates.apply(pd.to_datetime)
    if not extra["label_dates"].equals(normalized_dates):
        raise ValueError("extra label dates differ from v4")
    if len(catalog) != len(set(catalog)) or len(catalog) != 16:
        raise ValueError("lead watch v2 requires sixteen unique historical leads")
    if not set(catalog).issubset(set(parent_catalog) | set(extra["daily_ic"].columns)):
        raise ValueError("missing lead definition")
    return pd.concat([base_ic, extra["daily_ic"]], axis=1)[catalog]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--panel-root", type=Path, default=watch.PANEL_ROOT)
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    args = parser.parse_args()
    config_bytes = args.config.read_bytes()
    config = yaml.safe_load(config_bytes)
    parent_path = ROOT / config["parent_contract"]
    parent_bytes = parent_path.read_bytes()
    parent = yaml.safe_load(parent_bytes)
    if (config["entry_lag"], config["horizon"], config["signal_time"]) != (2, 5, "close_D"):
        raise ValueError("lead watch timing changed")
    if config["first_month"] != "2026-10":
        raise ValueError("lead watch first month changed")
    catalog = list(config["candidate_catalog"])
    parent_catalog = list(parent["candidate_catalog"])
    panel_dirs = sorted(p for p in args.panel_root.iterdir() if p.is_dir() and
                        (p / "daily_ic.csv").is_file() and (p / "label_dates.csv").is_file())
    if not panel_dirs:
        raise FileNotFoundError("no complete v4 daily panel")
    panel_dir = panel_dirs[-1]
    as_of = panel_dir.name
    base_ic = pd.read_csv(panel_dir / "daily_ic.csv", index_col=0, parse_dates=True)
    base_dates = pd.read_csv(panel_dir / "label_dates.csv", index_col=0, parse_dates=True)
    if base_ic.index.max() != pd.Timestamp(as_of) or not base_ic.index.equals(base_dates.index):
        raise ValueError("v4 panel as_of/calendar mismatch")
    if list(base_ic.columns) != parent_catalog:
        raise ValueError("v4 panel catalog mismatch")
    # Check every month from the first eligible one, so a missed scheduler run
    # cannot silently lose an earlier forward month.
    present = [c for c in catalog if c in parent_catalog]
    if not present:
        raise ValueError("no existing v4 lead")
    gate_config = {**config, "candidate_catalog": present}
    first = pd.Period(config["first_month"], freq="M")
    last = pd.Period(as_of, freq="M") - 1
    matured = [str(period) for period in pd.period_range(first, last, freq="M")
               if watch.monthly_rows(gate_config, base_ic, base_dates, str(period), as_of) is not None]
    if not matured:
        print("NOOP: no eligible month has fully matured labels")
        return
    from build_etf_ic_lead_extra_panel import build_extra, persist_extra
    extra = build_extra(as_of)
    merged = merge_panels(catalog, parent_catalog, base_ic, base_dates, extra)
    coverage = {item["candidate"]: item for item in extra["coverage"]}
    if set(coverage) != set(extra["daily_ic"].columns):
        raise ValueError("extra source coverage is incomplete")
    extra_panel_dir = persist_extra(extra, EXTRA_PANEL_ROOT)
    config_sha = hashlib.sha256(config_bytes).hexdigest()
    parent_sha = hashlib.sha256(parent_bytes).hexdigest()
    for month in matured:
        rows = watch.monthly_rows(config, merged, base_dates, month, as_of)
        if rows is None:
            raise ValueError("maturity changed while building extra panel")
        for row in rows:
            row["config_sha256"] = config_sha
            row["parent_contract_sha256"] = parent_sha
            row["panel_dir"] = str(panel_dir)
            row["extra_panel_dir"] = str(extra_panel_dir)
            source_status = (
                coverage[row["candidate"]]["status"] if row["candidate"] in coverage
                else "V4_PANEL"
            )
            row["source_status"] = source_status
            row["ic_status"] = ic_status(source_status, row["n"])
            row["extra_panel_version"] = extra["version"]
        print(f"{month}: " + ("APPENDED" if watch.append_once(args.ledger, rows)
                            else "NOOP: month already recorded"))


if __name__ == "__main__":
    main()
