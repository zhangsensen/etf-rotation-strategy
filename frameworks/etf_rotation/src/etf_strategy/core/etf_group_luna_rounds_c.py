"""Causal daily OHLC and fixed-pool price-transmission atoms for rounds 46–50."""
from __future__ import annotations

import numpy as np
import pandas as pd


WINDOW = 20
POOL_SIZE = 14
DIRECTIONS = {
    "l46_prior_channel_close_position": 1,
    "l46_intraday_upper_channel_penetration": 1,
    "l46_upper_channel_close_acceptance": 1,
    "l46_lower_channel_close_penetration": -1,
    "l47_prior_body_to_next_gap_corr": 1,
    "l47_prior_clv_to_next_gap_corr": 1,
    "l47_prior_range_to_next_gap_size_corr": -1,
    "l47_gap_magnitude_to_next_gap_magnitude_corr": -1,
    "l48_inside_day_rate": -1,
    "l48_outside_day_rate": -1,
    "l48_post_inside_return_contribution": 1,
    "l48_post_inside_range_contribution": -1,
    "l49_peer_gap_to_member_body_beta": 1,
    "l49_peer_gap_to_member_range_beta": -1,
    "l49_peer_gap_to_member_gap_beta": 1,
    "l49_peer_gap_to_member_downside_range_beta": -1,
    "l50_peer_body_to_member_gap_beta": 1,
    "l50_peer_body_to_member_body_beta": 1,
    "l50_peer_body_to_member_range_beta": -1,
    "l50_peer_range_to_member_open_dislocation_beta": -1,
}


def _clean(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.astype(float).replace([np.inf, -np.inf], np.nan)


def _complete(mask: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    return mask.astype(float).rolling(window, min_periods=window).sum().eq(window)


def _strict_mean(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.rolling(WINDOW, min_periods=WINDOW).mean()
    return out.where(_complete(frame.notna()))


def _valid_ohlc(open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    return (
        open_.gt(0.0) & high.gt(0.0) & low.gt(0.0) & close.gt(0.0)
        & high.ge(pd.concat([open_, close], axis=0).groupby(level=0).max())
        & low.le(pd.concat([open_, close], axis=0).groupby(level=0).min())
    )


def _positive_excess(value: pd.DataFrame, boundary: pd.DataFrame) -> pd.DataFrame:
    """Positive distance beyond a boundary, with relative-price tie handling."""
    ratio = value.div(boundary.where(boundary.gt(0.0)))
    return (value - boundary).clip(lower=0.0).where(ratio.gt(1.0 + 1e-12), 0.0).where(ratio.notna())


def _negative_excess(boundary: pd.DataFrame, value: pd.DataFrame) -> pd.DataFrame:
    """Positive distance below a boundary, with relative-price tie handling."""
    ratio = value.div(boundary.where(boundary.gt(0.0)))
    return (boundary - value).clip(lower=0.0).where(ratio.lt(1.0 - 1e-12), 0.0).where(ratio.notna())


def _corr(x: pd.DataFrame, y: pd.DataFrame) -> pd.DataFrame:
    valid = x.notna() & y.notna()
    xm = x.rolling(WINDOW, min_periods=WINDOW).mean()
    ym = y.rolling(WINDOW, min_periods=WINDOW).mean()
    cov = (x * y).rolling(WINDOW, min_periods=WINDOW).mean() - xm * ym
    sx = x.rolling(WINDOW, min_periods=WINDOW).std(ddof=0)
    sy = y.rolling(WINDOW, min_periods=WINDOW).std(ddof=0)
    return cov.div((sx * sy).where((sx * sy).gt(0.0))).where(_complete(valid))


def _beta(y: pd.DataFrame, x: pd.DataFrame) -> pd.DataFrame:
    valid = x.notna() & y.notna()
    xm = x.rolling(WINDOW, min_periods=WINDOW).mean()
    ym = y.rolling(WINDOW, min_periods=WINDOW).mean()
    cov = (x * y).rolling(WINDOW, min_periods=WINDOW).mean() - xm * ym
    var = x.rolling(WINDOW, min_periods=WINDOW).var(ddof=0)
    return cov.div(var.where(var.gt(0.0))).where(_complete(valid))


def _rolling_boundary_atoms(open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    prior_high = high.shift(1).rolling(WINDOW, min_periods=WINDOW).max()
    prior_low = low.shift(1).rolling(WINDOW, min_periods=WINDOW).min()
    prior_range = prior_high - prior_low
    valid_today = _valid_ohlc(open_, high, low, close)
    valid_prior = _complete(valid_today.shift(1)) & prior_range.gt(0.0)
    valid = valid_prior & valid_today
    p = (close - prior_low).div(prior_range.where(prior_range.gt(0.0))).where(valid)
    upper_probe = _positive_excess(high, prior_high).div(prior_range.where(prior_range.gt(0.0))).where(valid)
    upper_close = _positive_excess(close, prior_high).div(prior_range.where(prior_range.gt(0.0))).where(valid)
    lower_close = _negative_excess(prior_low, close).div(prior_range.where(prior_range.gt(0.0))).where(valid)
    return {
        "l46_prior_channel_close_position": _strict_mean(p),
        "l46_intraday_upper_channel_penetration": _strict_mean(upper_probe),
        "l46_upper_channel_close_acceptance": _strict_mean(upper_close),
        "l46_lower_channel_close_penetration": _strict_mean(lower_close),
    }


def _carry_atoms(open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    previous = close.shift(1)
    gap = open_.div(previous.where(previous.gt(0.0))).sub(1.0)
    body = close.div(open_.where(open_.gt(0.0))).sub(1.0)
    clv = (2.0 * close - high - low).div((high - low).where((high - low).gt(0.0)))
    relrange = (high - low).div(previous.where(previous.gt(0.0)))
    valid = _valid_ohlc(open_, high, low, close)
    gap, body, clv, relrange = (v.where(valid) for v in (gap, body, clv, relrange))
    return {
        "l47_prior_body_to_next_gap_corr": _corr(body.shift(1), gap),
        "l47_prior_clv_to_next_gap_corr": _corr(clv.shift(1), gap),
        "l47_prior_range_to_next_gap_size_corr": _corr(relrange.shift(1), gap.abs()),
        "l47_gap_magnitude_to_next_gap_magnitude_corr": _corr(gap.abs().shift(1), gap.abs()),
    }


def _relative_tie_compare(a: pd.DataFrame, b: pd.DataFrame, tol: float = 1e-12) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return strict greater/less states, treating relative-scale ties as equal."""
    ratio = a.div(b.where(b.ne(0.0)))
    greater = ratio.gt(1.0 + tol)
    less = ratio.lt(1.0 - tol)
    return greater, less


def _containment_atoms(open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    prev_high, prev_low = high.shift(1), low.shift(1)
    higher, lower = _relative_tie_compare(high, prev_high), _relative_tie_compare(low, prev_low)
    valid_today = _valid_ohlc(open_, high, low, close)
    valid = valid_today & valid_today.shift(1, fill_value=False) & prev_high.gt(0.0) & prev_low.gt(0.0)
    inside = ((~higher[0]) & (~lower[1])).astype(float).where(valid)
    outside = (higher[0] & lower[1]).astype(float).where(valid)
    ret = close.div(close.shift(1).where(close.shift(1).gt(0.0))).sub(1.0).where(valid)
    relrange = (high - low).div(close.shift(1).where(close.shift(1).gt(0.0))).where(valid)
    inside_lag = inside.shift(1)
    # Non-inside days contribute zero by design; missing source states stay NaN.
    return {
        "l48_inside_day_rate": _strict_mean(inside),
        "l48_outside_day_rate": _strict_mean(outside),
        "l48_post_inside_return_contribution": _strict_mean((inside_lag * ret).where(inside_lag.notna() & ret.notna())),
        "l48_post_inside_range_contribution": _strict_mean((inside_lag * relrange).where(inside_lag.notna() & relrange.notna())),
    }


def _peer_mean(frame: pd.DataFrame) -> pd.DataFrame:
    values = frame.to_numpy(dtype=float)
    out = np.full(values.shape, np.nan)
    for col in range(values.shape[1]):
        peers = np.delete(values, col, axis=1)
        valid = np.isfinite(peers).all(axis=1)
        out[valid, col] = peers[valid].mean(axis=1)
    return pd.DataFrame(out, index=frame.index, columns=frame.columns)


def _peer_atoms(open_: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    prev_close = close.shift(1)
    gap = open_.div(prev_close.where(prev_close.gt(0.0))).sub(1.0)
    body = close.div(open_.where(open_.gt(0.0))).sub(1.0)
    relrange = (high - low).div(prev_close.where(prev_close.gt(0.0)))
    downside_range = (open_ - low).div(prev_close.where(prev_close.gt(0.0)))
    valid = _valid_ohlc(open_, high, low, close) & prev_close.gt(0.0)
    gap, body, relrange, downside_range = (v.where(valid) for v in (gap, body, relrange, downside_range))
    all14 = gap.notna().all(axis=1) & body.notna().all(axis=1) & relrange.notna().all(axis=1) & downside_range.notna().all(axis=1)
    gap, body, relrange, downside_range = (v.where(all14, axis=0) for v in (gap, body, relrange, downside_range))
    peer_gap = _peer_mean(gap)
    peer_abs_gap = _peer_mean(gap.abs())
    peer_body = _peer_mean(body)
    peer_abs_body = _peer_mean(body.abs())
    peer_range = _peer_mean(relrange)

    return {
        "l49_peer_gap_to_member_body_beta": _beta(body, peer_gap.shift(1)),
        "l49_peer_gap_to_member_range_beta": _beta(relrange, peer_abs_gap.shift(1)),
        "l49_peer_gap_to_member_gap_beta": _beta(gap, peer_gap.shift(1)),
        "l49_peer_gap_to_member_downside_range_beta": _beta(downside_range, peer_gap.shift(1)),
        "l50_peer_body_to_member_gap_beta": _beta(gap, peer_body.shift(1)),
        "l50_peer_body_to_member_body_beta": _beta(body, peer_body.shift(1)),
        "l50_peer_body_to_member_range_beta": _beta(relrange, peer_abs_body.shift(1)),
        "l50_peer_range_to_member_open_dislocation_beta": _beta(gap.abs(), peer_range.shift(1)),
    }


def build_atoms(panels: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    """Build selected signed member scores using D-close daily OHLC only."""
    if tuple(cfg.get("windows", (WINDOW,))) != (WINDOW,):
        raise ValueError("Luna rounds 46-50 are frozen to window 20")
    mechanisms = cfg.get("mechanisms", {})
    if not mechanisms or set(mechanisms) - set(DIRECTIONS):
        raise ValueError("mechanisms must be a nonempty subset of approved Luna round-C candidates")
    mismatches = [name for name, entry in mechanisms.items() if entry.get("direction") != DIRECTIONS[name]]
    if mismatches:
        raise ValueError(f"frozen direction mismatch: {mismatches}")
    needed = {"open", "high", "low", "close"}
    missing = needed - set(panels)
    if missing:
        raise KeyError(f"missing daily OHLC panels: {sorted(missing)}")
    open_, high, low, close = (_clean(panels[k]) for k in ("open", "high", "low", "close"))
    if any(not open_.index.equals(v.index) or not open_.columns.equals(v.columns) for v in (high, low, close)):
        raise ValueError("OHLC panels must have identical axes")
    if any(frame.shape[1] != POOL_SIZE for frame in (open_, high, low, close)) and any(name.startswith(("l49_", "l50_")) for name in mechanisms):
        raise ValueError("peer price atoms require the fixed 14-member population")

    selected = set(mechanisms)
    raw: dict[str, pd.DataFrame] = {}
    if any(name.startswith("l46_") for name in selected):
        raw.update(_rolling_boundary_atoms(open_, high, low, close))
    if any(name.startswith("l47_") for name in selected):
        raw.update(_carry_atoms(open_, high, low, close))
    if any(name.startswith("l48_") for name in selected):
        raw.update(_containment_atoms(open_, high, low, close))
    if any(name.startswith(("l49_", "l50_")) for name in selected):
        raw.update(_peer_atoms(open_, high, low, close))
    return {
        f"{name}_20": (raw[name] * DIRECTIONS[name]).replace([np.inf, -np.inf], np.nan)
        for name in mechanisms
    }
