"""S29 stage (round_625, main controller directive): second batch of
"mechanism atoms" -- rewrite this line's remaining two-window-significant
pairings as single self-contained statistics, following S27's validated
pattern (single-statistic atoms directly encoding a two-variable
relationship outperformed recombining two pre-existing atoms as
left/right pairing legs).

Each atom below is inspired by one of this line's own admitted pairings
(S27B5/WA1/NI1's MFI_EXTREME_FRAC right leg, UE3/UE1's overnight-share x
underwater/entropy left legs, FC3's underwater-vs-category-dispersion
pairing, LB7's afternoon-volume x BEST_DAY pairing, XC5's
bucket-count-shift x BEST_DAY pairing) but is a SELF-CONTAINED
recomputation from raw daily/1m panels -- it does not import or read any
other family's registered atom, consistent with every prior new-family
module on this line (S2-S28 never cross-import between family builders;
cross-referencing only happens at the mining-driver pairing level).
Formulas reuse the same underlying definitions this line already
validated (Grossman-Zhou 1993 underwater fraction from
intraday_drawdown_1m; Quong-Soudack 1989 MFI from
accumulation_distribution_1m; Yang-Zhang 2000 overnight-variance share
from range_based_vol_1m, simplified to a 2-component overnight/intraday
variance ratio here rather than the full 3-component decomposition,
documented per atom below; volume-time bucket sizing from S24
volume_time_1m) rather than re-deriving them from a blank slate.

Atoms:
  MFI_EXTREME_UNDERWATER_SKEW_20: within each day, frac(MFI extreme bar
    | underwater bar) - frac(MFI extreme bar | above-water bar), 20d
    mean. Tests whether money-flow extremes cluster inside intraday
    drawdowns (S27B5/WA1/NI1's shared right leg, examined directly
    instead of paired against a second atom).
  MFI_EXTREME_FWD5_RET_20: mean within-day forward-5-bar return
    following an MFI-extreme bar, 20d mean (does an MFI extreme predict
    near-term continuation or reversal).
  ON_UNDERWATER_SPLIT_20: simplified overnight-variance-share proxy
    on_share_t = overnight_ret_t^2 / (overnight_ret_t^2 + intraday_ret_t^2)
    (a 2-component Yang-Zhang-lite ratio, not the full 3-component
    decomposition range_based_vol_1m uses); over a rolling 40d window,
    split days by within-window median on_share, output
    mean(underwater_frac | upper half) - mean(underwater_frac | lower
    half) (UE3/UE1's overnight-share x underwater mechanism, examined
    directly).
  REL_UNDERWATER_CATEGORY_20: this ETF's daily underwater_frac minus
    the cross-sectional mean underwater_frac of its sleeve-category
    peers (sleeve grouping from config/etf_rotation_universe_v1.json's
    candidate-role "sleeve" field: technology n=8 vs auxiliary_rotation
    n=6), 20d mean (FC3's underwater-vs-category-dispersion mechanism).
  PM_FRONTRUN_RET_CONSIST_20: 20d mean of
    1{sign(afternoon_share_t - rolling20_mean(afternoon_share)) ==
    sign(daily_return_t)}, where afternoon_share_t = 13:00-13:10 volume
    / day volume (LB7's afternoon-volume x day-return mechanism).
  BESTDAY_BUCKET_COUNT_RATIO_20: over a rolling 20d window, the volume-
    time bucket count (ref_bucket_size = lagged-20d mean daily volume /
    50, n_buckets = floor(day_volume / ref_bucket_size), same formula
    as S24 volume_time_1m's VT_BUCKET_COUNT) on the day with the
    window's max return, divided by the window's mean bucket count
    (XC5's bucket-count x BEST_DAY mechanism).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "MFI_EXTREME_UNDERWATER_SKEW_20",
    "MFI_EXTREME_FWD5_RET_20",
    "ON_UNDERWATER_SPLIT_20",
    "REL_UNDERWATER_CATEGORY_20",
    "PM_FRONTRUN_RET_CONSIST_20",
    "BESTDAY_BUCKET_COUNT_RATIO_20",
)

_MFI_WINDOW = 14
_ON_SPLIT_WINDOW = 40
_BESTDAY_WINDOW = 20
_REF_N_BUCKETS = 50
_UNIVERSE_CONFIG = Path(str(Path(__file__).resolve().parents[7] / "config/etf_rotation_universe_v1.json"))


def _load_sleeve_map() -> dict:
    try:
        data = json.loads(_UNIVERSE_CONFIG.read_text())
    except Exception:  # noqa: BLE001
        return {}
    return {
        e["ts_code"]: e.get("sleeve", "unknown")
        for e in data.get("etfs", [])
        if e.get("role") == "candidate"
    }


def _daily_bar_mechanism(day: pd.DataFrame) -> dict:
    day = day.sort_values("datetime")
    close = day["close"].to_numpy(float)
    high = day["high"].to_numpy(float)
    low = day["low"].to_numpy(float)
    volume = day["volume"].to_numpy(float)
    n = len(close)
    if n < 20 or np.any(close <= 0):
        return {}

    running_peak = np.maximum.accumulate(close)
    drawdown = (running_peak - close) / running_peak
    underwater = drawdown > 0
    underwater_frac = float(np.mean(underwater))

    typical = (high + low + close) / 3.0
    tp_diff = np.diff(typical)
    raw_flow = typical * volume
    pos_flow = np.zeros(n)
    neg_flow = np.zeros(n)
    pos_flow[1:] = np.where(tp_diff > 0, raw_flow[1:], 0.0)
    neg_flow[1:] = np.where(tp_diff < 0, raw_flow[1:], 0.0)
    mfi = np.empty(n)
    for i in range(n):
        start = max(0, i - _MFI_WINDOW + 1)
        pos_sum = pos_flow[start : i + 1].sum()
        neg_sum = neg_flow[start : i + 1].sum()
        if neg_sum <= 0:
            mfi[i] = 100.0 if pos_sum > 0 else 50.0
        else:
            mfi[i] = 100.0 - 100.0 / (1.0 + pos_sum / neg_sum)
    extreme = (mfi > 80.0) | (mfi < 20.0)

    n_uw = int(np.sum(underwater))
    n_above = n - n_uw
    frac_extreme_uw = float(np.mean(extreme[underwater])) if n_uw > 0 else np.nan
    frac_extreme_above = float(np.mean(extreme[~underwater])) if n_above > 0 else np.nan
    mfi_uw_skew = (
        frac_extreme_uw - frac_extreme_above
        if np.isfinite(frac_extreme_uw) and np.isfinite(frac_extreme_above)
        else np.nan
    )

    fwd_rets = [
        (close[i + 5] - close[i]) / close[i]
        for i in range(n)
        if extreme[i] and i + 5 < n
    ]
    mfi_fwd5_ret = float(np.mean(fwd_rets)) if fwd_rets else np.nan

    tod = day["datetime"].dt.time
    pm_mask = (tod >= pd.to_datetime("13:00").time()) & (tod < pd.to_datetime("13:10").time())
    total_vol = float(volume.sum())
    afternoon_share = float(volume[pm_mask.to_numpy()].sum() / total_vol) if total_vol > 0 else np.nan

    return {
        "underwater_frac": underwater_frac,
        "mfi_uw_skew": mfi_uw_skew,
        "mfi_fwd5_ret": mfi_fwd5_ret,
        "afternoon_share": afternoon_share,
    }


def _daily_1m_frame(data_root, sym, as_of) -> pd.DataFrame:
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
        stats = _daily_bar_mechanism(day)
        if not stats:
            continue
        stats["date"] = date
        recs.append(stats)
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _rolling_split_diff(level: pd.Series, target: pd.Series, window: int) -> pd.Series:
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


def _bestday_bucket_ratio(daily_ret: pd.Series, bucket_count: pd.Series, window: int) -> pd.Series:
    df = pd.concat({"ret": daily_ret, "bucket": bucket_count}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    ret = df["ret"].to_numpy(float)
    bucket = df["bucket"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        ret_w = ret[start : i + 1]
        bucket_w = bucket[start : i + 1]
        mean_bucket = np.mean(bucket_w)
        if mean_bucket <= 0:
            continue
        best_idx = int(np.argmax(ret_w))
        out.iloc[i] = float(bucket_w[best_idx] / mean_bucket)
    return out


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    open_p = panels["open"]
    close_p = panels["close"]
    volume_p = panels["volume"]

    prev_close = close_p.shift(1)
    overnight_ret = np.log(open_p / prev_close.where(prev_close > 0))
    intraday_ret = np.log(close_p / open_p.where(open_p > 0))
    on_share = (overnight_ret ** 2) / (overnight_ret ** 2 + intraday_ret ** 2 + 1e-12)

    ref_bucket_size = volume_p.shift(1).rolling(20, min_periods=12).mean() / _REF_N_BUCKETS
    bucket_count = np.floor(volume_p / ref_bucket_size.where(ref_bucket_size > 0))
    daily_ret = close_p.pct_change()

    sleeve_map = _load_sleeve_map()

    per_symbol_daily: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        daily = _daily_1m_frame(data_root, sym, as_of)
        per_symbol_daily[sym] = daily
        if daily.empty:
            continue

        uw_skew_20 = daily["mfi_uw_skew"].rolling(20, min_periods=12).mean()
        fwd5_ret_20 = daily["mfi_fwd5_ret"].rolling(20, min_periods=12).mean()
        out["MFI_EXTREME_UNDERWATER_SKEW_20"][sym] = uw_skew_20.reindex(dates)
        out["MFI_EXTREME_FWD5_RET_20"][sym] = fwd5_ret_20.reindex(dates)

        on_level = on_share[sym].reindex(daily.index)
        split_diff = _rolling_split_diff(on_level, daily["underwater_frac"], _ON_SPLIT_WINDOW)
        out["ON_UNDERWATER_SPLIT_20"][sym] = split_diff.reindex(dates)

        afternoon = daily["afternoon_share"]
        afternoon_ref_20 = afternoon.rolling(20, min_periods=12).mean()
        deviation = afternoon - afternoon_ref_20
        ret_aligned = daily_ret[sym].reindex(daily.index)
        consist = np.sign(deviation) == np.sign(ret_aligned)
        consist = consist.where(deviation.notna() & ret_aligned.notna())
        consist_20 = consist.astype(float).rolling(20, min_periods=12).mean()
        out["PM_FRONTRUN_RET_CONSIST_20"][sym] = consist_20.reindex(dates)

        bd_ratio = _bestday_bucket_ratio(daily_ret[sym], bucket_count[sym], _BESTDAY_WINDOW)
        out["BESTDAY_BUCKET_COUNT_RATIO_20"][sym] = bd_ratio.reindex(dates)

    underwater_daily = pd.DataFrame(
        {sym: per_symbol_daily[sym].get("underwater_frac", pd.Series(dtype=float)) for sym in symbols}
    )
    underwater_daily = underwater_daily.reindex(dates)
    for sym in symbols:
        sleeve = sleeve_map.get(sym)
        if sleeve is None:
            continue
        peers = [s for s in symbols if s != sym and sleeve_map.get(s) == sleeve]
        if not peers:
            continue
        peer_mean = underwater_daily[peers].mean(axis=1, skipna=True)
        rel = underwater_daily[sym] - peer_mean
        rel_20 = rel.rolling(20, min_periods=12).mean()
        out["REL_UNDERWATER_CATEGORY_20"][sym] = rel_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("mechanism_atoms_v2", "mechanism_atoms_v2", _build))
