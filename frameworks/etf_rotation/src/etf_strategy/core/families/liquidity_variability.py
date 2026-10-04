"""Provider for turnover variability."""
from __future__ import annotations

from ..etf_liquidity_variability_factor_space import build_liquidity_variability_factor_space
from ..family_provider import FamilyProvider
from ..family_registry import register_family


def _build(panels, eligibility, data_root, config):
    del eligibility, data_root, config
    return build_liquidity_variability_factor_space(panels["amount"])


register_family(
    FamilyProvider("liquidity_variability", "liquidity_variability", _build)
)
