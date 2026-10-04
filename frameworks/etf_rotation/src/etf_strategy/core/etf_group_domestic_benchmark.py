"""Frozen D-close domestic benchmark features for fixed-14 ETF IC research.

510300/510500 are auxiliary benchmark-role inputs, never candidate members.
Both mechanisms use only trailing exchange sessions through the signal close.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

WINDOW = 60
BENCHMARKS = ["510300.SH", "510500.SH"]
MECHANISMS = {"cn_mid_large_style_transmission": 1,
              "cn_largecap_downside_resilience": 1}
CANDIDATES = {
    "159995.SZ", "159516.SZ", "515880.SH", "159852.SZ", "562500.SH",
    "159732.SZ", "513130.SH", "159992.SZ", "513120.SH", "518880.SH",
    "512400.SH", "512890.SH", "159611.SZ", "513100.SH",
}


def _validate(panels: dict, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    if config.get("source_type") != "domestic_benchmark" or config.get("windows") != [WINDOW]:
        raise ValueError("frozen domestic benchmark source/60-session window required")
    if config.get("auxiliary_symbols") != BENCHMARKS:
        raise ValueError("exact benchmark-role 510300/510500 inputs required")
    definitions = config.get("mechanisms")
    if not isinstance(definitions, dict) or definitions.keys() != MECHANISMS.keys():
        raise ValueError("both frozen domestic benchmark mechanisms required")
    if any(definitions[name].get("direction") != sign for name, sign in MECHANISMS.items()):
        raise ValueError("domestic benchmark direction changed")
    if set(panels) != {"close", "benchmark_close"}:
        raise ValueError("need candidate and benchmark adjusted closes only")
    close = panels["close"].astype(float)
    benchmark = panels["benchmark_close"].astype(float)
    if (list(benchmark.columns) != BENCHMARKS or set(close.columns) != CANDIDATES or
            close.columns.has_duplicates or not close.index.equals(benchmark.index) or
            close.index.has_duplicates or not close.index.is_monotonic_increasing):
        raise ValueError("fixed 14/eight benchmark calendar alignment violated")
    if np.isinf(close.to_numpy()).any() or np.isinf(benchmark.to_numpy()).any():
        raise ValueError("infinite benchmark or ETF close")
    return close, benchmark


def build_atoms(panels: dict, config: dict) -> dict[str, pd.DataFrame]:
    close, benchmark = _validate(panels, config)
    own = close.pct_change(fill_method=None)
    large = benchmark[BENCHMARKS[0]].pct_change(fill_method=None)
    mid = benchmark[BENCHMARKS[1]].pct_change(fill_method=None)
    spread = mid - large
    spread_var = spread.rolling(WINDOW, min_periods=WINDOW).var(ddof=0).where(lambda x: x.gt(0))
    beta_style = own.rolling(WINDOW, min_periods=WINDOW).cov(spread, ddof=0).div(spread_var, axis=0)
    style20 = (benchmark[BENCHMARKS[1]].div(benchmark[BENCHMARKS[1]].shift(20))
               .div(benchmark[BENCHMARKS[0]].div(benchmark[BENCHMARKS[0]].shift(20))).sub(1))
    style_score = beta_style.mul(style20, axis=0)

    down = large.where(large.lt(0))
    down_var = down.rolling(WINDOW, min_periods=10).var(ddof=0).where(lambda x: x.gt(0))
    paired_all = own.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW)
    paired_all &= large.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW).to_numpy()[:, None]
    beta_down = own.where(large.lt(0), axis=0).rolling(WINDOW, min_periods=10).cov(down, ddof=0)
    downside_score = -beta_down.div(down_var, axis=0).where(paired_all)
    return {
        "cn_mid_large_style_transmission_60": style_score.replace([np.inf, -np.inf], np.nan),
        "cn_largecap_downside_resilience_60": downside_score.replace([np.inf, -np.inf], np.nan),
    }


def leakage_checks(panels: dict, config: dict, cut: str | pd.Timestamp) -> dict[str, bool]:
    cut = pd.Timestamp(cut)
    full = build_atoms(panels, config)
    prefix = build_atoms({key: frame.loc[:cut].copy() for key, frame in panels.items()}, config)
    changed = {key: frame.copy() for key, frame in panels.items()}
    for frame in changed.values():
        frame.loc[frame.index > cut] *= 1.73
    perturbed = build_atoms(changed, config)
    for name, atom in full.items():
        pd.testing.assert_frame_equal(atom.loc[:cut], prefix[name], check_exact=False,
                                      rtol=1e-10, atol=1e-12)
        pd.testing.assert_frame_equal(atom.loc[:cut], perturbed[name].loc[:cut], check_exact=False,
                                      rtol=1e-10, atol=1e-12)
    return {f"{name}:prefix_and_future_perturbation": True for name in full}
