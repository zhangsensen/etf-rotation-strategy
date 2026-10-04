"""Statistical referee primitives for ETF factor mining.

The functions in this module do not build factors.  They turn a frozen signal
and an executable forward-return panel into tie-neutral portfolio series and
statistics used by the mining gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import NormalDist
from typing import Iterable

import numpy as np
import pandas as pd

from .etf_rank_utils import canonical_scores


@dataclass(frozen=True)
class TopKSeries:
    excess: pd.Series
    precision: pd.Series
    eligible_count: pd.Series
    signal_weights: pd.DataFrame
    outcome_weights: pd.DataFrame
    dropped_label_days: int = 0


def fractional_topk_weights(
    scores: pd.DataFrame,
    k: int,
    *,
    min_names: int,
) -> pd.DataFrame:
    """Return top-k membership weights without column-order tie breaking.

    Names above the boundary receive weight one.  Names tied at the boundary
    share the remaining weight.  Each valid row sums to ``k``.
    """
    if k < 1 or min_names < k:
        raise ValueError("require min_names >= k >= 1")
    values = canonical_scores(scores).to_numpy(dtype=float)
    weights = np.zeros_like(values)
    for row_no, row in enumerate(values):
        valid = np.isfinite(row)
        if int(valid.sum()) < min_names:
            continue
        boundary = np.sort(row[valid])[::-1][k - 1]
        above = valid & (row > boundary)
        tied = valid & (row == boundary)
        remaining = k - int(above.sum())
        weights[row_no, above] = 1.0
        if remaining > 0:
            weights[row_no, tied] = remaining / int(tied.sum())
    return pd.DataFrame(weights, index=scores.index, columns=scores.columns)


def topk_series(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    *,
    direction: float,
    k: int,
    min_names: int,
) -> TopKSeries:
    """Build executable top-k excess and tie-neutral precision series."""
    if direction not in (-1.0, 1.0):
        raise ValueError("direction must be +1 or -1")
    score = (signal * direction).where(eligibility)
    forward = forward_return.where(eligibility)
    # Selection is decided on D from what is KNOWN on D: the score. Label availability (a
    # future fact) must never remove a name from the candidate set (2026-09-21 fix: the previous
    # `score.notna() & forward.notna()` mask silently replaced a top name whose exit open was
    # missing by the 4th name). A day is scored only if every selectable name has an executable
    # label; otherwise the day is dropped, never re-ranked.
    known = score.notna()
    eligible_count = known.sum(axis=1)
    label_complete = (~known | forward.notna()).all(axis=1)
    ok_count = eligible_count >= min_names
    ok = ok_count & label_complete
    forward = forward.where(known)

    signal_weights = fractional_topk_weights(score, k, min_names=min_names)
    outcome_weights = fractional_topk_weights(forward, k, min_names=min_names)
    top_return = (forward.fillna(0.0) * signal_weights).sum(axis=1) / k
    equal_weight_return = forward.mean(axis=1)
    excess = (top_return - equal_weight_return).where(ok)
    precision = ((signal_weights * outcome_weights).sum(axis=1) / k).where(ok)
    return TopKSeries(
        excess=excess,
        precision=precision,
        eligible_count=eligible_count.where(ok),
        signal_weights=signal_weights,
        outcome_weights=outcome_weights,
        dropped_label_days=int((ok_count & ~label_complete).sum()),
    )


def purge_by_exit(series: pd.Series, calendar: pd.Index, window_end: pd.Timestamp, offset_sessions: int) -> pd.Series:
    """Keep only signal dates whose exit session (signal + offset_sessions on the trading calendar)
    is on or before ``window_end``. Windows are otherwise sliced by signal date, which lets the
    last ``offset_sessions`` signals of a window use prices after its end (2026-09-21 fix)."""
    cal = pd.DatetimeIndex(calendar).sort_values()
    end_pos = int(cal.searchsorted(pd.Timestamp(window_end), side="right")) - 1
    last_signal_pos = end_pos - int(offset_sessions)
    if last_signal_pos < 0:
        return series.iloc[0:0]
    return series.loc[: cal[last_signal_pos]]


def block_t(series: pd.Series, block_sessions: int) -> tuple[float, int]:
    """t statistic of non-overlapping signal-date block means."""
    if block_sessions < 1:
        raise ValueError("block_sessions must be positive")
    values = series.dropna().to_numpy(dtype=float)
    # full blocks only: a 2-day tail block carried the same weight as a 5-day block (2026-09-21 fix)
    blocks = [
        float(np.mean(values[start : start + block_sessions]))
        for start in range(0, len(values) - block_sessions + 1, block_sessions)
    ]
    if len(blocks) <= 3:
        return float("nan"), len(blocks)
    array = np.asarray(blocks)
    standard_error = array.std(ddof=1) / np.sqrt(len(array))
    if not np.isfinite(standard_error) or standard_error <= 0:
        return float("nan"), len(blocks)
    return float(array.mean() / standard_error), len(blocks)


def block_t_calendar(series: pd.Series, calendar: pd.Index, block_sessions: int) -> tuple[float, int]:
    """Block t where blocks are ``block_sessions`` consecutive TRADING SESSIONS on ``calendar``
    (2026-09-21): a block is used only if every session in it has an observation, so dropping
    label-incomplete days cannot shrink a block to fewer sessions. ``series`` may carry NaN."""
    if block_sessions < 1:
        raise ValueError("block_sessions must be positive")
    cal = pd.DatetimeIndex(calendar).sort_values()
    if len(series):
        cal = cal[(cal >= series.index.min()) & (cal <= series.index.max())]
    values = series.reindex(cal).to_numpy(dtype=float)
    blocks = []
    for start in range(0, len(values) - block_sessions + 1, block_sessions):
        chunk = values[start : start + block_sessions]
        if np.isfinite(chunk).all():
            blocks.append(float(chunk.mean()))
    if len(blocks) <= 3:
        return float("nan"), len(blocks)
    array = np.asarray(blocks)
    standard_error = array.std(ddof=1) / np.sqrt(len(array))
    if not np.isfinite(standard_error) or standard_error <= 0:
        return float("nan"), len(blocks)
    return float(array.mean() / standard_error), len(blocks)


def newey_west_t(series: pd.Series, lag: int) -> float:
    """Bartlett-kernel Newey-West t statistic for a sample mean."""
    if lag < 0:
        raise ValueError("lag must be non-negative")
    values = series.dropna().to_numpy(dtype=float)
    count = len(values)
    if count < max(20, lag + 3):
        return float("nan")
    demeaned = values - values.mean()
    long_run_variance = float(demeaned @ demeaned) / count
    for offset in range(1, min(lag, count - 1) + 1):
        weight = 1.0 - offset / (lag + 1.0)
        covariance = float(demeaned[offset:] @ demeaned[:-offset]) / count
        long_run_variance += 2.0 * weight * covariance
    if not np.isfinite(long_run_variance) or long_run_variance <= 0:
        return float("nan")
    return float(values.mean() / np.sqrt(long_run_variance / count))


def newey_west_t_calendar(series: pd.Series, calendar: pd.Index, lag: int) -> float:
    """Newey-West t where the lag is measured in TRADING SESSIONS on ``calendar`` (2026-09-21):
    the series is placed on the calendar, autocovariances at lag j use only session pairs (t, t-j)
    where both observations exist, and each is scaled by the number of such pairs."""
    if lag < 0:
        raise ValueError("lag must be non-negative")
    cal = pd.DatetimeIndex(calendar).sort_values()
    if len(series):
        cal = cal[(cal >= series.index.min()) & (cal <= series.index.max())]
    x = series.reindex(cal).to_numpy(dtype=float)
    present = np.isfinite(x)
    count = int(present.sum())
    if count < max(20, lag + 3):
        return float("nan")
    mean = float(x[present].mean())
    d = np.where(present, x - mean, 0.0)
    long_run_variance = float((d[present] @ d[present]) / count)
    for j in range(1, min(lag, len(x) - 1) + 1):
        both = present[j:] & present[:-j]
        n_pairs = int(both.sum())
        if n_pairs == 0:
            continue
        weight = 1.0 - j / (lag + 1.0)
        # Codex round-4: gamma_j = (sum over available session pairs of d_t d_{t-j}) / count.
        # With no gaps this is the standard estimator; with gaps the missing pairs contribute zero
        # rather than being imputed by rescaling.
        covariance = float((d[j:][both] @ d[:-j][both]) / count)
        long_run_variance += 2.0 * weight * covariance
    if not np.isfinite(long_run_variance) or long_run_variance <= 0:
        return float("nan")
    return float(mean / np.sqrt(long_run_variance / count))


def one_sided_normal_pvalue(t_stat: float) -> float:
    if not np.isfinite(t_stat):
        return 1.0
    return float(1.0 - NormalDist().cdf(float(t_stat)))


def holm_rejections(pvalues: Iterable[float], alpha: float) -> list[bool]:
    """Holm step-down decisions in input order."""
    values = np.asarray(list(pvalues), dtype=float)
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")
    values = np.where(np.isfinite(values), values, 1.0)
    order = np.argsort(values)
    accepted = np.zeros(len(values), dtype=bool)
    for position, index in enumerate(order):
        if values[index] <= alpha / (len(values) - position):
            accepted[index] = True
        else:
            break
    return accepted.tolist()


def campaign_bonferroni_pass(
    t_stat: float,
    *,
    alpha: float,
    hypothesis_budget: int,
) -> tuple[bool, float]:
    """Fixed-budget campaign gate for repeated preregistered tests.

    This controls the declared test budget.  It does not turn hypotheses made
    after viewing the same outcome surface into independent confirmation.
    """
    if hypothesis_budget < 1:
        raise ValueError("hypothesis_budget must be positive")
    pvalue = one_sided_normal_pvalue(t_stat)
    return bool(pvalue <= alpha / hypothesis_budget), pvalue


def paired_increment_stats(
    candidate_excess: pd.Series,
    leg_excess: pd.Series,
    *,
    discovery_end: pd.Timestamp,
    audit_start: pd.Timestamp,
    audit_end: pd.Timestamp,
    horizon: int,
    calendar: pd.Index | None = None,
    lag: int = 0,
    discovery_start: pd.Timestamp | None = None,
) -> dict[str, float]:
    """Measure candidate contribution over one standalone leg on matched days."""
    pair = pd.concat(
        [candidate_excess.rename("candidate"), leg_excess.rename("leg")],
        axis=1,
    ).dropna()
    delta = pair["candidate"] - pair["leg"]
    discovery = delta.loc[discovery_start:discovery_end] if discovery_start is not None else delta.loc[:discovery_end]
    audit = delta.loc[audit_start:audit_end]
    if calendar is not None:
        discovery = purge_by_exit(discovery, calendar, discovery_end, lag + horizon)
        audit = purge_by_exit(audit, calendar, audit_end, lag + horizon)
        return {
            "discovery_bp": float(discovery.mean() * 1e4) if len(discovery) else float("nan"),
            "discovery_t_hac": newey_west_t_calendar(discovery, calendar, max(0, horizon - 1)),
            "audit_bp": float(audit.mean() * 1e4) if len(audit) else float("nan"),
            "audit_t_hac": newey_west_t_calendar(audit, calendar, max(0, horizon - 1)),
            "discovery_days": float(len(discovery)),
            "audit_days": float(len(audit)),
        }
    return {
        "discovery_bp": float(discovery.mean() * 1e4) if len(discovery) else float("nan"),
        "discovery_t_hac": newey_west_t(discovery, max(0, horizon - 1)),
        "audit_bp": float(audit.mean() * 1e4) if len(audit) else float("nan"),
        "audit_t_hac": newey_west_t(audit, max(0, horizon - 1)),
        "discovery_days": float(len(discovery)),
        "audit_days": float(len(audit)),
    }
