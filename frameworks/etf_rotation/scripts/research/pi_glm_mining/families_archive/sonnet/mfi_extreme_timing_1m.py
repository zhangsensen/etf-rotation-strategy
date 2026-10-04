"""Stage-S37 family: mfi_extreme_timing_1m -- deepens this line's
strongest volume-bearing mechanism (S33's finding that the informative
part of "volume extremes inside drawdowns" is WHERE MFI extremes occur,
not how much volume they carry: S29Q1's MFI_EXTREME_UNDERWATER_SKEW_20,
audit t 3.60, only distinguishes underwater vs above-water). This family
adds finer positional structure: relative to the day's trough/peak bar,
direction (overbought vs oversold), and time-of-day segment. Directive
2026-09-21 round_636 (S37 stage, main controller).

Note: round_570's already-registered money_flow_extremes_1m family (S15
self-directed deepening) covers directional asymmetry
(MFI_EXTREME_ASYM_20), persistence (MFI_EXTREME_STREAK_20), and a
continuous late-in-day timing skew (its own MFI_EXTREME_TOD_SKEW_20,
mean bar_index/n over extreme bars minus 0.5) -- discovered via a plan-
time canonical-hash collision on the name "MFI_EXTREME_TOD_SKEW_20"
during this round. This family's genuinely new ground vs that one is the
TROUGH/PEAK positional atoms (relative to the day's price extremes, not
relative to elapsed time) and an edge-vs-middle segment count (distinct
construction from their continuous mean-position statistic). The
directional-skew LEVEL and streak atoms originally planned here were
dropped: MFI_EXTREME_DIR_SKEW_20 (level) came back shadow-flagged in
this round's atom_health (corr=0.87 vs money_flow_extremes_1m's
MFI_EXTREME_ASYM_20 -- despite the different denominator, fraction of
extreme bars only vs all-day bars, it is not independent enough to keep
as a standalone candidate) and is computed only internally now, solely
to derive its 20d CHANGE (MFI_EXTREME_DIR_SKEW_CHG_20, corr=0.44,
independent, kept). STREAK_LEN was independently shadow-flagged in this
round's own atom_health (corr=0.94 vs MFI_EXTREME_FRAC_20) before the
TOD_SKEW collision was found, so it is removed rather than renamed.

Literature anchors:
- Quong & Soudack (1989), Money Flow Index -- the same MFI(14) definition
  already used by accumulation_distribution_1m (S10), reused verbatim
  here (extreme = MFI>80 or MFI<20, the family's own "conventional 80/20
  boundary", not a newly tuned threshold).
- Blume, Easley & O'Hara (1994) -- volume/money-flow extremes carry
  information about trader type; WHEN within the day they occur is a
  distinct dimension from how often.
- Barclay & Hendershott (2003/2004) -- price discovery/information
  content is time-varying across the trading day (motivates the
  edge-vs-middle segment atom).

Implementation (per symbol, single 1m pass per day, self-contained --
computes its own MFI(14) series, does not import
accumulation_distribution_1m or money_flow_extremes_1m): for each day,
MFI is computed exactly as in accumulation_distribution_1m._daily_bar
(typical price TP, signed raw money flow, 14-bar trailing window,
MFI=100-100/(1+pos/neg)); extreme bars = MFI>80 or MFI<20. running_peak/
drawdown as in intraday_drawdown_1m to locate trough_idx=argmax(
drawdown); peak_idx = argmax(close) locates the day's high.

Atoms:
  MFI_EXTREME_TROUGH_SKEW_20: (count of extreme bars before trough_idx -
    count after trough_idx) / total extreme-bar count that day, 20d mean.
  MFI_EXTREME_PEAK_SKEW_20: same, relative to peak_idx (the day's high).
  MFI_EXTREME_DIR_SKEW_CHG_20: 20d change of (count MFI>80 - count
    MFI<20) / total extreme-bar count (directional skew of which extreme
    dominates, among extreme bars only); the level itself is shadow-
    flagged against an existing atom (see note above) and not exposed,
    only its change.
  MFI_EXTREME_EDGE_MID_SKEW_20: (extreme-bar count in first-30min +
    last-30min segments) / total extreme count - (extreme-bar count in
    the middle segment) / total extreme count, 20d mean (edge-of-day vs
    mid-day concentration of extremes, a segment-count construction,
    distinct from money_flow_extremes_1m's continuous mean-position
    timing statistic).
Days with zero extreme bars are excluded (division undefined).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "MFI_EXTREME_TROUGH_SKEW_20",
    "MFI_EXTREME_PEAK_SKEW_20",
    "MFI_EXTREME_DIR_SKEW_CHG_20",
    "MFI_EXTREME_EDGE_MID_SKEW_20",
)

_MFI_WINDOW = 14
_EDGE_BARS = 30


def _mfi_series(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    n = len(close)
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
            continue
        ratio = pos_sum / neg_sum
        mfi[i] = 100.0 - 100.0 / (1.0 + ratio)
    return mfi


def _daily_bar(day: pd.DataFrame) -> dict:
    day = day.sort_values("datetime")
    high = day["high"].to_numpy(float)
    low = day["low"].to_numpy(float)
    close = day["close"].to_numpy(float)
    volume = day["volume"].to_numpy(float)
    n = len(close)
    if n < 30 or np.any(close <= 0):
        return {}

    mfi = _mfi_series(high, low, close, volume)
    extreme = (mfi > 80.0) | (mfi < 20.0)
    n_extreme = int(np.sum(extreme))
    if n_extreme == 0:
        return {}

    running_peak = np.maximum.accumulate(close)
    drawdown = (running_peak - close) / running_peak
    trough_idx = int(np.argmax(drawdown))
    peak_idx = int(np.argmax(close))

    extreme_idx = np.flatnonzero(extreme)
    trough_skew = float(np.sum(extreme_idx < trough_idx) - np.sum(extreme_idx > trough_idx)) / n_extreme
    peak_skew = float(np.sum(extreme_idx < peak_idx) - np.sum(extreme_idx > peak_idx)) / n_extreme

    high_ext = int(np.sum(mfi[extreme] > 80.0))
    low_ext = int(np.sum(mfi[extreme] < 20.0))
    dir_skew = float(high_ext - low_ext) / n_extreme

    edge = min(_EDGE_BARS, n // 2)
    edge_mask = np.zeros(n, dtype=bool)
    edge_mask[:edge] = True
    edge_mask[n - edge :] = True
    n_edge_extreme = int(np.sum(extreme & edge_mask))
    n_mid_extreme = n_extreme - n_edge_extreme
    edge_mid_skew = float(n_edge_extreme - n_mid_extreme) / n_extreme

    return {
        "trough_skew": trough_skew,
        "peak_skew": peak_skew,
        "dir_skew": dir_skew,
        "edge_mid_skew": edge_mid_skew,
    }


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


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    for sym in symbols:
        daily = _daily_frame(data_root, sym, as_of)
        if daily.empty:
            continue

        trough_skew_20 = daily["trough_skew"].rolling(20, min_periods=12).mean()
        peak_skew_20 = daily["peak_skew"].rolling(20, min_periods=12).mean()
        dir_skew_20 = daily["dir_skew"].rolling(20, min_periods=12).mean()  # internal only, feeds CHG below
        edge_mid_skew_20 = daily["edge_mid_skew"].rolling(20, min_periods=12).mean()

        out["MFI_EXTREME_TROUGH_SKEW_20"][sym] = trough_skew_20.reindex(dates)
        out["MFI_EXTREME_PEAK_SKEW_20"][sym] = peak_skew_20.reindex(dates)
        out["MFI_EXTREME_DIR_SKEW_CHG_20"][sym] = (dir_skew_20 - dir_skew_20.shift(20)).reindex(dates)
        out["MFI_EXTREME_EDGE_MID_SKEW_20"][sym] = edge_mid_skew_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("mfi_extreme_timing_1m", "mfi_extreme_timing_1m", _build))
