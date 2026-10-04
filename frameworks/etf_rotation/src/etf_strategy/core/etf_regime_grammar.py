"""Independent, typed time-series grammar for ETF regime states (v4 ATTACK)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping, Sequence

import pandas as pd


@dataclass(frozen=True, order=True)
class RegimeExpression:
    operator: str
    left: str
    right: str | None
    family: str

    @property
    def expression_id(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:20]

    @property
    def readable(self) -> str:
        if self.operator == "atomic":
            return self.left
        symbol = {"sum": "+", "spread": "-", "interaction": "*"}[self.operator]
        return f"z({self.left}) {symbol} z({self.right})"


def enumerate_regime_expressions(atoms: Sequence[object], operators: Sequence[str], pair_policy: str) -> list[RegimeExpression]:
    allowed = {"atomic", "sum", "spread", "interaction"}
    if set(operators) - allowed or pair_policy != "cross_family_only":
        raise ValueError("unsupported ETF regime grammar v4")
    ordered = sorted(atoms)
    expressions = [RegimeExpression("atomic", a.name, None, a.family) for a in ordered if "atomic" in operators]
    for i, left in enumerate(ordered):
        for right in ordered[i + 1 :]:
            if left.family == right.family:
                continue
            family = "+".join(sorted((left.family, right.family)))
            expressions.extend(RegimeExpression(op, left.name, right.name, family) for op in sorted(set(operators) - {"atomic"}))
    return sorted(expressions, key=lambda expr: expr.expression_id)


def materialize_regime_expression(expression: RegimeExpression, states: Mapping[str, pd.Series]) -> pd.Series:
    left = states[expression.left]
    if expression.operator == "atomic":
        return left
    right = states[expression.right]
    if expression.operator == "sum":
        return left + right
    if expression.operator == "spread":
        return left - right
    if expression.operator == "interaction":
        return left * right
    raise ValueError(expression.operator)
