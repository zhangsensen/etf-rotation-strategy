"""Locally derived new families (USER directive 2026-09-19 20:05, no external data):

- cost_distribution: chip/cost distribution built from 1d panels
  (close/high/low/amount). Only RELATIVE distribution shape is used; decay
  uses a scale-free trailing-amount turnover proxy -- never future turnover.
- bar_size_order_flow: 1m bar-size-layered direction (bar-level "large order"
  proxy; NOT a claim of true order-level data).
- intraday_volume_profile_1m: 1m volume distribution over the session.

1m atoms use only bars with datetime < as_of + 1 day (via the engine's own
complete-day reader), satisfying the leak contract.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..etf_intraday_factor_space import _read_complete_days

COST_GRID = 200
COST_WINDOW_LONG = 120
COST_WINDOW_SHORT = 20
ROLL_ATOM_WINDOW = 20


# --------------------------------------------------------------------------
# cost_distribution (1d panels)
# --------------------------------------------------------------------------
def _chip_stats(highs, lows, masses, close_norm, grid, gmin, gmax):
    """masses: per-day chip mass already decayed; close_norm/highs/lows in grid
    coordinates ([0,1]). Returns dict of stats."""
    lo = np.clip((np.minimum(lows, highs) - gmin) / (gmax - gmin), 0.0, 1.0)
    hi = np.clip((np.maximum(lows, highs) - gmin) / (gmax - gmin), 0.0, 1.0)
    span = np.maximum(hi - lo, 1e-9)
    density = (masses / span)[:, None] * ((grid[None, :] >= lo[:, None]) & (grid[None, :] <= hi[:, None]))
    mass = density.sum(axis=0)
    total = mass.sum()
    if total <= 0:
        return None
    avg_cost = float((mass * grid).sum() / total)
    cum = np.cumsum(mass) / total
    q05 = float(grid[np.searchsorted(cum, 0.05)])
    q95 = float(grid[np.searchsorted(cum, 0.95)])
    below = float(mass[grid <= close_norm].sum() / total)
    return {
        "profit": below,
        "overhang": 1.0 - below,
        "avg_cost": avg_cost,
        "range90": (q95 - q05) / max(avg_cost, 1e-9),
    }


def _build_cost_distribution(panels, eligibility, data_root, config):
    close, high, low, amount = panels["close"], panels["high"], panels["low"], panels["amount"]
    atoms = [a["name"] for a in config["atoms"]]
    out = {name: pd.DataFrame(np.nan, index=close.index, columns=close.columns) for name in atoms}
    grid = None
    for sym in close.columns:
        c, h, l, a = close[sym], high[sym], low[sym], amount[sym]
        med60 = a.rolling(60, min_periods=20).median()
        rate = (a / med60).fillna(0.0).clip(lower=0.0)
        log_decay = np.log1p(-rate.clip(upper=0.95))  # per-day decay log factor
        cum_decay = np.concatenate([[0.0], np.cumsum(log_decay.values)])
        n = len(c)
        lo_w = max(0, n - 1500)
        for i in range(n):
            i0 = max(0, i - COST_WINDOW_LONG + 1)
            if i - i0 + 1 < 40:
                continue
            hi_w = h.values[i0:i + 1]
            lo_w2 = l.values[i0:i + 1]
            gmin, gmax = float(np.nanmin(lo_w2)), float(np.nanmax(hi_w))
            if not np.isfinite(gmin) or not np.isfinite(gmax) or gmax <= gmin:
                continue
            if grid is None or grid.size != COST_GRID:
                grid = np.linspace(0.0, 1.0, COST_GRID)
            decay_at_i = cum_decay[i + 1]
            masses_long = np.exp(decay_at_i - cum_decay[i0 + 1:i + 2]) * a.values[i0:i + 1]
            c_norm = float(np.clip((c.values[i] - gmin) / (gmax - gmin), 0.0, 1.0))
            stats_long = _chip_stats(hi_w, lo_w2, masses_long, c_norm, grid, gmin, gmax)
            if stats_long is None:
                continue
            j0 = max(0, i - COST_WINDOW_SHORT + 1)
            masses_short = np.exp(decay_at_i - cum_decay[j0 + 1:i + 2]) * a.values[j0:i + 1]
            stats_short = _chip_stats(
                h.values[j0:i + 1], l.values[j0:i + 1], masses_short, c_norm, grid, gmin, gmax
            )
            date = c.index[i]
            if "PROFIT_RATIO_60" in out and stats_long:
                out["PROFIT_RATIO_60"].loc[date, sym] = stats_long["profit"]
            if "CHIP_RANGE_90_60" in out and stats_long:
                out["CHIP_RANGE_90_60"].loc[date, sym] = stats_long["range90"]
            if "OVERHAND_THICKNESS_60" in out and stats_long:
                out["OVERHAND_THICKNESS_60"].loc[date, sym] = stats_long["overhang"]
            if stats_short:
                if "PRICE_VS_AVGCOST_20" in out:
                    avg_cost_price = gmin + stats_short["avg_cost"] * (gmax - gmin)
                    out["PRICE_VS_AVGCOST_20"].loc[date, sym] = (
                        c.values[i] / avg_cost_price - 1.0
                        if avg_cost_price > 0
                        else np.nan
                    )
                if "COST_CENTER_SHIFT_20" in out:
                    out["COST_CENTER_SHIFT_20"].loc[date, sym] = (
                        stats_short["avg_cost"] / stats_long["avg_cost"] - 1.0
                        if stats_long["avg_cost"] > 0
                        else np.nan
                    )
    return out


# --------------------------------------------------------------------------
# 1m helpers
# --------------------------------------------------------------------------
def _daily_1m_features(frame: pd.DataFrame) -> pd.Series:
    """Per-day features from one complete 1m session."""
    close = frame["close"].to_numpy(dtype=float)
    turnover = frame["turnover"].to_numpy(dtype=float)
    open_ = frame["open"].to_numpy(dtype=float)
    if len(close) < 60 or turnover.sum() <= 0:
        return pd.Series(dtype=float)
    prev = np.concatenate([[open_[0]], close[:-1]])
    direction = np.sign(close - prev)
    signed = direction * turnover
    total = turnover.sum()
    med = np.median(turnover)
    big = turnover > 5.0 * med
    feats = {
        "imbalance_1m": signed.sum() / total,
        "bigbar_vol_share_1m": turnover[big].sum() / total if big.any() else 0.0,
        "bigbar_dir_1m": direction[big].mean() if big.any() else 0.0,
        "close5_vs_day_1m": float(
            np.sign(close[-1] / close[-6] - 1.0) == np.sign(close[-1] / open_[0] - 1.0)
        ),
        "bigbar_edge_share_1m": (
            (turnover[:30][big[:30]].sum() + turnover[-30:][big[-30:]].sum()) / total
        ),
        "open30_share_1m": turnover[:30].sum() / total,
        "close30_share_1m": turnover[-30:].sum() / total,
        "vol_autocorr_1m": float(np.corrcoef(turnover[:-1], turnover[1:])[0, 1])
        if np.std(turnover[:-1]) > 0 and np.std(turnover[1:]) > 0
        else np.nan,
        "spike_freq_1m": float((turnover > 5.0 * med).mean()),
    }
    bins = np.array_split(turnover, 8)
    probs = np.array([b.sum() for b in bins])
    probs = probs / probs.sum() if probs.sum() > 0 else probs
    feats["vol_entropy_1m"] = float(
        -(probs[probs > 0] * np.log(probs[probs > 0])).sum() / np.log(8)
    )
    return pd.Series(feats)


def _build_1m_atom_space(panels, data_root, config, mapping: dict[str, str]):
    """mapping: per-day feature name -> atom name (rolling-mean aggregated)."""
    close = panels["close"]
    frequency = str(config["frequency"])
    out = {
        atom: pd.DataFrame(np.nan, index=close.index, columns=close.columns)
        for atom in mapping.values()
    }
    as_of = close.index.max()
    for sym in close.columns:
        path = Path(data_root) / frequency / f"{sym}.parquet"
        if not path.exists():
            continue
        try:
            frame, _ = _read_complete_days(Path(data_root), sym, frequency, as_of)
        except Exception:  # noqa: BLE001 - missing/incomplete 1m -> NaN columns
            continue
        if frame.empty:
            continue
        frame = frame.copy()
        frame["date"] = frame["datetime"].dt.normalize()
        records = []
        for date, day in frame.groupby("date", sort=True):
            feats = _daily_1m_features(day)
            if len(feats) == 0:
                continue
            feats["date"] = date
            records.append(feats)
        daily = pd.DataFrame(records).set_index("date") if records else pd.DataFrame()
        if daily.empty:
            continue
        for feat, atom in mapping.items():
            series = daily[feat].rolling(ROLL_ATOM_WINDOW, min_periods=10).mean()
            out[atom][sym] = series.reindex(close.index)
    return out


ATOM_MAP_FLOW = {
    "imbalance_1m": "TICK_IMBALANCE_20",
    "bigbar_vol_share_1m": "BIGBAR_VOL_SHARE_20",
    "bigbar_dir_1m": "BIGBAR_DIR_SKEW_20",
    "close5_vs_day_1m": "CLOSE5_DAY_CONSIST_20",
    "bigbar_edge_share_1m": "BIGBAR_EDGE_CONC_20",
}

ATOM_MAP_PROFILE = {
    "open30_share_1m": "OPEN30_VOL_SHARE_20",
    "close30_share_1m": "CLOSE30_VOL_SHARE_20",
    "vol_autocorr_1m": "VOL_AUTOCORR_20",
    "spike_freq_1m": "VOL_SPIKE_FREQ_20",
    "vol_entropy_1m": "VOL_ENTROPY_20",
}


def _build_bar_size_order_flow(panels, eligibility, data_root, config):
    return _build_1m_atom_space(panels, data_root, config, ATOM_MAP_FLOW)


def _build_intraday_volume_profile(panels, eligibility, data_root, config):
    return _build_1m_atom_space(panels, data_root, config, ATOM_MAP_PROFILE)


register_family(
    FamilyProvider("cost_distribution", "cost_distribution", _build_cost_distribution)
)
register_family(
    FamilyProvider("bar_size_order_flow", "bar_size_order_flow", _build_bar_size_order_flow)
)
register_family(
    FamilyProvider(
        "intraday_volume_profile_1m", "intraday_volume_profile_1m", _build_intraday_volume_profile
    )
)
