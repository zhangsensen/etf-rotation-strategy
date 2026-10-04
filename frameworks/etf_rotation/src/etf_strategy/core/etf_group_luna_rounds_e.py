"""Cross-sectional return-rank and conditional-recovery atoms for rounds 66–70."""
from __future__ import annotations

import numpy as np
import pandas as pd


WINDOW = 20
POOL_SIZE = 14
DIRECTIONS = {
    "l66_relative_rank_persistence": 1,
    "l66_rank_upgrade_rate": 1,
    "l66_rank_mobility": -1,
    "l67_median_residual_return": 1,
    "l67_trimmed_peer_relative_return": 1,
    "l67_cross_sectional_relative_zscore": 1,
    "l68_down_market_relative_win_rate": 1,
    "l68_down_market_relative_mean": 1,
    "l68_down_market_rank": 1,
    "l69_post_long_break_relative_return": 1,
    "l69_post_long_break_gap_excess": 1,
    "l69_post_long_break_body_excess": 1,
    "l70_negative_residual_recovery_rate": 1,
    "l70_negative_residual_recovery_magnitude": 1,
    "l70_negative_residual_nextday_mean": 1,
}


def _clean(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.astype(float).replace([np.inf, -np.inf], np.nan)


def _complete(mask: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    return mask.astype(float).rolling(window, min_periods=window).sum().eq(window)


def _strict_mean(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.rolling(WINDOW, min_periods=WINDOW).mean()
    return out.where(_complete(frame.notna()))


def _conditional_mean(value: pd.DataFrame, event: pd.DataFrame, valid: pd.DataFrame) -> pd.DataFrame:
    """Conditional mean over events inside 20 consecutive valid rows."""
    selected = event.astype(bool) & valid.astype(bool) & value.notna()
    count = selected.astype(float).rolling(WINDOW, min_periods=WINDOW).sum()
    total = value.where(selected).fillna(0.0).rolling(WINDOW, min_periods=WINDOW).sum()
    return total.div(count.where(count.gt(0.0))).where(_complete(valid))


def _inputs(panels: dict[str, pd.DataFrame], cfg: dict) -> tuple[list[str], pd.DataFrame]:
    if tuple(cfg.get("windows", (WINDOW,))) != (WINDOW,):
        raise ValueError("Luna rounds 66–70 are frozen to window 20")
    mechanisms = cfg.get("mechanisms", {})
    if not mechanisms or set(mechanisms) - set(DIRECTIONS):
        raise ValueError("mechanisms must be a nonempty subset of approved Luna round-E candidates")
    mismatches = [name for name, entry in mechanisms.items() if entry.get("direction") != DIRECTIONS[name]]
    if mismatches:
        raise ValueError(f"frozen direction mismatch: {mismatches}")
    if "close" not in panels:
        raise KeyError("missing daily close panel")
    close = _clean(panels["close"])
    if not isinstance(close.index, pd.DatetimeIndex) or not close.index.is_monotonic_increasing or close.index.has_duplicates:
        raise ValueError("close index must be a unique increasing DatetimeIndex")
    if any(frame.shape[1] != POOL_SIZE for frame in (close,)):
        raise ValueError("rounds 66–70 require the fixed 14-member population")
    if close.columns.has_duplicates or close.isna().all().all():
        raise ValueError("close panel must have unique members and observed data")
    close = close.where(close.gt(0.0))
    return list(mechanisms), close


def _raw_atoms(close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    returns = close.pct_change(fill_method=None)
    # Cross-sectional mechanisms fail closed for a date if any member is missing.
    all14 = returns.notna().all(axis=1)
    returns = returns.where(all14, axis=0)
    peer_total = returns.sum(axis=1, min_count=POOL_SIZE)
    peer_mean = returns.rsub(peer_total, axis=0).div(POOL_SIZE - 1)
    excess = returns - peer_mean

    rank = returns.rank(axis=1, method="average", pct=True).where(all14, axis=0)
    rank_pairs = rank.notna() & rank.shift(1).notna()
    rank_corr = rank.rolling(WINDOW, min_periods=WINDOW).corr(rank.shift(1)).where(_complete(rank_pairs))
    rank_change = rank - rank.shift(1)
    rank_upgrade = _strict_mean(rank_change.gt(0.0).astype(float).where(rank_change.notna()))
    rank_mobility = _strict_mean(rank_change.abs().where(rank_change.notna()))

    median_residual = excess.rolling(WINDOW, min_periods=WINDOW).median().where(_complete(excess.notna()))
    trimmed_peer = pd.DataFrame(np.nan, index=returns.index, columns=returns.columns)
    for j, col in enumerate(returns.columns):
        peers = returns.drop(columns=col)
        ordered = np.sort(peers.to_numpy(dtype=float), axis=1)
        trimmed = pd.Series(ordered[:, 1:-1].mean(axis=1), index=returns.index)
        trimmed_peer[col] = trimmed.where(all14)
    trimmed_relative = _strict_mean((returns - trimmed_peer).where(all14, axis=0))
    cs_mean = returns.mean(axis=1).where(all14)
    cs_std = returns.std(axis=1, ddof=0).where(all14 & returns.std(axis=1, ddof=0).gt(0.0))
    relative_z = returns.sub(cs_mean, axis=0).div(cs_std, axis=0)
    relative_z = _strict_mean(relative_z.where(all14, axis=0))

    down = peer_mean.lt(0.0)
    down_win = returns.gt(peer_mean).astype(float)
    down_rate = _conditional_mean(down_win, down, returns.notna())

    long_break = pd.Series(close.index.to_series().diff().dt.days.ge(3).to_numpy(), index=close.index)
    post_break_return = excess.where(long_break, axis=0)
    post_break_event = pd.DataFrame(np.broadcast_to(long_break.to_numpy()[:, None], returns.shape), index=returns.index, columns=returns.columns)
    post_break_mean = _conditional_mean(excess, post_break_event, returns.notna())
    pair_valid = excess.notna() & excess.shift(1).notna()
    prior_loss = excess.shift(1).lt(0.0) & pair_valid
    recovery_rate = _conditional_mean(excess.gt(0.0).astype(float), prior_loss, pair_valid)
    recovery_magnitude = _conditional_mean(excess, prior_loss & excess.gt(0.0), pair_valid)
    nextday_mean = _conditional_mean(excess, prior_loss, pair_valid)

    down_rank_mean = _conditional_mean(rank, down, returns.notna())

    return {
        "l66_relative_rank_persistence": rank_corr,
        "l66_rank_upgrade_rate": rank_upgrade,
        "l66_rank_mobility": rank_mobility,
        "l67_median_residual_return": median_residual,
        "l67_trimmed_peer_relative_return": trimmed_relative,
        "l67_cross_sectional_relative_zscore": relative_z,
        "l68_down_market_relative_win_rate": down_rate,
        "l68_down_market_relative_mean": _conditional_mean(excess, down, returns.notna()),
        "l68_down_market_rank": down_rank_mean,
        "l69_post_long_break_relative_return": post_break_mean,
        "l69_post_long_break_gap_excess": post_break_mean,
        "l69_post_long_break_body_excess": post_break_mean,
        "l70_negative_residual_recovery_rate": recovery_rate,
        "l70_negative_residual_recovery_magnitude": recovery_magnitude,
        "l70_negative_residual_nextday_mean": nextday_mean,
    }


def build_atoms(panels: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    """Build signed member scores using only D-close history and the date index."""
    names, close = _inputs(panels, cfg)
    raw = _raw_atoms(close)
    if any(name.startswith("l69_") for name in names):
        if "open" not in panels:
            raise KeyError("l69 post-long-break atoms require daily open panel")
        open_ = _clean(panels["open"])
        open_ = open_.where(open_.gt(0.0))
        if not open_.index.equals(close.index) or not open_.columns.equals(close.columns):
            raise ValueError("open and close panels must have identical axes")
        returns = close.pct_change(fill_method=None)
        all14 = returns.notna().all(axis=1)
        open_all14 = open_.notna().all(axis=1)
        valid_rows = all14 & open_all14
        long_break = pd.Series(close.index.to_series().diff().dt.days.ge(3).to_numpy(), index=close.index)
        peer_total = returns.sum(axis=1, min_count=POOL_SIZE)
        peer_mean = returns.rsub(peer_total, axis=0).div(POOL_SIZE - 1)
        excess = returns - peer_mean
        gap = open_.div(close.shift(1)).sub(1.0)
        body = close.div(open_).sub(1.0)
        peer_gap = gap.rsub(gap.sum(axis=1, min_count=POOL_SIZE), axis=0).div(POOL_SIZE - 1)
        peer_body = body.rsub(body.sum(axis=1, min_count=POOL_SIZE), axis=0).div(POOL_SIZE - 1)
        valid = pd.DataFrame(np.broadcast_to(valid_rows.to_numpy()[:, None], returns.shape), index=returns.index, columns=returns.columns)
        event = pd.DataFrame(np.broadcast_to(long_break.to_numpy()[:, None], returns.shape), index=returns.index, columns=returns.columns)
        for name, frame in {
            "l69_post_long_break_gap_excess": gap - peer_gap,
            "l69_post_long_break_body_excess": body - peer_body,
        }.items():
            raw[name] = _conditional_mean(frame, event, valid)
    return {
        f"{name}_20": raw[name].mul(DIRECTIONS[name]).replace([np.inf, -np.inf], np.nan)
        for name in names
    }
