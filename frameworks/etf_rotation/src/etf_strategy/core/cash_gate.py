"""Absolute risk-off gate built only from already shifted timing inputs.

The gate answers whether the portfolio may participate. It does not rank ETFs,
change factor scores, or introduce a new threshold. ``dual_worst`` maps the
existing light-timing defensive state AND the existing regime gate's lowest
configured exposure to cash. Inputs must already be available for the decision
date; shifting remains the caller's responsibility.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def load_cash_gate(config):
    backtest = config.get("backtest", {})
    cfg = backtest.get("cash_gate", {})
    mode = str(cfg.get("mode", "disabled"))
    if mode not in ("disabled", "dual_worst"):
        raise ValueError(f"Unsupported cash_gate mode: {mode}")
    if mode == "dual_worst":
        if not bool(backtest.get("timing", {}).get("enabled", True)):
            raise ValueError("dual_worst cash gate requires timing.enabled")
        regime = backtest.get("regime_gate", {})
        if not bool(regime.get("enabled", False)):
            raise ValueError("dual_worst cash gate requires regime_gate.enabled")
        if regime.get("mode", "volatility") != "volatility":
            raise ValueError("dual_worst is frozen to the volatility regime gate")
        exposure = backtest.get("exposure_control", {})
        if exposure.get("mode", "legacy") != "cap_retained":
            raise ValueError("cash gate requires cap_retained execution")
    return {"mode": mode, "start_date": cfg.get("start_date")}


def apply_cash_gate(timing, regime, dates, config):
    """Return adjusted target exposures and an auditable decision table."""
    timing = np.asarray(timing, dtype=np.float64)
    regime = np.asarray(regime, dtype=np.float64)
    dates = pd.DatetimeIndex(dates)
    if timing.ndim != 1 or regime.ndim != 1 or len(timing) != len(regime) or len(timing) != len(dates):
        raise ValueError("cash gate inputs must be aligned 1D arrays")
    if not np.isfinite(timing).all() or not np.isfinite(regime).all():
        raise ValueError("cash gate inputs must be finite")
    cfg = load_cash_gate(config)
    adjusted = timing * regime
    risk_off = np.zeros(len(dates), dtype=bool)
    active = np.zeros(len(dates), dtype=bool)
    if cfg["mode"] == "dual_worst":
        backtest = config["backtest"]
        defensive = float(backtest["timing"]["extreme_position"])
        exposures = tuple(backtest["regime_gate"]["volatility"]["exposures"])
        if not exposures:
            raise ValueError("volatility exposures cannot be empty")
        worst = float(min(exposures))
        active[:] = True
        if cfg["start_date"]:
            active &= dates >= pd.Timestamp(cfg["start_date"])
        risk_off = active & np.isclose(timing, defensive) & np.isclose(regime, worst)
        adjusted[risk_off] = 0.0
    audit = pd.DataFrame({
        "date": dates, "cash_gate_active": active, "light_timing": timing,
        "regime_gate": regime, "risk_off": risk_off, "target_exposure": adjusted,
    }).set_index("date")
    return adjusted, audit
