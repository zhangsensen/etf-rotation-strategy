"""Load the locally observed A-share index daily cross-section."""
from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds

from .etf_all_daily_data import AllEtfDailyContext


INDEX_CODE = re.compile(r"(?:000\d{3}\.SH|399\d{3}\.SZ)")


def load_external_index_daily(
    data_root: str | Path,
    *,
    start: str,
    as_of: str,
    min_history_sessions: int = 120,
    liquidity_window: int = 20,
    min_median_turnover_cny: float = 0.0,
) -> AllEtfDailyContext:
    """Load index OHLCV rows while excluding stocks, funds and future rows."""
    root = Path(data_root).resolve()
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(as_of)
    if start_ts > end_ts or min_history_sessions < 1 or liquidity_window < 1:
        raise ValueError("invalid index daily date/history contract")
    schema = pa.schema(
        [
            ("ts_code", pa.string()),
            ("trade_date", pa.timestamp("ns")),
            ("open", pa.float64()),
            ("high", pa.float64()),
            ("low", pa.float64()),
            ("close", pa.float64()),
            ("volume", pa.float64()),
            ("turnover", pa.float64()),
            ("turnover_rate", pa.float64()),
            ("is_st", pa.bool_()),
            ("sector", pa.string()),
        ]
    )
    paths = sorted(str(path) for path in root.glob("*.parquet"))
    if not paths:
        raise ValueError("index daily root contains no canonical parquet files")
    dataset = ds.dataset(paths, format="parquet", schema=schema)
    table = dataset.to_table(
        columns=[
            "ts_code", "trade_date", "open", "high", "low", "close",
            "volume", "turnover",
        ],
        filter=(ds.field("trade_date") >= pa.scalar(start_ts.to_datetime64()))
        & (ds.field("trade_date") <= pa.scalar(end_ts.to_datetime64())),
    )
    daily = table.to_pandas()
    daily["ts_code"] = daily["ts_code"].astype(str).str.strip().str.upper()
    daily = daily[
        daily["ts_code"].map(lambda value: bool(INDEX_CODE.fullmatch(value)))
    ].copy()
    daily["trade_date"] = pd.to_datetime(daily["trade_date"], errors="coerce")
    daily = daily[
        daily["trade_date"].notna()
        & daily["trade_date"].between(start_ts, end_ts)
    ]
    if daily.empty or daily.duplicated(["trade_date", "ts_code"]).any():
        raise ValueError("index daily population is empty or duplicated")
    for column in ("open", "high", "low", "close", "volume", "turnover"):
        daily[column] = pd.to_numeric(daily[column], errors="coerce")
    symbols = tuple(sorted(daily["ts_code"].unique()))
    sessions = pd.DatetimeIndex(sorted(daily["trade_date"].unique()))
    if sessions.empty or sessions[-1] != end_ts:
        raise ValueError("index as_of must be an observed trading session")

    panels: dict[str, pd.DataFrame] = {}
    for output, source in (
        ("open", "open"), ("high", "high"), ("low", "low"),
        ("close", "close"), ("volume", "volume"), ("amount", "turnover"),
    ):
        panels[output] = daily.pivot(
            index="trade_date", columns="ts_code", values=source
        ).reindex(index=sessions, columns=symbols).astype(float)
    valid = (
        panels["open"].gt(0)
        & panels["high"].gt(0)
        & panels["low"].gt(0)
        & panels["close"].gt(0)
        & panels["volume"].gt(0)
        & panels["amount"].gt(0)
    )
    lifecycle = valid.cumsum().gt(0)
    history = valid.cumsum().ge(min_history_sessions)
    liquid = panels["amount"].rolling(
        liquidity_window, min_periods=liquidity_window
    ).median().ge(min_median_turnover_cny)
    eligibility = lifecycle & valid & history & liquid
    return AllEtfDailyContext(
        panels=panels,
        eligibility=eligibility,
        lifecycle=lifecycle,
        symbols=symbols,
        sessions=sessions,
        population_table=pd.DataFrame({"ts_code": symbols}),
    )
