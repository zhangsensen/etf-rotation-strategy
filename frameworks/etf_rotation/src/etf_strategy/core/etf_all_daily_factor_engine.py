"""Frozen-candidate referee for broad point-in-time ETF daily factors.

This module deliberately contains no candidate-generation logic.  Candidate
formulas and signs are inputs fixed before the forward surface is acquired.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

from .etf_factor_grammar import cross_sectional_rank
from .etf_family_referee import common_sample_spearman
from .etf_marginal_ic import STATUS_EVALUATED, residualize_scores_diagnostic
from .etf_mining_referee import (
    campaign_bonferroni_pass,
    fractional_topk_weights,
    newey_west_t_calendar,
    purge_by_exit,
)


@dataclass(frozen=True)
class ForwardGates:
    campaign_budget: int
    alpha: float
    min_names: int
    min_days: int
    min_signed_mean_ic: float
    min_hac_t: float
    top_fraction: float
    min_top_label_coverage: float
    min_top_excess_bp: float
    min_top_excess_hac_t: float
    max_abs_rank_corr: float
    min_residual_mean_ic: float
    min_residual_hac_t: float

    def validate(self) -> None:
        if self.campaign_budget < 1 or self.min_names < 10 or self.min_days < 1:
            raise ValueError("campaign budget, names and days must be positive")
        if (
            not 0.0 < self.alpha < 1.0
            or not 0.0 < self.top_fraction < 1.0
            or not 0.0 < self.min_top_label_coverage <= 1.0
        ):
            raise ValueError("alpha, top_fraction and label coverage must be in (0, 1]")
        if not 0.0 <= self.max_abs_rank_corr <= 1.0:
            raise ValueError("max_abs_rank_corr must be in [0, 1]")


def compose_candidate(
    spec: Mapping[str, object],
    atoms: Mapping[str, pd.DataFrame],
    eligibility: pd.DataFrame,
) -> pd.DataFrame:
    """Materialize a frozen atomic or rank-spread expression."""
    operator = str(spec["operator"])
    left = str(dict(spec["left"])["name"])
    if left not in atoms:
        raise ValueError(f"candidate atom is unavailable: {left}")
    if operator == "atomic":
        return atoms[left].reindex_like(eligibility).where(eligibility)
    if operator != "rank_spread":
        raise ValueError(f"unsupported frozen operator: {operator}")
    right = str(dict(spec["right"])["name"])
    if right not in atoms:
        raise ValueError(f"candidate atom is unavailable: {right}")
    spread = atoms[left].reindex_like(eligibility) - atoms[right].reindex_like(eligibility)
    return cross_sectional_rank(spread, eligibility).astype("float32")


def surface_stats(
    series: pd.Series,
    *,
    start: str,
    end: str,
    calendar: pd.Index,
    exit_offset: int,
    hac_lag: int,
) -> dict[str, float | int]:
    window = series.loc[pd.Timestamp(start):pd.Timestamp(end)]
    window = purge_by_exit(window, calendar, pd.Timestamp(end), exit_offset)
    clean = window.dropna()
    return {
        "days": int(len(clean)),
        "mean": float(clean.mean()) if len(clean) else float("nan"),
        "hac_t": float(newey_west_t_calendar(window, calendar, hac_lag)),
    }


def top_fraction_excess(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    *,
    direction: int,
    fraction: float,
    min_names: int,
    min_label_coverage: float,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """D-known top-fraction excess with fail-closed missing-label handling.

    Selection never sees label availability.  A day below the declared label
    coverage is dropped.  Otherwise missing returns are assigned zero to both
    the selected sleeve and equal-weight benchmark; they never trigger
    replacement by a lower-ranked name.
    """
    if direction not in (-1, 1) or not 0.0 < fraction < 1.0:
        raise ValueError("direction must be +/-1 and fraction must be in (0,1)")
    score = (signal * float(direction)).where(eligibility)
    label = forward_return.reindex_like(score).where(eligibility)
    excess = pd.Series(np.nan, index=score.index, name="top_fraction_excess")
    selected_count = pd.Series(0, index=score.index, dtype=int, name="selected_count")
    label_coverage = pd.Series(np.nan, index=score.index, name="label_coverage")
    for date in score.index:
        known = score.loc[date].replace([np.inf, -np.inf], np.nan).dropna()
        n = int(len(known))
        if n < min_names:
            continue
        # Label availability is a future fact and is never allowed to alter
        # the selected names.
        outcome = label.loc[date, known.index].replace([np.inf, -np.inf], np.nan)
        coverage = float(outcome.notna().mean())
        label_coverage.loc[date] = coverage
        if coverage < min_label_coverage:
            continue
        k = max(1, int(np.ceil(n * fraction)))
        one_row = pd.DataFrame([known], index=[date])
        weights = fractional_topk_weights(one_row, k, min_names=n).iloc[0]
        conservative = outcome.fillna(0.0)
        excess.loc[date] = float((conservative * weights).sum() / k - conservative.mean())
        selected_count.loc[date] = k
    return excess, selected_count, label_coverage


def mean_abs_daily_rank_corr(
    left: pd.DataFrame,
    right: pd.DataFrame,
    eligibility: pd.DataFrame,
    *,
    min_names: int,
    start: str,
    end: str,
) -> float:
    daily, _ = common_sample_spearman(left, right, eligibility, min_names)
    clean = daily.loc[pd.Timestamp(start):pd.Timestamp(end)].dropna()
    return float(clean.abs().mean()) if len(clean) else float("nan")


def evaluate_forward_candidate(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    references: Mapping[str, pd.DataFrame],
    *,
    candidate_id: str,
    direction: int,
    start: str,
    end: str,
    calendar: pd.Index,
    entry_lag: int,
    horizon: int,
    gates: ForwardGates,
) -> tuple[dict[str, object], pd.DataFrame]:
    """Apply the frozen forward gates, excluding sequential redundancy."""
    gates.validate()
    if direction not in (-1, 1):
        raise ValueError("candidate direction must be frozen to +/-1")
    signed_signal = signal * float(direction)
    ic, pair_count = common_sample_spearman(
        signed_signal, forward_return, eligibility, gates.min_names
    )
    stats = surface_stats(
        ic,
        start=start,
        end=end,
        calendar=calendar,
        exit_offset=entry_lag + horizon,
        hac_lag=horizon - 1,
    )
    campaign_pass, pvalue = campaign_bonferroni_pass(
        float(stats["hac_t"]), alpha=gates.alpha, hypothesis_budget=gates.campaign_budget
    )
    top, selected_count, label_coverage = top_fraction_excess(
        signal,
        forward_return,
        eligibility,
        direction=direction,
        fraction=gates.top_fraction,
        min_names=gates.min_names,
        min_label_coverage=gates.min_top_label_coverage,
    )
    top_stats = surface_stats(
        top,
        start=start,
        end=end,
        calendar=calendar,
        exit_offset=entry_lag + horizon,
        hac_lag=horizon - 1,
    )
    residual, diagnostics, residual_status = residualize_scores_diagnostic(
        signed_signal,
        references,
        candidate_name=candidate_id,
        min_pairs=gates.min_names,
    )
    residual_ic, _ = common_sample_spearman(
        residual, forward_return, eligibility, gates.min_names
    )
    residual_stats = surface_stats(
        residual_ic,
        start=start,
        end=end,
        calendar=calendar,
        exit_offset=entry_lag + horizon,
        hac_lag=horizon - 1,
    )
    failures: list[str] = []
    if stats["days"] < gates.min_days:
        failures.append("forward_days")
    if not np.isfinite(stats["mean"]) or stats["mean"] < gates.min_signed_mean_ic:
        failures.append("forward_mean_ic")
    if not np.isfinite(stats["hac_t"]) or stats["hac_t"] < gates.min_hac_t:
        failures.append("forward_hac_t")
    if not campaign_pass:
        failures.append("campaign_bonferroni")
    if top_stats["days"] < gates.min_days:
        failures.append("top_excess_days")
    if not np.isfinite(top_stats["mean"]) or top_stats["mean"] * 1e4 < gates.min_top_excess_bp:
        failures.append("top_excess_mean")
    if not np.isfinite(top_stats["hac_t"]) or top_stats["hac_t"] < gates.min_top_excess_hac_t:
        failures.append("top_excess_hac_t")
    if residual_status != STATUS_EVALUATED:
        failures.append(f"residual_{residual_status.lower()}")
    if residual_stats["days"] < gates.min_days:
        failures.append("residual_days")
    if not np.isfinite(residual_stats["mean"]) or residual_stats["mean"] < gates.min_residual_mean_ic:
        failures.append("residual_mean_ic")
    if not np.isfinite(residual_stats["hac_t"]) or residual_stats["hac_t"] < gates.min_residual_hac_t:
        failures.append("residual_hac_t")
    row: dict[str, object] = {
        "candidate_id": candidate_id,
        "expected_sign": direction,
        "forward_days": stats["days"],
        "forward_mean_ic": stats["mean"],
        "forward_hac_t": stats["hac_t"],
        "forward_one_sided_p": pvalue,
        "campaign_bonferroni_pass": campaign_pass,
        "forward_median_pair_count": float(
            pair_count.loc[pd.Timestamp(start):pd.Timestamp(end)].median(skipna=True)
        ),
        "top_excess_days": top_stats["days"],
        "top_excess_bp": float(top_stats["mean"]) * 1e4,
        "top_excess_hac_t": top_stats["hac_t"],
        "median_selected_count": float(
            selected_count.loc[pd.Timestamp(start):pd.Timestamp(end)].replace(0, np.nan).median()
        ),
        "median_top_label_coverage": float(
            label_coverage.loc[pd.Timestamp(start):pd.Timestamp(end)].median(skipna=True)
        ),
        "residual_status": residual_status,
        "residual_ok_fraction": float(diagnostics["status"].eq("OK").mean()),
        "residual_days": residual_stats["days"],
        "residual_mean_ic": residual_stats["mean"],
        "residual_hac_t": residual_stats["hac_t"],
        "intrinsic_pass": not failures,
        "gate_failures": ";".join(failures),
    }
    return row, residual
