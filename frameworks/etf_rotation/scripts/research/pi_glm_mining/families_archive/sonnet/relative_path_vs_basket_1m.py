"""Stage-S15 family (controller-specified 2026-09-20 20:03, round_571):
relative_path_vs_basket_1m -- the same intraday path-geometry constructs
S7 (drawdown) and S6 (permutation entropy) validated on the ABSOLUTE
price path, reapplied to the ACTIVE return path (asset minus 14-ETF
basket proxy), per Grinold-Kahn active-return framing. Note: this line's
round_570 explored a separate, self-directed "S15" (money_flow_extremes_1m,
deepening S10) before the controller issued this official S15 spec in the
same turn; that round_570 work stands as its own completed stage (its
STATUS.json/REPORT.md retain the label S15_money_flow_extremes_1m) and is
NOT the same stage as this one. This family is the controller's actual
S15.

Literature anchors:
- Grinold & Kahn, "Active Portfolio Management" -- active return
  (asset return minus benchmark/basket return) as the object of interest
  for a manager evaluated relative to a benchmark; active-return paths
  can be analyzed with the same drawdown/efficiency tools used for
  absolute price paths.
- Chekhlov, Uryasev & Zabarankin (2005), CDaR -- reapplied here to the
  cumulative ACTIVE return path (peak-to-current drawdown in active-
  return space) rather than absolute price, following this line's S7
  precedent.
- Bandt & Pompe (2002) -- permutation entropy reapplied to the ACTIVE
  1m return series (not the absolute return series S6 already covers).
- Kaufman (1995)-style efficiency ratio (this line's existing
  `path_efficiency` family precedent, reapplied to the active path):
  |net displacement| / path length, in active-return units.

Implementation (practitioner proxy; reuses this line's established
510300.SH/510500.SH basket-proxy convention from S4/S8/S13's
jump_continuous_beta.py/frequency_domain_beta_1m.py, self-contained
recomputation per this line's no-cross-family-import convention): within
each trading day, using 1m simple returns r_i (asset) and r_m,i (basket
proxy, mean of the two benchmark ETFs' 1m returns):
  Active return ar_i = r_i - r_m,i. Cumulative active path L_i =
    cumsum(ar), L_0=0 (day-anchored). Peak_i = running max of L (from
    L_0); Drawdown_i = Peak_i - L_i (additive, active-return units).
  REL_MAXDD_20 / REL_MAXDD_CHG_20 = 20d mean / 20d change of the day's
    max(Drawdown).
  REL_UNDERWATER_FRAC_20 / REL_UNDERWATER_FRAC_CHG_20 = 20d mean / 20d
    change of the day's fraction of bars with Drawdown>0.
  REL_RECOVERY_FRAC_20: using the day's single largest active-drawdown
    episode (trough t*=argmax(Drawdown), preceding peak p*, first
    recovery index r*>t* where L_r*>=Peak_p*; unrecovered by day-end=1.0,
    exact construction mirroring S12's RECOVERY_TIME_FRAC_20), 20d mean.
  REL_PERM_ENTROPY_20: Bandt-Pompe (d=3, delay=1) permutation entropy of
    the raw active-return series ar_i (not the cumulative path), 20d
    mean.
  REL_PATH_EFFICIENCY_20 = |L_n| / sum(|ar_i|) (guarded denominator>0),
    20d mean.
  UNDERWATER_FRAC_DIFF_20 = 20d mean of daily(absolute_underwater_frac -
    active_underwater_frac), where absolute_underwater_frac uses the
    same drawdown construction on the raw price path (peak of close,
    fractional drawdown, matching S7's UNDERWATER_FRAC_20 convention,
    self-contained recomputation) -- the share of the day's underwater
    time attributable to the basket rather than idiosyncratic moves.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ROLL_WINDOW = 20
MIN_BARS_PER_DAY = 120

ATOM_NAMES = (
    "REL_UNDERWATER_FRAC_20",
    "REL_UNDERWATER_FRAC_CHG_20",
    "REL_MAXDD_20",
    "REL_MAXDD_CHG_20",
    "REL_RECOVERY_FRAC_20",
    "REL_PERM_ENTROPY_20",
    "REL_PATH_EFFICIENCY_20",
    "UNDERWATER_FRAC_DIFF_20",
)

_EMBED_DIM = 3
_N_STATES = math.factorial(_EMBED_DIM)
_PATTERNS = {p: i for i, p in enumerate(itertools.permutations(range(_EMBED_DIM)))}
_LOG_N_STATES = math.log(_N_STATES)


def _market_return_series(data_root, benchmark_symbols, frequency, as_of) -> pd.Series:
    legs = []
    for sym in benchmark_symbols:
        try:
            frame, _ = _read_complete_days(data_root, sym, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        frame = frame.sort_values("datetime")[["datetime", "close"]].copy()
        frame["ret"] = frame["close"].pct_change()
        legs.append(frame.set_index("datetime")["ret"])
    if not legs:
        return pd.Series(dtype=float)
    return pd.concat(legs, axis=1).mean(axis=1, skipna=True)


def _permutation_entropy(values: np.ndarray) -> float:
    n = len(values)
    d = _EMBED_DIM
    if n < d + 1:
        return float("nan")
    counts = np.zeros(_N_STATES)
    for i in range(n - d + 1):
        window = values[i : i + d]
        order = tuple(np.argsort(np.argsort(window, kind="stable")))
        counts[_PATTERNS[order]] += 1
    total = counts.sum()
    if total <= 0:
        return float("nan")
    p = counts[counts > 0] / total
    return float(-np.sum(p * np.log(p)) / _LOG_N_STATES)


def _drawdown_recovery_frac(levels: np.ndarray) -> tuple[float, float, float]:
    """Given a cumulative level path (L_0=0 prepended), return
    (max_drawdown, underwater_frac, recovery_frac) using S12's episode
    construction (single largest-drawdown episode)."""
    peak = np.maximum.accumulate(levels)
    dd = peak - levels
    n = len(levels)
    max_dd = float(np.max(dd))
    underwater_frac = float(np.mean(dd > 0))
    if max_dd <= 0:
        return max_dd, underwater_frac, 0.0
    t_star = int(np.argmax(dd))
    peak_before = peak[: t_star + 1]
    p_star = int(np.where(peak_before == peak_before[-1])[0][0])
    peak_value = float(peak[p_star])
    recovered_idx = np.where(levels[t_star + 1 :] >= peak_value)[0]
    if len(recovered_idx) > 0:
        r_star = t_star + 1 + int(recovered_idx[0])
        recovery_frac = (r_star - t_star) / (n - 1)
    else:
        recovery_frac = 1.0
    return max_dd, underwater_frac, float(recovery_frac)


def _day_relative_path_features(day: pd.DataFrame, mkt_ret: pd.Series) -> dict | None:
    close = day["close"].to_numpy(float)
    open0 = float(day["open"].to_numpy(float)[0])
    times = day["datetime"]
    m = mkt_ret.reindex(times).to_numpy(float)
    prev = np.concatenate([[open0], close[:-1]])
    with np.errstate(all="ignore"):
        r = close / np.where(prev > 0, prev, np.nan) - 1.0
    finite = np.isfinite(r) & np.isfinite(m)
    n_ok = int(finite.sum())
    if n_ok < MIN_BARS_PER_DAY:
        return None
    r_ok = r[finite]
    m_ok = m[finite]
    ar = r_ok - m_ok

    levels = np.concatenate([[0.0], np.cumsum(ar)])
    max_dd, underwater_frac, recovery_frac = _drawdown_recovery_frac(levels)

    path_len = float(np.sum(np.abs(ar)))
    path_eff = float(abs(levels[-1]) / path_len) if path_len > 0 else float("nan")

    perm_entropy = _permutation_entropy(ar)

    abs_peak = np.maximum.accumulate(close)
    with np.errstate(all="ignore"):
        abs_dd = (abs_peak - close) / abs_peak
    abs_underwater_frac = float(np.mean(abs_dd[finite] > 0)) if finite.any() else float("nan")

    return {
        "max_dd": max_dd,
        "underwater_frac": underwater_frac,
        "recovery_frac": recovery_frac,
        "perm_entropy": perm_entropy,
        "path_eff": path_eff,
        "underwater_diff": abs_underwater_frac - underwater_frac,
    }


def _build_relative_path(panels, eligibility, data_root, config):
    close = panels["close"]
    dates = close.index
    frequency = str(config.get("frequency", "1m"))
    benchmark_symbols = list(config["benchmark_symbols"])
    as_of = dates.max()
    root = data_root
    out = {name: pd.DataFrame(np.nan, index=dates, columns=close.columns) for name in ATOM_NAMES}

    mkt_ret = _market_return_series(root, benchmark_symbols, frequency, as_of)
    if mkt_ret.empty:
        return out

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
            feats = _day_relative_path_features(day, mkt_ret)
            if feats is not None:
                feats["date"] = date
                records.append(feats)
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date").sort_index()

        uf_20 = daily["underwater_frac"].rolling(ROLL_WINDOW, min_periods=10).mean()
        out["REL_UNDERWATER_FRAC_20"][sym] = uf_20.reindex(dates)
        out["REL_UNDERWATER_FRAC_CHG_20"][sym] = (uf_20 - uf_20.shift(ROLL_WINDOW)).reindex(dates)

        dd_20 = daily["max_dd"].rolling(ROLL_WINDOW, min_periods=10).mean()
        out["REL_MAXDD_20"][sym] = dd_20.reindex(dates)
        out["REL_MAXDD_CHG_20"][sym] = (dd_20 - dd_20.shift(ROLL_WINDOW)).reindex(dates)

        out["REL_RECOVERY_FRAC_20"][sym] = (
            daily["recovery_frac"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["REL_PERM_ENTROPY_20"][sym] = (
            daily["perm_entropy"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["REL_PATH_EFFICIENCY_20"][sym] = (
            daily["path_eff"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["UNDERWATER_FRAC_DIFF_20"][sym] = (
            daily["underwater_diff"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
    return out


register_family(
    FamilyProvider("relative_path_vs_basket_1m", "relative_path_vs_basket_1m", _build_relative_path)
)
