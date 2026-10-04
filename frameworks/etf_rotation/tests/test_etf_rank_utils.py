"""Synthetic-only tests for the canonical ETF ranking boundary."""
from io import StringIO

import pandas as pd
import pytest

from etf_strategy.core.etf_mining_referee import fractional_topk_weights
from etf_strategy.core.etf_rank_utils import canonical_scores, stable_rank


def test_binary_float_aliases_are_average_ranked_as_ties():
    scores = pd.DataFrame([[0.2, 0.19999999999999998, 0.1]], columns=list("abc"))
    ranks = stable_rank(scores)
    assert ranks.loc[0, "a"] == ranks.loc[0, "b"] == 2.5


def test_csv_round_trip_cannot_change_canonical_ranks():
    scores = pd.DataFrame(
        [[0.2, 0.19999999999999998, 1 / 3], [0.4, 0.4 + 4e-15, -0.1]],
        index=pd.to_datetime(["2026-01-02", "2026-01-05"]),
        columns=list("abc"),
    )
    encoded = scores.to_csv(float_format="%.17g")
    restored = pd.read_csv(StringIO(encoded), index_col=0, parse_dates=True)
    pd.testing.assert_frame_equal(stable_rank(scores), stable_rank(restored))
    pd.testing.assert_frame_equal(canonical_scores(scores), canonical_scores(restored))


def test_topk_selection_uses_the_same_canonical_ties():
    scores = pd.DataFrame([[0.2, 0.19999999999999998, 0.1]], columns=list("abc"))
    weights = fractional_topk_weights(scores, 1, min_names=3)
    assert weights.loc[0].to_dict() == {"a": 0.5, "b": 0.5, "c": 0.0}


# --- 2026-09-23: significant-digit rounding regression tests -----------
# Absolute 12-decimal rounding manufactured false ties for small-magnitude
# scores (e.g. illiquidity-family candidates ~1e-11); fixed by rounding to
# 12 significant digits instead. These tests pin the fix's exact boundary.

def test_binary_float_aliases_still_tie_under_significant_digit_rounding():
    scores = pd.DataFrame([[0.2, 0.19999999999999998, 0.1]], columns=list("abc"))
    ranks = stable_rank(scores)
    assert ranks.loc[0, "a"] == ranks.loc[0, "b"] == 2.5


def test_small_magnitude_scores_are_not_falsely_tied():
    # These previously collapsed to the same value under round(x, 12).
    scores = pd.DataFrame([[1.1e-11, 1.2e-11, 1.3e-11]], columns=list("abc"))
    canonical = canonical_scores(scores)
    assert canonical.loc[0].nunique() == 3
    ranks = stable_rank(scores)
    assert ranks.loc[0].tolist() == [1.0, 2.0, 3.0]


def test_zero_negative_and_nan_are_handled():
    scores = pd.DataFrame([[0.0, -1.23456789012345e-3, float("nan"), 5.0]], columns=list("abcd"))
    canonical = canonical_scores(scores)
    assert canonical.loc[0, "a"] == 0.0
    assert canonical.loc[0, "b"] == pytest.approx(-1.23456789012e-3)
    assert pd.isna(canonical.loc[0, "c"])
    ranks = stable_rank(scores)
    assert pd.isna(ranks.loc[0, "c"])
    assert ranks.loc[0, "b"] < ranks.loc[0, "a"] < ranks.loc[0, "d"]


def test_canonical_scores_rejects_non_positive_significant_digits():
    scores = pd.DataFrame([[1.0, 2.0]], columns=list("ab"))
    with pytest.raises(ValueError, match="significant_digits"):
        canonical_scores(scores, significant_digits=0)
