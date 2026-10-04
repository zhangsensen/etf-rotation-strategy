"""Read the maintained ETF store without changing it or filling missing sessions.

This is an explicit new-data adapter, not a replacement for the legacy loader.
Adjusted OHLC are research views; actual execution prices remain unadjusted.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd


@contextmanager
def _read_lock(root: Path):
    lock_path = root / ".update.lock"
    # The production updater retains this file. Offline fixtures need no lock.
    if not lock_path.exists():
        yield
        return
    with lock_path.open("r") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("ETF update in progress; retry after publication") from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def load_canonical_daily(
    data_root: str | Path,
    universe_path: str | Path,
    *,
    as_of: str,
    roles: tuple[str, ...] | None = None,
    allow_future_only_symbols: bool = False,
) -> dict[str, pd.DataFrame]:
    """Return adjusted research OHLCV matrices with exchange-qualified columns.

    Only rows through as_of enter the view or adjustment denominator. No
    reclassification is inferred: current roles describe today's research pool,
    not historical point-in-time membership. All selected files must reach as_of.
    With allow_future_only_symbols, files whose entire history starts after the
    cutoff contribute empty columns (not invented prices or inception claims).
    """
    root = Path(data_root)
    cutoff = pd.Timestamp(as_of)
    if pd.isna(cutoff) or cutoff.tzinfo is not None or cutoff != cutoff.normalize():
        raise ValueError("as_of must be a timezone-naive trading date")
    universe = json.loads(Path(universe_path).read_text())["etfs"]
    if roles is not None and not set(roles) <= {r["role"] for r in universe}:
        raise ValueError("Unknown universe role")
    symbols = [r["ts_code"] for r in universe if roles is None or r["role"] in roles]
    if not symbols or len(symbols) != len(set(symbols)):
        raise ValueError("Selected universe must be nonempty and unique")
    fields = ("open", "high", "low", "close", "volume", "amount")
    panels: dict[str, dict[str, pd.Series]] = {name: {} for name in fields}
    with _read_lock(root):
        for symbol in symbols:
            if not re.fullmatch(r"(?:5\d{5}\.SH|1[568]\d{4}\.SZ)", symbol):
                raise ValueError(f"Invalid fund symbol: {symbol}")
            daily = pd.read_parquet(root / "1d" / f"{symbol}.parquet",
                                    filters=[("trade_date", "<=", cutoff)])
            adj = pd.read_parquet(root / "adj_factor" / f"{symbol}.parquet",
                                  filters=[("trade_date", "<=", cutoff)])
            for frame in (daily, adj):
                if not frame.ts_code.eq(symbol).all():
                    raise ValueError(f"Symbol mismatch: {symbol}")
                frame["trade_date"] = pd.to_datetime(frame.trade_date)
                if frame.trade_date.isna().any() or frame.trade_date.duplicated().any():
                    raise ValueError(f"Invalid or duplicate dates: {symbol}")
            daily = daily.set_index("trade_date").sort_index()
            future_only = False
            if daily.empty and allow_future_only_symbols:
                dates = pd.read_parquet(root / "1d" / f"{symbol}.parquet", columns=["trade_date"])
                future_only = not dates.empty and pd.to_datetime(dates.trade_date).min() > cutoff
            daily = daily.loc[:cutoff]
            adj = adj.set_index("trade_date").sort_index().loc[:cutoff]
            if daily.empty and future_only and allow_future_only_symbols:
                for field in fields:
                    panels[field][symbol] = pd.Series(dtype=float, index=pd.DatetimeIndex([], name='trade_date'))
                continue
            if daily.empty or daily.index[-1] != cutoff:
                raise ValueError(f"Daily data does not reach as_of: {symbol}")
            if not daily.price_basis.eq("unadjusted").all():
                raise ValueError(f"Expected unadjusted daily prices: {symbol}")
            prices = daily[["open", "high", "low", "close"]]
            amounts = daily[["volume", "turnover"]]
            if (not np.isfinite(prices.to_numpy()).all() or (prices <= 0).any().any()
                    or not np.isfinite(amounts.to_numpy()).all() or (amounts < 0).any().any()
                    or (daily.high < prices.max(axis=1)).any()
                    or (daily.low > prices.min(axis=1)).any()):
                raise ValueError(f"Invalid OHLCV: {symbol}")
            factors = adj.adj_factor.reindex(daily.index)
            if not np.isfinite(factors).all() or (factors <= 0).any():
                raise ValueError(f"Missing or invalid adjustment factors: {symbol}")
            scale = factors / factors.iloc[-1]
            for field in fields:
                source = "turnover" if field == "amount" else field
                series = daily[source]
                if field in ("open", "high", "low", "close"):
                    series = series * scale
                panels[field][symbol] = series
    return {field: pd.DataFrame(values).sort_index() for field, values in panels.items()}


def reference_factors(prices: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Exercise migrated formulas; restore missing-window masks at the boundary.

    These are unvalidated research factors, not trade recommendations. Masking
    prevents legacy price-position's 0.5 fallback from inventing prelisting data.
    """
    from etf_strategy.core.precise_factor_library_v2 import PreciseFactorLibrary

    library = PreciseFactorLibrary()
    close, high, low = (prices[k] for k in ("close", "high", "low"))
    valid = close.notna() & high.notna() & low.notna()
    position = library._price_position_batch(close, high, low, window=120)
    position = position.where(valid.rolling(120, min_periods=120).sum().eq(120))
    breakout = pd.DataFrame({s: library.breakout_20d(high[s], close[s]) for s in close})
    breakout = breakout.where(valid & valid.shift(1).rolling(20, min_periods=20).sum().eq(20))
    return {"PRICE_POSITION_120D": position, "BREAKOUT_20D": breakout}
