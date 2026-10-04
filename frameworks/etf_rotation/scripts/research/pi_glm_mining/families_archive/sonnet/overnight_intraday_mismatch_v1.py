"""Stage-S27 family: overnight_intraday_mismatch_v1 -- deepening the
mechanism shared by S21's UE3 (+53.3bp/t3.08), S16's HB1 (+56.5bp/t2.98)
and pi's CY95 (t1.76): a mismatch between the OVERNIGHT directional
signal and the INTRADAY drawdown/recovery path, directive 2026-09-20
round_614 (S27 stage, main controller, pre-specified direction,
following S26R's closure).

Literature anchors:
- Lou, Polk & Skouras (2019), "A Tug of War: Overnight versus Intraday
  Expected Returns" -- overnight and intraday returns are driven by
  different investor clienteles/mechanisms, motivating constructs that
  explicitly relate the two rather than treating them as substitutes.
- Barclay & Hendershott (2003), "Price Discovery and Trading After
  Hours" -- overnight price discovery is often reversed or confirmed by
  the following day's intraday path.
- Bogousslavsky (2021), "The Cross-Section of Intraday and Overnight
  Returns" -- systematic overnight/intraday return patterns tied to
  investor inattention and rebalancing flows.

Unlike S16-S25's atoms (which recombine EXISTING atoms as left/right
legs), this family builds 4 NEW single-statistic atoms (+2 20d-change
variants) that directly encode the overnight-vs-intraday-drawdown
relationship as ONE number per day, rather than leaving it to a
rank_spread pairing of two separately-computed atoms:

  ON_TROUGH_RECOVERY_MATCH_20: fraction of trailing-20 days where the
    day exhibits a 'dip/pop-then-recover-toward-gap-direction' pattern:
    for a gap-up day (overnight_ret>0), the day dipped below open
    (low<open) AND closed above the midpoint of (low,open); for a
    gap-down day (overnight_ret<0), the day popped above open
    (high>open) AND closed below the midpoint of (high,open). Days with
    overnight_ret==0 or no dip/pop score 0.
  GAP_DD_CONSUMPTION_RATIO_20: |intraday max drawdown from the day's
    own open| / |overnight_ret|, clipped to [0,3] (per directive), 20d
    mean -- how much of the overnight gap gets 'eaten' by the day's own
    drawdown.
  ON_STREAK_UF_COV_20: NOT a product-of-two-atoms construct -- a single
    rolling statistic: the 20-day rolling covariance between the daily
    overnight-sign-streak series and the daily intraday-underwater-
    fraction series.
  ON_SIGN_UF_DIFF_20: within a trailing 20-day window, mean(intraday
    underwater fraction | overnight_ret>0) minus mean(intraday
    underwater fraction | overnight_ret<0); NaN if either group is
    empty in the window.
  *_CHG_20: 20-day change of ON_TROUGH_RECOVERY_MATCH_20 and
    GAP_DD_CONSUMPTION_RATIO_20 (the two most directly interpretable
    atoms, per directive's 'only do the 2 strongest').

All daily statistics use only that day's own 1m bars plus the prior
day's close (for the overnight gap); no same-day-or-later leakage."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "ON_TROUGH_RECOVERY_MATCH_20",
    "GAP_DD_CONSUMPTION_RATIO_20",
    "ON_STREAK_UF_COV_20",
    "ON_SIGN_UF_DIFF_20",
    "ON_TROUGH_RECOVERY_MATCH_CHG_20",
    "GAP_DD_CONSUMPTION_RATIO_CHG_20",
)

_RATIO_CLIP = 3.0
_GAP_EPS = 1e-6


def _daily_intraday_stats(data_root, sym, as_of) -> pd.DataFrame:
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
        prices = day["close"].to_numpy(float)
        mask = np.isfinite(prices) & (prices > 0)
        prices = prices[mask]
        n = len(prices)
        if n < 10:
            continue
        open_p = float(prices[0])
        close_p = float(prices[-1])
        low_p = float(np.min(prices))
        high_p = float(np.max(prices))

        running_peak = np.maximum.accumulate(prices)
        drawdown = (running_peak - prices) / running_peak
        max_dd = float(np.max(drawdown))
        underwater_frac = float(np.mean(drawdown > 0))

        recs.append(
            {
                "date": date,
                "open": open_p,
                "close": close_p,
                "low": low_p,
                "high": high_p,
                "max_dd": max_dd,
                "underwater_frac": underwater_frac,
            }
        )
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _trough_recovery_match(row) -> float:
    overnight = row["overnight_ret"]
    open_p, low_p, high_p, close_p = row["open"], row["low"], row["high"], row["close"]
    if not np.isfinite(overnight) or overnight == 0:
        return 0.0
    if overnight > 0:
        if low_p < open_p and close_p > (low_p + open_p) / 2.0:
            return 1.0
        return 0.0
    if high_p > open_p and close_p < (high_p + open_p) / 2.0:
        return 1.0
    return 0.0


def _sign_streak(signs: np.ndarray) -> np.ndarray:
    streak = np.zeros(len(signs))
    cur = 0.0
    prev_sign = 0.0
    for i, s in enumerate(signs):
        if s == 0:
            cur = 0.0
        elif s == prev_sign:
            cur += s
        else:
            cur = s
        streak[i] = cur
        prev_sign = s if s != 0 else prev_sign
    return streak


def _daily_frame(data_root, sym, as_of, close_panel: pd.Series, open_panel: pd.Series) -> pd.DataFrame:
    intraday = _daily_intraday_stats(data_root, sym, as_of)
    if intraday.empty:
        return pd.DataFrame()

    prev_close = close_panel.shift(1)
    overnight_ret = (open_panel / prev_close - 1.0).reindex(intraday.index)
    intraday["overnight_ret"] = overnight_ret

    intraday["trough_recovery_match"] = intraday.apply(_trough_recovery_match, axis=1)

    ratio = intraday["max_dd"] / intraday["overnight_ret"].abs()
    ratio = ratio.where(intraday["overnight_ret"].abs() > _GAP_EPS)
    intraday["gap_dd_ratio"] = ratio.clip(lower=0.0, upper=_RATIO_CLIP)

    signs = np.sign(intraday["overnight_ret"].fillna(0.0).to_numpy())
    intraday["on_sign_streak"] = _sign_streak(signs)

    return intraday


def _rolling_cov(a: pd.Series, b: pd.Series, window: int = 20, min_periods: int = 12) -> pd.Series:
    return a.rolling(window, min_periods=min_periods).cov(b)


def _rolling_conditional_diff(overnight: pd.Series, underwater: pd.Series, window: int = 20) -> pd.Series:
    pos_mask = overnight > 0
    neg_mask = overnight < 0
    pos_uf = underwater.where(pos_mask)
    neg_uf = underwater.where(neg_mask)
    pos_mean = pos_uf.rolling(window, min_periods=1).apply(lambda x: np.nanmean(x) if np.any(~np.isnan(x)) else np.nan, raw=True)
    neg_mean = neg_uf.rolling(window, min_periods=1).apply(lambda x: np.nanmean(x) if np.any(~np.isnan(x)) else np.nan, raw=True)
    diff = pos_mean - neg_mean
    n_valid = overnight.rolling(window, min_periods=12).count()
    return diff.where(n_valid >= 12)


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    close_p = panels["close"]
    open_p = panels["open"]

    for sym in symbols:
        daily = _daily_frame(data_root, sym, as_of, close_p[sym], open_p[sym])
        if daily.empty:
            continue

        match_20 = daily["trough_recovery_match"].rolling(20, min_periods=12).mean()
        ratio_20 = daily["gap_dd_ratio"].rolling(20, min_periods=12).mean()
        cov_20 = _rolling_cov(daily["on_sign_streak"], daily["underwater_frac"])
        diff_20 = _rolling_conditional_diff(daily["overnight_ret"], daily["underwater_frac"])

        out["ON_TROUGH_RECOVERY_MATCH_20"][sym] = match_20.reindex(dates)
        out["GAP_DD_CONSUMPTION_RATIO_20"][sym] = ratio_20.reindex(dates)
        out["ON_STREAK_UF_COV_20"][sym] = cov_20.reindex(dates)
        out["ON_SIGN_UF_DIFF_20"][sym] = diff_20.reindex(dates)
        out["ON_TROUGH_RECOVERY_MATCH_CHG_20"][sym] = (match_20 - match_20.shift(20)).reindex(dates)
        out["GAP_DD_CONSUMPTION_RATIO_CHG_20"][sym] = (ratio_20 - ratio_20.shift(20)).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("overnight_intraday_mismatch_v1", "overnight_intraday_mismatch_v1", _build))
