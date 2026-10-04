"""Cross-sectional residualization against already admitted ETF factors."""
from __future__ import annotations

from collections.abc import Mapping
import numpy as np
import pandas as pd

DIAGNOSTIC_COLUMNS = ("date", "n_pairs", "design_rank", "condition_number", "status")

STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
STATUS_BASELINE_MEMBER = "BASELINE_MEMBER"
STATUS_INSUFFICIENT_PAIRS = "INSUFFICIENT_PAIRS"
STATUS_INSUFFICIENT_DOF = "INSUFFICIENT_DOF"
STATUS_RANK_DEFICIENT = "RANK_DEFICIENT"
STATUS_NO_RESIDUAL_VARIATION = "NO_RESIDUAL_VARIATION"
STATUS_OK = "OK"
STATUS_EVALUATED = "EVALUATED"
STATUS_NOT_ESTIMABLE = "NOT_ESTIMABLE"

_EPS = float(np.finfo(float).eps)


def residualize_scores(
    candidate: pd.DataFrame,
    admitted: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Legacy residualizer.

    Returns the candidate unchanged when ``admitted`` is empty, which a caller
    can mistake for "residual survives an empty shelf". Kept byte-for-byte for
    existing callers; new gates must use :func:`residualize_scores_diagnostic`.
    """
    if not admitted:
        return candidate.copy()
    result = pd.DataFrame(np.nan, index=candidate.index, columns=candidate.columns)
    for date in candidate.index:
        columns = [candidate.loc[date].rename("candidate")]
        columns.extend(frame.reindex_like(candidate).loc[date].rename(name) for name, frame in admitted.items())
        pair = pd.concat(columns, axis=1).dropna()
        if len(pair) <= len(admitted) + 2:
            continue
        x = pair[list(admitted)].to_numpy(dtype=float)
        x = np.column_stack([np.ones(len(x)), x])
        y = pair["candidate"].to_numpy(dtype=float)
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        result.loc[date, pair.index] = y - x @ beta
    return result


def _empty_residual(candidate: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(np.nan, index=candidate.index, columns=candidate.columns, dtype=float)


def _flat_diagnostic(candidate: pd.DataFrame, status: str) -> pd.DataFrame:
    rows = [
        {
            "date": date,
            "n_pairs": int(candidate.loc[date].notna().sum()),
            "design_rank": 0,
            "condition_number": np.nan,
            "status": status,
        }
        for date in candidate.index
    ]
    return pd.DataFrame(rows, columns=list(DIAGNOSTIC_COLUMNS))


def residualize_scores_diagnostic(
    candidate: pd.DataFrame,
    references: Mapping[str, pd.DataFrame],
    *,
    candidate_name: str | None = None,
    min_pairs: int = 8,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Residualize a candidate against reference scores, reporting estimability.

    ``references`` maps reference name -> score frame. Returns
    ``(residual, diagnostic, global_status)``.

    The contract differs from :func:`residualize_scores` in the cases that
    matter for a gate:

    * empty ``references`` -> all-NaN residual and ``NOT_APPLICABLE``. There is
      no baseline to be marginal to, so nothing has been demonstrated; this is
      explicitly **not** a pass.
    * ``candidate_name`` already in ``references`` -> all-NaN residual and
      ``BASELINE_MEMBER``. A factor cannot be marginal to itself.

    Otherwise, per date: intersect the finite names of the candidate and every
    reference, re-rank *every* series (average method, percentile) on exactly
    that common name set, prepend an intercept, and solve least squares. A date
    is only used when it has at least ``min_pairs`` names, the design matrix has
    full column rank and a finite condition number, residual degrees of freedom
    ``n - rank >= 2``, and the candidate and its residual actually vary.

    Rank and conditioning use the standard singular-value tolerance
    ``max(shape) * s_max * eps`` and variation uses ``eps`` scaled by the data's
    own magnitude, so no threshold is tuned against observed data.

    ``diagnostic`` carries one row per date with columns
    ``date, n_pairs, design_rank, condition_number, status``. ``global_status``
    is ``EVALUATED`` when at least one date produced a finite residual, and
    ``NOT_ESTIMABLE`` when none did.
    """
    if not isinstance(min_pairs, int) or min_pairs < 1:
        raise ValueError('min_pairs must be a positive integer')
    if '__candidate__' in references:
        raise ValueError('__candidate__ is reserved for the candidate score')
    if not references:
        return (
            _empty_residual(candidate),
            _flat_diagnostic(candidate, STATUS_NOT_APPLICABLE),
            STATUS_NOT_APPLICABLE,
        )
    if candidate_name is not None and candidate_name in references:
        return (
            _empty_residual(candidate),
            _flat_diagnostic(candidate, STATUS_BASELINE_MEMBER),
            STATUS_BASELINE_MEMBER,
        )

    names = list(references)
    aligned = {
        name: pd.DataFrame(frame).reindex(
            index=candidate.index, columns=candidate.columns
        )
        for name, frame in references.items()
    }
    residual = _empty_residual(candidate)
    rows: list[dict[str, object]] = []
    usable = False

    for date in candidate.index:
        frame = pd.concat(
            [candidate.loc[date].rename("__candidate__")]
            + [aligned[name].loc[date].rename(name) for name in names],
            axis=1,
        ).replace([np.inf, -np.inf], np.nan).dropna()
        n_pairs = int(len(frame))
        if n_pairs < int(min_pairs):
            rows.append(
                {
                    "date": date,
                    "n_pairs": n_pairs,
                    "design_rank": 0,
                    "condition_number": np.nan,
                    "status": STATUS_INSUFFICIENT_PAIRS,
                }
            )
            continue

        ranked = frame.rank(axis=0, method="average", pct=True)
        y = ranked["__candidate__"].to_numpy(dtype=float)
        design = np.column_stack(
            [np.ones(n_pairs)] + [ranked[name].to_numpy(dtype=float) for name in names]
        )
        singular = np.linalg.svd(design, compute_uv=False)
        tolerance = max(design.shape) * float(singular[0]) * _EPS
        design_rank = int(np.count_nonzero(singular > tolerance))
        smallest = float(singular[-1])
        condition = (
            float(singular[0]) / smallest if smallest > tolerance else float(np.inf)
        )

        def record(status: str) -> None:
            rows.append(
                {
                    "date": date,
                    "n_pairs": n_pairs,
                    "design_rank": design_rank,
                    "condition_number": condition,
                    "status": status,
                }
            )

        if design_rank < design.shape[1] or not np.isfinite(condition):
            record(STATUS_RANK_DEFICIENT)
            continue
        if n_pairs - design_rank < 2:
            record(STATUS_INSUFFICIENT_DOF)
            continue

        candidate_scale = max(1.0, float(np.max(np.abs(y))))
        if float(np.ptp(y)) <= _EPS * candidate_scale * n_pairs:
            record(STATUS_NO_RESIDUAL_VARIATION)
            continue

        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        values = y - design @ beta
        if not np.all(np.isfinite(values)):
            record(STATUS_RANK_DEFICIENT)
            continue
        if float(np.ptp(values)) <= _EPS * candidate_scale * n_pairs:
            record(STATUS_NO_RESIDUAL_VARIATION)
            continue

        residual.loc[date, frame.index] = values
        usable = True
        record(STATUS_OK)

    diagnostic = pd.DataFrame(rows, columns=list(DIAGNOSTIC_COLUMNS))
    return residual, diagnostic, STATUS_EVALUATED if usable else STATUS_NOT_ESTIMABLE
