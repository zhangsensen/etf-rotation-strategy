"""S26R2 stage (round_617): re-reproduction of pi lane's core volume-
channel atoms using pi's PRECISE definitions (main controller's
2026-09-20 note after S26R: S26R used the controller's own paraphrase
of the definitions -- top-10%-by-volume bars, mean+3*std threshold,
positive-bar-fraction-minus-0.5 -- which differs from pi's actual
definitions, so S26R tested threshold sensitivity rather than a
same-definition independent implementation).

Atom definitions (directive 2026-09-20, S26R2 block, still not reading
pi's code -- only the prose definitions supplied):
  big-bar test: a 1m bar's AMOUNT (not volume) exceeds 5x that day's
    median 1m bar amount (median computed from that day's own bars).
  R2_BIGBAR_VOL_SHARE_20: big-bar volume / day total volume, 20d mean.
  R2_BIGBAR_DIR_SKEW_20: within big bars, (buy volume - sell volume) /
    total big-bar volume, where direction is assigned by the tick rule
    (bar close > previous bar close -> buy; < -> sell; == -> carry
    forward the previous bar's direction, defaulting to buy on the
    day's first bar), 20d mean.
  R2_VOL_SPIKE_FREQ_20: fraction of 1m bars whose VOLUME exceeds 5x
    that day's median 1m bar volume, 20d mean.
  R2_VOL_AUTOCORR_20: lag-1 autocorrelation of the 1m volume series
    within each day, 20d mean (same statistical definition as S26R's
    R_VOL_AUTOCORR_20, rebuilt here from scratch in this new module for
    the new family's self-containment).

R2_ULCER_20 and R2_GAP_FILL_FRACTION_60 are NOT rebuilt here per the
directive ('复用 S26R 的 R_ 版本') -- round_617's driver references
S26R's existing R_ULCER_20 / R_GAP_FILL_FRACTION_60 atoms directly.

Registered as two sub-families (repl_volume_core_v2a: VOL_SPIKE_FREQ,
BIGBAR_DIR_SKEW; repl_volume_core_v2b: BIGBAR_VOL_SHARE, VOL_AUTOCORR)
so the R2_Z2 pair reproduction (BIGBAR_DIR_SKEW x VOL_AUTOCORR)
satisfies the engine's cross_family_only pair policy."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "R2_BIGBAR_VOL_SHARE_20",
    "R2_BIGBAR_DIR_SKEW_20",
    "R2_VOL_SPIKE_FREQ_20",
    "R2_VOL_AUTOCORR_20",
)

_BIGBAR_MULT = 5.0


def _daily_stats(data_root, sym, as_of) -> pd.DataFrame:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if frame.empty or "volume" not in frame.columns or "turnover" not in frame.columns:
        return pd.DataFrame()
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()

    recs = []
    for date, day in frame.groupby("date", sort=True):
        vol = day["volume"].to_numpy(float)
        amt = day["turnover"].to_numpy(float)
        close = day["close"].to_numpy(float)
        n = len(vol)
        if n < 10:
            continue

        median_amt = float(np.median(amt))
        big_mask = amt > (_BIGBAR_MULT * median_amt) if median_amt > 0 else np.zeros(n, dtype=bool)
        total_vol = float(np.sum(vol))
        big_vol = float(np.sum(vol[big_mask]))
        bigbar_vol_share = big_vol / total_vol if total_vol > 0 else np.nan

        direction = np.ones(n)
        prev_dir = 1.0
        for i in range(1, n):
            if close[i] > close[i - 1]:
                direction[i] = 1.0
                prev_dir = 1.0
            elif close[i] < close[i - 1]:
                direction[i] = -1.0
                prev_dir = -1.0
            else:
                direction[i] = prev_dir
        if big_vol > 0:
            buy_vol = float(np.sum(vol[big_mask & (direction > 0)]))
            sell_vol = float(np.sum(vol[big_mask & (direction < 0)]))
            bigbar_dir_skew = (buy_vol - sell_vol) / big_vol
        else:
            bigbar_dir_skew = np.nan

        median_vol = float(np.median(vol))
        spike_freq = float(np.mean(vol > (_BIGBAR_MULT * median_vol))) if median_vol > 0 else np.nan

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
                "bigbar_vol_share": bigbar_vol_share,
                "bigbar_dir_skew": bigbar_dir_skew,
                "spike_freq": spike_freq,
                "vol_autocorr": vol_autocorr,
            }
        )
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _build_all(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    for sym in symbols:
        daily = _daily_stats(data_root, sym, as_of)
        if daily.empty:
            continue
        share_20 = daily["bigbar_vol_share"].rolling(20, min_periods=12).mean()
        skew_20 = daily["bigbar_dir_skew"].rolling(20, min_periods=12).mean()
        spike_20 = daily["spike_freq"].rolling(20, min_periods=12).mean()
        autocorr_20 = daily["vol_autocorr"].rolling(20, min_periods=12).mean()

        out["R2_BIGBAR_VOL_SHARE_20"][sym] = share_20.reindex(dates)
        out["R2_BIGBAR_DIR_SKEW_20"][sym] = skew_20.reindex(dates)
        out["R2_VOL_SPIKE_FREQ_20"][sym] = spike_20.reindex(dates)
        out["R2_VOL_AUTOCORR_20"][sym] = autocorr_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


_V2A_ATOMS = ("R2_VOL_SPIKE_FREQ_20", "R2_BIGBAR_DIR_SKEW_20")
_V2B_ATOMS = ("R2_BIGBAR_VOL_SHARE_20", "R2_VOL_AUTOCORR_20")


def _build_v2a(panels, eligibility, data_root, config):
    full = _build_all(panels, eligibility, data_root, config)
    return {name: full[name] for name in _V2A_ATOMS}


def _build_v2b(panels, eligibility, data_root, config):
    full = _build_all(panels, eligibility, data_root, config)
    return {name: full[name] for name in _V2B_ATOMS}


register_family(FamilyProvider("repl_volume_core_v2a", "repl_volume_core_v2a", _build_v2a))
register_family(FamilyProvider("repl_volume_core_v2b", "repl_volume_core_v2b", _build_v2b))
