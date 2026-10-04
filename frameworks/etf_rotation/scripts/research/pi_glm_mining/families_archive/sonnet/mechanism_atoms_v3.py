"""S30 stage (round_627, main controller directive): third batch of
mechanism atoms, this time inspired by pi lane's stage-37 significant
pairings (CO36, CK04, CJ16, CZ01/CY95, CR08, CQ31) and built in parallel
independent form on this line.

Efficiency directive (main controller, 2026-09-21 00:40, issued after
S29 closed): pilot new families on a small sample before a full run, and
prefer reuse over re-deriving expensive 1m statistics from scratch. This
family follows that directive aggressively: 5 of its 6 source mechanisms
reuse ALREADY-BUILT atoms from earlier stages via resolve_family() calls
inside _build() (VT_AUTOCORR_20 from S24 volume_time_1m, LUNCH_PRE_RUN_20
from S14 pi_lunch_prerun_1m, LUNCH_POST_RUN_20 from S22 lunch_break_1m,
S28_VOV_HAR_RESID_20 from S28 pi_repl_s28, PV_ELASTICITY_20 from S14
pi_pv_elasticity_1m) -- this is a deliberate departure from S2-S29's
self-contained-only convention, made specifically to avoid redundant 1m
recomputation now that the controller has flagged compute cost as a
concern (S17's first_passage_times_1m took 37+65 minutes for one weak
candidate). Cross-family builders here only consume the `frequency` key
from their config argument (verified empty for all referenced modules),
so a minimal {"frequency": "1m"} dict is passed rather than loading each
family's real YAML. The 6th source mechanism (CZ01/CY95, overnight
direction vs intraday trough recovery) is not rebuilt at all -- it is
byte-identical to S27's already-registered ON_TROUGH_RECOVERY_MATCH_20
(overnight_intraday_mismatch_v1), reused directly as a driver-level
atomic candidate rather than duplicated here.

Only 2 lightweight NEW 1m-derived daily statistics are computed from
scratch, both single-pass day-groupby aggregations (no bucket-boundary
search, no MFI-style rolling-14-bar loop): the last-5-minute return sign
(for the CK04-inspired atom) and the first-30-minute volume sum (for the
CR08-inspired atom).

Atoms:
  VT_AUTOCORR_ACTIVITY_SPLIT_20 (from CO36): rolling-40d window, split
    days by median daily volume (activity level, panels-native, no 1m),
    mean(VT_AUTOCORR_20 | high-activity half) - mean(... | low-activity
    half).
  AM_PRERUN_CLOSE5_CONSIST_20 (from CK04): 20d mean of
    1{sign(LUNCH_PRE_RUN_20 - its own rolling20 mean) ==
    sign(last-5-minute return)}.
  PM_POSTRUN_DAY_CONSIST_20 (from CJ16): 20d mean of
    1{sign(LUNCH_POST_RUN_20 - its own rolling20 mean) ==
    sign(daily close-to-close return)}.
  FIRST30_BUCKET_SHARE_20: floor(first-30-min volume / ref_bucket_size)
    / floor(day volume / ref_bucket_size), ref_bucket_size = lagged-20d
    mean daily volume / 50 (same formula as S24 volume_time_1m /
    S29 BESTDAY_BUCKET_COUNT_RATIO_20), 20d mean (from CR08).
  HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20 (from CQ31): rolling-40d window,
    split days by sign of S28_VOV_HAR_RESID_20, mean(PV_ELASTICITY_20 |
    HAR residual positive) - mean(... | HAR residual negative).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family, resolve_family

ATOM_NAMES = (
    "VT_AUTOCORR_ACTIVITY_SPLIT_20",
    "AM_PRERUN_CLOSE5_CONSIST_20",
    "PM_POSTRUN_DAY_CONSIST_20",
    "FIRST30_BUCKET_SHARE_20",
    "HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20",
)

_SPLIT_WINDOW = 40
_REF_N_BUCKETS = 50
_DUMMY_CONFIG = {"frequency": "1m"}


def _resolved(source: str, panels, eligibility, data_root) -> dict:
    return resolve_family(source).builder(panels, eligibility, data_root, _DUMMY_CONFIG)


def _daily_bar_v3(day: pd.DataFrame) -> dict:
    day = day.sort_values("datetime")
    close = day["close"].to_numpy(float)
    volume = day["volume"].to_numpy(float)
    n = len(close)
    if n < 30 or np.any(close <= 0):
        return {}

    close5_ret = float(close[-1] / close[-5] - 1.0) if n >= 5 else np.nan
    first30_vol = float(volume[:30].sum())

    return {"close5_ret": close5_ret, "first30_vol": first30_vol}


def _daily_1m_frame_v3(data_root, sym, as_of) -> pd.DataFrame:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if frame.empty or "close" not in frame.columns:
        return pd.DataFrame()
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()

    recs = []
    for date, day in frame.groupby("date", sort=True):
        stats = _daily_bar_v3(day)
        if not stats:
            continue
        stats["date"] = date
        recs.append(stats)
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


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
        if len(pos) == 0 or len(neg) == 0:
            continue
        out.iloc[i] = float(np.mean(pos) - np.mean(neg))
    return out


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    volume_p = panels["volume"]
    close_p = panels["close"]
    daily_ret = close_p.pct_change()

    vt_space = _resolved("volume_time_1m", panels, eligibility, data_root)
    vt_autocorr = vt_space["VT_AUTOCORR_20"]

    prerun_space = _resolved("pi_lunch_prerun_1m", panels, eligibility, data_root)
    lunch_prerun = prerun_space["LUNCH_PRE_RUN_20"]

    postrun_space = _resolved("lunch_break_1m", panels, eligibility, data_root)
    lunch_postrun = postrun_space["LUNCH_POST_RUN_20"]

    har_space = _resolved("pi_repl_s28", panels, eligibility, data_root)
    har_resid = har_space["S28_VOV_HAR_RESID_20"]

    pv_space = _resolved("pi_pv_elasticity_1m", panels, eligibility, data_root)
    pv_elasticity = pv_space["PV_ELASTICITY_20"]

    ref_bucket_size = volume_p.shift(1).rolling(20, min_periods=12).mean() / _REF_N_BUCKETS
    day_bucket_count = np.floor(volume_p / ref_bucket_size.where(ref_bucket_size > 0))

    for sym in symbols:
        activity_diff = _rolling_median_split_diff(volume_p[sym], vt_autocorr[sym], _SPLIT_WINDOW)
        out["VT_AUTOCORR_ACTIVITY_SPLIT_20"][sym] = activity_diff.reindex(dates)

        har_pv_diff = _rolling_sign_split_diff(har_resid[sym], pv_elasticity[sym], _SPLIT_WINDOW)
        out["HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20"][sym] = har_pv_diff.reindex(dates)

        daily = _daily_1m_frame_v3(data_root, sym, as_of)
        if daily.empty:
            continue

        prerun_ref_20 = lunch_prerun[sym].rolling(20, min_periods=12).mean()
        prerun_dev = lunch_prerun[sym] - prerun_ref_20
        close5 = daily["close5_ret"].reindex(dates)
        am_consist = np.sign(prerun_dev) == np.sign(close5)
        am_consist = am_consist.where(prerun_dev.notna() & close5.notna())
        am_consist_20 = am_consist.astype(float).rolling(20, min_periods=12).mean()
        out["AM_PRERUN_CLOSE5_CONSIST_20"][sym] = am_consist_20.reindex(dates)

        postrun_ref_20 = lunch_postrun[sym].rolling(20, min_periods=12).mean()
        postrun_dev = lunch_postrun[sym] - postrun_ref_20
        pm_consist = np.sign(postrun_dev) == np.sign(daily_ret[sym])
        pm_consist = pm_consist.where(postrun_dev.notna() & daily_ret[sym].notna())
        pm_consist_20 = pm_consist.astype(float).rolling(20, min_periods=12).mean()
        out["PM_POSTRUN_DAY_CONSIST_20"][sym] = pm_consist_20.reindex(dates)

        first30_vol = daily["first30_vol"].reindex(dates)
        ref_b = ref_bucket_size[sym]
        first30_bucket = np.floor(first30_vol / ref_b.where(ref_b > 0))
        day_bucket = day_bucket_count[sym]
        ratio = first30_bucket / day_bucket.where(day_bucket > 0)
        ratio_20 = ratio.rolling(20, min_periods=12).mean()
        out["FIRST30_BUCKET_SHARE_20"][sym] = ratio_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("mechanism_atoms_v3", "mechanism_atoms_v3", _build))
