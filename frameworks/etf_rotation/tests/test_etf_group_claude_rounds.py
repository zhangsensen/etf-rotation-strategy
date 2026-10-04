"""Synthetic-only tests for etf_group_claude_rounds.py (Batch A market
co-movement + Batch B long-horizon price structure + Batch C relative
market risk structure). Hand-calculated formulas, per-mechanism
window/direction validation, and leakage (prefix/perturbation) invariance.
"""
import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_group_claude_rounds import (
    _DEFINITIONS,
    build_atoms,
    leakage_checks,
)


def _panels(n=320, seed=3):
    """14 fixed names, long enough history for the window=250 candidates,
    with enough cross-sectional and time variation to avoid zero-variance
    rolling windows (which would make beta/corr legitimately NaN, not test
    the formula)."""
    idx = pd.bdate_range("2024-01-02", periods=n)
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=float)
    names = [f"m{i:02d}" for i in range(14)]
    market_wave = 0.0006 * np.sin(t / 11.0)
    returns = {}
    for i, name in enumerate(names):
        idio = rng.normal(0, 0.01, n)
        phase = 0.0004 * np.cos(t / (5.0 + i))
        returns[name] = market_wave + phase + idio
    returns_df = pd.DataFrame(returns, index=idx)
    close = 100.0 * (1.0 + returns_df).cumprod()
    open_scale = 1.0 + rng.normal(0, 0.001, (n, 14))
    open_ = close.shift(1).to_numpy()
    open_[0] = close.iloc[0].to_numpy()
    open_ = pd.DataFrame(open_, index=idx, columns=names) * open_scale
    span = 0.01 + 0.002 * (1.0 + np.sin(t[:, None] / 6.0))
    high = pd.DataFrame(
        np.maximum(open_.to_numpy(), close.to_numpy()) * (1.0 + span), index=idx, columns=names
    )
    low = pd.DataFrame(
        np.minimum(open_.to_numpy(), close.to_numpy()) * (1.0 - span), index=idx, columns=names
    )
    volume = pd.DataFrame(
        (1_000_000.0 + 200_000.0 * (1.0 + np.cos(t / 4.0)))[:, None] * np.ones((1, 14)),
        index=idx, columns=names,
    )
    amount = volume * close
    return {"open": open_, "high": high, "low": low, "close": close, "volume": volume, "amount": amount}


def _cfg(names):
    return {"mechanisms": {
        name: {"direction": _DEFINITIONS[name][0], "window": _DEFINITIONS[name][1]} for name in names
    }}


_ANCHOR_RENAME = {"m00": "518880.SH", "m01": "513100.SH", "m02": "513130.SH"}


def _panels_with_anchors(n=320, seed=3):
    """Same as _panels, but 3 of the 14 generic "m00".."m13" columns are
    relabeled to the real anchor tickers (gold/us_large_growth/
    hk_technology), which the anchor-correlation candidates hardcode by
    name and would otherwise KeyError against the generic fixture."""
    panels = _panels(n=n, seed=seed)
    return {key: df.rename(columns=_ANCHOR_RENAME) for key, df in panels.items()}


_BAR_TIMES = list(pd.date_range("09:35", "11:30", freq="5min").time) + list(
    pd.date_range("13:05", "15:00", freq="5min").time
)
assert len(_BAR_TIMES) == 48  # matches the real 5m data's session structure exactly


def _minute_panels(daily_index, seed=61, names=None):
    """Synthetic 5m OHLC panel matching the real data's 48-bar session
    structure (09:35-11:30, 13:05-15:00) for the same 14 names and
    trading days as a _panels() daily fixture. Pass `names` (e.g. a
    _panels_with_anchors() panel's own columns) to match a caller whose
    daily panel doesn't use the generic m00..m13 labels."""
    names = list(names) if names is not None else [f"m{i:02d}" for i in range(14)]
    minute_idx = pd.DatetimeIndex(
        [pd.Timestamp.combine(d.date(), bt) for d in daily_index for bt in _BAR_TIMES]
    )
    n5 = len(minute_idx)
    rng = np.random.default_rng(seed)
    market_wave = 0.0002 * np.sin(np.arange(n5) / 23.0)
    m_returns = pd.DataFrame(
        {name: market_wave + rng.normal(0, 0.003, n5) for name in names}, index=minute_idx
    )
    close = (1.0 + m_returns).cumprod() * 1.0
    open_ = close.shift(1).fillna(1.0)
    high = np.maximum(open_.to_numpy(), close.to_numpy()) * 1.001
    low = np.minimum(open_.to_numpy(), close.to_numpy()) * 0.999
    return {
        "close": close, "open": open_,
        "high": pd.DataFrame(high, index=minute_idx, columns=names),
        "low": pd.DataFrame(low, index=minute_idx, columns=names),
    }


from etf_strategy.core.etf_group_claude_rounds import _ECONOMIC_GROUPS  # noqa: E402

_REAL_TICKERS = [t for members in _ECONOMIC_GROUPS.values() for t in members]
assert len(_REAL_TICKERS) == 14
_REAL_TICKER_RENAME = {f"m{i:02d}": t for i, t in enumerate(_REAL_TICKERS)}


def _macro_panel(daily_index, seed=71):
    """Synthetic macro panel (5 variables, in _MACRO_COLUMNS order) for the
    round-11 macro-exposure candidates. Deliberately on its OWN native
    calendar (calendar-day frequency, including weekends the A-share
    trading calendar never has, and starting 10 days before daily_index)
    rather than daily_index itself, to exercise the real union+ffill+lag
    alignment path (not a fixture that trivially already matches the
    target calendar)."""
    from etf_strategy.core.etf_group_claude_rounds import _MACRO_COLUMNS
    start = daily_index.min() - pd.Timedelta(days=10)
    end = daily_index.max()
    native_idx = pd.date_range(start, end, freq="D")
    rng = np.random.default_rng(seed)
    n = len(native_idx)
    base = {
        "real_rate": 2.0, "nominal_rate": 4.0, "usdcnh": 7.0,
        "copper": 70000.0, "bond_future": 100.0,
    }
    data = {}
    for col in _MACRO_COLUMNS:
        steps = rng.normal(0, 0.05, n)
        data[col] = base[col] + np.cumsum(steps)
    return pd.DataFrame(data, index=native_idx)[list(_MACRO_COLUMNS)]


def _panels_with_real_tickers(n=320, seed=3):
    """Same as _panels, but all 14 generic columns are relabeled to the
    real ETF tickers, in the exact grouping _ECONOMIC_GROUPS defines.
    Needed by the Theme M dispersion-conditional candidates, which
    hardcode the 8-group membership by real ticker name."""
    panels = _panels(n=n, seed=seed)
    return {key: df.rename(columns=_REAL_TICKER_RENAME) for key, df in panels.items()}


ALL_NAMES = list(_DEFINITIONS)


def test_definitions_cover_exactly_batch_a_b_and_c():
    assert set(_DEFINITIONS) == {
        "beta_asymmetry", "corr_stability_20_60", "lead_to_market", "overnight_intraday_beta_gap",
        "momentum_120_skip5", "momentum_250_skip20", "vol_scaled_momentum", "tsmom_consistency",
        "vol_of_vol", "illiquidity_trend",
        "downside_correlation", "beta_variability", "market_tail_relative_return",
        "capture_asymmetry", "corr_level", "residual_vol_term_structure_20_60",
        "high_low_vol_beta_gap", "market_jump_response", "lag1_beta_to_market", "residual_skew_gap",
        "residual_market_vol_corr",
        "cokurtosis", "downside_coskewness", "avg_peer_residual_corr", "peer_corr_network_change",
        "peer_corr_dispersion",
        "amount_beta_to_market_amount", "volume_surge_relative_return", "amount_share_change",
        "overnight_momentum_relative_market", "overnight_intraday_sign_consistency_relative_market",
        "corr_dispersion_vs_anchors", "corr_level_to_nearest_anchor", "corr_nearest_anchor_change",
        "quantile_beta_gap", "tail_coexceedance_asymmetry",
        "intraday_realized_corr", "intraday_realized_beta", "minute_lead_lag_corr",
        "corwin_schultz_spread", "residual_kurtosis",
        "dispersion_conditional_relative_return", "dispersion_conditional_beta_gap",
        "residual_variance_ratio_1_5", "residual_sign_run", "residual_drawdown", "residual_tail_ratio",
        "roll_spread", "gap_fill_completion_relative_market",
        "post_market_tail_relative_return", "post_own_tail_relative_return", "beta_to_leader_group",
        "corr_horizon_ratio", "beta_horizon_ratio", "month_end_calendar_relative_return",
        "rank_persistence", "residual_semideviation_asymmetry", "weekday_relative_return_pattern",
        "post_market_tail_delayed_relative_return", "post_own_tail_delayed_relative_return",
        "post_dispersion_delayed_relative_return",
        "group_return_autocorrelation_relative", "group_momentum_rank_relative",
        "macro_expected_return_60_20", "real_rate_beta", "usd_beta", "commodity_beta", "macro_r2",
    }
    assert _DEFINITIONS["beta_asymmetry"] == (-1, 60)
    assert _DEFINITIONS["momentum_250_skip20"] == (1, 250)
    assert _DEFINITIONS["illiquidity_trend"] == (-1, 60)
    assert _DEFINITIONS["downside_correlation"] == (-1, 60)
    assert _DEFINITIONS["beta_variability"] == (-1, 60)
    assert _DEFINITIONS["market_tail_relative_return"] == (1, 60)
    assert _DEFINITIONS["capture_asymmetry"] == (1, 60)
    assert _DEFINITIONS["corr_level"] == (-1, 60)
    assert _DEFINITIONS["residual_vol_term_structure_20_60"] == (-1, 60)
    assert _DEFINITIONS["high_low_vol_beta_gap"] == (-1, 60)
    assert _DEFINITIONS["market_jump_response"] == (-1, 60)
    assert _DEFINITIONS["lag1_beta_to_market"] == (1, 60)
    assert _DEFINITIONS["residual_skew_gap"] == (1, 60)
    assert _DEFINITIONS["residual_market_vol_corr"] == (-1, 60)
    assert _DEFINITIONS["cokurtosis"] == (-1, 60)
    assert _DEFINITIONS["downside_coskewness"] == (-1, 60)
    assert _DEFINITIONS["avg_peer_residual_corr"] == (-1, 60)
    assert _DEFINITIONS["peer_corr_network_change"] == (-1, 60)
    assert _DEFINITIONS["peer_corr_dispersion"] == (-1, 60)
    assert _DEFINITIONS["amount_beta_to_market_amount"] == (-1, 60)
    assert _DEFINITIONS["volume_surge_relative_return"] == (1, 60)
    assert _DEFINITIONS["amount_share_change"] == (1, 60)
    assert _DEFINITIONS["overnight_momentum_relative_market"] == (1, 60)
    assert _DEFINITIONS["overnight_intraday_sign_consistency_relative_market"] == (1, 60)
    assert _DEFINITIONS["corr_dispersion_vs_anchors"] == (-1, 60)
    assert _DEFINITIONS["corr_level_to_nearest_anchor"] == (-1, 60)
    assert _DEFINITIONS["corr_nearest_anchor_change"] == (-1, 60)
    assert _DEFINITIONS["quantile_beta_gap"] == (-1, 60)
    assert _DEFINITIONS["tail_coexceedance_asymmetry"] == (1, 60)
    assert _DEFINITIONS["intraday_realized_corr"] == (-1, 20)
    assert _DEFINITIONS["intraday_realized_beta"] == (-1, 20)
    assert _DEFINITIONS["minute_lead_lag_corr"] == (1, 20)
    assert _DEFINITIONS["corwin_schultz_spread"] == (-1, 20)
    assert _DEFINITIONS["residual_kurtosis"] == (-1, 60)
    assert _DEFINITIONS["dispersion_conditional_relative_return"] == (1, 60)
    assert _DEFINITIONS["dispersion_conditional_beta_gap"] == (-1, 60)
    assert _DEFINITIONS["residual_variance_ratio_1_5"] == (1, 60)
    assert _DEFINITIONS["residual_sign_run"] == (1, 60)
    assert _DEFINITIONS["residual_drawdown"] == (-1, 60)
    assert _DEFINITIONS["residual_tail_ratio"] == (1, 60)
    assert _DEFINITIONS["roll_spread"] == (-1, 60)
    assert _DEFINITIONS["gap_fill_completion_relative_market"] == (-1, 60)
    assert _DEFINITIONS["post_market_tail_relative_return"] == (1, 60)
    assert _DEFINITIONS["post_own_tail_relative_return"] == (1, 60)
    assert _DEFINITIONS["beta_to_leader_group"] == (1, 20)
    assert _DEFINITIONS["corr_horizon_ratio"] == (-1, 60)
    assert _DEFINITIONS["beta_horizon_ratio"] == (1, 60)
    assert _DEFINITIONS["month_end_calendar_relative_return"] == (1, 120)
    assert _DEFINITIONS["rank_persistence"] == (1, 60)
    assert _DEFINITIONS["residual_semideviation_asymmetry"] == (1, 60)
    assert _DEFINITIONS["weekday_relative_return_pattern"] == (1, 60)
    assert _DEFINITIONS["post_market_tail_delayed_relative_return"] == (1, 60)
    assert _DEFINITIONS["post_own_tail_delayed_relative_return"] == (-1, 60)
    assert _DEFINITIONS["post_dispersion_delayed_relative_return"] == (-1, 60)
    assert _DEFINITIONS["group_return_autocorrelation_relative"] == (1, 60)
    assert _DEFINITIONS["group_momentum_rank_relative"] == (1, 60)
    assert _DEFINITIONS["macro_expected_return_60_20"] == (1, 60)
    assert _DEFINITIONS["real_rate_beta"] == (-1, 60)
    assert _DEFINITIONS["usd_beta"] == (-1, 60)
    assert _DEFINITIONS["commodity_beta"] == (1, 60)
    assert _DEFINITIONS["macro_r2"] == (-1, 60)


def test_rejects_unknown_mechanism():
    panels = _panels(n=60)
    cfg = {"mechanisms": {"not_a_real_mechanism": {"direction": 1, "window": 20}}}
    with pytest.raises(ValueError, match="unapproved"):
        build_atoms(panels, cfg)


def test_rejects_direction_or_window_mismatch():
    panels = _panels(n=60)
    cfg = {"mechanisms": {"beta_asymmetry": {"direction": 1, "window": 60}}}  # wrong direction
    with pytest.raises(ValueError, match="mismatch"):
        build_atoms(panels, cfg)
    cfg = {"mechanisms": {"beta_asymmetry": {"direction": -1, "window": 20}}}  # wrong window
    with pytest.raises(ValueError, match="mismatch"):
        build_atoms(panels, cfg)


def test_requires_fixed_14_name_pool():
    panels = _panels(n=60)
    panels = {k: v.iloc[:, :13] for k, v in panels.items()}
    cfg = _cfg(["momentum_120_skip5"])
    with pytest.raises(ValueError, match="14-name pool"):
        build_atoms(panels, cfg)


def test_illiquidity_trend_requires_amount_panel():
    panels = _panels(n=60)
    del panels["amount"]
    cfg = _cfg(["illiquidity_trend"])
    with pytest.raises(KeyError, match="amount"):
        build_atoms(panels, cfg)


def test_momentum_120_skip5_hand_formula():
    panels = _panels(n=200)
    cfg = _cfg(["momentum_120_skip5"])
    out = build_atoms(panels, cfg)["momentum_120_skip5_120"]
    close = panels["close"]
    expected = close.shift(5).div(close.shift(120)).sub(1.0)  # direction +1
    pd.testing.assert_frame_equal(out, expected)
    assert out.iloc[:120].isna().all().all()
    assert out.iloc[125:].notna().all().all()


def test_momentum_250_skip20_hand_formula():
    panels = _panels(n=320)
    cfg = _cfg(["momentum_250_skip20"])
    out = build_atoms(panels, cfg)["momentum_250_skip20_250"]
    close = panels["close"]
    expected = close.shift(20).div(close.shift(250)).sub(1.0)
    pd.testing.assert_frame_equal(out, expected)
    assert out.iloc[:250].isna().all().all()


def test_illiquidity_trend_hand_formula_and_direction():
    panels = _panels(n=150)
    cfg = _cfg(["illiquidity_trend"])
    out = build_atoms(panels, cfg)["illiquidity_trend_60"]
    close, amount = panels["close"], panels["amount"]
    returns = close.pct_change(fill_method=None)
    illiquidity = returns.abs().div(amount.where(amount > 0))
    amihud20 = illiquidity.rolling(20, min_periods=20).mean()
    amihud60 = illiquidity.rolling(60, min_periods=60).mean()
    expected = (amihud20.div(amihud60.where(amihud60 > 0)).sub(1.0)) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected)


def test_corr_stability_hand_formula():
    panels = _panels(n=150)
    cfg = _cfg(["corr_stability_20_60"])
    out = build_atoms(panels, cfg)["corr_stability_20_60_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)

    def rolling_corr(window):
        x_mean = market.rolling(window, min_periods=window).mean()
        y_mean = returns.rolling(window, min_periods=window).mean()
        cov = returns.mul(market, axis=0).rolling(window, min_periods=window).mean().sub(
            y_mean.mul(x_mean, axis=0)
        )
        x_var = market.pow(2).rolling(window, min_periods=window).mean() - x_mean.pow(2)
        y_var = returns.pow(2).rolling(window, min_periods=window).mean() - y_mean.pow(2)
        denom = y_var.where(y_var > 0).mul(x_var.where(x_var > 0), axis=0).pow(0.5)
        return cov.div(denom)

    expected = (rolling_corr(20) - rolling_corr(60)).abs() * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected)


def test_tsmom_consistency_hand_formula_on_constructed_blocks():
    # 20 flat lead-in days (so the first constructed block's own pct_change(20)
    # has a valid 20-days-ago reference), then six deterministic 20-day
    # blocks with a known positive-return count, so the block-fraction
    # formula can be checked exactly by hand.
    idx = pd.bdate_range("2024-01-02", periods=146)
    names = [f"m{i:02d}" for i in range(14)]
    block_signs = [1, 1, -1, 1, -1, 1]  # 4 of 6 blocks positive -> 4/6
    daily = np.concatenate(
        [np.zeros(20)] + [np.full(20, 0.001 * s) for s in block_signs] + [np.zeros(6)]
    )
    returns = pd.DataFrame(np.tile(daily[:, None], (1, 14)), index=idx, columns=names)
    close = 100.0 * (1.0 + returns).cumprod()
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.concat([open_, close]).groupby(level=0).max() * 1.001
    low = pd.concat([open_, close]).groupby(level=0).min() * 0.999
    volume = pd.DataFrame(1_000_000.0, index=idx, columns=names)
    panels = {"open": open_, "high": high, "low": low, "close": close, "volume": volume, "amount": volume * close}

    cfg = _cfg(["tsmom_consistency"])
    out = build_atoms(panels, cfg)["tsmom_consistency_120"]
    # The 120-row window ending at row 139 (0-indexed) spans exactly the 6
    # constructed 20-day blocks (rows 20:140), with the 20 lead-in days
    # supplying the first block's own 20-days-ago reference.
    assert out.iloc[139, 0] == pytest.approx(4 / 6)


def test_beta_asymmetry_uses_conditional_min_periods_not_full_window():
    # A pure alternating up/down market column-set: every rolling(60) window
    # has ~30 down days and ~30 up days, never 60 of either -- under a
    # strict min_periods=60 on the masked series this would be all-NaN.
    panels = _panels(n=200)
    cfg = _cfg(["beta_asymmetry"])
    out = build_atoms(panels, cfg)["beta_asymmetry_60"]
    assert out.iloc[100:].notna().any().any()


def test_lead_to_market_and_overnight_intraday_beta_gap_are_not_degenerate():
    panels = _panels(n=200)
    cfg = _cfg(["lead_to_market", "overnight_intraday_beta_gap"])
    out = build_atoms(panels, cfg)
    for name in ("lead_to_market_60", "overnight_intraday_beta_gap_60"):
        series = out[name]
        assert series.notna().any().any()
        assert series.abs().max().max() < 50  # sanity bound, not a tight hand-calc


# --- Batch C: relative market risk structure ----------------------------

def test_corr_level_hand_formula():
    panels = _panels(n=150)
    cfg = _cfg(["corr_level"])
    out = build_atoms(panels, cfg)["corr_level_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)

    x_mean = market.rolling(60, min_periods=60).mean()
    y_mean = returns.rolling(60, min_periods=60).mean()
    cov = returns.mul(market, axis=0).rolling(60, min_periods=60).mean().sub(y_mean.mul(x_mean, axis=0))
    x_var = market.pow(2).rolling(60, min_periods=60).mean() - x_mean.pow(2)
    y_var = returns.pow(2).rolling(60, min_periods=60).mean() - y_mean.pow(2)
    denom = y_var.where(y_var > 0).mul(x_var.where(x_var > 0), axis=0).pow(0.5)
    expected = cov.div(denom) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected)


def test_residual_vol_term_structure_hand_formula():
    panels = _panels(n=150)
    cfg = _cfg(["residual_vol_term_structure_20_60"])
    out = build_atoms(panels, cfg)["residual_vol_term_structure_20_60_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    residual = returns.sub(market, axis=0)
    short_vol = residual.rolling(20, min_periods=20).std()
    long_vol = residual.rolling(60, min_periods=60).std()
    expected = short_vol.div(long_vol.where(long_vol > 0)) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected)


def test_beta_variability_hand_formula():
    panels = _panels(n=150)
    cfg = _cfg(["beta_variability"])
    out = build_atoms(panels, cfg)["beta_variability_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    x_mean = market.rolling(20, min_periods=20).mean()
    y_mean = returns.rolling(20, min_periods=20).mean()
    cov = returns.mul(market, axis=0).rolling(20, min_periods=20).mean().sub(y_mean.mul(x_mean, axis=0))
    var = market.pow(2).rolling(20, min_periods=20).mean() - x_mean.pow(2)
    beta20 = cov.div(var.where(var > 0), axis=0)
    expected = beta20.rolling(60, min_periods=60).std() * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected)


def test_market_tail_relative_return_matches_direct_recomputation():
    # Independent second implementation of the same formula (built from the
    # module's own documented spec, not copy-pasted from the source), plus
    # a hand-checkable boundary: a member with zero excess return every day
    # must show a tail-conditional mean of exactly 0.
    panels = _panels(n=150, seed=5)
    cfg = _cfg(["market_tail_relative_return"])
    out = build_atoms(panels, cfg)["market_tail_relative_return_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    market_q20 = market.rolling(60, min_periods=60).quantile(0.20)
    tail_day = market.le(market_q20)
    relative_return = returns.sub(market, axis=0)
    count = tail_day.astype(float).rolling(60, min_periods=1).sum()
    tail_mask = np.broadcast_to(
        np.asarray(tail_day)[:, None], relative_return.shape
    )  # positional row broadcast, not label alignment
    total = relative_return.where(tail_mask).rolling(60, min_periods=1).sum()
    expected = total.div(count.where(count >= 3), axis=0) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected)

    # A member whose return always equals the (recomputed) market has zero
    # excess every day, tail or not; its tail-conditional mean must be
    # exactly 0 wherever it is defined. The market itself is the mean of
    # all 14 members including this one, so simply copying the OLD market
    # into m00 would not be self-consistent (m00 is 1/14 of the new
    # market). The fixed point is r_m00 = mean(other 13 members' returns):
    # new_market = (r_m00 + S) / 14 with S = sum(other 13) = r_m00 * 13
    # gives new_market = r_m00 exactly.
    other_returns = returns.drop(columns=["m00"])
    other_mean = other_returns.mean(axis=1)
    zero_excess = close.copy()
    zero_excess["m00"] = 100.0 * (1.0 + other_mean.fillna(0)).cumprod()
    out_zero = build_atoms({**panels, "close": zero_excess}, cfg)["market_tail_relative_return_60"]
    valid = out_zero["m00"].dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-9).all()


def test_downside_correlation_hand_formula():
    # Independent second implementation: rolling corr(market, member) using
    # only the rows where market < 0, matching _rolling_corr_scalar's
    # pairwise-deletion semantics (NaN on up-days drops that row from the
    # window's corr, it does not zero it).
    panels = _panels(n=200, seed=7)
    cfg = _cfg(["downside_correlation"])
    out = build_atoms(panels, cfg)["downside_correlation_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    down_mask = market.lt(0)
    market_down = market.where(down_mask)
    min_periods = max(10, 60 // 4)
    expected = {}
    for col in returns.columns:
        member_down = returns[col].where(down_mask)
        expected[col] = market_down.rolling(60, min_periods=min_periods).corr(member_down)
    expected_df = pd.DataFrame(expected, index=returns.index) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected_df, check_exact=False, rtol=1e-9, atol=1e-12)

    # Non-degenerate: with 200 rows of noisy synthetic data, most members
    # should have a defined value well before the end of the sample.
    assert out.notna().any(axis=1).sum() > 50


def test_capture_asymmetry_zero_for_market_tracking_member():
    # Boundary case reusing the same self-consistent fixed point as the
    # market_tail_relative_return zero-excess test: a member whose return
    # equals the (recomputed) market every day tracks up-days and
    # down-days identically, so up_capture == down_capture == 1 and
    # capture_asymmetry (their difference, direction +1) must be exactly 0
    # wherever both legs are defined.
    panels = _panels(n=200, seed=9)
    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    other_returns = returns.drop(columns=["m00"])
    other_mean = other_returns.mean(axis=1)
    tracking = close.copy()
    tracking["m00"] = 100.0 * (1.0 + other_mean.fillna(0)).cumprod()

    cfg = _cfg(["capture_asymmetry"])
    out = build_atoms({**panels, "close": tracking}, cfg)["capture_asymmetry_60"]
    valid = out["m00"].dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-9).all()


def test_lag1_beta_to_market_hand_formula():
    # Independent second implementation: dense rolling OLS beta of today's
    # member return on yesterday's market return, via pandas rolling
    # mean/cov/var built directly from the covariance identity (not calling
    # _rolling_beta from the source module).
    panels = _panels(n=200, seed=11)
    cfg = _cfg(["lag1_beta_to_market"])
    out = build_atoms(panels, cfg)["lag1_beta_to_market_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    market_lag = market.shift(1)
    x_mean = market_lag.rolling(60, min_periods=60).mean()
    y_mean = returns.rolling(60, min_periods=60).mean()
    cov = returns.mul(market_lag, axis=0).rolling(60, min_periods=60).mean().sub(
        y_mean.mul(x_mean, axis=0)
    )
    var = market_lag.pow(2).rolling(60, min_periods=60).mean() - x_mean.pow(2)
    expected = cov.div(var.where(var > 0), axis=0) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_high_low_vol_beta_gap_zero_for_market_tracking_member():
    # Boundary case, same self-consistent fixed point as the Batch C
    # zero-excess tests: a member whose return equals the (recomputed)
    # market every day has beta==1 to the market on ANY subset of days,
    # high-vol or low-vol alike, so the gap must be exactly 0 wherever both
    # legs are defined.
    panels = _panels(n=200, seed=13)
    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    other_returns = returns.drop(columns=["m00"])
    other_mean = other_returns.mean(axis=1)
    tracking = close.copy()
    tracking["m00"] = 100.0 * (1.0 + other_mean.fillna(0)).cumprod()

    cfg = _cfg(["high_low_vol_beta_gap"])
    out = build_atoms({**panels, "close": tracking}, cfg)["high_low_vol_beta_gap_60"]
    valid = out["m00"].dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-6).all()


def test_market_jump_response_zero_for_market_tracking_member():
    # Same fixed point: a member with zero idiosyncratic dispersion every
    # day (its return always equals the market) has |r_i - r_m| == 0 on
    # both jump and normal days, so the response (their difference) must
    # be exactly 0 wherever both legs are defined.
    panels = _panels(n=200, seed=15)
    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    other_returns = returns.drop(columns=["m00"])
    other_mean = other_returns.mean(axis=1)
    tracking = close.copy()
    tracking["m00"] = 100.0 * (1.0 + other_mean.fillna(0)).cumprod()

    cfg = _cfg(["market_jump_response"])
    out = build_atoms({**panels, "close": tracking}, cfg)["market_jump_response_60"]
    valid = out["m00"].dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-9).all()


def test_residual_skew_gap_hand_formula():
    # Independent second implementation: a plain per-window, per-column
    # Python loop computing pandas' own Series.skew() on the up-day-only
    # and down-day-only masked values, matching the source's conditional
    # min_periods floor. Slower than a vectorized recomputation but exact
    # and free of any of the source's own rolling/masking machinery, which
    # matters most for this candidate since it is the only one using
    # rolling().apply() with a hand-rolled validity check.
    panels = _panels(n=160, seed=17)
    cfg = _cfg(["residual_skew_gap"])
    out = build_atoms(panels, cfg)["residual_skew_gap_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    residual = returns.sub(market, axis=0)
    up_mask, down_mask = market.gt(0), market.lt(0)
    min_periods = max(10, 60 // 4)

    window = 60
    idx = residual.index
    expected = pd.DataFrame(index=idx, columns=residual.columns, dtype=float)
    # Only check a sparse sample of rows (every 7th, once past warmup) to
    # keep this independent Python-loop recomputation fast while still
    # covering early-, mid-, and late-window behavior.
    check_positions = range(window - 1, len(idx), 7)
    for col in residual.columns:
        for i in check_positions:
            lo = i - window + 1
            up_vals = residual[col].iloc[lo:i + 1][up_mask.iloc[lo:i + 1]].dropna()
            down_vals = residual[col].iloc[lo:i + 1][down_mask.iloc[lo:i + 1]].dropna()
            skew_up = up_vals.skew() if len(up_vals) >= min_periods else np.nan
            skew_down = down_vals.skew() if len(down_vals) >= min_periods else np.nan
            expected.iloc[i, expected.columns.get_loc(col)] = skew_up - skew_down

    for col in residual.columns:
        for i in check_positions:
            a, b = out[col].iloc[i], expected[col].iloc[i]
            if pd.isna(a) and pd.isna(b):
                continue
            assert abs(a - b) < 1e-9, f"{col} row {i}: got {a}, expected {b}"


def test_residual_market_vol_corr_hand_formula():
    # Independent second implementation: rolling corr(market_vol,
    # |r_i - r_m|) computed via the covariance identity directly (not
    # calling _rolling_corr_scalar from the source module).
    panels = _panels(n=200, seed=19)
    cfg = _cfg(["residual_market_vol_corr"])
    out = build_atoms(panels, cfg)["residual_market_vol_corr_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    idio_abs = returns.sub(market, axis=0).abs()
    market_vol = market.rolling(5, min_periods=5).std()

    x_mean = market_vol.rolling(60, min_periods=60).mean()
    y_mean = idio_abs.rolling(60, min_periods=60).mean()
    cov = idio_abs.mul(market_vol, axis=0).rolling(60, min_periods=60).mean().sub(
        y_mean.mul(x_mean, axis=0)
    )
    x_var = market_vol.pow(2).rolling(60, min_periods=60).mean() - x_mean.pow(2)
    y_var = idio_abs.pow(2).rolling(60, min_periods=60).mean() - y_mean.pow(2)
    denom = y_var.where(y_var > 0).mul(x_var.where(x_var > 0), axis=0).pow(0.5)
    expected = cov.div(denom) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_cokurtosis_hand_formula():
    # Independent second implementation: direct (non-raw-moment) definition
    # E[(x-mean(x))(y-mean(y))**3] / (std(x)*std(y)**3), computed with a
    # plain Python loop + numpy over a sparse sample of rows, bypassing the
    # source's raw-moment-expansion algebra entirely (that expansion was
    # separately verified against this same direct definition on synthetic
    # arrays before being written into the module, but this test re-checks
    # it against the actual built candidate output, not just the formula
    # in isolation).
    panels = _panels(n=160, seed=21)
    cfg = _cfg(["cokurtosis"])
    out = build_atoms(panels, cfg)["cokurtosis_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    window = 60
    idx = returns.index
    check_positions = range(window - 1, len(idx), 11)
    for col in returns.columns:
        for i in check_positions:
            lo = i - window + 1
            x = returns[col].iloc[lo:i + 1].to_numpy()
            y = market.iloc[lo:i + 1].to_numpy()
            if np.isnan(x).any() or np.isnan(y).any():
                continue
            ex, ey = x.mean(), y.mean()
            direct = np.mean((x - ex) * (y - ey) ** 3)
            std_x, std_y = x.std(), y.std()
            expected = -1 * direct / (std_x * std_y ** 3)  # direction -1
            got = out[col].iloc[i]
            assert abs(got - expected) < 1e-8, f"{col} row {i}: got {got}, expected {expected}"


def test_downside_coskewness_hand_formula():
    # Independent second implementation: direct definition of coskewness
    # restricted to the market's own down-day rows within the window,
    # bypassing the source's raw-moment-expansion algebra.
    panels = _panels(n=160, seed=23)
    cfg = _cfg(["downside_coskewness"])
    out = build_atoms(panels, cfg)["downside_coskewness_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    down_mask = market.lt(0)
    window = 60
    min_periods = max(10, window // 4)
    idx = returns.index
    check_positions = range(window - 1, len(idx), 11)
    for col in returns.columns:
        for i in check_positions:
            lo = i - window + 1
            sub_down = down_mask.iloc[lo:i + 1]
            x = returns[col].iloc[lo:i + 1][sub_down].dropna()
            y = market.iloc[lo:i + 1][sub_down].dropna()
            common = x.index.intersection(y.index)
            x, y = x.loc[common].to_numpy(), y.loc[common].to_numpy()
            got = out[col].iloc[i]
            if len(x) < min_periods:
                assert pd.isna(got), f"{col} row {i}: expected NaN (n={len(x)}<{min_periods})"
                continue
            ex, ey = x.mean(), y.mean()
            direct = np.mean((x - ex) * (y - ey) ** 2)
            var_x, var_y = x.var(), y.var()
            if var_x <= 0 or var_y <= 0:
                continue
            expected = -1 * direct / (np.sqrt(var_x) * var_y)  # direction -1
            assert abs(got - expected) < 1e-8, f"{col} row {i}: got {got}, expected {expected}"


def test_avg_peer_residual_corr_hand_formula_and_not_degenerate():
    # Regression guard for the bug caught while building this candidate:
    # a naive "correlate with the leave-one-out AVERAGE of the other 13
    # residuals" shortcut is exactly +/-1 always, because market is the
    # equal-weight mean of all 14 members INCLUDING the one being scored,
    # so the 14 residuals sum to exactly zero at every date and the
    # leave-one-out average is therefore an exact negative scalar multiple
    # of the member's own residual. This test both (a) asserts the output
    # is NOT pinned near +/-1 and (b) hand-checks one member at one row
    # against a direct numpy computation of the true mean of 13 separate
    # pairwise correlations.
    panels = _panels(n=160, seed=25)
    cfg = _cfg(["avg_peer_residual_corr"])
    out = build_atoms(panels, cfg)["avg_peer_residual_corr_60"]
    valid = out.stack().dropna()
    assert len(valid) > 100
    assert valid.abs().max() < 0.9, "looks degenerate (near +/-1) -- the leave-one-out-sum bug may be back"

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    residual = returns.sub(market, axis=0)
    window = 60
    row = len(residual.index) - 1  # last row, fully warmed up
    target = "m00"
    lo = row - window + 1
    own = residual[target].iloc[lo:row + 1]
    peer_corrs = []
    for col in residual.columns:
        if col == target:
            continue
        other = residual[col].iloc[lo:row + 1]
        peer_corrs.append(own.corr(other))
    expected = -1 * float(np.mean(peer_corrs))  # direction -1
    got = out[target].iloc[row]
    assert abs(got - expected) < 1e-8, f"got {got}, expected {expected}"


def test_peer_corr_network_change_equals_short_minus_long():
    # peer_corr_network_change is defined as the 20-day level minus the
    # 60-day level of the SAME underlying statistic; check that identity
    # holds against a direct recomputation of the level candidate at both
    # windows (not against the network_change build function's own
    # internals -- calling the level function twice independently here
    # rather than trusting its internal short/long wiring).
    panels = _panels(n=160, seed=27)
    # avg_peer_residual_corr's own window field isn't actually read by its
    # build function (only close is used; the 20/60 split is hard-coded
    # inside peer_corr_network_change), so build the two legs directly via
    # the module's internal function instead of through build_atoms/cfg.
    from etf_strategy.core.etf_group_claude_rounds import (
        _build_avg_peer_residual_corr, _build_peer_corr_network_change,
    )
    short = _build_avg_peer_residual_corr(panels["close"], 20)
    long = _build_avg_peer_residual_corr(panels["close"], 60)
    expected = (short - long) * -1  # direction -1
    cfg = _cfg(["peer_corr_network_change"])
    out = build_atoms(panels, cfg)["peer_corr_network_change_60"]
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_peer_corr_dispersion_hand_formula_and_not_degenerate():
    # Same regression guard style as avg_peer_residual_corr: not pinned at
    # a degenerate constant, plus a hand-check of one member at one row
    # against a direct numpy std of 13 separate pairwise correlations.
    panels = _panels(n=160, seed=29)
    cfg = _cfg(["peer_corr_dispersion"])
    out = build_atoms(panels, cfg)["peer_corr_dispersion_60"]
    valid = out.stack().dropna()
    assert len(valid) > 100
    # direction -1 is applied to the raw (always non-negative) std, so the
    # registered atom is always <= 0.
    assert valid.max() <= 0.0

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    residual = returns.sub(market, axis=0)
    window = 60
    row = len(residual.index) - 1
    target = "m00"
    lo = row - window + 1
    own = residual[target].iloc[lo:row + 1]
    peer_corrs = []
    for col in residual.columns:
        if col == target:
            continue
        other = residual[col].iloc[lo:row + 1]
        peer_corrs.append(own.corr(other))
    expected = -1 * float(np.std(peer_corrs, ddof=1))  # direction -1
    got = out[target].iloc[row]
    assert abs(got - expected) < 1e-8, f"got {got}, expected {expected}"


def test_amount_beta_to_market_amount_hand_formula():
    # Independent second implementation: dense rolling OLS beta of each
    # member's own amount pct-change on the fixed14 equal-weight mean of
    # all 14 members' amount pct-change, via the covariance identity
    # (not calling _rolling_beta from the source module).
    panels = _panels(n=200, seed=31)
    cfg = _cfg(["amount_beta_to_market_amount"])
    out = build_atoms(panels, cfg)["amount_beta_to_market_amount_60"]

    amount = panels["amount"]
    amount_change = amount.pct_change(fill_method=None)
    all_valid = amount_change.notna().all(axis=1)
    market_amount_change = amount_change.mean(axis=1).where(all_valid)
    x_mean = market_amount_change.rolling(60, min_periods=60).mean()
    y_mean = amount_change.rolling(60, min_periods=60).mean()
    cov = amount_change.mul(market_amount_change, axis=0).rolling(60, min_periods=60).mean().sub(
        y_mean.mul(x_mean, axis=0)
    )
    var = market_amount_change.pow(2).rolling(60, min_periods=60).mean() - x_mean.pow(2)
    expected = cov.div(var.where(var > 0), axis=0) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_volume_surge_relative_return_zero_for_market_tracking_member():
    # Same self-consistent fixed point as the earlier zero-excess tests: a
    # member whose return always equals the (recomputed) market has zero
    # excess return on EVERY day, own-volume-surge or not, so the
    # surge-vs-normal difference must be exactly 0 wherever both legs are
    # defined -- regardless of that member's own volume pattern, which is
    # untouched by this construction.
    panels = _panels(n=200, seed=33)
    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    other_returns = returns.drop(columns=["m00"])
    other_mean = other_returns.mean(axis=1)
    tracking = close.copy()
    tracking["m00"] = 100.0 * (1.0 + other_mean.fillna(0)).cumprod()

    cfg = _cfg(["volume_surge_relative_return"])
    out = build_atoms({**panels, "close": tracking}, cfg)["volume_surge_relative_return_60"]
    valid = out["m00"].dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-9).all()


def test_amount_share_change_hand_formula():
    # Independent second implementation: this member's share of the
    # cross-sectional total amount, short(20)-average minus long(60)-
    # average, computed directly rather than through the source's own
    # rolling calls.
    panels = _panels(n=160, seed=35)
    cfg = _cfg(["amount_share_change"])
    out = build_atoms(panels, cfg)["amount_share_change_60"]

    amount = panels["amount"]
    total = amount.sum(axis=1)
    share = amount.div(total.where(total > 0), axis=0)
    short = share.rolling(20, min_periods=20).mean()
    long = share.rolling(60, min_periods=60).mean()
    expected = (short - long) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)

    # Hand-checkable boundary: a member with a perfectly constant amount
    # share (e.g. always exactly 1/14 of total) has a flat share series,
    # so its short-average must equal its long-average exactly, and the
    # change must be exactly 0 wherever both legs are defined.
    flat_amount = amount.copy()
    for col in flat_amount.columns:
        flat_amount[col] = total / 14.0
    out_flat = build_atoms({**panels, "amount": flat_amount}, cfg)["amount_share_change_60"]
    valid = out_flat.stack().dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-9).all()


def test_overnight_momentum_relative_market_hand_formula():
    # Independent second implementation: overnight = open/prev_close - 1,
    # overnight_market = fixed14 all-complete equal-weight mean, rolling
    # mean of the difference over the window, computed directly rather
    # than via _market_return_from from the source module.
    panels = _panels(n=200, seed=37)
    cfg = _cfg(["overnight_momentum_relative_market"])
    out = build_atoms(panels, cfg)["overnight_momentum_relative_market_60"]

    open_, close = panels["open"], panels["close"]
    overnight = open_.div(close.shift(1)).sub(1.0)
    all_valid = overnight.notna().all(axis=1)
    overnight_market = overnight.mean(axis=1).where(all_valid)
    relative = overnight.sub(overnight_market, axis=0)
    expected = relative.rolling(60, min_periods=60).mean() * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_overnight_intraday_sign_consistency_hand_formula():
    # Independent second implementation: own sign-agreement rate minus
    # market's own sign-agreement rate, computed directly with numpy sign
    # comparisons rather than via the source's own masking pipeline.
    panels = _panels(n=200, seed=39)
    cfg = _cfg(["overnight_intraday_sign_consistency_relative_market"])
    out = build_atoms(panels, cfg)["overnight_intraday_sign_consistency_relative_market_60"]

    open_, close = panels["open"], panels["close"]
    overnight = open_.div(close.shift(1)).sub(1.0)
    intraday = close.div(open_).sub(1.0)
    all_valid_on = overnight.notna().all(axis=1)
    all_valid_in = intraday.notna().all(axis=1)
    overnight_market = overnight.mean(axis=1).where(all_valid_on)
    intraday_market = intraday.mean(axis=1).where(all_valid_in)

    own_valid = overnight.notna() & intraday.notna()
    own_agree = (np.sign(overnight) == np.sign(intraday)).astype(float).where(own_valid)
    own_rate = own_agree.rolling(60, min_periods=60).mean()

    market_valid = overnight_market.notna() & intraday_market.notna()
    market_agree = pd.Series(
        np.where(market_valid, (np.sign(overnight_market) == np.sign(intraday_market)).astype(float), np.nan),
        index=overnight_market.index,
    )
    market_rate = market_agree.rolling(60, min_periods=60).mean()

    expected = own_rate.sub(market_rate, axis=0) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_corr_dispersion_and_level_vs_anchors_hand_formula():
    # Independent second implementation: for each member, corr against
    # each of the 3 real anchor tickers computed directly with pandas'
    # own .rolling().corr() (not the source's _rolling_corr_scalar raw-
    # moment covariance/variance formula), then max-min (dispersion) and
    # max (level to nearest anchor) taken elementwise.
    panels = _panels_with_anchors(n=200, seed=41)
    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    residual = returns.sub(market, axis=0)

    anchors = ["518880.SH", "513100.SH", "513130.SH"]
    corrs = [residual.rolling(60, min_periods=60).corr(residual[a]) for a in anchors]
    corr_max = corrs[0].combine(corrs[1], np.maximum).combine(corrs[2], np.maximum)
    corr_min = corrs[0].combine(corrs[1], np.minimum).combine(corrs[2], np.minimum)

    cfg_disp = _cfg(["corr_dispersion_vs_anchors"])
    out_disp = build_atoms(panels, cfg_disp)["corr_dispersion_vs_anchors_60"]
    expected_disp = (corr_max - corr_min) * -1  # direction -1
    pd.testing.assert_frame_equal(out_disp, expected_disp, check_exact=False, rtol=1e-6, atol=1e-9)

    cfg_level = _cfg(["corr_level_to_nearest_anchor"])
    out_level = build_atoms(panels, cfg_level)["corr_level_to_nearest_anchor_60"]
    expected_level = corr_max * -1  # direction -1
    pd.testing.assert_frame_equal(out_level, expected_level, check_exact=False, rtol=1e-6, atol=1e-9)

    # Hand-checkable boundary: any anchor's own column must show corr==1
    # against itself in the max (its own row can never be excluded), so
    # its corr_level_to_nearest_anchor must be exactly -1 (direction -1
    # applied to a raw max of exactly 1) wherever defined.
    for a in anchors:
        valid = out_level[a].dropna()
        assert len(valid) > 0
        assert (valid == -1.0).all()


def test_corr_nearest_anchor_change_equals_short_minus_long():
    panels = _panels_with_anchors(n=200, seed=43)
    from etf_strategy.core.etf_group_claude_rounds import _build_corr_level_to_nearest_anchor
    short = _build_corr_level_to_nearest_anchor(panels["close"], 20)
    long = _build_corr_level_to_nearest_anchor(panels["close"], 60)
    expected = (short - long) * -1  # direction -1
    cfg = _cfg(["corr_nearest_anchor_change"])
    out = build_atoms(panels, cfg)["corr_nearest_anchor_change_60"]
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_anchor_candidates_reject_missing_anchor_ticker():
    # If the 14-name pool doesn't include the 3 real anchor tickers (e.g.
    # a caller passes the generic m00..m13 fixture), the anchor
    # candidates must fail loudly, not silently compute against the wrong
    # columns.
    panels = _panels(n=60)  # generic m00..m13 names, no real tickers
    cfg = _cfg(["corr_level_to_nearest_anchor"])
    with pytest.raises(KeyError, match="anchor tickers"):
        build_atoms(panels, cfg)


def test_quantile_beta_gap_hand_formula():
    # Independent second implementation: tercile thresholds and
    # conditional beta computed directly with pandas' own
    # rolling().quantile()/cov()/var() calls, not the source's
    # _rolling_beta raw-moment covariance/variance formula.
    panels = _panels(n=200, seed=45)
    cfg = _cfg(["quantile_beta_gap"])
    out = build_atoms(panels, cfg)["quantile_beta_gap_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    window = 60
    min_periods = 10
    q33 = market.rolling(window, min_periods=window).quantile(1.0 / 3.0)
    q67 = market.rolling(window, min_periods=window).quantile(2.0 / 3.0)
    valid = market.notna() & q33.notna() & q67.notna()
    top_mask = valid & market.ge(q67)
    bottom_mask = valid & market.le(q33)

    def conditional_beta(mask):
        x = market.where(mask)
        y = returns.where(mask, axis=0)
        x_mean = x.rolling(window, min_periods=min_periods).mean()
        y_mean = y.rolling(window, min_periods=min_periods).mean()
        cov = y.mul(x, axis=0).rolling(window, min_periods=min_periods).mean().sub(
            y_mean.mul(x_mean, axis=0)
        )
        var = x.pow(2).rolling(window, min_periods=min_periods).mean() - x_mean.pow(2)
        return cov.div(var.where(var > 0), axis=0)

    expected = (conditional_beta(top_mask) - conditional_beta(bottom_mask)) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-6, atol=1e-9)


def test_tail_coexceedance_asymmetry_hand_formula_and_boundary():
    # Independent second implementation via a direct per-day count over a
    # sparse sample of rows, plus a hand-checkable boundary: a member
    # whose return always equals the (recomputed) market co-exceeds with
    # the market's own tail 100% of the time on BOTH sides (whenever the
    # market is in its own tail, so is this member, trivially, since they
    # are the same series), so the asymmetry must be exactly 0 wherever
    # both legs are defined.
    panels = _panels(n=200, seed=47)
    cfg = _cfg(["tail_coexceedance_asymmetry"])
    out = build_atoms(panels, cfg)["tail_coexceedance_asymmetry_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    window, min_periods = 60, 3
    market_q80 = market.rolling(window, min_periods=window).quantile(0.80)
    market_q20 = market.rolling(window, min_periods=window).quantile(0.20)
    market_valid = market.notna() & market_q80.notna() & market_q20.notna()

    # Each day's tail membership uses THAT DAY's own trailing-window
    # quantile threshold (evolving/causal, same as market_tail_relative_
    # return's tail_day construction), not a single threshold frozen at
    # the window's last day retroactively applied to earlier days.
    market_up_day = market_valid & market.ge(market_q80)
    market_down_day = market_valid & market.le(market_q20)

    check_positions = range(window - 1, len(returns.index), 13)
    for col in ["m00", "m05"]:
        member_q80 = returns[col].rolling(window, min_periods=window).quantile(0.80)
        member_q20 = returns[col].rolling(window, min_periods=window).quantile(0.20)
        member_valid = returns[col].notna() & member_q80.notna() & member_q20.notna()
        member_up_day = member_valid & returns[col].ge(member_q80)
        member_down_day = member_valid & returns[col].le(member_q20)
        for i in check_positions:
            lo = i - window + 1
            mu = market_up_day.iloc[lo:i + 1]
            md = market_down_day.iloc[lo:i + 1]
            xu = member_up_day.iloc[lo:i + 1]
            xd = member_down_day.iloc[lo:i + 1]
            if mu.sum() < min_periods or md.sum() < min_periods:
                assert pd.isna(out[col].iloc[i])
                continue
            up = (xu & mu).sum() / mu.sum()
            down = (xd & md).sum() / md.sum()
            got = out[col].iloc[i]
            assert abs(got - (up - down)) < 1e-9, f"{col} row {i}: got {got}, expected {up - down}"

    other_returns = returns.drop(columns=["m00"])
    other_mean = other_returns.mean(axis=1)
    tracking = close.copy()
    tracking["m00"] = 100.0 * (1.0 + other_mean.fillna(0)).cumprod()
    out_tracking = build_atoms({**panels, "close": tracking}, cfg)["tail_coexceedance_asymmetry_60"]
    valid = out_tracking["m00"].dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-9).all()


def test_intraday_mechanisms_require_minute_panel():
    panels = _panels(n=40)  # no "minute" key
    cfg = _cfg(["intraday_realized_corr"])
    with pytest.raises(KeyError, match="minute panels"):
        build_atoms(panels, cfg)


def test_intraday_realized_corr_and_beta_hand_formula():
    from etf_strategy.core.etf_group_claude_rounds import _daily_intraday_pair_stats, _daily_market_5m

    panels = _panels(n=40, seed=63)
    minute = _minute_panels(panels["close"].index, seed=64)
    full_panels = {**panels, "minute": minute}

    returns_5m, market_5m = _daily_market_5m(minute["close"])
    daily_corr, daily_beta = _daily_intraday_pair_stats(market_5m, returns_5m)

    # Hand check one (day, member) cell: direct numpy corrcoef/cov from
    # that single day's raw 5m returns, bypassing the production per-day
    # loop entirely.
    day0 = daily_corr.index[5]
    col = "m03"
    day_returns = returns_5m.loc[returns_5m.index.normalize() == day0]
    x = market_5m.loc[day_returns.index].to_numpy()
    y = day_returns[col].to_numpy()
    valid = ~np.isnan(x) & ~np.isnan(y)
    xv, yv = x[valid], y[valid]
    expected_corr = np.corrcoef(xv, yv)[0, 1]
    expected_beta = np.cov(xv, yv, ddof=0)[0, 1] / np.var(xv)
    assert abs(daily_corr.loc[day0, col] - expected_corr) < 1e-9
    assert abs(daily_beta.loc[day0, col] - expected_beta) < 1e-9

    # And check the registered atom really is the 20-day rolling mean of
    # that same daily statistic, reindexed onto the full daily calendar,
    # with direction -1 applied.
    expected_corr_atom = daily_corr.reindex(panels["close"].index).rolling(20, min_periods=20).mean() * -1
    out_corr = build_atoms(full_panels, _cfg(["intraday_realized_corr"]))["intraday_realized_corr_20"]
    pd.testing.assert_frame_equal(out_corr, expected_corr_atom, check_exact=False, rtol=1e-9, atol=1e-12)

    expected_beta_atom = daily_beta.reindex(panels["close"].index).rolling(20, min_periods=20).mean() * -1
    out_beta = build_atoms(full_panels, _cfg(["intraday_realized_beta"]))["intraday_realized_beta_20"]
    pd.testing.assert_frame_equal(out_beta, expected_beta_atom, check_exact=False, rtol=1e-9, atol=1e-12)


def test_minute_lead_lag_corr_hand_formula_and_first_bar_boundary():
    from etf_strategy.core.etf_group_claude_rounds import _daily_intraday_pair_stats, _daily_market_5m

    panels = _panels(n=40, seed=65)
    minute = _minute_panels(panels["close"].index, seed=66)
    full_panels = {**panels, "minute": minute}

    returns_5m, market_5m = _daily_market_5m(minute["close"])
    day = returns_5m.index.normalize()
    lagged = returns_5m.groupby(day).shift(1)
    daily_corr, _daily_beta = _daily_intraday_pair_stats(market_5m, lagged)
    expected = daily_corr.reindex(panels["close"].index).rolling(20, min_periods=20).mean() * 1  # direction +1

    out = build_atoms(full_panels, _cfg(["minute_lead_lag_corr"]))["minute_lead_lag_corr_20"]
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)

    # Hand-checkable boundary: the very first 5m bar of every day has no
    # same-day predecessor, so its lagged return must be NaN for every
    # member on every day (never silently wrapping to the prior day's
    # last bar, and never silently treated as 0).
    first_bar_per_day = lagged.groupby(day).apply(lambda g: g.iloc[0])
    assert first_bar_per_day.isna().all().all()


def test_apply_513100_halt_mask_masks_only_the_flagged_window(tmp_path):
    from etf_strategy.core.etf_group_claude_rounds import apply_513100_halt_mask

    idx = pd.bdate_range("2024-01-02", periods=3)
    minute = _minute_panels(idx, seed=67)
    minute["close"]["513100.SH"] = minute["close"]["m00"]  # give it a real-ticker column to mask

    # Build a minimal synthetic 1m file for 513100.SH: zero volume for the
    # entire 09:31-10:30 window on idx[1] (a halt day), nonzero on the
    # other two days.
    halt_day, normal_days = idx[1], [idx[0], idx[2]]
    one_min_times = pd.date_range("09:31", "10:30", freq="1min").time
    rows = []
    for d in idx:
        volume = 0.0 if d == halt_day else 100.0
        for t in one_min_times:
            rows.append({"datetime": pd.Timestamp.combine(d.date(), t), "volume": volume})
    raw = pd.DataFrame(rows)
    minute_dir = tmp_path / "1m"
    minute_dir.mkdir()
    raw.to_parquet(minute_dir / "513100.SH.parquet")

    masked = apply_513100_halt_mask(minute, tmp_path)
    close = masked["close"]["513100.SH"]
    minute_of_day = close.index.hour * 60 + close.index.minute
    in_window = (minute_of_day >= 571) & (minute_of_day <= 630)
    on_halt_day = close.index.normalize() == halt_day

    assert close[in_window & on_halt_day].isna().all()
    assert close[~(in_window & on_halt_day)].notna().all()
    for d in normal_days:
        assert close[close.index.normalize() == d].notna().all()


def test_corwin_schultz_spread_hand_formula():
    # Independent second implementation of the Corwin-Schultz (2012)
    # estimator, written fresh from the paper's definition (not copied
    # from the source), plus a manual per-day spot check with plain
    # Python floats on one column to triple-verify the algebra.
    panels = _panels(n=100, seed=71)
    cfg = _cfg(["corwin_schultz_spread"])
    out = build_atoms(panels, cfg)["corwin_schultz_spread_20"]

    high, low = panels["high"], panels["low"]
    log_hl = np.log(high / low)
    beta = log_hl.pow(2) + log_hl.shift(1).pow(2)
    hi2 = np.maximum(high, high.shift(1))
    lo2 = np.minimum(low, low.shift(1))
    gamma = np.log(hi2 / lo2).pow(2)
    k = 3.0 - 2.0 * 2.0 ** 0.5
    alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    daily_spread = (2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))).clip(lower=0.0)
    expected = daily_spread.rolling(20, min_periods=20).mean() * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)

    # Manual plain-float spot check for one (day, column) cell, following
    # the paper's formula literally rather than any vectorized pandas
    # expression.
    col = "m04"
    i = 55
    h_t, l_t = float(high[col].iloc[i]), float(low[col].iloc[i])
    h_p, l_p = float(high[col].iloc[i - 1]), float(low[col].iloc[i - 1])
    import math
    beta_i = math.log(h_t / l_t) ** 2 + math.log(h_p / l_p) ** 2
    gamma_i = math.log(max(h_t, h_p) / min(l_t, l_p)) ** 2
    k_i = 3.0 - 2.0 * math.sqrt(2.0)
    alpha_i = (math.sqrt(2.0 * beta_i) - math.sqrt(beta_i)) / k_i - math.sqrt(gamma_i / k_i)
    s_i = max(0.0, 2.0 * (math.exp(alpha_i) - 1.0) / (1.0 + math.exp(alpha_i)))
    assert abs(daily_spread[col].iloc[i] - s_i) < 1e-9


def test_residual_kurtosis_hand_formula():
    # Independent second implementation via scipy's unbiased Fisher
    # kurtosis estimator (verified separately to match pandas' own
    # Series.kurt() exactly), applied to a sparse sample of rolling
    # windows computed manually, not through pandas' own .rolling().kurt().
    from scipy import stats

    panels = _panels(n=160, seed=73)
    cfg = _cfg(["residual_kurtosis"])
    out = build_atoms(panels, cfg)["residual_kurtosis_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    residual = returns.sub(market, axis=0)

    window = 60
    check_positions = range(window - 1, len(residual.index), 11)
    for col in ["m00", "m07"]:
        for i in check_positions:
            window_vals = residual[col].iloc[i - window + 1:i + 1].to_numpy()
            got = out[col].iloc[i]
            if np.isnan(window_vals).any():
                assert pd.isna(got), f"{col} row {i}: expected NaN (window has a gap)"
                continue
            expected = -1 * stats.kurtosis(window_vals, fisher=True, bias=False)  # direction -1
            assert abs(got - expected) < 1e-6, f"{col} row {i}: got {got}, expected {expected}"


def _independent_group_dispersion(returns):
    group_returns = {}
    for gid, members in _ECONOMIC_GROUPS.items():
        sub = returns[list(members)]
        all_present = sub.notna().all(axis=1)
        group_returns[gid] = sub.mean(axis=1).where(all_present)
    df = pd.DataFrame(group_returns)
    all_valid = df.notna().all(axis=1)
    return df.std(axis=1).where(all_valid)


def test_dispersion_conditional_relative_return_hand_formula():
    # Independent second implementation: group dispersion and the
    # conditional mean recomputed directly with pandas quantile/where
    # calls, not via the source's _rolling_conditional_mean helper.
    panels = _panels_with_real_tickers(n=200, seed=81)
    cfg = _cfg(["dispersion_conditional_relative_return"])
    out = build_atoms(panels, cfg)["dispersion_conditional_relative_return_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    dispersion = _independent_group_dispersion(returns)
    q67 = dispersion.rolling(60, min_periods=60).quantile(2.0 / 3.0)
    valid = dispersion.notna() & q67.notna()
    high_day = valid & dispersion.ge(q67)
    relative_return = returns.sub(market, axis=0)
    mask = np.broadcast_to(np.asarray(high_day)[:, None], relative_return.shape)
    count = high_day.astype(float).rolling(60, min_periods=1).sum()
    total = relative_return.where(mask).rolling(60, min_periods=1).sum()
    expected = total.div(count.where(count >= 8), axis=0) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_dispersion_conditional_beta_gap_hand_formula():
    panels = _panels_with_real_tickers(n=200, seed=83)
    cfg = _cfg(["dispersion_conditional_beta_gap"])
    out = build_atoms(panels, cfg)["dispersion_conditional_beta_gap_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    dispersion = _independent_group_dispersion(returns)
    window, min_periods = 60, 10
    q33 = dispersion.rolling(window, min_periods=window).quantile(1.0 / 3.0)
    q67 = dispersion.rolling(window, min_periods=window).quantile(2.0 / 3.0)
    valid = dispersion.notna() & q33.notna() & q67.notna()
    high_day = valid & dispersion.ge(q67)
    low_day = valid & dispersion.le(q33)

    def conditional_beta(mask):
        x = market.where(mask)
        y = returns.where(mask, axis=0)
        x_mean = x.rolling(window, min_periods=min_periods).mean()
        y_mean = y.rolling(window, min_periods=min_periods).mean()
        cov = y.mul(x, axis=0).rolling(window, min_periods=min_periods).mean().sub(
            y_mean.mul(x_mean, axis=0)
        )
        var = x.pow(2).rolling(window, min_periods=min_periods).mean() - x_mean.pow(2)
        return cov.div(var.where(var > 0), axis=0)

    expected = (conditional_beta(high_day) - conditional_beta(low_day)) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-6, atol=1e-9)


def test_residual_variance_ratio_1_5_hand_formula():
    panels = _panels(n=200, seed=85)
    cfg = _cfg(["residual_variance_ratio_1_5"])
    out = build_atoms(panels, cfg)["residual_variance_ratio_1_5_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    residual = returns.sub(market, axis=0)
    residual_5d = residual.rolling(5, min_periods=5).sum()
    var_5d = residual_5d.rolling(60, min_periods=60).var()
    var_1d = residual.rolling(60, min_periods=60).var()
    expected = var_5d.div(5.0 * var_1d.where(var_1d > 0)) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_residual_sign_run_hand_formula():
    # Independent second implementation: plain Python loop counting sign
    # flips over a sparse sample of (day, column) windows, not via
    # numpy vectorized rolling().apply().
    panels = _panels(n=160, seed=87)
    cfg = _cfg(["residual_sign_run"])
    out = build_atoms(panels, cfg)["residual_sign_run_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    residual = returns.sub(market, axis=0)

    window, min_periods = 60, 30
    check_positions = range(window - 1, len(residual.index), 13)
    for col in ["m00", "m09"]:
        for i in check_positions:
            window_vals = residual[col].iloc[i - window + 1:i + 1].dropna().tolist()
            got = out[col].iloc[i]
            if len(window_vals) < min_periods:
                assert pd.isna(got)
                continue
            signs = [1 if v > 0 else (-1 if v < 0 else 0) for v in window_vals]
            flips = sum(1 for a, b in zip(signs, signs[1:]) if a != b)
            expected = len(window_vals) / (flips + 1) * 1  # direction +1
            assert abs(got - expected) < 1e-9, f"{col} row {i}: got {got}, expected {expected}"


def test_residual_drawdown_hand_formula_and_zero_boundary():
    # Independent second implementation: plain Python loop computing the
    # windowed cumulative-path max drawdown, over a sparse sample.
    panels = _panels(n=160, seed=89)
    cfg = _cfg(["residual_drawdown"])
    out = build_atoms(panels, cfg)["residual_drawdown_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    residual = returns.sub(market, axis=0)

    window = 60
    check_positions = range(window - 1, len(residual.index), 13)
    for col in ["m02", "m11"]:
        for i in check_positions:
            window_vals = residual[col].iloc[i - window + 1:i + 1]
            got = out[col].iloc[i]
            if window_vals.isna().any():
                assert pd.isna(got)
                continue
            # No implicit leading-zero reference: the path starts exactly
            # at its first value (matching np.cumsum with no prepended
            # 0), so the very first day's drawdown-from-peak-so-far is
            # trivially 0 regardless of that value's own sign.
            cum = None
            peak = None
            max_dd = 0.0
            for v in window_vals:
                cum = v if cum is None else cum + v
                peak = cum if peak is None else max(peak, cum)
                max_dd = min(max_dd, cum - peak)
            expected = max_dd * -1  # direction -1
            assert abs(got - expected) < 1e-9, f"{col} row {i}: got {got}, expected {expected}"

    # A member with an entirely flat (zero) residual path has cum==0 and
    # peak==0 at every step, so its max drawdown must be exactly 0 (a
    # trivial but hand-checkable boundary).
    # m03's residual is ~0 only if its return equals the recomputed
    # market; reuse the established fixed-point trick (residual = r_i -
    # mean(all 14 incl. i), so r_i = mean(other 13) makes it exact).
    flat = close.copy()
    other_mean = returns.drop(columns=["m03"]).mean(axis=1)
    flat["m03"] = 100.0 * (1.0 + other_mean.fillna(0)).cumprod()
    out_flat = build_atoms({**panels, "close": flat}, cfg)["residual_drawdown_60"]
    valid = out_flat["m03"].dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-9).all()


def test_residual_tail_ratio_hand_formula():
    panels = _panels(n=200, seed=91)
    cfg = _cfg(["residual_tail_ratio"])
    out = build_atoms(panels, cfg)["residual_tail_ratio_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    residual = returns.sub(market, axis=0)
    window = 60
    sigma = residual.rolling(window, min_periods=window).std()
    valid = residual.notna() & sigma.notna() & sigma.gt(0)
    pos_day = (valid & residual.gt(2.0 * sigma)).astype(float)
    neg_day = (valid & residual.lt(-2.0 * sigma)).astype(float)
    pos_count = pos_day.rolling(window, min_periods=1).sum()
    neg_count = neg_day.rolling(window, min_periods=1).sum()
    expected = pos_count.div(neg_count.where(neg_count > 0)) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_roll_spread_hand_formula():
    # Independent second implementation via pandas' own rolling
    # mean/cov formula written fresh, not calling the source's helper
    # functions.
    panels = _panels(n=200, seed=93)
    cfg = _cfg(["roll_spread"])
    out = build_atoms(panels, cfg)["roll_spread_60"]

    close = panels["close"]
    dp = close.diff()
    dp_lag = dp.shift(1)
    mean_x = dp.rolling(60, min_periods=60).mean()
    mean_y = dp_lag.rolling(60, min_periods=60).mean()
    cov = dp.mul(dp_lag).rolling(60, min_periods=60).mean() - mean_x.mul(mean_y)
    expected = (2.0 * (-cov).clip(lower=0.0).pow(0.5)) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)

    # Hand-checkable boundary: a strictly monotonically-trending price
    # path (dP constant positive every day) has Cov(dP_t, dP_{t-1})==0
    # (no variance at all in dP), so the raw spread must be exactly 0
    # (not NaN, not negative) for that member wherever the window is full.
    trend = close.copy()
    trend["m00"] = 100.0 + 0.01 * np.arange(len(close.index))
    out_trend = build_atoms({**panels, "close": trend}, cfg)["roll_spread_60"]
    valid = out_trend["m00"].dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-9).all()


def test_gap_fill_completion_relative_market_hand_formula():
    panels = _panels(n=200, seed=95)
    cfg = _cfg(["gap_fill_completion_relative_market"])
    out = build_atoms(panels, cfg)["gap_fill_completion_relative_market_60"]

    open_, close = panels["open"], panels["close"]
    gap = open_.div(close.shift(1)).sub(1.0)
    body = close.div(open_).sub(1.0)
    gap_valid = gap.notna() & body.notna()
    filled = gap_valid & gap.ne(0) & (-np.sign(gap) * body).ge(gap.abs())
    own_rate = filled.astype(float).where(gap_valid).rolling(60, min_periods=60).mean()

    all_valid_gap = gap.notna().all(axis=1)
    market_gap = gap.mean(axis=1).where(all_valid_gap)
    all_valid_body = body.notna().all(axis=1)
    market_body = body.mean(axis=1).where(all_valid_body)
    market_valid = market_gap.notna() & market_body.notna()
    market_filled = market_valid & market_gap.ne(0) & (-np.sign(market_gap) * market_body).ge(market_gap.abs())
    market_rate = market_filled.astype(float).where(market_valid).rolling(60, min_periods=60).mean()

    expected = own_rate.sub(market_rate, axis=0) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_post_market_tail_relative_return_hand_formula():
    panels = _panels(n=200, seed=97)
    cfg = _cfg(["post_market_tail_relative_return"])
    out = build_atoms(panels, cfg)["post_market_tail_relative_return_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    abs_market = market.abs()
    q80 = abs_market.rolling(60, min_periods=60).quantile(0.80)
    market_valid = abs_market.notna() & q80.notna()
    tail_day = market_valid & abs_market.ge(q80)
    post_tail_day = tail_day.shift(1, fill_value=False)
    relative_return = returns.sub(market, axis=0)
    mask = np.broadcast_to(np.asarray(post_tail_day)[:, None], relative_return.shape)
    count = post_tail_day.astype(float).rolling(60, min_periods=1).sum()
    total = relative_return.where(mask).rolling(60, min_periods=1).sum()
    expected = total.div(count.where(count >= 3), axis=0) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)

    # Hand-checkable boundary: shifting the tail mask means day 0 can
    # never itself be a "post-tail" day (there is no day -1 to have been
    # a tail day), so the very first row must never count toward the
    # conditional mean -- confirmed implicitly by post_tail_day.iloc[0]
    # being False by construction (fill_value=False).
    assert not bool(post_tail_day.iloc[0].any())


def test_post_own_tail_relative_return_hand_formula():
    panels = _panels(n=200, seed=99)
    cfg = _cfg(["post_own_tail_relative_return"])
    out = build_atoms(panels, cfg)["post_own_tail_relative_return_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    residual = returns.sub(market, axis=0)
    abs_residual = residual.abs()
    q80 = abs_residual.rolling(60, min_periods=60).quantile(0.80)
    own_valid = abs_residual.notna() & q80.notna()
    own_tail_day = own_valid & abs_residual.ge(q80)
    post_own_tail_day = own_tail_day.shift(1, fill_value=False)
    count = post_own_tail_day.astype(float).rolling(60, min_periods=1).sum()
    total = residual.where(post_own_tail_day).rolling(60, min_periods=1).sum()
    expected = total.div(count.where(count >= 3)) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_post_market_tail_delayed_relative_return_hand_formula():
    # Independent second implementation of the round 9 days-t+2..t+5
    # delayed window, built with a plain OR of 4 explicit .shift() calls
    # rather than re-deriving the source's own delayed_window expression.
    panels = _panels(n=220, seed=131)
    cfg = _cfg(["post_market_tail_delayed_relative_return"])
    out = build_atoms(panels, cfg)["post_market_tail_delayed_relative_return_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    abs_market = market.abs()
    q80 = abs_market.rolling(60, min_periods=60).quantile(0.80)
    market_valid = abs_market.notna() & q80.notna()
    tail_day = market_valid & abs_market.ge(q80)
    delayed = pd.Series(False, index=close.index)
    for k in (2, 3, 4, 5):
        delayed = delayed | tail_day.shift(k, fill_value=False)
    relative_return = returns.sub(market, axis=0)
    mask = np.broadcast_to(np.asarray(delayed)[:, None], relative_return.shape)
    count = delayed.astype(float).rolling(60, min_periods=1).sum()
    total = relative_return.where(mask).rolling(60, min_periods=1).sum()
    expected = total.div(count.where(count >= 3), axis=0) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)

    # Boundary: days 0-1 can never be "delayed post-tail" (shift(2..5) all
    # need at least 2 prior rows), so neither can ever count.
    assert not bool(delayed.iloc[0]) and not bool(delayed.iloc[1])


def test_post_own_tail_delayed_relative_return_hand_formula():
    panels = _panels(n=220, seed=133)
    cfg = _cfg(["post_own_tail_delayed_relative_return"])
    out = build_atoms(panels, cfg)["post_own_tail_delayed_relative_return_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    residual = returns.sub(market, axis=0)
    abs_residual = residual.abs()
    q80 = abs_residual.rolling(60, min_periods=60).quantile(0.80)
    own_valid = abs_residual.notna() & q80.notna()
    own_tail_day = own_valid & abs_residual.ge(q80)
    delayed = own_tail_day.shift(2, fill_value=False)
    for k in (3, 4, 5):
        delayed = delayed | own_tail_day.shift(k, fill_value=False)
    count = delayed.astype(float).rolling(60, min_periods=1).sum()
    total = residual.where(delayed).rolling(60, min_periods=1).sum()
    expected = total.div(count.where(count >= 3)) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_post_dispersion_delayed_relative_return_hand_formula():
    panels = _panels_with_real_tickers(n=220, seed=137)
    cfg = _cfg(["post_dispersion_delayed_relative_return"])
    out = build_atoms(panels, cfg)["post_dispersion_delayed_relative_return_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    dispersion = _independent_group_dispersion(returns)
    q80 = dispersion.rolling(60, min_periods=60).quantile(0.80)
    valid = dispersion.notna() & q80.notna()
    high_disp_day = valid & dispersion.ge(q80)
    delayed = pd.Series(False, index=close.index)
    for k in (2, 3, 4, 5):
        delayed = delayed | high_disp_day.shift(k, fill_value=False)
    relative_return = returns.sub(market, axis=0)
    mask = np.broadcast_to(np.asarray(delayed)[:, None], relative_return.shape)
    count = delayed.astype(float).rolling(60, min_periods=1).sum()
    total = relative_return.where(mask).rolling(60, min_periods=1).sum()
    expected = total.div(count.where(count >= 3), axis=0) * -1  # direction -1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_group_return_autocorrelation_relative_hand_formula():
    # Independent second implementation: recompute the 8 group returns
    # directly from _ECONOMIC_GROUPS (not via the source's _group_returns_
    # df helper), then a plain numpy lag-1 correlation per group per day
    # over a small dense sample, cross-checked against pandas' own
    # .rolling().corr(shift(1)) result used by the production code.
    panels = _panels_with_real_tickers(n=160, seed=141)
    cfg = _cfg(["group_return_autocorrelation_relative"])
    out = build_atoms(panels, cfg)["group_return_autocorrelation_relative_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    group_returns = {}
    for gid, members in _ECONOMIC_GROUPS.items():
        sub = returns[list(members)]
        all_present = sub.notna().all(axis=1)
        group_returns[gid] = sub.mean(axis=1).where(all_present)
    group_returns_df = pd.DataFrame(group_returns)
    lag1 = group_returns_df.rolling(60, min_periods=60).corr(group_returns_df.shift(1))
    member_to_group = {m: gid for gid, members in _ECONOMIC_GROUPS.items() for m in members}
    expected = pd.DataFrame(
        {m: lag1[gid] for m, gid in member_to_group.items()}
    )[close.columns] * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)

    # Hand spot-check at one date/member using plain numpy corrcoef on the
    # single-member hk_technology group (513130.SH) -- for a single-member
    # group this must equal that member's own raw-return lag-1
    # autocorrelation (the degeneracy this candidate's docstring discloses).
    t = 140
    window = group_returns_df["hk_technology"].iloc[t - 59:t + 1].to_numpy()
    window_lag = group_returns_df["hk_technology"].shift(1).iloc[t - 59:t + 1].to_numpy()
    valid = ~(np.isnan(window) | np.isnan(window_lag))
    expected_corr = np.corrcoef(window[valid], window_lag[valid])[0, 1]
    assert abs(out["513130.SH"].iloc[t] - expected_corr) < 1e-9
    own_return = returns["513130.SH"]
    own_lag1_autocorr = own_return.rolling(60, min_periods=60).corr(own_return.shift(1))
    assert abs(out["513130.SH"].iloc[t] - own_lag1_autocorr.iloc[t]) < 1e-9


def test_group_momentum_rank_relative_hand_formula():
    panels = _panels_with_real_tickers(n=160, seed=143)
    cfg = _cfg(["group_momentum_rank_relative"])
    out = build_atoms(panels, cfg)["group_momentum_rank_relative_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    group_returns = {}
    for gid, members in _ECONOMIC_GROUPS.items():
        sub = returns[list(members)]
        all_present = sub.notna().all(axis=1)
        group_returns[gid] = sub.mean(axis=1).where(all_present)
    group_returns_df = pd.DataFrame(group_returns)
    momentum = group_returns_df.rolling(60, min_periods=60).mean()
    rank = momentum.rank(axis=1)
    member_to_group = {m: gid for gid, members in _ECONOMIC_GROUPS.items() for m in members}
    expected = pd.DataFrame(
        {m: rank[gid] for m, gid in member_to_group.items()}
    )[close.columns] * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)

    # Rank must always be in [1, 8] (8 economic groups) on any day all 8
    # groups are valid, and every member of the SAME group must carry the
    # identical rank that day (cn_technology_manufacturing has 6 members).
    valid_rows = momentum.notna().all(axis=1)
    cn_members = list(_ECONOMIC_GROUPS["cn_technology_manufacturing"])
    same_group_rank = out.loc[valid_rows, cn_members]
    assert (same_group_rank.nunique(axis=1) == 1).all()
    assert out.loc[valid_rows].min().min() >= 1 and out.loc[valid_rows].max().max() <= 8


def _independent_macro_changes(macro_native, calendar):
    """Independent second implementation of _macro_daily_changes's
    alignment+lag+diff logic, using pd.merge_asof (backward, same-day-
    inclusive) instead of the source's own reindex+ffill path for STAGE 1
    (as-of-that-A-share-date visibility). Stage 2 (the extra one-A-share-
    session lag for foreign columns) is then applied as an EXPLICIT
    .shift(1) on the resulting A-share-indexed series, matching the
    source's actual two-stage semantics exactly: the lag is one A-share
    SESSION on the already-aligned series, not "native date strictly
    before the A-share calendar date" collapsed into a single query --
    those two are NOT equivalent when the native calendar has entries on
    non-A-share days (e.g. USDCNH trades weekends): a Saturday print only
    becomes visible once Monday's row has ALREADY reindexed/ffilled it in
    stage 1, and then only takes effect from the row AFTER Monday (stage
    2's shift), not from Monday itself -- confirmed by first getting this
    wrong (collapsing to a single strict-inequality merge_asof) and this
    test failing against the real implementation before being corrected
    to the two-stage form actually used in production."""
    from etf_strategy.core.etf_group_claude_rounds import _MACRO_COLUMNS, _MACRO_FOREIGN_COLUMNS
    cal_df = pd.DataFrame({"cal_date": calendar}).sort_values("cal_date")
    aligned = {}
    for col in _MACRO_COLUMNS:
        s = macro_native[col].dropna().sort_index()
        src = pd.DataFrame({"native_date": s.index, "value": s.to_numpy()}).sort_values("native_date")
        merged = pd.merge_asof(
            cal_df, src, left_on="cal_date", right_on="native_date",
            direction="backward", allow_exact_matches=True,
        )
        stage1 = pd.Series(merged["value"].to_numpy(), index=calendar)
        aligned[col] = stage1.shift(1) if col in _MACRO_FOREIGN_COLUMNS else stage1
    aligned_df = pd.DataFrame(aligned)[list(_MACRO_COLUMNS)]
    changes = pd.DataFrame(index=calendar)
    for col in _MACRO_COLUMNS:
        if col in ("real_rate", "nominal_rate"):
            changes[col] = aligned_df[col].diff()
        else:
            changes[col] = aligned_df[col].pct_change()
    return changes


def test_macro_changes_alignment_independent_merge_asof():
    from etf_strategy.core.etf_group_claude_rounds import _macro_daily_changes
    panels = _panels(n=200, seed=151)
    macro_native = _macro_panel(panels["close"].index, seed=153)
    got = _macro_daily_changes(macro_native, panels["close"].index)
    expected = _independent_macro_changes(macro_native, panels["close"].index)
    pd.testing.assert_frame_equal(got, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_real_rate_usd_commodity_beta_hand_formula():
    panels = _panels(n=200, seed=155)
    macro_native = _macro_panel(panels["close"].index, seed=157)
    panels_with_macro = {**panels, "macro": macro_native}
    cfg = _cfg(["real_rate_beta", "usd_beta", "commodity_beta"])
    out = build_atoms(panels_with_macro, cfg)

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    changes = _independent_macro_changes(macro_native, close.index)
    window = 60
    for cand, col, direction in (
        ("real_rate_beta_60", "real_rate", -1),
        ("usd_beta_60", "usdcnh", -1),
        ("commodity_beta_60", "copper", 1),
    ):
        x = changes[col]
        x_mean = x.rolling(window, min_periods=window).mean()
        y_mean = returns.rolling(window, min_periods=window).mean()
        cov = returns.mul(x, axis=0).rolling(window, min_periods=window).mean().sub(
            y_mean.mul(x_mean, axis=0)
        )
        var = x.pow(2).rolling(window, min_periods=window).mean() - x_mean.pow(2)
        expected = cov.div(var.where(var > 0), axis=0) * direction
        pd.testing.assert_frame_equal(out[cand], expected, check_exact=False, rtol=1e-8, atol=1e-11)


def test_macro_r2_and_macro_expected_return_hand_formula():
    # Spot-checked at a sparse sample of (day, member) cells via an
    # explicit independent numpy lstsq -- not the source's own
    # _rolling_multi_ols helper -- matching the campaign's established
    # "independent second implementation" convention for regression-based
    # candidates (e.g. test_beta_to_leader_group_hand_formula).
    panels = _panels(n=200, seed=159)
    macro_native = _macro_panel(panels["close"].index, seed=161)
    panels_with_macro = {**panels, "macro": macro_native}
    cfg = _cfg(["macro_r2", "macro_expected_return_60_20"])
    out = build_atoms(panels_with_macro, cfg)

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    changes = _independent_macro_changes(macro_native, close.index)
    from etf_strategy.core.etf_group_claude_rounds import _MACRO_COLUMNS
    x_all = changes[list(_MACRO_COLUMNS)].to_numpy()
    window = 60
    for t in (199, 150, 100):
        start = t - window + 1
        xw = x_all[start:t + 1]
        if np.isnan(xw).any():
            continue
        xc = xw - xw.mean(axis=0, keepdims=True)
        cum20 = changes[list(_MACRO_COLUMNS)].iloc[t - 19:t + 1].sum()
        for member in list(close.columns)[:4]:
            yw = returns[member].to_numpy()[start:t + 1]
            if np.isnan(yw).any():
                continue
            yc = yw - yw.mean()
            sst = float(np.sum(yc ** 2))
            if sst <= 0:
                continue
            beta, *_ = np.linalg.lstsq(xc, yc, rcond=None)
            fitted = xc @ beta
            ssr = float(np.sum((yc - fitted) ** 2))
            r2 = 1.0 - ssr / sst
            got_r2 = out["macro_r2_60"][member].iloc[t]
            assert abs(got_r2 - (r2 * -1)) < 1e-8, f"r2 mismatch at t={t} member={member}"

            expected_score = float(np.dot(beta, cum20.to_numpy())) * 1  # direction +1
            got_score = out["macro_expected_return_60_20_60"][member].iloc[t]
            assert abs(got_score - expected_score) < 1e-8, f"expected_return mismatch at t={t} member={member}"


def test_macro_foreign_next_day_domestic_same_day_lag_boundary():
    # The core business rule under test (master, 2026-09-24): a foreign
    # print (USDCNH here) dated calendar-day t must NOT be visible in any
    # atom's value on the A-share trading date that IS calendar-day t
    # itself, only from the next A-share trading date onward. A domestic
    # print (copper) dated t IS visible the same A-share date.
    idx = pd.bdate_range("2024-03-04", periods=5)  # Mon..Fri, one clean week
    step_date = idx[2]  # Wednesday
    native_idx = pd.date_range(idx[0] - pd.Timedelta(days=3), idx[-1], freq="D")
    from etf_strategy.core.etf_group_claude_rounds import _macro_daily_changes, _MACRO_COLUMNS
    data = {col: 1.0 for col in _MACRO_COLUMNS}
    macro = pd.DataFrame([data] * len(native_idx), index=native_idx)
    # A clean step: usdcnh (foreign) and copper (domestic) both jump by
    # +1.0 starting exactly on step_date (Wednesday), flat before and after.
    macro.loc[macro.index < step_date, "usdcnh"] = 7.0
    macro.loc[macro.index >= step_date, "usdcnh"] = 8.0
    macro.loc[macro.index < step_date, "copper"] = 70000.0
    macro.loc[macro.index >= step_date, "copper"] = 71000.0

    changes = _macro_daily_changes(macro, idx)
    # Wednesday itself: domestic (copper) already reflects the step (its
    # own pct_change vs Tuesday is large and positive); foreign (usdcnh)
    # does NOT yet reflect it (still flat vs Tuesday, since Wednesday's
    # own print isn't usable until Thursday).
    assert changes["copper"].loc[step_date] > 0.01
    assert abs(changes["usdcnh"].loc[step_date]) < 1e-9
    # Thursday: foreign NOW reflects the step (comparing Thursday's
    # lagged-usable value, which is Wednesday's print, against
    # Wednesday's lagged-usable value, which is Tuesday's print).
    thursday = idx[3]
    assert changes["usdcnh"].loc[thursday] > 0.01
    # Friday: no further step, foreign change back to ~0 (both days now
    # see the same, already-lagged Wednesday print).
    friday = idx[4]
    assert abs(changes["usdcnh"].loc[friday]) < 1e-9


def test_beta_to_leader_group_hand_formula():
    # Independent second implementation, spot-checked at a sparse sample
    # of (day, member) cells: recompute the 8 group returns, that day's
    # leader/second group (with the "own group can't lead itself"
    # substitution), and a plain numpy regression of the member's return
    # against the SELECTED group's own returns over the same 20-day
    # window -- not via the source's precompute-all-8-then-select
    # approach, a genuinely different computation path to the same
    # number.
    panels = _panels_with_real_tickers(n=160, seed=105)
    cfg = _cfg(["beta_to_leader_group"])
    out = build_atoms(panels, cfg)["beta_to_leader_group_20"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    group_ret = {}
    for gid, members in _ECONOMIC_GROUPS.items():
        sub = returns[list(members)]
        all_present = sub.notna().all(axis=1)
        group_ret[gid] = sub.mean(axis=1).where(all_present)
    group_ret_df = pd.DataFrame(group_ret)
    perf = group_ret_df.rolling(20, min_periods=20).mean()

    member_to_group = {m: gid for gid, members in _ECONOMIC_GROUPS.items() for m in members}
    window = 20
    check_positions = range(window - 1, len(returns.index), 13)
    for member in ["159995.SZ", "518880.SH", "512890.SH"]:
        own_group = member_to_group[member]
        for i in check_positions:
            perf_row = perf.iloc[i]
            got = out[member].iloc[i]
            if perf_row.isna().any():
                assert pd.isna(got)
                continue
            leader = perf_row.idxmax()
            if leader == own_group:
                remaining = perf_row.drop(index=leader)
                leader = remaining.idxmax()
            x = group_ret_df[leader].iloc[i - window + 1:i + 1].to_numpy()
            y = returns[member].iloc[i - window + 1:i + 1].to_numpy()
            valid = ~np.isnan(x) & ~np.isnan(y)
            if valid.sum() < 15:
                assert pd.isna(got)
                continue
            xv, yv = x[valid], y[valid]
            xc, yc = xv - xv.mean(), yv - yv.mean()
            var_x = np.mean(xc * xc)
            if var_x <= 0:
                assert pd.isna(got)
                continue
            expected = np.mean(xc * yc) / var_x * 1  # direction +1
            assert abs(got - expected) < 1e-9, f"{member} row {i}: got {got}, expected {expected}"


def test_corr_and_beta_horizon_ratio_hand_formula():
    # Independent second implementation: 1-day and 5-day market/member
    # legs and their rolling corr/beta recomputed directly with pandas'
    # own built-in rolling().corr()/cov()/var(), not the source's own
    # helper functions.
    panels = _panels(n=200, seed=109)
    close = panels["close"]
    returns_1d = close.pct_change(fill_method=None)
    all_valid_1d = returns_1d.notna().all(axis=1)
    market_1d = returns_1d.mean(axis=1).where(all_valid_1d)
    returns_5d = close.pct_change(5, fill_method=None)
    all_valid_5d = returns_5d.notna().all(axis=1)
    market_5d = returns_5d.mean(axis=1).where(all_valid_5d)

    corr_1d = returns_1d.rolling(60, min_periods=60).corr(market_1d)
    corr_5d = returns_5d.rolling(60, min_periods=60).corr(market_5d)
    expected_corr_ratio = corr_5d.div(corr_1d.where(corr_1d.abs() > 0)) * -1  # direction -1
    out_corr = build_atoms(panels, _cfg(["corr_horizon_ratio"]))["corr_horizon_ratio_60"]
    pd.testing.assert_frame_equal(out_corr, expected_corr_ratio, check_exact=False, rtol=1e-6, atol=1e-9)

    def rolling_beta_builtin(x, y, window):
        cov = y.rolling(window, min_periods=window).cov(x)
        var = x.rolling(window, min_periods=window).var()
        return cov.div(var, axis=0)

    beta_1d = rolling_beta_builtin(market_1d, returns_1d, 60)
    beta_5d = rolling_beta_builtin(market_5d, returns_5d, 60)
    expected_beta_ratio = beta_5d.div(beta_1d.where(beta_1d.abs() > 0)) * 1  # direction +1
    out_beta = build_atoms(panels, _cfg(["beta_horizon_ratio"]))["beta_horizon_ratio_60"]
    pd.testing.assert_frame_equal(out_beta, expected_beta_ratio, check_exact=False, rtol=1e-4, atol=1e-7)


def test_month_end_calendar_relative_return_hand_formula_and_boundary():
    # Independent second implementation of the month-end mask via a plain
    # per-date Python check (day-of-month vs that month's actual day
    # count, not the source's index.day/index.days_in_month vectorized
    # form), plus a hand-checkable boundary.
    panels = _panels(n=260, seed=111)
    cfg = _cfg(["month_end_calendar_relative_return"])
    out = build_atoms(panels, cfg)["month_end_calendar_relative_return_120"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    relative_return = returns.sub(market, axis=0)

    import calendar as calendar_module

    idx = close.index
    month_end_mask = pd.Series(
        [d.day >= calendar_module.monthrange(d.year, d.month)[1] - 4 for d in idx], index=idx
    )

    window, min_periods = 120, 8
    check_positions = range(window - 1, len(idx), 17)
    for col in ["m01", "m10"]:
        for i in check_positions:
            lo = i - window + 1
            window_mask = month_end_mask.iloc[lo:i + 1]
            vals = relative_return[col].iloc[lo:i + 1][window_mask].dropna()
            got = out[col].iloc[i]
            if len(vals) < min_periods:
                assert pd.isna(got), f"{col} row {i}: expected NaN (n={len(vals)}<{min_periods})"
                continue
            expected = vals.mean() * 1  # direction +1
            assert abs(got - expected) < 1e-9, f"{col} row {i}: got {got}, expected {expected}"

    # Hand-checkable boundary: a member whose return always equals the
    # (recomputed) market has zero excess return on every day, month-end
    # or not, so the feature must be exactly 0 wherever defined.
    other_mean = returns.drop(columns=["m00"]).mean(axis=1)
    tracking = close.copy()
    tracking["m00"] = 100.0 * (1.0 + other_mean.fillna(0)).cumprod()
    out_tracking = build_atoms({**panels, "close": tracking}, cfg)["month_end_calendar_relative_return_120"]
    valid = out_tracking["m00"].dropna()
    assert len(valid) > 0
    assert (valid.abs() < 1e-9).all()


def test_rank_persistence_hand_formula():
    panels = _panels(n=200, seed=117)
    cfg = _cfg(["rank_persistence"])
    out = build_atoms(panels, cfg)["rank_persistence_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    daily_rank = returns.rank(axis=1)
    expected = daily_rank.rolling(60, min_periods=60).mean() * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)

    # Hand-checkable boundary: cross-sectional rank among 14 members is
    # always a permutation of 1..14, so its window-average must always
    # lie strictly within [1, 14] wherever defined.
    valid = out.stack().dropna()
    assert len(valid) > 0
    assert valid.between(1.0, 14.0).all()


def test_residual_semideviation_asymmetry_hand_formula():
    panels = _panels(n=200, seed=119)
    cfg = _cfg(["residual_semideviation_asymmetry"])
    out = build_atoms(panels, cfg)["residual_semideviation_asymmetry_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    residual = returns.sub(market, axis=0)
    min_periods = max(10, 60 // 4)
    up_vol = residual.where(residual.gt(0)).rolling(60, min_periods=min_periods).std()
    down_vol = residual.where(residual.lt(0)).rolling(60, min_periods=min_periods).std()
    expected = up_vol.sub(down_vol) * 1  # direction +1
    pd.testing.assert_frame_equal(out, expected, check_exact=False, rtol=1e-9, atol=1e-12)


def test_weekday_relative_return_pattern_hand_formula():
    panels = _panels(n=200, seed=121)
    cfg = _cfg(["weekday_relative_return_pattern"])
    out = build_atoms(panels, cfg)["weekday_relative_return_pattern_60"]

    close = panels["close"]
    returns = close.pct_change(fill_method=None)
    all_valid = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_valid)
    relative_return = returns.sub(market, axis=0)
    window, min_periods = 60, 3
    is_friday = close.index.dayofweek == 4
    is_monday = close.index.dayofweek == 0

    check_positions = range(window - 1, len(close.index), 13)
    for col in ["m03", "m12"]:
        for i in check_positions:
            lo = i - window + 1
            fri_vals = relative_return[col].iloc[lo:i + 1][is_friday[lo:i + 1]].dropna()
            mon_vals = relative_return[col].iloc[lo:i + 1][is_monday[lo:i + 1]].dropna()
            got = out[col].iloc[i]
            fri_ok = len(fri_vals) >= min_periods
            mon_ok = len(mon_vals) >= min_periods
            if not (fri_ok and mon_ok):
                assert pd.isna(got)
                continue
            expected = (fri_vals.mean() - mon_vals.mean()) * 1  # direction +1
            assert abs(got - expected) < 1e-9, f"{col} row {i}: got {got}, expected {expected}"


def test_leakage_checks_pass_for_every_mechanism():
    panels = _panels_with_real_tickers(n=320)
    panels = {**panels, "minute": _minute_panels(panels["close"].index, names=panels["close"].columns)}
    panels = {**panels, "macro": _macro_panel(panels["close"].index)}
    cfg = _cfg(ALL_NAMES)
    cut = panels["close"].index[220]
    assert all(leakage_checks(panels, cfg, cut).values())


def test_month_end_calendar_relative_return_is_leak_free_at_arbitrary_cuts():
    # Regression guard against ever reintroducing the original trading-
    # day-count-based definition's leak (see the module docstring above
    # _month_end_calendar_day_mask): unlike "last 3 TRADING days of the
    # month" (forward-dependent -- you cannot know a month has only 3
    # trading days left until it has actually ended), the calendar-day
    # proxy depends only on each date's own intrinsic day-of-month/days-
    # in-month, so it must stay truncation-invariant at ANY cut,
    # including cuts that fall mid-month (the exact scenario that broke
    # the original definition). Checked at two different, deliberately
    # non-month-aligned cuts.
    panels = _panels(n=320)
    cfg = _cfg(["month_end_calendar_relative_return"])
    for cut in (panels["close"].index[150], panels["close"].index[220]):
        assert leakage_checks(panels, cfg, cut)["month_end_calendar_relative_return_120"]
