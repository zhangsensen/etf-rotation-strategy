"""S33 stage (round_632, main controller directive): deepen the
strongest content mechanism on this line -- money-flow/volume extremes
occurring inside intraday drawdowns (S27B5 t3.89, S29Q1 t3.60, WA1
t2.15). New self-contained constructs, no threshold tuning beyond the
already-validated pi-precise big-bar definition (amount > day-median
amount x5, same as S26R2/repl_volume_core_v2).

Literature anchors:
- Blume, Easley & O'Hara (1994), "Market Statistics and Technical
  Analysis: The Role of Volume", JF -- volume as a signal-quality proxy
  distinct from price alone.
- Campbell, Grossman & Wang (1993), "Trading Volume and Serial
  Correlation in Stock Returns", QJE -- volume accompanying price
  declines predicts reversal (liquidity-driven selling).
- Karpoff (1987), "The Relation Between Price Changes and Trading
  Volume: A Survey", JFQA -- volume-price relationship asymmetry.

Implementation (per symbol, single 1m pass per day, self-contained --
no cross-family imports): for each day, running_peak = cummax(close),
drawdown = (peak-close)/peak, underwater = drawdown > 0, trough_idx =
argmax(drawdown).

Atoms:
  DD_VOL_SHARE_EXCESS_20: (volume in underwater bars / day volume) -
    (underwater bar count / day bar count), 20d mean. Positive means
    the drawdown segment is disproportionately volume-heavy.
  TROUGH_PREPOST_VOL_RATIO_20: log(volume in the 5 bars before the
    trough / volume in the 5 bars after the trough), 20d mean (panic
    selling into the low vs absorption volume after).
  DD_RET_VOL_CORR_20: within-day correlation between 1m return and 1m
    volume, restricted to underwater bars only, 20d mean (positive =
    volume expands as price falls further inside the drawdown,
    "selling-type" drawdown).
  DD_BIGBAR_VOL_SHARE_20: big-bar volume (bar amount > day-median
    amount x5, pi's precise definition) within underwater bars / total
    underwater-bar volume, 20d mean.
  RECOVERY_VOL_SHARE_EXCESS_20: (volume in the recovery segment --
    trough to the bar where price first regains the pre-drawdown peak,
    or day end if never recovered -- / day volume) - (recovery bar
    count / day bar count), 20d mean.
  DD_VOL_SHARE_EXCESS_CHG_20 / DD_RET_VOL_CORR_CHG_20: 20d change of the
    two atoms judged most likely to carry distinct information (the
    volume-concentration dimension and the selling-direction dimension).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "DD_VOL_SHARE_EXCESS_20",
    "TROUGH_PREPOST_VOL_RATIO_20",
    "DD_RET_VOL_CORR_20",
    "DD_BIGBAR_VOL_SHARE_20",
    "RECOVERY_VOL_SHARE_EXCESS_20",
    "DD_VOL_SHARE_EXCESS_CHG_20",
    "DD_RET_VOL_CORR_CHG_20",
)

_BIGBAR_MULT = 5.0
_PREPOST_WINDOW = 5


def _daily_bar_dd_vol(day: pd.DataFrame) -> dict:
    day = day.sort_values("datetime")
    close = day["close"].to_numpy(float)
    volume = day["volume"].to_numpy(float)
    amount = day["turnover"].to_numpy(float) if "turnover" in day.columns else None
    n = len(close)
    if n < 20 or np.any(close <= 0):
        return {}

    total_vol = float(np.sum(volume))
    if total_vol <= 0:
        return {}

    running_peak = np.maximum.accumulate(close)
    drawdown = (running_peak - close) / running_peak
    underwater = drawdown > 0
    n_uw = int(np.sum(underwater))
    trough_idx = int(np.argmax(drawdown))

    uw_vol_share = float(np.sum(volume[underwater]) / total_vol)
    uw_bar_share = float(n_uw) / float(n)
    dd_vol_excess = uw_vol_share - uw_bar_share

    pre_start = max(0, trough_idx - _PREPOST_WINDOW)
    pre_vol = float(np.sum(volume[pre_start:trough_idx]))
    post_end = min(n, trough_idx + 1 + _PREPOST_WINDOW)
    post_vol = float(np.sum(volume[trough_idx + 1 : post_end]))
    prepost_ratio = float(np.log(pre_vol / post_vol)) if pre_vol > 0 and post_vol > 0 else np.nan

    ret = np.diff(close) / close[:-1]
    vol_tail = volume[1:]
    uw_tail = underwater[1:]
    if int(np.sum(uw_tail)) >= 5 and np.std(ret[uw_tail]) > 0 and np.std(vol_tail[uw_tail]) > 0:
        dd_ret_vol_corr = float(np.corrcoef(ret[uw_tail], vol_tail[uw_tail])[0, 1])
    else:
        dd_ret_vol_corr = np.nan

    dd_bigbar_share = np.nan
    if amount is not None and n_uw > 0:
        median_amt = float(np.median(amount))
        if median_amt > 0:
            big_mask = amount > (_BIGBAR_MULT * median_amt)
            dd_vol_total = float(np.sum(volume[underwater]))
            if dd_vol_total > 0:
                dd_bigbar_share = float(np.sum(volume[underwater & big_mask]) / dd_vol_total)

    peak_at_trough = running_peak[trough_idx]
    recovered = np.where(close[trough_idx:] >= peak_at_trough)[0]
    if len(recovered) > 0:
        recovery_end = trough_idx + int(recovered[0])
    else:
        recovery_end = n - 1
    recovery_bars = slice(trough_idx, recovery_end + 1)
    recovery_n = recovery_end - trough_idx + 1
    recovery_vol_share = float(np.sum(volume[recovery_bars]) / total_vol)
    recovery_bar_share = float(recovery_n) / float(n)
    recovery_vol_excess = recovery_vol_share - recovery_bar_share

    return {
        "dd_vol_excess": dd_vol_excess,
        "prepost_ratio": prepost_ratio,
        "dd_ret_vol_corr": dd_ret_vol_corr,
        "dd_bigbar_share": dd_bigbar_share,
        "recovery_vol_excess": recovery_vol_excess,
    }


def _daily_frame(data_root, sym, as_of) -> pd.DataFrame:
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
        stats = _daily_bar_dd_vol(day)
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

        dd_vol_excess_20 = daily["dd_vol_excess"].rolling(20, min_periods=12).mean()
        prepost_ratio_20 = daily["prepost_ratio"].rolling(20, min_periods=12).mean()
        dd_ret_vol_corr_20 = daily["dd_ret_vol_corr"].rolling(20, min_periods=12).mean()
        dd_bigbar_share_20 = daily["dd_bigbar_share"].rolling(20, min_periods=12).mean()
        recovery_vol_excess_20 = daily["recovery_vol_excess"].rolling(20, min_periods=12).mean()

        out["DD_VOL_SHARE_EXCESS_20"][sym] = dd_vol_excess_20.reindex(dates)
        out["TROUGH_PREPOST_VOL_RATIO_20"][sym] = prepost_ratio_20.reindex(dates)
        out["DD_RET_VOL_CORR_20"][sym] = dd_ret_vol_corr_20.reindex(dates)
        out["DD_BIGBAR_VOL_SHARE_20"][sym] = dd_bigbar_share_20.reindex(dates)
        out["RECOVERY_VOL_SHARE_EXCESS_20"][sym] = recovery_vol_excess_20.reindex(dates)
        out["DD_VOL_SHARE_EXCESS_CHG_20"][sym] = (
            dd_vol_excess_20 - dd_vol_excess_20.shift(20)
        ).reindex(dates)
        out["DD_RET_VOL_CORR_CHG_20"][sym] = (
            dd_ret_vol_corr_20 - dd_ret_vol_corr_20.shift(20)
        ).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("volume_extremes_in_drawdown_1m", "volume_extremes_in_drawdown_1m", _build))
