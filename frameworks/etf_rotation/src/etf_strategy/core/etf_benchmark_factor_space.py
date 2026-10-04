"""ETF relative-market atoms computed from declared benchmark ETFs."""
from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd


def _safe_div(left: pd.DataFrame, right: pd.DataFrame | pd.Series) -> pd.DataFrame:
    denominator = right.replace(0.0, np.nan)
    return left.div(denominator, axis=0).replace([np.inf, -np.inf], np.nan)


def build_benchmark_factor_space(
    close: pd.DataFrame,
    benchmark_symbols: Sequence[str],
) -> dict[str, pd.DataFrame]:
    """Build market-relative features known by D close, without forward returns."""
    benchmarks = list(benchmark_symbols)
    missing = sorted(set(benchmarks) - set(close.columns))
    if not benchmarks or missing:
        raise ValueError(f"Invalid benchmark symbols; missing={missing}")
    close = close.astype(float)
    returns = close.pct_change(fill_method=None)
    market_return = returns[benchmarks].mean(axis=1, skipna=False)
    factors: dict[str, pd.DataFrame] = {}

    for window in (20, 60, 120):
        asset_momentum = close / close.shift(window) - 1.0
        market_growth = (1.0 + market_return).rolling(window, min_periods=window).apply(
            np.prod, raw=True
        ) - 1.0
        factors[f"REL_MARKET_MOM_{window}"] = asset_momentum.sub(market_growth, axis=0)

    for window in (20, 60):
        covariance = returns.rolling(window, min_periods=window).cov(market_return)
        market_variance = market_return.rolling(window, min_periods=window).var(ddof=1)
        beta = _safe_div(covariance, market_variance)
        factors[f"MARKET_BETA_{window}"] = beta
        factors[f"MARKET_CORR_{window}"] = returns.rolling(
            window, min_periods=window
        ).corr(market_return)
        residual_vol = returns.sub(
            market_return, axis=0
        ).rolling(window, min_periods=window).std(ddof=1)
        factors[f"BENCHMARK_RESIDUAL_VOL_{window}"] = residual_vol

        downside_market = market_return.where(market_return < 0.0)
        downside_asset = returns.where(market_return.lt(0.0), axis=0)
        numerator = downside_asset.mul(downside_market, axis=0).rolling(
            window, min_periods=max(5, window // 4)
        ).sum()
        denominator = downside_market.pow(2).rolling(
            window, min_periods=max(5, window // 4)
        ).sum()
        factors[f"DOWNSIDE_BETA_{window}"] = _safe_div(numerator, denominator)

        upside_market = market_return.where(market_return > 0.0)
        upside_asset = returns.where(market_return.gt(0.0), axis=0)
        upside_numerator = upside_asset.mul(upside_market, axis=0).rolling(
            window, min_periods=max(5, window // 4)
        ).sum()
        upside_denominator = upside_market.pow(2).rolling(
            window, min_periods=max(5, window // 4)
        ).sum()
        factors[f"UPSIDE_BETA_{window}"] = _safe_div(upside_numerator, upside_denominator)

    return {name: frame.where(np.isfinite(frame)) for name, frame in factors.items()}
