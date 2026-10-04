"""Stage-15 family: coskewness_risk — systematic higher-moment (co-skew /
co-kurtosis) risk vs the market benchmark, directive 2026-09-20 round_080.

Literature anchors (also recorded in family_coskewness_risk_v1.yaml):
- Harvey & Siddique (2000), "Conditional Skewness in Asset Pricing Tests",
  Journal of Finance — coskewness E[(r_i-mu_i)(r_m-mu_m)^2] / (sigma_i *
  var_m); assets with more negative coskewness (crash-risk exposure) earn
  higher expected returns.
- Ang, Chen & Xing (2006), "Downside Risk", Review of Financial Studies —
  conditional/downside coskewness computed only over market-down days.
- Dittmar (2002), "Nonlinear Pricing Kernels, Kurtosis Preference, and
  Evidence from the Cross Section of Equity Returns", Journal of Finance —
  cokurtosis E[(r_i-mu_i)(r_m-mu_m)^3] / (sigma_i * sigma_m^3).

Benchmark = equal-weight mean return of the declared benchmark ETFs
(510300.SH, 510500.SH), matching the market_sensitivity family convention
so the two families are directly comparable in atom_health.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "COSKEW_20",
    "COSKEW_60",
    "COSKEW_CHG_20",
    "DOWNSIDE_COSKEW_60",
    "COKURT_60",
)


def _windows(arr: np.ndarray, window: int) -> np.ndarray:
    n = len(arr)
    if n < window:
        return np.empty((0, window))
    return np.lib.stride_tricks.sliding_window_view(arr, window)


def _coskew(x: np.ndarray, m: np.ndarray, window: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    xw, mw = _windows(x, window), _windows(m, window)
    if not len(xw):
        return out
    valid = np.isfinite(xw).all(axis=1) & np.isfinite(mw).all(axis=1)
    xbar, mbar = xw.mean(axis=1), mw.mean(axis=1)
    ex, em = xw - xbar[:, None], mw - mbar[:, None]
    numerator = (ex * em ** 2).mean(axis=1)
    denom = xw.std(axis=1, ddof=1) * mw.var(axis=1, ddof=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        val = np.where(valid & (denom > 0), numerator / denom, np.nan)
    out[window - 1:] = val
    return out


def _cokurt(x: np.ndarray, m: np.ndarray, window: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    xw, mw = _windows(x, window), _windows(m, window)
    if not len(xw):
        return out
    valid = np.isfinite(xw).all(axis=1) & np.isfinite(mw).all(axis=1)
    xbar, mbar = xw.mean(axis=1), mw.mean(axis=1)
    ex, em = xw - xbar[:, None], mw - mbar[:, None]
    numerator = (ex * em ** 3).mean(axis=1)
    denom = xw.std(axis=1, ddof=1) * (mw.std(axis=1, ddof=1) ** 3)
    with np.errstate(invalid="ignore", divide="ignore"):
        val = np.where(valid & (denom > 0), numerator / denom, np.nan)
    out[window - 1:] = val
    return out


def _downside_coskew(x: np.ndarray, m: np.ndarray, window: int, min_down: int = 15) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan)
    for t in range(window - 1, n):
        xs = x[t - window + 1: t + 1]
        ms = m[t - window + 1: t + 1]
        mask = np.isfinite(xs) & np.isfinite(ms) & (ms < 0.0)
        if mask.sum() < min_down:
            continue
        xsub, msub = xs[mask], ms[mask]
        xbar, mbar = xsub.mean(), msub.mean()
        ex, em = xsub - xbar, msub - mbar
        numerator = float(np.mean(ex * em ** 2))
        sigma_x = float(np.std(xsub, ddof=1))
        var_m = float(np.var(msub, ddof=1))
        denom = sigma_x * var_m
        if denom > 0:
            out[t] = numerator / denom
    return out


def _build(panels, eligibility, data_root, config):
    benchmarks = list(config["benchmark_symbols"])
    close = panels["close"].astype(float)
    returns = close.pct_change(fill_method=None)
    market_return = returns[benchmarks].mean(axis=1, skipna=False)
    dates = close.index
    symbols = list(close.columns)
    m = market_return.to_numpy(float)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}
    for sym in symbols:
        x = returns[sym].to_numpy(float)
        coskew20 = _coskew(x, m, 20)
        coskew60 = _coskew(x, m, 60)
        cokurt60 = _cokurt(x, m, 60)
        down60 = _downside_coskew(x, m, 60)
        chg20 = pd.Series(coskew60, index=dates)
        chg20 = (chg20 - chg20.shift(20)).to_numpy(float)
        out["COSKEW_20"][sym] = coskew20
        out["COSKEW_60"][sym] = coskew60
        out["COSKEW_CHG_20"][sym] = chg20
        out["DOWNSIDE_COSKEW_60"][sym] = down60
        out["COKURT_60"][sym] = cokurt60
    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("coskewness_risk", "coskewness_risk", _build))
