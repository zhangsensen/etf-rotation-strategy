"""Fixed entry-price protection, separate from legacy high-water-mark stops.

Contract: entry VWAP * (1 - loss_pct), active from the next trading session;
daily intraday stop, gaps fill at open, no same-session re-entry. Fees are
charged separately, so the realized net loss is not capped at loss_pct.
"""
from __future__ import annotations

import math


def load_fixed_stop(config):
    risk = config.get("backtest", {}).get("risk_control", {})
    loss = float(risk.get("etf_stop_loss", 0.0))
    if not math.isfinite(loss) or not 0 <= loss < 1:
        raise ValueError("etf_stop_loss must be finite and in [0, 1)")
    mode = risk.get("etf_stop_execution", "next_session_intraday")
    if mode != "next_session_intraday":
        raise ValueError(f"Unsupported etf_stop_execution: {mode}")
    if not risk.get("enabled", True) or not risk.get("etf_stop_enabled", True):
        loss = 0.0
    if loss and (risk.get("stop_method", "fixed") != "fixed"
                 or float(risk.get("trailing_stop_pct", 0.0)) != 0):
        raise ValueError("Entry-price stop cannot be mixed with legacy ATR/trailing stops")
    return {"etf_stop_loss": loss,
            "etf_stop_start_date": risk.get("etf_stop_start_date")}
