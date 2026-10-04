"""Daily ETF family providers for breadth extension v2."""
from __future__ import annotations

from ..etf_breadth_extensions import build_breadth_extensions
from ..family_provider import FamilyProvider
from ..family_registry import register_family


def _build(panels, eligibility, data_root, config):
    return build_breadth_extensions(panels)


for family in (
    "transaction_friction", "conditional_activity",
    "return_concentration", "auction_range_overlap", "activity_response",
    "uncertainty_activity",
):
    register_family(FamilyProvider(family, family, _build))
