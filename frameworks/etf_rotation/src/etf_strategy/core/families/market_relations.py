"""Independent ETF families describing market and asset-class relations."""
from pathlib import Path

import yaml

from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..etf_benchmark_factor_space import build_benchmark_factor_space
from ..etf_cross_asset_factor_space import build_cross_asset_factor_space, parse_asset_classes


def _benchmark(panels, eligibility, data_root, config):
    return build_benchmark_factor_space(
        panels["close"], tuple(config["benchmark_symbols"])
    )


def _cross_asset(panels, eligibility, data_root, config):
    root = Path(__file__).resolve().parents[4]
    path = Path(str(config["asset_class_config"]))
    path = path if path.is_absolute() else (root / path).resolve()
    classes = yaml.safe_load(path.read_text())["classes"]
    mapping = parse_asset_classes(classes, list(panels["close"].columns))
    return build_cross_asset_factor_space(panels["close"], eligibility, mapping)


register_family(FamilyProvider("market_sensitivity", "market_sensitivity", _benchmark))
register_family(FamilyProvider("category_leadership", "category_leadership", _cross_asset))
register_family(FamilyProvider("within_category_selection", "within_category_selection", _cross_asset))
register_family(FamilyProvider("category_state", "category_state", _cross_asset))
