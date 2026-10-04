"""Frozen NASDAQ-100 beta exposure atom for fixed-14 ETF IC discovery.

The caller supplies latest-known US returns aligned to A-share dates. Its
source observation date must be strictly earlier than the A-share signal date
and no more than five calendar days old. The atom is beta_i,D-1 * u_D, where
beta is estimated from the latest 60 paired A-share sessions ending by D-1.
Group aggregation and IC evaluation remain in the discovery/evidence layers.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


WINDOW = 60
SERIES = "NASDAQ100"
MECHANISM = "us_lagged_transmission"
ATOM = f"{MECHANISM}_{WINDOW}"
DIRECTION = 1
CANDIDATES = {
    "159995.SZ", "159516.SZ", "515880.SH", "159852.SZ", "562500.SH",
    "159732.SZ", "513130.SH", "159992.SZ", "513120.SH", "518880.SH",
    "512400.SH", "512890.SH", "159611.SZ", "513100.SH",
}


def _validate(panels: dict, config: dict) -> tuple[pd.DataFrame, pd.Series]:
    if config.get("source_type") != "us_index":
        raise ValueError("US index source_type required")
    if config.get("series") != SERIES:
        raise ValueError("fixed NASDAQ100 series required")
    if config.get("windows") != [WINDOW]:
        raise ValueError("fixed 60 paired-session window required")
    definitions = config.get("mechanisms")
    if (not isinstance(definitions, dict) or set(definitions) != {MECHANISM}
            or definitions[MECHANISM].get("direction") != DIRECTION):
        raise ValueError("exactly one fixed +1 NASDAQ100 beta mechanism required")
    if set(panels) != {"close", "us_return"}:
        raise ValueError("need ETF closes and aligned NASDAQ100 returns")

    close = panels["close"].astype(float)
    us = panels["us_return"]
    if not isinstance(us, pd.DataFrame) or list(us.columns) != [SERIES]:
        raise ValueError("us_return must contain only the NASDAQ100 column")
    us = us[SERIES].astype(float)
    if not close.index.equals(us.index):
        raise ValueError("ETF and US return panels must use the same A-share calendar")
    if not close.index.is_unique or not close.index.is_monotonic_increasing:
        raise ValueError("A-share calendar must be unique and sorted")
    if close.columns.has_duplicates or set(close.columns) != CANDIDATES:
        raise ValueError("ETF close panel must contain exactly the fixed 14 candidates")
    if np.isinf(close.to_numpy()).any() or np.isinf(us.to_numpy()).any():
        raise ValueError("close and aligned US returns may not contain infinity")
    return close, us


def _rolling_60_pair_beta(own_return: pd.Series, prior_us_return: pd.Series) -> pd.Series:
    """Estimate rolling beta on exactly 60 consecutive A-share session rows."""
    valid = own_return.notna() & prior_us_return.notna()
    own = own_return.where(valid)
    us = prior_us_return.where(valid)
    variance = us.rolling(WINDOW, min_periods=WINDOW).var(ddof=1)
    covariance = own.rolling(WINDOW, min_periods=WINDOW).cov(us, ddof=1)
    return covariance.div(variance.where(variance.gt(0)))


def build_atoms(panels: dict, config: dict) -> dict[str, pd.DataFrame]:
    """Return the member-date score beta_i,D-1 * latest-known NASDAQ100 return_D.

    ``us_return`` is expected to have been aligned by the caller using a strict
    source-date < signal-date as-of join and a five-calendar-day staleness cap.
    The beta pairs each ETF close return on s with the US return available on
    the prior A-share session s-1. Direction is fixed at +1.
    """
    close, us_return = _validate(panels, config)
    own_return = close.pct_change(fill_method=None)
    prior_us_return = us_return.shift(1)
    raw = pd.DataFrame(np.nan, index=close.index, columns=close.columns, dtype=float)
    for symbol in close.columns:
        beta_through_previous = _rolling_60_pair_beta(
            own_return[symbol], prior_us_return
        ).shift(1)
        raw[symbol] = beta_through_previous * us_return
    return {ATOM: raw.replace([np.inf, -np.inf], np.nan)}


def leakage_checks(panels: dict, config: dict, cut: str | pd.Timestamp) -> dict[str, bool]:
    """Assert prefix invariance and invariance to all post-cut input changes."""
    cut = pd.Timestamp(cut)
    full = build_atoms(panels, config)
    prefix_panels = {key: value.loc[:cut].copy() for key, value in panels.items()}
    prefix = build_atoms(prefix_panels, config)
    changed = {key: value.copy() for key, value in panels.items()}
    for value in changed.values():
        value.loc[value.index > cut] *= 1.73
    perturbed = build_atoms(changed, config)
    for name, atom in full.items():
        pd.testing.assert_frame_equal(
            atom.loc[:cut], prefix[name].loc[:cut], check_exact=False,
            rtol=1e-10, atol=1e-12,
        )
        pd.testing.assert_frame_equal(
            atom.loc[:cut], perturbed[name].loc[:cut], check_exact=False,
            rtol=1e-10, atol=1e-12,
        )
    return {f"{name}:prefix_and_future_perturbation": True for name in full}
