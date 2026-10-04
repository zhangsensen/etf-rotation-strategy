"""Stage-S7 family: intraday_drawdown_1m -- intraday drawdown path
structure from the 1m price path, directive 2026-09-20 round_545 (S7
stage, main controller, pre-specified direction).

Literature anchors:
- Magdon-Ismail & Atiya (2004), "Maximum Drawdown", Risk Magazine --
  distributional properties of the maximum peak-to-trough decline within
  a finite path; applied here to the intraday 1m price path rather than
  the usual daily-return path.
- Chekhlov, Uryasev & Zabarankin (2005), "Drawdown Measure in Portfolio
  Optimization" -- Conditional Drawdown-at-Risk (CDaR), the average of
  the worst-quantile drawdowns along the path, applied here to the
  intraday 1m drawdown series (worst 20% of bars by drawdown depth).
- Grossman & Zhou (1993), "Optimal Investment Strategies for Controlling
  Drawdowns" -- underwater-time framing (fraction of the path spent below
  the running peak) as a distinct risk dimension from drawdown depth
  itself.

Implementation (practitioner proxy, consistent with this line's existing
1m conventions): within each trading day, using 1m close prices:
  running_peak_t = cummax(price_1..t); drawdown_t = (peak_t - price_t) / peak_t
  running_trough_t = cummin(price_1..t); runup_t = (price_t - trough_t) / trough_t
  max_drawdown = max(drawdown_t); max_runup = max(runup_t)
  underwater_frac = fraction of bars with drawdown_t > 0
  cdar = mean of drawdown_t over the worst 20% of bars by drawdown_t
  trough_timing = argmax(drawdown_t) / (n_bars - 1), in [0,1] (0=open,
    1=close), the intraday position where the deepest drawdown occurs
All daily statistics are rolled to a 20-day mean (or 20-day change for
two of them), never using same-day-or-later information beyond the day
itself.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "INTRADAY_MAXDD_20",
    "INTRADAY_MAXRUNUP_20",
    "DD_RUNUP_ASYM_20",
    "UNDERWATER_FRAC_20",
    "INTRADAY_CDAR_20",
    "DD_TROUGH_TIMING_20",
    "INTRADAY_MAXDD_CHG_20",
    "UNDERWATER_FRAC_CHG_20",
)

_CDAR_QUANTILE = 0.20


def _daily_drawdown_stats(prices: np.ndarray) -> dict:
    n = len(prices)
    if n < 5:
        return {}
    running_peak = np.maximum.accumulate(prices)
    running_trough = np.minimum.accumulate(prices)
    drawdown = (running_peak - prices) / running_peak
    runup = (prices - running_trough) / running_trough

    max_dd = float(np.max(drawdown))
    max_runup = float(np.max(runup))
    underwater_frac = float(np.mean(drawdown > 0))

    k = max(1, int(np.ceil(n * _CDAR_QUANTILE)))
    worst_dd = np.sort(drawdown)[-k:]
    cdar = float(np.mean(worst_dd))

    trough_idx = int(np.argmax(drawdown))
    trough_timing = trough_idx / (n - 1) if n > 1 else 0.5

    return {
        "max_dd": max_dd,
        "max_runup": max_runup,
        "underwater_frac": underwater_frac,
        "cdar": cdar,
        "trough_timing": trough_timing,
    }


def _daily_drawdown_frame(data_root, sym, as_of) -> pd.DataFrame:
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
        prices = day["close"].to_numpy(float)
        prices = prices[np.isfinite(prices) & (prices > 0)]
        stats = _daily_drawdown_stats(prices)
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
        daily = _daily_drawdown_frame(data_root, sym, as_of)
        if daily.empty:
            continue

        max_dd_20 = daily["max_dd"].rolling(20, min_periods=12).mean()
        max_runup_20 = daily["max_runup"].rolling(20, min_periods=12).mean()
        underwater_frac_20 = daily["underwater_frac"].rolling(20, min_periods=12).mean()
        cdar_20 = daily["cdar"].rolling(20, min_periods=12).mean()
        trough_timing_20 = daily["trough_timing"].rolling(20, min_periods=12).mean()
        dd_runup_asym_20 = max_dd_20 - max_runup_20

        out["INTRADAY_MAXDD_20"][sym] = max_dd_20.reindex(dates)
        out["INTRADAY_MAXRUNUP_20"][sym] = max_runup_20.reindex(dates)
        out["DD_RUNUP_ASYM_20"][sym] = dd_runup_asym_20.reindex(dates)
        out["UNDERWATER_FRAC_20"][sym] = underwater_frac_20.reindex(dates)
        out["INTRADAY_CDAR_20"][sym] = cdar_20.reindex(dates)
        out["DD_TROUGH_TIMING_20"][sym] = trough_timing_20.reindex(dates)
        out["INTRADAY_MAXDD_CHG_20"][sym] = (max_dd_20 - max_dd_20.shift(20)).reindex(dates)
        out["UNDERWATER_FRAC_CHG_20"][sym] = (
            underwater_frac_20 - underwater_frac_20.shift(20)
        ).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("intraday_drawdown_1m", "intraday_drawdown_1m", _build))
