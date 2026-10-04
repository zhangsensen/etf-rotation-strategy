#!/usr/bin/env python3
"""Literature close-price factors for the long-history discovery panel
(PREREG_LONGHISTORY_DISCOVERY_20260924.md §2(b)).

Every function here takes a generic `close: pd.DataFrame` (any column
count/naming -- the same "close(D) only" convention etf_group_claude_
rounds.py's generic candidates already use) so the SAME implementation
runs unchanged on either the 8-group discovery proxy panel or the real
14-member ETF panel later (prereg: "同一公式在两套面板上用同一实现"). Where
an existing registered candidate in etf_group_claude_rounds.py already
implements a literature concept (e.g. momentum_250_skip20 for "12-1 skip-
month momentum"), that candidate is reused directly (source=a in
CATALOG.csv) and NOT reimplemented here -- see the driver script's own
catalog-building notes for which of the 17 named literature concepts map
to an existing (a) candidate vs a new (b) function in this file.

"EW8" throughout = the equal-weight mean of whatever columns are passed
in (8 discovery-panel groups, or -- unchanged code -- 14 real members
later), on dates all columns are valid; this mirrors etf_group_claude_
rounds.py's own _market_return convention exactly, just renamed for
clarity in a discovery-panel context where the columns ARE the 8 groups
already (no further member->group aggregation needed).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from etf_strategy.core.etf_group_claude_rounds import _rolling_beta  # noqa: E402


def _ew8_return(close: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    ew8 = returns.mean(axis=1).where(all_valid)
    return returns, ew8


def build_trailing_return(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Plain trailing `window`-day return: close(t)/close(t-window) - 1.
    Serves BOTH the momentum_N (N in 5/20/60/120/250) and reversal_N (N in
    5/20) catalog rows -- momentum_5/reversal_5 and momentum_20/reversal_20
    are the IDENTICAL formula with opposite a-priori hypothesis labels;
    the prereg's own discovery protocol (direction = discovered IC sign,
    §3.2) resolves which hypothesis the data supports, and the dedup step
    (§3.4, correlation 1.0 between the two identically-formulaed rows)
    will naturally collapse the redundant one -- not something this
    catalog build unilaterally decides."""
    return close.pct_change(window, fill_method=None)


def build_realized_vol(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling `window`-day realized volatility (std of daily returns).
    Literature vol_20/vol_60."""
    returns = close.pct_change(fill_method=None)
    return returns.rolling(window, min_periods=window).std()


def build_beta_to_ew8(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling `window`-day beta of each column's own return on EW8 (the
    equal-weight mean of all columns, all-valid-days-only). Literature
    "对EW8的贝塔"."""
    returns, ew8 = _ew8_return(close)
    return _rolling_beta(ew8, returns, window, window)


def build_idio_vol(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling `window`-day std of the EW8-market-model RESIDUAL (return
    minus beta*EW8, using the SAME rolling beta as build_beta_to_ew8, not
    a separately-estimated one -- consistent single market-model fit).
    Literature "特质波动" (idiosyncratic volatility)."""
    returns, ew8 = _ew8_return(close)
    beta = _rolling_beta(ew8, returns, window, window)
    fitted = beta.mul(ew8, axis=0)
    residual = returns.sub(fitted)
    return residual.rolling(window, min_periods=window).std()


def build_residual_momentum(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Trailing `window`-day CUMULATIVE residual return (return minus its
    own EW8-beta-implied fitted return, summed over the window, not
    compounded -- a momentum-style factor on the market-model residual
    rather than the raw price). Literature "残差动量"."""
    returns, ew8 = _ew8_return(close)
    beta = _rolling_beta(ew8, returns, window, window)
    fitted = beta.mul(ew8, axis=0)
    residual = returns.sub(fitted)
    return residual.rolling(window, min_periods=window).sum()


def build_max5(close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Highest single-day return over the trailing `window` (default 5)
    days -- the Bali/Cakici/Whitelaw "MAX" lottery-demand factor.
    Literature "MAX5"."""
    returns = close.pct_change(fill_method=None)
    return returns.rolling(window, min_periods=window).max()


def build_skew(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling `window`-day skewness of daily returns (pandas' own Fisher-
    adjusted .skew()). Literature "偏度60"."""
    returns = close.pct_change(fill_method=None)
    return returns.rolling(window, min_periods=window).skew()


def build_downside_beta(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling `window`-day beta of each column's own return on EW8,
    computed ONLY on days EW8's own return is negative (same down-day
    conditioning convention as etf_group_claude_rounds.py's beta_
    asymmetry candidate, applied here as a standalone downside beta
    rather than an up-minus-down GAP). Literature "下行贝塔"."""
    returns, ew8 = _ew8_return(close)
    down_mask = ew8.lt(0)
    min_periods = max(10, window // 4)
    return _rolling_beta(
        ew8.where(down_mask), returns.where(down_mask, axis=0), window, min_periods
    )


def build_corr_to_ew8_change(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """corr(own return, EW8) on a short (20-day) window minus its own long
    (60-day) window value -- is co-movement with the broad proxy pool
    currently rising relative to its own recent history. Same term-
    structure construction as etf_group_claude_rounds.py's corr_
    stability_20_60/peer_corr_network_change. Registered window is 60
    (the longer of its own two fixed internal legs, 20 and 60). Literature
    "与EW8相关性变化"."""
    del window  # this candidate's own two legs are fixed at 20 and 60
    returns, ew8 = _ew8_return(close)

    def corr_at(w):
        x_mean = ew8.rolling(w, min_periods=w).mean()
        y_mean = returns.rolling(w, min_periods=w).mean()
        cov = returns.mul(ew8, axis=0).rolling(w, min_periods=w).mean().sub(y_mean.mul(x_mean, axis=0))
        x_var = ew8.pow(2).rolling(w, min_periods=w).mean() - x_mean.pow(2)
        y_var = returns.pow(2).rolling(w, min_periods=w).mean() - y_mean.pow(2)
        denom = y_var.where(y_var > 0).mul(x_var.where(x_var > 0), axis=0).pow(0.5)
        return cov.div(denom)

    return corr_at(20) - corr_at(60)
