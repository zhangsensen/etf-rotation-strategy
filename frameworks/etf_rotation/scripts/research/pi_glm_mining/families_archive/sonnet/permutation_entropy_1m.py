"""Stage-S6 family: permutation_entropy_1m -- ordinal-pattern complexity of
the 1m return and volume sequences, directive 2026-09-20 round_541 (S6
stage, main controller, pre-specified direction).

Literature anchors:
- Bandt & Pompe (2002), "Permutation Entropy: A Natural Complexity Measure
  for Time Series", Physical Review Letters -- for embedding dimension d
  (here d=3, delay=1), every window of d consecutive values is mapped to
  its ordinal (rank) pattern; the Shannon entropy of the resulting
  pattern distribution, normalized by log(d!), measures how random
  (H->1) vs. structured/predictable (H->0) the sequence is.
- Rosso, Larrondo, Martin, Plastino & Fuentes (2007), "Distinguishing
  Noise from Chaos", Physical Review Letters -- statistical complexity
  C_JS = Q_J[P,Pe] * H_norm, the product of normalized permutation
  entropy and the Jensen-Shannon disequilibrium between the observed
  ordinal-pattern distribution P and the uniform distribution Pe; C_JS is
  near zero for both pure noise (H~1) and perfectly periodic/deterministic
  sequences (H~0), peaking at intermediate structured-but-not-trivial
  dynamics.
- Zunino, Zanin, Tabak & Perez-Rosso (2010), "Complexity-entropy causality
  plane: a useful approach to quantify the stock market inefficiency" --
  the (H, C) plane position for a market series relative to the
  white-noise point (H=1, C=0) is used directly as an inefficiency proxy
  (distance from that point summarizes joint entropy+complexity
  deviation from pure randomness).

Implementation (practitioner proxy, consistent with this line's existing
1m conventions): within each trading day, using the day's 1m close-to-
close returns (and separately, 1m volumes), embedding dimension d=3,
delay=1: every consecutive triple is mapped to one of 3!=6 ordinal
patterns (ties broken by index order); the observed pattern-frequency
distribution P gives H_norm = -sum(p*ln(p))/ln(6) and the Rosso et al.
statistical complexity C_JS = Q0 * J[P,Pe] * H_norm, where J is the
Jensen-Shannon divergence between P and the uniform Pe, and Q0 is the
Lamberti et al. (2004) normalization constant for N=6. All daily
statistics are rolled to a 20-day mean (or 20-day change for three of
them), never using same-day-or-later information beyond the day itself.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "PERM_ENTROPY_RET_20",
    "STAT_COMPLEXITY_20",
    "CEP_DISTANCE_20",
    "PERM_ENTROPY_VOL_20",
    "ENTROPY_RET_VOL_DIFF_20",
    "PERM_ENTROPY_RET_CHG_20",
    "STAT_COMPLEXITY_CHG_20",
    "PERM_ENTROPY_VOL_CHG_20",
)

_EMBED_DIM = 3
_N_STATES = math.factorial(_EMBED_DIM)
_PATTERNS = {p: i for i, p in enumerate(itertools.permutations(range(_EMBED_DIM)))}
_LOG_N = math.log(_N_STATES)


def _q0_constant(n: int) -> float:
    term = ((n + 1) / n) * math.log(n + 1) - 2 * math.log(2 * n) + math.log(n)
    return -2.0 / term


_Q0 = _q0_constant(_N_STATES)


def _ordinal_pattern_counts(values: np.ndarray) -> np.ndarray:
    n = len(values)
    d = _EMBED_DIM
    if n < d:
        return np.zeros(_N_STATES)
    counts = np.zeros(_N_STATES)
    for i in range(n - d + 1):
        window = values[i : i + d]
        order = tuple(np.argsort(np.argsort(window, kind="stable")))
        counts[_PATTERNS[order]] += 1
    return counts


def _entropy_and_complexity(counts: np.ndarray) -> tuple[float, float]:
    total = counts.sum()
    if total <= 0:
        return np.nan, np.nan
    p = counts / total
    nz = p > 0
    h = float(-np.sum(p[nz] * np.log(p[nz])))
    h_norm = h / _LOG_N

    pe = np.full(_N_STATES, 1.0 / _N_STATES)
    p_mix = (p + pe) / 2.0
    s_mix = float(-np.sum(p_mix[p_mix > 0] * np.log(p_mix[p_mix > 0])))
    s_p = h
    s_pe = _LOG_N
    j_div = s_mix - s_p / 2.0 - s_pe / 2.0
    c_js = _Q0 * j_div * h_norm
    return h_norm, c_js


def _daily_series(frame: pd.DataFrame, column: str, use_returns: bool) -> np.ndarray:
    values = frame[column].to_numpy(float)
    if use_returns:
        values = np.diff(values) / values[:-1]
    return values[np.isfinite(values)]


def _daily_pe_frame(data_root, sym, as_of) -> pd.DataFrame:
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
        ret = _daily_series(day, "close", use_returns=True)
        vol = _daily_series(day, "volume", use_returns=False)
        if len(ret) < _EMBED_DIM + 5 or len(vol) < _EMBED_DIM + 5:
            continue
        h_ret, c_ret = _entropy_and_complexity(_ordinal_pattern_counts(ret))
        h_vol, c_vol = _entropy_and_complexity(_ordinal_pattern_counts(vol))
        if not (np.isfinite(h_ret) and np.isfinite(h_vol)):
            continue
        recs.append(
            {
                "date": date,
                "h_ret": h_ret,
                "c_ret": c_ret,
                "h_vol": h_vol,
            }
        )
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    for sym in symbols:
        daily = _daily_pe_frame(data_root, sym, as_of)
        if daily.empty:
            continue

        h_ret_20 = daily["h_ret"].rolling(20, min_periods=12).mean()
        c_ret_20 = daily["c_ret"].rolling(20, min_periods=12).mean()
        h_vol_20 = daily["h_vol"].rolling(20, min_periods=12).mean()
        cep_dist_20 = np.sqrt((1.0 - h_ret_20) ** 2 + c_ret_20**2)
        ret_vol_diff_20 = h_ret_20 - h_vol_20

        out["PERM_ENTROPY_RET_20"][sym] = h_ret_20.reindex(dates)
        out["STAT_COMPLEXITY_20"][sym] = c_ret_20.reindex(dates)
        out["CEP_DISTANCE_20"][sym] = cep_dist_20.reindex(dates)
        out["PERM_ENTROPY_VOL_20"][sym] = h_vol_20.reindex(dates)
        out["ENTROPY_RET_VOL_DIFF_20"][sym] = ret_vol_diff_20.reindex(dates)
        out["PERM_ENTROPY_RET_CHG_20"][sym] = (h_ret_20 - h_ret_20.shift(20)).reindex(dates)
        out["STAT_COMPLEXITY_CHG_20"][sym] = (c_ret_20 - c_ret_20.shift(20)).reindex(dates)
        out["PERM_ENTROPY_VOL_CHG_20"][sym] = (h_vol_20 - h_vol_20.shift(20)).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("permutation_entropy_1m", "permutation_entropy_1m", _build))
