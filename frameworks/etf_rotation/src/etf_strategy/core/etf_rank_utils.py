"""Deterministic cross-sectional ranking for the ETF rotation project.

Factor scores can be algebraically equal while differing by one floating-point
representation bit (for example ``0.2`` and ``0.19999999999999998``).  Such
values are economic ties and must not acquire different ranks after a CSV or
Parquet round trip.  Quantisation is applied only at the ranking/selection
boundary; raw factor values remain unchanged for audit.

Quantisation is by SIGNIFICANT digits, not absolute decimal places.  ETF
group scores span many orders of magnitude across mechanisms -- an amount- or
illiquidity-denominated score can sit around 1e-11 while a return-denominated
score sits around 1e-1.  Absolute 12-decimal rounding (``round(x, 12)``)
collapses every distinct value below ~1e-11 into the same few grid points,
manufacturing false ties for small-magnitude candidates while leaving
larger-magnitude candidates untouched (2026-09-23: found via the monthly
factory's reproducibility gate on ``reverse_illiquidity_5``, whose score
median is 1.27e-11; absolute rounding produced false ties on 56% of
evaluation-window days).  Rounding to N significant digits scales the
precision with the value's own magnitude instead, so a value near 1e-11 keeps
the same 12 digits of resolution a value near 1e-1 gets.
"""
from __future__ import annotations

import pandas as pd


ETF_SCORE_SIGNIFICANT_DIGITS = 12


def _round_significant(value: float, significant_digits: int) -> float:
    if value != value:  # NaN
        return value
    return float(f"{value:.{significant_digits}g}")


def canonical_scores(
    values: pd.DataFrame, *, significant_digits: int = ETF_SCORE_SIGNIFICANT_DIGITS
) -> pd.DataFrame:
    """Return the canonical score representation used by every ETF rank gate."""
    if not isinstance(values, pd.DataFrame):
        raise TypeError("ETF scores must be a pandas DataFrame")
    if (
        isinstance(significant_digits, bool)
        or not isinstance(significant_digits, int)
        or significant_digits < 1
    ):
        raise ValueError("significant_digits must be a positive integer")
    floats = values.astype(float)
    return floats.map(lambda v: _round_significant(v, significant_digits))


def stable_rank(
    values: pd.DataFrame,
    *,
    pct: bool = False,
    significant_digits: int = ETF_SCORE_SIGNIFICANT_DIGITS,
) -> pd.DataFrame:
    """Rank canonical scores cross-sectionally with average ranks for ties."""
    return canonical_scores(values, significant_digits=significant_digits).rank(
        axis=1,
        pct=pct,
        method="average",
        na_option="keep",
    )


__all__ = ["ETF_SCORE_SIGNIFICANT_DIGITS", "canonical_scores", "stable_rank"]
