"""Two frozen domestic-bond auxiliary mechanisms for fixed-14 ETF IC discovery.

511010.SH is an auxiliary rate-sensitive ETF, never a fifteenth candidate.
Only information through the D close enters a score. The directions are
economic priors, not fitted signs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


WINDOW = 60
DIRECTIONS = {"bond_trend_exposure": 1, "bond_shock_underreaction": 1}


def _validate(config: dict, panels: dict) -> None:
    if config.get("source_type") != "auxiliary_bond":
        raise ValueError("auxiliary bond source_type required")
    if config.get("auxiliary_symbol") != "511010.SH":
        raise ValueError("fixed auxiliary bond symbol required")
    if config.get("windows") != [WINDOW] or config.get("mechanisms") is None:
        raise ValueError("fixed 60-day window required")
    for name, definition in config["mechanisms"].items():
        if name not in DIRECTIONS or definition.get("direction") != DIRECTIONS[name]:
            raise ValueError(f"unknown bond mechanism or changed direction: {name}")
    if set(panels) != {"close", "bond_close"}:
        raise ValueError("need ETF and auxiliary bond adjusted closes")
    if not panels["close"].index.equals(panels["bond_close"].index):
        raise ValueError("misaligned bond calendar")
    if list(panels["bond_close"].columns) != ["511010.SH"]:
        raise ValueError("bond auxiliary input must contain only 511010.SH")


def build_atoms(panels: dict, config: dict) -> dict[str, pd.DataFrame]:
    _validate(config, panels)
    close = panels["close"].astype(float)
    bond_close = panels["bond_close"]["511010.SH"].astype(float)
    own = close.pct_change(fill_method=None)
    bond = bond_close.pct_change(fill_method=None)
    variance = bond.rolling(WINDOW, min_periods=WINDOW).var(ddof=0)
    covariance = own.rolling(WINDOW, min_periods=WINDOW).cov(bond, ddof=0)
    beta = covariance.div(variance.where(variance.gt(0)), axis=0)
    trend20 = bond_close.pct_change(20, fill_method=None)
    shock5 = bond_close.pct_change(5, fill_method=None)
    own5 = close.pct_change(5, fill_method=None)
    raw = {
        "bond_trend_exposure": beta.mul(trend20, axis=0),
        "bond_shock_underreaction": beta.mul(shock5, axis=0) - own5,
    }
    return {f"{name}_{WINDOW}": (raw[name] * DIRECTIONS[name]).replace(
        [np.inf, -np.inf], np.nan)
        for name in config["mechanisms"]}


def leakage_checks(panels: dict, config: dict, cut: str) -> dict[str, bool]:
    full = build_atoms(panels, config)
    prefix = build_atoms({k: v.loc[:cut] for k, v in panels.items()}, config)
    changed = {k: v.copy() for k, v in panels.items()}
    for frame in changed.values():
        frame.loc[frame.index > cut] *= 1.73
    perturbed = build_atoms(changed, config)
    for name in full:
        pd.testing.assert_frame_equal(full[name].loc[:cut], prefix[name], check_exact=False,
                                      rtol=1e-9, atol=1e-12)
        pd.testing.assert_frame_equal(full[name].loc[:cut], perturbed[name].loc[:cut], check_exact=False,
                                      rtol=1e-9, atol=1e-12)
    return {name: True for name in full}
