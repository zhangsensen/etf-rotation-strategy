"""Stage-S24 family: volume_time_1m -- the volume clock itself (fixed
bucket VOLUME size, variable bucket COUNT per day), independently
implemented in parallel to pi lane's stage 17, directive 2026-09-20
round_603 (S24 stage, main controller, pre-specified direction,
following S23's closure). NOT built by reading pi's code -- only the
literature definitions below and the two required right-leg formulas
supplied in the directive.

This differs from S23's volume_time_drawdown, which resampled each day
into a FIXED COUNT of 50 buckets (bucket size varies day to day). Here
the bucket VOLUME SIZE is fixed (a slowly-moving reference derived from
the trailing 20 days, never today's own volume), so the number of
buckets per day varies with today's volume relative to the recent
past -- the standard "volume clock" construction.

Literature anchors:
- Clark (1973), "A Subordinated Stochastic Process Model with Finite
  Variance for Speculative Prices" -- the original volume/subordinated-
  time-clock idea: price increments become closer to i.i.d. normal when
  sampled per unit of volume rather than per unit of calendar time.
- Ane & Geman (2000), "Order Flow, Transaction Clock, and Normality of
  Asset Returns" -- volume-time resampling removes calendar-time serial
  correlation/clustering artifacts.
- Easley, Lopez de Prado & O'Hara (2012), "The Volume Clock: Insights
  into the High-Frequency Paradigm" -- fixed-size volume buckets as the
  natural clock for detecting informed trading; VPIN-style constructs.

Implementation (practitioner proxy, no arbitrary calendar threshold):
  ref_bucket_size(day t) = mean(daily_total_volume[t-20..t-1]) / 50,
    i.e. a REFERENCE bucket size derived strictly from the trailing 20
    trading days (excludes day t itself -- no lookahead, and crucially
    does not mechanically rescale with day t's own volume, so today's
    bucket COUNT is a genuine signal of today's volume regime)
  within day t: cumvol_s = cumsum(volume_1..s); bucket prices at the
    first bar where cumvol_s crosses each multiple of ref_bucket_size(t)
    (n_buckets_t = floor(total_volume_t / ref_bucket_size(t)), varies
    day to day)
  bucket_returns = diff(log(bucket_prices)) (volume-time log-return
    series, length n_buckets_t - 1)
  RV_v = sum(bucket_returns^2); RV_v_ratio = RV_v / calendar RV_1m
  VT_AUTOCORR = lag-1 autocorrelation of bucket_returns
  VT_RET_SKEW = skewness of bucket_returns
  bucket_durations = number of 1m bars consumed by each bucket;
    VT_BUCKET_GINI = Gini coefficient of bucket_durations (how uneven
    the calendar-time spacing of equal-volume buckets is)
  VT_BUCKET_COUNT = n_buckets_t (raw count); VT_BUCKET_COUNT_SHIFT =
    20-day change of its 20-day rolling mean
  VT_LATE_MOM = sum of bucket_returns in the last 20% of buckets by
    count (volume-time late-session momentum)
All daily statistics are rolled to a 20-day mean (or 20-day change),
never using same-day-or-later information beyond the day itself; the
reference bucket size additionally never uses day t's own volume.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "RV_V_20",
    "RV_V_RATIO_20",
    "VT_AUTOCORR_20",
    "VT_RET_SKEW_20",
    "VT_BUCKET_GINI_20",
    "VT_BUCKET_COUNT_20",
    "VT_BUCKET_COUNT_SHIFT_20",
    "VT_LATE_MOM_20",
)

_REF_N_BUCKETS = 50
_LATE_FRAC = 0.20


def _gini(x: np.ndarray) -> float:
    x = np.sort(x[np.isfinite(x) & (x >= 0)])
    n = len(x)
    if n == 0:
        return np.nan
    total = x.sum()
    if total <= 0:
        return np.nan
    cumx = np.cumsum(x)
    return float((n + 1 - 2.0 * np.sum(cumx) / cumx[-1]) / n)


def _skew(x: np.ndarray) -> float:
    n = len(x)
    if n < 5:
        return np.nan
    mu = np.mean(x)
    sd = np.std(x)
    if sd <= 0:
        return np.nan
    return float(np.mean(((x - mu) / sd) ** 3))


def _volume_time_day_stats(prices: np.ndarray, volumes: np.ndarray, ref_bucket_size: float) -> dict:
    n = len(prices)
    if n < 10 or not np.isfinite(ref_bucket_size) or ref_bucket_size <= 0:
        return {}
    volumes = np.where(np.isfinite(volumes) & (volumes >= 0), volumes, 0.0)
    cumvol = np.cumsum(volumes)
    total = cumvol[-1]
    if not np.isfinite(total) or total <= 0:
        return {}
    n_buckets = int(np.floor(total / ref_bucket_size))
    if n_buckets < 5:
        return {}
    thresholds = ref_bucket_size * np.arange(1, n_buckets + 1)
    idx = np.searchsorted(cumvol, thresholds, side="left")
    idx = np.clip(idx, 0, n - 1)
    bucket_prices = prices[idx]
    bucket_prices = np.concatenate(([prices[0]], bucket_prices))

    log_prices = np.log(bucket_prices)
    bucket_returns = np.diff(log_prices)
    if len(bucket_returns) < 5:
        return {}

    calendar_log_ret = np.diff(np.log(prices))
    calendar_rv = float(np.sum(calendar_log_ret ** 2))
    rv_v = float(np.sum(bucket_returns ** 2))
    rv_v_ratio = rv_v / calendar_rv if calendar_rv > 0 else np.nan

    autocorr = np.nan
    if len(bucket_returns) >= 6:
        a, b = bucket_returns[:-1], bucket_returns[1:]
        if np.std(a) > 0 and np.std(b) > 0:
            autocorr = float(np.corrcoef(a, b)[0, 1])

    bucket_durations = np.diff(np.concatenate(([0], idx))).astype(float)
    bucket_durations = np.where(bucket_durations <= 0, 1.0, bucket_durations)

    n_late = max(1, int(np.ceil(len(bucket_returns) * _LATE_FRAC)))
    late_mom = float(np.sum(bucket_returns[-n_late:]))

    return {
        "rv_v": rv_v,
        "rv_v_ratio": rv_v_ratio,
        "vt_autocorr": autocorr,
        "vt_ret_skew": _skew(bucket_returns),
        "vt_bucket_gini": _gini(bucket_durations),
        "vt_bucket_count": float(n_buckets),
        "vt_late_mom": late_mom,
    }


def _daily_frame(data_root, sym, as_of) -> pd.DataFrame:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if frame.empty or "volume" not in frame.columns:
        return pd.DataFrame()
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()

    daily_volume = frame.groupby("date", sort=True)["volume"].sum()
    ref_bucket_size = (daily_volume.shift(1).rolling(20, min_periods=12).mean() / _REF_N_BUCKETS)

    recs = []
    for date, day in frame.groupby("date", sort=True):
        ref = ref_bucket_size.get(date, np.nan)
        prices = day["close"].to_numpy(float)
        volumes = day["volume"].to_numpy(float)
        mask = np.isfinite(prices) & (prices > 0)
        prices = prices[mask]
        volumes = volumes[mask]
        stats = _volume_time_day_stats(prices, volumes, float(ref) if np.isfinite(ref) else np.nan)
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

    for sym in symbols:
        daily = _daily_frame(data_root, sym, as_of)
        if daily.empty:
            continue

        rv_v_20 = daily["rv_v"].rolling(20, min_periods=12).mean()
        rv_v_ratio_20 = daily["rv_v_ratio"].rolling(20, min_periods=12).mean()
        vt_autocorr_20 = daily["vt_autocorr"].rolling(20, min_periods=12).mean()
        vt_skew_20 = daily["vt_ret_skew"].rolling(20, min_periods=12).mean()
        vt_gini_20 = daily["vt_bucket_gini"].rolling(20, min_periods=12).mean()
        vt_count_20 = daily["vt_bucket_count"].rolling(20, min_periods=12).mean()
        vt_late_mom_20 = daily["vt_late_mom"].rolling(20, min_periods=12).mean()

        out["RV_V_20"][sym] = rv_v_20.reindex(dates)
        out["RV_V_RATIO_20"][sym] = rv_v_ratio_20.reindex(dates)
        out["VT_AUTOCORR_20"][sym] = vt_autocorr_20.reindex(dates)
        out["VT_RET_SKEW_20"][sym] = vt_skew_20.reindex(dates)
        out["VT_BUCKET_GINI_20"][sym] = vt_gini_20.reindex(dates)
        out["VT_BUCKET_COUNT_20"][sym] = vt_count_20.reindex(dates)
        out["VT_BUCKET_COUNT_SHIFT_20"][sym] = (vt_count_20 - vt_count_20.shift(20)).reindex(dates)
        out["VT_LATE_MOM_20"][sym] = vt_late_mom_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("volume_time_1m", "volume_time_1m", _build))
