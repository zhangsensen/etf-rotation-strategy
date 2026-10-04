"""Per-process cache shared by ETF intraday family providers."""
from __future__ import annotations

from pathlib import Path

from ..etf_intraday_factor_space import build_intraday_factor_space


_CACHE: dict[tuple[str, tuple[str, ...], str, str], dict] = {}


def build_cached_intraday(panels, data_root, config):
    symbols = tuple(panels["close"].columns)
    frequency = str(config["frequency"])
    as_of = str(panels["close"].index.max())
    key = (str(Path(data_root).resolve()), symbols, frequency, as_of)
    if key not in _CACHE:
        _CACHE[key] = build_intraday_factor_space(
            data_root, symbols, frequency=frequency, as_of=panels["close"].index.max()
        )
    return _CACHE[key]
