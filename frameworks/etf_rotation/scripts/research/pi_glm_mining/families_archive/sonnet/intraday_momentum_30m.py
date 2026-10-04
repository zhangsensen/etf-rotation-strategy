"""Stage-18 family: intraday_momentum_30m -- market intraday momentum,
directive 2026-09-20 round_513 (S3 stage, main controller).

Literature anchor:
- Gao, Han, Li & Zhou (2018), "Market Intraday Momentum", Journal of
  Financial Economics 129(2) -- the return of the first half-hour of
  trading reliably predicts the return of the last half-hour of the same
  day; the relationship is a rolling correlation/regression across days,
  not a same-day level or spread (already covered separately by
  intraday_return_path's FIRST_HOUR_RET/LAST_HOUR_RET/
  MORNING_AFTERNOON_SPREAD).

round_513 GAP_SCAN_2 found the local 30m bar frequency
(data/etf_rotation_v1/30m) is used by zero of the 66 existing families;
this family is the first to use it, with the first and last 30m bar of
each trading day giving a clean half-hour-return proxy without needing
sub-bar aggregation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "INTRADAY_MOM_CORR_20",
    "INTRADAY_MOM_CORR_60",
    "INTRADAY_MOM_BETA_20",
    "OVERNIGHT_FIRST30_CORR_20",
    "LAST30_NEXTOPEN_CORR_20",
)


def _daily_session_returns(data_root, sym, frequency, as_of) -> pd.DataFrame:
    """Per-day overnight / first-30min / last-30min returns from 30m bars."""
    try:
        frame, _ = _read_complete_days(data_root, sym, frequency, as_of)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if frame.empty:
        return pd.DataFrame()
    frame = frame.copy()
    frame["date"] = frame["datetime"].dt.normalize()
    recs = []
    prev_close = np.nan
    for date, day in frame.groupby("date", sort=True):
        day = day.sort_values("datetime")
        opens = day["open"].to_numpy(float)
        closes = day["close"].to_numpy(float)
        if len(opens) < 2 or not np.isfinite(opens[0]) or opens[0] <= 0:
            prev_close = closes[-1] if len(closes) and np.isfinite(closes[-1]) else prev_close
            continue
        first30 = closes[0] / opens[0] - 1.0 if opens[0] > 0 else np.nan
        last30 = closes[-1] / opens[-1] - 1.0 if opens[-1] > 0 else np.nan
        overnight = opens[0] / prev_close - 1.0 if (prev_close and prev_close > 0) else np.nan
        recs.append({"date": date, "overnight": overnight, "first30": first30, "last30": last30})
        prev_close = closes[-1] if np.isfinite(closes[-1]) else prev_close
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _rolling_beta(y: pd.Series, x: pd.Series, window: int, min_periods: int) -> pd.Series:
    cov = y.rolling(window, min_periods=min_periods).cov(x)
    var = x.rolling(window, min_periods=min_periods).var()
    return (cov / var.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)


def _build(panels, eligibility, data_root, config):
    frequency = str(config.get("frequency", "30m"))
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}
    for sym in symbols:
        sess = _daily_session_returns(data_root, sym, frequency, as_of)
        if sess.empty:
            continue
        overnight = sess["overnight"]
        first30 = sess["first30"]
        last30 = sess["last30"]
        # last30(t-1) paired with overnight(t): both known by close(t), unlike
        # pairing last30(t) with overnight(t+1) which would need tomorrow's
        # open at signal date t (future leak). Shifting last30 forward keeps
        # every pair inside the window available as of the signal date.
        lagged_last30 = last30.shift(1)

        corr20 = first30.rolling(20, min_periods=12).corr(last30)
        corr60 = first30.rolling(60, min_periods=36).corr(last30)
        beta20 = _rolling_beta(last30, first30, 20, 12)
        on_first_corr20 = overnight.rolling(20, min_periods=12).corr(first30)
        last_nexton_corr20 = overnight.rolling(20, min_periods=12).corr(lagged_last30)

        out["INTRADAY_MOM_CORR_20"][sym] = corr20.reindex(dates)
        out["INTRADAY_MOM_CORR_60"][sym] = corr60.reindex(dates)
        out["INTRADAY_MOM_BETA_20"][sym] = beta20.reindex(dates)
        out["OVERNIGHT_FIRST30_CORR_20"][sym] = on_first_corr20.reindex(dates)
        out["LAST30_NEXTOPEN_CORR_20"][sym] = last_nexton_corr20.reindex(dates)
    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("intraday_momentum_30m", "intraday_momentum_30m", _build))
