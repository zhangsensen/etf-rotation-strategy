"""Public ETF regime-label entrypoint.

Implementation lives in the isolated ``etf_strategy.core`` package so the
runner, tests, and downstream research tools share one source of truth.
"""
from etf_strategy.core.etf_regime_label import (  # noqa: F401
    DEFENSIVE_SYMBOLS,
    BasketSpec,
    basket_spec_from_universe,
    build_regime_labels,
    label_contract,
)

__all__ = [
    "DEFENSIVE_SYMBOLS",
    "BasketSpec",
    "basket_spec_from_universe",
    "build_regime_labels",
    "label_contract",
]
