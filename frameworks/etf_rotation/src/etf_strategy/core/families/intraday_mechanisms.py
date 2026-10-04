"""Independent ETF intraday return-path, turnover-shape and VWAP families."""
from ..family_provider import FamilyProvider
from ..family_registry import register_family
from .intraday_cache import build_cached_intraday


def _build(panels, eligibility, data_root, config):
    return build_cached_intraday(panels, data_root, config)


register_family(FamilyProvider("intraday_return_path", "intraday_return_path", _build))
register_family(FamilyProvider("intraday_turnover_shape", "intraday_turnover_shape", _build))
register_family(FamilyProvider("intraday_vwap_position", "intraday_vwap_position", _build))
