"""Family-first referee for ETF cross-sectional factor discovery."""
from __future__ import annotations

import numpy as np
import pandas as pd


def resolve_permutation_draws(
    configured_draws: int,
    alpha: float,
    *,
    multiplicity: int = 1,
    max_draws: int = 1_000_000,
) -> int:
    """Return a reachable Monte Carlo resolution after the sharpest Holm split.

    ``(exceed + 1) / (draws + 1)`` has a hard floor.  A generation whose alpha
    is below that floor could never pass, even with an observed zero exceedance.
    Increase the configured draw count deterministically and fail clearly when
    the requested resolution exceeds the bounded runtime budget.
    """
    if not np.isfinite(alpha) or alpha <= 0.0 or alpha >= 1.0:
        raise ValueError("alpha must be finite and in (0, 1)")
    if configured_draws < 1 or max_draws < 1 or multiplicity < 1:
        raise ValueError("permutation draw limits must be positive")
    required = int(np.floor(float(multiplicity) / float(alpha))) + 1
    draws = max(int(configured_draws), required)
    if draws > int(max_draws):
        raise ValueError(
            f"permutation resolution unreachable within max_draws={max_draws}: "
            f"alpha={alpha:.12g}, multiplicity={multiplicity} requires at least {required} draws"
        )
    return draws


def common_sample_spearman(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    min_pairs: int,
) -> tuple[pd.Series, pd.Series]:
    """Daily Spearman IC after intersecting signal/label validity.

    Ranking after the common mask is essential: independently ranked inputs
    are not a Spearman coefficient when their missing-name sets differ.
    """
    forward_return = forward_return.reindex_like(signal)
    eligible = eligibility.reindex_like(signal).fillna(False)
    common = (signal.replace([np.inf, -np.inf], np.nan).notna()
              & forward_return.replace([np.inf, -np.inf], np.nan).notna() & eligible)
    x = signal.where(common).rank(axis=1, method="average")
    y = forward_return.where(common).rank(axis=1, method="average")
    count = common.sum(axis=1).astype(int).rename("pair_count")
    xc = x.sub(x.mean(axis=1), axis=0)
    yc = y.sub(y.mean(axis=1), axis=0)
    numerator = (xc * yc).sum(axis=1, min_count=1)
    denominator = np.sqrt(
        xc.pow(2).sum(axis=1, min_count=1) * yc.pow(2).sum(axis=1, min_count=1)
    )
    ic = (numerator / denominator.replace(0.0, np.nan)).where(count >= min_pairs)
    return ic.rename("ic"), count


def timing_exposure_diagnostic(
    ic: pd.Series,
    basket_forward_return: pd.Series,
    discovery_end: str | pd.Timestamp,
) -> tuple[float, float]:
    """Report IC exposure to the forward basket without changing or gating IC."""
    pair = pd.concat(
        [ic.rename("ic"), basket_forward_return.rename("basket")], axis=1
    ).loc[:pd.Timestamp(discovery_end)].dropna()
    if len(pair) < 3 or float(pair["basket"].var(ddof=1)) <= 0.0:
        return np.nan, np.nan
    beta = float(pair["ic"].cov(pair["basket"]) / pair["basket"].var(ddof=1))
    corr = float(pair["ic"].corr(pair["basket"]))
    return beta, corr * corr


def block_means(values: pd.DataFrame, block_sessions: int) -> pd.DataFrame:
    """Non-overlapping calendar-row block means, retaining cross-factor dependence."""
    if block_sessions < 1:
        raise ValueError("block_sessions must be positive")
    rows = []
    for start in range(0, len(values), block_sessions):
        block = values.iloc[start : start + block_sessions]
        minimum = max(2, len(block) // 2)
        rows.append(block.mean(axis=0).where(block.count(axis=0) >= minimum))
    return pd.DataFrame(rows, columns=values.columns)


def maxstat_block_signflip(
    ic_matrix: pd.DataFrame,
    *,
    block_sessions: int = 20,
    draws: int = 2000,
    seed: int = 20260919,
) -> tuple[pd.Series, pd.Series]:
    """Family-wise max-|t| p-values via block Rademacher wild bootstrap."""
    blocks = block_means(ic_matrix, block_sessions)
    arr = blocks.to_numpy(dtype=float)
    valid = np.isfinite(arr)
    counts = valid.sum(axis=0)
    safe = np.where(valid, arr, 0.0)
    second_sum = np.square(safe).sum(axis=0)

    def _tstat(matrix: np.ndarray) -> np.ndarray:
        n = counts.astype(float)
        means = matrix.sum(axis=0) / np.maximum(n, 1.0)
        second = np.square(matrix).sum(axis=0) / np.maximum(n, 1.0)
        variance = np.maximum((second - means * means) * n / np.maximum(n - 1.0, 1.0), 0.0)
        se = np.sqrt(variance / np.maximum(n, 1.0))
        return np.divide(means, se, out=np.full_like(means, np.nan), where=(counts >= 4) & (se > 0))

    observed = _tstat(safe)
    rng = np.random.default_rng(seed)
    exceed = np.zeros(arr.shape[1], dtype=int)
    valid_draws = 0
    attempts = 0
    while valid_draws < int(draws):
        batch = min(512, int(draws) - valid_draws)
        attempts += batch
        if attempts > int(draws) * 10:
            raise ValueError("unable to produce enough finite max-stat bootstrap draws")
        signs = rng.choice(
            np.array([-1.0, 1.0]), size=(batch, arr.shape[0], 1)
        )
        signed_sum = (safe[None, :, :] * signs).sum(axis=1)
        n = counts.astype(float)[None, :]
        means = signed_sum / np.maximum(n, 1.0)
        second = second_sum[None, :] / np.maximum(n, 1.0)
        variance = np.maximum(
            (second - means * means) * n / np.maximum(n - 1.0, 1.0), 0.0
        )
        se = np.sqrt(variance / np.maximum(n, 1.0))
        null_t = np.divide(
            means,
            se,
            out=np.full_like(means, np.nan),
            where=(counts[None, :] >= 4) & (se > 0),
        )
        with np.errstate(all="ignore"):
            maxima = np.nanmax(np.abs(null_t), axis=1)
        finite_rows = np.isfinite(maxima)
        if not finite_rows.any():
            continue
        finite_maxima = maxima[finite_rows]
        exceed += np.sum(
            finite_maxima[:, None] >= np.abs(observed)[None, :], axis=0
        ).astype(int)
        valid_draws += int(len(finite_maxima))
    pvalue = (exceed + 1.0) / (float(valid_draws) + 1.0)
    pvalue[~np.isfinite(observed)] = np.nan
    return (
        pd.Series(observed, index=ic_matrix.columns, name="block_t"),
        pd.Series(pvalue, index=ic_matrix.columns, name="maxstat_pvalue"),
    )


def effective_test_count(ic_matrix: pd.DataFrame) -> float:
    """Participation ratio of the sign-aligned daily-IC correlation spectrum."""
    frame = ic_matrix.copy()
    signs = np.sign(frame.mean(axis=0)).replace(0.0, 1.0)
    frame = frame.mul(signs, axis=1)
    frame = frame.apply(lambda col: col.fillna(col.mean()), axis=0).dropna(axis=1, how="all")
    if frame.empty:
        return np.nan
    standardized = frame.sub(frame.mean()).div(frame.std(ddof=1).replace(0.0, np.nan)).fillna(0.0)
    singular = np.linalg.svd(standardized.to_numpy(dtype=float), compute_uv=False)
    eigenvalues = np.square(singular) / max(len(standardized) - 1, 1)
    denominator = float(np.square(eigenvalues).sum())
    return float(np.square(eigenvalues.sum()) / denominator) if denominator > 0 else np.nan
