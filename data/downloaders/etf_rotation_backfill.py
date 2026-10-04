"""Backfill the explicit rotation universe from TuShare daily and CMES raw 1m.

No live-account operations. Raw prices, volume in shares, turnover in CNY.
Minute timestamps are bar ends; resampling never crosses the lunch break.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

PRICE = ["open", "high", "low", "close"]
RENAME = {
    "时间": "datetime",
    "开盘价": "open",
    "最高价": "high",
    "最低价": "low",
    "收盘价": "close",
    "成交量": "volume",
    "成交额": "turnover",
}


def save(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.parquet")
    frame.to_parquet(tmp, index=False)
    tmp.replace(path)


def archive_is_current(path, year, as_of):
    """An in-progress vendor year must not become a permanent stale cache."""
    receipt = path.with_suffix(path.suffix + ".receipt.json")
    if not path.exists() or not receipt.exists():
        return False
    stamp = pd.Timestamp(json.loads(receipt.read_text())["downloaded_at_utc"])
    last_required_day = min(pd.Timestamp(f"{year}-12-31"), pd.Timestamp(as_of))
    required_after = (last_required_day + pd.Timedelta(hours=16, minutes=30)).tz_localize(
        "Asia/Shanghai"
    )
    return stamp >= required_after


def validate(frame, key):
    if frame.empty or frame[key].isna().any() or frame[key].duplicated().any():
        raise ValueError("empty, null or duplicated timestamps")
    x = frame[PRICE + ["volume", "turnover"]]
    if not np.isfinite(x.to_numpy(dtype=float)).all():
        raise ValueError("non-finite market values")
    if (x[PRICE] <= 0).any().any() or (x[["volume", "turnover"]] < 0).any().any():
        raise ValueError("invalid prices or negative activity")
    if (
        (x.high < x[["open", "close", "low"]].max(axis=1) - 1e-8)
        | (x.low > x[["open", "close", "high"]].min(axis=1) + 1e-8)
    ).any():
        raise ValueError("invalid OHLC range")


def clean_activity_roundoff(frame):
    """Record and clamp sub-yuan negative amount only on zero-volume bars."""
    x = frame.copy()
    mask = x.volume.eq(0) & x.turnover.between(-1, 0, inclusive="left")
    corrections = x.loc[mask].copy()
    x.loc[mask, "turnover"] = 0.0
    return x, corrections


def resample(frame, minutes):
    """Only publish full constituent-count bars, with explicit lunch anchors."""
    t = frame.datetime
    mod = t.dt.hour * 60 + t.dt.minute
    morning = mod.between(571, 690)
    afternoon = mod.between(781, 900)
    x = frame.loc[morning | afternoon].copy()
    off = np.where(morning.loc[x.index], mod.loc[x.index] - 570, mod.loc[x.index] - 780)
    anchor = np.where(morning.loc[x.index], 570, 780)
    x["bucket"] = x.datetime.dt.normalize() + pd.to_timedelta(
        anchor + ((off - 1) // minutes + 1) * minutes, unit="m"
    )
    out = x.groupby("bucket", sort=True).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        turnover=("turnover", "sum"),
        constituent_count=("datetime", "size"),
    )
    out = (
        out.loc[out.constituent_count.eq(minutes)]
        .reset_index()
        .rename(columns={"bucket": "datetime"})
    )
    out["ts_code"] = frame.ts_code.iloc[0]
    out["price_basis"] = "unadjusted"
    out["source"] = "resampled_cmes_1m"
    return out


def read_minutes(path, symbol, end):
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError("expected one CSV per symbol/year")
        code, exchange = symbol.split(".")
        if Path(names[0]).stem.upper() != f"{exchange}.{code}":
            raise ValueError("vendor ZIP member does not match requested symbol")
        x = pd.read_csv(io.BytesIO(z.read(names[0])), encoding="utf-8-sig").rename(columns=RENAME)
    x = x[["datetime", *PRICE, "volume", "turnover"]].copy()
    x["datetime"] = pd.to_datetime(x.datetime)
    if not x.datetime.dt.year.eq(int(path.parent.name)).all():
        raise ValueError("vendor timestamps do not match requested archive year")
    x = x.loc[x.datetime < pd.Timestamp(end) + pd.Timedelta(days=1)]
    x["ts_code"] = symbol
    x["source"] = "cmes_a_etf_1min"
    x["price_basis"] = "unadjusted"
    return x.sort_values("datetime").reset_index(drop=True)


def tushare_client():
    import tushare as ts

    from data.downloaders.credentials import tushare_token

    TUSHARE_TOKEN = tushare_token()
    return ts.pro_api(TUSHARE_TOKEN)


def fetch(pro, method, **kwargs):
    for attempt in range(3):
        try:
            return getattr(pro, method)(**kwargs)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2**attempt)


def daily(pro, symbol, listed, end, root):
    raw_parts, adj_parts = [], []
    for year in range(int(listed[:4]), int(end[:4]) + 1, 4):
        start = max(listed, f"{year}0101")
        stop = min(end.replace("-", ""), f"{year + 3}1231")
        for api, parts in [("fund_daily", raw_parts), ("fund_adj", adj_parts)]:
            path = root / "sources" / "tushare" / api / f"{symbol}_{start}_{stop}.parquet"
            if path.exists():
                part = pd.read_parquet(path)
            else:
                part = fetch(pro, api, ts_code=symbol, start_date=start, end_date=stop)
                if not part.empty:
                    save(part, path)
                time.sleep(0.15)
            if not part.empty:
                parts.append(part)
    raw = (
        pd.concat(raw_parts, ignore_index=True)
        .drop_duplicates("trade_date")
        .sort_values("trade_date")
    )
    out = raw.rename(columns={"vol": "volume", "amount": "turnover"}).copy()
    out["trade_date"] = pd.to_datetime(out.trade_date, format="%Y%m%d")
    out["volume"] *= 100.0
    out["turnover"] *= 1000.0
    out["price_basis"] = "unadjusted"
    out["source"] = "tushare_fund_daily"
    out = out[["ts_code", "trade_date", *PRICE, "volume", "turnover", "price_basis", "source"]]
    validate(out, "trade_date")
    save(out, root / "1d" / f"{symbol}.parquet")
    if adj_parts:
        adj = (
            pd.concat(adj_parts, ignore_index=True)
            .drop_duplicates("trade_date")
            .sort_values("trade_date")
        )
        adj["trade_date"] = pd.to_datetime(adj.trade_date, format="%Y%m%d")
        save(adj, root / "adj_factor" / f"{symbol}.parquet")
        q = out.merge(
            adj[["trade_date", "adj_factor"]], on="trade_date", how="left", validate="one_to_one"
        )
        if q.adj_factor.notna().all() and q.adj_factor.gt(0).all():
            ratio = q.adj_factor / q.adj_factor.iloc[-1]
            q[PRICE] = q[PRICE].mul(ratio, axis=0)
            q["price_basis"] = "qfq_asof_" + end
            save(q, root / "1d_qfq" / f"{symbol}.parquet")
    return out


def audit(day, minute, sessions):
    x = minute.assign(trade_date=minute.datetime.dt.normalize())
    agg = x.groupby("trade_date").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        turnover=("turnover", "sum"),
        bars=("datetime", "size"),
    )
    merged = day.merge(agg, on="trade_date", suffixes=("_daily", "_minute"))
    for c in PRICE + ["volume", "turnover"]:
        merged[c + "_relative_error"] = (
            merged[c + "_minute"] - merged[c + "_daily"]
        ).abs() / merged[c + "_daily"].abs().clip(lower=1e-9)
    minute_dates = pd.DatetimeIndex(agg.index)
    expected = sessions[(sessions >= day.trade_date.min()) & (sessions <= day.trade_date.max())]
    report = {
        "daily_rows": len(day),
        "daily_first": str(day.trade_date.min()),
        "daily_latest": str(day.trade_date.max()),
        "minute_rows": len(minute),
        "minute_first": str(minute.datetime.min()),
        "minute_latest": str(minute.datetime.max()),
        "daily_missing_sessions": [str(s.date()) for s in expected.difference(day.trade_date)],
        "minute_missing_daily_dates": [
            str(s.date()) for s in pd.DatetimeIndex(day.trade_date).difference(minute_dates)
        ],
        "minute_days_not_240": int(agg.bars.ne(240).sum()),
        "matched_days": len(merged),
        "close_mismatch_days": int(merged.close_relative_error.gt(0.002).sum()),
        "ohlc_mismatch_days": int(
            merged[[c + "_relative_error" for c in PRICE]].gt(0.002).any(axis=1).sum()
        ),
        "volume_mismatch_days": int(merged.volume_relative_error.gt(0.01).sum()),
        "turnover_mismatch_days": int(merged.turnover_relative_error.gt(0.01).sum()),
    }
    report["status"] = (
        "PASS"
        if not any(
            [
                report["daily_missing_sessions"],
                report["minute_missing_daily_dates"],
                report["minute_days_not_240"],
                report["ohlc_mismatch_days"],
                report["volume_mismatch_days"],
                report["turnover_mismatch_days"],
            ]
        )
        else "GAPS_OR_MISMATCHES"
    )
    return report, merged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/etf_rotation_universe_v1.json"))
    parser.add_argument(
        "--output", type=Path, default=Path(str(Path(__file__).resolve().parents[2] / "data/etf_rotation_v1"))
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("/home/sensen/data_vendor/cmes/archive/etf_rotation_v1"),
    )
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--symbols", nargs="*")
    parser.add_argument("--report-name", default="manifest.json")
    args = parser.parse_args()
    from data.downloaders.asset_boundary import assert_asset_root, is_fund_code

    root = args.output.resolve()
    assert_asset_root(root, "fund")
    universe = json.loads(args.config.read_text())["etfs"]
    if any(not is_fund_code(row["ts_code"]) for row in universe):
        raise ValueError("ETF configuration contains a non-fund code")
    if args.symbols:
        if not set(args.symbols) <= {r["ts_code"] for r in universe}:
            raise ValueError("Unknown ETF symbols")
        universe = [r for r in universe if r["ts_code"] in args.symbols]
    if not universe:
        raise ValueError("Empty ETF universe")
    from data.downloaders.cmes_archive import _load_cmes_stock_modules
    from data.downloaders.cmes_archive import _download

    _, history = _load_cmes_stock_modules()
    token = Path("/home/sensen/.config/cmesdata/token").read_text().strip()
    root.mkdir(parents=True, exist_ok=True)
    pro = tushare_client()
    basic_path = root / "metadata" / "fund_basic.parquet"
    basic = (
        pd.read_parquet(basic_path)
        if basic_path.exists()
        else fetch(pro, "fund_basic", market="E", fields="ts_code,name,list_date,delist_date")
    )
    if not basic_path.exists():
        save(basic, basic_path)
    cal_path = root / "metadata" / ("trade_calendar_" + args.as_of + ".parquet")
    cal = (
        pd.read_parquet(cal_path)
        if cal_path.exists()
        else fetch(
            pro,
            "trade_cal",
            exchange="SSE",
            start_date="20000101",
            end_date=args.as_of.replace("-", ""),
            is_open="1",
        )
    )
    if not cal_path.exists():
        save(cal, cal_path)
    sessions = pd.DatetimeIndex(pd.to_datetime(cal.cal_date, format="%Y%m%d")).sort_values()
    if pd.Timestamp(args.as_of) not in sessions:
        raise ValueError("as-of must be an open session")
    manifest = {
        "as_of": args.as_of,
        "price_basis": "unadjusted",
        "volume_unit": "shares",
        "turnover_unit": "CNY",
        "minute_timestamp": "Asia/Shanghai, bar end",
        "universe": universe,
        "symbols": {},
        "failures": {},
        "command": "python -m data.downloaders.etf_rotation_backfill --as-of " + args.as_of,
    }
    for row in universe:
        symbol = row["ts_code"]
        print("START", symbol, flush=True)
        try:
            match = basic.loc[basic.ts_code.eq(symbol)]
            listed = str(match.list_date.iloc[0]) if len(match) else "20050101"
            if len(listed) != 8 or not listed.isdigit():
                listed = "20050101"
            day = daily(pro, symbol, listed, args.as_of, root)
            print(
                "DAILY",
                symbol,
                len(day),
                str(day.trade_date.min()),
                str(day.trade_date.max()),
                flush=True,
            )
            parts = []
            errors = []
            code, exchange = symbol.split(".")
            for year in range(day.trade_date.min().year, int(args.as_of[:4]) + 1):
                dest = args.archive / "a_etf_1min" / str(year) / f"{exchange}.{code}.zip"
                if not archive_is_current(dest, year, args.as_of):
                    result = _download(
                        history,
                        {"symbol": "a_etf_1min", "name": f"{exchange}.{code}", "folder": str(year)},
                        dest,
                        token,
                        1,
                        1,
                        60,
                    )
                    if not result["completed"]:
                        errors.append({"year": year, "error": result["error"]})
                        print("MINUTE_MISSING", symbol, year, result["error"], flush=True)
                        continue
                part = read_minutes(dest, symbol, args.as_of)
                if not part.empty:
                    parts.append(part)
                print("MINUTE_YEAR", symbol, year, len(part), flush=True)
            if not parts:
                raise ValueError("no minute history")
            minute = (
                pd.concat(parts, ignore_index=True).sort_values("datetime").reset_index(drop=True)
            )
            minute_of_day = minute.datetime.dt.hour * 60 + minute.datetime.dt.minute
            regular = minute_of_day.between(571, 690) | minute_of_day.between(781, 900)
            off_session = minute.loc[~regular].copy()
            save(off_session, root / "qa" / f"{symbol}_off_session.parquet")
            minute = minute.loc[regular].reset_index(drop=True)
            minute, roundoff = clean_activity_roundoff(minute)
            save(roundoff, root / "qa" / f"{symbol}_turnover_roundoff.parquet")
            validate(minute, "datetime")
            save(minute, root / "1m" / f"{symbol}.parquet")
            for size in [5, 15, 30, 60]:
                bars = resample(minute, size)
                validate(bars, "datetime")
                save(bars, root / f"{size}m" / f"{symbol}.parquet")
            report, comparison = audit(day, minute, sessions)
            report["download_errors"] = errors
            report["off_session_rows_quarantined"] = len(off_session)
            report["zero_volume_sub_yuan_turnover_corrections"] = len(roundoff)
            report["listing_date"] = listed
            report["daily_fresh"] = day.trade_date.max() == pd.Timestamp(args.as_of)
            report["minute_fresh"] = minute.datetime.max() == pd.Timestamp(args.as_of + " 15:00:00")
            if not report["daily_fresh"] or not report["minute_fresh"]:
                report["status"] = "STALE"
            save(comparison, root / "qa" / f"{symbol}_daily_comparison.parquet")
            manifest["symbols"][symbol] = report
            print("DONE", symbol, json.dumps(report, ensure_ascii=False), flush=True)
        except Exception as exc:
            manifest["failures"][symbol] = str(exc).replace(token, "[REDACTED]")[:500]
            print("FAILED", symbol, manifest["failures"][symbol], flush=True)
        destination = root / args.report_name
        tmp = destination.with_suffix(".tmp.json")
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        tmp.replace(destination)
    print("COMPLETE", len(manifest["symbols"]), "failed", len(manifest["failures"]), flush=True)
    return 1 if manifest["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
