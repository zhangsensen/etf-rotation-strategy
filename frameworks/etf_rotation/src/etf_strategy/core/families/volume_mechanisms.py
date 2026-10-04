"""Independent ETF trading-activity and price-volume families."""
from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..etf_liquidity_factor_space import build_liquidity_factor_space


def _build(panels, eligibility, data_root, config):
    return build_liquidity_factor_space(panels)


register_family(FamilyProvider("trading_activity", "trading_activity", _build))
register_family(FamilyProvider("price_volume_coupling", "price_volume_coupling", _build))
