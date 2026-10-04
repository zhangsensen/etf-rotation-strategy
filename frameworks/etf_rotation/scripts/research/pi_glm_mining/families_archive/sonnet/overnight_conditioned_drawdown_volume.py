"""Stage-S36 family: overnight_conditioned_drawdown_volume -- merges this
line's two strongest mechanisms into single conditional-statistic atoms:
the volume-free "overnight direction x intraday drawdown" channel
(UE3/HB1/S27B5 left legs, audit t 2.98-3.89) and the volume-bearing
"volume extremes inside intraday drawdowns" channel (S29Q1/S33, audit t
3.4-3.9). Directive 2026-09-21 round_635 (S36 stage, main controller).
The contract forbids multi-atom product constructs, but permits a single
conditional statistic (a time-series split or a rolling correlation) as
one atom.

Literature anchors:
- Lou, Polk & Skouras (2019), "A Tug of War: Overnight versus Intraday
  Expected Returns" -- overnight and intraday returns are driven by
  distinct investor clienteles; conditioning intraday statistics on
  overnight direction is economically motivated, not an arbitrary split.
- Blume, Easley & O'Hara (1994); Campbell, Grossman & Wang (1993) --
  volume as signal quality / volume-accompanied declines predicting
  reversal (same anchors as S33's volume_extremes_in_drawdown_1m).
- Barclay & Hendershott (2003/2004) -- price discovery is time-varying
  across the trading day; conditioning by an ex-ante-observable overnight
  state is a standard time-series (not cross-sectional) split.

Implementation: this family computes NO new 1m statistics from scratch.
It imports the private per-day (pre-rolling) daily-stat builders directly
from two already-registered self-contained families and combines their
raw daily columns with new rolling conditional statistics:
  - overnight_intraday_mismatch_v1._daily_frame (S27): overnight_ret,
    underwater_frac, gap_dd_ratio (per day, before any 20d rolling).
  - volume_extremes_in_drawdown_1m._daily_frame (S33): dd_vol_excess,
    prepost_ratio (per day, before any 20d rolling).
Both already do a single 1m pass per symbol; reusing their raw daily
frames avoids a third re-read of 1m data (consistent with the 2026-09-21
00:40 efficiency directive to prefer reuse over re-derivation).

Atoms (time-series conditioning only, never cross-sectional):
  OVERNIGHT_SIGN_DDVOL_EXCESS_DIFF_20: rolling 40-day window, split days
    by sign(overnight_ret); mean(dd_vol_excess | overnight>0) -
    mean(dd_vol_excess | overnight<0). Window widened to 40 (not 20) so
    each conditional side still averages roughly 20 qualifying days,
    consistent with S30's HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20
    precedent for sign-conditioned differences.
  GAP_MAGNITUDE_UNDERWATER_SPLIT_20: rolling 20-day window, split days by
    the median of |overnight_ret|/sigma_prev (sigma_prev = std of daily
    returns over the prior 20 days, shift(1)); mean(underwater_frac |
    above-median gap magnitude) - mean(underwater_frac | below-median).
  ON_POS_TROUGH_PREPOST_RATIO_20: rolling 40-day window, mean of
    prepost_ratio restricted to days where overnight_ret > 0 only (a
    conditional level, not a difference).
  GAP_CONSUMPTION_DDVOL_CORR_20: 20-day rolling Pearson correlation
    between gap_dd_ratio and dd_vol_excess (a single statistic, not a
    product/interaction atom).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..family_provider import FamilyProvider
from ..family_registry import register_family
from .overnight_intraday_mismatch_v1 import _daily_frame as _on_daily_frame
from .volume_extremes_in_drawdown_1m import _daily_frame as _ddvol_daily_frame

ATOM_NAMES = (
    "OVERNIGHT_SIGN_DDVOL_EXCESS_DIFF_20",
    "GAP_MAGNITUDE_UNDERWATER_SPLIT_20",
    "ON_POS_TROUGH_PREPOST_RATIO_20",
    "GAP_CONSUMPTION_DDVOL_CORR_20",
)

_SIGN_SPLIT_WINDOW = 40
_MEDIAN_SPLIT_WINDOW = 20
_COND_MEAN_WINDOW = 40
_CORR_WINDOW = 20


def _rolling_sign_split_diff(level: pd.Series, target: pd.Series, window: int) -> pd.Series:
    df = pd.concat({"level": level, "target": target}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    lv = df["level"].to_numpy(float)
    tg = df["target"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        lv_w = lv[start : i + 1]
        tg_w = tg[start : i + 1]
        pos = tg_w[lv_w > 0]
        neg = tg_w[lv_w < 0]
        if len(pos) < 5 or len(neg) < 5:
            continue
        out.iloc[i] = float(np.mean(pos) - np.mean(neg))
    return out


def _rolling_median_split_diff(level: pd.Series, target: pd.Series, window: int) -> pd.Series:
    df = pd.concat({"level": level, "target": target}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    lv = df["level"].to_numpy(float)
    tg = df["target"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        lv_w = lv[start : i + 1]
        tg_w = tg[start : i + 1]
        med = np.median(lv_w)
        upper = tg_w[lv_w >= med]
        lower = tg_w[lv_w < med]
        if len(upper) == 0 or len(lower) == 0:
            continue
        out.iloc[i] = float(np.mean(upper) - np.mean(lower))
    return out


def _rolling_conditional_mean_positive(level: pd.Series, target: pd.Series, window: int) -> pd.Series:
    df = pd.concat({"level": level, "target": target}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    lv = df["level"].to_numpy(float)
    tg = df["target"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        lv_w = lv[start : i + 1]
        tg_w = tg[start : i + 1]
        pos = tg_w[lv_w > 0]
        if len(pos) < 5:
            continue
        out.iloc[i] = float(np.mean(pos))
    return out


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    close_p = panels["close"]
    open_p = panels["open"]
    daily_ret = close_p.pct_change()
    sigma_all = daily_ret.rolling(20, min_periods=15).std().shift(1)

    for sym in symbols:
        on_daily = _on_daily_frame(data_root, sym, as_of, close_p[sym], open_p[sym])
        ddvol_daily = _ddvol_daily_frame(data_root, sym, as_of)
        if on_daily.empty or ddvol_daily.empty:
            continue

        merged = on_daily[["overnight_ret", "underwater_frac", "gap_dd_ratio"]].join(
            ddvol_daily[["dd_vol_excess", "prepost_ratio"]], how="inner"
        )
        if merged.empty:
            continue

        sign_diff = _rolling_sign_split_diff(
            merged["overnight_ret"], merged["dd_vol_excess"], _SIGN_SPLIT_WINDOW
        )
        out["OVERNIGHT_SIGN_DDVOL_EXCESS_DIFF_20"][sym] = sign_diff.reindex(dates)

        gap_magnitude = (merged["overnight_ret"].abs() / sigma_all[sym].reindex(merged.index)).where(
            sigma_all[sym].reindex(merged.index) > 0
        )
        magnitude_diff = _rolling_median_split_diff(
            gap_magnitude, merged["underwater_frac"], _MEDIAN_SPLIT_WINDOW
        )
        out["GAP_MAGNITUDE_UNDERWATER_SPLIT_20"][sym] = magnitude_diff.reindex(dates)

        on_pos_prepost = _rolling_conditional_mean_positive(
            merged["overnight_ret"], merged["prepost_ratio"], _COND_MEAN_WINDOW
        )
        out["ON_POS_TROUGH_PREPOST_RATIO_20"][sym] = on_pos_prepost.reindex(dates)

        gap_ddvol_corr = merged["gap_dd_ratio"].rolling(_CORR_WINDOW, min_periods=12).corr(
            merged["dd_vol_excess"]
        )
        out["GAP_CONSUMPTION_DDVOL_CORR_20"][sym] = gap_ddvol_corr.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("overnight_conditioned_drawdown_volume", "overnight_conditioned_drawdown_volume", _build))
