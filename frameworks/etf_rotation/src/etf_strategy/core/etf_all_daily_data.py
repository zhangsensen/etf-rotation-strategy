"""Point-in-time loader for the broad exchange-traded-fund daily cache."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable

import numpy as np
import pandas as pd


ETF_CODE = re.compile(r"(?:5\d{5}\.SH|1[568]\d{4}\.SZ)")


@dataclass(frozen=True)
class AllEtfDailyContext:
    panels: dict[str, pd.DataFrame]
    eligibility: pd.DataFrame
    lifecycle: pd.DataFrame
    symbols: tuple[str, ...]
    sessions: pd.DatetimeIndex
    population_table: pd.DataFrame


def _read_partitions(paths: Iterable[Path], columns: list[str]) -> pd.DataFrame:
    frames = [pd.read_parquet(path, columns=columns) for path in paths]
    if not frames:
        raise ValueError("daily cache contains no partitions in the requested range")
    return pd.concat(frames, ignore_index=True)


def _dates(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, format="%Y%m%d", errors="coerce")


def load_all_etf_daily(
    data_root: str | Path,
    *,
    start: str,
    as_of: str,
    min_history_sessions: int = 120,
    liquidity_window: int = 20,
    min_median_amount_thousand: float = 10_000.0,
) -> AllEtfDailyContext:
    """Load adjusted daily panels and a D-known eligibility mask.

    Population is the point-in-time set of exchange funds whose identity name
    contains ``ETF`` and whose code is exchange-qualified.  Listing lifecycle,
    observed history, same-day OHLCV, and trailing median amount are the only
    eligibility inputs.  No future return or future survival field is used.
    """
    if min_history_sessions < 1 or liquidity_window < 1:
        raise ValueError("history and liquidity windows must be positive")
    if min_median_amount_thousand < 0:
        raise ValueError("liquidity threshold must be nonnegative")
    root = Path(data_root).resolve()
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(as_of)
    if (
        pd.isna(start_ts)
        or pd.isna(end_ts)
        or start_ts.tzinfo is not None
        or end_ts.tzinfo is not None
        or start_ts != start_ts.normalize()
        or end_ts != end_ts.normalize()
        or start_ts > end_ts
    ):
        raise ValueError("start/as_of must be ordered timezone-naive dates")

    manifest = json.loads((root / "manifest.json").read_text())
    if manifest.get("schema_version") != "all_exchange_etf_daily_cache_v1":
        raise ValueError("unexpected all-ETF cache schema")
    if pd.Timestamp(manifest["start"]) > start_ts or pd.Timestamp(manifest["end"]) < end_ts:
        raise ValueError("cache manifest does not cover requested dates")

    calendar = pd.read_parquet(root / "metadata/trading_sessions.parquet")
    sessions = pd.DatetimeIndex(_dates(calendar["trade_date"]).dropna().sort_values().unique())
    sessions = sessions[(sessions >= start_ts) & (sessions <= end_ts)]
    if sessions.empty or sessions[-1] != end_ts:
        raise ValueError("as_of must be a cached open trading session")

    basic = pd.read_parquet(root / "metadata/fund_basic.parquet").copy()
    basic["ts_code"] = basic["ts_code"].astype(str).str.strip().str.upper()
    basic["list_date_parsed"] = _dates(basic["list_date"])
    basic["delist_date_parsed"] = _dates(basic["delist_date"])
    names = basic["name"].fillna("").astype(str)
    codes = basic["ts_code"].map(lambda value: bool(ETF_CODE.fullmatch(value)))
    etf_named = names.str.contains("ETF", case=False, regex=False)
    population = basic.loc[
        codes
        & etf_named
        & basic["list_date_parsed"].notna()
        & basic["list_date_parsed"].le(end_ts)
        & (
            basic["delist_date_parsed"].isna()
            | basic["delist_date_parsed"].ge(start_ts)
        )
    ].copy()
    if population["ts_code"].duplicated().any() or population.empty:
        raise ValueError("ETF identity population is empty or duplicated")
    population = population.sort_values("ts_code").reset_index(drop=True)
    symbols = tuple(population["ts_code"])

    date_keys = [value.strftime("%Y%m%d") for value in sessions]
    daily_paths = [root / "raw/fund_daily" / f"{value}.parquet" for value in date_keys]
    adj_paths = [root / "raw/fund_adj" / f"{value}.parquet" for value in date_keys]
    missing = [str(path) for path in (*daily_paths, *adj_paths) if not path.exists()]
    if missing:
        raise ValueError(f"cache is missing {len(missing)} requested partitions; first={missing[0]}")

    daily = _read_partitions(
        daily_paths,
        ["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"],
    )
    adj = _read_partitions(adj_paths, ["ts_code", "trade_date", "adj_factor"])
    daily["trade_date"] = _dates(daily["trade_date"])
    adj["trade_date"] = _dates(adj["trade_date"])
    daily = daily[daily["ts_code"].isin(symbols)]
    adj = adj[adj["ts_code"].isin(symbols)]
    if daily.duplicated(["trade_date", "ts_code"]).any() or adj.duplicated(
        ["trade_date", "ts_code"]
    ).any():
        raise ValueError("daily or adjustment cache contains duplicate symbol-dates")
    merged = daily.merge(
        adj,
        on=["ts_code", "trade_date"],
        how="left",
        validate="one_to_one",
    )
    for column in ("open", "high", "low", "close", "vol", "amount", "adj_factor"):
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    valid_factor = np.isfinite(merged["adj_factor"]) & merged["adj_factor"].gt(0)
    merged = merged.loc[valid_factor].copy()

    panels: dict[str, pd.DataFrame] = {}
    for field in ("open", "high", "low", "close"):
        merged[f"adjusted_{field}"] = merged[field] * merged["adj_factor"]
        panels[field] = (
            merged.pivot(index="trade_date", columns="ts_code", values=f"adjusted_{field}")
            .reindex(index=sessions, columns=symbols)
            .astype(float)
        )
    panels["volume"] = (
        merged.pivot(index="trade_date", columns="ts_code", values="vol")
        .reindex(index=sessions, columns=symbols)
        .astype(float)
    )
    panels["amount"] = (
        merged.pivot(index="trade_date", columns="ts_code", values="amount")
        .reindex(index=sessions, columns=symbols)
        .astype(float)
    )

    list_dates = population.set_index("ts_code")["list_date_parsed"].reindex(symbols)
    delist_dates = population.set_index("ts_code")["delist_date_parsed"].reindex(symbols)
    lifecycle = pd.DataFrame(
        sessions.to_numpy()[:, None] >= list_dates.to_numpy()[None, :],
        index=sessions,
        columns=symbols,
    )
    lifecycle &= pd.DataFrame(
        pd.isna(delist_dates.to_numpy())[None, :]
        | (sessions.to_numpy()[:, None] <= delist_dates.to_numpy()[None, :]),
        index=sessions,
        columns=symbols,
    )
    valid_today = (
        panels["open"].gt(0)
        & panels["high"].gt(0)
        & panels["low"].gt(0)
        & panels["close"].gt(0)
        & panels["volume"].gt(0)
        & panels["amount"].gt(0)
    )
    observed_history = valid_today.cumsum().ge(min_history_sessions)
    liquid = panels["amount"].rolling(
        liquidity_window, min_periods=liquidity_window
    ).median().ge(min_median_amount_thousand)
    eligibility = lifecycle & valid_today & observed_history & liquid
    return AllEtfDailyContext(
        panels=panels,
        eligibility=eligibility,
        lifecycle=lifecycle,
        symbols=symbols,
        sessions=sessions,
        population_table=population,
    )


def hash_all_etf_cache_contract(data_root: str | Path) -> dict[str, object]:
    """Hash small contract files; raw partitions remain local and are counted."""
    root = Path(data_root).resolve()
    files = (
        root / "manifest.json",
        root / "metadata/fund_basic.parquet",
        root / "metadata/trading_sessions.parquet",
    )
    payload: dict[str, object] = {"root": str(root), "files": {}}
    for path in files:
        payload["files"][str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    payload["daily_partition_count"] = len(list((root / "raw/fund_daily").glob("*.parquet")))
    payload["adj_partition_count"] = len(list((root / "raw/fund_adj").glob("*.parquet")))
    return payload
