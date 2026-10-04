"""Approved daily group-mechanism atoms for the ETF IC batch 2.

The functions here only build member-by-date atoms.  Group aggregation and IC
evaluation remain in the existing discovery/evidence layers.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


MECHANISMS = ("shock_session_response", "downshock_recovery")


def _rolling_ratio(numerator: pd.DataFrame, denominator: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling ratio with complete-window semantics and no zero fallback."""
    num = numerator.rolling(window, min_periods=window).sum()
    den = denominator.rolling(window, min_periods=window).sum()
    return num.div(den.where(den.ne(0)))


def build_atoms(panels: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    """Return approved member x date atoms, using data available by D close.

    ``shock_session_response`` measures session response to the magnitude of an
    overnight shock. ``downshock_recovery`` measures the next-session response
    conditional on the prior session's downside shock. Both are direction +1;
    direction is deliberately not applied here so the returned atom is the
    stated raw mechanism.
    """
    windows = tuple(cfg.get("windows", (20)))
    if windows != (20,):
        raise ValueError("batch 2 is frozen to window 20")
    definitions = cfg.get('mechanisms', {})
    if set(definitions) != set(MECHANISMS) or any(
        definitions[name].get('direction') != 1 for name in MECHANISMS
    ):
        raise ValueError('batch 2 requires exactly two approved +1 mechanisms')
    missing = {k for k in ("open", "close") if k not in panels}
    if missing:
        raise KeyError(f"missing daily panels: {sorted(missing)}")
    close = panels["close"].astype(float)
    open_ = panels["open"].astype(float)
    if not close.index.equals(open_.index) or not close.columns.equals(open_.columns):
        raise ValueError("open/close panels must have identical member-date axes")

    with np.errstate(divide="ignore", invalid="ignore"):
        gap = open_.div(close.shift(1)) - 1.0
        session = close.div(open_) - 1.0
        response = _rolling_ratio(gap.abs() * session, gap.pow(2), 20)

        ret = close.pct_change(fill_method=None)
        q = ret.clip(upper=0).abs()
        recovery = _rolling_ratio(q.shift(1) * ret, q.shift(1).pow(2), 20)

    atoms = {
        "shock_session_response_20": response,
        "downshock_recovery_20": recovery,
    }
    return {name: value.replace([np.inf, -np.inf], np.nan) for name, value in atoms.items()}


def leakage_checks(panels: dict[str, pd.DataFrame], cfg: dict, cut: str | pd.Timestamp) -> dict[str, bool]:
    """Assert prefix invariance and future-value perturbation invariance."""
    cut = pd.Timestamp(cut)
    full = build_atoms(panels, cfg)
    prefix_panels = {k: v.loc[:cut].copy() for k, v in panels.items()}
    prefix = build_atoms(prefix_panels, cfg)
    perturbed = {k: v.copy() for k, v in panels.items()}
    for value in perturbed.values():
        value.loc[value.index > cut] *= 1.71
    future = build_atoms(perturbed, cfg)
    checks: dict[str, bool] = {}
    for name, atom in full.items():
        pd.testing.assert_frame_equal(
            atom.loc[:cut], prefix[name].loc[:cut], check_exact=False, rtol=1e-10, atol=1e-12
        )
        pd.testing.assert_frame_equal(
            atom.loc[:cut], future[name].loc[:cut], check_exact=False, rtol=1e-10, atol=1e-12
        )
        checks[f"{name}:prefix"] = True
        checks[f"{name}:future_perturbation"] = True
    return checks
