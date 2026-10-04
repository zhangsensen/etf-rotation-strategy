"""Provider for overnight-versus-session volatility allocation."""
from __future__ import annotations

from ..etf_gap_volatility_factor_space import build_gap_volatility_factor_space
from ..family_provider import FamilyProvider
from ..family_registry import register_family


def _build(panels, eligibility, data_root, config):
    del eligibility, data_root, config
    return build_gap_volatility_factor_space(panels["open"], panels["close"])


register_family(FamilyProvider("gap_volatility", "gap_volatility", _build))
