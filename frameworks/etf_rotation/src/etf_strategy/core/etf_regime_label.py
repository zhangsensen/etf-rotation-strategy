"""Executable ETF regime labels for the isolated ETF research line.

The label is a time-series spread: a fixed attack basket minus a fixed
defensive basket.  A signal dated D is only executable at the D+2 open.  This
module deliberately has no cross-sectional ranking or stock-line imports.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


DEFENSIVE_SYMBOLS: tuple[str, ...] = (
    "511010.SH",  # five-year government bond
    "511880.SH",  # money market
    "518880.SH",  # gold
    "512890.SH",  # dividend low volatility
)


@dataclass(frozen=True)
class BasketSpec:
    attack_symbols: tuple[str, ...]
    defensive_symbols: tuple[str, ...] = DEFENSIVE_SYMBOLS
    min_attack_members: int = 6
    min_defensive_members: int = 4

    def __post_init__(self) -> None:
        if not self.attack_symbols:
            raise ValueError("attack basket cannot be empty")
        if len(set(self.attack_symbols)) != len(self.attack_symbols):
            raise ValueError("attack basket symbols must be unique")
        if set(self.attack_symbols) & set(self.defensive_symbols):
            raise ValueError("attack and defensive baskets must be disjoint")
        if self.min_attack_members < 1 or self.min_defensive_members < 1:
            raise ValueError("minimum basket member counts must be positive")
        if self.min_attack_members > len(self.attack_symbols):
            raise ValueError("minimum attack members exceeds basket size")
        if self.min_defensive_members > len(self.defensive_symbols):
            raise ValueError("minimum defensive members exceeds basket size")


def basket_spec_from_universe(
    universe_path: str | Path,
    *,
    defensive_symbols: Sequence[str] = DEFENSIVE_SYMBOLS,
    min_attack_members: int = 6,
    min_defensive_members: int = 4,
) -> BasketSpec:
    """Resolve the fixed baskets from the predeclared universe metadata.

    The defensive set is intentionally explicit, even when a symbol's role is
    currently ``candidate``.  Attack is the candidate role with all defensive
    symbols removed; no observation or benchmark ETF can enter the label.
    """
    rows = json.loads(Path(universe_path).read_text())["etfs"]
    available = {str(row["ts_code"]) for row in rows}
    defensive = tuple(str(symbol) for symbol in defensive_symbols)
    missing = sorted(set(defensive) - available)
    if missing:
        raise ValueError(f"configured defensive symbols absent from universe: {missing}")
    attack = tuple(
        sorted(
            str(row["ts_code"])
            for row in rows
            if row.get("role") == "candidate" and str(row["ts_code"]) not in defensive
        )
    )
    if len(attack) < min_attack_members:
        raise ValueError("candidate attack basket is smaller than its minimum")
    return BasketSpec(
        attack_symbols=attack,
        defensive_symbols=defensive,
        min_attack_members=min_attack_members,
        min_defensive_members=min_defensive_members,
    )


def _basket_return(
    open_prices: pd.DataFrame,
    symbols: Sequence[str],
    horizon: int,
    entry_lag: int,
    min_members: int,
) -> tuple[pd.Series, pd.Series]:
    entry = open_prices.shift(-entry_lag).reindex(columns=symbols)
    exit_price = open_prices.shift(-(entry_lag + horizon)).reindex(columns=symbols)
    # Membership on signal date D cannot be inferred from a listing that only
    # appears during the forward label window.
    known_on_signal_date = open_prices.reindex(columns=symbols).gt(0)
    valid = (
        known_on_signal_date
        & entry.gt(0)
        & exit_price.gt(0)
        & entry.notna()
        & exit_price.notna()
    )
    returns = (exit_price / entry - 1.0).where(valid)
    count = returns.notna().sum(axis=1).astype("int64")
    basket = returns.mean(axis=1).where(count >= min_members)
    return basket.rename("basket_return"), count.rename("member_count")


def build_regime_labels(
    open_prices: pd.DataFrame,
    basket: BasketSpec,
    *,
    horizons: Sequence[int] = (5, 10, 20),
    entry_lag: int = 2,
) -> dict[int, pd.DataFrame]:
    """Build labels indexed by signal date D.

    Every output has signal_date D, entry_date D+2 and exit_date D+2+H.  The
    basket return uses equal weights among available members only when the
    configured minimum is met.  No forward value is used to decide eligibility
    at D; future prices only populate the outcome columns.
    """
    if entry_lag <= 0:
        raise ValueError("entry_lag must be positive")
    if not open_prices.index.is_monotonic_increasing or open_prices.index.has_duplicates:
        raise ValueError("open_prices index must be increasing and unique")
    unknown = (set(basket.attack_symbols) | set(basket.defensive_symbols)) - set(open_prices.columns)
    if unknown:
        raise ValueError(f"basket symbols absent from prices: {sorted(unknown)}")
    outputs: dict[int, pd.DataFrame] = {}
    for horizon in horizons:
        if int(horizon) <= 0:
            raise ValueError("horizons must be positive")
        attack, attack_count = _basket_return(
            open_prices, basket.attack_symbols, int(horizon), entry_lag, basket.min_attack_members
        )
        defensive, defensive_count = _basket_return(
            open_prices,
            basket.defensive_symbols,
            int(horizon),
            entry_lag,
            basket.min_defensive_members,
        )
        frame = pd.DataFrame(
            {
                "signal_date": open_prices.index,
                "entry_date": open_prices.index.to_series().shift(-entry_lag).to_numpy(),
                "exit_date": open_prices.index.to_series().shift(-(entry_lag + int(horizon))).to_numpy(),
                "attack_return": attack,
                "defensive_return": defensive,
                "basket_spread": attack - defensive,
                "attack_member_count": attack_count,
                "defensive_member_count": defensive_count,
            },
            index=open_prices.index,
        )
        frame["horizon"] = int(horizon)
        frame["entry_lag_sessions"] = int(entry_lag)
        valid = frame["basket_spread"].notna()
        # Dates are metadata, not a way to fill outcomes.  A valid label must
        # prove the executable ordering explicitly.
        if (
            frame.loc[valid, "entry_date"].le(frame.loc[valid, "signal_date"]).any()
            or frame.loc[valid, "exit_date"].le(frame.loc[valid, "entry_date"]).any()
        ):
            raise AssertionError("label violates signal < entry < exit timing")
        outputs[int(horizon)] = frame.reset_index(drop=True)
    return outputs


def label_contract(basket: BasketSpec, horizons: Sequence[int], entry_lag: int) -> dict[str, object]:
    return {
        "signal_time": "close(D)",
        "entry_time": f"open(D+{entry_lag})",
        "exit_time": f"open(D+{entry_lag}+H)",
        "label": "equal_weight(attack) - equal_weight(defensive)",
        "horizons": [int(value) for value in horizons],
        "entry_lag_sessions": int(entry_lag),
        "attack_symbols": list(basket.attack_symbols),
        "defensive_symbols": list(basket.defensive_symbols),
        "min_attack_members": basket.min_attack_members,
        "min_defensive_members": basket.min_defensive_members,
        "missing_rule": (
            "members must already have a positive price on signal date D; drop a date when "
            "valid members are below the configured minimum; never fill prices"
        ),
    }
