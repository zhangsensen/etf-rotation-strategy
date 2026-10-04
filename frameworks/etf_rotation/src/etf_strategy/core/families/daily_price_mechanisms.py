"""Independent ETF families derived from daily adjusted OHLC paths."""
from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..ohlcv_factor_mining import build_ohlcv_factor_space
from ..etf_daily_structure_factor_space import build_daily_structure_factor_space


def _ohlcv(panels, eligibility, data_root, config):
    return build_ohlcv_factor_space(panels)


def _structure(panels, eligibility, data_root, config):
    return build_daily_structure_factor_space(panels)


register_family(FamilyProvider("directional_trend", "directional_trend", _ohlcv))
register_family(FamilyProvider("price_location", "price_location", _ohlcv))
register_family(FamilyProvider("downside_risk", "downside_risk", _ohlcv))
register_family(FamilyProvider("daily_candle", "daily_candle", _structure))
register_family(FamilyProvider("path_efficiency", "path_efficiency", _structure))
register_family(FamilyProvider("return_tail_shape", "return_tail_shape", _structure))
