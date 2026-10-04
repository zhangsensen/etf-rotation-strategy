from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..etf_liquidity_factor_space import build_liquidity_factor_space


def _build(panels, eligibility, data_root, config):
    return build_liquidity_factor_space(panels)


# Retired compatibility builder intentionally has no registry side effect.
