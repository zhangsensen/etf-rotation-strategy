"""Independent overnight-gap response family."""
from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..etf_gap_response_factor_space import build_gap_response_factor_space


def _build(panels, eligibility, data_root, config):
    return build_gap_response_factor_space(panels)


register_family(FamilyProvider("gap_response", "gap_response", _build))
