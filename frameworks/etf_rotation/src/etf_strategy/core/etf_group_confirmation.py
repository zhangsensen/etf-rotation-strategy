"""Time-surface policy for ETF group-factor evidence.

The policy is intentionally separate from factor formulas.  It prevents a
direction chosen with 2025 labels from borrowing 2025 again in its judge, and
prevents formulas iterated after viewing 2026 from calling that segment clean
confirmation.
"""
from __future__ import annotations

from collections.abc import Mapping


def evidence_policy(config: Mapping, candidate: str) -> str:
    """Return the fail-closed evidence policy for a frozen candidate."""
    explicit = config.get("evidence_policy")
    if explicit:
        return str(explicit)

    name = str(candidate)
    surface = config.get("discovery_surface")
    version = str(config.get("version", ""))
    if name.startswith("reverse_"):
        return "POST_RESULT_REVERSE_NOT_CONFIRMATION"
    # Batch20+ range-shock variants were iterated after the combined 2025/2026
    # surface had been inspected.  Their 2026 numbers remain historical leads.
    if (
        "range_shock" in name
        and any(f"batch{n}" in version for n in range(20, 100))
    ):
        return "SEEN_2026_ADAPTIVE_NOT_CONFIRMATION"
    if surface in {"2025_POST_IC_DIRECTION", "2025_POST_OUTCOME_DISCOVERY"}:
        return "2025_DIRECTION_2026_HISTORICAL_SEGMENT"
    if surface == "2025_DIRECTION_DISCOVERY_ONLY":
        return "DIRECTION_DISCOVERY_ONLY"
    return "PRIOR_DIRECTION_FULL_WINDOW"


__all__ = ["evidence_policy"]
