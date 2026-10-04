"""Stage-S15 family: money_flow_extremes_1m -- structure of intraday
Money Flow Index (MFI) extreme readings, directive 2026-09-21 round_570
(S15 stage, self-directed deepening of this line's single strongest
finding, S10's `MFI_EXTREME_FRAC_20 x DEP_DRIFT_20` (NI8, discovery
block-t=4.88, audit +27.7bp -- the highest block-t recorded anywhere in
this mining line, higher than S6's PA1 seed for S11 or S7's QA8 seed for
S12). Process note: round_570 initially and mistakenly re-registered
S10 (`accumulation_distribution_1m`) as though it were an unstarted
stage -- this line's own history (outputs/round_540/RETROSPECTIVE.md)
shows S10 actually closed in round_540, well before the current
conversation window began, with 5 net admissions including NI8. The
controller directive's repeated inclusion of the S10 block in every
turn's cumulative text was legacy/reference text, not a re-activation
signal. This family instead deepens the highest-value channel S10
actually found, mirroring how S11 deepened S6 and S12 deepened S7.

Literature anchors:
- Quong & Soudack (1989), Money Flow Index -- the base construct being
  deepened; this family decomposes "extreme reading frequency" (S10's
  single pooled two-tail measure) into direction, persistence, timing,
  volume-weight and forward-reversal-quality facets.
- Wilder (1978), New Concepts in Technical Trading Systems -- the RSI/
  extreme-oscillator literature's core claim is that PERSISTENCE and
  eventual REVERSAL of extreme readings, not just their frequency, carry
  the signal; motivates the streak, reversal-hit-rate and asymmetry atoms.
- Admati & Pfleiderer (1988), "A Theory of Intraday Patterns: Volume and
  Price Variability", RFS -- informed/discretionary trading concentrates
  at specific times of day; motivates the time-of-day skew atom (are MFI
  extremes clustering near the open, close, or spread through the day).
- Easley, Kiefer, O'Hara & Paperman (1996), PIN -- volume concentration
  on informed-trading days/bars as an information-content proxy;
  motivates the volume-weighted extreme-bar concentration atom (are
  extreme-MFI bars also the bars carrying most of the day's volume).

Implementation (practitioner proxy, self-contained recomputation of the
S10 base construct -- consistent with this line's convention of not
importing across family modules): within each trading day, using 1m
OHLCV bars, recompute the same trailing-14-bar intraday MFI series as
S10's `accumulation_distribution_1m` family (typical price TP=(H+L+C)/3,
raw money flow=TP*volume, MFI_i = 100-100/(1+pos_14/neg_14)), then:
  MFI_EXTREME_HI_FRAC_20 / MFI_EXTREME_LO_FRAC_20 = 20d mean of the
    day's fraction of bars with MFI>80 / MFI<20 (S10 pooled both tails
    into one atom; this splits them).
  MFI_EXTREME_ASYM_20 = 20d mean of daily(HI_frac - LO_frac) (net
    directional extreme bias).
  MFI_EXTREME_STREAK_20 = 20d mean of the day's longest consecutive-
    extreme-bar run, as a fraction of the day's bar count (persistence).
  MFI_EXTREME_TOD_SKEW_20 = 20d mean of the day's mean(bar_index/n) over
    extreme bars minus 0.5 (positive = extremes cluster late in the day).
  MFI_EXTREME_FRAC_CHG_20 = 20-day change of S10's own
    MFI_EXTREME_FRAC_20-equivalent (both tails pooled), recomputed here
    for self-containment.
  MFI_REVERSAL_HITRATE_20 = 20d mean of the day's fraction of extreme
    bars (with >=5 bars of same-day room remaining) whose subsequent
    5-bar return sign is OPPOSITE the extreme's direction (a realized
    reversal), among days with >=1 qualifying extreme bar.
  MFI_EXTREME_VOL_CONC_20 = 20d mean of (volume on extreme-MFI bars) /
    (total day volume).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ROLL_WINDOW = 20
MFI_WINDOW = 14
MFI_HI = 80.0
MFI_LO = 20.0
REVERSAL_HORIZON = 5

ATOM_NAMES = (
    "MFI_EXTREME_HI_FRAC_20",
    "MFI_EXTREME_LO_FRAC_20",
    "MFI_EXTREME_ASYM_20",
    "MFI_EXTREME_STREAK_20",
    "MFI_EXTREME_TOD_SKEW_20",
    "MFI_EXTREME_FRAC_CHG_20",
    "MFI_REVERSAL_HITRATE_20",
    "MFI_EXTREME_VOL_CONC_20",
)


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
        start = max(0, i - MFI_WINDOW + 1)
        pos_sum = pos_flow[start : i + 1].sum()
        neg_sum = neg_flow[start : i + 1].sum()
        if neg_sum <= 0:
            mfi[i] = 100.0 if pos_sum > 0 else 50.0
        else:
            mfi[i] = 100.0 - 100.0 / (1.0 + pos_sum / neg_sum)
    return mfi


def _longest_streak(mask: np.ndarray) -> int:
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def _day_extreme_features(day: pd.DataFrame) -> dict | None:
    high = day["high"].to_numpy(float)
    low = day["low"].to_numpy(float)
    close = day["close"].to_numpy(float)
    volume = day["volume"].to_numpy(float)
    n = len(close)
    if n < 120 or not np.all(np.isfinite(volume)) or not np.all(volume >= 0):
        return None
    total_vol = float(volume.sum())
    if total_vol <= 0:
        return None

    mfi = _mfi_series(high, low, close, volume)
    hi_mask = mfi > MFI_HI
    lo_mask = mfi < MFI_LO
    extreme_mask = hi_mask | lo_mask

    hi_frac = float(np.mean(hi_mask))
    lo_frac = float(np.mean(lo_mask))
    extreme_frac = float(np.mean(extreme_mask))
    asym = hi_frac - lo_frac
    streak_frac = _longest_streak(extreme_mask) / n

    idx_frac = np.arange(n, dtype=float) / max(n - 1, 1)
    tod_skew = float(np.mean(idx_frac[extreme_mask]) - 0.5) if extreme_mask.any() else float("nan")

    extreme_vol_conc = float(volume[extreme_mask].sum() / total_vol) if extreme_mask.any() else 0.0

    hits = []
    ext_idx = np.where(extreme_mask)[0]
    for i in ext_idx:
        if i + REVERSAL_HORIZON >= n:
            continue
        direction = 1.0 if hi_mask[i] else -1.0
        fut_ret = close[i + REVERSAL_HORIZON] / close[i] - 1.0
        if not np.isfinite(fut_ret) or fut_ret == 0:
            continue
        hits.append(1.0 if np.sign(fut_ret) == -direction else 0.0)
    reversal_hitrate = float(np.mean(hits)) if hits else float("nan")

    return {
        "hi_frac": hi_frac,
        "lo_frac": lo_frac,
        "asym": asym,
        "extreme_frac": extreme_frac,
        "streak_frac": streak_frac,
        "tod_skew": tod_skew,
        "extreme_vol_conc": extreme_vol_conc,
        "reversal_hitrate": reversal_hitrate,
    }


def _build_money_flow_extremes(panels, eligibility, data_root, config):
    close = panels["close"]
    dates = close.index
    frequency = str(config.get("frequency", "1m"))
    as_of = dates.max()
    root = Path(data_root)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=close.columns) for name in ATOM_NAMES}
    for sym in close.columns:
        try:
            frame, _ = _read_complete_days(root, sym, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        frame = frame.copy()
        frame["date"] = frame["datetime"].dt.normalize()
        records = []
        for date, day in frame.groupby("date", sort=True):
            feats = _day_extreme_features(day)
            if feats is not None:
                feats["date"] = date
                records.append(feats)
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date").sort_index()

        out["MFI_EXTREME_HI_FRAC_20"][sym] = (
            daily["hi_frac"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["MFI_EXTREME_LO_FRAC_20"][sym] = (
            daily["lo_frac"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["MFI_EXTREME_ASYM_20"][sym] = (
            daily["asym"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["MFI_EXTREME_STREAK_20"][sym] = (
            daily["streak_frac"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["MFI_EXTREME_TOD_SKEW_20"][sym] = (
            daily["tod_skew"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        extreme_frac_20 = daily["extreme_frac"].rolling(ROLL_WINDOW, min_periods=10).mean()
        out["MFI_EXTREME_FRAC_CHG_20"][sym] = (
            extreme_frac_20 - extreme_frac_20.shift(ROLL_WINDOW)
        ).reindex(dates)
        out["MFI_REVERSAL_HITRATE_20"][sym] = (
            daily["reversal_hitrate"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["MFI_EXTREME_VOL_CONC_20"][sym] = (
            daily["extreme_vol_conc"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
    return out


register_family(
    FamilyProvider("money_flow_extremes_1m", "money_flow_extremes_1m", _build_money_flow_extremes)
)
