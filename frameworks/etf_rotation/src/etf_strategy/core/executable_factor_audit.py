"""Point-in-time factor diagnostics using executable open-to-open labels."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def apply_availability_lag(signal: pd.DataFrame, sessions: int) -> pd.DataFrame:
    """Move observations to the first conservatively usable signal session."""
    if not isinstance(sessions, int) or isinstance(sessions, bool) or sessions < 0:
        raise ValueError("sessions must be a non-negative integer")
    return signal.shift(sessions)


def forward_open_return(open_prices: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Return from D+1 open to D+1+horizon open, indexed by signal date D."""
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon <= 0:
        raise ValueError("horizon must be a positive integer")
    entry = open_prices.shift(-1)
    exit_price = open_prices.shift(-(horizon + 1))
    result = exit_price / entry - 1.0
    return result.where((entry > 0) & (exit_price > 0))


def daily_cross_sectional_ic(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    min_pairs: int = 5,
) -> pd.DataFrame:
    """Calculate one Spearman IC per signal date without filling missing data."""
    if min_pairs < 3:
        raise ValueError("min_pairs must be at least 3")
    if not signal.index.equals(forward_return.index):
        raise ValueError("signal and forward return dates must match exactly")
    if list(signal.columns) != list(forward_return.columns):
        raise ValueError("signal and forward return symbols must match exactly")

    rows = []
    for date in signal.index:
        pair = pd.concat(
            [signal.loc[date].rename("signal"), forward_return.loc[date].rename("return")],
            axis=1,
        ).replace([np.inf, -np.inf], np.nan).dropna()
        count = len(pair)
        ic = pair["signal"].corr(pair["return"], method="spearman") if count >= min_pairs else np.nan
        rows.append((date, ic, count))
    return pd.DataFrame(rows, columns=["signal_date", "ic", "pair_count"]).set_index("signal_date")


def summarize_ic(daily: pd.DataFrame) -> dict:
    """Summarize daily ICs; annualized ICIR is descriptive discovery evidence."""
    values = daily["ic"].dropna()
    if values.empty:
        return {
            "days": 0,
            "mean_ic": np.nan,
            "std_ic": np.nan,
            "icir_ann": np.nan,
            "positive_rate": np.nan,
            "median_pairs": np.nan,
        }
    std = float(values.std(ddof=1))
    return {
        "days": int(len(values)),
        "mean_ic": float(values.mean()),
        "std_ic": std,
        "icir_ann": float(values.mean() / std * math.sqrt(252)) if std > 0 else np.nan,
        "positive_rate": float((values > 0).mean()),
        "median_pairs": float(daily.loc[values.index, "pair_count"].median()),
    }


def rolling_direction_stability(
    daily: pd.DataFrame,
    direction: int,
    window: int = 180,
    step: int = 60,
) -> tuple[float, int]:
    """Fraction of fixed rolling windows whose mean IC agrees with direction."""
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or 1")
    values = daily["ic"]
    signs = []
    for start in range(0, max(0, len(values) - window + 1), step):
        chunk = values.iloc[start : start + window].dropna()
        if len(chunk) >= window // 2:
            signs.append(np.sign(chunk.mean()))
    if not signs:
        return np.nan, 0
    return float(np.mean(np.asarray(signs) == direction)), len(signs)
