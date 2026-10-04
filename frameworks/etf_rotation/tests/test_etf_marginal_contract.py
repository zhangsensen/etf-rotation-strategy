"""Contract tests for the diagnostic ETF residualizer.

All fixtures are synthetic and constructed in-process; no market data is read.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_marginal_ic import (
    DIAGNOSTIC_COLUMNS,
    STATUS_BASELINE_MEMBER,
    STATUS_EVALUATED,
    STATUS_INSUFFICIENT_PAIRS,
    STATUS_NO_RESIDUAL_VARIATION,
    STATUS_NOT_APPLICABLE,
    STATUS_NOT_ESTIMABLE,
    STATUS_OK,
    STATUS_RANK_DEFICIENT,
    residualize_scores,
    residualize_scores_diagnostic,
)

NAMES = list("ABCDEFGHIJ")


def _frame(rows: list[list[float]], periods: int | None = None) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=periods or len(rows), freq="D")
    return pd.DataFrame(rows, index=index, columns=NAMES, dtype=float)


def _informative_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(20260919)
    reference = _frame(rng.normal(size=(4, len(NAMES))).tolist())
    candidate = reference * 0.5 + _frame(rng.normal(size=(4, len(NAMES))).tolist())
    return candidate, reference


def test_empty_shelf_is_not_reported_as_success() -> None:
    candidate, _ = _informative_panel()
    residual, diagnostic, status = residualize_scores_diagnostic(candidate, {})

    assert status == STATUS_NOT_APPLICABLE
    assert status != STATUS_EVALUATED
    assert residual.isna().all().all()
    assert residual.shape == candidate.shape
    assert list(diagnostic.columns) == list(DIAGNOSTIC_COLUMNS)
    assert set(diagnostic["status"]) == {STATUS_NOT_APPLICABLE}

    # The legacy helper silently hands the raw candidate back, which is what a
    # caller could mistake for "marginal against an empty shelf".
    legacy = residualize_scores(candidate, {})
    pd.testing.assert_frame_equal(legacy, candidate)


def test_candidate_listed_as_its_own_reference_is_baseline_member() -> None:
    candidate, reference = _informative_panel()
    residual, diagnostic, status = residualize_scores_diagnostic(
        candidate,
        {"shelf_a": reference, "candidate_factor": candidate},
        candidate_name="candidate_factor",
    )
    assert status == STATUS_BASELINE_MEMBER
    assert residual.isna().all().all()
    assert set(diagnostic["status"]) == {STATUS_BASELINE_MEMBER}


def test_candidate_name_absent_from_references_is_evaluated_normally() -> None:
    candidate, reference = _informative_panel()
    _, _, status = residualize_scores_diagnostic(
        candidate, {"shelf_a": reference}, candidate_name="candidate_factor"
    )
    assert status == STATUS_EVALUATED


def test_exactly_collinear_controls_are_rejected_not_silently_solved() -> None:
    candidate, reference = _informative_panel()
    duplicate = reference.copy()
    affine = reference * 3.0 + 7.0  # rank-identical to `reference`

    residual, diagnostic, status = residualize_scores_diagnostic(
        candidate, {"shelf_a": reference, "shelf_b": duplicate, "shelf_c": affine}
    )
    assert status == STATUS_NOT_ESTIMABLE
    assert set(diagnostic["status"]) == {STATUS_RANK_DEFICIENT}
    assert residual.isna().all().all()
    assert (diagnostic["design_rank"] < 4).all()

    # numpy's lstsq would have returned a minimum-norm "answer" for the same
    # design without complaint.
    legacy = residualize_scores(
        candidate, {"shelf_a": reference, "shelf_b": duplicate, "shelf_c": affine}
    )
    assert legacy.notna().any().any()


def test_constant_candidate_has_no_residual_variation() -> None:
    _, reference = _informative_panel()
    constant = pd.DataFrame(
        4.0, index=reference.index, columns=reference.columns, dtype=float
    )
    residual, diagnostic, status = residualize_scores_diagnostic(
        constant, {"shelf_a": reference}
    )
    assert status == STATUS_NOT_ESTIMABLE
    assert set(diagnostic["status"]) == {STATUS_NO_RESIDUAL_VARIATION}
    assert residual.isna().all().all()


def test_candidate_that_is_an_affine_image_of_the_shelf_has_no_residual() -> None:
    _, reference = _informative_panel()
    candidate = reference * 3.0 + 7.0
    residual, diagnostic, status = residualize_scores_diagnostic(
        candidate, {"shelf_a": reference}
    )
    assert status == STATUS_NOT_ESTIMABLE
    assert set(diagnostic["status"]) == {STATUS_NO_RESIDUAL_VARIATION}
    assert residual.isna().all().all()


def test_min_pairs_floor_is_enforced_and_never_lowered() -> None:
    candidate, reference = _informative_panel()
    thin = candidate.copy()
    thin.iloc[0, 3:] = np.nan  # only three usable names on day 0
    residual, diagnostic, status = residualize_scores_diagnostic(
        thin, {"shelf_a": reference}, min_pairs=8
    )
    day0 = diagnostic.iloc[0]
    assert day0["status"] == STATUS_INSUFFICIENT_PAIRS
    assert int(day0["n_pairs"]) == 3
    assert residual.iloc[0].isna().all()
    assert status == STATUS_EVALUATED  # the remaining days are still usable


def test_missing_sample_is_reranked_on_the_common_names() -> None:
    """Ranks must be recomputed on the intersected names, not inherited."""
    candidate_values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    reference_values = [5.0, 1.0, 9.0, 2.0, 8.0, 3.0, 7.0, 4.0, 6.0, 0.0]
    candidate = _frame([candidate_values])
    reference = _frame([reference_values])
    candidate.iloc[0, 2] = np.nan  # drop C from the candidate
    reference.iloc[0, 7] = np.nan  # drop H from the reference

    residual, diagnostic, status = residualize_scores_diagnostic(
        candidate, {"shelf_a": reference}, min_pairs=8
    )
    assert status == STATUS_EVALUATED
    assert diagnostic.iloc[0]["status"] == STATUS_OK
    assert int(diagnostic.iloc[0]["n_pairs"]) == 8
    assert int(diagnostic.iloc[0]["design_rank"]) == 2
    assert np.isfinite(float(diagnostic.iloc[0]["condition_number"]))

    common = [name for name in NAMES if name not in {"C", "H"}]
    assert residual.loc[residual.index[0], ["C", "H"]].isna().all()

    # Independent expectation: rank both series *within the eight common names*
    # (average method, percentile) and fit y = a + b x by closed form.
    n = len(common)
    y = pd.Series(
        [candidate_values[NAMES.index(name)] for name in common], index=common
    ).rank(method="average") / n
    x = pd.Series(
        [reference_values[NAMES.index(name)] for name in common], index=common
    ).rank(method="average") / n
    beta = float(((x - x.mean()) * (y - y.mean())).sum() / ((x - x.mean()) ** 2).sum())
    alpha = float(y.mean() - beta * x.mean())
    expected = y - (alpha + beta * x)

    observed = residual.loc[residual.index[0], common].astype(float)
    np.testing.assert_allclose(observed.to_numpy(), expected.to_numpy(), atol=1e-12)

    # Ranking over all ten names first and only then intersecting is a different
    # (wrong) answer, so the assertion above really pins the rerank.
    stale_y = pd.Series(candidate_values, index=NAMES).rank(method="average") / len(NAMES)
    stale_x = pd.Series(reference_values, index=NAMES).rank(method="average") / len(NAMES)
    stale_y, stale_x = stale_y[common], stale_x[common]
    stale_beta = float(
        ((stale_x - stale_x.mean()) * (stale_y - stale_y.mean())).sum()
        / ((stale_x - stale_x.mean()) ** 2).sum()
    )
    stale = stale_y - (stale_y.mean() - stale_beta * stale_x.mean() + stale_beta * stale_x)
    assert not np.allclose(stale.to_numpy(), expected.to_numpy(), atol=1e-12)


def test_residual_for_a_date_depends_only_on_that_date_prefix_causality() -> None:
    candidate, reference = _informative_panel()
    full_residual, full_diag, full_status = residualize_scores_diagnostic(
        candidate, {"shelf_a": reference}
    )
    assert full_status == STATUS_EVALUATED

    for prefix in range(1, len(candidate.index) + 1):
        sliced_residual, sliced_diag, _ = residualize_scores_diagnostic(
            candidate.iloc[:prefix], {"shelf_a": reference.iloc[:prefix]}
        )
        pd.testing.assert_frame_equal(
            sliced_residual, full_residual.iloc[:prefix], check_freq=False
        )
        pd.testing.assert_frame_equal(
            sliced_diag.reset_index(drop=True),
            full_diag.iloc[:prefix].reset_index(drop=True),
        )

    # A later date changing cannot move an earlier residual.
    perturbed = candidate.copy()
    perturbed.iloc[-1] = perturbed.iloc[-1] * 100.0 + 5.0
    perturbed_residual, _, _ = residualize_scores_diagnostic(
        perturbed, {"shelf_a": reference}
    )
    pd.testing.assert_frame_equal(
        perturbed_residual.iloc[:-1], full_residual.iloc[:-1], check_freq=False
    )


def test_references_are_reindexed_onto_the_candidate_panel() -> None:
    candidate, reference = _informative_panel()
    shifted = reference.drop(columns=["J"])
    residual, diagnostic, status = residualize_scores_diagnostic(
        candidate, {"shelf_a": shifted}, min_pairs=8
    )
    assert status == STATUS_EVALUATED
    assert diagnostic["n_pairs"].eq(9).all()
    assert residual["J"].isna().all()


def test_nonfinite_reference_is_not_ranked_as_an_extreme():
    dates=pd.date_range('2024-01-01',periods=1)
    candidate=pd.DataFrame([[1,3,2,5,4,7,6,9,8]],index=dates)
    reference=pd.DataFrame([[4,1,5,2,6,3,8,7,np.inf]],index=dates)
    residual,diagnostic,status=residualize_scores_diagnostic(candidate,{'R':reference},min_pairs=8)
    assert diagnostic.n_pairs.iloc[0]==8
    assert pd.isna(residual.iloc[0,-1])
