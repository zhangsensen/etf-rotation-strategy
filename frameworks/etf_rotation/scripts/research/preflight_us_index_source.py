#!/usr/bin/env python3
"""Check external US index closes for D-close ETF research without labels.

FRED historical observations are discovery data, not verified publication
vintages. Market data and diagnostics stay under local runtime_outputs/.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
SERIES = ("NASDAQ100", "SP500")
START = "2023-01-01"
COLD_CUTOFF = "2026-03-24"
MAX_STALE_CALENDAR_DAYS = 5


def parse_series(raw: bytes, series: str, cutoff: pd.Timestamp) -> pd.DataFrame:
    frame = pd.read_csv(StringIO(raw.decode("utf-8")))
    if list(frame.columns) != ["observation_date", series]:
        raise ValueError(f"unexpected FRED columns for {series}")
    frame["source_date"] = pd.to_datetime(frame.observation_date, errors="raise")
    frame["close"] = pd.to_numeric(frame[series], errors="coerce")
    if frame.source_date.isna().any() or frame.source_date.duplicated().any():
        raise ValueError(f"invalid FRED dates for {series}")
    if frame.source_date.max() > cutoff:
        raise ValueError(f"FRED response exceeded cold cutoff for {series}")
    frame = frame.dropna(subset=["close"]).sort_values("source_date")
    if frame.empty or frame.close.le(0).any():
        raise ValueError(f"no positive FRED closes for {series}")
    frame["return"] = frame.close.pct_change(fill_method=None)
    return frame[["source_date", "close", "return"]].reset_index(drop=True)


def align_known_returns(source: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """A US-date close is eligible only on a later A-share calendar date."""
    if calendar.has_duplicates or not calendar.is_monotonic_increasing:
        raise ValueError("A-share calendar must be unique and sorted")
    aligned = pd.merge_asof(
        pd.DataFrame({"signal_date": calendar}), source[["source_date", "return"]],
        left_on="signal_date", right_on="source_date", direction="backward",
        allow_exact_matches=False,
    )
    aligned["age_calendar_days"] = (aligned.signal_date - aligned.source_date).dt.days
    aligned["available"] = (aligned["age_calendar_days"].between(1, MAX_STALE_CALENDAR_DAYS)
                            & aligned["return"].notna())
    aligned.loc[~aligned.available, "return"] = float("nan")
    if not aligned.loc[aligned.available, "source_date"].lt(
        aligned.loc[aligned.available, "signal_date"]
    ).all():
        raise ValueError("future US close entered an A-share signal")
    return aligned.set_index("signal_date")


def run(output: Path, cutoff: str = COLD_CUTOFF) -> dict:
    if output.exists():
        raise FileExistsError(output)
    as_of = pd.Timestamp(cutoff)
    if as_of > pd.Timestamp(COLD_CUTOFF) or as_of != as_of.normalize():
        raise ValueError("source preflight may not exceed ETF cold cutoff")
    calendar_raw = pd.read_parquet(
        DATA_ROOT / "1d/510300.SH.parquet", columns=["trade_date"],
        filters=[("trade_date", "<=", as_of)],
    )
    calendar = pd.DatetimeIndex(pd.to_datetime(calendar_raw.trade_date)).sort_values()
    calendar = calendar[(calendar >= pd.Timestamp("2024-01-01")) & (calendar <= as_of)]
    records = {}
    raw_files = {}
    for series in SERIES:
        response = requests.get(URL, params={"id": series, "cosd": START, "coed": cutoff}, timeout=30)
        response.raise_for_status()
        raw = response.content
        source = parse_series(raw, series, as_of)
        aligned = align_known_returns(source, calendar)
        raw_files[series] = raw
        counts = {str(year): {"sessions": int((calendar.year == year).sum()),
                              "available": int(aligned.loc[aligned.index.year == year, "available"].sum())}
                  for year in sorted(set(calendar.year))}
        records[series] = {"raw_sha256": sha256(raw).hexdigest(),
                           "first_source_date": str(source.source_date.min().date()),
                           "last_source_date": str(source.source_date.max().date()),
                           "max_observed_age_days": int(aligned.age_calendar_days.max()),
                           "coverage": counts,
                           "source_page": f"https://fred.stlouisfed.org/series/{series}"}
    output.mkdir(parents=True)
    for series, raw in raw_files.items():
        (output / f"{series}.csv").write_bytes(raw)
    manifest = {"status": "PREFLIGHT_NO_ETF_LABELS_READ", "cutoff": cutoff,
                "date_rule": "US observation_date strictly earlier than A-share signal_date",
                "max_stale_calendar_days": MAX_STALE_CALENDAR_DAYS,
                "publication_vintage": "FRED historical snapshot; actual D-close release timestamps not verified",
                "source": URL, "series": records}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--as-of", default=COLD_CUTOFF)
    args = parser.parse_args()
    result = run(args.output, args.as_of)
    print(json.dumps({"output": str(args.output), "coverage": {
        series: item["coverage"] for series, item in result["series"].items()
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
