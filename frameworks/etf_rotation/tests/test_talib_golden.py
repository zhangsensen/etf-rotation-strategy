"""Golden test for the pinned TA-Lib dependency.

TA-Lib functions (EMA/RSI/MACD seeding) are not numerically stable across
versions. Sealed indicator definitions record ``talib.__version__`` and their
outputs; a silent upgrade would invalidate frozen hashes. This test pins both
the version and representative outputs on a fixed synthetic input, so an
upgrade fails loudly instead of changing factor values silently.

The dependency is optional for repos that never run indicator batches: the
whole test skips when talib is absent.
"""
from __future__ import annotations

import numpy as np
import pytest

talib = pytest.importorskip("talib", reason="TA-Lib not installed")

PINNED_VERSION = "0.8.1"

# Deterministic synthetic series (same generator as the 2026-10-03 pre-check).
_rng = np.random.default_rng(0)
_CLOSE = np.cumsum(_rng.standard_normal(300)) + 100.0
_HIGH = _CLOSE + np.abs(_rng.standard_normal(300))
_LOW = _CLOSE - np.abs(_rng.standard_normal(300))

# Golden outputs produced with TA-Lib 0.8.1 on this exact input
# (generated once on 2026-10-03 from the generator above).
_GOLDEN = {
    "macd_dif_last": -2.1381700961128445,
    "macd_signal_last": -2.15571865988505,
    "macd_hist_last": 0.017548563772205483,
    "rsi14_last": 35.47879828221938,
    "stoch_k_last": 42.95211672385498,
    "stoch_d_last": 44.90728552339811,
    "bbands_upper_last": 97.31766935028747,
    "adx14_last": 26.67202666694883,
}


def test_version_is_pinned():
    assert talib.__version__ == PINNED_VERSION, (
        f"talib {talib.__version__} != pinned {PINNED_VERSION}; sealed "
        "indicator definitions require re-freezing outputs after a version bump"
    )


@pytest.mark.parametrize("key", sorted(_GOLDEN))
def test_golden_outputs(key):
    macd, signal, hist = talib.MACD(_CLOSE)
    k, d = talib.STOCH(_HIGH, _LOW, _CLOSE, fastk_period=9, slowk_period=3, slowd_period=3)
    rsi = talib.RSI(_CLOSE, 14)
    upper, _, _ = talib.BBANDS(_CLOSE, 20)
    adx = talib.ADX(_HIGH, _LOW, _CLOSE, 14)
    got = {
        "macd_dif_last": macd[-1],
        "macd_signal_last": signal[-1],
        "macd_hist_last": hist[-1],
        "rsi14_last": rsi[-1],
        "stoch_k_last": k[-1],
        "stoch_d_last": d[-1],
        "bbands_upper_last": upper[-1],
        "adx14_last": adx[-1],
    }[key]
    assert got == pytest.approx(_GOLDEN[key], rel=1e-12, abs=1e-12), (
        f"{key} drifted from the 0.8.1 golden value: {got!r}"
    )
