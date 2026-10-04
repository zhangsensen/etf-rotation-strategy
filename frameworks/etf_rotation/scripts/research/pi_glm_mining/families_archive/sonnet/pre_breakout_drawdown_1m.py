"""Stage-S35 family: pre_breakout_drawdown_1m -- mechanism atom, directive
2026-09-21 round_634 (S35 stage, main controller). Motivated by pi line
stage 34's DB09 (FP_UP_20 - RP_UW_CHG_20, audit +31.9bp/t2.06), the only
first-passage-time construct that survived pairing: "how much drawdown
does price endure before it breaks out upward". This family writes that
mechanism directly as a single-leg atom rather than a two-atom spread.

Literature anchors:
- Karatzas & Shreve, "Brownian Motion and Stochastic Calculus" -- first
  passage time of a random walk to a level as a path-dependent statistic.
- Magdon-Ismail & Atiya (2004), "Maximum Drawdown" -- drawdown depth
  along a finite path, applied here only to the PRE-breakout segment of
  the day rather than the whole day.
- Grossman & Zhou (1993), "Optimal Investment Strategies for Controlling
  Drawdowns" -- underwater-time framing, applied to the same pre-breakout
  segment.
- Bogousslavsky (2021), "The Cross-Section of Intraday and Overnight
  Returns" -- intraday path shape (not just the terminal return) carries
  distinct information from the day's net return.

Implementation (practitioner proxy, sigma-calibrated, no fixed absolute
threshold, consistent with this line's first_passage_times_1m /
intraday_drawdown_1m conventions): for day D, sigma_prev is the std of
daily close-to-close returns over the 20 trading days strictly BEFORE D
(rolling(20).std().shift(1)). Within day D's 1m path, normalized excess
return r_t = close_1..t / open_D - 1:
  up_idx = first bar index where r_t >= sigma_prev (else n_bars - 1,
    i.e. the whole day is the "pre-breakout" segment)
  pre segment = bars [0 .. up_idx] inclusive (the touch bar itself is
    included: drawdown endured UP TO AND INCLUDING the moment of
    breakout)
  pre_maxdd_sigma = max((running_peak - price)/running_peak) over the
    pre segment, normalized by sigma_prev (dimensionless: how many sigma
    of pain relative to the sigma used to define the breakout itself)
  pre_underwater_frac = fraction of bars in the pre segment with
    drawdown_t > 0
  down_idx = first bar index where r_t <= -sigma_prev (NaN/excluded that
    day if never touched)
  post_trough_recovery: only when down_idx exists -- touch_price =
    price[down_idx]; post segment = bars [down_idx .. end]; low_after =
    min(post segment); recovery = (close - low_after) / (touch_price -
    low_after); excluded (NaN) when touch_price == low_after (denominator
    zero, i.e. price never went lower than the touch bar after touching
    -sigma)
All daily statistics are rolled to a 20-day mean (or 20-day change for
the first two), never using same-day-or-later information beyond the day
itself; sigma_prev itself uses only strictly prior days.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "PRE_BREAKOUT_MAXDD_SIGMA_20",
    "PRE_BREAKOUT_UNDERWATER_FRAC_20",
    "POST_TROUGH_RECOVERY_20",
    "PRE_BREAKOUT_MAXDD_SIGMA_CHG_20",
    "PRE_BREAKOUT_UNDERWATER_FRAC_CHG_20",
)


def _daily_stats(prices: np.ndarray, sigma: float) -> dict:
    n = len(prices)
    if n < 5 or not np.isfinite(sigma) or sigma <= 0:
        return {}
    open_px = prices[0]
    if open_px <= 0:
        return {}
    r = prices / open_px - 1.0

    up_hits = np.flatnonzero(r >= sigma)
    up_idx = int(up_hits[0]) if up_hits.size else n - 1

    pre = prices[: up_idx + 1]
    running_peak = np.maximum.accumulate(pre)
    drawdown = (running_peak - pre) / running_peak
    pre_maxdd_sigma = float(np.max(drawdown)) / sigma
    pre_underwater_frac = float(np.mean(drawdown > 0))

    down_hits = np.flatnonzero(r <= -sigma)
    recovery = np.nan
    if down_hits.size:
        down_idx = int(down_hits[0])
        touch_price = prices[down_idx]
        post = prices[down_idx:]
        low_after = float(np.min(post))
        close_px = float(prices[-1])
        denom = touch_price - low_after
        if denom > 0:
            recovery = (close_px - low_after) / denom

    return {
        "pre_maxdd_sigma": pre_maxdd_sigma,
        "pre_underwater_frac": pre_underwater_frac,
        "post_trough_recovery": recovery,
    }


def _daily_frame(data_root, sym, as_of, sigma_by_date: pd.Series) -> pd.DataFrame:
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
        stats = _daily_stats(prices, float(sigma))
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
        daily = _daily_frame(data_root, sym, as_of, sigma_by_date)
        if daily.empty:
            continue

        maxdd_20 = daily["pre_maxdd_sigma"].rolling(20, min_periods=12).mean()
        uwf_20 = daily["pre_underwater_frac"].rolling(20, min_periods=12).mean()
        recovery_20 = daily["post_trough_recovery"].rolling(20, min_periods=4).mean()

        out["PRE_BREAKOUT_MAXDD_SIGMA_20"][sym] = maxdd_20.reindex(dates)
        out["PRE_BREAKOUT_UNDERWATER_FRAC_20"][sym] = uwf_20.reindex(dates)
        out["POST_TROUGH_RECOVERY_20"][sym] = recovery_20.reindex(dates)
        out["PRE_BREAKOUT_MAXDD_SIGMA_CHG_20"][sym] = (maxdd_20 - maxdd_20.shift(20)).reindex(dates)
        out["PRE_BREAKOUT_UNDERWATER_FRAC_CHG_20"][sym] = (uwf_20 - uwf_20.shift(20)).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("pre_breakout_drawdown_1m", "pre_breakout_drawdown_1m", _build))
