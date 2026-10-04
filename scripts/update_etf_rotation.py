"""Independent ETF scheduler: private lock, bounded workers, validated publication."""

from __future__ import annotations

import argparse
import fcntl
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PERIODS = ("1d", "1d_qfq", "adj_factor", "1m", "5m", "15m", "30m", "60m")


def worker_command(symbol, as_of, output):
    return [
        sys.executable,
        "-m",
        "data.downloaders.etf_rotation_backfill",
        "--as-of",
        as_of,
        "--symbols",
        symbol,
        "--output",
        str(output),
    ]


def publish(stage, output, symbol, as_of):
    report = json.loads((stage / "manifest.json").read_text())
    row = report["symbols"].get(symbol, {})
    if (
        report["failures"]
        or row.get("download_errors")
        or not (row.get("daily_fresh") and row.get("minute_fresh"))
    ):
        raise ValueError("Incomplete/stale ETF download; previous data preserved")
    if any(not (stage / period / f"{symbol}.parquet").exists() for period in PERIODS):
        raise ValueError("Missing period; previous data preserved")
    # Validate every primary file before replacing any. Rename is atomic per file.
    from data.downloaders.etf_rotation_backfill import validate
    import pandas as pd

    for period in PERIODS:
        if period != "adj_factor":
            validate(
                pd.read_parquet(stage / period / f"{symbol}.parquet"),
                "trade_date" if period.startswith("1d") else "datetime",
            )
    for period in PERIODS:
        dest = output / period / f"{symbol}.parquet"
        dest.parent.mkdir(parents=True, exist_ok=True)
        (stage / period / dest.name).replace(dest)
    (output / "qa").mkdir(exist_ok=True)
    for path in (stage / "qa").glob(f"{symbol}_*.parquet"):
        shutil.copy2(path, output / "qa" / path.name)
    (output / "update_reports").mkdir(exist_ok=True)
    shutil.copy2(stage / "manifest.json", output / "update_reports" / f"{symbol}.json")
    return row


def run_one(symbol, as_of, output, timeout=300, runner=subprocess.run):
    stage = output / ".staging" / symbol
    stage.mkdir(parents=True, exist_ok=True)
    log = output / "logs" / f"{as_of}_{symbol}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        with log.open("a") as handle:
            result = runner(
                worker_command(symbol, as_of, stage),
                cwd=ROOT,
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=timeout,
            )
        if result.returncode:
            raise ValueError(f"worker exit={result.returncode}; see {log}")
        return {"ok": True, "audit": publish(stage, output, symbol, as_of)}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "log": str(log)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of")
    parser.add_argument("--symbols", nargs="+")
    parser.add_argument(
        "--output", type=Path, default=Path(str(Path(__file__).resolve().parents[1] / "data/etf_rotation_v1"))
    )
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--resolve-date", action="store_true")
    args = parser.parse_args()
    if args.resolve_date:
        from data.downloaders.etf_rotation_backfill import tushare_client, fetch

        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        end = now.date() if now.hour >= 18 else now.date() - timedelta(days=1)
        cal = fetch(
            tushare_client(),
            "trade_cal",
            exchange="SSE",
            is_open="1",
            start_date=(end - timedelta(days=40)).strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
        )
        print(datetime.strptime(str(cal.cal_date.max()), "%Y%m%d").strftime("%Y-%m-%d"))
        return 0
    if args.output.name != "etf_rotation_v1":
        raise ValueError("ETF scheduler requires dedicated etf_rotation_v1 root")
    from data.downloaders.asset_boundary import assert_asset_root

    assert_asset_root(args.output, "fund")
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / ".update.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("ETF update already running")
            return 0
        as_of = (
            args.as_of
            or subprocess.run(
                [sys.executable, __file__, "--resolve-date"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=60,
                check=True,
            )
            .stdout.strip()
            .splitlines()[-1]
        )
        configuration = json.loads((ROOT / "config/etf_rotation_universe_v1.json").read_text())
        universe = [r["ts_code"] for r in configuration["etfs"]]
        if args.symbols and not set(args.symbols) <= set(universe):
            raise ValueError("Unknown ETF symbols")
        symbols = args.symbols or universe
        result = {"as_of": as_of, "symbols": {}}
        for symbol in symbols:
            result["symbols"][symbol] = run_one(symbol, as_of, args.output, args.timeout)
            print(symbol, "OK" if result["symbols"][symbol]["ok"] else "FAILED", flush=True)
            tmp = args.output / "update_status.tmp.json"
            tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            tmp.replace(args.output / "update_status.json")
        # Publish a new aggregate manifest only after a complete successful universe run.
        # Partial/failed runs retain the historical audit and expose update_status.json.
        if set(symbols) == set(universe) and all(r["ok"] for r in result["symbols"].values()):
            import hashlib
            import pyarrow.parquet as pq

            manifest = (
                json.loads((args.output / "manifest.json").read_text())
                if (args.output / "manifest.json").exists()
                else {}
            )
            # These fields belong to the original full backfill audit. Its snapshot
            # is retained separately; they must not describe a changed universe.
            for key in (
                "cross_source_issue_count",
                "cross_source_issue_symbol_dates",
                "minute_only_days",
                "supplementary_checks",
                "verification",
                "quality_status",
            ):
                manifest.pop(key, None)
            manifest.update(
                as_of=as_of,
                config=configuration,
                universe=configuration["etfs"],
                universe_count=len(universe),
                periods=list(PERIODS),
                file_count=len(universe) * len(PERIODS),
                rows_by_period={
                    period: sum(
                        pq.ParquetFile(args.output / period / f"{s}.parquet").metadata.num_rows
                        for s in universe
                    )
                    for period in PERIODS
                },
                all_files_fresh=True,
                daily_dates_without_minutes=sum(
                    len(r["audit"]["minute_missing_daily_dates"])
                    for r in result["symbols"].values()
                ),
                minute_days_not_240=sum(
                    r["audit"]["minute_days_not_240"] for r in result["symbols"].values()
                ),
                quality_status="SEE_PER_SYMBOL_AUDITS_NOT_ZERO_ISSUE_CERTIFICATION",
                input_sha256={
                    "config/etf_rotation_universe_v1.json": hashlib.sha256(
                        (ROOT / "config/etf_rotation_universe_v1.json").read_bytes()
                    ).hexdigest()
                },
                classification_revision=configuration.get("classification_revision"),
                symbols={s: r["audit"] for s, r in result["symbols"].items()},
                failures={},
            )
            tmp = args.output / "manifest.tmp.json"
            tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
            tmp.replace(args.output / "manifest.json")
        return int(any(not row["ok"] for row in result["symbols"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
