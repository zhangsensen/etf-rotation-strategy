"""Stage-S23 family: volume_time_drawdown -- intraday drawdown path
geometry computed under VOLUME time rather than calendar time, directive
2026-09-20 round_600 (S23 stage, main controller, pre-specified
direction, following S22's closure).

Literature anchors:
- Ane & Geman (2000), "Order Flow, Transaction Clock, and Normality of
  Asset Returns" -- resampling the price path in volume/transaction time
  rather than calendar time removes the well-known non-normality/
  clustering artifacts of calendar-time sampling.
- Easley, Lopez de Prado & O'Hara (2012), "The Volume Clock: Insights
  into the High-Frequency Paradigm" -- volume bars/buckets as the natural
  clock for detecting informed-trading-driven price moves, since volume
  arrival rate (not calendar time) tracks information flow.
- Magdon-Ismail & Atiya (2004) / Chekhlov-Uryasev-Zabarankin (2005) /
  Grossman & Zhou (1993) -- the same drawdown-geometry primitives as
  S7's intraday_drawdown_1m (calendar-time), reapplied here to the
  volume-time-resampled path to test whether the underwater/drawdown
  signal (S7's strongest single atom, UNDERWATER_FRAC_CHG_20) is a
  calendar-time artifact or survives a volume-time reclocking.

Implementation (practitioner proxy, no fixed threshold): within each
trading day, using 1m close prices and 1m volumes:
  bucket_size = total_day_volume / 50 (50 volume-time buckets/day, not a
    fixed price/volume threshold -- adapts to each day's own volume)
  cumvol_t = cumsum(volume_1..t); for k=1..50, bucket_price_k = close at
    the first bar where cumvol_t >= k * bucket_size (volume-time
    resampled price path, length 50)
  running_peak/drawdown/underwater_frac/max_dd/trough_position computed
    on this volume-time path exactly as S7's calendar-time stats;
  recovery_frac = (buckets from trough to first bucket >= pre-trough
    peak) / (buckets remaining after trough); unrecovered by day end = 1
  path_efficiency = |bucket_price[-1] - bucket_price[0]| / sum(|diffs|)
  cal_vt_uf_diff = calendar-time underwater_frac (same day, same
    definition as S7's UNDERWATER_FRAC_20) minus volume-time
    underwater_frac (tests whether drawdowns concentrate in high-volume
    periods, i.e. calendar-time underwater exceeds volume-time
    underwater when dips happen on low-volume/quiet bars)
All daily statistics are rolled to a 20-day mean (or 20-day change),
never using same-day-or-later information beyond the day itself.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "VT_UNDERWATER_FRAC_20",
    "VT_UNDERWATER_FRAC_CHG_20",
    "VT_MAXDD_20",
    "VT_MAXDD_CHG_20",
    "VT_RECOVERY_FRAC_20",
    "CAL_VT_UF_DIFF_20",
    "VT_PATH_EFFICIENCY_20",
    "VT_TROUGH_VOL_POS_20",
)

_N_BUCKETS = 50


def _volume_time_bucket_prices(prices: np.ndarray, volumes: np.ndarray) -> np.ndarray | None:
    n = len(prices)
    if n < 10:
        return None
    volumes = np.where(np.isfinite(volumes) & (volumes >= 0), volumes, 0.0)
    cumvol = np.cumsum(volumes)
    total = cumvol[-1]
    if not np.isfinite(total) or total <= 0:
        return None
    thresholds = total * (np.arange(1, _N_BUCKETS + 1) / _N_BUCKETS)
    idx = np.searchsorted(cumvol, thresholds, side="left")
    idx = np.clip(idx, 0, n - 1)
    return prices[idx]


def _cal_underwater_frac(prices: np.ndarray) -> float:
    running_peak = np.maximum.accumulate(prices)
    drawdown = (running_peak - prices) / running_peak
    return float(np.mean(drawdown > 0))


def _vt_stats(bucket_prices: np.ndarray) -> dict:
    n = len(bucket_prices)
    if n < 10:
        return {}
    running_peak = np.maximum.accumulate(bucket_prices)
    drawdown = (running_peak - bucket_prices) / running_peak

    underwater_frac = float(np.mean(drawdown > 0))
    max_dd = float(np.max(drawdown))
    trough_idx = int(np.argmax(drawdown))
    trough_vol_pos = trough_idx / (n - 1) if n > 1 else 0.5

    net_disp = abs(float(bucket_prices[-1] - bucket_prices[0]))
    path_len = float(np.sum(np.abs(np.diff(bucket_prices))))
    path_efficiency = net_disp / path_len if path_len > 0 else np.nan

    peak_at_trough = running_peak[trough_idx]
    remaining = n - 1 - trough_idx
    if remaining > 0:
        after = bucket_prices[trough_idx + 1 :]
        hits = np.flatnonzero(after >= peak_at_trough)
        recovery_frac = float((hits[0] + 1) / remaining) if hits.size else 1.0
    else:
        recovery_frac = 1.0

    return {
        "vt_underwater_frac": underwater_frac,
        "vt_maxdd": max_dd,
        "vt_trough_vol_pos": trough_vol_pos,
        "vt_path_efficiency": path_efficiency,
        "vt_recovery_frac": recovery_frac,
    }


def _daily_vt_frame(data_root, sym, as_of) -> pd.DataFrame:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if frame.empty or "volume" not in frame.columns:
        return pd.DataFrame()
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()

    recs = []
    for date, day in frame.groupby("date", sort=True):
        prices = day["close"].to_numpy(float)
        volumes = day["volume"].to_numpy(float)
        mask = np.isfinite(prices) & (prices > 0)
        prices = prices[mask]
        volumes = volumes[mask]
        if len(prices) < 10:
            continue
        bucket_prices = _volume_time_bucket_prices(prices, volumes)
        if bucket_prices is None:
            continue
        stats = _vt_stats(bucket_prices)
        if not stats:
            continue
        stats["cal_underwater_frac"] = _cal_underwater_frac(prices)
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
        daily = _daily_vt_frame(data_root, sym, as_of)
        if daily.empty:
            continue

        vt_uf_20 = daily["vt_underwater_frac"].rolling(20, min_periods=12).mean()
        vt_maxdd_20 = daily["vt_maxdd"].rolling(20, min_periods=12).mean()
        vt_recovery_20 = daily["vt_recovery_frac"].rolling(20, min_periods=12).mean()
        vt_path_eff_20 = daily["vt_path_efficiency"].rolling(20, min_periods=12).mean()
        vt_trough_pos_20 = daily["vt_trough_vol_pos"].rolling(20, min_periods=12).mean()
        cal_uf_20 = daily["cal_underwater_frac"].rolling(20, min_periods=12).mean()

        out["VT_UNDERWATER_FRAC_20"][sym] = vt_uf_20.reindex(dates)
        out["VT_UNDERWATER_FRAC_CHG_20"][sym] = (vt_uf_20 - vt_uf_20.shift(20)).reindex(dates)
        out["VT_MAXDD_20"][sym] = vt_maxdd_20.reindex(dates)
        out["VT_MAXDD_CHG_20"][sym] = (vt_maxdd_20 - vt_maxdd_20.shift(20)).reindex(dates)
        out["VT_RECOVERY_FRAC_20"][sym] = vt_recovery_20.reindex(dates)
        out["CAL_VT_UF_DIFF_20"][sym] = (cal_uf_20 - vt_uf_20).reindex(dates)
        out["VT_PATH_EFFICIENCY_20"][sym] = vt_path_eff_20.reindex(dates)
        out["VT_TROUGH_VOL_POS_20"][sym] = vt_trough_pos_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("volume_time_drawdown", "volume_time_drawdown", _build))
