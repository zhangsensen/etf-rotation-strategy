"""Stage-S11 family: complexity_measures_1m -- nonlinear-dynamics
complexity measures of the 1m return sequence beyond permutation entropy,
directive 2026-09-20 round_557 (S11 stage, main controller, pre-specified
direction, deepening the S6 channel: PERM_ENTROPY_RET_20 was this line's
first two-window-significant single atom carrying no volume information,
audit +52.4bp / t 2.09).

Literature anchors:
- Pincus (1991), "Approximate Entropy as a Measure of System Complexity",
  PNAS -- ApEn(m, r): for embedding dimension m and tolerance r, the
  log-average fraction of m-length (and m+1-length) template matches
  within tolerance r (Chebyshev distance), ApEn = phi(m) - phi(m+1);
  self-matches are included (biased but well-defined for short series).
- Richman & Moorman (2000), "Physiological Time-Series Analysis Using
  Approximate Entropy and Sample Entropy", Am J Physiol -- SampEn(m, r)
  fixes ApEn's self-match and relative-consistency bias by excluding
  self-matches and using a fixed template count from all A/B, giving
  SampEn = -ln(A/B) where B, A are total (not per-template-averaged)
  match counts at lengths m and m+1.
- Lempel & Ziv (1976) / Kaspar & Schuster (1987), normalized LZ76
  complexity -- the number of distinct substrings encountered while
  parsing a binary sequence left-to-right, normalized by the asymptotic
  n/log2(n) bound; measures algorithmic (pattern-copying) complexity of
  the sign sequence, a different axis than ordinal-pattern entropy.
- Eckmann, Kamphorst & Ruelle (1987), "Recurrence Plots of Dynamical
  Systems", Europhys. Lett. -- recurrence rate RR = fraction of embedded
  state-space point pairs within tolerance r of each other (equivalent to
  the m=2 correlation sum); low RR = trajectory rarely revisits nearby
  states (higher-dimensional/noisier dynamics).
- Zunino, Zanin, Perez & Rosso (2012) and related multiscale-entropy
  literature (building on Costa, Goldberger & Peng 2002 MSE) -- computing
  entropy after coarse-graining (here: aggregating 1m bars into 5m/15m
  blocks) reveals whether apparent 1m-scale disorder persists, increases,
  or resolves into more structure at coarser scales.

Implementation (practitioner proxy, consistent with this line's existing
1m conventions, e.g. permutation_entropy_1m.py's per-day-then-rolling-
mean pattern): within each trading day, using the day's 1m close-to-close
returns r (open-anchored first bar, PIT within the day):
  tol = 0.2 * std(r) (Pincus/Richman-Moorman convention: r-tolerance as a
    fraction of the series' own standard deviation, m=2 embedding)
  phi/count helper shared across SampEn, ApEn and RR (all derived from
  the same pairwise Chebyshev-distance match matrix at embedding lengths
  2 and 3):
    SAMPEN_RET_20 = -ln(A_total / B_total), self-matches excluded
    APEN_RET_20 = mean(ln(C_m)) - mean(ln(C_{m+1})), self-matches included
    RECURRENCE_RATE_20 = mean pairwise match fraction at m=2 (self excl.)
  LZ_COMPLEXITY_20: binarize sign(r) to {0,1}, run LZ76 parsing, divide
    by n/log2(n).
  MSPE_5M_20 / MSPE_15M_20: aggregate 1m log-returns into 5m/15m block
    sums (i.e. returns of the coarser series), then compute Bandt-Pompe
    (2002) permutation entropy (d=3, delay=1, normalized by ln(6)) on the
    coarser series, exactly as in permutation_entropy_1m.py's method.
  MSPE_SCALE_DIFF_20 = MSPE_15M_20 (pre-rolling daily value) minus the
    same-day 1m-scale permutation entropy (computed internally, not
    exposed as its own atom -- this line's PERM_ENTROPY_RET_20 already
    covers that level; here only the CROSS-SCALE DIFFERENCE is new).
  SAMPEN_RET_CHG_20 = 20-day change of SAMPEN_RET_20.
  All daily statistics are rolled to a 20-day mean (or 20-day change for
  the CHG atom), never using same-day-or-later information beyond the
  day itself.
"""
from __future__ import annotations

import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ROLL_WINDOW = 20
TOL_MULT = 0.2  # Pincus/Richman-Moorman: tolerance as a fraction of series std
SAMPEN_M = 2

ATOMS = (
    "SAMPEN_RET_20",
    "APEN_RET_20",
    "LZ_COMPLEXITY_20",
    "MSPE_5M_20",
    "MSPE_15M_20",
    "MSPE_SCALE_DIFF_20",
    "RECURRENCE_RATE_20",
    "SAMPEN_RET_CHG_20",
)

_EMBED_DIM = 3
_N_STATES = math.factorial(_EMBED_DIM)
_PATTERNS = {p: i for i, p in enumerate(itertools.permutations(range(_EMBED_DIM)))}
_LOG_N_STATES = math.log(_N_STATES)


def _match_counts(r: np.ndarray, m: int, tol: float) -> np.ndarray:
    """For embedding length m, count matches (Chebyshev distance <= tol)
    per template, INCLUDING self-matches (subtract 1 later where an
    exclusive count is needed)."""
    n = len(r)
    if n <= m:
        return np.array([])
    idx = np.arange(m)[None, :] + np.arange(n - m + 1)[:, None]
    windows = r[idx]
    diff = np.max(np.abs(windows[:, None, :] - windows[None, :, :]), axis=2)
    return np.sum(diff <= tol, axis=1).astype(float)


def _sample_entropy(r: np.ndarray, m: int, tol: float) -> float:
    n = len(r)
    if n <= m + 1 or tol <= 0:
        return float("nan")
    b_counts = _match_counts(r, m, tol) - 1.0
    a_counts = _match_counts(r, m + 1, tol) - 1.0
    b_total = float(np.sum(b_counts[: n - m - 1 + 1]))
    a_total = float(np.sum(a_counts))
    if b_total <= 0 or a_total <= 0:
        return float("nan")
    return -math.log(a_total / b_total)


def _approx_entropy(r: np.ndarray, m: int, tol: float) -> float:
    n = len(r)
    if n <= m + 1 or tol <= 0:
        return float("nan")

    def _phi(k: int) -> float:
        counts = _match_counts(r, k, tol)
        denom = n - k + 1
        c = counts / denom
        c = c[c > 0]
        if len(c) == 0:
            return float("nan")
        return float(np.mean(np.log(c)))

    p_m, p_m1 = _phi(m), _phi(m + 1)
    if not (np.isfinite(p_m) and np.isfinite(p_m1)):
        return float("nan")
    return p_m - p_m1


def _recurrence_rate(r: np.ndarray, m: int, tol: float) -> float:
    n = len(r)
    if n <= m or tol <= 0:
        return float("nan")
    counts = _match_counts(r, m, tol) - 1.0
    denom = n - m + 1
    if denom <= 1:
        return float("nan")
    return float(np.sum(counts) / (denom * (denom - 1)))


def _lz76_complexity(bits: np.ndarray) -> float:
    n = len(bits)
    if n < 4:
        return float("nan")
    s = "".join("1" if b else "0" for b in bits)
    i, k, l = 0, 1, 1
    c, k_max = 1, 1
    while True:
        if s[i + k - 1] == s[l + k - 1]:
            k += 1
            if l + k > n:
                c += 1
                break
        else:
            k_max = max(k, k_max)
            i += 1
            if i == l:
                c += 1
                l += k_max
                if l + 1 > n:
                    break
                i = 0
                k = 1
                k_max = 1
            else:
                k = 1
    b_n = n / math.log2(n) if n > 1 else float("nan")
    return c / b_n if b_n and np.isfinite(b_n) else float("nan")


def _ordinal_pattern_entropy(values: np.ndarray) -> float:
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
    h = -np.sum(p * np.log(p)) / _LOG_N_STATES
    return float(h)


def _block_sum_returns(r: np.ndarray, block: int) -> np.ndarray:
    n = len(r)
    usable = (n // block) * block
    if usable < block:
        return np.array([])
    return r[:usable].reshape(-1, block).sum(axis=1)


def _day_complexity_features(day: pd.DataFrame) -> dict | None:
    close = day["close"].to_numpy(float)
    open0 = float(day["open"].to_numpy(float)[0])
    prev = np.concatenate([[open0], close[:-1]])
    with np.errstate(all="ignore"):
        r = close / np.where(prev > 0, prev, np.nan) - 1.0
    ok = np.isfinite(r)
    if ok.sum() < 120:
        return None
    r = r[ok]
    sd = float(np.std(r))
    if sd <= 0:
        return None
    tol = TOL_MULT * sd

    sampen = _sample_entropy(r, SAMPEN_M, tol)
    apen = _approx_entropy(r, SAMPEN_M, tol)
    rr = _recurrence_rate(r, SAMPEN_M, tol)
    bits = (r > 0).astype(int)
    lz = _lz76_complexity(bits)

    r5 = _block_sum_returns(r, 5)
    r15 = _block_sum_returns(r, 15)
    mspe5 = _ordinal_pattern_entropy(r5) if len(r5) >= _EMBED_DIM + 1 else float("nan")
    mspe15 = _ordinal_pattern_entropy(r15) if len(r15) >= _EMBED_DIM + 1 else float("nan")
    pe1m = _ordinal_pattern_entropy(r)
    scale_diff = (
        mspe15 - pe1m if np.isfinite(mspe15) and np.isfinite(pe1m) else float("nan")
    )

    return {
        "sampen": sampen,
        "apen": apen,
        "lz": lz,
        "mspe5": mspe5,
        "mspe15": mspe15,
        "scale_diff": scale_diff,
        "rr": rr,
    }


def _build_complexity(panels, eligibility, data_root, config):
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
            feats = _day_complexity_features(day)
            if feats is not None:
                feats["date"] = date
                records.append(feats)
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date").sort_index()

        sampen_20 = daily["sampen"].rolling(ROLL_WINDOW, min_periods=10).mean()
        out["SAMPEN_RET_20"][sym] = sampen_20.reindex(dates)
        out["SAMPEN_RET_CHG_20"][sym] = (sampen_20 - sampen_20.shift(ROLL_WINDOW)).reindex(dates)
        out["APEN_RET_20"][sym] = (
            daily["apen"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["LZ_COMPLEXITY_20"][sym] = (
            daily["lz"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["MSPE_5M_20"][sym] = (
            daily["mspe5"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["MSPE_15M_20"][sym] = (
            daily["mspe15"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["MSPE_SCALE_DIFF_20"][sym] = (
            daily["scale_diff"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["RECURRENCE_RATE_20"][sym] = (
            daily["rr"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
    return out


register_family(FamilyProvider("complexity_measures_1m", "complexity_measures_1m", _build_complexity))
