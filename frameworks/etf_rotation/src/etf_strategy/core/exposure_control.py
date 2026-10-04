"""Fee-aware reduction of retained positions to a prescribed exposure ceiling.

This is an execution rule, not another timing signal or a new allocation model.
It never increases retained positions, changes their relative weights, or reads
future prices. Call after pricing ordinary rotation sells at the execution open.
"""
from __future__ import annotations

import math


def retained_scale(cash, values, rates, target):
    """Return proportional retained-quantity multiplier, accounting for sell fees."""
    if not math.isfinite(target) or not 0 <= target <= 1:
        raise ValueError("Exposure target must be finite and in [0, 1]")
    if not math.isfinite(cash) or cash < -.01:
        raise ValueError("Invalid cash for exposure control")
    if any(not math.isfinite(v) or v < 0 for v in values.values()):
        raise ValueError("Invalid retained position value")
    if any(not math.isfinite(rates[t]) or not 0 <= rates[t] < 1 for t in values):
        raise ValueError("Invalid transaction cost")
    kept = sum(values.values())
    nav = cash + kept
    if kept <= 0 or kept <= target * nav:
        return 1.0
    weighted_fee = sum(v * rates[t] for t, v in values.items()) / kept
    # kept - sold = target * (nav - sold * weighted_fee)
    sold = (kept - target * nav) / (1 - target * weighted_fee)
    return max(0.0, min(1.0, 1 - sold / kept))


def load_exposure_control(config):
    control = config.get("backtest", {}).get("exposure_control", {})
    mode = control.get("mode", "legacy")
    if mode not in ("legacy", "cap_retained"):
        raise ValueError(f"Unsupported exposure_control mode: {mode}")
    return {"exposure_control": mode, "exposure_start_date": control.get("start_date")}
