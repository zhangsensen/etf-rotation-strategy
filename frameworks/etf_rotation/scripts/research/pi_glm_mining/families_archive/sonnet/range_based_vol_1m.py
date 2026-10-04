"""Stage-S9 family: range_based_vol_1m -- OHLC range-based volatility
estimators vs close-to-close realized variance, directive 2026-09-20
round_553 (S9 stage, main controller, pre-specified direction).

Literature anchors:
- Parkinson (1980), "The Extreme Value Method for Estimating the
  Variance of the Rate of Return", JoB -- high-low range estimator,
  (1/(4 ln2)) * ln(H/L)^2, more efficient than close-to-close RV under
  continuous GBM but biased upward by intraday drift/jumps.
- Garman & Klass (1980), "On the Estimation of Security Price
  Volatilities from Historical Data", JoB -- adds the open-close term to
  Parkinson, 0.5*ln(H/L)^2 - (2ln2-1)*ln(C/O)^2, further efficiency gain.
- Rogers & Satchell (1991), "Estimating Variance From High, Low and
  Closing Prices", Ann. Appl. Prob. -- drift-independent range estimator,
  ln(H/C)*ln(H/O) + ln(L/C)*ln(L/O), unbiased under nonzero drift unlike
  Parkinson/GK.
- Yang & Zhang (2000), "Drift-Independent Volatility Estimation Based on
  High, Low, Open, and Close Prices", J. Business -- decomposes daily
  variance into overnight (close-to-open) + opening-session (open-close)
  + Rogers-Satchell components; handles both drift and the overnight jump
  that Parkinson/GK/RS all mishandle.
- Alizadeh, Brandt & Diebold (2002), "Range-Based Estimation of
  Stochastic Volatility Models", JF -- range-based estimators are far
  more efficient (lower variance) than return-based RV for a given number
  of observations, motivating the ratio-to-RV framing used here.

Implementation (practitioner proxy, consistent with this line's existing
1m conventions, e.g. etf_realized_1m_families.py's per-day-then-rolling-
mean pattern): within each trading day, using 1m OHLC bars:
  For each 1m bar i with (o_i, h_i, l_i, c_i):
    pk_i = (1/(4 ln2)) * ln(h_i/l_i)^2
    gk_i = 0.5*ln(h_i/l_i)^2 - (2 ln2 - 1)*ln(c_i/o_i)^2
    rs_i = ln(h_i/c_i)*ln(h_i/o_i) + ln(l_i/c_i)*ln(l_i/o_i)
    r_i  = ln(c_i / c_{i-1})  (c_0 := day's first bar open, PIT within day)
  Day-level: PK = sum(pk_i), GK = sum(gk_i), RS = sum(rs_i), RV = sum(r_i^2)
  Ratios (guarded RV>0): pk_ratio=PK/RV, gk_ratio=GK/RV, rs_ratio=RS/RV
  PARKINSON_RV_RATIO_20 / GK_RV_RATIO_20 / RS_RV_RATIO_20 = 20-day rolling
    mean of the corresponding daily ratio (bar-internal activity vs
    bar-to-bar activity: >1 means range info sees more variance than
    close-to-close captures, e.g. intra-bar reversals).
  GK_RV_RATIO_CHG_20 = 20-day change of GK_RV_RATIO_20 (GK chosen as the
    most literature-efficient of the three ratio estimators to track
    trend/z variants of).
  GK_RV_RATIO_Z_60 = 60-day rolling z-score of the raw daily gk_ratio
    series (same convention as etf_fund_data_families.py's SHARE_Z_60).
  WICK_SHARE_20 = 20-day rolling mean of the full-day
    (upper_wick+lower_wick)/(H-L) (bar-internal reversal strength using
    the day's aggregate O/H/L/C, not summed over 1m bars).
  YZ_OVERNIGHT_SHARE_20: full Yang-Zhang (2000) decomposition on the daily
    (not 1m-summed) O/H/L/C series over a rolling 20-day window:
    overnight_t = ln(O_t / C_{t-1}); openclose_t = ln(C_t / O_t)
    rs_daily_t  = ln(H_t/C_t)*ln(H_t/O_t) + ln(L_t/C_t)*ln(L_t/O_t)
    V_o = rolling-20 var(overnight_t); V_c = rolling-20 var(openclose_t)
    V_rs = rolling-20 mean(rs_daily_t)
    k = 0.34 / (1.34 + 21/19)  (Yang-Zhang constant for n=20)
    YZ_OVERNIGHT_SHARE_20 = V_o / (V_o + k*V_c + (1-k)*V_rs)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ROLL_WINDOW = 20
Z_WINDOW = 60
LN2 = float(np.log(2.0))
YZ_K = 0.34 / (1.34 + (ROLL_WINDOW + 1) / (ROLL_WINDOW - 1))

ATOMS = (
    "PARKINSON_RV_RATIO_20",
    "GK_RV_RATIO_20",
    "RS_RV_RATIO_20",
    "YZ_OVERNIGHT_SHARE_20",
    "GK_RV_RATIO_CHG_20",
    "GK_RV_RATIO_Z_60",
    "WICK_SHARE_20",
)


def _day_range_ratios(day: pd.DataFrame) -> dict | None:
    o = day["open"].to_numpy(float)
    h = day["high"].to_numpy(float)
    l = day["low"].to_numpy(float)
    c = day["close"].to_numpy(float)
    if len(c) < 60 or not np.all(np.isfinite([o, h, l, c])):
        return None
    prev_c = np.concatenate([[o[0]], c[:-1]])
    with np.errstate(all="ignore"):
        r = np.log(c / np.where(prev_c > 0, prev_c, np.nan))
        log_hl = np.log(np.where((h > 0) & (l > 0), h / l, np.nan))
        log_co = np.log(np.where((c > 0) & (o > 0), c / o, np.nan))
        log_hc = np.log(np.where((h > 0) & (c > 0), h / c, np.nan))
        log_ho = np.log(np.where((h > 0) & (o > 0), h / o, np.nan))
        log_lc = np.log(np.where((l > 0) & (c > 0), l / c, np.nan))
        log_lo = np.log(np.where((l > 0) & (o > 0), l / o, np.nan))
    ok = np.isfinite(r) & np.isfinite(log_hl) & np.isfinite(log_co)
    if ok.sum() < 60:
        return None
    r, log_hl, log_co = r[ok], log_hl[ok], log_co[ok]
    log_hc, log_ho, log_lc, log_lo = log_hc[ok], log_ho[ok], log_lc[ok], log_lo[ok]
    rv = float(np.sum(r * r))
    if rv <= 0:
        return None
    pk = (1.0 / (4.0 * LN2)) * float(np.sum(log_hl**2))
    gk = float(np.sum(0.5 * log_hl**2 - (2.0 * LN2 - 1.0) * log_co**2))
    rs = float(np.sum(log_hc * log_ho + log_lc * log_lo))
    day_o = float(o[0])
    day_h = float(np.max(h))
    day_l = float(np.min(l))
    day_c = float(c[-1])
    return {
        "pk_ratio": pk / rv,
        "gk_ratio": gk / rv,
        "rs_ratio": rs / rv,
        "day_o": day_o,
        "day_h": day_h,
        "day_l": day_l,
        "day_c": day_c,
    }


def _build_range_based_vol(panels, eligibility, data_root, config):
    close = panels["close"]
    dates = close.index
    frequency = str(config.get("frequency", "1m"))
    as_of = dates.max()
    root = Path(data_root)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=close.columns) for name in ATOMS}
    for sym in close.columns:
        try:
            frame, _ = _read_complete_days(root, sym, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        frame = frame.copy()
        frame["date"] = frame["datetime"].dt.normalize()
        records = []
        for date, day in frame.groupby("date", sort=True):
            feats = _day_range_ratios(day)
            if feats is not None:
                feats["date"] = date
                records.append(feats)
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date").sort_index()

        pk_ratio = daily["pk_ratio"]
        gk_ratio = daily["gk_ratio"]
        rs_ratio = daily["rs_ratio"]
        out["PARKINSON_RV_RATIO_20"][sym] = (
            pk_ratio.rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["RS_RV_RATIO_20"][sym] = (
            rs_ratio.rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        gk_ratio_20 = gk_ratio.rolling(ROLL_WINDOW, min_periods=10).mean()
        out["GK_RV_RATIO_20"][sym] = gk_ratio_20.reindex(dates)
        out["GK_RV_RATIO_CHG_20"][sym] = (gk_ratio_20 - gk_ratio_20.shift(ROLL_WINDOW)).reindex(dates)
        gk_mu60 = gk_ratio.rolling(Z_WINDOW, min_periods=30).mean()
        gk_sd60 = gk_ratio.rolling(Z_WINDOW, min_periods=30).std()
        out["GK_RV_RATIO_Z_60"][sym] = ((gk_ratio - gk_mu60) / gk_sd60).reindex(dates)

        day_o, day_h, day_l, day_c = daily["day_o"], daily["day_h"], daily["day_l"], daily["day_c"]
        rng = day_h - day_l
        with np.errstate(all="ignore"):
            upper = day_h - np.maximum(day_o, day_c)
            lower = np.minimum(day_o, day_c) - day_l
            wick_share = (upper + lower) / rng.where(rng > 0)
        out["WICK_SHARE_20"][sym] = (
            wick_share.rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )

        prev_c = day_c.shift(1)
        with np.errstate(all="ignore"):
            overnight = np.log(day_o / prev_c.where(prev_c > 0))
            openclose = np.log(day_c / day_o.where(day_o > 0))
            rs_daily = (
                np.log(day_h / day_c.where(day_c > 0)) * np.log(day_h / day_o.where(day_o > 0))
                + np.log(day_l / day_c.where(day_c > 0)) * np.log(day_l / day_o.where(day_o > 0))
            )
        v_o = overnight.rolling(ROLL_WINDOW, min_periods=10).var()
        v_c = openclose.rolling(ROLL_WINDOW, min_periods=10).var()
        v_rs = rs_daily.rolling(ROLL_WINDOW, min_periods=10).mean()
        yz_total = v_o + YZ_K * v_c + (1.0 - YZ_K) * v_rs
        with np.errstate(all="ignore"):
            overnight_share = v_o / yz_total.where(yz_total > 0)
        out["YZ_OVERNIGHT_SHARE_20"][sym] = overnight_share.reindex(dates)
    return out


register_family(FamilyProvider("range_based_vol_1m", "range_based_vol_1m", _build_range_based_vol))
