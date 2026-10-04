"""Point-in-time loader for the non-ETF exchange-fund holdout population."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .etf_all_daily_data import (
    AllEtfDailyContext,
    ETF_CODE,
    _dates,
    _read_partitions,
)


def load_external_non_etf_daily(
    data_root: str | Path,
    *,
    start: str,
    as_of: str,
    allowed_fund_types: tuple[str, ...] = ("股票型", "混合型"),
    min_history_sessions: int = 120,
    liquidity_window: int = 20,
    min_median_amount_thousand: float = 10_000.0,
) -> AllEtfDailyContext:
    """Load a lifecycle-correct non-ETF population never used by ETF discovery.

    Identity uses only the frozen ``fund_basic`` snapshot, code class, fund
    type and listing lifecycle.  Outcomes never enter identity or eligibility.
    """
    if not allowed_fund_types:
        raise ValueError("allowed_fund_types must be nonempty")
    if min_history_sessions < 1 or liquidity_window < 1:
        raise ValueError("history and liquidity windows must be positive")
    root = Path(data_root).resolve()
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(as_of)
    if start_ts > end_ts or start_ts != start_ts.normalize() or end_ts != end_ts.normalize():
        raise ValueError("start/as_of must be ordered dates")

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
    population = basic.loc[
        basic["ts_code"].map(lambda value: bool(ETF_CODE.fullmatch(value)))
        & ~names.str.contains("ETF", case=False, regex=False)
        & basic["fund_type"].isin(allowed_fund_types)
        & basic["list_date_parsed"].notna()
        & basic["list_date_parsed"].le(end_ts)
        & (basic["delist_date_parsed"].isna() | basic["delist_date_parsed"].ge(start_ts))
    ].copy()
    if population.empty or population["ts_code"].duplicated().any():
        raise ValueError("external fund identity population is empty or duplicated")
    population = population.sort_values("ts_code").reset_index(drop=True)
    symbols = tuple(population["ts_code"])

    keys = [date.strftime("%Y%m%d") for date in sessions]
    daily_paths = [root / "raw/fund_daily" / f"{key}.parquet" for key in keys]
    adj_paths = [root / "raw/fund_adj" / f"{key}.parquet" for key in keys]
    missing = [path for path in (*daily_paths, *adj_paths) if not path.exists()]
    if missing:
        raise ValueError(f"external cache partitions missing; first={missing[0]}")
    daily = _read_partitions(
        daily_paths,
        ["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"],
    )
    adj = _read_partitions(adj_paths, ["ts_code", "trade_date", "adj_factor"])
    daily["trade_date"], adj["trade_date"] = _dates(daily["trade_date"]), _dates(adj["trade_date"])
    daily, adj = daily[daily["ts_code"].isin(symbols)], adj[adj["ts_code"].isin(symbols)]
    if daily.duplicated(["trade_date", "ts_code"]).any() or adj.duplicated(
        ["trade_date", "ts_code"]
    ).any():
        raise ValueError("external daily or adjustment rows are duplicated")
    merged = daily.merge(adj, on=["ts_code", "trade_date"], how="left", validate="one_to_one")
    for column in ("open", "high", "low", "close", "vol", "amount", "adj_factor"):
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    merged = merged[np.isfinite(merged["adj_factor"]) & merged["adj_factor"].gt(0)].copy()

    panels: dict[str, pd.DataFrame] = {}
    for field in ("open", "high", "low", "close"):
        merged[f"adjusted_{field}"] = merged[field] * merged["adj_factor"]
        panels[field] = merged.pivot(
            index="trade_date", columns="ts_code", values=f"adjusted_{field}"
        ).reindex(index=sessions, columns=symbols).astype(float)
    for output, source in (("volume", "vol"), ("amount", "amount")):
        panels[output] = merged.pivot(
            index="trade_date", columns="ts_code", values=source
        ).reindex(index=sessions, columns=symbols).astype(float)

    indexed = population.set_index("ts_code")
    list_dates = indexed["list_date_parsed"].reindex(symbols)
    delist_dates = indexed["delist_date_parsed"].reindex(symbols)
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
    valid = (
        panels["open"].gt(0)
        & panels["high"].gt(0)
        & panels["low"].gt(0)
        & panels["close"].gt(0)
        & panels["volume"].gt(0)
        & panels["amount"].gt(0)
    )
    history = valid.cumsum().ge(min_history_sessions)
    liquid = panels["amount"].rolling(
        liquidity_window, min_periods=liquidity_window
    ).median().ge(min_median_amount_thousand)
    eligibility = lifecycle & valid & history & liquid
    return AllEtfDailyContext(
        panels=panels,
        eligibility=eligibility,
        lifecycle=lifecycle,
        symbols=symbols,
        sessions=sessions,
        population_table=population,
    )
