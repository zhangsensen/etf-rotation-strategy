"""Stage-S12 family: intraday_pain_recovery_1m -- ulcer/pain index and
drawdown-recovery structure of the 1m intraday path, directive
2026-09-20 round_561 (S12 stage, main controller, pre-specified
direction, deepening the S7 channel: UNDERWATER_FRAC_CHG_20 was this
line's highest audit-excess single atom, +60.6bp / t 2.88, five years all
positive, volume-free).

Literature anchors:
- Martin & McCann (1989), the Ulcer Index -- sqrt(mean(drawdown_i^2)),
  a root-mean-square drawdown measure that penalizes deep drawdowns more
  than shallow ones (unlike the plain mean-absolute pain index below).
- Zephyr Associates' Pain Index -- mean(|drawdown_i|), the linear
  (non-squared) counterpart to the Ulcer Index; the ratio/difference
  between the two indicates drawdown severity concentration (UI >> PI
  means a few deep drawdowns dominate; UI ~ PI means drawdowns are
  uniformly shallow).
- Magdon-Ismail & Atiya (2004), maximum drawdown distribution -- the
  single largest peak-to-trough episode within the day is the anchor for
  the recovery-time and speed constructs below.
- Grossman & Zhou (1993), drawdown-constrained portfolio choice -- the
  time a path spends "underwater" (below its running peak) is treated as
  economically distinct from the drawdown's depth.
- Bacon (2008), "Practical Portfolio Performance Measurement and
  Attribution" -- recovery-time / recovery-speed as a distinct
  performance-measurement dimension from drawdown depth itself.

Implementation (practitioner proxy, consistent with this line's existing
1m conventions, e.g. intraday_drawdown_1m.py's per-day-then-rolling-mean
pattern): within each trading day, using the 1m close price path p_i
(open-anchored, PIT within the day), running peak P_i = cummax(p_i),
fractional drawdown dd_i = (P_i - p_i) / P_i:
  ULCER_INDEX_20 = 20d mean of sqrt(mean_i(dd_i^2))  [per-day RMS drawdown]
  PAIN_INDEX_20 = 20d mean of mean_i(dd_i)            [per-day mean drawdown]
  ULCER_INDEX_CHG_20 / PAIN_INDEX_CHG_20 = 20-day change of the above.
  Single-episode recovery construct, anchored on the day's global trough
  t* = argmax(dd_i), preceding peak index p* (last index with dd=0 before
  t*), and the first index r* > t* (if any) where p_i >= P_{p*} (full
  recovery to the pre-drawdown high):
    RECOVERY_TIME_FRAC_20 = 20d mean of (r*-t*)/n if recovered, else 1.0
      (unrecovered by day-end is coded as the worst-case value 1.0, per
      directive).
    dd_speed = (P_{p*} - p_{t*}) / max(t*-p*, 1)  [price drop per bar,
      peak to trough]
    recovery_speed = (P_{p*}-p_{t*})/max(r*-t*,1) if recovered, else
      (p_{n-1}-p_{t*})/max(n-1-t*,1)  [partial-recovery speed using the
      day's remaining bars if the trough is never fully recovered]
    DD_RECOVERY_SPEED_RATIO_20 = 20d mean of dd_speed / recovery_speed
      (guarded recovery_speed>0).
  UNDERWATER_FRAC_Z_60: daily underwater_frac = fraction of bars with
    dd_i>0 (self-contained recomputation, same definition as S7's
    UNDERWATER_FRAC_20 but not importing across family modules); 60-day
    rolling z-score of the raw daily series (same convention as
    etf_fund_data_families.py's SHARE_Z_60).
  RECOVERY_TIME_FRAC_CHG_20 = 20-day change of RECOVERY_TIME_FRAC_20.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ROLL_WINDOW = 20
Z_WINDOW = 60

ATOMS = (
    "ULCER_INDEX_20",
    "PAIN_INDEX_20",
    "ULCER_INDEX_CHG_20",
    "PAIN_INDEX_CHG_20",
    "RECOVERY_TIME_FRAC_20",
    "DD_RECOVERY_SPEED_RATIO_20",
    "UNDERWATER_FRAC_Z_60",
    "RECOVERY_TIME_FRAC_CHG_20",
)


def _day_pain_recovery_features(day: pd.DataFrame) -> dict | None:
    close = day["close"].to_numpy(float)
    open0 = float(day["open"].to_numpy(float)[0])
    prices = np.concatenate([[open0], close])
    n = len(prices)
    if n < 60 or not np.all(np.isfinite(prices)) or not np.all(prices > 0):
        return None

    peak = np.maximum.accumulate(prices)
    with np.errstate(all="ignore"):
        dd = (peak - prices) / peak
    if not np.all(np.isfinite(dd)):
        return None

    ulcer = float(np.sqrt(np.mean(dd**2)))
    pain = float(np.mean(dd))
    underwater_frac = float(np.mean(dd > 0))

    t_star = int(np.argmax(dd))
    if dd[t_star] <= 0:
        return {
            "ulcer": ulcer,
            "pain": pain,
            "underwater_frac": underwater_frac,
            "recovery_frac": 0.0,
            "speed_ratio": float("nan"),
        }
    peak_before = peak[: t_star + 1]
    p_star_candidates = np.where(peak_before == peak_before[-1])[0]
    p_star = int(p_star_candidates[0])
    peak_value = float(peak[p_star])
    trough_price = float(prices[t_star])
    dd_amount = peak_value - trough_price
    dd_bars = max(t_star - p_star, 1)
    dd_speed = dd_amount / dd_bars

    recovered_idx = np.where(prices[t_star + 1 :] >= peak_value)[0]
    if len(recovered_idx) > 0:
        r_star = t_star + 1 + int(recovered_idx[0])
        recovery_frac = (r_star - t_star) / (n - 1)
        recovery_amount = dd_amount
        recovery_bars = max(r_star - t_star, 1)
    else:
        recovery_frac = 1.0
        recovery_amount = float(prices[-1] - trough_price)
        recovery_bars = max((n - 1) - t_star, 1)

    with np.errstate(all="ignore"):
        recovery_speed = recovery_amount / recovery_bars if recovery_amount > 0 else np.nan
        speed_ratio = dd_speed / recovery_speed if recovery_speed and recovery_speed > 0 else np.nan

    return {
        "ulcer": ulcer,
        "pain": pain,
        "underwater_frac": underwater_frac,
        "recovery_frac": float(recovery_frac),
        "speed_ratio": float(speed_ratio) if np.isfinite(speed_ratio) else float("nan"),
    }


def _build_pain_recovery(panels, eligibility, data_root, config):
    close = panels["close"]
    dates = close.index
    frequency = str(config.get("frequency", "1m"))
    as_of = dates.max()
    root = Path(data_root)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=close.columns) for name in ATOMS}
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
            feats = _day_pain_recovery_features(day)
            if feats is not None:
                feats["date"] = date
                records.append(feats)
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date").sort_index()

        ulcer_20 = daily["ulcer"].rolling(ROLL_WINDOW, min_periods=10).mean()
        pain_20 = daily["pain"].rolling(ROLL_WINDOW, min_periods=10).mean()
        out["ULCER_INDEX_20"][sym] = ulcer_20.reindex(dates)
        out["PAIN_INDEX_20"][sym] = pain_20.reindex(dates)
        out["ULCER_INDEX_CHG_20"][sym] = (ulcer_20 - ulcer_20.shift(ROLL_WINDOW)).reindex(dates)
        out["PAIN_INDEX_CHG_20"][sym] = (pain_20 - pain_20.shift(ROLL_WINDOW)).reindex(dates)

        recovery_frac_20 = daily["recovery_frac"].rolling(ROLL_WINDOW, min_periods=10).mean()
        out["RECOVERY_TIME_FRAC_20"][sym] = recovery_frac_20.reindex(dates)
        out["RECOVERY_TIME_FRAC_CHG_20"][sym] = (
            recovery_frac_20 - recovery_frac_20.shift(ROLL_WINDOW)
        ).reindex(dates)
        out["DD_RECOVERY_SPEED_RATIO_20"][sym] = (
            daily["speed_ratio"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )

        uf = daily["underwater_frac"]
        mu60 = uf.rolling(Z_WINDOW, min_periods=30).mean()
        sd60 = uf.rolling(Z_WINDOW, min_periods=30).std()
        out["UNDERWATER_FRAC_Z_60"][sym] = ((uf - mu60) / sd60).reindex(dates)
    return out


register_family(
    FamilyProvider("intraday_pain_recovery_1m", "intraday_pain_recovery_1m", _build_pain_recovery)
)
