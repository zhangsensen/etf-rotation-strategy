"""Claude-authored fixed-window daily OHLCV atoms (Batch A: market
co-movement structure; Batch B: long-horizon price structure [closed
2026-09-23, no further variants]; Batch C onward: relative market risk
structure, mined round-by-round under the USER 2026-09-23 50-round
sub-agent mining campaign -- round 1 = Batch C, round 2 continues the same
theme with high_low_vol_beta_gap/market_jump_response/lag1_beta_to_market/
residual_skew_gap plus one Theme-B (higher-order co-movement) family,
residual_market_vol_corr, added to round 2 after market_jump_response was
dropped on the no-label dedup precheck (round rule: minimum 4 survivors
per round from round 2 onward, filled with a new family, never a variant)),
rounds registered incrementally 2026-09-23 onward.

Unlike etf_group_daily_rounds.py, this module has no single global WINDOW
constant: each mechanism's rolling window is a frozen, per-mechanism part of
its own definition (declared in ``_DEFINITIONS`` and echoed by the config),
because Batch A needs window 60 and Batch B needs 20/60/120/250. Frozen
economic direction, close(D)-causal only, no future leakage.

"Market" matches etf_group_daily_rounds._market_residuals exactly: the
equal-weight mean of all 14 candidates' close-to-close returns on dates
where every one of the 14 has a valid return (never a partial-membership
average).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# name -> (direction, window). Both are part of the frozen definition; a
# config whose direction or window disagrees with this table is rejected.
_DEFINITIONS = {
    # Batch A: market co-movement structure, window 60 (corr_stability also
    # reads a 20-day leg internally, but its own registered window is 60,
    # matching |corr20 - corr60| being one candidate at one w=60 cadence).
    "beta_asymmetry": (-1, 60),
    "corr_stability_20_60": (-1, 60),
    "lead_to_market": (1, 60),
    "overnight_intraday_beta_gap": (1, 60),
    # Batch B: long-horizon price structure.
    "momentum_120_skip5": (1, 120),
    "momentum_250_skip20": (1, 250),
    "vol_scaled_momentum": (1, 60),
    "tsmom_consistency": (1, 120),
    "vol_of_vol": (-1, 60),
    "illiquidity_trend": (-1, 60),
    # Batch C: relative market risk structure, window 60.
    "downside_correlation": (-1, 60),
    "beta_variability": (-1, 60),
    "market_tail_relative_return": (1, 60),
    "capture_asymmetry": (1, 60),
    "corr_level": (-1, 60),
    "residual_vol_term_structure_20_60": (-1, 60),
    # Round 2 (Theme A continuation: relative market risk structure), window 60.
    "high_low_vol_beta_gap": (-1, 60),
    "market_jump_response": (-1, 60),
    "lag1_beta_to_market": (1, 60),
    "residual_skew_gap": (1, 60),
    # Round 2 (Theme B: higher-order co-movement), window 60.
    "residual_market_vol_corr": (-1, 60),
    # Round 3 (Theme B: higher-order co-movement continued), window 60.
    "cokurtosis": (-1, 60),
    "downside_coskewness": (-1, 60),
    # Round 3 (Theme C: cross-group correlation network), window 60.
    "avg_peer_residual_corr": (-1, 60),
    "peer_corr_network_change": (-1, 60),
    "peer_corr_dispersion": (-1, 60),
    # Round 4 (Theme E: trading-activity relative to market), window 60.
    "amount_beta_to_market_amount": (-1, 60),
    "volume_surge_relative_return": (1, 60),
    "amount_share_change": (1, 60),
    # Round 4 (Theme F: overnight information), window 60.
    "overnight_momentum_relative_market": (1, 60),
    "overnight_intraday_sign_consistency_relative_market": (1, 60),
    # Round 5 (Theme C, remaining item: correlation to 3 fixed macro anchors), window 60.
    "corr_dispersion_vs_anchors": (-1, 60),
    "corr_level_to_nearest_anchor": (-1, 60),
    "corr_nearest_anchor_change": (-1, 60),
    # Round 5 (Theme G: cross-group conditional dependence), window 60.
    "quantile_beta_gap": (-1, 60),
    "tail_coexceedance_asymmetry": (1, 60),
    # Round 5 (Theme D: minute-level co-movement, 5m bars), window 20.
    "intraday_realized_corr": (-1, 20),
    "intraday_realized_beta": (-1, 20),
    "minute_lead_lag_corr": (1, 20),
    # Round 5 (Theme H: relative liquidity structure / Theme I: residual
    # distribution shape), window 20/60, master's 2026-09-23 own-formula spec.
    "corwin_schultz_spread": (-1, 20),
    "residual_kurtosis": (-1, 60),
    # Round 6 (Theme M: dispersion-conditional / R: residual time-series
    # structure / U: residual path / I: residual distribution shape).
    "dispersion_conditional_relative_return": (1, 60),
    "dispersion_conditional_beta_gap": (-1, 60),
    "residual_variance_ratio_1_5": (1, 60),
    "residual_sign_run": (1, 60),
    "residual_drawdown": (-1, 60),
    "residual_tail_ratio": (1, 60),
    # Round 7 (Theme H: Roll 1984 spread estimator, master's own formula).
    "roll_spread": (-1, 60),
    # Round 7 (self-devised, MY_ASSUMPTION, mechanism written before
    # definition; each is flagged distinctly in its own docstring below).
    "gap_fill_completion_relative_market": (-1, 60),
    "post_market_tail_relative_return": (1, 60),
    "post_own_tail_relative_return": (1, 60),
    # Round 7, 3rd candidate (master's own formula, not counted against the
    # MY_ASSUMPTION quota; roll_spread was closed after failing structural
    # diagnostics -- see notes on _build_roll_spread).
    "beta_to_leader_group": (1, 20),
    # Round 8 (master's own formulas: return-horizon ratios + calendar
    # seasonality).
    "corr_horizon_ratio": (-1, 60),
    "beta_horizon_ratio": (1, 60),
    "month_end_calendar_relative_return": (1, 120),
    # Round 8, self-devised (MY_ASSUMPTION, mechanism written before
    # definition; master's cap: <=3 per round).
    "rank_persistence": (1, 60),
    "residual_semideviation_asymmetry": (1, 60),
    "weekday_relative_return_pattern": (1, 60),
    # Round 9 (self-devised, MY_ASSUMPTION, mechanism written before
    # definition; master gave only the angle -- "post-event time structure
    # of relative returns, days t+2..t+5, distinct from round 7's next-day-
    # only test" -- no formulas; master's cap: <=3 per round).
    "post_market_tail_delayed_relative_return": (1, 60),
    "post_own_tail_delayed_relative_return": (-1, 60),
    "post_dispersion_delayed_relative_return": (-1, 60),
    # Round 10 (self-devised, MY_ASSUMPTION, mechanism written before
    # definition; master gave no formula/angle for round 10, only that
    # rounds 9/10 are both self-devised; master's cap: <=3 per round.
    # Only 2 registered this round -- see notes on _build_group_return_
    # autocorrelation_relative for why a well-differentiated 3rd was not
    # found without either colliding with an already-tested cross-engine
    # family or a degenerate single-member-group construction).
    "group_return_autocorrelation_relative": (1, 60),
    "group_momentum_rank_relative": (1, 60),
    # Round 11 (master's own formulas: macro exposure family, new data
    # source this campaign's IC framework has never used -- see
    # _MACRO_MECHANISMS/load_macro_panel notes).
    "macro_expected_return_60_20": (1, 60),
    "real_rate_beta": (-1, 60),
    "usd_beta": (-1, 60),
    "commodity_beta": (1, 60),
    "macro_r2": (-1, 60),
}

# The 8 economic groups over the fixed 14-name pool (master's own
# taxonomy, frameworks/etf_rotation/configs/etf_candidate14_economic_
# group_v1.yaml, frozen 2026-09-22). Hardcoded here only for the Theme M
# dispersion-conditional candidates, which need the cross-sectional GROUP
# structure itself (not just the 14 raw members) to build their regime
# label; every other candidate in this module stays generic over the
# 14-name pool with no group knowledge.
_ECONOMIC_GROUPS = {
    "cn_technology_manufacturing": (
        "159995.SZ", "159516.SZ", "515880.SH", "159852.SZ", "562500.SH", "159732.SZ",
    ),
    "hk_technology": ("513130.SH",),
    "us_large_growth": ("513100.SH",),
    "innovative_pharma": ("159992.SZ", "513120.SH"),
    "gold": ("518880.SH",),
    "metals_equity": ("512400.SH",),
    "dividend_low_vol": ("512890.SH",),
    "electric_power": ("159611.SZ",),
}

# Gold / US large-growth / HK-technology, the three ETFs master specified as
# fixed macro anchors for Theme C's "correlation gap vs anchors" family.
# First (and, per current plan, only) hardcoded tickers in this module;
# every other candidate treats the 14-name pool generically via
# panels/close.columns. Confirmed against
# frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml's
# single-member groups (gold, us_large_growth, hk_technology).
_ANCHOR_TICKERS = ("518880.SH", "513100.SH", "513130.SH")

# Minimum non-null observations required inside a conditional (masked)
# rolling window, e.g. beta_asymmetry's down-day-only or up-day-only legs.
# A `window`-row span holds roughly half that many down (or up) days; using
# `window` (a Batch A/B window of 60) as min_periods on an already-masked
# series is unsatisfiable (it would require every row in the span to belong
# to the conditional subset), so a fixed, pre-registered fraction is used
# instead: max(10, window // 4).
def _conditional_min_periods(window: int) -> int:
    return max(10, window // 4)


def _validate_config(cfg: dict) -> None:
    mechanisms = cfg.get("mechanisms", {})
    # Upper bound is a sanity cap on a single config's mechanism count, not
    # the campaign budget (that is enforced separately by discover_etf_
    # groups.py's budget_cap ledger check). Raised from the original 16
    # (Batch A+B+C's total) to accommodate the 50-round mining campaign
    # (USER 2026-09-23), each round registering its own new mechanisms into
    # this same table.
    if not 1 <= len(mechanisms) <= 400:
        raise ValueError("claude_rounds requires 1..400 mechanisms")
    unknown = set(mechanisms) - set(_DEFINITIONS)
    if unknown:
        raise ValueError(f"unapproved claude_rounds mechanisms: {sorted(unknown)}")
    bad = []
    for name, definition in mechanisms.items():
        direction, window = _DEFINITIONS[name]
        if definition.get("direction") != direction or definition.get("window") != window:
            bad.append(name)
    if bad:
        raise ValueError(f"claude_rounds direction/window mismatch: {bad}")


_MINUTE_MECHANISMS = {
    "intraday_realized_corr", "intraday_realized_beta", "minute_lead_lag_corr",
}

# Round 11 (master's own formulas: macro exposure family, new data source --
# US 10y real/nominal yield, USDCNH, copper and 10y bond futures -- this
# campaign's IC framework has never used before).
_MACRO_MECHANISMS = {
    "macro_expected_return_60_20", "real_rate_beta", "usd_beta",
    "commodity_beta", "macro_r2",
}
# Foreign-market variables (US Treasury yields, USDCNH) can only be used
# starting the A-share trading date whose own calendar date is at least
# one day after the foreign print's own date (master, 2026-09-24: "外国数据
# 日期t只能在A股t+1起使用") -- an extra one-A-share-session .shift(1) is
# applied to these after forward-filling onto the A-share calendar.
# Domestic futures (CU/T) settle same-day and need no extra shift (master:
# "国内期货当日收盘可用"). Column order here IS the regressor order for
# macro_expected_return_60_20/macro_r2's multivariate regression.
_MACRO_FOREIGN_COLUMNS = ("real_rate", "nominal_rate", "usdcnh")
_MACRO_DOMESTIC_COLUMNS = ("copper", "bond_future")
_MACRO_COLUMNS = _MACRO_FOREIGN_COLUMNS + _MACRO_DOMESTIC_COLUMNS


def _panels(panels: dict[str, pd.DataFrame], names: tuple[str, ...]) -> dict[str, pd.DataFrame]:
    required = {"open", "high", "low", "close"}
    if set(names) & {
        "illiquidity_trend", "amount_beta_to_market_amount",
        "volume_surge_relative_return", "amount_share_change",
    }:
        required.add("amount")
    needs_minute = bool(set(names) & _MINUTE_MECHANISMS)
    needs_macro = bool(set(names) & _MACRO_MECHANISMS)
    missing = required - set(panels)
    if missing:
        raise KeyError(f"missing daily panels: {sorted(missing)}")
    if needs_minute and "minute" not in panels:
        raise KeyError("missing minute panels: ['minute']")
    if needs_macro and "macro" not in panels:
        raise KeyError("missing macro panel: ['macro']")
    out = {key: panels[key].astype(float) for key in required}
    first = out["close"]
    if any(not first.index.equals(value.index) or not first.columns.equals(value.columns)
           for value in out.values()):
        raise ValueError("daily panels must have identical member-date axes")
    if first.shape[1] != 14:
        raise ValueError("market co-movement/long-horizon atoms require the fixed 14-name pool")
    if needs_minute:
        minute = panels["minute"]
        minute_close = minute["close"]
        if minute_close.shape[1] != 14 or set(minute_close.columns) != set(first.columns):
            raise ValueError("minute panels require the same fixed 14-name pool as the daily panels")
        out["minute"] = {key: minute[key].astype(float) for key in ("close",)}
    if needs_macro:
        macro = panels["macro"].astype(float)
        if set(macro.columns) != set(_MACRO_COLUMNS):
            raise ValueError(f"macro panel must have exactly columns {_MACRO_COLUMNS}")
        out["macro"] = macro
    return out


def _market_return(close: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Matches etf_group_daily_rounds._market_residuals's market leg exactly:
    equal-weight mean of all 14 returns, only on dates where all 14 are
    valid (never a partial-membership average)."""
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    return returns, market


def _rolling_beta(x: pd.Series, y: pd.DataFrame, window: int, min_periods: int) -> pd.DataFrame:
    x_mean = x.rolling(window, min_periods=min_periods).mean()
    y_mean = y.rolling(window, min_periods=min_periods).mean()
    covariance = y.mul(x, axis=0).rolling(window, min_periods=min_periods).mean().sub(
        y_mean.mul(x_mean, axis=0)
    )
    variance = x.pow(2).rolling(window, min_periods=min_periods).mean() - x_mean.pow(2)
    return covariance.div(variance.where(variance > 0), axis=0)


def _rolling_corr_scalar(
    x: pd.Series, y: pd.DataFrame, window: int, min_periods: int | None = None
) -> pd.DataFrame:
    mp = window if min_periods is None else min_periods
    x_mean = x.rolling(window, min_periods=mp).mean()
    y_mean = y.rolling(window, min_periods=mp).mean()
    covariance = y.mul(x, axis=0).rolling(window, min_periods=mp).mean().sub(
        y_mean.mul(x_mean, axis=0)
    )
    x_var = x.pow(2).rolling(window, min_periods=mp).mean() - x_mean.pow(2)
    y_var = y.pow(2).rolling(window, min_periods=mp).mean() - y_mean.pow(2)
    denominator = y_var.where(y_var > 0).mul(x_var.where(x_var > 0), axis=0).pow(0.5)
    return covariance.div(denominator)


def _rolling_conditional_mean(
    value: pd.DataFrame, mask: pd.DataFrame, window: int, min_periods: int
) -> pd.DataFrame:
    """Mean of value over the trailing window, counting only rows where mask
    is True (mask may be a DataFrame or a market-wide Series broadcast)."""
    masked = value.where(mask, axis=0) if isinstance(mask, pd.Series) else value.where(mask)
    count = (mask if isinstance(mask, pd.DataFrame) else pd.DataFrame(
        {c: mask for c in value.columns}, index=value.index
    )).astype(float).rolling(window, min_periods=1).sum()
    total = masked.rolling(window, min_periods=1).sum()
    return total.div(count.where(count >= min_periods))


def _rolling_conditional_mean_series(
    value: pd.Series, mask: pd.Series, window: int, min_periods: int
) -> pd.Series:
    """Series-only counterpart of _rolling_conditional_mean, for a
    market-level (not per-member) conditional moment such as E[r_m|mask]
    or E[r_m**2|mask]."""
    masked = value.where(mask)
    count = mask.astype(float).rolling(window, min_periods=1).sum()
    total = masked.rolling(window, min_periods=1).sum()
    return total.div(count.where(count >= min_periods))


def _build_beta_asymmetry(close: pd.DataFrame, window: int) -> pd.DataFrame:
    returns, market = _market_return(close)
    min_periods = _conditional_min_periods(window)
    down_mask, up_mask = market.lt(0), market.gt(0)
    beta_down = _rolling_beta(
        market.where(down_mask), returns.where(down_mask, axis=0), window, min_periods
    )
    beta_up = _rolling_beta(
        market.where(up_mask), returns.where(up_mask, axis=0), window, min_periods
    )
    return beta_down - beta_up


def _build_corr_stability_20_60(close: pd.DataFrame, window: int) -> pd.DataFrame:
    del window  # this candidate's own two legs are fixed at 20 and 60
    _returns, market = _market_return(close)
    returns = close.pct_change(fill_method=None)
    corr20 = _rolling_corr_scalar(market, returns, 20)
    corr60 = _rolling_corr_scalar(market, returns, 60)
    return (corr20 - corr60).abs()


def _build_lead_to_market(close: pd.DataFrame, window: int) -> pd.DataFrame:
    returns, market = _market_return(close)
    return (
        _rolling_corr_scalar(market, returns.shift(1), window)
        - _rolling_corr_scalar(market.shift(1), returns, window)
    )


def _build_overnight_intraday_beta_gap(
    open_: pd.DataFrame, close: pd.DataFrame, window: int
) -> pd.DataFrame:
    overnight = open_.div(close.shift(1)).sub(1.0)
    intraday = close.div(open_).sub(1.0)
    _overnight_returns, overnight_market = _market_return_from(overnight)
    _intraday_returns, intraday_market = _market_return_from(intraday)
    beta_overnight = _rolling_beta(overnight_market, overnight, window, window)
    beta_intraday = _rolling_beta(intraday_market, intraday, window, window)
    return beta_overnight - beta_intraday


def _market_return_from(returns: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    return returns, market


def _build_momentum_skip(close: pd.DataFrame, lookback: int, skip: int) -> pd.DataFrame:
    return close.shift(skip).div(close.shift(lookback)).sub(1.0)


def _build_vol_scaled_momentum(close: pd.DataFrame, window: int) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    ret_over_window = close.pct_change(window, fill_method=None)
    vol = returns.rolling(window, min_periods=window).std()
    return ret_over_window.div(vol.where(vol > 0))


def _build_tsmom_consistency(close: pd.DataFrame, window: int) -> pd.DataFrame:
    if window % 20 != 0:
        raise ValueError("tsmom_consistency requires a window that is a multiple of 20")
    blocks = window // 20
    block_returns = close.pct_change(20, fill_method=None)
    # gt(0) on NaN silently evaluates False, which would hide a genuinely
    # missing block return as a "negative" one; re-mask explicitly so an
    # invalid block return stays NaN and is caught by the isfinite check
    # below instead of silently miscounting.
    positive_block = block_returns.gt(0).astype(float).where(block_returns.notna())

    def block_fraction(values: np.ndarray) -> float:
        # The window's last row is "today"; the six block-end points are
        # today, today-20d, today-40d, ... today-100d, i.e. sampled
        # backward from the end of the window, not forward from its start
        # (forward sampling would include position 0, which is one day
        # short of the first block's own 20-day return and always invalid).
        sampled = values[-1::-20][:blocks]
        if len(sampled) != blocks or not np.isfinite(sampled).all():
            return np.nan
        return float(np.mean(sampled))

    return positive_block.rolling(window, min_periods=window).apply(block_fraction, raw=True)


def _build_vol_of_vol(close: pd.DataFrame, window: int) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    short_vol = returns.rolling(20, min_periods=20).std()
    vol_of_vol = short_vol.rolling(window, min_periods=window).std()
    vol_level = short_vol.rolling(window, min_periods=window).mean()
    return vol_of_vol.div(vol_level.where(vol_level > 0))


def _build_illiquidity_trend(
    close: pd.DataFrame, amount: pd.DataFrame, window: int
) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    illiquidity = returns.abs().div(amount.where(amount > 0))
    amihud_short = illiquidity.rolling(20, min_periods=20).mean()
    amihud_long = illiquidity.rolling(window, min_periods=window).mean()
    return amihud_short.div(amihud_long.where(amihud_long > 0)).sub(1.0)


# --- Batch C: relative market risk structure --------------------------

def _build_downside_correlation(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """corr(r_i, r_m) computed only on the market's own down days
    (r_m<0), rolling window with a relaxed conditional min_periods (the
    down-day subset of a 60-row span is never itself 60 rows)."""
    returns, market = _market_return(close)
    min_periods = _conditional_min_periods(window)
    down_mask = market.lt(0)
    return _rolling_corr_scalar(
        market.where(down_mask), returns.where(down_mask, axis=0), window, min_periods
    )


def _build_beta_variability(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Standard deviation of the rolling-20-day beta over the trailing
    `window` days: instability of market exposure, not its level."""
    returns, market = _market_return(close)
    beta20 = _rolling_beta(market, returns, 20, 20)
    return beta20.rolling(window, min_periods=window).std()


def _build_market_tail_relative_return(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """mean(r_i - r_m) on the market's own worst 20% days within the
    trailing window (a crisis-day relative-return persistence candidate,
    not the always-on residual-downside-mean family)."""
    returns, market = _market_return(close)
    market_q20 = market.rolling(window, min_periods=window).quantile(0.20)
    tail_day = market.le(market_q20)
    relative_return = returns.sub(market, axis=0)
    return _rolling_conditional_mean(relative_return, tail_day, window, min_periods=3)


def _build_capture_asymmetry(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """[mean(r_i|up)/mean(r_m|up)] - [mean(r_i|down)/mean(r_m|down)]: the
    difference between the name's up-capture and down-capture ratios (not
    the same statistic as beta_asymmetry, which differences the two
    *regression slopes* rather than the two *conditional-mean ratios*;
    left as a separate candidate, resolved by the no-label dedup precheck,
    not assumed identical up front)."""
    returns, market = _market_return(close)
    min_periods = _conditional_min_periods(window)
    up_mask, down_mask = market.gt(0), market.lt(0)
    up_i = _rolling_conditional_mean(returns, up_mask, window, min_periods)
    up_m = _rolling_conditional_mean(
        pd.DataFrame({c: market for c in returns.columns}, index=returns.index),
        up_mask, window, min_periods,
    )
    down_i = _rolling_conditional_mean(returns, down_mask, window, min_periods)
    down_m = _rolling_conditional_mean(
        pd.DataFrame({c: market for c in returns.columns}, index=returns.index),
        down_mask, window, min_periods,
    )
    up_capture = up_i.div(up_m.where(up_m.abs() > 0))
    down_capture = down_i.div(down_m.where(down_m.abs() > 0))
    return up_capture - down_capture


def _build_corr_level(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Plain corr(r_i, r_m), dense rolling window (no conditioning). Low
    correlation marks a diversifier; direction -1 expects the more
    market-linked names to be relatively weaker."""
    returns, market = _market_return(close)
    return _rolling_corr_scalar(market, returns, window)


def _build_residual_vol_term_structure(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """std(residual, 20) / std(residual, 60), residual = r_i - r_m (the
    same market leg as etf_group_daily_rounds._market_residuals). A term
    structure of IDIOSYNCRATIC volatility, distinct from the existing
    realized_vol_term_structure family (which is on total return, not the
    market-residual)."""
    del window  # this candidate's own two legs are fixed at 20 and 60
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)
    short_vol = residual.rolling(20, min_periods=20).std()
    long_vol = residual.rolling(60, min_periods=60).std()
    return short_vol.div(long_vol.where(long_vol > 0))


# --- Round 2: relative market risk structure (Theme A continuation) ---

def _rolling_conditional_skew(
    value: pd.DataFrame, mask: pd.Series, window: int, min_periods: int
) -> pd.DataFrame:
    """Rolling skew of `value` within the trailing window, counting only
    rows where `mask` is True. `.rolling().apply(raw=True)` receives the
    raw (NaN-laden, mask-excluded) window and is trusted to enforce its own
    validity floor (min_periods here is our own conditional-subset floor,
    not pandas' dense one, exactly the same relationship as
    _rolling_conditional_mean's `count.where(count >= min_periods)`)."""
    masked = value.where(mask, axis=0)

    def skew_of_valid(window_values: np.ndarray) -> float:
        valid = window_values[~np.isnan(window_values)]
        if len(valid) < min_periods:
            return np.nan
        return float(pd.Series(valid).skew())

    return masked.rolling(window, min_periods=1).apply(skew_of_valid, raw=True)


def _build_high_low_vol_beta_gap(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """beta(r_i, r_m) on the market's own high-realized-vol days minus the
    same beta on its low-vol days, both within the trailing window. High/low
    is relative and self-referential: a day is "high-vol" if the market's
    trailing 5-day realized vol on that day is at or above the trailing
    `window`-day rolling MEDIAN of that same 5-day vol series (both legs
    computed only from data up to and including that day, so the regime
    label itself is causal). Same conditional-beta-difference construction
    as beta_asymmetry (already HAS_LEADS), but conditioning on the market's
    own volatility regime instead of the sign of its return."""
    returns, market = _market_return(close)
    min_periods = _conditional_min_periods(window)
    market_vol5 = market.rolling(5, min_periods=5).std()
    vol_median = market_vol5.rolling(window, min_periods=window).median()
    valid_regime = market_vol5.notna() & vol_median.notna()
    high_vol = valid_regime & market_vol5.ge(vol_median)
    low_vol = valid_regime & market_vol5.lt(vol_median)
    beta_high = _rolling_beta(
        market.where(high_vol), returns.where(high_vol, axis=0), window, min_periods
    )
    beta_low = _rolling_beta(
        market.where(low_vol), returns.where(low_vol, axis=0), window, min_periods
    )
    return beta_high - beta_low


def _build_market_jump_response(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """mean(|r_i - r_m|) on the market's own "jump" days (|r_m| in the
    trailing window's own top 20% by absolute value, either direction)
    minus the same conditional mean on non-jump days: does this name move
    more (in absolute idiosyncratic terms) specifically when the market
    itself makes an unusually large move, versus its ordinary-day baseline.
    Distinct from market_tail_relative_return (which conditions on the
    worst 20% only, directional, and reports signed excess return, not
    absolute idiosyncratic dispersion relative to a same-name baseline)."""
    returns, market = _market_return(close)
    min_periods = _conditional_min_periods(window)
    abs_market = market.abs()
    jump_threshold = abs_market.rolling(window, min_periods=window).quantile(0.80)
    valid = abs_market.notna() & jump_threshold.notna()
    jump_day = valid & abs_market.ge(jump_threshold)
    normal_day = valid & ~abs_market.ge(jump_threshold)
    idio_dispersion = returns.sub(market, axis=0).abs()
    jump_mean = _rolling_conditional_mean(idio_dispersion, jump_day, window, min_periods=3)
    normal_mean = _rolling_conditional_mean(idio_dispersion, normal_day, window, min_periods)
    return jump_mean - normal_mean


def _build_lag1_beta_to_market(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """beta(r_i,t on r_m,t-1): dense (unconditional) rolling regression of
    today's member return on yesterday's market return. A persistently
    positive lag-1 beta marks a name whose price keeps catching up to
    information the market already priced in the day before (slow
    diffusion / non-synchronous trading); direction +1 expects that
    catch-up tendency to continue predicting near-term relative strength.
    A different raw statistic from the already-registered lead_to_market
    (a DIFFERENCE of two opposite-direction lead-lag correlations, tested
    NO_DIRECTIONAL_LEAD), not assumed identical up front."""
    returns, market = _market_return(close)
    return _rolling_beta(market.shift(1), returns, window, window)


def _build_residual_skew_gap(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """skew(r_i - r_m | r_m>0) - skew(r_i - r_m | r_m<0): the difference
    between the name's idiosyncratic-return skew on the market's up-days
    and its skew on the market's down-days. A larger (more positive) gap
    means the name's residual distribution is more favorably (right-)
    skewed specifically when the market rises than when it falls -- an
    upside-optionality / resilience signal; direction +1 expects that
    asymmetry to predict relative strength."""
    returns, market = _market_return(close)
    min_periods = _conditional_min_periods(window)
    residual = returns.sub(market, axis=0)
    up_mask, down_mask = market.gt(0), market.lt(0)
    skew_up = _rolling_conditional_skew(residual, up_mask, window, min_periods)
    skew_down = _rolling_conditional_skew(residual, down_mask, window, min_periods)
    return skew_up - skew_down


# --- Round 2: higher-order co-movement (Theme B) ----------------------

def _build_residual_market_vol_corr(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """corr(market_vol, |r_i - r_m|): does this name's idiosyncratic return
    dispersion expand specifically when the market's own volatility
    (trailing 5-day realized) expands, i.e. does its idiosyncratic risk
    fail to diversify away exactly when overall risk is elevated. A
    different statistic from beta_variability (instability of the beta
    LEVEL over time) and from vol_of_vol (the name's OWN vol-of-vol,
    market-independent): this is a co-movement between the market's vol
    regime and the name's residual dispersion, both measured concurrently.
    direction -1: higher pro-cyclical idiosyncratic dispersion predicts
    relative weakness."""
    returns, market = _market_return(close)
    idio_abs = returns.sub(market, axis=0).abs()
    market_vol = market.rolling(5, min_periods=5).std()
    return _rolling_corr_scalar(market_vol, idio_abs, window)


# --- Round 3: higher-order co-movement continued + cross-group network ---
#
# Both cokurtosis and downside_coskewness use the raw-moment expansion of a
# centered joint co-moment (avoiding an explicit per-window re-centering
# pass, the same technique _rolling_beta/_rolling_corr_scalar already use
# for the 2nd joint moment). Verified numerically against the direct/naive
# definition on synthetic arrays before being written into this module:
#   E[(X-EX)(Y-EY)^2] = E[XY^2] - 2*EY*E[XY] + 2*EX*EY^2 - EX*E[Y^2]
#   E[(X-EX)(Y-EY)^3] = E[XY^3] - 3*EY*E[XY^2] + 3*EY^2*E[XY]
#                        - EX*E[Y^3] + 3*EY*EX*E[Y^2] - 3*EX*EY^3

def _build_cokurtosis(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Co-kurtosis of member on market: E[(r_i-E_i)(r_m-E_m)^3] /
    (std_i * std_m^3), dense rolling window. Measures whether the name's
    returns amplify specifically on the market's own extreme (tail) days,
    a 4th-moment analog of coskewness (already registered and HAS_LEADS as
    daily_rounds:market_coskewness, a different -- 3rd moment -- statistic,
    not re-derived here). direction -1: higher systematic tail
    co-movement predicts relative weakness."""
    returns, market = _market_return(close)
    mp = window
    ex = returns.rolling(window, min_periods=mp).mean()
    ey = market.rolling(window, min_periods=mp).mean()
    exy3 = returns.mul(market.pow(3), axis=0).rolling(window, min_periods=mp).mean()
    exy2 = returns.mul(market.pow(2), axis=0).rolling(window, min_periods=mp).mean()
    exy = returns.mul(market, axis=0).rolling(window, min_periods=mp).mean()
    ey3 = market.pow(3).rolling(window, min_periods=mp).mean()
    ey2 = market.pow(2).rolling(window, min_periods=mp).mean()
    numerator = (
        exy3
        .sub(exy2.mul(3 * ey, axis=0))
        .add(exy.mul(3 * ey.pow(2), axis=0))
        .sub(ex.mul(ey3, axis=0))
        .add(ex.mul(3 * ey, axis=0).mul(ey2, axis=0))
        .sub(ex.mul(3 * ey.pow(3), axis=0))
    )
    var_i = returns.pow(2).rolling(window, min_periods=mp).mean() - ex.pow(2)
    var_m = market.pow(2).rolling(window, min_periods=mp).mean() - ey.pow(2)
    std_i = var_i.where(var_i > 0).pow(0.5)
    std_m3 = var_m.where(var_m > 0).pow(1.5)
    return numerator.div(std_i.mul(std_m3, axis=0))


def _build_downside_coskewness(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Coskewness of member on market, computed only on the market's own
    down days (r_m<0): E[(r_i-E_i)(r_m-E_m)^2 | r_m<0] / (std_i|down *
    var_m|down), the same conditional-subset technique as
    downside_correlation (Batch C) but for the 3rd joint co-moment
    (Harvey-Siddique style downside coskewness). direction -1: a name
    whose downside amplifies more than proportionally when the market
    itself is already falling predicts relative weakness."""
    returns, market = _market_return(close)
    min_periods = _conditional_min_periods(window)
    down_mask = market.lt(0)
    market2 = market.pow(2)
    ey = _rolling_conditional_mean_series(market, down_mask, window, min_periods)
    ey2 = _rolling_conditional_mean_series(market2, down_mask, window, min_periods)
    ex = _rolling_conditional_mean(returns, down_mask, window, min_periods)
    exy = _rolling_conditional_mean(returns.mul(market, axis=0), down_mask, window, min_periods)
    exy2 = _rolling_conditional_mean(returns.mul(market2, axis=0), down_mask, window, min_periods)
    numerator = (
        exy2
        .sub(exy.mul(2 * ey, axis=0))
        .add(ex.mul(2 * ey.pow(2), axis=0))
        .sub(ex.mul(ey2, axis=0))
    )
    exx = _rolling_conditional_mean(returns.pow(2), down_mask, window, min_periods)
    var_i = exx - ex.pow(2)
    var_m = ey2 - ey.pow(2)
    denom = var_i.where(var_i > 0).pow(0.5).mul(var_m.where(var_m > 0), axis=0)
    return numerator.div(denom)


def _pairwise_residual_corr(close: pd.DataFrame, window: int) -> tuple[list[str], dict[tuple[str, str], pd.Series]]:
    """All 91 (14-choose-2) rolling pairwise correlations of the market
    residuals (residual = r_i - r_m), keyed symmetrically. Shared by
    avg_peer_residual_corr (mean of a member's 13 peer correlations) and
    peer_corr_dispersion (their std), so the O(n^2) pairwise cost is paid
    once per candidate, not once per aggregation. Deliberately NOT a
    shortcut correlation against a leave-one-out linear combination of the
    other residuals: because r_m is the equal-weight mean of ALL 14
    members INCLUDING i itself, the 14 residuals sum to exactly zero at
    every date (sum_k(r_k) - 14*mean(r_k) == 0 identically), so a
    leave-one-out AVERAGE of the other 13 residuals is an exact negative
    scalar multiple of residual_i (peer_i == -residual_i/13 algebraically)
    and would correlate at exactly +/-1 regardless of the data -- confirmed
    as a real bug via a synthetic smoke test before being caught here, not
    merely suspected. Averaging (or taking the dispersion of) 13 separate
    genuine pairwise correlations has no such identity forcing it to a
    fixed value."""
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)
    cols = list(residual.columns)
    n = len(cols)
    pair_corr: dict[tuple[str, str], pd.Series] = {}
    for a in range(n):
        for b in range(a + 1, n):
            ca, cb = cols[a], cols[b]
            corr_ab = _rolling_corr_scalar(residual[ca], residual[[cb]], window)[cb]
            pair_corr[(ca, cb)] = corr_ab
            pair_corr[(cb, ca)] = corr_ab
    return cols, pair_corr


def _build_avg_peer_residual_corr(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """mean over the other 13 members j of corr(residual_i, residual_j).
    Measures whether the name's idiosyncratic (market-adjusted) moves
    still comove with the rest of the 14-name network; direction -1:
    higher residual crowding with peers means less true diversification
    value, predicting relative weakness."""
    cols, pair_corr = _pairwise_residual_corr(close, window)
    n = len(cols)
    result = pd.DataFrame(index=next(iter(pair_corr.values())).index, columns=cols, dtype=float)
    for a in range(n):
        ca = cols[a]
        peer_corrs = [pair_corr[(ca, cols[b])] for b in range(n) if b != a]
        result[ca] = sum(peer_corrs) / (n - 1)
    return result


def _build_peer_corr_dispersion(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """std over the other 13 members j of corr(residual_i, residual_j):
    is the name's connectedness to the network EVEN (similar correlation
    to all 13 peers) or CONCENTRATED (highly correlated with a subgroup,
    near-zero with the rest). A different statistic from
    avg_peer_residual_corr (the LEVEL of connectedness, not its
    unevenness); the two are computed from the same underlying pairwise
    matrix but are not the same number and are not assumed related a
    priori (resolved, like everything else in this module, by the
    no-label dedup precheck rather than an a priori collision judgment).
    direction -1: a concentrated (uneven) peer-correlation structure is
    treated as a crowding/fragility signal, the same directional logic
    already used for illiquidity_trend/downside_correlation/
    high_low_vol_beta_gap (concentration or crowding predicts relative
    weakness)."""
    cols, pair_corr = _pairwise_residual_corr(close, window)
    n = len(cols)
    result = pd.DataFrame(index=next(iter(pair_corr.values())).index, columns=cols, dtype=float)
    for a in range(n):
        ca = cols[a]
        peer_corrs = pd.concat([pair_corr[(ca, cols[b])] for b in range(n) if b != a], axis=1)
        result[ca] = peer_corrs.std(axis=1)
    return result


def _build_peer_corr_network_change(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """avg_peer_residual_corr on a short (20-day) window minus its own
    long (60-day) window value: is the name's residual connectedness to
    the rest of the network currently rising relative to its own recent
    history. Same term-structure construction as corr_stability_20_60 and
    residual_vol_term_structure_20_60, applied to the peer-network
    correlation level instead of the market correlation level or
    idiosyncratic vol. direction -1: a rising peer-connectedness trend
    predicts relative weakness. Registered window is 60 (the longer of
    its own two fixed internal legs, 20 and 60)."""
    del window  # this candidate's own two legs are fixed at 20 and 60
    short = _build_avg_peer_residual_corr(close, 20)
    long = _build_avg_peer_residual_corr(close, 60)
    return short - long


# --- Round 4: trading-activity relative to market (Theme E) -----------

def _build_amount_beta_to_market_amount(close: pd.DataFrame, amount: pd.DataFrame, window: int) -> pd.DataFrame:
    """beta(amount_change_i, market_amount_change), dense rolling window,
    where amount_change is a simple percent change (the "return" of daily
    traded amount) and market_amount_change is the fixed14 equal-weight
    mean of all 14 members' amount_change on dates where all 14 are valid
    (same all-complete-only convention as _market_return, applied to
    amount instead of price). A different statistic from the already-
    registered daily_rounds:market_residual_amount_beta (which regresses
    PRICE residual on the member's OWN amount innovation, price-vs-own-
    volume); this is member-amount-change vs MARKET-amount-change,
    amount-vs-amount cross-sectional elasticity, not price-vs-own-volume.
    direction -1: a name whose trading-activity surges amplify in lockstep
    with aggregate market trading activity is treated as a liquidity-
    herding/crowding signal, predicting relative weakness."""
    amount_change = amount.pct_change(fill_method=None)
    all_valid = amount_change.notna().all(axis=1)
    market_amount_change = amount_change.mean(axis=1).where(all_valid)
    return _rolling_beta(market_amount_change, amount_change, window, window)


def _build_volume_surge_relative_return(close: pd.DataFrame, amount: pd.DataFrame, window: int) -> pd.DataFrame:
    """mean(r_i - r_m) on the member's OWN high-trading-activity days
    (its own amount in the trailing window's own top 20%, a per-member
    threshold, not a market-wide one) minus the same conditional mean on
    its own ordinary-activity days: does this name's relative return
    firm up specifically when ITS OWN trading activity surges (volume
    confirming price, a standard technical-analysis heuristic). Distinct
    from market_jump_response (conditions on the MARKET's own move
    magnitude, not the member's own amount) and from
    market_tail_relative_return (conditions on the market's worst days,
    not the member's own volume). direction +1: relative-return
    confirmation on the member's own high-activity days predicts
    continuation."""
    returns, market = _market_return(close)
    min_periods = _conditional_min_periods(window)
    amount_q80 = amount.rolling(window, min_periods=window).quantile(0.80)
    valid = amount.notna() & amount_q80.notna()
    surge_day = valid & amount.ge(amount_q80)
    normal_day = valid & ~amount.ge(amount_q80)
    relative_return = returns.sub(market, axis=0)
    surge_mean = _rolling_conditional_mean(relative_return, surge_day, window, min_periods=3)
    normal_mean = _rolling_conditional_mean(relative_return, normal_day, window, min_periods)
    return surge_mean - normal_mean


def _build_amount_share_change(close: pd.DataFrame, amount: pd.DataFrame, window: int) -> pd.DataFrame:
    """This member's share of total 14-name trading amount
    (amount_i / sum_all_14(amount)) on a short (20-day) rolling average
    minus its own long (60-day) rolling average: is the name's relative
    trading-activity share currently elevated versus its own recent
    longer-run level. Same term-structure construction as
    corr_stability_20_60/residual_vol_term_structure_20_60/
    peer_corr_network_change, applied to trading-activity share instead
    of a correlation or volatility level. direction +1: a rising relative
    activity-share trend is treated as a capital-attention/flow-following
    signal, predicting relative strength. Registered window is 60 (the
    longer of its own two fixed internal legs, 20 and 60)."""
    del window  # this candidate's own two legs are fixed at 20 and 60
    total_amount = amount.sum(axis=1)
    share = amount.div(total_amount.where(total_amount > 0), axis=0)
    short = share.rolling(20, min_periods=20).mean()
    long = share.rolling(60, min_periods=60).mean()
    return short - long


# --- Round 4: overnight information (Theme F) --------------------------

def _build_overnight_momentum_relative_market(open_: pd.DataFrame, close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling mean of (overnight_i - overnight_market), overnight =
    open/prev_close - 1, overnight_market = the fixed14 all-complete
    equal-weight mean of all 14 members' overnight returns (same
    leg-specific market definition _build_overnight_intraday_beta_gap
    already uses for its overnight leg). A persistent positive relative
    overnight edge is treated as momentum (overnight returns carry
    distinct, often macro/gap-driven information from intraday returns);
    direction +1: persistence of that edge predicts continuation."""
    overnight = open_.div(close.shift(1)).sub(1.0)
    _overnight_returns, overnight_market = _market_return_from(overnight)
    relative_overnight = overnight.sub(overnight_market, axis=0)
    return relative_overnight.rolling(window, min_periods=window).mean()


def _build_overnight_intraday_sign_consistency_relative_market(
    open_: pd.DataFrame, close: pd.DataFrame, window: int
) -> pd.DataFrame:
    """Rate at which this member's own overnight and intraday returns
    have the SAME sign (a "trend continuation from open to close" day),
    minus the analogous rate for the market itself (each leg's own
    fixed14 all-complete equal-weight mean, same construction as
    overnight_intraday_beta_gap). A different statistic from the already-
    tested daily_rounds:overnight_intraday_switch_rate, which compares
    sign(FULL close-to-close return) against sign(intraday return) with
    no market benchmark; this compares sign(OVERNIGHT alone) against
    sign(intraday alone), and subtracts the market's own rate rather than
    reporting an absolute level. direction +1: a name whose
    overnight-to-intraday moves reinforce (agree in sign) more often than
    the market's own baseline rate is treated as a trend-confirmation
    signal, predicting continuation."""
    overnight = open_.div(close.shift(1)).sub(1.0)
    intraday = close.div(open_).sub(1.0)
    _overnight_returns, overnight_market = _market_return_from(overnight)
    _intraday_returns, intraday_market = _market_return_from(intraday)
    own_valid = overnight.notna() & intraday.notna()
    own_agree = own_valid & (np.sign(overnight) == np.sign(intraday))
    own_rate = own_agree.astype(float).where(own_valid).rolling(window, min_periods=window).mean()
    market_valid = overnight_market.notna() & intraday_market.notna()
    market_agree = market_valid & (np.sign(overnight_market) == np.sign(intraday_market))
    market_rate = market_agree.astype(float).where(market_valid).rolling(window, min_periods=window).mean()
    return own_rate.sub(market_rate, axis=0)


# --- Round 5: correlation to fixed macro anchors (Theme C, remaining) --

def _anchor_residual_corrs(close: pd.DataFrame, window: int) -> list[pd.DataFrame]:
    """Rolling corr(residual_anchor, residual_i) for each of the 3 fixed
    anchors, against every one of the 14 members (including the anchor
    itself, which is trivially always corr==1 in its own row -- a real,
    not degenerate, edge case: the anchor member's "distance from its own
    macro group" is meaningfully always-perfectly-correlated with itself,
    not an algebraic artifact like the avg_peer_residual_corr bug)."""
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)
    missing = [t for t in _ANCHOR_TICKERS if t not in residual.columns]
    if missing:
        raise KeyError(f"anchor tickers not in the fixed 14-name pool: {missing}")
    return [_rolling_corr_scalar(residual[t], residual, window) for t in _ANCHOR_TICKERS]


def _build_corr_dispersion_vs_anchors(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """max - min across the 3 anchor correlations: is this name's macro
    linkage concentrated in ONE specific anchor (gold / US large-growth /
    HK tech) or spread evenly across all three. direction -1: a
    concentrated, single-regime-dependent linkage is treated as a
    fragility/crowding signal, the same directional logic already used
    for peer_corr_dispersion and illiquidity_trend."""
    c0, c1, c2 = _anchor_residual_corrs(close, window)
    corr_max = c0.combine(c1, np.maximum).combine(c2, np.maximum)
    corr_min = c0.combine(c1, np.minimum).combine(c2, np.minimum)
    return corr_max - corr_min


def _build_corr_level_to_nearest_anchor(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """max across the 3 anchor correlations: how strongly is this name
    tied to its single CLOSEST macro anchor, regardless of which one.
    direction -1: stronger anchor-dependence means less true
    diversification value, the same directional logic already used for
    corr_level (dropped on dedup in round 1, not re-derived here -- this
    is a different statistic, the max of 3 specific anchor correlations,
    not a single correlation to the fixed14 market average)."""
    c0, c1, c2 = _anchor_residual_corrs(close, window)
    return c0.combine(c1, np.maximum).combine(c2, np.maximum)


def _build_corr_nearest_anchor_change(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """corr_level_to_nearest_anchor on a short (20-day) window minus its
    own long (60-day) window value: is anchor-dependence currently rising
    relative to its own recent history. Same term-structure construction
    as corr_stability_20_60/residual_vol_term_structure_20_60/
    peer_corr_network_change. direction -1: a rising anchor-dependence
    trend predicts relative weakness. Registered window is 60 (the longer
    of its own two fixed internal legs, 20 and 60)."""
    del window  # this candidate's own two legs are fixed at 20 and 60
    short = _build_corr_level_to_nearest_anchor(close, 20)
    long = _build_corr_level_to_nearest_anchor(close, 60)
    return short - long


# --- Round 5: cross-group conditional dependence (Theme G) ------------

def _build_quantile_beta_gap(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """beta(r_i, r_m) on the market's own top-tercile-return days minus
    the same beta on its bottom-tercile-return days, both within the
    trailing window (tercile thresholds are the window's own rolling 1/3
    and 2/3 quantiles of r_m, so the regime label is causal). Same
    conditional-beta-difference construction as beta_asymmetry (already
    HAS_LEADS) and high_low_vol_beta_gap, conditioning on the market's
    RETURN LEVEL (top vs bottom tercile) instead of its sign or its
    volatility regime. direction -1: amplified beta specifically on the
    market's best days relative to its worst days is treated as an
    asymmetric-upside-exposure risk-concentration signal, predicting
    relative weakness."""
    returns, market = _market_return(close)
    # A tercile (~1/3) subset of a 60-row window has ~20 qualifying days,
    # smaller than the ~50% subsets _conditional_min_periods was
    # calibrated for; its floor of 15 would demand 75% density within a
    # ~20-row tercile subset, elevating the NaN rate well past what a
    # regression genuinely needs. Use the same floor value (10) but
    # without the window//4 term, matching a beta regression's need for
    # more points than a simple conditional mean (unlike the tail
    # candidates' min_periods=3), just relaxed from the 50%-subset floor.
    min_periods = 10
    market_q33 = market.rolling(window, min_periods=window).quantile(1.0 / 3.0)
    market_q67 = market.rolling(window, min_periods=window).quantile(2.0 / 3.0)
    valid = market.notna() & market_q33.notna() & market_q67.notna()
    top_mask = valid & market.ge(market_q67)
    bottom_mask = valid & market.le(market_q33)
    beta_top = _rolling_beta(
        market.where(top_mask), returns.where(top_mask, axis=0), window, min_periods
    )
    beta_bottom = _rolling_beta(
        market.where(bottom_mask), returns.where(bottom_mask, axis=0), window, min_periods
    )
    return beta_top - beta_bottom


def _build_tail_coexceedance_asymmetry(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Upper-tail coexceedance rate minus lower-tail coexceedance rate,
    a standard tail-dependence-coefficient-style estimator. Upper:
    P(member in its own top-20% days | market in its own top-20% days)
    within the trailing window, i.e. the fraction of the market's own
    best days on which the member was ALSO independently having one of
    its own best days; lower is the analogous quantity for both series'
    bottom-20% days. direction +1: a name that co-exceeds with the
    market's upside more often than with its downside (upside beta
    without matching downside beta) is treated as a favorable asymmetry,
    predicting relative strength."""
    returns, market = _market_return(close)
    # A 20%-quantile tail subset of a 60-row window has ~12 qualifying
    # days on average, below _conditional_min_periods(60)=15 (calibrated
    # for ~50% up/down subsets elsewhere in this module); using that
    # floor here would make the whole candidate structurally all-NaN, not
    # legitimately sparse. Use the same min_periods=3 floor as
    # market_tail_relative_return's own 20%-tail conditional mean.
    min_periods = 3
    market_q80 = market.rolling(window, min_periods=window).quantile(0.80)
    market_q20 = market.rolling(window, min_periods=window).quantile(0.20)
    member_q80 = returns.rolling(window, min_periods=window).quantile(0.80)
    member_q20 = returns.rolling(window, min_periods=window).quantile(0.20)
    market_valid = market.notna() & market_q80.notna() & market_q20.notna()
    member_valid = returns.notna() & member_q80.notna() & member_q20.notna()

    market_up = (market_valid & market.ge(market_q80)).astype(float)
    market_down = (market_valid & market.le(market_q20)).astype(float)
    member_up = member_valid & returns.ge(member_q80)
    member_down = member_valid & returns.le(member_q20)
    joint_up = member_up.astype(float).mul(market_up, axis=0)
    joint_down = member_down.astype(float).mul(market_down, axis=0)

    market_up_count = market_up.rolling(window, min_periods=1).sum()
    market_down_count = market_down.rolling(window, min_periods=1).sum()
    joint_up_count = joint_up.rolling(window, min_periods=1).sum()
    joint_down_count = joint_down.rolling(window, min_periods=1).sum()

    coexceed_up = joint_up_count.div(
        market_up_count.where(market_up_count >= min_periods), axis=0
    )
    coexceed_down = joint_down_count.div(
        market_down_count.where(market_down_count >= min_periods), axis=0
    )
    return coexceed_up - coexceed_down


# --- Round 5: minute-level co-movement (Theme D), 5m bars -------------
#
# Unlike every other candidate in this module, these three read 5-minute
# intraday bars (already-resampled data/etf_rotation_v1/5m/<symbol>.parquet,
# NOT the raw 1m ticks). The daily-frequency feature each registers is a
# 20-TRADING-DAY rolling mean of a per-day intraday statistic computed from
# that single day's ~47 within-day 5m returns; "window=20" therefore means
# 20 trading days of smoothing over the daily statistic, not 20 five-minute
# bars, matching every other window in this module being trading-day-based.

def load_minute_panels(root, symbols: list[str], as_of: str) -> dict[str, pd.DataFrame]:
    """Load 5m OHLC bars for the fixed 14-name pool from
    data/etf_rotation_v1/5m/<symbol>.parquet, as wide DataFrames (index=5m
    timestamp, columns=symbol), bounded to `as_of`'s calendar date
    inclusive. Only 'close' is actually used by the three minute
    candidates, but open/high/low are loaded too for parity with the
    daily loader and potential future use."""
    from pathlib import Path
    root = Path(root)
    upper = pd.Timestamp(as_of) + pd.Timedelta(days=1)
    fields: dict[str, dict[str, pd.Series]] = {"open": {}, "high": {}, "low": {}, "close": {}}
    for sym in symbols:
        df = pd.read_parquet(root / "5m" / f"{sym}.parquet")
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime").sort_index()
        df = df.loc[df.index < upper]
        for key in fields:
            fields[key][sym] = df[key]
    return {key: pd.DataFrame(values).sort_index() for key, values in fields.items()}


def apply_513100_halt_mask(minute_panels: dict[str, pd.DataFrame], root) -> dict[str, pd.DataFrame]:
    """513100.SH is QDII-quota-gated and halts trading at the open,
    resuming at 10:30, on days its onshore premium is elevated (project
    memory: "高溢价时开盘停牌至10:30"). Its 5m bars in that window are
    either absent or a stale carry-forward of the prior close, not real
    trades; including them would fabricate liquidity that never existed.
    Reuses the existing, already-tested `open_halt_dates` diagnostic
    (etf_ic_monthly_factory.py, built for the monthly IC factory's own
    halt-window handling) on 513100.SH's raw 1m data to identify halted
    dates, then masks (sets to NaN) ONLY 513100.SH's 09:35-10:30 5m bars
    on those dates -- the same window open_halt_dates itself checks
    (09:31-10:30) for zero volume."""
    from pathlib import Path
    from .etf_ic_monthly_factory import open_halt_dates
    root = Path(root)
    ticker = "513100.SH"
    if ticker not in minute_panels["close"].columns:
        return minute_panels
    raw = pd.read_parquet(root / "1m" / f"{ticker}.parquet")
    raw["datetime"] = pd.to_datetime(raw["datetime"])
    halted = open_halt_dates(raw[["datetime", "volume"]])
    if len(halted) == 0:
        return minute_panels
    idx = minute_panels["close"].index
    minute_of_day = idx.hour * 60 + idx.minute
    in_halt_window = (minute_of_day >= 571) & (minute_of_day <= 630)  # 09:31-10:30
    is_halted_day = pd.Series(idx.normalize(), index=idx).isin(pd.DatetimeIndex(halted)).to_numpy()
    mask = pd.Series(in_halt_window & is_halted_day, index=idx)
    out = {key: value.copy() for key, value in minute_panels.items()}
    for key in out:
        out[key].loc[mask, ticker] = np.nan
    return out


def load_macro_panel(root, as_of: str) -> pd.DataFrame:
    """Round 11 (master's own formulas). Load the 5 macro variables from
    local read-only parquet files under `root` (the exact
    .../long_history_proxies/macro directory, a different root than the
    price DATA_ROOT -- these are research-only proxy series, no data-
    production-authority claim), as a single wide DataFrame indexed by
    each variable's own native calendar date (union across all 5; each
    file's own date/trade_date column is NOT yet aligned to the A-share
    trading calendar -- that alignment, including the domestic-same-day
    vs foreign-next-day lag rule, happens inside the build functions that
    consume this panel via `_macro_daily_changes`, using the `close`
    panel's own index as the target A-share calendar). Bounded to as_of
    inclusive on each series' own native date (source files themselves
    extend through 2026-03-24; this is a defensive bound, not a
    workaround for a coverage gap -- verified all 5 series cover the
    campaign's full 2023-07-27+ price-panel window with no gaps).

    Column mapping: real_rate=us_trycr.y10 (US 10y TIPS real yield),
    nominal_rate=us_tycr.y10 (US 10y nominal yield), usdcnh=USDCNH.
    bid_close, copper=CU.close (Shanghai copper futures main), bond_
    future=T.close (10y China government bond futures main)."""
    from pathlib import Path
    root = Path(root)
    as_of_ts = pd.Timestamp(as_of)

    def _load(path, date_col, value_col):
        df = pd.read_parquet(path)
        dates = pd.to_datetime(df[date_col].astype(str), format="%Y%m%d")
        s = pd.Series(df[value_col].to_numpy(dtype=float), index=dates)
        s = s[~s.index.duplicated(keep="last")].sort_index()
        return s.loc[s.index <= as_of_ts]

    series = {
        "real_rate": _load(root / "us_trycr.parquet", "date", "y10"),
        "nominal_rate": _load(root / "us_tycr.parquet", "date", "y10"),
        "usdcnh": _load(root / "USDCNH.parquet", "trade_date", "bid_close"),
        "copper": _load(root / "CU.parquet", "trade_date", "close"),
        "bond_future": _load(root / "T.parquet", "trade_date", "close"),
    }
    return pd.DataFrame(series)[list(_MACRO_COLUMNS)].sort_index()


def _intraday_5m_returns(minute_close: pd.DataFrame) -> pd.DataFrame:
    """Within-day 5m pct-change, reset at every day boundary (the first
    bar of each day is NaN, never an overnight gap misread as a 5-minute
    return)."""
    day = minute_close.index.normalize()
    return minute_close.groupby(day).pct_change(fill_method=None)


def _daily_intraday_pair_stats(
    x_5m: pd.Series, y_5m: pd.DataFrame, min_bars: int = 10
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """For each trading day present in x_5m/y_5m's index, compute
    corr(x, y) and beta(y on x) from that single day's 5m observations
    only (pairwise-complete per column), requiring at least `min_bars`
    valid paired bars (out of ~47 possible) or the day is NaN. Returns
    (daily_corr, daily_beta), each indexed by trading day (not by 5m
    timestamp) -- a genuinely daily-frequency panel, matching every other
    atom in this module, ready for the caller's own trading-day rolling
    window."""
    day_index = x_5m.index.normalize()
    unique_days = pd.DatetimeIndex(sorted(set(day_index)))
    cols = y_5m.columns
    corr_out = pd.DataFrame(np.nan, index=unique_days, columns=cols)
    beta_out = pd.DataFrame(np.nan, index=unique_days, columns=cols)
    x_vals = x_5m.to_numpy()
    for day in unique_days:
        day_mask = np.asarray(day_index == day)
        x_day = x_vals[day_mask]
        y_day = y_5m.loc[day_mask]
        for col in cols:
            y_col = y_day[col].to_numpy()
            valid = ~np.isnan(x_day) & ~np.isnan(y_col)
            if valid.sum() < min_bars:
                continue
            xv, yv = x_day[valid], y_col[valid]
            xc, yc = xv - xv.mean(), yv - yv.mean()
            var_x = np.mean(xc * xc)
            if var_x <= 0:
                continue
            cov = np.mean(xc * yc)
            beta_out.loc[day, col] = cov / var_x
            var_y = np.mean(yc * yc)
            if var_y <= 0:
                continue
            corr_out.loc[day, col] = cov / np.sqrt(var_x * var_y)
    return corr_out, beta_out


def _daily_market_5m(minute_close: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    returns_5m = _intraday_5m_returns(minute_close)
    all_valid = returns_5m.notna().all(axis=1)
    market_5m = returns_5m.mean(axis=1).where(all_valid)
    return returns_5m, market_5m


def _reindex_to_daily(daily_stat: pd.DataFrame, close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Reindex a trading-day-indexed intraday statistic onto the full
    daily calendar (the minute data's own trading-day index may not
    exactly match the daily panel's, e.g. at history's edges), then take
    the registered trading-day rolling mean."""
    aligned = daily_stat.reindex(close.index)
    return aligned.rolling(window, min_periods=window).mean()


def _build_intraday_realized_corr(close: pd.DataFrame, minute_close: pd.DataFrame, window: int) -> pd.DataFrame:
    """20-trading-day rolling mean of the per-day realized correlation
    between each member's 5m returns and the market's 5m returns (fixed14
    all-complete equal-weight mean of 5m returns, the intraday analog of
    _market_return). direction -1: tighter intraday co-movement with the
    market predicts relative weakness, the same directional logic as
    corr_level (daily-frequency)."""
    returns_5m, market_5m = _daily_market_5m(minute_close)
    daily_corr, _daily_beta = _daily_intraday_pair_stats(market_5m, returns_5m)
    return _reindex_to_daily(daily_corr, close, window)


def _build_intraday_realized_beta(close: pd.DataFrame, minute_close: pd.DataFrame, window: int) -> pd.DataFrame:
    """20-trading-day rolling mean of the per-day realized beta of each
    member's 5m returns on the market's 5m returns. direction -1: higher
    intraday beta amplification predicts relative weakness, the same
    directional logic as high_low_vol_beta_gap/quantile_beta_gap."""
    returns_5m, market_5m = _daily_market_5m(minute_close)
    _daily_corr, daily_beta = _daily_intraday_pair_stats(market_5m, returns_5m)
    return _reindex_to_daily(daily_beta, close, window)


def _build_minute_lead_lag_corr(close: pd.DataFrame, minute_close: pd.DataFrame, window: int) -> pd.DataFrame:
    """20-trading-day rolling mean of the per-day realized correlation
    between each member's PRIOR 5m bar return and the market's
    CONTEMPORANEOUS 5m bar return (member leads market by one 5-minute
    bar); the lag is taken within each trading day only (the first bar of
    a day has no same-day predecessor and is NaN, never wrapping into the
    prior day's last bar). direction +1: a name whose intraday moves
    systematically lead the market's is expected to keep leading,
    predicting relative strength -- the same directional sign as the
    already-registered daily-frequency lead_to_market, a different
    statistic (5-minute-bar lag, not one full trading day)."""
    returns_5m, market_5m = _daily_market_5m(minute_close)
    day = returns_5m.index.normalize()
    lagged_returns_5m = returns_5m.groupby(day).shift(1)
    daily_corr, _daily_beta = _daily_intraday_pair_stats(market_5m, lagged_returns_5m)
    return _reindex_to_daily(daily_corr, close, window)


# --- Round 5: relative liquidity structure (Theme H) -------------------

def _build_corwin_schultz_spread(high: pd.DataFrame, low: pd.DataFrame, window: int) -> pd.DataFrame:
    """Corwin-Schultz (2012) "A Simple Way to Estimate Bid-Ask Spreads
    from Daily High and Low Prices" 2-day proportional-spread estimator,
    20-day rolling mean. beta_t = ln(H_t/L_t)^2 + ln(H_{t-1}/L_{t-1})^2;
    gamma_t = ln(max(H_t,H_{t-1}) / min(L_t,L_{t-1}))^2; k = 3-2*sqrt(2);
    alpha_t = (sqrt(2*beta_t)-sqrt(beta_t))/k - sqrt(gamma_t/k);
    S_t = 2*(e^alpha_t - 1)/(1 + e^alpha_t), negative estimates clipped
    to 0 per the paper's own convention (master's spec). Uses the same
    qfq-adjusted high/low panels as every other candidate's close (same
    adjustment basis). direction -1: a wider estimated spread means worse
    liquidity, predicting relative weakness. A different statistic from
    the existing illiquidity_trend family (Amihud-style, price-impact per
    unit traded amount, not a spread estimator); resolved by the
    no-label dedup precheck, not assumed distinct a priori."""
    valid = high.gt(0) & low.gt(0) & high.ge(low)
    log_hl = np.log(high.where(valid) / low.where(valid))
    beta = log_hl.pow(2) + log_hl.shift(1).pow(2)
    h_max2 = np.maximum(high, high.shift(1))
    l_min2 = np.minimum(low, low.shift(1))
    pair_valid = valid & valid.shift(1, fill_value=False) & h_max2.gt(0) & l_min2.gt(0)
    gamma = np.log(h_max2.where(pair_valid) / l_min2.where(pair_valid)).pow(2)
    k = 3.0 - 2.0 * np.sqrt(2.0)
    alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    spread = (2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))).clip(lower=0.0)
    return spread.rolling(window, min_periods=window).mean()


# --- Round 5: residual distribution shape (Theme I) ---------------------

def _build_residual_kurtosis(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Rolling excess kurtosis (pandas' own Fisher-definition .kurt(),
    kurtosis-3) of the market residual (r_i - r_m, the same market leg as
    etf_group_daily_rounds._market_residuals). direction -1: fatter
    residual tails mark elevated idiosyncratic shock risk, predicting
    relative weakness."""
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)
    return residual.rolling(window, min_periods=window).kurt()


# --- Round 6: dispersion-conditional (Theme M) -------------------------

def _group_dispersion(returns: pd.DataFrame) -> pd.Series:
    """Daily cross-sectional std of the 8 economic groups' own mean
    returns (each group's return = equal-weight mean of ITS members on
    dates all of them are valid, matching group_scores' own convention),
    only on dates all 8 groups are valid. USER's own dispersion framework
    (see project memory 2026-09-22): high dispersion = the 8-group cross-
    section is meaningfully differentiated that day."""
    group_returns = {}
    for gid, members in _ECONOMIC_GROUPS.items():
        sub = returns[list(members)]
        all_present = sub.notna().all(axis=1)
        group_returns[gid] = sub.mean(axis=1).where(all_present)
    group_returns_df = pd.DataFrame(group_returns)
    all_groups_valid = group_returns_df.notna().all(axis=1)
    return group_returns_df.std(axis=1).where(all_groups_valid)


def _build_dispersion_conditional_relative_return(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """mean(r_i - r_m) on days the 8-group cross-sectional return
    dispersion is in the trailing window's own top tercile (high-
    dispersion days), i.e. the "winner continuation in high-dispersion
    regimes" hypothesis from USER's dispersion framework. direction +1."""
    returns, market = _market_return(close)
    min_periods = 8
    dispersion = _group_dispersion(returns)
    disp_q67 = dispersion.rolling(window, min_periods=window).quantile(2.0 / 3.0)
    valid = dispersion.notna() & disp_q67.notna()
    high_disp_day = valid & dispersion.ge(disp_q67)
    relative_return = returns.sub(market, axis=0)
    return _rolling_conditional_mean(relative_return, high_disp_day, window, min_periods)


def _build_dispersion_conditional_beta_gap(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """beta(r_i, r_m) on high-dispersion days minus the same beta on
    low-dispersion days (bottom tercile), both within the trailing
    window; same conditional-beta-difference construction as
    beta_asymmetry/high_low_vol_beta_gap/quantile_beta_gap, conditioning
    on the 8-group cross-sectional dispersion regime. direction -1."""
    returns, market = _market_return(close)
    min_periods = 10  # tercile subset, same floor as quantile_beta_gap
    dispersion = _group_dispersion(returns)
    disp_q33 = dispersion.rolling(window, min_periods=window).quantile(1.0 / 3.0)
    disp_q67 = dispersion.rolling(window, min_periods=window).quantile(2.0 / 3.0)
    valid = dispersion.notna() & disp_q33.notna() & disp_q67.notna()
    high_disp_day = valid & dispersion.ge(disp_q67)
    low_disp_day = valid & dispersion.le(disp_q33)
    beta_high = _rolling_beta(
        market.where(high_disp_day), returns.where(high_disp_day, axis=0), window, min_periods
    )
    beta_low = _rolling_beta(
        market.where(low_disp_day), returns.where(low_disp_day, axis=0), window, min_periods
    )
    return beta_high - beta_low


# --- Round 6: residual time-series structure (Theme R) -----------------

def _build_residual_variance_ratio_1_5(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Variance-ratio-test style statistic: Var(5-day overlapping
    cumulative residual return) / (5 * Var(1-day residual return)), both
    variances taken over the trailing 60-day window. VR>1 marks
    trending/positively-autocorrelated residual returns; VR<1 marks
    mean-reversion. direction +1: residual trendiness (VR>1) predicts
    continuation."""
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)
    residual_5d = residual.rolling(5, min_periods=5).sum()
    var_5d = residual_5d.rolling(window, min_periods=window).var()
    var_1d = residual.rolling(window, min_periods=window).var()
    return var_5d.div(5.0 * var_1d.where(var_1d > 0))


def _build_residual_sign_run(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Average run length of consecutive same-sign residual days within
    the trailing 60-day window: (count of valid days) / (1 + count of
    sign flips between consecutive valid days). direction +1: longer
    average sign persistence marks a trending residual, predicting
    continuation."""
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)
    min_periods = 30

    def run_length(window_vals: np.ndarray) -> float:
        valid = window_vals[~np.isnan(window_vals)]
        if len(valid) < min_periods:
            return np.nan
        signs = np.sign(valid)
        flips = int(np.sum(signs[1:] != signs[:-1]))
        return len(valid) / (flips + 1)

    return residual.rolling(window, min_periods=1).apply(run_length, raw=True)


# --- Round 6: residual path (Theme U) -----------------------------------

def _build_residual_drawdown(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Maximum drawdown (most negative trough-minus-running-peak value,
    <=0) of the cumulative residual-return PATH computed fresh within
    each trailing 60-day window (the cumulative path restarts at 0 at
    the start of every window, not from history's start -- a genuine
    rolling/windowed max drawdown, not a path-dependent all-history one).
    Requires a full, gap-free window (any NaN inside it makes that day
    NaN, since a windowed cumulative path with a gap is not well
    defined). direction -1: master's own spec (a different object from
    the already-closed own-drawdown family -- this is drawdown of the
    MARKET RESIDUAL path, not the member's own raw price path;
    resolved by the no-label dedup precheck, not assumed distinct a
    priori)."""
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)

    def max_drawdown(window_vals: np.ndarray) -> float:
        if np.isnan(window_vals).any():
            return np.nan
        cum = np.cumsum(window_vals)
        running_max = np.maximum.accumulate(cum)
        return float(np.min(cum - running_max))

    return residual.rolling(window, min_periods=window).apply(max_drawdown, raw=True)


# --- Round 6: residual distribution shape (Theme I) ---------------------

def _build_residual_tail_ratio(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Ratio of the trailing-window count of residual days beyond
    +2*sigma to the count beyond -2*sigma, sigma being that same
    trailing-60-day window's own (causal, evolving) residual std.
    direction +1: more positive-tail events than negative-tail events is
    a favorable skew, predicting relative strength."""
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)
    sigma = residual.rolling(window, min_periods=window).std()
    valid = residual.notna() & sigma.notna() & sigma.gt(0)
    pos_tail_day = (valid & residual.gt(2.0 * sigma)).astype(float)
    neg_tail_day = (valid & residual.lt(-2.0 * sigma)).astype(float)
    pos_count = pos_tail_day.rolling(window, min_periods=1).sum()
    neg_count = neg_tail_day.rolling(window, min_periods=1).sum()
    return pos_count.div(neg_count.where(neg_count > 0))


# --- Round 7: relative liquidity structure, second estimator (Theme H) -

def _build_roll_spread(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """Roll (1984) bid-ask spread estimator: 2*sqrt(-Cov(dP_t, dP_{t-1})),
    negative covariance estimates (i.e. no detectable bid-ask bounce)
    clipped to a spread of 0 rather than left undefined, master's own
    spec. dP = close.diff() (same adjustment basis as every other
    candidate's close). direction -1: a wider estimated spread means
    worse liquidity, predicting relative weakness. A different estimator
    from the already-tried (and dedup-dropped) corwin_schultz_spread
    (high/low range based, not close-to-close covariance based);
    resolved by the no-label dedup precheck like everything else in this
    module, not assumed distinct a priori."""
    dp = close.diff()
    dp_lag = dp.shift(1)
    mean_x = dp.rolling(window, min_periods=window).mean()
    mean_y = dp_lag.rolling(window, min_periods=window).mean()
    cov = dp.mul(dp_lag).rolling(window, min_periods=window).mean() - mean_x.mul(mean_y)
    return 2.0 * (-cov).clip(lower=0.0).pow(0.5)


# --- Round 7: self-devised (MY_ASSUMPTION), mechanism-first -------------
#
# MY_ASSUMPTION 1: a name's own gap (open vs prior close) getting "filled"
# (reversed) by the intraday session more often than the MARKET's own gaps
# get filled is read as a lack-of-conviction/follow-through signal (the
# same "confirmation predicts continuation" narrative already used
# successfully for volume_surge_relative_return and overnight_intraday_
# sign_consistency_relative_market, just applied to gap-repair completion
# instead of volume or sign agreement). Adjacent to the already-tested
# daily_rounds:gap_repair_completion_rate (an ABSOLUTE own-name level, no
# market benchmark); this candidate's market-relative framing is the same
# differentiator that made overnight_intraday_sign_consistency_relative_
# market acceptable despite its own adjacency to overnight_intraday_
# switch_rate -- resolved by the no-label dedup precheck, not assumed
# distinct a priori.

def _build_gap_fill_completion_relative_market(
    open_: pd.DataFrame, close: pd.DataFrame, window: int
) -> pd.DataFrame:
    """Own gap-fill completion rate minus the market's own gap-fill
    completion rate (each leg's own fixed14 all-complete equal-weight
    mean, same construction as overnight_intraday_beta_gap). A day's gap
    counts as "filled" if the intraday body move at least fully reverses
    the overnight gap. direction -1: relatively MORE gap-reversal than
    the market is read as weaker follow-through conviction, predicting
    relative weakness."""
    gap = open_.div(close.shift(1)).sub(1.0)
    body = close.div(open_).sub(1.0)
    gap_valid = gap.notna() & body.notna()
    filled_day = gap_valid & gap.ne(0) & (-np.sign(gap) * body).ge(gap.abs())
    own_rate = filled_day.astype(float).where(gap_valid).rolling(window, min_periods=window).mean()

    _gap_returns, market_gap = _market_return_from(gap)
    _body_returns, market_body = _market_return_from(body)
    market_valid = market_gap.notna() & market_body.notna()
    market_filled_day = market_valid & market_gap.ne(0) & (-np.sign(market_gap) * market_body).ge(market_gap.abs())
    market_rate = market_filled_day.astype(float).where(market_valid).rolling(window, min_periods=window).mean()
    return own_rate.sub(market_rate, axis=0)


# MY_ASSUMPTION 2: the day immediately AFTER a market-wide tail event (the
# market itself, not the member, had one of its own most extreme moves the
# prior day), a name's relative return is read as a "shock absorption /
# recovery" signal -- resilience predicts continuation, the same narrative
# already used for market_tail_relative_return and volume_surge_relative_
# return, but shifted to the day AFTER the event instead of the event day
# itself (neither of those two prior, dedup-dropped candidates looked at
# next-day dynamics). The tail-day classification for day t-1 only uses
# data through t-1 (fully causal); shifting that classification forward by
# one day to label day t introduces no leakage.

def _build_post_market_tail_relative_return(close: pd.DataFrame, window: int) -> pd.DataFrame:
    returns, market = _market_return(close)
    abs_market = market.abs()
    market_q80 = abs_market.rolling(window, min_periods=window).quantile(0.80)
    market_valid = abs_market.notna() & market_q80.notna()
    market_tail_day = market_valid & abs_market.ge(market_q80)
    post_tail_day = market_tail_day.shift(1, fill_value=False)
    relative_return = returns.sub(market, axis=0)
    return _rolling_conditional_mean(relative_return, post_tail_day, window, min_periods=3)


# MY_ASSUMPTION 3: same "day after an extreme, resilience predicts
# continuation" mechanism as MY_ASSUMPTION 2, but conditioned on the
# MEMBER'S OWN extreme residual day instead of the market's -- a different
# conditioning variable, the same distinction the campaign has already
# treated as legitimately separate candidates (e.g. beta_asymmetry vs
# high_low_vol_beta_gap vs quantile_beta_gap vs dispersion_conditional_
# beta_gap, all "conditional beta gap" on different regime variables).

def _build_post_own_tail_relative_return(close: pd.DataFrame, window: int) -> pd.DataFrame:
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)
    abs_residual = residual.abs()
    own_q80 = abs_residual.rolling(window, min_periods=window).quantile(0.80)
    own_valid = abs_residual.notna() & own_q80.notna()
    own_tail_day = own_valid & abs_residual.ge(own_q80)
    post_own_tail_day = own_tail_day.shift(1, fill_value=False)
    return _rolling_conditional_mean(residual, post_own_tail_day, window, min_periods=3)


# --- Round 7, 3rd candidate: rotation-leader co-movement (master's own
# formula) ---------------------------------------------------------------

def _group_returns_df(returns: pd.DataFrame) -> pd.DataFrame:
    group_returns = {}
    for gid, members in _ECONOMIC_GROUPS.items():
        sub = returns[list(members)]
        all_present = sub.notna().all(axis=1)
        group_returns[gid] = sub.mean(axis=1).where(all_present)
    return pd.DataFrame(group_returns)


def _leader_group_ids(group_returns: pd.DataFrame, window: int) -> tuple[pd.Series, pd.Series]:
    """Per-day leader (rank-1) and second (rank-2) economic-group id, by
    trailing `window`-day mean group return (causal). Only defined on
    days all 8 groups are valid; NaN (object) elsewhere."""
    perf = group_returns.rolling(window, min_periods=window).mean()
    all_valid = perf.notna().all(axis=1)
    leader_id = pd.Series(index=perf.index, dtype=object)
    second_id = pd.Series(index=perf.index, dtype=object)
    valid_idx = perf.index[all_valid]
    sub = perf.loc[valid_idx]
    if len(sub):
        lead = sub.idxmax(axis=1)
        row_max = sub.max(axis=1)
        is_leader = sub.eq(row_max, axis=0)
        masked = sub.where(~is_leader, -np.inf)
        sec = masked.idxmax(axis=1)
        leader_id.loc[valid_idx] = lead
        second_id.loc[valid_idx] = sec
    return leader_id, second_id


def _build_beta_to_leader_group(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """beta(r_i, r_leader_group) over the trailing `window`-day window,
    where leader_group is the economic group (of the 8) with the highest
    trailing-`window`-day mean group return AS OF THAT DAY -- the SAME
    window's own last day, not re-selected day-by-day within the window
    (the group identity is fixed for the whole regression window, only
    its historical returns over that window are used). For a member
    whose OWN group is the leader, the SECOND-highest group is used
    instead (a name can't lead itself). min_periods=15, master's own
    spec. direction +1: co-movement with the current rotation leader is
    read as participation in the leadership rotation, expected to
    continue.

    Implementation: precompute member-vs-group beta for EVERY (member,
    group) pair using the standard fixed-x rolling beta (each of these 8
    beta series already correctly uses that one group's own trailing-
    window history at every day), then select, per member per day, the
    one column matching that day's effective leader id -- this reproduces
    "assume group L was the x variable for the whole window ending at t"
    without needing to reassemble a different window slice per day."""
    returns, _market = _market_return(close)
    group_returns = _group_returns_df(returns)
    leader_id, second_id = _leader_group_ids(group_returns, window)
    min_periods = 15

    beta_vs_group = {
        gid: _rolling_beta(group_returns[gid], returns, window, min_periods)
        for gid in _ECONOMIC_GROUPS
    }
    member_to_group = {m: gid for gid, members in _ECONOMIC_GROUPS.items() for m in members}
    group_labels = list(_ECONOMIC_GROUPS)
    label_to_idx = {g: i for i, g in enumerate(group_labels)}

    n = len(returns.index)
    result = pd.DataFrame(index=returns.index, columns=returns.columns, dtype=float)
    for member in returns.columns:
        own_group = member_to_group[member]
        effective_leader = leader_id.where(leader_id.ne(own_group), second_id)
        stack = np.column_stack([beta_vs_group[g][member].to_numpy() for g in group_labels])
        col_idx = effective_leader.map(label_to_idx)
        valid = col_idx.notna().to_numpy()
        col_idx_arr = col_idx.fillna(0).astype(int).to_numpy()
        selected = stack[np.arange(n), col_idx_arr]
        result[member] = np.where(valid, selected, np.nan)
    return result


# --- Round 8: return-horizon ratios (master's own formulas) -----------

def _horizon_5d_returns(close: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """5-day overlapping compounded returns (close.pct_change(5)) for
    every member, plus their fixed14 all-complete equal-weight mean
    (same aggregation convention as _market_return's 1-day market leg,
    just built from each member's own 5-day return instead of its 1-day
    return)."""
    returns_5d = close.pct_change(5, fill_method=None)
    all_valid = returns_5d.notna().all(axis=1)
    market_5d = returns_5d.mean(axis=1).where(all_valid)
    return returns_5d, market_5d


def _build_corr_horizon_ratio(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """corr(5-day overlapping r_i, r_m) / corr(1-day r_i, r_m), both over
    the trailing 60-day window (dense). A ratio below 1 (high-frequency
    correlation lower than low-frequency correlation) is an Epps-effect-
    style signature of lagged/staggered co-movement -- a different object
    from minute_lead_lag_corr/lead_to_market (those measure LEAD-LAG
    DIRECTION at a fixed lag; this measures the AGGREGATION-HORIZON level
    at which co-movement becomes visible, direction-agnostic); resolved
    by the no-label dedup precheck like everything else in this module,
    not assumed distinct a priori. direction -1: master's own spec."""
    returns_1d, market_1d = _market_return(close)
    returns_5d, market_5d = _horizon_5d_returns(close)
    corr_1d = _rolling_corr_scalar(market_1d, returns_1d, window)
    corr_5d = _rolling_corr_scalar(market_5d, returns_5d, window)
    return corr_5d.div(corr_1d.where(corr_1d.abs() > 0))


def _build_beta_horizon_ratio(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """beta(5-day overlapping r_i, r_m) / beta(1-day r_i, r_m), both over
    the trailing 60-day window (dense). direction +1: master's own spec
    (an asset whose true exposure is under-measured at the 1-day horizon
    relative to the 5-day horizon is expected to keep catching up)."""
    returns_1d, market_1d = _market_return(close)
    returns_5d, market_5d = _horizon_5d_returns(close)
    beta_1d = _rolling_beta(market_1d, returns_1d, window, window)
    beta_5d = _rolling_beta(market_5d, returns_5d, window, window)
    return beta_5d.div(beta_1d.where(beta_1d.abs() > 0))


# --- Round 8: calendar seasonality (master's own formula) ---------------
#
# Originally specified as "last 3 TRADING days of the month"
# (month_end_relative_return), but that classification is inherently
# forward-dependent: whether a day within the still-open current month is
# one of its last 3 trading days cannot be known until the month has
# actually ended (i.e. until the following month's first trading day is
# observed), which fails leakage_checks's truncation-invariance test for
# any cut falling mid-month (confirmed, not just suspected -- see
# test_etf_group_claude_rounds.py's history around 2026-09-23 round 8).
# Master approved (2026-09-23) replacing it with a CALENDAR-DAY proxy:
# day >= days_in_month - 4 (the last 5 calendar days of the month), using
# only each date's own intrinsic calendar properties -- no dependency on
# which other dates happen to be present in whatever panel slice is being
# evaluated, hence provably leak-free under any truncation.

def _month_end_calendar_day_mask(index: pd.DatetimeIndex) -> pd.Series:
    """True on the last 5 calendar days of each month (day-of-month >=
    days-in-month - 4), an approximation of "last 3 trading days" that
    uses only each date's own intrinsic properties."""
    return pd.Series(index.day >= (index.days_in_month - 4), index=index)


def _build_month_end_calendar_relative_return(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """mean(r_i - r_m) on the last-5-calendar-days-of-the-month subset
    (approximating "last 3 trading days", master's own spec) of the
    trailing 120-day window. direction +1: master's own spec (month-end
    flow seasonality persistence). Coverage is expected to run thin at
    this sample size; reported, not padded -- a COVERAGE_INSUFFICIENT
    read (n<360 at the evaluation stage) is expected to be a real
    possibility for this candidate, not a code defect."""
    returns, market = _market_return(close)
    month_end_day = _month_end_calendar_day_mask(close.index)
    relative_return = returns.sub(market, axis=0)
    return _rolling_conditional_mean(relative_return, month_end_day, window, min_periods=8)


# --- Round 8, self-devised (MY_ASSUMPTION), mechanism-first -------------
#
# MY_ASSUMPTION 1: a member's cross-sectional RANK among the 14 (by raw
# daily return) persisting high over time is read as relative-strength
# momentum that is ROBUST to overall market/volatility-level differences
# across members, unlike a raw-value momentum statistic (Batch B's
# momentum_120_skip5/momentum_250_skip20). Adjacent to the already-tested
# daily_rounds:activity_rank_dynamics, but that family is built from
# trading ACTIVITY (volume/amount) rank, not RETURN rank -- a different
# underlying variable, resolved by the no-label dedup precheck, not
# assumed distinct a priori.

def _build_rank_persistence(close: pd.DataFrame, window: int) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    daily_rank = returns.rank(axis=1)
    return daily_rank.rolling(window, min_periods=window).mean()


# MY_ASSUMPTION 2: the market-residual return distribution's volatility
# asymmetry between the residual's own up-days and down-days (upside
# semi-deviation minus downside semi-deviation) is read the same way as
# residual_skew_gap's up/down asymmetry (a different moment -- 2nd, not
# 3rd -- of the same up/down-day conditional split; the campaign has
# already accepted variance-ratio/kurtosis/skew-gap as distinct moment-
# family candidates on the same residual series, not merged a priori).

def _build_residual_semideviation_asymmetry(close: pd.DataFrame, window: int) -> pd.DataFrame:
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)
    min_periods = _conditional_min_periods(window)
    up_vol = residual.where(residual.gt(0)).rolling(window, min_periods=min_periods).std()
    down_vol = residual.where(residual.lt(0)).rolling(window, min_periods=min_periods).std()
    return up_vol.sub(down_vol)


# MY_ASSUMPTION 3: a day-of-week seasonality pattern in relative returns
# (the classic "weekend effect" literature: Monday relative weakness,
# Friday relative strength) persisting is read the same "seasonality
# persistence" way as master's own month_end_relative_return -- but
# UNLIKE month-end classification, a date's weekday name is an intrinsic,
# immediately-known property of the date itself (no forward information
# about whether more trading days remain in any period is ever needed),
# so this candidate has no analog of month_end_relative_return's
# leakage issue.

def _build_weekday_relative_return_pattern(close: pd.DataFrame, window: int) -> pd.DataFrame:
    returns, market = _market_return(close)
    relative_return = returns.sub(market, axis=0)
    weekday = close.index.dayofweek  # Monday=0 ... Friday=4
    is_friday = pd.Series(weekday == 4, index=close.index)
    is_monday = pd.Series(weekday == 0, index=close.index)
    # A single weekday is ~1/5 of trading days (~12 of 60), well below
    # _conditional_min_periods(60)=15 (calibrated for ~50% up/down-day
    # subsets elsewhere in this module); use the same floor already used
    # for other ~20%-scale subsets (market_tail_relative_return's tail
    # days, tail_coexceedance_asymmetry's tail days).
    min_periods = 3
    friday_mean = _rolling_conditional_mean(relative_return, is_friday, window, min_periods)
    monday_mean = _rolling_conditional_mean(relative_return, is_monday, window, min_periods)
    return friday_mean.sub(monday_mean)


# --- Round 9 (self-devised, MY_ASSUMPTION, mechanism written before
# definition). Master's angle for round 9/10: "post-event TIME STRUCTURE
# of relative returns" -- specifically the days t+2..t+5 window, distinct
# from round 7's post_market_tail_relative_return/post_own_tail_relative_
# return, which only looked at the immediate next day (t+1) and were both
# NOT_SUPPORTED_THIS_SCREEN. The mechanism claim here is not "the same
# next-day effect, just measured later" -- it is that day+1 captures the
# FAST/algorithmic reaction (already tested, not found), while capital
# reallocation into/out of ETFs specifically (thinner liquidity/attention
# than index futures or large-cap single names) takes several days to
# fully manifest, so the days-2-to-5 window is a genuinely different
# timing hypothesis, not a re-run of the day+1 test with a new name. ------

def _build_post_market_tail_delayed_relative_return(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """MY_ASSUMPTION 1: "slow flow" continuation, days t+2..t+5 after a
    market-wide tail day (same tail-day threshold construction as round 7's
    post_market_tail_relative_return -- top quintile trailing |r_m|).
    direction +1 (continuation/resilience narrative, same as round 7's
    version, now applied to the delayed window instead of day+1)."""
    returns, market = _market_return(close)
    abs_market = market.abs()
    market_q80 = abs_market.rolling(window, min_periods=window).quantile(0.80)
    market_valid = abs_market.notna() & market_q80.notna()
    market_tail_day = market_valid & abs_market.ge(market_q80)
    delayed_window = (
        market_tail_day.shift(2, fill_value=False)
        | market_tail_day.shift(3, fill_value=False)
        | market_tail_day.shift(4, fill_value=False)
        | market_tail_day.shift(5, fill_value=False)
    )
    relative_return = returns.sub(market, axis=0)
    return _rolling_conditional_mean(relative_return, delayed_window, window, min_periods=3)


def _build_post_own_tail_delayed_relative_return(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """MY_ASSUMPTION 2: delayed REVERSAL, days t+2..t+5 after a member's OWN
    idiosyncratic tail day (same own-residual threshold construction as
    round 7's post_own_tail_relative_return -- top quintile trailing
    |residual|). Mechanism distinct from candidate 1: an idiosyncratic
    single-name residual shock is more likely a transient premium/discount
    dislocation (liquidity-driven overshoot, temporary creation/redemption
    imbalance) that the ETF arbitrage mechanism corrects over the following
    days, unlike a market-wide move which reflects genuine repricing.
    direction -1 (reversal, opposite of candidate 1's continuation)."""
    returns, market = _market_return(close)
    residual = returns.sub(market, axis=0)
    abs_residual = residual.abs()
    own_q80 = abs_residual.rolling(window, min_periods=window).quantile(0.80)
    own_valid = abs_residual.notna() & own_q80.notna()
    own_tail_day = own_valid & abs_residual.ge(own_q80)
    delayed_window = (
        own_tail_day.shift(2, fill_value=False)
        | own_tail_day.shift(3, fill_value=False)
        | own_tail_day.shift(4, fill_value=False)
        | own_tail_day.shift(5, fill_value=False)
    )
    return _rolling_conditional_mean(residual, delayed_window, window, min_periods=3)


def _build_post_dispersion_delayed_relative_return(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """MY_ASSUMPTION 3: delayed REVERSAL, days t+2..t+5 after a high
    8-GROUP cross-sectional dispersion day (reuses _group_dispersion, the
    same USER dispersion-framework measure as round 6's dispersion_
    conditional_relative_return/_beta_gap -- top quintile trailing
    dispersion, q80 for consistency with this round's own other two
    candidates; round 6 used tercile q67 for its SAME-day version).
    Mechanism distinct from candidates 1/2: the conditioning event here is
    cross-sectional DIFFERENTIATION (a rotation/regime-split event across
    the 8 economic groups), not a single benchmark return's own magnitude.
    High-dispersion days often reflect a temporary, flow-driven
    differentiation (thematic rotation overreaction, concentrated
    creation/redemption in a subset of groups) rather than fully
    efficient repricing; as dispersion normalizes over the following days,
    the pool's average relative-return level specifically in this delayed
    post-dispersion regime should compress back toward the market mean --
    a genuinely different narrative from round 6's SAME-day continuation
    hypothesis (direction +1, dropped at dedup before ever being IC-tested,
    0.7389 vs vol_scaled_momentum_60) and from this round's candidates 1/2
    (single-benchmark tail event, not cross-sectional dispersion).
    direction -1 (reversion)."""
    returns, market = _market_return(close)
    dispersion = _group_dispersion(returns)
    disp_q80 = dispersion.rolling(window, min_periods=window).quantile(0.80)
    valid = dispersion.notna() & disp_q80.notna()
    high_disp_day = valid & dispersion.ge(disp_q80)
    delayed_window = (
        high_disp_day.shift(2, fill_value=False)
        | high_disp_day.shift(3, fill_value=False)
        | high_disp_day.shift(4, fill_value=False)
        | high_disp_day.shift(5, fill_value=False)
    )
    relative_return = returns.sub(market, axis=0)
    return _rolling_conditional_mean(relative_return, delayed_window, window, min_periods=3)


# --- Round 10 (self-devised, MY_ASSUMPTION, mechanism written before
# definition; master gave no formula or angle this round, only that both
# rounds 9 and 10 are self-devised). Before drafting these, checked the
# freshest family snapshot's own claude_rounds rows AND the cross-engine
# daily_rounds/minute rows in the same families.csv (both engines share one
# registry) for the "easy" adjacent territories: per-member amount/turnover
# confirmation and asymmetry (daily_rounds:amount_return_asymmetry,
# amount_shock_body_efficiency, amount_conditional_body_asymmetry,
# market_residual_amount_beta, ~15 more amount_* rows, plus ~15 more
# minute:minute_amount_*/minute_turnover_return_corr rows -- this whole
# vein is extensively mined already, several explicitly DO_NOT_REPEAT);
# per-member residual serial-dependence (daily_rounds:market_residual_
# sign_persistence, _turning_rate, _path_efficiency -- literally a Kaufman
# Efficiency Ratio on the residual, which was this session's first idea for
# a 3rd candidate before this check ruled it out); and Kaufman Efficiency
# Ratio itself (daily_rounds:market_residual_path_efficiency, exact same
# formula). All of these are either already registered (INCOMPLETE_
# EVIDENCE, not closed, but "don't repeat without new information") or a
# near-exact match to something registered. The two candidates below work
# at the ECONOMIC-GROUP level instead (8 groups, not 14 members), a
# genuinely unexplored axis under both claude_rounds and daily_rounds
# (no group_momentum/group_rank/group_autocorr/group_leader rows in either
# engine's family list) -- ONLY 2 registered this round, not 3: a
# well-differentiated 3rd construction on this same group axis (e.g. a
# "does today's group leader rank reverse" companion to candidate 2) would
# be either a near-mirror-image of candidate 2 (same underlying group-rank
# statistic, opposite direction, high expected anti-correlation) or would
# have to fall back into the saturated per-member vein above; reported
# honestly rather than forcing a weak 3rd. -----------------------------

def _build_group_return_autocorrelation_relative(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """MY_ASSUMPTION 1: each member's factor value is its OWN ECONOMIC
    GROUP's trailing lag-1 return autocorrelation (group_returns_df, the
    same 8-group equal-weight all-members-valid construction round 7's
    beta_to_leader_group and round 6's dispersion candidates use), a
    regime indicator -- is this member's sector currently in a trending
    (positive autocorrelation) or choppy/mean-reverting (negative
    autocorrelation) state. Different statistic and lag structure from
    tsmom_consistency (20-day BLOCK sign-consistency, already registered,
    DO_NOT_REPEAT) and from market_residual_sign_persistence/_turning_rate
    (per-MEMBER residual, not per-GROUP raw return). For the 6 single-
    member economic groups this reduces to that member's own raw-return
    lag-1 autocorrelation (no group-aggregation effect for those 6 --
    disclosed in config notes, not hidden); only the 2 multi-member groups
    get genuine group-level aggregation. direction +1: membership in a
    currently trending group predicts relative continuation."""
    returns, _market = _market_return(close)
    group_returns = _group_returns_df(returns)
    lag1_autocorr = group_returns.rolling(window, min_periods=window).corr(group_returns.shift(1))
    member_to_group = {m: gid for gid, members in _ECONOMIC_GROUPS.items() for m in members}
    return pd.DataFrame(
        {m: lag1_autocorr[gid] for m, gid in member_to_group.items()}
    )[close.columns]


def _build_group_momentum_rank_relative(close: pd.DataFrame, window: int) -> pd.DataFrame:
    """MY_ASSUMPTION 2: each member's factor value is its OWN ECONOMIC
    GROUP's trailing-window mean-return RANK among all 8 groups (1=worst
    .. 8=best), a group-level cross-sectional momentum measure -- distinct
    from round 7's beta_to_leader_group (a regression BETA of the member's
    OWN return against only the single #1-ranked group's return series,
    dropped at dedup 0.7335 before ever being IC-tested) in that this uses
    the member's OWN group's rank position among all 8, not a beta to
    whichever OTHER group currently leads. Also distinct from member-level
    momentum_120_skip5/momentum_250_skip20 (individual price momentum
    level, not a group-membership rank). direction +1: belonging to a
    currently higher-ranked (leading) group predicts continuation, the
    same sign convention this campaign already uses for its other
    momentum-family candidates."""
    returns, _market = _market_return(close)
    group_returns = _group_returns_df(returns)
    group_momentum = group_returns.rolling(window, min_periods=window).mean()
    group_rank = group_momentum.rank(axis=1)
    member_to_group = {m: gid for gid, members in _ECONOMIC_GROUPS.items() for m in members}
    return pd.DataFrame(
        {m: group_rank[gid] for m, gid in member_to_group.items()}
    )[close.columns]


# --- Round 11 (master's own formulas: macro exposure family) -----------

def _align_macro_series(series: pd.Series, calendar: pd.DatetimeIndex, foreign: bool) -> pd.Series:
    """Align one macro variable (its own native date index) onto the
    A-share trading calendar in two explicit stages: (1) forward-fill --
    for each A-share date d, the latest native value with native_date <=
    d (same-day-inclusive; never uses a value dated after d); (2) for
    FOREIGN variables only, an additional one-A-share-SESSION .shift(1)
    on the now A-share-indexed result of stage 1 (not on the native date
    axis, and not a fixed calendar-day count).

    This is deliberately CONSERVATIVE (errs toward more lag, never less)
    for a foreign print whose native date falls on a day the A-share
    calendar has no session for (e.g. a weekend USDCNH print): stage 1
    already discards/ffills through non-A-share native dates before stage
    2's shift ever runs, so such a print only takes effect from the A-
    share session AFTER the one that first ffills it in -- i.e. TWO A-
    share sessions after the weekend it was printed on (e.g. a Saturday
    print becomes visible from Tuesday, not Monday), not the minimum
    "next calendar day" a literal reading of master's rule ("外国数据日期t
    只能在A股t+1起使用") might suggest for that edge case. Never a leak in
    either direction -- only more conservative than the strict minimum
    lag when native and A-share calendars diverge. Domestic futures
    (foreign=False) get no extra shift -- same-day close is usable
    (master's rule); their native calendar has no A-share-absent trading
    days in the first place, so this edge case does not apply to them."""
    combined = series.index.union(calendar)
    filled = series.reindex(combined).ffill()
    aligned = filled.reindex(calendar)
    if foreign:
        aligned = aligned.shift(1)
    return aligned


def _macro_daily_changes(macro: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """Each of the 5 macro variables, aligned onto `calendar` (the A-share
    trading calendar, i.e. close.index) with the correct domestic-same-
    day vs foreign-next-day lag, then differenced: yield LEVELS (real_
    rate, nominal_rate) use a simple level diff (standard convention for
    rates, not a percent change); price-level variables (usdcnh, copper,
    bond_future) use pct_change. Column order is _MACRO_COLUMNS
    throughout (the regressor order for the multivariate candidates)."""
    aligned = {
        col: _align_macro_series(macro[col], calendar, foreign=col in _MACRO_FOREIGN_COLUMNS)
        for col in _MACRO_COLUMNS
    }
    changes = {}
    for col in _MACRO_COLUMNS:
        if col in ("real_rate", "nominal_rate"):
            changes[col] = aligned[col].diff()
        else:
            changes[col] = aligned[col].pct_change(fill_method=None)
    return pd.DataFrame(changes, index=calendar)[list(_MACRO_COLUMNS)]


def _rolling_multi_ols(X: pd.DataFrame, y: pd.DataFrame, window: int, min_periods: int) -> tuple[dict, pd.DataFrame]:
    """Rolling multivariate OLS (with intercept, via centered X/y) of each
    member's own return on the 5 macro regressors in X, one explicit
    np.linalg.lstsq solve per (day, member) -- not a vectorized rolling-
    moments closed form. Chosen for auditability (etf-reviewer can read a
    literal lstsq call) over raw speed; ~ (n_days x 14) small (window x 5)
    solves, negligible cost for this panel's size.

    Returns (betas, r2): betas is {member: DataFrame(n_days, 5)} of that
    member's own rolling regression coefficients (columns = X's own
    columns, no intercept column); r2 is DataFrame(n_days, 14) of the
    rolling R² (fraction of that member's own return variance explained
    by the 5 macro regressors over the same window)."""
    idx = y.index
    cols = list(X.columns)
    members = list(y.columns)
    k = len(cols)
    x_vals = X[cols].to_numpy()
    y_vals = y[members].to_numpy()
    n = len(idx)
    betas_arr = {m: np.full((n, k), np.nan) for m in members}
    r2_arr = np.full((n, len(members)), np.nan)
    for t in range(window - 1, n):
        start = t - window + 1
        xw = x_vals[start:t + 1]
        if np.isnan(xw).any():
            continue
        x_centered = xw - xw.mean(axis=0, keepdims=True)
        for mi in range(len(members)):
            yw = y_vals[start:t + 1, mi]
            if np.isnan(yw).any() or len(yw) < min_periods:
                continue
            y_centered = yw - yw.mean()
            sst = float(np.sum(y_centered ** 2))
            if sst <= 0:
                continue
            beta, _residuals, _rank, _sv = np.linalg.lstsq(x_centered, y_centered, rcond=None)
            betas_arr[members[mi]][t] = beta
            fitted = x_centered @ beta
            ssr = float(np.sum((y_centered - fitted) ** 2))
            r2_arr[t, mi] = 1.0 - ssr / sst
    betas = {m: pd.DataFrame(betas_arr[m], index=idx, columns=cols) for m in members}
    r2 = pd.DataFrame(r2_arr, index=idx, columns=members)
    return betas, r2


def _build_real_rate_beta(close: pd.DataFrame, macro: pd.DataFrame, window: int) -> pd.DataFrame:
    """60-day beta of each member's own return on the daily CHANGE in the
    US 10y real (TIPS) yield, foreign-next-day-lagged. direction -1
    (master): more negatively sensitive to real rates predicts relative
    strength (a rate-sensitivity premium narrative)."""
    returns = close.pct_change(fill_method=None)
    changes = _macro_daily_changes(macro, close.index)
    return _rolling_beta(changes["real_rate"], returns, window, window)


def _build_usd_beta(close: pd.DataFrame, macro: pd.DataFrame, window: int) -> pd.DataFrame:
    """60-day beta of each member's own return on USDCNH's own daily
    return, foreign-next-day-lagged. direction -1 (master)."""
    returns = close.pct_change(fill_method=None)
    changes = _macro_daily_changes(macro, close.index)
    return _rolling_beta(changes["usdcnh"], returns, window, window)


def _build_commodity_beta(close: pd.DataFrame, macro: pd.DataFrame, window: int) -> pd.DataFrame:
    """60-day beta of each member's own return on Shanghai copper
    futures' own daily return, same-day (domestic, no extra lag).
    direction +1 (master)."""
    returns = close.pct_change(fill_method=None)
    changes = _macro_daily_changes(macro, close.index)
    return _rolling_beta(changes["copper"], returns, window, window)


def _build_macro_r2(close: pd.DataFrame, macro: pd.DataFrame, window: int) -> pd.DataFrame:
    """60-day R² of each member's own return regressed on all 5 macro
    changes jointly (real rate, nominal rate, USDCNH, copper, bond
    future). direction -1 (master): low macro explanatory power = the
    member's return is idiosyncratically (not macro-)driven."""
    returns = close.pct_change(fill_method=None)
    changes = _macro_daily_changes(macro, close.index)
    _betas, r2 = _rolling_multi_ols(changes, returns, window, window)
    return r2


def _build_macro_expected_return(close: pd.DataFrame, macro: pd.DataFrame, window: int) -> pd.DataFrame:
    """Two legs, master's own spec: a 60-day rolling multivariate OLS beta
    (each member's own return on the 5 macro changes jointly) times the
    SAME 5 macro variables' own 20-day cumulative change, summed across
    the 5 regressors -- "macro-driven expected return continues" (same
    two-legs-registered-at-the-longer-one convention as amount_share_
    change_60/corr_stability_20_60_60: the 20-day cumulative-change leg is
    a second, internally fixed window, not the registered `window`
    argument). direction +1 (master)."""
    del window  # this candidate's own two legs are fixed at 60 (beta) and 20 (cumulative change)
    returns = close.pct_change(fill_method=None)
    changes = _macro_daily_changes(macro, close.index)
    betas, _r2 = _rolling_multi_ols(changes, returns, 60, 60)
    cum_change_20d = changes.rolling(20, min_periods=20).sum()
    score = pd.DataFrame(index=close.index, columns=close.columns, dtype=float)
    for member in close.columns:
        contrib = betas[member][list(_MACRO_COLUMNS)] * cum_change_20d
        any_missing = contrib.isna().any(axis=1)
        score[member] = contrib.sum(axis=1).where(~any_missing)
    return score


def build_atoms(panels: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    _validate_config(cfg)
    names = tuple(cfg["mechanisms"])
    p = _panels(panels, names)
    result: dict[str, pd.DataFrame] = {}
    for name, definition in cfg["mechanisms"].items():
        direction, window = definition["direction"], definition["window"]
        if name == "beta_asymmetry":
            raw = _build_beta_asymmetry(p["close"], window)
        elif name == "corr_stability_20_60":
            raw = _build_corr_stability_20_60(p["close"], window)
        elif name == "lead_to_market":
            raw = _build_lead_to_market(p["close"], window)
        elif name == "overnight_intraday_beta_gap":
            raw = _build_overnight_intraday_beta_gap(p["open"], p["close"], window)
        elif name == "momentum_120_skip5":
            raw = _build_momentum_skip(p["close"], lookback=120, skip=5)
        elif name == "momentum_250_skip20":
            raw = _build_momentum_skip(p["close"], lookback=250, skip=20)
        elif name == "vol_scaled_momentum":
            raw = _build_vol_scaled_momentum(p["close"], window)
        elif name == "tsmom_consistency":
            raw = _build_tsmom_consistency(p["close"], window)
        elif name == "vol_of_vol":
            raw = _build_vol_of_vol(p["close"], window)
        elif name == "illiquidity_trend":
            raw = _build_illiquidity_trend(p["close"], p["amount"], window)
        elif name == "downside_correlation":
            raw = _build_downside_correlation(p["close"], window)
        elif name == "beta_variability":
            raw = _build_beta_variability(p["close"], window)
        elif name == "market_tail_relative_return":
            raw = _build_market_tail_relative_return(p["close"], window)
        elif name == "capture_asymmetry":
            raw = _build_capture_asymmetry(p["close"], window)
        elif name == "corr_level":
            raw = _build_corr_level(p["close"], window)
        elif name == "residual_vol_term_structure_20_60":
            raw = _build_residual_vol_term_structure(p["close"], window)
        elif name == "high_low_vol_beta_gap":
            raw = _build_high_low_vol_beta_gap(p["close"], window)
        elif name == "market_jump_response":
            raw = _build_market_jump_response(p["close"], window)
        elif name == "lag1_beta_to_market":
            raw = _build_lag1_beta_to_market(p["close"], window)
        elif name == "residual_skew_gap":
            raw = _build_residual_skew_gap(p["close"], window)
        elif name == "residual_market_vol_corr":
            raw = _build_residual_market_vol_corr(p["close"], window)
        elif name == "cokurtosis":
            raw = _build_cokurtosis(p["close"], window)
        elif name == "downside_coskewness":
            raw = _build_downside_coskewness(p["close"], window)
        elif name == "avg_peer_residual_corr":
            raw = _build_avg_peer_residual_corr(p["close"], window)
        elif name == "peer_corr_network_change":
            raw = _build_peer_corr_network_change(p["close"], window)
        elif name == "peer_corr_dispersion":
            raw = _build_peer_corr_dispersion(p["close"], window)
        elif name == "amount_beta_to_market_amount":
            raw = _build_amount_beta_to_market_amount(p["close"], p["amount"], window)
        elif name == "volume_surge_relative_return":
            raw = _build_volume_surge_relative_return(p["close"], p["amount"], window)
        elif name == "amount_share_change":
            raw = _build_amount_share_change(p["close"], p["amount"], window)
        elif name == "overnight_momentum_relative_market":
            raw = _build_overnight_momentum_relative_market(p["open"], p["close"], window)
        elif name == "overnight_intraday_sign_consistency_relative_market":
            raw = _build_overnight_intraday_sign_consistency_relative_market(p["open"], p["close"], window)
        elif name == "corr_dispersion_vs_anchors":
            raw = _build_corr_dispersion_vs_anchors(p["close"], window)
        elif name == "corr_level_to_nearest_anchor":
            raw = _build_corr_level_to_nearest_anchor(p["close"], window)
        elif name == "corr_nearest_anchor_change":
            raw = _build_corr_nearest_anchor_change(p["close"], window)
        elif name == "quantile_beta_gap":
            raw = _build_quantile_beta_gap(p["close"], window)
        elif name == "tail_coexceedance_asymmetry":
            raw = _build_tail_coexceedance_asymmetry(p["close"], window)
        elif name == "intraday_realized_corr":
            raw = _build_intraday_realized_corr(p["close"], p["minute"]["close"], window)
        elif name == "intraday_realized_beta":
            raw = _build_intraday_realized_beta(p["close"], p["minute"]["close"], window)
        elif name == "minute_lead_lag_corr":
            raw = _build_minute_lead_lag_corr(p["close"], p["minute"]["close"], window)
        elif name == "corwin_schultz_spread":
            raw = _build_corwin_schultz_spread(p["high"], p["low"], window)
        elif name == "residual_kurtosis":
            raw = _build_residual_kurtosis(p["close"], window)
        elif name == "dispersion_conditional_relative_return":
            raw = _build_dispersion_conditional_relative_return(p["close"], window)
        elif name == "dispersion_conditional_beta_gap":
            raw = _build_dispersion_conditional_beta_gap(p["close"], window)
        elif name == "residual_variance_ratio_1_5":
            raw = _build_residual_variance_ratio_1_5(p["close"], window)
        elif name == "residual_sign_run":
            raw = _build_residual_sign_run(p["close"], window)
        elif name == "residual_drawdown":
            raw = _build_residual_drawdown(p["close"], window)
        elif name == "residual_tail_ratio":
            raw = _build_residual_tail_ratio(p["close"], window)
        elif name == "roll_spread":
            raw = _build_roll_spread(p["close"], window)
        elif name == "gap_fill_completion_relative_market":
            raw = _build_gap_fill_completion_relative_market(p["open"], p["close"], window)
        elif name == "post_market_tail_relative_return":
            raw = _build_post_market_tail_relative_return(p["close"], window)
        elif name == "post_own_tail_relative_return":
            raw = _build_post_own_tail_relative_return(p["close"], window)
        elif name == "beta_to_leader_group":
            raw = _build_beta_to_leader_group(p["close"], window)
        elif name == "corr_horizon_ratio":
            raw = _build_corr_horizon_ratio(p["close"], window)
        elif name == "beta_horizon_ratio":
            raw = _build_beta_horizon_ratio(p["close"], window)
        elif name == "month_end_calendar_relative_return":
            raw = _build_month_end_calendar_relative_return(p["close"], window)
        elif name == "rank_persistence":
            raw = _build_rank_persistence(p["close"], window)
        elif name == "residual_semideviation_asymmetry":
            raw = _build_residual_semideviation_asymmetry(p["close"], window)
        elif name == "weekday_relative_return_pattern":
            raw = _build_weekday_relative_return_pattern(p["close"], window)
        elif name == "post_market_tail_delayed_relative_return":
            raw = _build_post_market_tail_delayed_relative_return(p["close"], window)
        elif name == "post_own_tail_delayed_relative_return":
            raw = _build_post_own_tail_delayed_relative_return(p["close"], window)
        elif name == "post_dispersion_delayed_relative_return":
            raw = _build_post_dispersion_delayed_relative_return(p["close"], window)
        elif name == "group_return_autocorrelation_relative":
            raw = _build_group_return_autocorrelation_relative(p["close"], window)
        elif name == "group_momentum_rank_relative":
            raw = _build_group_momentum_rank_relative(p["close"], window)
        elif name == "macro_expected_return_60_20":
            raw = _build_macro_expected_return(p["close"], p["macro"], window)
        elif name == "real_rate_beta":
            raw = _build_real_rate_beta(p["close"], p["macro"], window)
        elif name == "usd_beta":
            raw = _build_usd_beta(p["close"], p["macro"], window)
        elif name == "commodity_beta":
            raw = _build_commodity_beta(p["close"], p["macro"], window)
        elif name == "macro_r2":
            raw = _build_macro_r2(p["close"], p["macro"], window)
        else:
            raise ValueError(f"unhandled claude_rounds mechanism: {name}")
        result[f"{name}_{window}"] = (raw * direction).replace([np.inf, -np.inf], np.nan)
    return result


def leakage_checks(panels: dict[str, pd.DataFrame], cfg: dict, cut: str | pd.Timestamp) -> dict[str, bool]:
    """Dynamic prefix and future-perturbation invariance for every atom.

    `panels['minute']`, when present, is a nested dict of 5m DataFrames
    (not itself a DataFrame) and is handled separately: `cut` is a daily
    date, so the minute truncation/perturbation boundary is that date's
    end-of-day timestamp, keeping every 5m bar on the cut date itself in
    the "seen" (prefix) side.
    """
    minute_cut = pd.Timestamp(cut) + pd.Timedelta(hours=23, minutes=59, seconds=59)

    def _truncate(v):
        if isinstance(v, dict):
            return {k2: v2.loc[:minute_cut] for k2, v2 in v.items()}
        return v.loc[:cut]

    def _perturb(v):
        if isinstance(v, dict):
            out = {k2: v2.copy() for k2, v2 in v.items()}
            for v2 in out.values():
                v2.loc[v2.index > minute_cut] *= 1.71
            return out
        out = v.copy()
        out.loc[out.index > cut] *= 1.71
        return out

    full = build_atoms(panels, cfg)
    prefix = build_atoms({k: _truncate(v) for k, v in panels.items()}, cfg)
    mutated = {k: _perturb(v) for k, v in panels.items()}
    changed = build_atoms(mutated, cfg)
    checks = {}
    for name in full:
        pd.testing.assert_frame_equal(
            full[name].loc[:cut], prefix[name], check_exact=False, rtol=1e-9, atol=1e-12
        )
        pd.testing.assert_frame_equal(
            full[name].loc[:cut], changed[name].loc[:cut], check_exact=False, rtol=1e-9, atol=1e-12
        )
        checks[name] = True
    return checks
