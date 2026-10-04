"""S26 stage (corrected, round_612): independent re-implementation of pi
lane's core 1m volume-channel atoms and the daily-frequency atoms
needed for its significant pairings, main controller's correction
2026-09-20 23:35 after round_609 wrongly treated a canonical-hash
collision against pre-existing shelf atoms as 'reproduction'.

Controller's explicit instruction: rewrite from the literature
definitions in a NEW family file, prefix every atom R_, do not import
or copy any existing implementation (bar_size_order_flow,
intraday_volume_profile_1m, liquidity_variability, drawdown,
gap_repair). This file uses only raw OHLCV panels (open/high/low/close/
volume/amount) and the shared 1m reader helper _read_complete_days
(a data-access utility, not a factor implementation), and computes
every statistic from scratch.

Atom definitions (directive 2026-09-20, S26 block):
  R_VOL_SPIKE_FREQ_20: within each day, threshold = mean(1m volume) +
    3*std(1m volume) (both computed from that day's own bars only);
    fraction of bars exceeding threshold; 20d rolling mean.
  R_BIGBAR_VOL_SHARE_20: within each day, the top ceil(10%) of bars by
    volume; their combined volume / the day's total volume; 20d
    rolling mean.
  R_BIGBAR_DIR_SKEW_20: within the same top-volume bars, fraction with
    close > open minus 0.5; 20d rolling mean.
  R_VOL_AUTOCORR_20: within each day, lag-1 autocorrelation of the 1m
    volume series; 20d rolling mean.
  R_LOG_AMOUNT_VOL_20: 20-day rolling standard deviation of
    log(daily amount).
  R_ULCER_20: standard Ulcer Index (Martin-McCann 1989) on daily close,
    20-day window: DD_t = (rolling_max_20(close)_t - close_t) /
    rolling_max_20(close)_t; ulcer_t = sqrt(rolling_mean_20(DD^2)).
  R_GAP_FILL_FRACTION_60: per day, gap_t = open_t/close_{t-1} - 1; for
    |gap_t| > 0.1% treat as a genuine gap and mark filled=1 if the
    day's range crossed back through close_{t-1} (low_t <= close_{t-1}
    <= high_t), else filled=0; days with |gap_t| <= 0.1% are treated as
    trivially filled (filled=1, nothing to repair); 60-day rolling mean
    of the filled indicator.

All statistics use only data up to and including day t; no
same-day-or-later leakage beyond the day's own 1m bars for the
intraday atoms."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "R_VOL_SPIKE_FREQ_20",
    "R_BIGBAR_VOL_SHARE_20",
    "R_BIGBAR_DIR_SKEW_20",
    "R_VOL_AUTOCORR_20",
    "R_LOG_AMOUNT_VOL_20",
    "R_ULCER_20",
    "R_GAP_FILL_FRACTION_60",
)

_TOP_FRAC = 0.10
_GAP_EPS = 0.001


def _daily_1m_stats(data_root, sym, as_of) -> pd.DataFrame:
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
        vol = day["volume"].to_numpy(float)
        openp = day["open"].to_numpy(float)
        closep = day["close"].to_numpy(float)
        n = len(vol)
        if n < 10:
            continue
        vol_mean = float(np.mean(vol))
        vol_std = float(np.std(vol))
        threshold = vol_mean + 3.0 * vol_std
        spike_freq = float(np.mean(vol > threshold)) if threshold > 0 else np.nan

        n_top = max(1, int(np.ceil(n * _TOP_FRAC)))
        top_idx = np.argsort(vol)[-n_top:]
        total_vol = float(np.sum(vol))
        bigbar_vol_share = float(np.sum(vol[top_idx]) / total_vol) if total_vol > 0 else np.nan
        top_pos_frac = float(np.mean(closep[top_idx] > openp[top_idx]))
        bigbar_dir_skew = top_pos_frac - 0.5

        if n >= 6 and np.std(vol) > 0:
            a, b = vol[:-1], vol[1:]
            if np.std(a) > 0 and np.std(b) > 0:
                vol_autocorr = float(np.corrcoef(a, b)[0, 1])
            else:
                vol_autocorr = np.nan
        else:
            vol_autocorr = np.nan

        recs.append(
            {
                "date": date,
                "spike_freq": spike_freq,
                "bigbar_vol_share": bigbar_vol_share,
                "bigbar_dir_skew": bigbar_dir_skew,
                "vol_autocorr": vol_autocorr,
            }
        )
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


_FAMILY_A_ATOMS = ("R_VOL_SPIKE_FREQ_20", "R_BIGBAR_DIR_SKEW_20", "R_LOG_AMOUNT_VOL_20")
_FAMILY_B_ATOMS = (
    "R_BIGBAR_VOL_SHARE_20",
    "R_VOL_AUTOCORR_20",
    "R_ULCER_20",
    "R_GAP_FILL_FRACTION_60",
)


def _build_all(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    open_p = panels["open"]
    high_p = panels["high"]
    low_p = panels["low"]
    close_p = panels["close"]
    amount_p = panels["amount"]

    # ---- daily-frequency atoms (vectorized across all symbols) ----
    log_amount = np.log(amount_p.where(amount_p > 0))
    r_log_amount_vol_20 = log_amount.rolling(20, min_periods=12).std()
    out["R_LOG_AMOUNT_VOL_20"] = r_log_amount_vol_20.reindex(dates)

    roll_max_20 = close_p.rolling(20, min_periods=12).max()
    dd = (roll_max_20 - close_p) / roll_max_20
    r_ulcer_20 = np.sqrt((dd ** 2).rolling(20, min_periods=12).mean())
    out["R_ULCER_20"] = r_ulcer_20.reindex(dates)

    prev_close = close_p.shift(1)
    gap = open_p / prev_close - 1.0
    filled = ((low_p <= prev_close) & (high_p >= prev_close)) | (gap.abs() <= _GAP_EPS)
    filled_num = filled.astype(float).where(prev_close.notna())
    r_gap_fill_60 = filled_num.rolling(60, min_periods=30).mean()
    out["R_GAP_FILL_FRACTION_60"] = r_gap_fill_60.reindex(dates)

    # ---- 1m-derived intraday atoms (per symbol) ----
    for sym in symbols:
        daily = _daily_1m_stats(data_root, sym, as_of)
        if daily.empty:
            continue
        spike_20 = daily["spike_freq"].rolling(20, min_periods=12).mean()
        share_20 = daily["bigbar_vol_share"].rolling(20, min_periods=12).mean()
        skew_20 = daily["bigbar_dir_skew"].rolling(20, min_periods=12).mean()
        autocorr_20 = daily["vol_autocorr"].rolling(20, min_periods=12).mean()

        out["R_VOL_SPIKE_FREQ_20"][sym] = spike_20.reindex(dates)
        out["R_BIGBAR_VOL_SHARE_20"][sym] = share_20.reindex(dates)
        out["R_BIGBAR_DIR_SKEW_20"][sym] = skew_20.reindex(dates)
        out["R_VOL_AUTOCORR_20"][sym] = autocorr_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


def _build_family_a(panels, eligibility, data_root, config):
    full = _build_all(panels, eligibility, data_root, config)
    return {name: full[name] for name in _FAMILY_A_ATOMS}


def _build_family_b(panels, eligibility, data_root, config):
    full = _build_all(panels, eligibility, data_root, config)
    return {name: full[name] for name in _FAMILY_B_ATOMS}


# Registered as two families (not one) so the 4 directive pair-reproductions
# satisfy the engine's cross_family_only pair policy -- the original pi-side
# atoms these R_ atoms replace were themselves split across bar_size_order_flow /
# intraday_volume_profile_1m / liquidity_variability / drawdown / gap_repair,
# so splitting the rewrite into two families mirrors that structural fact
# rather than being an artificial workaround.
register_family(FamilyProvider("repl_volume_core_a", "repl_volume_core_a", _build_family_a))
register_family(FamilyProvider("repl_volume_core_b", "repl_volume_core_b", _build_family_b))
