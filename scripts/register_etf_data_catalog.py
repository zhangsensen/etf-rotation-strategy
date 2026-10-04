"""Register isolated ETF assets in the existing local DuckDB inventory (not certification)."""

from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import duckdb
import pyarrow.parquet as pq


def inspect(path):
    files = sorted(path.rglob("*.parquet"))
    fields, starts, ends = {}, [], []
    count = size = 0
    for file in files:
        pf = pq.ParquetFile(file)
        count += pf.metadata.num_rows
        size += file.stat().st_size
        for field in pf.schema_arrow:
            fields.setdefault(field.name, set()).add(str(field.type))
        names = pf.schema_arrow.names
        key = next((k for k in ("trade_date", "datetime") if k in names), None)
        if key:
            index = names.index(key)
            for i in range(pf.metadata.num_row_groups):
                stat = pf.metadata.row_group(i).column(index).statistics
                if stat and stat.has_min_max:
                    starts.append(str(stat.min))
                    ends.append(str(stat.max))
    return len(files), count, size, min(starts, default=None), max(ends, default=None), fields


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--database", type=Path, required=True)
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()
    stamp = datetime.now(timezone.utc)
    periods = ("1d", "1d_qfq", "adj_factor", "1m", "5m", "15m", "30m", "60m")
    records = []
    for period in periods:
        path = a.data_root / "etf_rotation_v1" / period
        provider = "TuShare" if period in ("1d", "1d_qfq", "adj_factor") else "CMES"
        records.append(
            (
                f"etf_rotation_v1_{period}",
                path,
                period,
                provider,
                "independent ETF maintenance; cross-source QA flags unresolved",
                "PRESENT_WITH_QA_FLAGS",
            )
        )
    records.append(
        (
            "etf_qmt_legacy",
            a.data_root / "etf_qmt_legacy",
            "mixed",
            "legacy_QMT_TuShare",
            "preserved historical fund files; not an active update source",
            "ARCHIVE",
        )
    )
    prepared = [(record, inspect(record[1])) for record in records]
    if not a.apply:
        print([(record[0], stats[:5]) for record, stats in prepared])
        return
    # Opening read-only first verifies there is no incompatible writer before backup.
    with duckdb.connect(str(a.database), read_only=True) as c:
        c.execute("select count(*) from assets").fetchone()
    backup = a.database.with_name(
        a.database.name + ".before_etf_" + stamp.strftime("%Y%m%dT%H%M%S") + ".bak"
    )
    shutil.copy2(a.database, backup)
    with duckdb.connect(str(a.database)) as c:
        c.execute("begin transaction")
        try:
            for record, stats in prepared:
                asset_id, path, period, provider, role, status = record
                nfiles, nrows, nbytes, start, end, fields = stats
                c.execute(
                    "insert or replace into assets values (" + ",".join(["?"] * 17) + ")",
                    [
                        asset_id,
                        provider,
                        "ETF / fund market data",
                        "isolated_etf",
                        period,
                        "configured_20"
                        if asset_id != "etf_qmt_legacy"
                        else "historical_migrated_funds",
                        role,
                        "bar_end; adjustment_asof_for_qfq",
                        str(path),
                        "parquet",
                        nfiles,
                        nrows,
                        nbytes,
                        start,
                        end,
                        status,
                        stamp,
                    ],
                )
                c.execute("delete from asset_fields where asset_id=?", [asset_id])
                c.executemany(
                    "insert into asset_fields values (?,?,?)",
                    [(asset_id, name, " | ".join(sorted(types))) for name, types in fields.items()],
                )
            for name in ("tech_etf_ts", "intraday_etf", "t0_etf"):
                c.execute(
                    "update assets set role=?, physical_status=?, updated_at=? where asset_id=?",
                    [
                        "legacy ETF tree; not the active rotation update source",
                        "LEGACY_PRESENT",
                        stamp,
                        name,
                    ],
                )
                c.execute(
                    "update asset_decisions set reason=?, next_action=?, decided_at=? where asset_id=?",
                    [
                        "Legacy research tree; ETF maintenance moved to etf_rotation_v1",
                        "retain history; do not assume fresh; audit consumer before reuse",
                        stamp,
                        name,
                    ],
                )
            c.execute("commit")
        except Exception:
            c.execute("rollback")
            raise
        print(
            "registered_assets",
            len(prepared),
            "fields",
            c.execute(
                "select count(*) from asset_fields where asset_id like 'etf_rotation_v1_%' or asset_id='etf_qmt_legacy'"
            ).fetchone()[0],
        )
    print("backup", backup)


if __name__ == "__main__":
    main()
