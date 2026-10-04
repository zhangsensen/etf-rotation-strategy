"""Stage-S65 family (round_676, main controller directive, 2026-09-21):
1m-resolution capital-gains overhang / holding-cost distribution --
Grinblatt & Han (2005) reference price recursion, generalized so the
"price paid" for each day's turned-over volume is not a single daily
close but a distribution over that day's intraday 1m-bar prices,
weighted by each bar's share of the day's volume.

Literature anchors:
- Grinblatt & Han (2005), "Prospect theory, mental accounting, and
  momentum" -- eq. (1)-(3): reference price RP_t = sum_n w_n P_{t-n},
  w_n proportional to turnover_{t-n} times the survival probability the
  shares bought at t-n were never turned over since.
- Frazzini (2006), "The disposition effect and underreaction to news".

Turnover (E30 correction -- the S63/1d family's V_t/Vbar_t proxy
degenerated to ~1.0 and made CGO_60/GAIN_OVERHANG_60/LOSS_OVERHANG_60 a
disguised same-day-return signal, see round_674 CONTROLLER_VOID.json):
this family uses REAL turnover, TO_t = daily volume_t / PIT fund shares
outstanding (fund_share/<sym>.parquet 'fund_shares' column, aligned by
usable_from_date via merge_asof so only shares-outstanding known as of
<=D are used -- no average-volume proxy).

Intraday cost distribution (practitioner proxy, consistent with this
line's existing 1m conventions): each trading day is split into 8 fixed
30-minute buckets (4 morning + 4 afternoon, 240 1m bars / 8 = 30 bars
each); bucket "price" = volume-weighted mean of 1m close (a vwap proxy,
since 1m OHLCV has no true tick vwap) and bucket "share" = bucket volume
/ day's intraday volume. Combining the day-level Grinblatt-Han survival
weight w_n with each day's intraday bucket-share distribution gives a
weighted set of (price, weight) points spanning N days x 8 buckets,
which is what CGO_1M_N / UNDERWATER_VOL_SHARE_1M_N / COST_CONC_1M_N /
MODE_DIST_1M_N / COST_SKEW_1M_N are computed from.

Atoms (<=6 cap; N=20/60 per directive):
  CGO_1M_20, CGO_1M_60: (close_D - weighted_mean_cost)/weighted_mean_cost.
  UNDERWATER_VOL_SHARE_1M_60: share of the N=60 cost distribution's
    weight sitting at a price above close_D (underwater holders).
  COST_CONC_1M_60: Herfindahl of the cost distribution over 20 equal-
    width price/close_D ratio bins spanning [0.7, 1.3] (values outside
    clipped to the edge bins) -- a practitioner bin choice, not the
    literature's exact quantile scheme.
  MODE_DIST_1M_60: (close_D - modal-bin price)/close_D.
  COST_SKEW_1M_60: weighted skewness of price/close_D - 1 across the
    N=60 x 8 distribution (closed-form moments, no binning).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "CGO_1M_20",
    "CGO_1M_60",
    "UNDERWATER_VOL_SHARE_1M_60",
    "COST_CONC_1M_60",
    "MODE_DIST_1M_60",
    "COST_SKEW_1M_60",
)

_N_BUCKETS = 8
_TURNOVER_CLIP = 0.99
_BIN_EDGES = np.linspace(0.7, 1.3, 21)  # 20 bins


def _daily_bucket_frame(data_root: Path, sym: str, as_of) -> pd.DataFrame:
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
        close = day["close"].to_numpy(float)
        volume = day["volume"].to_numpy(float)
        n = len(close)
        if n < _N_BUCKETS * 3:
            continue
        total_vol = float(volume.sum())
        if total_vol <= 0:
            continue
        close_chunks = np.array_split(close, _N_BUCKETS)
        vol_chunks = np.array_split(volume, _N_BUCKETS)
        vwaps = np.empty(_N_BUCKETS)
        shares = np.empty(_N_BUCKETS)
        for k in range(_N_BUCKETS):
            v = vol_chunks[k].sum()
            vwaps[k] = (close_chunks[k] * vol_chunks[k]).sum() / v if v > 0 else np.nan
            shares[k] = v / total_vol
        rec = {"date": date, "intraday_volume": total_vol}
        for k in range(_N_BUCKETS):
            rec[f"vwap_{k}"] = vwaps[k]
            rec[f"share_{k}"] = shares[k]
        recs.append(rec)
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _pit_fund_shares(data_root: Path, sym: str, dates: pd.DatetimeIndex) -> pd.Series:
    path = Path(data_root) / "fund_share" / f"{sym}.parquet"
    if not path.exists():
        return pd.Series(np.nan, index=dates)
    df = pd.read_parquet(path, columns=["usable_from_date", "fund_shares"]).dropna()
    df = df.sort_values("usable_from_date")
    left = pd.DataFrame({"date": dates})
    merged = pd.merge_asof(
        left, df, left_on="date", right_on="usable_from_date", direction="backward"
    )
    return pd.Series(merged["fund_shares"].to_numpy(), index=dates)


def _gh_day_weights(turnover_c: np.ndarray, n_window: int) -> np.ndarray:
    """Sliding-window Grinblatt-Han survival weights. Returns array shape
    (len(turnover_c) - n_window, n_window); row j, col i = weight on the
    day at absolute index (j + n_window) - 1 - i (i=0 is yesterday)."""
    length = len(turnover_c)
    n_valid = length - n_window
    if n_valid <= 0:
        return np.empty((0, n_window))
    a = np.empty((n_valid, n_window))
    for i in range(n_window):
        a[:, i] = turnover_c[n_window - 1 - i : length - 1 - i]
    b = 1.0 - a
    cumprod_b = np.cumprod(b, axis=1)
    weight = np.empty_like(a)
    weight[:, 0] = a[:, 0]
    weight[:, 1:] = a[:, 1:] * cumprod_b[:, :-1]
    wsum = weight.sum(axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        w = weight / wsum
    return np.where(np.isfinite(w), w, 0.0)


def _window_bucket_arrays(bucket_arr: np.ndarray, n_window: int) -> np.ndarray:
    """bucket_arr shape (T_days, 8) -> windowed shape (T_valid, n_window, 8),
    same lag convention as _gh_day_weights."""
    length = bucket_arr.shape[0]
    n_valid = length - n_window
    k = bucket_arr.shape[1]
    out = np.empty((n_valid, n_window, k))
    for i in range(n_window):
        out[:, i, :] = bucket_arr[n_window - 1 - i : length - 1 - i, :]
    return out


def _build(panels, eligibility, data_root, config):
    del eligibility, config
    close = panels["close"]
    volume = panels["volume"]
    dates = close.index
    symbols = list(close.columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    for sym in symbols:
        daily = _daily_bucket_frame(data_root, sym, as_of)
        if daily.empty or len(daily) < 90:
            continue
        daily_dates = daily.index
        vol_reindexed = volume[sym].reindex(daily_dates)
        fund_shares = _pit_fund_shares(data_root, sym, daily_dates)
        turnover = (vol_reindexed / fund_shares.replace(0, np.nan)).to_numpy(float)
        turnover = np.where(np.isfinite(turnover) & (turnover >= 0), turnover, 0.0)
        turnover_c = np.clip(turnover, 0.0, _TURNOVER_CLIP)

        vwap_arr = daily[[f"vwap_{k}" for k in range(_N_BUCKETS)]].to_numpy(float)
        share_arr = daily[[f"share_{k}" for k in range(_N_BUCKETS)]].to_numpy(float)
        share_arr = np.where(np.isfinite(share_arr), share_arr, 0.0)
        vwap_arr = np.where(np.isfinite(vwap_arr), vwap_arr, 0.0)

        close_daily = close[sym].reindex(daily_dates).to_numpy(float)

        for n_window, cgo_name in ((20, "CGO_1M_20"), (60, "CGO_1M_60")):
            if len(turnover_c) <= n_window:
                continue
            day_w = _gh_day_weights(turnover_c, n_window)
            vwap_w = _window_bucket_arrays(vwap_arr, n_window)
            share_w = _window_bucket_arrays(share_arr, n_window)
            combined_w = day_w[:, :, None] * share_w
            wsum = combined_w.sum(axis=(1, 2))
            combined_w = np.where(wsum[:, None, None] > 0, combined_w / np.where(wsum[:, None, None] > 0, wsum[:, None, None], 1.0), 0.0)

            cur_close = close_daily[n_window:]
            weighted_mean = (combined_w * vwap_w).sum(axis=(1, 2))
            valid = np.isfinite(weighted_mean) & (weighted_mean > 0) & np.isfinite(cur_close)
            cgo = np.where(valid, (cur_close - weighted_mean) / np.where(weighted_mean > 0, weighted_mean, np.nan), np.nan)
            out[cgo_name][sym] = pd.Series(cgo, index=daily_dates[n_window:]).reindex(dates)

            if n_window == 60:
                ratio = np.where(cur_close[:, None, None] > 0, vwap_w / np.where(cur_close[:, None, None] > 0, cur_close[:, None, None], np.nan), np.nan)
                ratio = np.where(np.isfinite(ratio), ratio, 1.0)

                underwater = (combined_w * (vwap_w > cur_close[:, None, None])).sum(axis=(1, 2))
                out["UNDERWATER_VOL_SHARE_1M_60"][sym] = pd.Series(
                    np.where(valid, underwater, np.nan), index=daily_dates[n_window:]
                ).reindex(dates)

                mean_r = (combined_w * (ratio - 1.0)).sum(axis=(1, 2))
                var_r = (combined_w * (ratio - 1.0 - mean_r[:, None, None]) ** 2).sum(axis=(1, 2))
                skew_num = (combined_w * (ratio - 1.0 - mean_r[:, None, None]) ** 3).sum(axis=(1, 2))
                with np.errstate(invalid="ignore", divide="ignore"):
                    skew = skew_num / np.where(var_r > 0, var_r ** 1.5, np.nan)
                out["COST_SKEW_1M_60"][sym] = pd.Series(
                    np.where(valid, skew, np.nan), index=daily_dates[n_window:]
                ).reindex(dates)

                t_valid = combined_w.shape[0]
                conc = np.full(t_valid, np.nan)
                mode_dist = np.full(t_valid, np.nan)
                ratio_clipped = np.clip(ratio, _BIN_EDGES[0], _BIN_EDGES[-1] - 1e-9)
                for t in range(t_valid):
                    if not valid[t]:
                        continue
                    w_flat = combined_w[t].ravel()
                    r_flat = ratio_clipped[t].ravel()
                    hist, _ = np.histogram(r_flat, bins=_BIN_EDGES, weights=w_flat)
                    hsum = hist.sum()
                    if hsum <= 0:
                        continue
                    hist = hist / hsum
                    conc[t] = float(np.sum(hist ** 2))
                    mode_bin = int(np.argmax(hist))
                    mode_center = 0.5 * (_BIN_EDGES[mode_bin] + _BIN_EDGES[mode_bin + 1])
                    mode_dist[t] = 1.0 - mode_center
                out["COST_CONC_1M_60"][sym] = pd.Series(conc, index=daily_dates[n_window:]).reindex(dates)
                out["MODE_DIST_1M_60"][sym] = pd.Series(mode_dist, index=daily_dates[n_window:]).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("cost_distribution_1m_sonnet", "cost_distribution_1m_sonnet", _build))
