"""ETF identity robustness gates for cross-sectional factor candidates."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .etf_family_referee import common_sample_spearman

MATCHED_LOSO_COLUMNS = (
    "excluded_symbol",
    "discovery_days",
    "audit_days",
    "discovery_ic",
    "seen_audit_ic",
    "baseline_discovery_ic",
    "baseline_seen_audit_ic",
    "discovery_delta",
    "audit_delta",
    "discovery_dates_dropped",
    "audit_dates_dropped",
    "discovery_symbol_pairs",
    "audit_symbol_pairs",
    "discovery_dates_dropped_vs_full",
    "audit_dates_dropped_vs_full",
    "excluded_discovery_contribution_days",
    "excluded_audit_contribution_days",
)


def leave_one_symbol_out(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    *,
    min_pairs: int,
    discovery_end: pd.Timestamp,
    audit_start: pd.Timestamp,
    audit_end: pd.Timestamp,
) -> pd.DataFrame:
    """Legacy leave-one-symbol-out table.

    Each row averages that exclusion's IC over *its own* finite-IC dates, so two
    rows (and the full-panel baseline) can be averaged over different calendars.
    Retained unchanged for backwards compatibility; new callers should prefer
    :func:`matched_leave_one_symbol_out`.
    """
    rows = []
    for excluded in signal.columns:
        columns = [column for column in signal.columns if column != excluded]
        ic, _ = common_sample_spearman(
            signal[columns], forward_return[columns], eligibility[columns], min_pairs
        )
        discovery = ic.loc[:discovery_end].dropna()
        audit = ic.loc[audit_start:audit_end].dropna()
        rows.append(
            {
                "excluded_symbol": excluded,
                "discovery_days": len(discovery),
                "discovery_ic": float(discovery.mean()) if len(discovery) else np.nan,
                "seen_audit_ic": float(audit.mean()) if len(audit) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _boolean_mask(mask: pd.Series, index: pd.Index) -> pd.Index:
    """Trading dates flagged ``True`` by ``mask``, aligned onto ``index``."""
    if mask is None:
        return index[:0]
    aligned = pd.Series(mask).reindex(index)
    aligned = aligned.fillna(False).astype(bool)
    return index[aligned.to_numpy()]


def _surface_stats(
    ic: pd.Series,
    baseline: pd.Series,
    count: pd.Series,
    check_dates: pd.Index,
    own_finite: pd.Index,
) -> dict[str, float]:
    """Mean IC / baseline IC / pair count over an explicit, shared date set."""
    if len(check_dates) == 0:
        return {
            "days": 0,
            "ic": np.nan,
            "baseline": np.nan,
            "delta": np.nan,
            "dropped": int(len(own_finite)),
            "pairs": np.nan,
        }
    value = float(ic.reindex(check_dates).mean())
    base = float(baseline.reindex(check_dates).mean())
    pairs = float(count.reindex(check_dates).mean())
    return {
        "days": int(len(check_dates)),
        "ic": value,
        "baseline": base,
        "delta": value - base,
        "dropped": int(len(own_finite.difference(check_dates))),
        "pairs": pairs,
    }


def matched_leave_one_symbol_out(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    *,
    min_pairs: int,
    discovery_mask: pd.Series,
    audit_mask: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Leave-one-symbol-out IC compared against a date-matched full-panel baseline.

    ``discovery_mask`` / ``audit_mask`` are boolean ``pd.Series`` indexed by
    trading date; the caller is responsible for endpoint purging before the call.
    ``min_pairs`` is applied unchanged to every exclusion — a date that falls
    below the pair floor once a symbol is removed is dropped, never rescued.

    Two tables are returned:

    ``shared``
        Every exclusion is scored on one identical calendar: the intersection of
        the finite-IC dates of the full panel *and* of **all** exclusions, taken
        per surface. Because the check dates are the same for every row, an IC
        difference between rows cannot come from a different sample of days.
    ``paired``
        Each exclusion is scored on the intersection of the full panel's finite
        dates with its own — a larger, per-row calendar that keeps more data at
        the cost of not being comparable across rows.

    In both tables ``baseline_*_ic`` is the full-panel IC averaged over exactly
    the same dates as that row, so ``*_delta`` isolates the symbol's effect
    rather than a change of calendar. ``*_dates_dropped`` counts that exclusion's
    own finite dates that the row's check set discarded. ``*_symbol_pairs`` is
    the mean number of ranked names contributing to that exclusion on the check
    dates. A group with no common dates yields NaN ICs and zero day counts; it
    never reports a usable number.
    """
    index = signal.index
    symbols = list(signal.columns)
    empty = pd.DataFrame(columns=list(MATCHED_LOSO_COLUMNS))
    if not symbols:
        return empty.copy(), empty.copy()

    discovery_dates = _boolean_mask(discovery_mask, index)
    audit_dates = _boolean_mask(audit_mask, index)

    full_ic, _ = common_sample_spearman(signal, forward_return, eligibility, min_pairs)
    contribution = (signal.replace([np.inf, -np.inf], np.nan).notna()
                    & forward_return.reindex_like(signal).replace([np.inf, -np.inf], np.nan).notna()
                    & eligibility.reindex_like(signal).fillna(False))
    full_finite = {
        "discovery": discovery_dates[full_ic.reindex(discovery_dates).notna().to_numpy()],
        "audit": audit_dates[full_ic.reindex(audit_dates).notna().to_numpy()],
    }

    per_symbol: dict[str, dict[str, object]] = {}
    for excluded in symbols:
        columns = [column for column in symbols if column != excluded]
        if columns:
            ic, count = common_sample_spearman(
                signal[columns],
                forward_return[columns],
                eligibility[columns],
                min_pairs,
            )
        else:
            ic = pd.Series(np.nan, index=index, name="ic")
            count = pd.Series(0, index=index, name="pair_count")
        per_symbol[excluded] = {
            "ic": ic,
            "count": count,
            "discovery": discovery_dates[ic.reindex(discovery_dates).notna().to_numpy()],
            "audit": audit_dates[ic.reindex(audit_dates).notna().to_numpy()],
        }

    shared: dict[str, pd.Index] = {}
    for surface in ("discovery", "audit"):
        common = full_finite[surface]
        for excluded in symbols:
            common = common.intersection(per_symbol[excluded][surface])
        shared[surface] = common

    shared_rows = []
    paired_rows = []
    for excluded in symbols:
        state = per_symbol[excluded]
        ic = state["ic"]
        count = state["count"]
        shared_stats = {
            surface: _surface_stats(
                ic, full_ic, count, shared[surface], state[surface]
            )
            for surface in ("discovery", "audit")
        }
        paired_stats = {
            surface: _surface_stats(
                ic,
                full_ic,
                count,
                full_finite[surface].intersection(state[surface]),
                state[surface],
            )
            for surface in ("discovery", "audit")
        }
        for target, stats in ((shared_rows, shared_stats), (paired_rows, paired_stats)):
            target.append(
                {
                    "excluded_symbol": excluded,
                    "discovery_days": stats["discovery"]["days"],
                    "audit_days": stats["audit"]["days"],
                    "discovery_ic": stats["discovery"]["ic"],
                    "seen_audit_ic": stats["audit"]["ic"],
                    "baseline_discovery_ic": stats["discovery"]["baseline"],
                    "baseline_seen_audit_ic": stats["audit"]["baseline"],
                    "discovery_delta": stats["discovery"]["delta"],
                    "audit_delta": stats["audit"]["delta"],
                    "discovery_dates_dropped": stats["discovery"]["dropped"],
                    "audit_dates_dropped": stats["audit"]["dropped"],
                    "discovery_symbol_pairs": stats["discovery"]["pairs"],
                    "audit_symbol_pairs": stats["audit"]["pairs"],
                    "discovery_dates_dropped_vs_full": len(full_finite['discovery']) - stats['discovery']['days'],
                    "audit_dates_dropped_vs_full": len(full_finite['audit']) - stats['audit']['days'],
                    "excluded_discovery_contribution_days": int(contribution.loc[full_finite['discovery'], excluded].sum()),
                    "excluded_audit_contribution_days": int(contribution.loc[full_finite['audit'], excluded].sum()),
                }
            )
    columns = list(MATCHED_LOSO_COLUMNS)
    return (
        pd.DataFrame(shared_rows, columns=columns),
        pd.DataFrame(paired_rows, columns=columns),
    )


def identity_gate(table: pd.DataFrame, direction: float, min_audit_ic: float, min_discovery_ic: float | None = None) -> bool:
    """Both surfaces must clear a magnitude floor when ``min_discovery_ic`` is given (2026-09-21:
    the discovery side previously only required the same sign)."""
    if min_discovery_ic is not None and not (table["discovery_ic"] * direction >= min_discovery_ic).all():
        return False
    return bool(
        not table.empty
        and table["discovery_ic"].notna().all()
        and table["seen_audit_ic"].notna().all()
        and (table["discovery_ic"] * direction > 0.0).all()
        and (table["seen_audit_ic"] * direction >= min_audit_ic).all()
    )
