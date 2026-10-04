#!/usr/bin/env python3
"""Download point-in-time exchange-fund daily bars into a local research cache.

The cache is data, not source control material.  It is partitioned by trade date
so interrupted downloads resume without rewriting completed sessions.  Fund
identity and listing lifecycle come from TuShare ``fund_basic(market='E')``;
prices and adjustment factors come from ``fund_daily`` and ``fund_adj``.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Callable

import pandas as pd


FUND_BASIC_FIELDS = (
    "ts_code,name,management,custodian,fund_type,found_date,due_date,list_date,"
    "issue_date,delist_date,issue_amount,m_fee,c_fee,duration_year,p_value,"
    "min_amount,exp_return,benchmark,status,invest_type,type,trustee,"
    "purc_startdate,redm_startdate,market"
)
DAILY_COLUMNS = (
    "ts_code", "trade_date", "pre_close", "open", "high", "low", "close",
    "change", "pct_chg", "vol", "amount",
)
ADJ_COLUMNS = ("ts_code", "trade_date", "adj_factor")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_token(source_project: Path) -> str:
    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if token:
        return token
    env_path = source_project / ".env"
    if env_path.exists():
        for raw in env_path.read_text().splitlines():
            line = raw.strip()
            if line.startswith("TUSHARE_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
                if token:
                    return token
    raise RuntimeError("TUSHARE_TOKEN is unavailable in the environment or source project .env")


@contextmanager
def _exclusive_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".download.lock"
    with lock_path.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_parquet(temporary, index=False)
    temporary.replace(path)


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def _call_with_retry(
    call: Callable[[], pd.DataFrame],
    *,
    attempts: int,
    endpoint: str,
    trade_date: str | None = None,
) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return call()
        except Exception as error:  # network/API errors are retriable
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(min(30.0, 2.0**attempt))
    suffix = f" trade_date={trade_date}" if trade_date else ""
    raise RuntimeError(f"TuShare {endpoint} failed after {attempts} attempts{suffix}") from last_error


def _validate_partition(
    frame: pd.DataFrame,
    *,
    trade_date: str,
    columns: tuple[str, ...],
    endpoint: str,
) -> pd.DataFrame:
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"{endpoint} missing columns: {sorted(missing)}")
    out = frame.loc[:, list(columns)].copy()
    out["ts_code"] = out["ts_code"].astype(str).str.strip().str.upper()
    out["trade_date"] = out["trade_date"].astype(str)
    if out.empty or set(out["trade_date"]) != {trade_date}:
        raise ValueError(f"{endpoint} returned an empty or wrong-date partition for {trade_date}")
    if out["ts_code"].duplicated().any():
        raise ValueError(f"{endpoint} returned duplicate codes for {trade_date}")
    return out.sort_values("ts_code").reset_index(drop=True)


def _sessions(pro: Any, start: str, end: str, attempts: int) -> list[str]:
    calendar = _call_with_retry(
        lambda: pro.trade_cal(
            exchange="SSE", start_date=start, end_date=end, is_open="1",
            fields="cal_date,is_open",
        ),
        attempts=attempts,
        endpoint="trade_cal",
    )
    if calendar.empty or set(calendar.columns) < {"cal_date", "is_open"}:
        raise ValueError("trade_cal returned no usable sessions")
    sessions = sorted(calendar.loc[calendar["is_open"].astype(int).eq(1), "cal_date"].astype(str))
    if not sessions:
        raise ValueError("trade_cal open-session list is empty")
    return sessions


def download(args: argparse.Namespace) -> None:
    import tushare as ts

    root = args.data_root.resolve()
    source_project = args.source_project.resolve()
    token = _load_token(source_project)
    pro = ts.pro_api(token)
    with _exclusive_lock(root):
        basic_path = root / "metadata/fund_basic.parquet"
        # The identity snapshot is part of the preregistered population contract.
        # Preserve it when extending a cache into the forward period; silently
        # refreshing names/listing metadata would mutate the sealed experiment.
        if basic_path.exists():
            basic = pd.read_parquet(basic_path)
        else:
            basic = _call_with_retry(
                lambda: pro.fund_basic(market="E", fields=FUND_BASIC_FIELDS),
                attempts=args.attempts,
                endpoint="fund_basic",
            )
            if basic.empty or basic["ts_code"].duplicated().any():
                raise ValueError("fund_basic is empty or contains duplicate codes")
            basic = basic.sort_values("ts_code").reset_index(drop=True)
            _atomic_parquet(basic, basic_path)

        requested_sessions = _sessions(pro, args.start, args.end, args.attempts)
        calendar_path = root / "metadata/trading_sessions.parquet"
        existing_sessions: list[str] = []
        if calendar_path.exists():
            existing_calendar = pd.read_parquet(calendar_path)
            if "trade_date" not in existing_calendar:
                raise ValueError("existing trading calendar is missing trade_date")
            existing_sessions = existing_calendar["trade_date"].astype(str).tolist()
        sessions = sorted(set(existing_sessions).union(requested_sessions))
        _atomic_parquet(pd.DataFrame({"trade_date": sessions}), calendar_path)

        daily_root = root / "raw/fund_daily"
        adj_root = root / "raw/fund_adj"
        completed = 0
        calls = 0
        for index, trade_date in enumerate(requested_sessions, start=1):
            daily_path = daily_root / f"{trade_date}.parquet"
            adj_path = adj_root / f"{trade_date}.parquet"
            if not daily_path.exists():
                daily = _call_with_retry(
                    lambda date=trade_date: pro.fund_daily(trade_date=date),
                    attempts=args.attempts,
                    endpoint="fund_daily",
                    trade_date=trade_date,
                )
                daily = _validate_partition(
                    daily, trade_date=trade_date, columns=DAILY_COLUMNS, endpoint="fund_daily"
                )
                _atomic_parquet(daily, daily_path)
                calls += 1
                time.sleep(args.rate_seconds)
            if not adj_path.exists():
                adj = _call_with_retry(
                    lambda date=trade_date: pro.fund_adj(trade_date=date),
                    attempts=args.attempts,
                    endpoint="fund_adj",
                    trade_date=trade_date,
                )
                adj = _validate_partition(
                    adj, trade_date=trade_date, columns=ADJ_COLUMNS, endpoint="fund_adj"
                )
                _atomic_parquet(adj, adj_path)
                calls += 1
                time.sleep(args.rate_seconds)
            completed += 1
            if index == 1 or index % args.progress_every == 0 or index == len(requested_sessions):
                print(
                    f"[download] sessions={index}/{len(requested_sessions)} api_calls={calls} "
                    f"latest={trade_date}",
                    flush=True,
                )

        manifest = {
            "schema_version": "all_exchange_etf_daily_cache_v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": "TuShare Pro fund_basic/fund_daily/fund_adj/trade_cal",
            "start": min(sessions),
            "end": max(sessions),
            "session_count": len(sessions),
            "completed_session_count": len(sessions),
            "requested_start": args.start,
            "requested_end": args.end,
            "requested_session_count": len(requested_sessions),
            "requested_completed_session_count": completed,
            "fund_basic_rows": len(basic),
            "fund_basic_sha256": _sha256(basic_path),
            "calendar_sha256": _sha256(calendar_path),
            "partition_policy": "one immutable parquet per endpoint per trade_date; reruns skip existing files",
            "data_files_are_local_only": True,
        }
        _atomic_json(manifest, root / "manifest.json")
        print(
            f"All-ETF daily cache complete: total_sessions={len(sessions)} "
            f"requested_sessions={len(requested_sessions)} root={root}",
            flush=True,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--start", required=True, help="YYYYMMDD inclusive")
    parser.add_argument("--end", required=True, help="YYYYMMDD inclusive")
    parser.add_argument(
        "--source-project",
        type=Path,
        default=Path(str(Path(__file__).resolve().parents[4])),
        help="Project containing the private TuShare .env; token values are never written",
    )
    parser.add_argument("--attempts", type=int, default=5)
    parser.add_argument("--rate-seconds", type=float, default=0.05)
    parser.add_argument("--progress-every", type=int, default=25)
    args = parser.parse_args()
    for field in ("start", "end"):
        value = getattr(args, field)
        parsed = pd.to_datetime(value, format="%Y%m%d", errors="raise")
        if parsed.strftime("%Y%m%d") != value:
            raise ValueError(f"--{field} must be YYYYMMDD")
    if args.start > args.end:
        raise ValueError("--start must not exceed --end")
    if args.attempts < 1 or args.rate_seconds < 0 or args.progress_every < 1:
        raise ValueError("attempts/progress must be positive and rate must be nonnegative")
    return args


if __name__ == "__main__":
    download(parse_args())
