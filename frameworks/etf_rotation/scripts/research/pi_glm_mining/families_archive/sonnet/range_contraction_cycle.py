"""Stage-S19 family: range_contraction_cycle -- daily true-range
contraction/expansion cycle structure, directive 2026-09-20 round_583
(S19 stage, main controller, pre-specified direction, parallel
independent implementation alongside pi lane's stage 32 -- NOT built by
reading pi's code).

Literature anchors:
- Crabel (1990), "Day Trading with Short Term Price Patterns and
  Opening Range Breakout" -- NR4/NR7 (narrowest true range of the last
  4/7 days) as a volatility-contraction precursor to a directional
  breakout.
- Bollinger (2001), "Bollinger on Bollinger Bands" -- band-width
  ("the squeeze") as a volatility-cycle indicator; a low percentile
  band-width historically precedes a range expansion.
- Parkinson (1980), "The Extreme Value Method for Estimating the
  Variance of the Rate of Return" -- range-based volatility estimation,
  reused here for the daily true-range series itself.
- Taylor (1986), "Modelling Financial Time Series" -- range/volatility
  series persistence as a distinct dimension from return persistence.

Directive-specific note: the directive's 5th bullet ("区间序列 1 阶自相关，20 日")
duplicates an ALREADY-EXISTING atom, `range_memory:RANGE_ACF1_20`
(lag-1 autocorrelation of (H-L)/prev_close over a rolling 20d window,
see `etf_range_memory_factor_space.py`) -- rebuilding an equivalent
construct under a new name would violate this line's standing "no
reinventing the wheel" rule. It is dropped from this family (reused
as-is via the pre-existing atom instead, available as a right-leg
partner in later pairing rounds) and replaced with a genuinely new 8th
construct, `CONTRACTION_DEPTH_60`, measuring how tight the CURRENT
20-day contraction floor is relative to the trailing 60-day range
distribution -- a continuous complement to the binary NR7 flag.

Implementation (all purely from daily OHLC, no 1m data needed; all
"level" atoms computed as of day t using data up to and including day
t, consistent with this line's existing convention -- no future
information enters any atom, and the label's T+1-open entry means no
leakage into tradable signal):
  TR_t = max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|)          (Wilder true range)
  TRUE_RANGE_RATIO_20   = TR_t / rolling_mean(TR, 20)_t
  LOW_RANGE_STREAK_20   = current run length of TR_t < rolling_median(TR, 20)_t
  NR7_FLAG_FREQ_20      = 20d mean of 1{TR_t == min(TR_{t-6..t})}
  DAYS_SINCE_NR7_20     = bars since the most recent NR7 flag (capped at 60)
  BB_WIDTH_PCTL_120     = 120d percentile rank of BB_WIDTH_t = 4*std(close,20)/mean(close,20)
  BB_WIDTH_CHG_20       = BB_WIDTH_t - BB_WIDTH_{t-20}
  CONTRACTION_DEPTH_60  = fraction of the trailing 60d TR values that are
                          >= the current rolling-20d minimum TR (higher
                          = today's contraction floor is unusually deep
                          relative to the last 60 days)
  BREAKOUT_DIR_CONSIST_20 = 20d mean, over "breakout days" only
                            (TR_t > 1.5*TR_{t-1} AND TR_{t-1} <
                            rolling_median(TR,20)_{t-1}, i.e. expansion
                            immediately following a contracted state),
                            of 1{sign(r_t) == sign(mean(r, trailing 5d
                            ending at t-1))} -- does the breakout day's
                            direction agree with the pre-existing
                            short trend, never using information beyond
                            day t.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "TRUE_RANGE_RATIO_20",
    "LOW_RANGE_STREAK_20",
    "NR7_FLAG_FREQ_20",
    "DAYS_SINCE_NR7_20",
    "BB_WIDTH_PCTL_120",
    "BB_WIDTH_CHG_20",
    "CONTRACTION_DEPTH_60",
    "BREAKOUT_DIR_CONSIST_20",
)

_DAYS_SINCE_CAP = 60


def _run_length(flag: np.ndarray) -> np.ndarray:
    out = np.zeros(len(flag), dtype=float)
    run = 0
    for i, f in enumerate(flag):
        if f:
            run += 1
        else:
            run = 0
        out[i] = run
    return out


def _bars_since(flag: np.ndarray, cap: int) -> np.ndarray:
    out = np.full(len(flag), float(cap))
    last = -1
    for i, f in enumerate(flag):
        if f:
            last = i
        out[i] = float(min(i - last, cap)) if last >= 0 else float(cap)
    return out


def _build(panels, eligibility, data_root, config):
    high, low, close = panels["high"], panels["low"], panels["close"]
    prev_close = close.shift(1)
    # elementwise max across three same-shape DataFrames (Wilder true range)
    tr = np.maximum(np.maximum((high - low).abs(), (high - prev_close).abs()), (low - prev_close).abs())

    ret = close.pct_change(fill_method=None)
    dates = close.index
    symbols = list(close.columns)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    for sym in symbols:
        tr_s = tr[sym]
        close_s = close[sym]
        ret_s = ret[sym]
        if tr_s.notna().sum() < 30:
            continue

        tr_mean20 = tr_s.rolling(20, min_periods=15).mean()
        out["TRUE_RANGE_RATIO_20"][sym] = (tr_s / tr_mean20).reindex(dates)

        tr_median20 = tr_s.rolling(20, min_periods=15).median()
        low_flag = (tr_s < tr_median20).to_numpy()
        out["LOW_RANGE_STREAK_20"][sym] = pd.Series(_run_length(low_flag), index=dates)

        nr7 = (tr_s <= tr_s.rolling(7, min_periods=7).min() + 1e-12).astype(float)
        nr7 = nr7.where(tr_s.rolling(7, min_periods=7).min().notna())
        out["NR7_FLAG_FREQ_20"][sym] = nr7.rolling(20, min_periods=12).mean().reindex(dates)

        nr7_flag = nr7.fillna(0).to_numpy().astype(bool)
        out["DAYS_SINCE_NR7_20"][sym] = pd.Series(
            _bars_since(nr7_flag, _DAYS_SINCE_CAP), index=dates
        )

        bb_std20 = close_s.rolling(20, min_periods=15).std()
        bb_mean20 = close_s.rolling(20, min_periods=15).mean()
        bb_width = (4.0 * bb_std20 / bb_mean20).where(bb_mean20 > 0)
        bb_pctl = bb_width.rolling(120, min_periods=60).apply(
            lambda x: float((x[-1] >= x).mean()), raw=True
        )
        out["BB_WIDTH_PCTL_120"][sym] = bb_pctl.reindex(dates)
        out["BB_WIDTH_CHG_20"][sym] = (bb_width - bb_width.shift(20)).reindex(dates)

        min20_tr = tr_s.rolling(20, min_periods=15).min()
        tr_vals = tr_s.to_numpy()
        min20_vals = min20_tr.to_numpy()
        depth = np.full(len(tr_vals), np.nan)
        for i in range(len(tr_vals)):
            if i < 59 or not np.isfinite(min20_vals[i]):
                continue
            window = tr_vals[i - 59 : i + 1]
            finite = window[np.isfinite(window)]
            if finite.size < 30:
                continue
            depth[i] = float((finite >= min20_vals[i]).mean())
        out["CONTRACTION_DEPTH_60"][sym] = pd.Series(depth, index=tr_s.index).reindex(dates)

        breakout = (tr_s > 1.5 * tr_s.shift(1)) & (tr_s.shift(1) < tr_median20.shift(1))
        prior5_mean_ret = ret_s.shift(1).rolling(5, min_periods=4).mean()
        consist = pd.Series(np.nan, index=dates)
        same_sign = np.sign(ret_s) == np.sign(prior5_mean_ret)
        consist = same_sign.astype(float).where(breakout & ret_s.notna() & prior5_mean_ret.notna())
        out["BREAKOUT_DIR_CONSIST_20"][sym] = consist.rolling(20, min_periods=6).mean().reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("range_contraction_cycle", "range_contraction_cycle", _build))
