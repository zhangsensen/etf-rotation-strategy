"""Independent minute mechanisms for ETF intraday breadth discovery.

The providers expose complete-D path atoms only.  They are intentionally
separate from the shared referee and catalog so this surface can be audited
before any family is promoted.
"""
from __future__ import annotations

from ..family_provider import FamilyProvider
from ..family_registry import register_family
from .intraday_cache import build_cached_intraday


def _build(panels, eligibility, data_root, config):
    return build_cached_intraday(panels, data_root, config)


register_family(
    FamilyProvider("intraday_tail_reversal_jump", "intraday_tail_reversal_jump", _build)
)
register_family(
    FamilyProvider("intraday_return_distribution", "intraday_return_distribution", _build)
)
register_family(
    FamilyProvider("intraday_turnover_asymmetry", "intraday_turnover_asymmetry", _build)
)
