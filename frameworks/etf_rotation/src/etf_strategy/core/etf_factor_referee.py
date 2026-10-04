"""ETF-only factor referee for relative rotation alpha."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def gpu_daily_rank_ic(
    signal_rank: pd.DataFrame,
    active_return_rank: pd.DataFrame,
    min_pairs: int,
) -> tuple[pd.Series, pd.Series]:
    """Compute daily rank correlation on CUDA with pairwise NaN masks."""
    import cupy as cp

    if not signal_rank.index.equals(active_return_rank.index):
        raise ValueError("signal and return dates must match")
    if list(signal_rank.columns) != list(active_return_rank.columns):
        raise ValueError("signal and return symbols must match")
    x = cp.asarray(signal_rank.to_numpy(dtype=np.float32))
    y = cp.asarray(active_return_rank.to_numpy(dtype=np.float32))
    valid = cp.isfinite(x) & cp.isfinite(y)
    n = valid.sum(axis=1).astype(cp.float32)
    x0 = cp.where(valid, x, 0.0)
    y0 = cp.where(valid, y, 0.0)
    sx, sy = x0.sum(axis=1), y0.sum(axis=1)
    safe_n = cp.maximum(n, 1.0)
    numerator = (x0 * y0).sum(axis=1) - sx * sy / safe_n
    vx = (x0 * x0).sum(axis=1) - sx * sx / safe_n
    vy = (y0 * y0).sum(axis=1) - sy * sy / safe_n
    denominator = cp.sqrt(cp.maximum(vx * vy, 0.0))
    corr = cp.where((n >= min_pairs) & (denominator > 0), numerator / denominator, cp.nan)
    return (
        pd.Series(cp.asnumpy(corr), index=signal_rank.index, name="ic"),
        pd.Series(cp.asnumpy(n).astype(int), index=signal_rank.index, name="pair_count"),
    )


def summarize_daily_ic(values: pd.Series) -> dict[str, float | int]:
    clean = values.dropna()
    if clean.empty:
        return {"days": 0, "mean_ic": np.nan, "icir_ann": np.nan}
    std = float(clean.std(ddof=1))
    return {
        "days": int(len(clean)),
        "mean_ic": float(clean.mean()),
        "icir_ann": float(clean.mean() / std * math.sqrt(252)) if std > 0 else np.nan,
    }


def rolling_direction_stability(
    values: pd.Series,
    direction: int,
    window: int = 180,
    step: int = 60,
) -> tuple[float, int]:
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or 1")
    signs = []
    for start in range(0, max(0, len(values) - window + 1), step):
        block = values.iloc[start : start + window].dropna()
        if len(block) >= window // 2:
            signs.append(np.sign(block.mean()))
    if not signs:
        return np.nan, 0
    return float(np.mean(np.asarray(signs) == direction)), len(signs)


def block_mean_pvalue(values: pd.Series, block_sessions: int = 60) -> tuple[float, int]:
    """Two-sided t-test over non-overlapping block means, not overlapping daily labels."""
    from scipy import stats

    clean = values.dropna().reset_index(drop=True)
    blocks = [
        float(clean.iloc[start : start + block_sessions].mean())
        for start in range(0, len(clean), block_sessions)
        if len(clean.iloc[start : start + block_sessions]) >= block_sessions // 2
    ]
    if len(blocks) < 4:
        return np.nan, len(blocks)
    result = stats.ttest_1samp(blocks, popmean=0.0, nan_policy="omit")
    return float(result.pvalue), len(blocks)


def holm_rejections(pvalues: pd.Series, alpha: float) -> pd.Series:
    """Holm-Bonferroni decisions over every generated expression."""
    result = pd.Series(False, index=pvalues.index)
    finite = pvalues.dropna().sort_values()
    total = len(finite)
    for rank, (index, pvalue) in enumerate(finite.items()):
        threshold = alpha / (total - rank)
        if pvalue > threshold:
            break
        result.loc[index] = True
    return result


def top_n_active_return(
    signal_rank: pd.DataFrame,
    active_return: pd.DataFrame,
    direction: int,
    top_n: int = 2,
) -> float:
    """Descriptive gross active return of daily Top-N selections."""
    signed = signal_rank * direction
    rows = []
    for date in signed.index:
        pair = pd.concat(
            [signed.loc[date].rename("signal"), active_return.loc[date].rename("active")],
            axis=1,
        ).dropna()
        if len(pair) >= top_n:
            rows.append(float(pair.nlargest(top_n, "signal")["active"].mean()))
    return float(np.mean(rows)) if rows else np.nan
