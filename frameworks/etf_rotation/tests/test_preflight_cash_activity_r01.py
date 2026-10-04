"""Synthetic timing checks for the label-free draft cash-activity features."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


PATH = Path(__file__).resolve().parents[1] / "scripts/research/preflight_cash_activity_r01.py"
SPEC = importlib.util.spec_from_file_location("preflight_cash_activity_r01", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_d_score_uses_preexisting_beta_not_d_return_or_d_shock_in_fit() -> None:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2025-01-01", periods=140)
    names = [f"ETF{i}" for i in range(8)]
    returns = rng.normal(0, 0.01, (len(dates), len(names)))
    close = pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), index=dates, columns=names)
    x = rng.normal(0, 0.1, len(dates))
    cash = pd.Series(1e10 * np.exp(np.cumsum(x)), index=dates)
    groups = {f"G{i}": {"members": [name]} for i, name in enumerate(names)}
    base = MODULE.feature_scores(close, cash, groups)
    d = dates[110]

    changed_close = close.copy()
    changed_close.loc[d, "ETF0"] *= 1.8
    same_cash = MODULE.feature_scores(changed_close, cash, groups)
    for name in base:
        pd.testing.assert_series_equal(base[name].loc[d], same_cash[name].loc[d])

    changed_cash = cash.copy()
    x_d = np.log(cash.loc[d] / cash.shift(1).loc[d])
    changed_cash.loc[d:] *= np.exp(0.1 * x_d)  # Keep x_D's sign; future shocks unchanged.
    moved = MODULE.feature_scores(close, changed_cash, groups)
    scale = np.log(changed_cash.loc[d] / changed_cash.shift(1).loc[d]) / np.log(cash.loc[d] / cash.shift(1).loc[d])
    for name in base:
        np.testing.assert_allclose(moved[name].loc[d].to_numpy(),
                                   base[name].loc[d].to_numpy() * scale, rtol=1e-10, atol=1e-10)
