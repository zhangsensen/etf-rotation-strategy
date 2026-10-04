"""ETF-only typed rank grammar; contains no stock factor registry or stock referee."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable, Mapping

import pandas as pd

from .etf_rank_utils import stable_rank


ETF_RESEARCH_DOMAIN = "etf_rotation"
ALLOWED_OPERATORS = {"atomic", "rank_mean", "rank_spread", "rank_interaction"}


@dataclass(frozen=True, order=True)
class AtomSpec:
    name: str
    family: str


@dataclass(frozen=True, order=True)
class ExpressionSpec:
    operator: str
    left: str
    right: str | None = None
    family: str = ""

    @property
    def expression_id(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()[:20]

    @property
    def readable(self) -> str:
        if self.operator == "atomic":
            return self.left
        symbol = {"rank_mean": "+", "rank_spread": "-", "rank_interaction": "*"}[
            self.operator
        ]
        return f"rank({self.left}) {symbol} rank({self.right})"


def parse_atoms(raw_atoms: Iterable[Mapping[str, str]]) -> list[AtomSpec]:
    atoms = [AtomSpec(name=str(row["name"]), family=str(row["family"])) for row in raw_atoms]
    if not atoms or len(atoms) != len(set(atoms)):
        raise ValueError("ETF atom registry must be non-empty and unique")
    names = [atom.name for atom in atoms]
    if len(names) != len(set(names)):
        raise ValueError("ETF atom names must be unique")
    return sorted(atoms)


def enumerate_expressions(
    atoms: Iterable[AtomSpec],
    operators: Iterable[str],
    pair_policy: str = "cross_family_only",
) -> list[ExpressionSpec]:
    """Deterministically enumerate a bounded ETF expression space."""
    atom_list = sorted(atoms)
    operator_set = set(operators)
    unknown = operator_set - ALLOWED_OPERATORS
    if unknown:
        raise ValueError(f"Unsupported ETF grammar operators: {sorted(unknown)}")
    if pair_policy != "cross_family_only":
        raise ValueError("Only cross_family_only is supported in ETF grammar v1")

    expressions: list[ExpressionSpec] = []
    if "atomic" in operator_set:
        expressions.extend(
            ExpressionSpec("atomic", atom.name, family=atom.family) for atom in atom_list
        )
    pair_operators = sorted(operator_set - {"atomic"})
    for index, left in enumerate(atom_list):
        for right in atom_list[index + 1 :]:
            if left.family == right.family:
                continue
            family = "+".join(sorted((left.family, right.family)))
            for operator in pair_operators:
                expressions.append(ExpressionSpec(operator, left.name, right.name, family))
    return sorted(expressions, key=lambda item: item.expression_id)


def materialize_expression(
    expression: ExpressionSpec,
    ranked_atoms: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Materialize one dimensionless rank expression without outcome access."""
    if expression.left not in ranked_atoms:
        raise KeyError(expression.left)
    left = ranked_atoms[expression.left]
    if expression.operator == "atomic":
        return left.copy()
    if expression.right is None or expression.right not in ranked_atoms:
        raise KeyError(expression.right)
    right = ranked_atoms[expression.right].reindex_like(left)
    if expression.operator == "rank_mean":
        return (left + right) / 2.0
    if expression.operator == "rank_spread":
        return left - right
    if expression.operator == "rank_interaction":
        return (left - 0.5) * (right - 0.5)
    raise ValueError(f"Unsupported operator: {expression.operator}")


def build_pit_eligibility(
    ohlcv: Mapping[str, pd.DataFrame],
    min_history_sessions: int,
    require_positive_volume: bool = True,
) -> pd.DataFrame:
    """Eligibility known on D; never uses future existence or future liquidity."""
    if min_history_sessions < 1:
        raise ValueError("min_history_sessions must be positive")
    close = ohlcv["close"]
    observed = close.notna().cumsum() >= min_history_sessions
    current = close.notna()
    for field in ("open", "high", "low"):
        current &= ohlcv[field].reindex_like(close).notna()
    if require_positive_volume:
        volume = ohlcv["volume"].reindex_like(close)
        current &= volume.gt(0) & volume.notna()
    return observed & current


def cross_sectional_rank(
    values: pd.DataFrame,
    eligibility: pd.DataFrame,
) -> pd.DataFrame:
    masked = values.where(eligibility.reindex_like(values).fillna(False))
    return stable_rank(masked, pct=True)


def active_forward_return(
    open_prices: pd.DataFrame,
    eligibility: pd.DataFrame,
    horizon: int,
    entry_lag: int,
) -> pd.DataFrame:
    """Future ETF return minus same-day eligible-pool EW return."""
    if horizon <= 0 or entry_lag <= 0:
        raise ValueError("horizon and entry_lag must be positive")
    entry = open_prices.shift(-entry_lag)
    exit_price = open_prices.shift(-(entry_lag + horizon))
    raw = (exit_price / entry - 1.0).where((entry > 0) & (exit_price > 0))
    eligible_raw = raw.where(eligibility.reindex_like(raw).fillna(False))
    benchmark = eligible_raw.mean(axis=1, skipna=True)
    return eligible_raw.sub(benchmark, axis=0)


def expression_source_is_etf_only() -> bool:
    """Machine-readable boundary used by manifests and regression tests."""
    return ETF_RESEARCH_DOMAIN == "etf_rotation"
