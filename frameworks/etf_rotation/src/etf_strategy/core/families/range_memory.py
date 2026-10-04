"""Independent daily range-memory family."""
from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..etf_range_memory_factor_space import build_range_memory_factor_space


def _build(panels, eligibility, data_root, config):
    return build_range_memory_factor_space(panels)


register_family(FamilyProvider("range_memory", "range_memory", _build))
