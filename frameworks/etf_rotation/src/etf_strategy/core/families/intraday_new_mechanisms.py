"""Distinct minute-only ETF mechanisms beyond path, turnover and VWAP."""
from __future__ import annotations

from ..family_provider import FamilyProvider
from ..family_registry import register_family
from .intraday_cache import build_cached_intraday


def _build(panels, eligibility, data_root, config):
    return build_cached_intraday(panels, data_root, config)


register_family(
    FamilyProvider("intraday_trend_consistency", "intraday_trend_consistency", _build)
)
register_family(
    FamilyProvider("intraday_volatility_structure", "intraday_volatility_structure", _build)
)
register_family(
    FamilyProvider("intraday_price_volume_shock", "intraday_price_volume_shock", _build)
)
