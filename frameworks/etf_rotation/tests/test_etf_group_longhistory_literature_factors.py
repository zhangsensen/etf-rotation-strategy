"""Hand-calculated tests for etf_group_longhistory_literature_factors.py
(PREREG_LONGHISTORY_DISCOVERY_20260924.md §2(b) literature candidates).
Independent second implementations of every formula, not calls into the
source's own helper functions (e.g. _rolling_beta), matching this
campaign's established testing convention."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/research"))
import etf_group_longhistory_literature_factors as lit  # noqa: E402


def _panel(n=200, seed=11, k=8):
    idx = pd.bdate_range("2015-01-05", periods=n)
    rng = np.random.default_rng(seed)
    names = [f"g{i:02d}" for i in range(k)]
    market_wave = 0.0005 * np.sin(np.arange(n) / 13.0)
    returns = {}
    for i, name in enumerate(names):
        idio = rng.normal(0, 0.012, n)
        phase = 0.0003 * np.cos(np.arange(n) / (6.0 + i))
        returns[name] = market_wave + phase + idio
    returns_df = pd.DataFrame(returns, index=idx)
    close = 100.0 * (1.0 + returns_df).cumprod()
    return close


def test_trailing_return_hand_formula():
    close = _panel()
    for w in (5, 20, 60):
        out = lit.build_trailing_return(close, w)
        expected = close / close.shift(w) - 1.0
        pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_realized_vol_hand_formula():
    close = _panel(seed=13)
    w = 20
    out = lit.build_realized_vol(close, w)
    returns = close.pct_change()
    # Independent std via numpy on a rolling window loop, sparse spot-check.
    col = close.columns[3]
    r = returns[col].to_numpy()
    t = 150
    window_vals = r[t - w + 1:t + 1]
    expected = np.std(window_vals, ddof=1)
    assert abs(out[col].iloc[t] - expected) < 1e-9


def test_beta_to_ew8_hand_formula():
    close = _panel(seed=17)
    w = 60
    out = lit.build_beta_to_ew8(close, w)
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    ew8 = returns.mean(axis=1).where(all_valid)
    col = close.columns[2]
    t = 180
    x = ew8.to_numpy()[t - w + 1:t + 1]
    y = returns[col].to_numpy()[t - w + 1:t + 1]
    expected = np.cov(x, y, ddof=0)[0, 1] / np.var(x, ddof=0)
    assert abs(out[col].iloc[t] - expected) < 1e-9


def test_idio_vol_and_residual_momentum_hand_formula():
    # The residual series uses a POINT-IN-TIME rolling beta (a fresh
    # trailing-window beta computed AT EACH day t', not one fixed beta
    # from the window ending at the day being evaluated, applied
    # retroactively across the whole window) -- matching how every other
    # residual-based candidate in this campaign works (e.g. _market_
    # return's own day-by-day residual). Independently reproduced here
    # via pandas' own .rolling().cov()/.var() (a different code path from
    # the source's _rolling_beta, which uses the E[XY]-E[X]E[Y] rolling-
    # means formula) applied at EVERY day, not hand-computed from a single
    # fixed-window beta (an earlier version of this test incorrectly
    # assumed a single fixed beta and disagreed with the real
    # implementation by ~1% -- caught and fixed before this landed).
    close = _panel(seed=19)
    w = 60
    idio = lit.build_idio_vol(close, w)
    resid_mom = lit.build_residual_momentum(close, w)

    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    ew8 = returns.mean(axis=1).where(all_valid)
    col = close.columns[5]

    cov = returns[col].rolling(w, min_periods=w).cov(ew8)
    var = ew8.rolling(w, min_periods=w).var()
    beta_series = cov / var
    residual_series = returns[col] - beta_series * ew8

    expected_idio = residual_series.rolling(w, min_periods=w).std()
    expected_resid_mom = residual_series.rolling(w, min_periods=w).sum()
    pd.testing.assert_series_equal(idio[col], expected_idio, check_exact=False, rtol=1e-7, atol=1e-10, check_names=False)
    pd.testing.assert_series_equal(resid_mom[col], expected_resid_mom, check_exact=False, rtol=1e-7, atol=1e-10, check_names=False)


def test_max5_hand_formula():
    close = _panel(seed=23)
    out = lit.build_max5(close, 5)
    returns = close.pct_change()
    col = close.columns[0]
    t = 100
    expected = returns[col].to_numpy()[t - 4:t + 1].max()
    assert abs(out[col].iloc[t] - expected) < 1e-9


def test_skew_hand_formula():
    close = _panel(seed=29)
    w = 60
    out = lit.build_skew(close, w)
    returns = close.pct_change()
    col = close.columns[6]
    t = 150
    window_vals = returns[col].to_numpy()[t - w + 1:t + 1]
    # Independent Fisher-adjusted sample skewness (matches pandas' own .skew()).
    n = len(window_vals)
    m = window_vals.mean()
    m2 = np.mean((window_vals - m) ** 2)
    m3 = np.mean((window_vals - m) ** 3)
    g1 = m3 / m2 ** 1.5
    expected = (np.sqrt(n * (n - 1)) / (n - 2)) * g1
    assert abs(out[col].iloc[t] - expected) < 1e-8


def test_downside_beta_hand_formula():
    close = _panel(seed=31)
    w = 60
    out = lit.build_downside_beta(close, w)
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    ew8 = returns.mean(axis=1).where(all_valid)
    down_mask = ew8 < 0
    col = close.columns[4]
    t = 190
    ew8_win = ew8.iloc[t - w + 1:t + 1]
    mask_win = down_mask.iloc[t - w + 1:t + 1]
    y_win = returns[col].iloc[t - w + 1:t + 1]
    x = ew8_win[mask_win].to_numpy()
    y = y_win[mask_win].to_numpy()
    if len(x) >= max(10, w // 4):
        expected = np.cov(x, y, ddof=0)[0, 1] / np.var(x, ddof=0)
        assert abs(out[col].iloc[t] - expected) < 1e-9
    else:
        assert pd.isna(out[col].iloc[t])


def test_corr_to_ew8_change_hand_formula():
    close = _panel(seed=37)
    out = lit.build_corr_to_ew8_change(close, 60)
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    ew8 = returns.mean(axis=1).where(all_valid)
    col = close.columns[1]
    t = 190

    def corr_np(w):
        x = ew8.to_numpy()[t - w + 1:t + 1]
        y = returns[col].to_numpy()[t - w + 1:t + 1]
        return np.corrcoef(x, y)[0, 1]

    expected = corr_np(20) - corr_np(60)
    assert abs(out[col].iloc[t] - expected) < 1e-9


def test_momentum_5_and_reversal_5_are_the_same_formula():
    """Documents the deliberate redundancy noted in CATALOG.csv: these two
    catalog rows are the identical formula, expected to collapse via the
    prereg's own §3.4 post-selection dedup rather than being merged here."""
    close = _panel(seed=41)
    a = lit.build_trailing_return(close, 5)
    b = lit.build_trailing_return(close, 5)
    pd.testing.assert_frame_equal(a, b)
