"""S31 stage (round_629, main controller directive): deepen S27's
GAP_DD_CONSUMPTION_RATIO_20 mechanism -- overnight gap's absorption path
during the intraday session. New self-contained constructs, no
threshold tuning.

Literature anchors:
- Barclay & Hendershott (2003), "Price Discovery and Trading After
  Hours", RFS -- post-open price discovery speed.
- Bogousslavsky (2021), "The Cross-Section of Intraday and Overnight
  Returns", JFE -- overnight/intraday return decomposition.
- Gao, Han, Li & Zhou (2018), "Market Intraday Momentum", JFE -- first
  30-minute return as an information-rich reference point.

Implementation (per symbol, from 1m close/high/low + daily open/close
panels): for each day, prev_close = previous day's close (panel-level,
PIT-safe); gap = open/prev_close - 1.
  GAP_FILL_TIMING_20: first 1m bar index (0-based) where price crosses
    back through prev_close (low_t <= prev_close <= high_t for that
    bar), divided by (n_bars - 1); untouched days record 1.0 (never
    filled), 20d mean.
  GAP_REMAIN_10AM_20 / GAP_REMAIN_1130_20 / GAP_REMAIN_CLOSE_20:
    (price_at_time - prev_close) / (open - prev_close) evaluated at the
    first bar at/after 10:00, at the last morning-session bar (11:25-
    11:30 window, session close), and at the day's final bar; each 20d
    mean (three distinct information-content checkpoints, not window
    variants of one construct).
  GAP_DD_DIRECTION_MATCH_20: for gap-up days, 1 if the day's maximum
    drawdown (from running peak) originates at the open bar itself
    (peak index == 0, i.e. price never rallied further before
    reversing); for gap-down days, the symmetric check using the day's
    maximum run-up from a running trough (trough index == 0); 20d mean.
  GAP_SHARE_OF_RANGE_20: |open - prev_close| / (day high - day low),
    20d mean (how much of the day's total price activity the overnight
    gap itself represents).
  GAP_FILL_TIMING_CHG_20 / GAP_DD_DIRECTION_MATCH_CHG_20: 20d change of
    the two atoms judged most likely to carry distinct information (the
    ratio's timing dimension and the drawdown-origin dimension), per
    the directive's "strongest 2" instruction -- selected here by
    construction-novelty reasoning ahead of atom_health, consistent
    with prior stages' practice of pre-committing which atoms get a
    CHG variant before running the health check.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "GAP_FILL_TIMING_20",
    "GAP_REMAIN_10AM_20",
    "GAP_REMAIN_1130_20",
    "GAP_REMAIN_CLOSE_20",
    "GAP_DD_DIRECTION_MATCH_20",
    "GAP_SHARE_OF_RANGE_20",
    "GAP_FILL_TIMING_CHG_20",
    "GAP_DD_DIRECTION_MATCH_CHG_20",
)

_GAP_EPS = 1e-6


def _daily_bar_gap(day: pd.DataFrame, prev_close: float) -> dict:
    day = day.sort_values("datetime")
    close = day["close"].to_numpy(float)
    high = day["high"].to_numpy(float)
    low = day["low"].to_numpy(float)
    ts = day["datetime"]
    n = len(close)
    if n < 20 or not np.isfinite(prev_close) or prev_close <= 0:
        return {}

    open_p = float(close[0])
    gap = open_p / prev_close - 1.0

    touched = (low <= prev_close) & (high >= prev_close)
    if touched.any():
        fill_idx = int(np.argmax(touched))
        fill_timing = float(fill_idx) / float(n - 1)
    else:
        fill_timing = 1.0

    tod = ts.dt.time
    am_mask = (tod >= pd.to_datetime("10:00").time())
    remain_10am = np.nan
    if am_mask.any() and abs(gap) > _GAP_EPS:
        idx10 = int(np.argmax(am_mask.to_numpy()))
        remain_10am = float((close[idx10] - prev_close) / (open_p - prev_close))

    pm_mask = (tod >= pd.to_datetime("11:25").time()) & (tod <= pd.to_datetime("11:30").time())
    remain_1130 = np.nan
    if pm_mask.any() and abs(gap) > _GAP_EPS:
        idx_pm = np.where(pm_mask.to_numpy())[0][-1]
        remain_1130 = float((close[idx_pm] - prev_close) / (open_p - prev_close))

    remain_close = np.nan
    if abs(gap) > _GAP_EPS:
        remain_close = float((close[-1] - prev_close) / (open_p - prev_close))

    running_peak = np.maximum.accumulate(close)
    drawdown = (running_peak - close) / running_peak
    trough_idx = int(np.argmax(drawdown))
    peak_idx = int(np.argmax(close[: trough_idx + 1])) if trough_idx >= 0 else 0

    running_trough = np.minimum.accumulate(close)
    runup = (close - running_trough) / running_trough
    peak_up_idx = int(np.argmax(runup))
    trough_of_up_idx = int(np.argmin(close[: peak_up_idx + 1])) if peak_up_idx >= 0 else 0

    if gap > _GAP_EPS:
        dd_match = 1.0 if peak_idx == 0 else 0.0
    elif gap < -_GAP_EPS:
        dd_match = 1.0 if trough_of_up_idx == 0 else 0.0
    else:
        dd_match = np.nan

    day_high = float(np.max(high))
    day_low = float(np.min(low))
    day_range = day_high - day_low
    share_of_range = float(abs(open_p - prev_close) / day_range) if day_range > 0 else np.nan

    return {
        "fill_timing": fill_timing,
        "remain_10am": remain_10am,
        "remain_1130": remain_1130,
        "remain_close": remain_close,
        "dd_match": dd_match,
        "share_of_range": share_of_range,
    }


def _daily_frame(data_root, sym, as_of, close_panel: pd.Series) -> pd.DataFrame:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if frame.empty:
        return pd.DataFrame()
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()

    prev_close_map = close_panel.shift(1)

    recs = []
    for date, day in frame.groupby("date", sort=True):
        prev_c = prev_close_map.get(date, np.nan)
        stats = _daily_bar_gap(day, float(prev_c) if pd.notna(prev_c) else np.nan)
        if not stats:
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

    close_p = panels["close"]

    for sym in symbols:
        daily = _daily_frame(data_root, sym, as_of, close_p[sym])
        if daily.empty:
            continue

        fill_timing_20 = daily["fill_timing"].rolling(20, min_periods=12).mean()
        remain_10am_20 = daily["remain_10am"].rolling(20, min_periods=12).mean()
        remain_1130_20 = daily["remain_1130"].rolling(20, min_periods=12).mean()
        remain_close_20 = daily["remain_close"].rolling(20, min_periods=12).mean()
        dd_match_20 = daily["dd_match"].rolling(20, min_periods=12).mean()
        share_of_range_20 = daily["share_of_range"].rolling(20, min_periods=12).mean()

        out["GAP_FILL_TIMING_20"][sym] = fill_timing_20.reindex(dates)
        out["GAP_REMAIN_10AM_20"][sym] = remain_10am_20.reindex(dates)
        out["GAP_REMAIN_1130_20"][sym] = remain_1130_20.reindex(dates)
        out["GAP_REMAIN_CLOSE_20"][sym] = remain_close_20.reindex(dates)
        out["GAP_DD_DIRECTION_MATCH_20"][sym] = dd_match_20.reindex(dates)
        out["GAP_SHARE_OF_RANGE_20"][sym] = share_of_range_20.reindex(dates)
        out["GAP_FILL_TIMING_CHG_20"][sym] = (fill_timing_20 - fill_timing_20.shift(20)).reindex(dates)
        out["GAP_DD_DIRECTION_MATCH_CHG_20"][sym] = (dd_match_20 - dd_match_20.shift(20)).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("gap_absorption_path_1m", "gap_absorption_path_1m", _build))
