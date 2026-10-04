#!/usr/bin/env python3
"""Describe saved H5 leads on the real-ETF history through the cold cutoff.

This does not select factors or change the existing IC judge. The fixed 14
members only coexist from 2023-07-27, so 2024 is the only full earlier year.
The archived share interaction has no pre-2025 saved parent scores and no
point-in-time forward share source; it remains explicitly uncomputable here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as discovery
from etf_strategy.core import etf_group_daily_rounds as daily_rounds
from etf_strategy.core import etf_group_claude_rounds as claude_rounds
from etf_strategy.core import etf_group_daily_outcome as daily_outcome
from etf_strategy.core.etf_mining_referee import block_t_calendar, newey_west_t_calendar
from etf_strategy.core.etf_rank_utils import stable_rank

import build_etf_ic_monthly_panel as monthly
import build_etf_ic_lead_extra_panel as extra
from profile_saved_etf_ic_horizons import read_csv_through, score_path

DATA_ROOT = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
UNIVERSE = ROOT / "config/etf_rotation_universe_v1.json"
GROUPS = ETF / "configs/etf_candidate14_economic_groups_v1.yaml"
WATCH = ETF / "configs/etf_ic_lead_watch_v2.yaml"
MAX_AS_OF = pd.Timestamp("2026-03-24")


def _source_score(candidate: str) -> Path:
    if candidate in extra.SOURCES:
        kind, run, _direction = extra.SOURCES[candidate]
        return extra._source_dir(kind, run) / f"scores_{candidate}.csv"
    return score_path(candidate, monthly.CANDIDATE_SOURCE_RUN[candidate])


def _score(candidate: str, panels: dict, groups: dict) -> pd.DataFrame | None:
    if candidate == "range_flow_20_40_1":
        return None
    if candidate in extra.SOURCES:
        cfg, name, window = extra._definition(candidate)
        kind = extra.SOURCES[candidate][0]
        if kind == "group_breadth":
            return extra._breadth_score(panels["close"], groups)
        if kind == "daily_outcome":
            atom = daily_outcome.build_atoms(panels, cfg)[candidate]
        elif kind == "claude_rounds":
            atom = claude_rounds.build_atoms(panels, {"mechanisms": {name: cfg["mechanisms"][name]}})[candidate]
        elif kind == "daily_rounds":
            atom = daily_rounds.build_atoms(panels, cfg)[candidate]
        elif kind == "daily":
            atom = discovery.build_atoms(panels, {"windows": [window],
                                                   "mechanisms": {name: cfg["mechanisms"][name]}})[candidate]
        else:
            raise ValueError(f"unsupported historical source {kind}: {candidate}")
    else:
        kind, name, window, direction = monthly._definition(candidate)
        cfg = json.loads((monthly.RUNS_DIR / monthly.CANDIDATE_SOURCE_RUN[candidate] / "PLAN.json").read_text())["config"]
        atom = (daily_rounds if kind == "daily_rounds" else discovery).build_atoms(panels, cfg)[candidate]
    return discovery.aggregate(atom, groups)


def _period_row(candidate: str, period: str, series: pd.Series,
                calendar: pd.DatetimeIndex) -> dict:
    values = series.reindex(calendar)
    t = newey_west_t_calendar(values, calendar, 10)
    block_t, blocks = block_t_calendar(values, calendar, 5)
    return {"candidate": candidate, "period": period, "n": int(values.notna().sum()),
            "ic": float(values.mean()) if values.notna().any() else None,
            "hac_t": float(t) if pd.notna(t) else None,
            "block_t": float(block_t) if pd.notna(block_t) else None,
            "blocks": int(blocks),
            "first_signal": str(values.dropna().index.min().date()) if values.notna().any() else None,
            "last_signal": str(values.dropna().index.max().date()) if values.notna().any() else None}


def run(as_of: str, output: Path) -> dict:
    cutoff = pd.Timestamp(as_of)
    if cutoff > MAX_AS_OF or cutoff != cutoff.normalize():
        raise ValueError("historical audit may not read beyond the 2026-03-24 cold cutoff")
    if output.exists():
        raise FileExistsError(output)
    config = yaml.safe_load(WATCH.read_text())
    catalog = list(config["candidate_catalog"])
    if len(catalog) != 16 or len(set(catalog)) != 16:
        raise ValueError("expected sixteen saved historical leads")
    groups = yaml.safe_load(GROUPS.read_text())["groups"]
    universe = json.loads(UNIVERSE.read_text())["etfs"]
    symbols = [item["ts_code"] for item in universe if item["role"] == "candidate"]
    discovery.validate_groups(groups, symbols)
    panels = load_canonical_daily(DATA_ROOT, UNIVERSE, as_of=as_of, roles=("candidate",))
    raw_calendar = pd.read_parquet(DATA_ROOT / "1d/510300.SH.parquet", columns=["trade_date"],
                                   filters=[("trade_date", "<=", cutoff)])
    calendar = pd.DatetimeIndex(pd.to_datetime(raw_calendar.trade_date)).sort_values()
    if calendar.max() != cutoff or len(panels["close"].index.difference(calendar)):
        raise ValueError("cold cutoff/calendar mismatch")
    panels = {key: panel.reindex(calendar) for key, panel in panels.items()}
    known = panels["close"].notna().rolling(60).sum().eq(60).all(axis=1) & panels["volume"].gt(0).all(axis=1)
    member_labels, dates = discovery.labels(panels, lag=2, horizon=5)
    group_labels = discovery.aggregate(member_labels, groups)
    mature = dates.exit_date.notna() & dates.exit_date.le(cutoff)
    valid_timing = dates.loc[mature]
    if not ((valid_timing.entry_date > valid_timing.signal_date) &
            (valid_timing.exit_date > valid_timing.entry_date)).all():
        raise ValueError("signal < entry < exit violated")
    daily = pd.DataFrame(index=calendar, columns=catalog, dtype=float)
    repro = []
    leave_2024 = []
    for candidate in catalog:
        score = _score(candidate, panels, groups)
        if score is None:
            repro.append({"candidate": candidate, "status": "UNCOMPUTABLE_PRE2025_SHARE_SOURCE"})
            continue
        score = score.reindex(calendar)[list(groups)]
        saved = read_csv_through(_source_score(candidate), calendar, as_of)[list(groups)]
        common = saved.index.intersection(score.index)
        left, right = saved.loc[common], score.loc[common]
        mismatch = left.isna().ne(right.isna()) | ((left - right).abs() > 1e-9 * left.abs().clip(lower=1e-12))
        errors = int(mismatch.to_numpy().sum())
        if errors:
            raise ValueError(f"saved score mismatch: {candidate} {errors} cells")
        repro.append({"candidate": candidate, "status": "MATCH", "compared_dates": len(common),
                      "mismatch_cells": errors})
        complete = known & score.notna().all(axis=1) & member_labels.notna().all(axis=1) & mature
        daily[candidate] = stable_rank(score).corrwith(group_labels.rank(axis=1, method="average"),
                                                 axis=1).where(complete)
        year_calendar = calendar[calendar.year == 2024]
        year_complete = complete & dates.exit_date.dt.year.eq(2024)
        for omitted in groups:
            reduced_ic = stable_rank(score.drop(columns=omitted)).corrwith(
                group_labels.drop(columns=omitted).rank(axis=1, method="average"), axis=1
            ).where(year_complete).reindex(year_calendar)
            leave_2024.append({"candidate": candidate, "omitted_group": omitted,
                               "n": int(reduced_ic.notna().sum()),
                               "ic": float(reduced_ic.mean()) if reduced_ic.notna().any() else None})
    rows = []
    for candidate in catalog:
        for year in (2024, 2025, 2026):
            year_calendar = calendar[calendar.year == year]
            year_ic = daily[candidate].where(dates.exit_date.dt.year.eq(year))
            rows.append(_period_row(candidate, str(year), year_ic, year_calendar))
    output.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(output / "yearly_ic.csv", index=False)
    pd.DataFrame(leave_2024).to_csv(output / "leave_group_2024.csv", index=False)
    daily.loc[calendar >= pd.Timestamp("2024-01-01")].to_csv(output / "daily_ic.csv", index_label="signal_date")
    manifest = {"as_of": as_of, "population": "fixed14_eight_groups", "signal": "close(D)",
                "label": "open(D+2)->open(D+7)", "metric": "signed_daily_eight_group_rank_ic",
                "year_boundary": "exclude signals whose exit is in another year",
                "historical_status": "DESCRIPTIVE_SEEN_HISTORY_NOT_INDEPENDENT_CONFIRMATION",
                "share_interaction": "UNCOMPUTABLE_PRE2025_SHARE_SOURCE",
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "reproducibility": repro}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default="2026-03-24")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = run(args.as_of, args.output)
    print(json.dumps({"output": str(args.output), "matched": sum(
        row["status"] == "MATCH" for row in manifest["reproducibility"])}))


if __name__ == "__main__":
    main()
