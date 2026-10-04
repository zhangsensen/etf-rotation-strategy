"""Time-series referee and family-aware Holm accounting for ETF regimes."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import math

import numpy as np
import pandas as pd
from scipy import stats


def non_overlapping(values: pd.Series, horizon: int, start: pd.Timestamp | None = None, end: pd.Timestamp | None = None) -> pd.Series:
    """Take every H-th label, resetting at each requested block boundary."""
    sliced = values.loc[start:end] if start is not None or end is not None else values
    sliced = sliced.dropna()
    if sliced.empty:
        return sliced
    return sliced.iloc[:: int(horizon)]


def robust_block_pvalue(values: pd.Series, *, block_size: int = 20) -> tuple[float, int, float]:
    """P-value on non-overlapping block means plus a median block effect."""
    clean = values.dropna().astype(float).reset_index(drop=True)
    blocks = [clean.iloc[i : i + block_size].mean() for i in range(0, len(clean), block_size) if len(clean.iloc[i : i + block_size]) >= block_size // 2]
    if len(blocks) < 4:
        return float("nan"), len(blocks), float("nan")
    pvalue = float(stats.ttest_1samp(np.asarray(blocks), 0.0, nan_policy="omit").pvalue)
    return pvalue, len(blocks), float(np.median(blocks))


def negative_effect_pvalue(values: pd.Series, *, block_size: int = 20) -> tuple[float, int, float]:
    """One-sided p-value for a signed effect being strictly below zero.

    The neutral block is a harm check.  It must reject only when the signed
    effect is statistically negative; a non-significant negative or positive
    estimate is therefore not presented as evidence of a gain or loss.
    """
    clean = values.dropna().astype(float).reset_index(drop=True)
    blocks = [
        clean.iloc[i : i + block_size].mean()
        for i in range(0, len(clean), block_size)
        if len(clean.iloc[i : i + block_size]) >= block_size // 2
    ]
    if len(blocks) < 4:
        return float("nan"), len(blocks), float("nan")
    result = stats.ttest_1samp(
        np.asarray(blocks), 0.0, nan_policy="omit", alternative="less"
    )
    return float(result.pvalue), len(blocks), float(np.median(blocks))


def directional_signature(
    horizon_block_means: Mapping[str, float],
    *,
    directional_blocks: Sequence[str],
    horizons: Sequence[int],
    min_signed_effect: float = 0.0,
) -> tuple[int, bool, dict[str, float]]:
    """Freeze direction from the predeclared directional cells only.

    The returned direction is a property of the six directional cells
    (two blocks x three horizons).  Neutral and diagnostic blocks cannot
    change the sign or rescue a failed directional gate.
    """
    cells = {
        f"{block}_h{int(horizon)}": float(
            horizon_block_means.get(f"{block}_h{int(horizon)}", np.nan)
        )
        for block in directional_blocks
        for horizon in horizons
    }
    finite = np.asarray(list(cells.values()), dtype=float)
    aggregate = float(np.nanmean(finite)) if np.isfinite(finite).any() else np.nan
    direction = 1 if np.isfinite(aggregate) and aggregate > 0.0 else -1
    signed = {key: value * direction for key, value in cells.items()}
    passed = bool(
        np.isfinite(finite).all()
        and np.isfinite(aggregate)
        and aggregate != 0.0
        and all(value > float(min_signed_effect) for value in signed.values())
    )
    return direction, passed, signed


def _simes(pvalues: pd.Series) -> float:
    finite = pvalues.dropna().sort_values().to_numpy(dtype=float)
    if not len(finite):
        return float("nan")
    ranks = np.arange(1, len(finite) + 1, dtype=float)
    return float(min(1.0, np.min(finite * len(finite) / ranks)))


def hierarchical_family_holm(
    pvalues: pd.Series,
    families: pd.Series,
    alpha: float,
    prior_attempts: pd.DataFrame | None = None,
) -> tuple[pd.Series, pd.DataFrame]:
    """Gate families first, then expressions, including every prior regime attempt.

    Family hypotheses use Simes p-values and Holm across all families.  A
    family that passes receives its Holm critical level for a second Holm test
    across every expression ever tried in that family.  Only current
    expression decisions are returned, while the table records the family
    accounting used by the campaign ledger.
    """
    current = pd.DataFrame({"pvalue": pvalues, "family": families, "current": True})
    frames = [current]
    if prior_attempts is not None and not prior_attempts.empty:
        required = {"pvalue", "family"}
        if not required <= set(prior_attempts):
            raise ValueError("prior_attempts must contain pvalue and family")
        prior = prior_attempts.loc[:, ["pvalue", "family"]].copy()
        prior.index = [f"prior:{i}" for i in range(len(prior))]
        prior["current"] = False
        frames.append(prior)
    attempts = pd.concat(frames, axis=0)
    family_pvalues = attempts.groupby("family", sort=True)["pvalue"].apply(_simes).sort_values()
    family_rows = []
    passed_families: dict[str, float] = {}
    total_families = len(family_pvalues)
    for rank, (family, family_pvalue) in enumerate(family_pvalues.items()):
        critical = alpha / max(total_families - rank, 1)
        passed = bool(np.isfinite(family_pvalue) and family_pvalue <= critical)
        family_rows.append(
            {
                "family": family,
                "family_pvalue": family_pvalue,
                "holm_critical": critical,
                "attempts": int((attempts.family == family).sum()),
                "family_pass": passed,
            }
        )
        if not passed:
            break
        passed_families[str(family)] = critical
    decided = {row["family"] for row in family_rows}
    for family, family_pvalue in family_pvalues.items():
        if family not in decided:
            family_rows.append(
                {
                    "family": family,
                    "family_pvalue": family_pvalue,
                    "holm_critical": np.nan,
                    "attempts": int((attempts.family == family).sum()),
                    "family_pass": False,
                }
            )

    expression_pass = pd.Series(False, index=pvalues.index)
    for family, family_alpha in passed_families.items():
        group = attempts.loc[attempts.family.eq(family), "pvalue"].dropna().sort_values()
        total = len(group)
        passed_indices = []
        for rank, (index, pvalue) in enumerate(group.items()):
            if pvalue <= family_alpha / max(total - rank, 1):
                passed_indices.append(index)
            else:
                break
        for index in passed_indices:
            if index in expression_pass.index:
                expression_pass.loc[index] = True
    table = pd.DataFrame(family_rows).sort_values("family").reset_index(drop=True)
    return expression_pass, table


def summarize_blocks(signal: pd.Series, labels: Mapping[int, pd.DataFrame], horizons: Sequence[int], blocks: Mapping[str, tuple[str, str]], direction: int) -> dict[str, object]:
    block_values: dict[str, float] = {}
    for block, (start, end) in blocks.items():
        vals = []
        for horizon in horizons:
            frame = labels[int(horizon)].set_index("signal_date")
            series = frame["basket_spread"].reindex(signal.index).mul(direction)
            sampled = non_overlapping(series, int(horizon), pd.Timestamp(start), pd.Timestamp(end))
            vals.append(float(sampled.mean()) if not sampled.empty else float("nan"))
        block_values[block] = float(np.nanmean(vals)) if np.isfinite(vals).any() else float("nan")
    return block_values


# ---------------------------------------------------------------------------
# Referee v2 (2026-09-18): block t-tests instead of six-cell sign agreement;
# multiple testing across the current generation only.  Calibrated with a
# planted-signal positive control and a block-shuffled null control.
# ---------------------------------------------------------------------------


def signed_block_ttest(
    signal: pd.Series,
    label: pd.Series,
    *,
    horizon: int,
    block: tuple[str, str],
    direction: int,
    block_size: int = 10,
) -> tuple[float, float, int]:
    """One-sided block t-test that direction * signal * label is positive.

    Non-overlapping labels are taken inside the block, then aggregated into
    block means so overlapping horizons do not inflate the sample size.
    """
    pair = pd.concat([signal.rename("s"), label.rename("y")], axis=1).dropna()
    pair = pair.loc[pd.Timestamp(block[0]) : pd.Timestamp(block[1])].iloc[:: int(horizon)]
    signed = (pair["s"] * pair["y"] * int(direction)).reset_index(drop=True)
    blocks = [
        float(signed.iloc[i : i + block_size].mean())
        for i in range(0, len(signed), block_size)
        if len(signed.iloc[i : i + block_size]) >= block_size // 2
    ]
    if len(blocks) < 3:
        return float("nan"), float("nan"), len(blocks)
    result = stats.ttest_1samp(np.asarray(blocks), 0.0, alternative="greater")
    return float(np.mean(blocks)), float(result.pvalue), len(blocks)


def directional_block_gate(
    signal: pd.Series,
    label: pd.Series,
    *,
    horizon: int,
    directional_blocks: Mapping[str, tuple[str, str]],
    block_alpha: float,
) -> tuple[int, bool, dict[str, float]]:
    """Freeze direction from pooled directional blocks, then require every
    directional block to reject "no effect" one-sided at block_alpha."""
    pooled = []
    for block in directional_blocks.values():
        pair = pd.concat([signal.rename("s"), label.rename("y")], axis=1).dropna()
        pair = pair.loc[pd.Timestamp(block[0]) : pd.Timestamp(block[1])].iloc[:: int(horizon)]
        pooled.append(pair["s"] * pair["y"])
    pooled_mean = float(pd.concat(pooled).mean()) if pooled else float("nan")
    direction = 1 if np.isfinite(pooled_mean) and pooled_mean > 0 else -1
    cells: dict[str, float] = {}
    passed = True
    for name, block in directional_blocks.items():
        mean, pvalue, count = signed_block_ttest(
            signal, label, horizon=horizon, block=block, direction=direction
        )
        cells[f"{name}_signed_mean"] = mean
        cells[f"{name}_pvalue"] = pvalue
        cells[f"{name}_blocks"] = count
        passed = passed and bool(np.isfinite(pvalue) and pvalue < block_alpha and mean > 0)
    return direction, passed, cells


def generation_family_holm(
    pvalues: pd.Series, families: pd.Series, alpha: float
) -> tuple[pd.Series, pd.DataFrame]:
    """Simes per family, Holm across this generation's families, then Holm
    within each passing family over this generation's expressions only.
    Prior generations stay in the ledger as a record, not in the denominator."""
    return hierarchical_family_holm(pvalues, families, alpha, prior_attempts=None)
