"""Single registry seam for ETF factor-family providers."""
from __future__ import annotations

import importlib
import pkgutil

from .family_provider import FamilyProvider

_REGISTRY: dict[str, FamilyProvider] = {}


def register_family(provider: FamilyProvider) -> None:
    if provider.source_name in _REGISTRY:
        raise ValueError(f"duplicate ETF family source: {provider.source_name}")
    _REGISTRY[provider.source_name] = provider


def resolve_family(source_name: str) -> FamilyProvider:
    if source_name not in _REGISTRY:
        raise KeyError(f"unregistered ETF family source: {source_name}")
    return _REGISTRY[source_name]


def load_builtin_families() -> None:
    package = importlib.import_module("etf_strategy.core.families")
    for module in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        importlib.import_module(module.name)


def registered_sources() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))
