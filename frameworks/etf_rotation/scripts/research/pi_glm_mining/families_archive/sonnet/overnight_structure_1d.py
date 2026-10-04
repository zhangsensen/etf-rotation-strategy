"""Stage-S21 family: overnight_structure_1d -- overnight/intraday tug-of-
war structure, directive 2026-09-20 round_592 (S21 stage, main
controller, pre-specified direction, parallel independent implementation
alongside pi lane's stage 22 -- NOT built by reading pi's code).

Literature anchors:
- Lou, Polk & Skouras (2019), "A Tug of War: Overnight versus Intraday
  Expected Returns", JFE -- overnight (close-to-open) and intraday
  (open-to-close) returns as economically distinct, sometimes
  offsetting return components.
- Berkman, Koch, Tuttle & Zhang (2012), "Paying Attention: Overnight
  Returns and the Persistence of Investor Sentiment", JFQA -- overnight
  return persistence and its relation to same-day intraday reversal.
- Aboody, Even-Tov, Lehavy & Trueman (2018), "Overnight Returns and
  Firm-Specific Investor Sentiment", JFQA -- overnight return skewness
  and sign persistence as sentiment proxies.
- Cliff, Cooper & Gulen (2008), "Return Differences between Trading and
  Non-Trading Hours" -- motivates comparing overnight vs. intraday
  realized-variance shares across a longer window.

Directive-compliance note: the directive's first bullet (overnight
return 20d mean) and the natural 60d analogue duplicate the
ALREADY-EXISTING atoms `daily_candle:GAP_MEAN_20` and
`daily_candle:GAP_MEAN_60` (both textually identical: 20d/60d mean of
open/prev_close - 1, confirmed exact match during S14/S18). Per the
standing "no reinventing the wheel" rule, those levels are reused
directly (not rebuilt) as inputs to this family's ratio/change atoms;
only genuinely new constructs are exposed here.

Implementation (all purely from daily OHLCV, no 1m data needed except
for the volume-adjusted atom; all "level" atoms computed as of day t
using data up to and including day t):
  on_ret_t = open_t / close_{t-1} - 1                    (overnight return)
  intraday_ret_t = close_t / open_t - 1                  (same-day intraday return)
  ON_PREM_SKEW_20    = 20d rolling skewness of on_ret
  ON_PREM_RATIO_20_60 = rolling_mean(on_ret,20) / rolling_mean(on_ret,60)
                        (using the existing GAP_MEAN_20/60 definitions,
                        recomputed here from on_ret directly for self-
                        containment, not as a new independent construct)
  ON_INTRADAY_CORR_20 = 20d rolling corr(on_ret, intraday_ret)
  ON_SIGN_STREAK_20  = 20d rolling mean of the current same-sign run
                        length of on_ret (using the prior day's sign to
                        continue/reset a streak counter)
  ON_RV_SHARE_60     = rolling_60d var(on_ret) / (rolling_60d var(on_ret)
                        + rolling_60d var(intraday_ret)) -- Yang-Zhang-
                        style overnight variance share; DIRECTIVE-FLAGGED
                        as likely near-duplicate of S9's
                        range_based_vol_1m:YZ_OVERNIGHT_SHARE_20 (a 20d
                        window, same-day-range-based estimator) -- built
                        here anyway for an atom-health cross-check, kept
                        only if it clears the 0.70 shadow threshold.
  ON_VOL_ADJ_RET_20  = on_ret_t weighted by the first 1m bar's share of
                        the day's total 1m volume (a large first-bar
                        volume share suggests the overnight information
                        is being actively traded through at the open),
                        20d rolling mean
  ON_ABS_MEAN_20     = 20d rolling mean of |on_ret| (overnight return
                        MAGNITUDE, distinct from its signed mean)
  ON_PREM_CHG_20     = rolling_mean(on_ret,20) - its value 20 trading
                        days earlier (20d change of the overnight-return
                        level, consistent with this line's *_CHG_20
                        convention)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "ON_PREM_SKEW_20",
    "ON_PREM_RATIO_20_60",
    "ON_INTRADAY_CORR_20",
    "ON_SIGN_STREAK_20",
    "ON_RV_SHARE_60",
    "ON_VOL_ADJ_RET_20",
    "ON_ABS_MEAN_20",
    "ON_PREM_CHG_20",
)


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


def _first_bar_volume_share(data_root, sym, as_of) -> pd.Series:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)
    if frame.empty:
        return pd.Series(dtype=float)
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()
    recs = []
    for date, day in frame.groupby("date", sort=True):
        vol = day["volume"].to_numpy(float)
        total = float(vol[np.isfinite(vol) & (vol > 0)].sum())
        if total <= 0 or len(vol) == 0:
            continue
        first_bar = float(vol[0]) if np.isfinite(vol[0]) else 0.0
        recs.append({"date": date, "share": first_bar / total})
    if not recs:
        return pd.Series(dtype=float)
    return pd.DataFrame(recs).set_index("date")["share"].sort_index()


def _build(panels, eligibility, data_root, config):
    close, open_ = panels["close"], panels["open"]
    prev_close = close.shift(1)
    on_ret = (open_ / prev_close - 1.0).where(prev_close > 0)
    intraday_ret = (close / open_ - 1.0).where(open_ > 0)

    dates = close.index
    symbols = list(close.columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    on_mean_20 = on_ret.rolling(20, min_periods=15).mean()
    on_mean_60 = on_ret.rolling(60, min_periods=45).mean()
    out["ON_PREM_SKEW_20"] = on_ret.rolling(20, min_periods=15).skew()
    out["ON_PREM_RATIO_20_60"] = (on_mean_20 / on_mean_60.abs()).where(on_mean_60.abs() > 1e-8)
    out["ON_INTRADAY_CORR_20"] = on_ret.rolling(20, min_periods=15).corr(intraday_ret)
    out["ON_RV_SHARE_60"] = (
        on_ret.rolling(60, min_periods=45).var()
        / (on_ret.rolling(60, min_periods=45).var() + intraday_ret.rolling(60, min_periods=45).var())
    ).where((on_ret.rolling(60, min_periods=45).var() + intraday_ret.rolling(60, min_periods=45).var()) > 0)
    out["ON_ABS_MEAN_20"] = on_ret.abs().rolling(20, min_periods=15).mean()
    out["ON_PREM_CHG_20"] = on_mean_20 - on_mean_20.shift(20)

    for sym in symbols:
        sign_flag = (on_ret[sym] > 0).to_numpy()
        neg_flag = (on_ret[sym] < 0).to_numpy()
        pos_streak = pd.Series(_run_length(sign_flag), index=dates)
        neg_streak = pd.Series(_run_length(neg_flag), index=dates)
        streak = pos_streak.where(sign_flag, -neg_streak)
        out["ON_SIGN_STREAK_20"][sym] = streak.rolling(20, min_periods=15).mean()

        vol_share = _first_bar_volume_share(data_root, sym, as_of)
        if not vol_share.empty:
            vol_share = vol_share.reindex(dates)
            weighted = on_ret[sym] * vol_share
            out["ON_VOL_ADJ_RET_20"][sym] = weighted.rolling(20, min_periods=15).mean()

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("overnight_structure_1d", "overnight_structure_1d", _build))
