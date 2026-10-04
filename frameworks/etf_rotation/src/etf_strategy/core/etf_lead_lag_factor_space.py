"""Cross-ETF lead-lag atoms known by D close."""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


def _safe_div(left: pd.DataFrame, right: pd.Series) -> pd.DataFrame:
    return left.div(right.replace(0.0, np.nan), axis=0).replace(
        [np.inf, -np.inf], np.nan
    )


def build_lead_lag_factor_space(
    close: pd.DataFrame,
    benchmark_symbols: Sequence[str],
    peer_symbols: Sequence[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Measure benchmark delay plus leave-one-out cross-ETF diffusion.

    Peer atoms use the other candidate ETFs' returns, never a same-day common
    return subtracted from the target.  ``peer_symbols`` is explicit so the
    candidate population cannot silently expand to benchmarks or defensive
    tools.
    """
    benchmarks = list(benchmark_symbols)
    missing = sorted(set(benchmarks) - set(close.columns))
    if not benchmarks or missing:
        raise ValueError(f"Invalid lead-lag benchmark symbols; missing={missing}")
    returns = close.astype(float).pct_change(fill_method=None)
    market = returns[benchmarks].mean(axis=1, skipna=False)
    lagged_market = market.shift(1)
    factors: dict[str, pd.DataFrame] = {}
    for window in (20, 60):
        covariance = returns.rolling(window, min_periods=window).cov(lagged_market)
        variance = lagged_market.rolling(window, min_periods=window).var(ddof=1)
        factors[f"MARKET_LEAD_BETA_{window}"] = _safe_div(covariance, variance)
        factors[f"MARKET_LEAD_CORR_{window}"] = returns.rolling(
            window, min_periods=window
        ).corr(lagged_market)
        factors[f"ASSET_LEAD_MARKET_CORR_{window}"] = returns.shift(1).rolling(
            window, min_periods=window
        ).corr(market)

    peers = list(peer_symbols) if peer_symbols is not None else list(close.columns)
    missing_peers = sorted(set(peers) - set(close.columns))
    if missing_peers:
        raise ValueError(f"peer_symbols must contain at least 3 available ETFs; missing={missing_peers}")
    if peer_symbols is None and len(peers) < 3:
        return {name: frame.where(np.isfinite(frame)) for name, frame in factors.items()}
    if len(peers) < 3:
        raise ValueError("peer_symbols must contain at least 3 available ETFs")
    peer_returns = returns[peers]
    for window in (20, 60):
        lead_beta = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
        lead_corr = lead_beta.copy()
        network_corr = lead_beta.copy()
        for symbol in peers:
            others = [item for item in peers if item != symbol]
            peer_mean = peer_returns[others].mean(axis=1, skipna=True)
            lagged_peer = peer_mean.shift(1)
            covariance = returns[symbol].rolling(window, min_periods=window).cov(lagged_peer)
            variance = lagged_peer.rolling(window, min_periods=window).var(ddof=1)
            lead_beta.loc[:, symbol] = covariance.div(variance.replace(0.0, np.nan))
            lead_corr.loc[:, symbol] = returns[symbol].rolling(window, min_periods=window).corr(lagged_peer)
            # A node's delayed connectivity to the rest of the candidate graph
            # is a diffusion statistic. Using lagged peers avoids turning the
            # same-day common move into a relative-strength family.
            pair_corrs = [returns[symbol].rolling(window, min_periods=window).corr(peer_returns[other].shift(1)) for other in others]
            network_corr.loc[:, symbol] = pd.concat(pair_corrs, axis=1).mean(axis=1)
        factors[f"PEER_LEAD_BETA_{window}"] = lead_beta
        factors[f"PEER_LEAD_CORR_{window}"] = lead_corr
        factors[f"PEER_LEAD_NETWORK_CORR_{window}"] = network_corr
    return {
        name: frame.where(np.isfinite(frame))
        for name, frame in factors.items()
    }
