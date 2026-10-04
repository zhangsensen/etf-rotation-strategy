"""ETF-only market-state atoms; all values are measurable at signal date D."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True, order=True)
class StateAtom:
    name: str
    family: str


def _mean_panel(close: pd.DataFrame, symbols: Sequence[str]) -> pd.Series:
    present = [s for s in symbols if s in close]
    if not present:
        raise ValueError("state basket has no symbols in close panel")
    return close[present].pct_change().mean(axis=1)


def _basket_return(
    close: pd.DataFrame,
    symbols: Sequence[str],
    window: int,
    min_members: int,
) -> pd.Series:
    """Point-in-time equal-weight basket return ending on D.

    A member is usable on D only when both endpoint prices are positive and
    present.  The minimum-member rule is evaluated independently on every D;
    no listing information from the future is used to fill the basket.
    """
    panel = close.reindex(columns=[s for s in symbols if s in close])
    if panel.empty:
        return pd.Series(np.nan, index=close.index, dtype=float)
    previous = panel.shift(int(window))
    valid = panel.gt(0) & previous.gt(0) & panel.notna() & previous.notna()
    returns = (panel / previous - 1.0).where(valid)
    basket = returns.mean(axis=1).where(returns.notna().sum(axis=1).ge(int(min_members)))
    return basket.rename(f"basket_return_{int(window)}")


def _basket_drawdown(
    close: pd.DataFrame,
    symbols: Sequence[str],
    window: int,
    min_members: int,
) -> pd.Series:
    """Average member drawdown from its trailing D-inclusive high.

    This is a basket-level state proxy with the same point-in-time member
    availability rule as the basket return.  Rolling highs include D and only
    earlier rows, so the value is measurable after close(D).
    """
    panel = close.reindex(columns=[s for s in symbols if s in close])
    if panel.empty:
        return pd.Series(np.nan, index=close.index, dtype=float)
    trailing_high = panel.rolling(int(window), min_periods=int(window)).max()
    valid = panel.gt(0) & trailing_high.gt(0) & panel.notna() & trailing_high.notna()
    drawdowns = (panel / trailing_high - 1.0).where(valid)
    basket = drawdowns.mean(axis=1).where(drawdowns.notna().sum(axis=1).ge(int(min_members)))
    return basket.rename(f"basket_drawdown_{int(window)}")


def build_market_state_space(
    close: pd.DataFrame,
    *,
    candidate_symbols: Sequence[str],
    benchmark_symbols: Sequence[str] = ("510300.SH", "510500.SH"),
    defensive_symbols: Sequence[str] = ("511010.SH", "511880.SH", "518880.SH", "512890.SH"),
    min_attack_members: int = 3,
    min_defensive_members: int = 4,
) -> dict[str, pd.Series]:
    """Return frozen, past-only state atoms.

    Benchmarks are inputs to market state only.  They are never used to form a
    cross-sectional rank or to enter the attack/defensive label here.
    """
    if close.empty or not close.index.is_monotonic_increasing or close.index.has_duplicates:
        raise ValueError("close panel must have a non-empty increasing unique index")
    candidates = [s for s in candidate_symbols if s in close]
    benchmarks = [s for s in benchmark_symbols if s in close]
    defensives = [s for s in defensive_symbols if s in close]
    if not candidates or not benchmarks or not defensives:
        raise ValueError("state space requires candidate, benchmark and defensive inputs")
    candidate_ret = close[candidates].pct_change()
    benchmark_ret = close[benchmarks].pct_change().mean(axis=1)
    defensive_ret = close[defensives].pct_change().mean(axis=1)
    atoms: dict[str, pd.Series] = {}
    for window in (5, 20, 60):
        atoms[f"BENCH_RET_{window}"] = close[benchmarks].pct_change(window).mean(axis=1)
        atoms[f"BENCH_SLOPE_{window}"] = benchmark_ret.rolling(window, min_periods=window).mean()
        atoms[f"DEFENSIVE_RET_{window}"] = close[defensives].pct_change(window).mean(axis=1)
        candidate_path = candidate_ret.rolling(window, min_periods=window).sum()
        candidate_path = candidate_path.where(
            candidate_ret.rolling(window, min_periods=window).count().eq(window)
        )
        atoms[f"CANDIDATE_BREADTH_{window}"] = candidate_path.gt(0).where(
            candidate_path.notna()
        ).mean(axis=1)
    atoms["BENCH_VOL_20"] = benchmark_ret.rolling(20, min_periods=20).std()
    atoms["BENCH_VOL_60"] = benchmark_ret.rolling(60, min_periods=60).std()
    atoms["CANDIDATE_DISPERSION_20"] = candidate_ret.rolling(20, min_periods=20).std().mean(axis=1)
    atoms["CANDIDATE_DISPERSION_60"] = candidate_ret.rolling(60, min_periods=60).std().mean(axis=1)
    for window in (20, 60):
        benchmark_ma = close[benchmarks].rolling(window, min_periods=window).mean()
        atoms[f"BENCH_ABOVE_MA_{window}"] = (close[benchmarks] / benchmark_ma - 1.0).mean(
            axis=1
        )
    atoms["DEFENSIVE_REL_BENCH_20"] = atoms["DEFENSIVE_RET_20"] - atoms["BENCH_RET_20"]
    atoms["DEFENSIVE_REL_BENCH_60"] = atoms["DEFENSIVE_RET_60"] - atoms["BENCH_RET_60"]
    atoms["GOLD_RET_20"] = close["518880.SH"].pct_change(20) if "518880.SH" in close else defensive_ret.rolling(20, min_periods=20).mean()
    # These are ETF-regime atoms: the same fixed baskets used by the label,
    # with no benchmark membership and no outcome values.  Keep the three
    # families separate so the grammar/ledger can account for them distinctly.
    for window in (20, 60):
        attack = _basket_return(close, candidates, window, min_attack_members)
        defensive = _basket_return(close, defensives, window, min_defensive_members)
        atoms[f"ATTACK_RET_{window}"] = attack
        atoms[f"ATTACK_REL_DEFENSIVE_{window}"] = attack - defensive
        atoms[f"ATTACK_DD_{window}"] = _basket_drawdown(
            close, candidates, window, min_attack_members
        )
    return {name: series.rename(name).astype(float) for name, series in atoms.items()}


def parse_state_atoms(raw_atoms: Sequence[Mapping[str, str]]) -> list[StateAtom]:
    atoms = [StateAtom(str(item["name"]), str(item["family"])) for item in raw_atoms]
    if not atoms or len(atoms) != len(set(atoms)) or len({a.name for a in atoms}) != len(atoms):
        raise ValueError("state atom registry must be non-empty and unique")
    return sorted(atoms)


def past_zscore(
    series: pd.Series,
    window: int = 252,
    min_observations: int | None = None,
) -> pd.Series:
    """Normalize using D and earlier observations only.

    ``min_observations`` permits isolated historical data gaps without making
    the next full window unusable. It is an availability rule only: rolling
    moments still contain no observations after D.
    """
    minimum = window if min_observations is None else min_observations
    if window < 1 or not 1 <= minimum <= window:
        raise ValueError("normalization requires 1 <= min_observations <= window")
    mean = series.rolling(window, min_periods=minimum).mean()
    std = series.rolling(window, min_periods=minimum).std()
    return ((series - mean) / std.replace(0.0, np.nan)).rename(series.name)
