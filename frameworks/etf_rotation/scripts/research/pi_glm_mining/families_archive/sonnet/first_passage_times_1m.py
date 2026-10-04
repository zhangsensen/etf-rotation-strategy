"""Stage-S17 family: first_passage_times_1m -- intraday first-passage-time
structure of the 1m price path, directive 2026-09-20 round_577 (S17 stage,
main controller, pre-specified direction, sigma-calibrated / no fixed
threshold).

Literature anchors:
- Zumbach (2007), "The Prediction Performance of Directional-Change ...",
  and Guillaume et al. (1997), "From the bird's eye to the microscope" --
  directional-change / threshold-crossing event time as an alternative
  intraday clock to calendar time; a fixed-threshold sequence of upturn
  and downturn events replaces the usual fixed-time-step sampling.
- Cont (2001), "Empirical properties of asset returns: stylized facts and
  statistical issues" -- motivates threshold calibration from the asset's
  own recent volatility rather than an arbitrary constant.
- Karatzas & Shreve, "Brownian Motion and Stochastic Calculus" -- first
  passage time of a random walk to a level is a canonical path-dependent
  statistic distinct from the level's terminal value.
- Bollerslev & Todorov (2011), "Tails, Fears, and Risk Premia" -- extreme
  first-passage / jump-arrival timing as a volatility-risk-distinct
  channel from realized-variance-based measures.

Implementation (practitioner proxy, consistent with this line's existing
1m conventions, no fixed absolute threshold): for each day D, sigma_prev
is the standard deviation of DAILY close-to-close returns over the 20
trading days strictly BEFORE D (rolling(20).std() then shift(1), so day
D's own return never enters its own sigma). Within day D's 1m path,
normalized excess return r_t = close_1..t / open_D - 1 is compared
against +/- sigma_prev:
  up_idx    = first bar index where r_t >= sigma_prev (else n_bars)
  down_idx  = first bar index where r_t <= -sigma_prev (else n_bars)
  up_first  = 1.0 if up_idx < down_idx, 0.0 if down_idx < up_idx, NaN if
              neither threshold was ever touched that day
  half_idx  = first bar index where |r_t| >= 0.5*sigma_prev (either
              direction; else day excluded from false-break stat)
  false_break = 1.0 if, after half_idx, r_t crosses back through 0 before
              day end (price returns to the open); 0.0 otherwise
  crossing_count = number of directional-change events using threshold
              sigma_prev on r_t (Zumbach/Guillaume-style alternating
              up-turn/down-turn detector: track a running extreme in the
              current direction; a reversal of >= sigma_prev from that
              extreme registers one crossing and flips direction)
All daily statistics are rolled to a 20-day mean (or 20-day change for
the two first-passage atoms), never using same-day-or-later information
beyond the day itself; sigma_prev itself uses only strictly prior days.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "FIRST_PASSAGE_UP_20",
    "FIRST_PASSAGE_DOWN_20",
    "PASSAGE_ASYM_20",
    "UP_FIRST_FRAC_20",
    "FALSE_BREAK_RATE_20",
    "SIGMA_CROSSING_COUNT_20",
    "FIRST_PASSAGE_UP_CHG_20",
    "FIRST_PASSAGE_DOWN_CHG_20",
)


def _daily_passage_stats(prices: np.ndarray, sigma: float) -> dict:
    n = len(prices)
    if n < 5 or not np.isfinite(sigma) or sigma <= 0:
        return {}
    open_px = prices[0]
    if open_px <= 0:
        return {}
    r = prices / open_px - 1.0

    up_hits = np.flatnonzero(r >= sigma)
    down_hits = np.flatnonzero(r <= -sigma)
    up_idx = int(up_hits[0]) if up_hits.size else n
    down_idx = int(down_hits[0]) if down_hits.size else n

    if up_idx < down_idx:
        up_first = 1.0
    elif down_idx < up_idx:
        up_first = 0.0
    else:
        up_first = np.nan

    half = 0.5 * sigma
    half_hits = np.flatnonzero(np.abs(r) >= half)
    if half_hits.size:
        half_idx = int(half_hits[0])
        broke_up = r[half_idx] > 0
        rest = r[half_idx + 1:]
        if rest.size == 0:
            false_break = 0.0
        elif broke_up:
            false_break = 1.0 if np.any(rest <= 0.0) else 0.0
        else:
            false_break = 1.0 if np.any(rest >= 0.0) else 0.0
    else:
        false_break = np.nan

    crossing_count = 0
    direction = 0
    extreme = r[0]
    for t in range(1, n):
        rt = r[t]
        if direction >= 0:
            if rt > extreme:
                extreme = rt
            elif extreme - rt >= sigma:
                crossing_count += 1
                direction = -1
                extreme = rt
                continue
        if direction <= 0:
            if rt < extreme:
                extreme = rt
            elif rt - extreme >= sigma:
                crossing_count += 1
                direction = 1
                extreme = rt

    return {
        "up_idx": float(up_idx),
        "down_idx": float(down_idx),
        "up_first": up_first,
        "false_break": false_break,
        "crossing_count": float(crossing_count),
    }


def _daily_passage_frame(data_root, sym, as_of, sigma_by_date: pd.Series) -> pd.DataFrame:
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
        sigma = sigma_by_date.get(date, np.nan)
        if not np.isfinite(sigma) or sigma <= 0:
            continue
        prices = day["close"].to_numpy(float)
        prices = prices[np.isfinite(prices) & (prices > 0)]
        stats = _daily_passage_stats(prices, float(sigma))
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

    daily_ret = panels["close"].pct_change()
    sigma_all = daily_ret.rolling(20, min_periods=15).std().shift(1)

    for sym in symbols:
        sigma_by_date = sigma_all[sym]
        daily = _daily_passage_frame(data_root, sym, as_of, sigma_by_date)
        if daily.empty:
            continue

        up_20 = daily["up_idx"].rolling(20, min_periods=12).mean()
        down_20 = daily["down_idx"].rolling(20, min_periods=12).mean()
        up_first_20 = daily["up_first"].rolling(20, min_periods=8).mean()
        false_break_20 = daily["false_break"].rolling(20, min_periods=8).mean()
        crossing_20 = daily["crossing_count"].rolling(20, min_periods=12).mean()
        passage_asym_20 = down_20 - up_20

        out["FIRST_PASSAGE_UP_20"][sym] = up_20.reindex(dates)
        out["FIRST_PASSAGE_DOWN_20"][sym] = down_20.reindex(dates)
        out["PASSAGE_ASYM_20"][sym] = passage_asym_20.reindex(dates)
        out["UP_FIRST_FRAC_20"][sym] = up_first_20.reindex(dates)
        out["FALSE_BREAK_RATE_20"][sym] = false_break_20.reindex(dates)
        out["SIGMA_CROSSING_COUNT_20"][sym] = crossing_20.reindex(dates)
        out["FIRST_PASSAGE_UP_CHG_20"][sym] = (up_20 - up_20.shift(20)).reindex(dates)
        out["FIRST_PASSAGE_DOWN_CHG_20"][sym] = (down_20 - down_20.shift(20)).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("first_passage_times_1m", "first_passage_times_1m", _build))
