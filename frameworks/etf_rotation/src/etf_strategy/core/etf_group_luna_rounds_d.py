"""Causal daily OHLC atoms for Luna rounds 61–65 (proposal-stage only)."""
from __future__ import annotations

import numpy as np
import pandas as pd

WINDOW = 20
POOL_SIZE = 14
DIRECTIONS = {
    "l61_upper_breakout_rejection_depth": -1,
    "l61_lower_breakdown_reclaim_depth": 1,
    "l61_failed_break_directional_balance": 1,
    "l62_ohlc_peak_to_trough_drawdown": -1,
    "l62_ohlc_trough_to_peak_runup": 1,
    "l63_rejected_range_to_body_energy": -1,
    "l63_lower_wick_to_upper_wick_energy": 1,
    "l64_post_inside_return_spread": 1,
    "l64_post_outside_return_spread": 1,
    "l65_midrange_drift": 1,
    "l65_gap_scaled_by_prior_range": 1,
}


def _clean(x: pd.DataFrame) -> pd.DataFrame:
    return x.astype(float).replace([np.inf, -np.inf], np.nan)


def _valid(o: pd.DataFrame, h: pd.DataFrame, l: pd.DataFrame, c: pd.DataFrame) -> pd.DataFrame:
    return (
        o.gt(0) & h.gt(0) & l.gt(0) & c.gt(0)
        & h.ge(pd.concat([o, c], axis=0).groupby(level=0).max())
        & l.le(pd.concat([o, c], axis=0).groupby(level=0).min())
    )


def _strict_mean(x: pd.DataFrame, n: int = WINDOW) -> pd.DataFrame:
    return x.rolling(n, min_periods=n).mean().where(x.notna().rolling(n, min_periods=n).sum().eq(n))


def _strict_gt(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    ratio = a.div(b.where(b.gt(0.0)))
    return ratio.gt(1.0 + 1e-12)


def _strict_lt(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    ratio = a.div(b.where(b.gt(0.0)))
    return ratio.lt(1.0 - 1e-12)


def _channel(o: pd.DataFrame, h: pd.DataFrame, l: pd.DataFrame, c: pd.DataFrame, valid: pd.DataFrame) -> dict[str, pd.DataFrame]:
    prior_h = h.shift(1).rolling(WINDOW, min_periods=WINDOW).max()
    prior_l = l.shift(1).rolling(WINDOW, min_periods=WINDOW).min()
    width = (prior_h - prior_l).where((prior_h - prior_l).gt(0))
    prior_ok = valid.shift(1).rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW)
    ok = valid & prior_ok & width.notna()
    upper_fail = _strict_gt(h, prior_h) & ~_strict_gt(c, prior_h) & ok
    lower_reclaim = _strict_lt(l, prior_l) & ~_strict_lt(c, prior_l) & ok
    up_depth = ((prior_h - c) / width).where(upper_fail, 0.0).where(ok)
    down_depth = ((c - prior_l) / width).where(lower_reclaim, 0.0).where(ok)
    balance = (lower_reclaim.astype(float) - upper_fail.astype(float)).where(ok)
    return {
        "l61_upper_breakout_rejection_depth": _strict_mean(up_depth),
        "l61_lower_breakdown_reclaim_depth": _strict_mean(down_depth),
        "l61_failed_break_directional_balance": _strict_mean(balance),
    }


def _ohlc_path(o: pd.DataFrame, h: pd.DataFrame, l: pd.DataFrame, c: pd.DataFrame, valid: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # Intraday high/low order is unknown. Only compare a day's low/high with
    # extrema from strictly earlier dates, so no same-bar ordering is assumed.
    shape = h.shape
    dd = np.full(shape, np.nan)
    ru = np.full(shape, np.nan)
    hv, lv, vv = h.to_numpy(), l.to_numpy(), valid.to_numpy()
    for t in range(WINDOW - 1, len(h)):
        for j in range(h.shape[1]):
            start = t - WINDOW + 1
            if not vv[start:t + 1, j].all():
                continue
            losses, gains = [], []
            for k in range(start + 1, t + 1):
                peak = np.max(hv[start:k, j])
                trough = np.min(lv[start:k, j])
                if peak > 0:
                    losses.append(max(0.0, (peak - lv[k, j]) / peak))
                if trough > 0:
                    gains.append(max(0.0, (hv[k, j] - trough) / trough))
            dd[t, j] = max(losses, default=0.0)
            ru[t, j] = max(gains, default=0.0)
    idx, cols = h.index, h.columns
    return {
        "l62_ohlc_peak_to_trough_drawdown": pd.DataFrame(dd, index=idx, columns=cols),
        "l62_ohlc_trough_to_peak_runup": pd.DataFrame(ru, index=idx, columns=cols),
    }


def _state_responses(o: pd.DataFrame, h: pd.DataFrame, l: pd.DataFrame, c: pd.DataFrame, valid: pd.DataFrame) -> dict[str, pd.DataFrame]:
    adjacent = valid & valid.shift(1, fill_value=False)
    inside = (~_strict_gt(h, h.shift(1)) & ~_strict_lt(l, l.shift(1))).where(adjacent)
    outside = (_strict_gt(h, h.shift(1)) & _strict_lt(l, l.shift(1))).where(adjacent)
    ret = (c / c.shift(1) - 1.0).where(adjacent)
    out: dict[str, pd.DataFrame] = {}
    for name, state in (("l64_post_inside_return_spread", inside.shift(1)), ("l64_post_outside_return_spread", outside.shift(1))):
        state = state.astype(float)
        # Trailing 20 response dates; compare conditional state and complement.
        s = state.where(ret.notna())
        n1 = s.rolling(WINDOW, min_periods=WINDOW).sum()
        n0 = (1.0 - s).where(s.notna()).rolling(WINDOW, min_periods=WINDOW).sum()
        a = (ret * s).rolling(WINDOW, min_periods=WINDOW).sum() / n1.where(n1.gt(0))
        b = (ret * (1.0 - s)).rolling(WINDOW, min_periods=WINDOW).sum() / n0.where(n0.gt(0))
        complete = ret.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW) & n1.gt(0) & n0.gt(0)
        out[name] = (a - b).where(complete)
    return out


def _midrange(o: pd.DataFrame, h: pd.DataFrame, l: pd.DataFrame, c: pd.DataFrame, valid: pd.DataFrame) -> dict[str, pd.DataFrame]:
    mid = (h + l) / 2.0
    midret = (mid / mid.shift(1) - 1.0).where(valid & valid.shift(1, fill_value=False))
    prev_range = (h.shift(1) - l.shift(1)).where((h.shift(1) - l.shift(1)).gt(0))
    gap = (o - c.shift(1)) / prev_range
    gap = gap.where(valid & valid.shift(1, fill_value=False) & prev_range.notna())
    return {
        "l65_midrange_drift": _strict_mean(midret),
        "l65_gap_scaled_by_prior_range": _strict_mean(gap),
    }


def _wick_energy(o: pd.DataFrame, h: pd.DataFrame, l: pd.DataFrame, c: pd.DataFrame, valid: pd.DataFrame) -> dict[str, pd.DataFrame]:
    upper_body = pd.concat([o, c], axis=0).groupby(level=0).max()
    lower_body = pd.concat([o, c], axis=0).groupby(level=0).min()
    scale = o.where(o.gt(0.0))
    upper = ((h - upper_body) / scale).clip(lower=0.0)
    lower = ((lower_body - l) / scale).clip(lower=0.0)
    body = ((c - o) / scale)
    upper2, lower2, body2 = upper.pow(2).where(valid), lower.pow(2).where(valid), body.pow(2).where(valid)
    wick_energy = upper2 + lower2
    rejected = wick_energy.div(body2.where(body2.gt(0.0)))
    wick_balance = (lower2 - upper2).div(wick_energy.where(wick_energy.gt(0.0)))
    return {
        "l63_rejected_range_to_body_energy": _strict_mean(rejected),
        "l63_lower_wick_to_upper_wick_energy": _strict_mean(wick_balance.where(valid)),
    }


def build_atoms(panels: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    """Build D-close known member scores; output candidate names end in ``_20``."""
    if tuple(cfg.get("windows", (WINDOW,))) != (WINDOW,):
        raise ValueError("Luna rounds D are frozen to window 20")
    mechanisms = cfg.get("mechanisms", {})
    if not mechanisms or set(mechanisms) - set(DIRECTIONS):
        raise ValueError("mechanisms must be a nonempty subset of Luna round-D candidates")
    bad = [n for n, entry in mechanisms.items() if entry.get("direction") != DIRECTIONS[n]]
    if bad:
        raise ValueError(f"frozen direction mismatch: {bad}")
    need = {"open", "high", "low", "close"}
    if need - set(panels):
        raise KeyError(f"missing daily OHLC panels: {sorted(need - set(panels))}")
    o, h, l, c = (_clean(panels[k]) for k in ("open", "high", "low", "close"))
    if any(not o.index.equals(x.index) or not o.columns.equals(x.columns) for x in (h, l, c)):
        raise ValueError("OHLC panels must have identical axes")
    if any(n.startswith("l62_") for n in mechanisms) and o.shape[1] != POOL_SIZE:
        raise ValueError("round-D path risk atoms require the fixed 14-member population")
    valid = _valid(o, h, l, c)
    selected = set(mechanisms)
    raw: dict[str, pd.DataFrame] = {}
    if any(n.startswith("l61_") for n in selected):
        raw.update(_channel(o, h, l, c, valid))
    if any(n.startswith("l62_") for n in selected):
        raw.update(_ohlc_path(o, h, l, c, valid))
    if any(n.startswith("l63_") for n in selected):
        raw.update(_wick_energy(o, h, l, c, valid))
    if any(n.startswith("l64_") for n in selected):
        raw.update(_state_responses(o, h, l, c, valid))
    if any(n.startswith("l65_") for n in selected):
        raw.update(_midrange(o, h, l, c, valid))
    return {f"{n}_20": raw[n] * DIRECTIONS[n] for n in mechanisms}
