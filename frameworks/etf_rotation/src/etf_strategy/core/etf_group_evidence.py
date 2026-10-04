"""Evidence-layer classification for ETF group discovery.

This module is deliberately independent of runners, data frames, and labels.  It
only classifies an already materialised summary row, keeping IC evidence separate
from economic-return evidence while retaining the legacy screen fields.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


def _finite(value: Any) -> bool:
    """Return true only for a finite real number (NaN/None fail closed)."""
    if isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _number(row: Mapping[str, Any], *names: str) -> float | None:
    for name in names:
        value = row.get(name)
        if _finite(value):
            return float(value)
    return None


def _threshold(screens: Mapping[str, Any], *names: str) -> float | None:
    return _number(screens, *names)


def _at_least(value: float | None, threshold: float | None) -> bool:
    return value is not None and threshold is not None and value >= threshold


def _paired_supported(
    paired: Any,
    screens: Mapping[str, Any],
    *,
    metric: str,
) -> bool | None:
    """Require every supplied interaction leg to pass its increment gate."""
    if paired is None:
        return None
    if isinstance(paired, Mapping):
        return False
    try:
        rows = list(paired)
    except TypeError:
        return False
    if len(rows) != 2 or not all(isinstance(item, Mapping) for item in rows):
        return False
    n_key = f"{metric}_n"
    mean_key = f"{metric}_increment_mean"
    hac_key = f"{metric}_increment_hac_t"
    min_n = _threshold(screens, "paired_min_days", "min_days")
    min_hac = _threshold(
        screens,
        "paired_min_hac_t",
        f"paired_min_{metric}_hac_t",
    )
    # Pair gates are intentionally metric-specific; IC increment never borrows
    # the economic return gate (and vice versa).
    return all(
        _at_least(_number(item, n_key), min_n)
        and (_number(item, mean_key) is not None)
        and _number(item, mean_key) > 0
        and _at_least(_number(item, hac_key), min_hac)
        for item in rows
    )


def evidence_layers(
    row: Mapping[str, Any],
    screens: Mapping[str, Any],
    cap: Any,
    paired_ic: Any = None,
    paired_economic: Any = None,
    *,
    historical_2026_row: Mapping[str, Any] | None = None,
    evidence_policy: str = "PRIOR_DIRECTION_FULL_WINDOW",
) -> dict[str, Any]:
    """Return independent IC/economic evidence layers for one summary row.

    ``screen_pass`` and ``all_layers`` are copied from the legacy runner row and
    are not used to grant either new layer.  ``cap`` is the fixed discovery
    budget; the normal one-sided IC p-value must be at most ``alpha / cap``.
    """
    if not isinstance(row, Mapping) or not isinstance(screens, Mapping):
        raise TypeError("row and screens must be mappings")

    min_days = _threshold(screens, "min_days")
    n = _number(row, "n", "ic_n")
    coverage = _at_least(n, min_days)

    ic_ok = (
        _at_least(_number(row, "ic_mean"), _threshold(screens, "min_ic"))
        and _at_least(_number(row, "ic_hac_t"), _threshold(screens, "min_ic_hac_t"))
        and _at_least(_number(row, "ic_block_t"), _threshold(screens, "min_ic_block_t"))
        and row.get("all_eligible_years_positive") is True
        and _at_least(_number(row, "positive_years"), _threshold(screens, "min_positive_years"))
        and (_number(row, "min_leave_group_ic") is not None)
        and _number(row, "min_leave_group_ic") > 0
    )
    historical_ic_supported = bool(coverage and ic_ok)

    allowed_policies = {
        "PRIOR_DIRECTION_FULL_WINDOW",
        "DIRECTION_DISCOVERY_ONLY",
        "2025_DIRECTION_2026_HISTORICAL_SEGMENT",
        "SEEN_2026_ADAPTIVE_NOT_CONFIRMATION",
        "POST_RESULT_REVERSE_NOT_CONFIRMATION",
    }
    if evidence_policy not in allowed_policies:
        raise ValueError(f"unsupported evidence policy: {evidence_policy}")
    historical_segment_required = evidence_policy == "2025_DIRECTION_2026_HISTORICAL_SEGMENT"
    historical_segment_contaminated = evidence_policy in {
        "SEEN_2026_ADAPTIVE_NOT_CONFIRMATION",
        "POST_RESULT_REVERSE_NOT_CONFIRMATION",
    }
    historical_min_days = _threshold(screens, "min_historical_2026_days") or 120.0
    historical_2026 = historical_2026_row if isinstance(historical_2026_row, Mapping) else {}
    historical_2026_metrics_pass = bool(
        _at_least(_number(historical_2026, "n", "ic_n"), historical_min_days)
        and _at_least(_number(historical_2026, "ic_mean"), _threshold(screens, "min_ic"))
        and _at_least(
            _number(historical_2026, "ic_hac_t"),
            _threshold(screens, "min_ic_hac_t"),
        )
        and _at_least(
            _number(historical_2026, "ic_block_t"),
            _threshold(screens, "min_ic_block_t"),
        )
        and (_number(historical_2026, "min_leave_group_ic") is not None)
        and _number(historical_2026, "min_leave_group_ic") > 0
    )
    historical_2026_supported = bool(
        historical_segment_required
        and not historical_segment_contaminated
        and historical_2026_metrics_pass
    )
    factor_evidence_supported = bool(
        historical_ic_supported
        if evidence_policy == "PRIOR_DIRECTION_FULL_WINDOW"
        else historical_2026_supported
    )

    alpha = _threshold(screens, "alpha")
    budget_cap = (
        float(cap)
        if isinstance(cap, int) and not isinstance(cap, bool) and cap > 0
        else None
    )
    budget_row = historical_2026 if historical_segment_required else row
    pvalue = _number(budget_row, "ic_p_normal_one_sided", "ic_pvalue", "ic_p")
    budget_ok = (
        pvalue is not None
        and alpha is not None
        and 0 < alpha < 1
        and budget_cap is not None
        and 0 <= pvalue <= 1
        and pvalue <= alpha / budget_cap
    )

    economic_ok = (
        (_number(row, "excess8_mean") is not None)
        and _number(row, "excess8_mean") > 0
        and _at_least(
            _number(row, "excess8_hac_t"),
            _threshold(screens, "min_excess8_hac_t"),
        )
    )
    economic_supported = bool(coverage and economic_ok)

    paired_ic_result = _paired_supported(paired_ic, screens, metric="ic")
    paired_economic_result = _paired_supported(
        paired_economic, screens, metric="excess8"
    )
    # Increment is a separate claim, never an extra gate on an IC lead.

    # Reverse is a watch-only diagnostic.  It is not a positive gate and is
    # intentionally signed (abs(t) would incorrectly turn a negative result into
    # positive evidence).
    reverse_watch = (
        (_number(row, "ic_mean") is not None and _number(row, "ic_mean") <= -0.01)
        and (_number(row, "ic_hac_t") is not None and _number(row, "ic_hac_t") <= -2)
        and (_number(row, "ic_block_t") is not None and _number(row, "ic_block_t") <= -2)
    )

    result: dict[str, Any] = {
        "coverage_sufficient": coverage,
        "ic_metrics_pass": bool(ic_ok),
        "historical_ic_supported": historical_ic_supported,
        # Compatibility name now means evidence valid under the candidate's
        # declared time policy, not merely a strong combined-window statistic.
        "ic_supported": factor_evidence_supported,
        "factor_evidence_supported": factor_evidence_supported,
        "evidence_policy": evidence_policy,
        "historical_2026_required": historical_segment_required,
        "historical_2026_contaminated": historical_segment_contaminated,
        "historical_2026_metrics_pass": historical_2026_metrics_pass,
        "historical_2026_supported": historical_2026_supported,
        "ic_budget_pass": bool(budget_ok),
        "ic_budget_supported": bool(factor_evidence_supported and budget_ok),
        "economic_metrics_pass": bool(economic_ok),
        "economic_supported": economic_supported,
        "paired_ic_supported": paired_ic_result,
        "paired_economic_supported": paired_economic_result,
        "reverse_watch": bool(reverse_watch),
        # Preserve legacy fields exactly for old consumers.  Missing fields stay
        # missing rather than being silently upgraded.
        "screen_pass": row.get("screen_pass"),
        "all_layers": row.get("all_layers"),
    }
    return result


__all__ = ["evidence_layers"]
