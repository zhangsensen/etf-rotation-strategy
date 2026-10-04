from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..etf_serial_dependence_factor_space import build_serial_dependence_factor_space


def _build(panels, eligibility, data_root, config):
    return build_serial_dependence_factor_space(panels)


register_family(FamilyProvider("serial_dependence", "serial_dependence", _build))
