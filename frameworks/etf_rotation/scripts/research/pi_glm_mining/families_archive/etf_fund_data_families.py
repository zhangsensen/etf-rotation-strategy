"""Primary-market data families (directive 5): fund_flow (Tushare fund_share)
and nav_premium (Tushare NAV). PIT alignment is exclusively
usable_from_date <= D (stable-sort duplicates by usable_from_date, keep
last = corrections). No trade_date/nav_date direct alignment is allowed."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..family_provider import FamilyProvider
from ..family_registry import register_family

_DATE_COLS = ("trade_date", "nav_date")


def _pit_series(data_root: Path, sub: str, sym: str, as_of, value_col: str) -> pd.Series:
    path = data_root / sub / f"{sym}.parquet"
    if not path.exists():
        return pd.Series(dtype=float)
    frame = pd.read_parquet(path)
    if frame.empty:
        return pd.Series(dtype=float)
    usable = pd.to_datetime(frame["usable_from_date"])
    frame = frame.loc[usable <= pd.Timestamp(as_of)].copy()
    if frame.empty:
        return pd.Series(dtype=float)
    frame["_u"] = usable.loc[frame.index]
    date_col = next((c for c in _DATE_COLS if c in frame.columns), None)
    if date_col is None:
        return pd.Series(dtype=float)
    frame = frame.sort_values(["_u"], kind="stable").drop_duplicates(date_col, keep="last")
    idx = pd.to_datetime(frame[date_col])
    vals = pd.to_numeric(frame[value_col], errors="coerce")
    series = pd.Series(vals.to_numpy(float), index=idx)
    return series[series.notna()].sort_index()


def _build_fund_flow(panels, eligibility, data_root, config):
    close = panels["close"]
    amount = panels["amount"]
    dates = close.index
    as_of = dates.max()
    root = Path(data_root)
    out = {
        name: pd.DataFrame(np.nan, index=dates, columns=close.columns)
        for name in (
            "SHARE_CHG_5",
            "SHARE_CHG_20",
            "SHARE_Z_60",
            "STREAK_DAYS",
            "SHARE_RET_CORR_20",
            "PRIMARY_SHARE_20",
        )
    }
    for sym in close.columns:
        shares = _pit_series(root, "fund_share", sym, as_of, "fund_shares")
        if shares.empty:
            shares = _pit_series(root, "fund_share", sym, as_of, "fd_share")
        if shares.empty:
            continue
        # reindex onto the daily calendar without forward-filling beyond facts:
        # shares only move on disclosure days, so ffill is the PIT-safe carrier
        s = shares.reindex(dates).ffill()
        chg1 = s.pct_change()
        out["SHARE_CHG_5"][sym] = s.pct_change(5)
        out["SHARE_CHG_20"][sym] = s.pct_change(20)
        mu = s.rolling(60, min_periods=30).mean()
        sd = s.rolling(60, min_periods=30).std()
        out["SHARE_Z_60"][sym] = (s - mu) / sd
        # signed consecutive-days streak of same-direction share change
        streak = pd.Series(np.nan, index=dates)
        run = 0
        prev_sign = 0
        arr = chg1.to_numpy(float)
        for i, v in enumerate(arr):
            if not np.isfinite(v) or v == 0:
                run = 0
                prev_sign = 0
                continue
            sign = 1 if v > 0 else -1
            run = run + 1 if sign == prev_sign else 1
            prev_sign = sign
            streak.iloc[i] = float(run * sign)
        out["STREAK_DAYS"][sym] = streak
        ret = close[sym].pct_change()
        out["SHARE_RET_CORR_20"][sym] = chg1.rolling(20, min_periods=10).corr(ret)
        primary = (chg1.abs() * s * close[sym]) / amount[sym].replace(0, np.nan)
        out["PRIMARY_SHARE_20"][sym] = primary.rolling(20, min_periods=10).mean()
    return out


def _build_nav_premium(panels, eligibility, data_root, config):
    close = panels["close"]
    dates = close.index
    as_of = dates.max()
    root = Path(data_root)
    out = {
        name: pd.DataFrame(np.nan, index=dates, columns=close.columns)
        for name in (
            "PREMIUM",
            "PREMIUM_Z_20",
            "PREMIUM_CHG_5",
            "PREM_SHARE_ALIGNED_20",
        )
    }
    for sym in close.columns:
        nav = _pit_series(root, "nav", sym, as_of, "unit_nav")
        shares = _pit_series(root, "fund_share", sym, as_of, "fund_shares")
        if shares.empty:
            shares = _pit_series(root, "fund_share", sym, as_of, "fd_share")
        premium = pd.Series(np.nan, index=dates)
        if not nav.empty:
            nav_d = nav.reindex(dates).ffill()
            with np.errstate(all="ignore"):
                premium = close[sym] / nav_d - 1.0
            premium = premium.replace([np.inf, -np.inf], np.nan)
        out["PREMIUM"][sym] = premium
        mu = premium.rolling(20, min_periods=10).mean()
        sd = premium.rolling(20, min_periods=10).std()
        out["PREMIUM_Z_20"][sym] = (premium - mu) / sd
        out["PREMIUM_CHG_5"][sym] = premium - premium.shift(5)
        if not shares.empty:
            chg1 = shares.reindex(dates).ffill().pct_change()
            align = np.sign(premium) * np.sign(chg1)
            out["PREM_SHARE_ALIGNED_20"][sym] = align.rolling(20, min_periods=10).mean()
    return out


register_family(FamilyProvider("fund_flow", "fund_flow", _build_fund_flow))
register_family(FamilyProvider("nav_premium", "nav_premium", _build_nav_premium))
