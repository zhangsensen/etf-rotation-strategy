"""Stage-S45 family: repl_overnight_core_v2 -- reproduction, round_645
(S45 stage, main controller directive 2026-09-21). S14 tried to
reproduce pi's overnight_structure_1d family's CZ01 using a
CONTROLLER-PARAPHRASED definition of BIGBAR_EDGE_CONC_20 ("big-bar
volume in the first/last 30 minutes") and failed to reproduce
(+6.8bp/t0.34 here vs pi's +55.2bp/t2.76). This round uses pi's own
CODE-LEVEL comment/definition instead ("share of big-bar volume in its
MODAL 30-minute slot", not "first or last 30 minutes"), to separate
"implementation idiosyncrasy" from "paraphrase distortion" as the true
cause of the earlier reproduction failure. Prefixed R2_ per directive
(distinct from S26R2's repl_volume_core_v2 atoms -- no name collision,
verified).

Literature/definition anchors (per directive, not read from pi code):
- Big-bar threshold: 1m bar amount > day-median bar amount x5 (this
  line's own established precise definition, reused from S26R2/S33).
- R2_BIGBAR_EDGE_CONC_20: split the day into 8 fixed 30-minute segments
  (240 1m bars / 8); the "modal" segment is whichever of the 8 holds the
  most big-bar volume that day; the atom is (big-bar volume in that
  modal segment) / (total big-bar volume that day), 20d mean.
- R2_ON_PREM_20: overnight_ret = open(D)/close(D-1) - 1, 20d mean (Lou-
  Polk-Skouras 2019).
- R2_GAP_FILL_RATE_20: for a gap up (overnight_ret>0), fraction of the
  gap given back by day's low: (open - low)/(open - prev_close), clipped
  [0,1]; for a gap down, symmetric: (high - open)/(prev_close - open),
  clipped [0,1]; zero-gap days excluded. 20d mean.
- R2_OPEN30_VOL_SHARE_20: first-30-minute volume / day volume, 20d mean.
- R2_PRICE_POSITION_20: (close - 20d low)/(20d high - 20d low), pure
  daily-panel, no 1m read.

Registered as two sub-families (repl_overnight_core_v2a: R2_ON_PREM_20,
R2_GAP_FILL_RATE_20; repl_overnight_core_v2b: R2_BIGBAR_EDGE_CONC_20,
R2_OPEN30_VOL_SHARE_20, R2_PRICE_POSITION_20) so the R2_CZ01/CY07/CY17
reproduction pairs satisfy the engine's cross_family_only pair policy
(same pattern as S26R2's repl_volume_core_v2a/v2b split)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "R2_BIGBAR_EDGE_CONC_20",
    "R2_ON_PREM_20",
    "R2_GAP_FILL_RATE_20",
    "R2_OPEN30_VOL_SHARE_20",
    "R2_PRICE_POSITION_20",
)

_BIGBAR_MULT = 5.0
_N_SEGMENTS = 8
_OPEN30_BARS = 30


def _daily_bar(day: pd.DataFrame) -> dict:
    day = day.sort_values("datetime")
    close = day["close"].to_numpy(float)
    volume = day["volume"].to_numpy(float)
    amount = day["turnover"].to_numpy(float) if "turnover" in day.columns else None
    n = len(close)
    if n < 60 or np.any(close <= 0):
        return {}

    total_vol = float(np.sum(volume))
    if total_vol <= 0:
        return {}

    open30_share = float(np.sum(volume[:_OPEN30_BARS]) / total_vol)

    bigbar_edge_conc = np.nan
    if amount is not None:
        median_amt = float(np.median(amount))
        if median_amt > 0:
            big_mask = amount > (_BIGBAR_MULT * median_amt)
            big_vol_total = float(np.sum(volume[big_mask]))
            if big_vol_total > 0:
                seg_size = max(1, n // _N_SEGMENTS)
                seg_idx = np.minimum(np.arange(n) // seg_size, _N_SEGMENTS - 1)
                seg_big_vol = np.zeros(_N_SEGMENTS)
                for s in range(_N_SEGMENTS):
                    seg_big_vol[s] = float(np.sum(volume[big_mask & (seg_idx == s)]))
                bigbar_edge_conc = float(np.max(seg_big_vol) / big_vol_total)

    return {"open30_share": open30_share, "bigbar_edge_conc": bigbar_edge_conc}


def _daily_frame(data_root, sym, as_of) -> pd.DataFrame:
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
        stats = _daily_bar(day)
        if not stats:
            continue
        stats["date"] = date
        recs.append(stats)
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _build_all(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    close_p = panels["close"]
    open_p = panels["open"]
    high_p = panels["high"]
    low_p = panels["low"]

    overnight_ret = open_p / close_p.shift(1) - 1.0
    on_prem_20 = overnight_ret.rolling(20, min_periods=12).mean()

    gap_up_fill = ((open_p - low_p) / (open_p - close_p.shift(1))).clip(lower=0.0, upper=1.0)
    gap_down_fill = ((high_p - open_p) / (close_p.shift(1) - open_p)).clip(lower=0.0, upper=1.0)
    gap_fill = gap_up_fill.where(overnight_ret > 0, gap_down_fill.where(overnight_ret < 0))
    gap_fill_rate_20 = gap_fill.rolling(20, min_periods=12).mean()

    price_position_20 = (close_p - low_p.rolling(20, min_periods=12).min()) / (
        high_p.rolling(20, min_periods=12).max() - low_p.rolling(20, min_periods=12).min()
    )

    out["R2_ON_PREM_20"] = on_prem_20.reindex(dates)
    out["R2_GAP_FILL_RATE_20"] = gap_fill_rate_20.reindex(dates)
    out["R2_PRICE_POSITION_20"] = price_position_20.reindex(dates)

    for sym in symbols:
        daily = _daily_frame(data_root, sym, as_of)
        if daily.empty:
            continue

        open30_20 = daily["open30_share"].rolling(20, min_periods=12).mean()
        bigbar_edge_20 = daily["bigbar_edge_conc"].rolling(20, min_periods=12).mean()

        out["R2_OPEN30_VOL_SHARE_20"][sym] = open30_20.reindex(dates)
        out["R2_BIGBAR_EDGE_CONC_20"][sym] = bigbar_edge_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


_V2A_ATOMS = ("R2_ON_PREM_20", "R2_GAP_FILL_RATE_20")
_V2B_ATOMS = ("R2_BIGBAR_EDGE_CONC_20", "R2_OPEN30_VOL_SHARE_20", "R2_PRICE_POSITION_20")


def _build_v2a(panels, eligibility, data_root, config):
    full = _build_all(panels, eligibility, data_root, config)
    return {name: full[name] for name in _V2A_ATOMS}


def _build_v2b(panels, eligibility, data_root, config):
    full = _build_all(panels, eligibility, data_root, config)
    return {name: full[name] for name in _V2B_ATOMS}


register_family(FamilyProvider("repl_overnight_core_v2a", "repl_overnight_core_v2a", _build_v2a))
register_family(FamilyProvider("repl_overnight_core_v2b", "repl_overnight_core_v2b", _build_v2b))
