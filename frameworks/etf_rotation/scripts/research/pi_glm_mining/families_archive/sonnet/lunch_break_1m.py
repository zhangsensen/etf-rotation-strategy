"""Stage-S22 family: lunch_break_1m -- A-share midday-recess structure
(the 90-minute halt between the 11:30 morning close and the 13:00
afternoon open), directive 2026-09-20 round_596 (S22 stage, main
controller, pre-specified direction, parallel independent implementation
alongside pi lane's stage 18, its densest stage -- NOT built by reading
pi's code).

Literature anchors:
- Barclay & Hendershott (2003, 2004), "Price Discovery and Trading
  After Hours" / "Order Consolidation, Price Efficiency, and Extreme
  Liquidity Shocks" -- price discovery around trading halts; the
  post-halt open re-aggregates information accumulated during the halt.
- Hong & Wang (2000), "Trading and Returns under Periodic Market
  Closures", JF -- periodic closures (including intraday lunch breaks in
  markets that have them) systematically affect the volatility and
  return pattern immediately before/after the closure.
- A-share microstructure literature on the lunch recess (11:30-13:00)
  documents pre-recess "position parking" volume spikes and post-recess
  gap/continuation patterns distinct from the overnight (close-to-open)
  gap already studied in S21.

Directive-compliance note: two of the directive's bullets duplicate
ALREADY-EXISTING atoms and are reused rather than rebuilt: "11:20-11:30
成交量占全日比例" is exactly `pi_lunch_prerun_1m:LUNCH_PRE_RUN_20`
(built in S14/round_569); "上午 vs 下午成交量占比之差" is a redundant
linear transform of the pre-existing
`intraday_volatility_structure:MORNING_VOL_SHARE`/`AFTERNOON_VOL_SHARE`
pair (which sum to 1, so their difference carries no information the
existing atoms don't already expose) -- reused/skipped, not rebuilt.
This family instead exposes the genuinely new midday-recess-specific
constructs the existing atoms do NOT cover.

Implementation (session boundaries: morning 09:30-11:30, afternoon
13:00-15:00, both from local 1m bar timestamps; all "level" atoms
computed as of day t using data up to and including day t):
  LUNCH_GAP_20        = 20d mean of (first PM 1m bar's open / last AM 1m
                         bar's close - 1)  (the midday-recess gap,
                         distinct from the overnight close-to-open gap)
  LUNCH_GAP_ABS_20    = 20d mean of |lunch gap|  (magnitude dimension)
  LUNCH_GAP_CHG_20    = 20d change of LUNCH_GAP_20
  LUNCH_GAP_FILL_15M_20 = on days with a non-trivial gap, 1{price
                         retraces to the last-AM-close level within the
                         first 15 minutes of the PM session}, 20d mean
                         (days with |gap| below a small floor are
                         excluded, consistent with S17/S19's
                         conditional-observation convention)
  AM_PM_RV_RATIO_20   = 20d mean of (morning-session RV / afternoon-
                         session RV), both realized variance of 1m
                         log returns within each session
  LUNCH_POST_RUN_20   = 20d mean of the day's 13:00-13:10 1m volume
                         share of total day volume (symmetric to the
                         pre-existing LUNCH_PRE_RUN_20's 11:20-11:30
                         window, but for the post-recess side)
  LUNCH_PRERUN_POSTRUN_RATIO_20 = 20d mean of (11:20-11:30 volume share
                         / 13:00-13:10 volume share) -- anticipation
                         (pre-recess) vs continuation (post-recess)
                         volume concentration; the pre-run leg is
                         recomputed internally here (not the exposed
                         S14 atom) purely as a same-day input to this
                         ratio, not a duplicate independent atom
  AM_PM_RET_CORR_20   = 20d rolling correlation between the day's
                         morning session return and afternoon session
                         return (distinct from the pre-existing same-
                         day MORNING_AFTERNOON_SPREAD level -- this is
                         a cross-day PERSISTENCE measure, not a same-
                         day spread)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "LUNCH_GAP_20",
    "LUNCH_GAP_ABS_20",
    "LUNCH_GAP_CHG_20",
    "LUNCH_GAP_FILL_15M_20",
    "AM_PM_RV_RATIO_20",
    "LUNCH_POST_RUN_20",
    "LUNCH_PRERUN_POSTRUN_RATIO_20",
    "AM_PM_RET_CORR_20",
)

_GAP_FLOOR = 1e-4


def _day_lunch_stats(day: pd.DataFrame) -> dict | None:
    ts = pd.to_datetime(day["datetime"])
    minutes = ts.dt.hour * 60 + ts.dt.minute
    morning = day[(minutes >= 9 * 60 + 30) & (minutes <= 11 * 60 + 30)]
    afternoon = day[(minutes >= 13 * 60) & (minutes <= 15 * 60)]
    if len(morning) < 30 or len(afternoon) < 30:
        return None

    am_close = float(morning["close"].to_numpy(float)[-1])
    pm_open = float(afternoon["open"].to_numpy(float)[0])
    if am_close <= 0 or pm_open <= 0:
        return None
    gap = pm_open / am_close - 1.0

    am_close_ret = morning["close"].pct_change().to_numpy(float)
    pm_close_ret = afternoon["close"].pct_change().to_numpy(float)
    am_rv = float(np.nansum(am_close_ret[np.isfinite(am_close_ret)] ** 2))
    pm_rv = float(np.nansum(pm_close_ret[np.isfinite(pm_close_ret)] ** 2))

    am_open = float(morning["open"].to_numpy(float)[0])
    pm_close = float(afternoon["close"].to_numpy(float)[-1])
    am_ret = am_close / am_open - 1.0 if am_open > 0 else np.nan
    pm_ret = pm_close / pm_open - 1.0 if pm_open > 0 else np.nan

    pm_minutes = minutes[afternoon.index]
    first15 = afternoon[pm_minutes <= 13 * 60 + 15]
    fill = np.nan
    if abs(gap) >= _GAP_FLOOR and len(first15) > 0:
        low15 = float(first15["low"].to_numpy(float).min())
        high15 = float(first15["high"].to_numpy(float).max())
        fill = 1.0 if (low15 <= am_close <= high15) else 0.0

    total_vol = float(day["volume"].to_numpy(float)[np.isfinite(day["volume"].to_numpy(float)) & (day["volume"].to_numpy(float) > 0)].sum())
    prerun_mask = (minutes >= 11 * 60 + 20) & (minutes <= 11 * 60 + 30)
    postrun_mask = (minutes >= 13 * 60) & (minutes <= 13 * 60 + 10)
    prerun_vol = float(day.loc[prerun_mask, "volume"].to_numpy(float).sum())
    postrun_vol = float(day.loc[postrun_mask, "volume"].to_numpy(float).sum())
    prerun_share = prerun_vol / total_vol if total_vol > 0 else np.nan
    postrun_share = postrun_vol / total_vol if total_vol > 0 else np.nan
    ratio = prerun_share / postrun_share if postrun_share and postrun_share > 1e-9 else np.nan

    return {
        "gap": gap,
        "am_rv": am_rv,
        "pm_rv": pm_rv,
        "am_ret": am_ret,
        "pm_ret": pm_ret,
        "fill": fill,
        "postrun_share": postrun_share,
        "prerun_postrun_ratio": ratio,
    }


def _daily_lunch_frame(data_root, sym, as_of) -> pd.DataFrame:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if frame.empty:
        return pd.DataFrame()
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()

    recs = []
    for date, day in frame.groupby("date", sort=True):
        stats = _day_lunch_stats(day)
        if stats is None:
            continue
        stats["date"] = date
        recs.append(stats)
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    for sym in symbols:
        daily = _daily_lunch_frame(data_root, sym, as_of)
        if daily.empty:
            continue

        gap_20 = daily["gap"].rolling(20, min_periods=15).mean()
        out["LUNCH_GAP_20"][sym] = gap_20.reindex(dates)
        out["LUNCH_GAP_ABS_20"][sym] = daily["gap"].abs().rolling(20, min_periods=15).mean().reindex(dates)
        out["LUNCH_GAP_CHG_20"][sym] = (gap_20 - gap_20.shift(20)).reindex(dates)
        out["LUNCH_GAP_FILL_15M_20"][sym] = daily["fill"].rolling(20, min_periods=8).mean().reindex(dates)

        rv_ratio = (daily["am_rv"] / daily["pm_rv"].where(daily["pm_rv"] > 1e-12))
        out["AM_PM_RV_RATIO_20"][sym] = rv_ratio.rolling(20, min_periods=15).mean().reindex(dates)

        out["LUNCH_POST_RUN_20"][sym] = daily["postrun_share"].rolling(20, min_periods=15).mean().reindex(dates)
        out["LUNCH_PRERUN_POSTRUN_RATIO_20"][sym] = (
            daily["prerun_postrun_ratio"].rolling(20, min_periods=12).mean().reindex(dates)
        )
        out["AM_PM_RET_CORR_20"][sym] = (
            daily["am_ret"].rolling(20, min_periods=15).corr(daily["pm_ret"]).reindex(dates)
        )

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("lunch_break_1m", "lunch_break_1m", _build))
