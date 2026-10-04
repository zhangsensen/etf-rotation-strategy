from pathlib import Path
from typing import Mapping
import pandas as pd
import yaml

from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..ohlcv_factor_mining import build_ohlcv_factor_space
from ..etf_cross_asset_factor_space import build_cross_asset_factor_space, parse_asset_classes
from ..etf_benchmark_factor_space import build_benchmark_factor_space


def _ohlcv(panels, eligibility, data_root, config):
    return build_ohlcv_factor_space(panels)


def _cross_asset(panels, eligibility, data_root, config):
    root = Path(__file__).resolve().parents[4]
    path = Path(str(config["asset_class_config"]))
    path = path if path.is_absolute() else (root / path).resolve()
    classes = yaml.safe_load(path.read_text())["classes"]
    mapping = parse_asset_classes(classes, list(panels["close"].columns))
    return build_cross_asset_factor_space(panels["close"], eligibility, mapping)


def _benchmark(panels, eligibility, data_root, config):
    return build_benchmark_factor_space(panels["close"], tuple(config["benchmark_symbols"]))


# Retired compatibility builders intentionally have no registry side effect.
