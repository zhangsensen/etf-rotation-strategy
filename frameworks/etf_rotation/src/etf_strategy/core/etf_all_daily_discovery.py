"""Discovery-only profiling for broad point-in-time ETF cross-sections."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

from .etf_family_referee import common_sample_spearman
from .etf_marginal_ic import STATUS_EVALUATED, residualize_scores_diagnostic
from .etf_mining_referee import newey_west_t_calendar, purge_by_exit


@dataclass(frozen=True)
class AllEtfDiscoverySettings:
    entry_lag: int = 2
    horizon: int = 5
    min_names: int = 100
    direction_start: str = "2021-08-09"
    direction_end: str = "2022-06-30"
    discovery_start: str = "2022-07-01"
    discovery_end: str = "2023-12-31"
    validation_start: str = "2024-01-01"
    validation_end: str = "2025-04-30"
    min_direction_days: int = 150
    min_discovery_days: int = 300
    min_validation_days: int = 250
    min_abs_controlled_ic: float = 0.005
    min_discovery_hac_t: float = 2.0
    min_validation_hac_t: float = 2.0

    def validate(self) -> None:
        if self.entry_lag < 1 or self.horizon < 1 or self.min_names < 10:
            raise ValueError("lag/horizon must be positive and min_names must be at least 10")
        dates = [
            pd.Timestamp(self.direction_start),
            pd.Timestamp(self.direction_end),
            pd.Timestamp(self.discovery_start),
            pd.Timestamp(self.discovery_end),
            pd.Timestamp(self.validation_start),
            pd.Timestamp(self.validation_end),
        ]
        if dates != sorted(dates):
            raise ValueError("discovery surfaces must be ordered and non-overlapping")
        if any(value < 1 for value in (
            self.min_direction_days, self.min_discovery_days, self.min_validation_days,
        )):
            raise ValueError("surface coverage requirements must be positive")
        if self.min_abs_controlled_ic < 0:
            raise ValueError("IC floor must be nonnegative")


def executable_forward_return(
    adjusted_open: pd.DataFrame,
    *,
    entry_lag: int,
    horizon: int,
) -> pd.DataFrame:
    """open(D+lag+H) / open(D+lag) - 1; labels never enter features."""
    entry = adjusted_open.shift(-entry_lag)
    exit_price = adjusted_open.shift(-(entry_lag + horizon))
    return (exit_price / entry - 1.0).where(entry.gt(0) & exit_price.gt(0))


def _stats(
    values: pd.Series,
    *,
    start: str,
    end: str,
    calendar: pd.Index,
    exit_offset: int,
    hac_lag: int,
    direction: int,
) -> dict[str, float | int]:
    surface = purge_by_exit(
        values.loc[pd.Timestamp(start):pd.Timestamp(end)],
        calendar,
        pd.Timestamp(end),
        exit_offset,
    )
    signed = surface * float(direction)
    clean = signed.dropna()
    return {
        "days": int(len(clean)),
        "mean": float(clean.mean()) if len(clean) else float("nan"),
        # Dependence comes from the H-session return overlap.  Entry lag moves
        # both endpoints but does not add overlapping return sessions.
        "hac_t": float(newey_west_t_calendar(signed, calendar, hac_lag)),
    }


def profile_all_etf_signal(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    controls: Mapping[str, pd.DataFrame],
    *,
    name: str,
    settings: AllEtfDiscoverySettings,
) -> dict[str, object]:
    """Profile one causal score without using validation outcomes in its formula."""
    settings.validate()
    raw_ic, raw_count = common_sample_spearman(
        signal, forward_return, eligibility, settings.min_names
    )
    residual, diagnostics, status = residualize_scores_diagnostic(
        signal,
        controls,
        candidate_name=name,
        min_pairs=settings.min_names,
    )
    controlled_ic, controlled_count = common_sample_spearman(
        residual, forward_return, eligibility, settings.min_names
    )
    fit = purge_by_exit(
        controlled_ic.loc[
            pd.Timestamp(settings.direction_start):pd.Timestamp(settings.direction_end)
        ],
        controlled_ic.index,
        pd.Timestamp(settings.direction_end),
        settings.entry_lag + settings.horizon,
    ).dropna()
    direction_mean = float(fit.mean()) if len(fit) else float("nan")
    direction = int(np.sign(direction_mean)) if np.isfinite(direction_mean) else 0
    raw_fit = purge_by_exit(
        raw_ic.loc[pd.Timestamp(settings.direction_start):pd.Timestamp(settings.direction_end)],
        raw_ic.index,
        pd.Timestamp(settings.direction_end),
        settings.entry_lag + settings.horizon,
    ).dropna()
    raw_direction = (
        int(np.sign(float(raw_fit.mean())))
        if len(raw_fit) and np.isfinite(float(raw_fit.mean()))
        else 0
    )
    discovery = _stats(
        controlled_ic,
        start=settings.discovery_start,
        end=settings.discovery_end,
        calendar=controlled_ic.index,
        exit_offset=settings.entry_lag + settings.horizon,
        hac_lag=settings.horizon - 1,
        direction=direction,
    )
    validation = _stats(
        controlled_ic,
        start=settings.validation_start,
        end=settings.validation_end,
        calendar=controlled_ic.index,
        exit_offset=settings.entry_lag + settings.horizon,
        hac_lag=settings.horizon - 1,
        direction=direction,
    )
    raw_discovery = _stats(
        raw_ic,
        start=settings.discovery_start,
        end=settings.discovery_end,
        calendar=raw_ic.index,
        exit_offset=settings.entry_lag + settings.horizon,
        hac_lag=settings.horizon - 1,
        direction=raw_direction,
    )
    raw_validation = _stats(
        raw_ic,
        start=settings.validation_start,
        end=settings.validation_end,
        calendar=raw_ic.index,
        exit_offset=settings.entry_lag + settings.horizon,
        hac_lag=settings.horizon - 1,
        direction=raw_direction,
    )
    stable = bool(
        status == STATUS_EVALUATED
        and direction != 0
        and len(fit) >= settings.min_direction_days
        and discovery["days"] >= settings.min_discovery_days
        and validation["days"] >= settings.min_validation_days
        and discovery["mean"] >= settings.min_abs_controlled_ic
        and validation["mean"] >= settings.min_abs_controlled_ic
        and discovery["hac_t"] >= settings.min_discovery_hac_t
        and validation["hac_t"] >= settings.min_validation_hac_t
    )
    ok_fraction = (
        float(diagnostics["status"].eq("OK").mean()) if len(diagnostics) else 0.0
    )
    return {
        "name": name,
        "control_status": status,
        "control_ok_fraction": ok_fraction,
        "direction_fit_days": int(len(fit)),
        "direction_fit_mean_ic": direction_mean,
        "direction": direction,
        "raw_direction": raw_direction,
        "discovery_days": discovery["days"],
        "controlled_discovery_ic": discovery["mean"],
        "controlled_discovery_hac_t": discovery["hac_t"],
        "validation_days": validation["days"],
        "controlled_validation_ic": validation["mean"],
        "controlled_validation_hac_t": validation["hac_t"],
        "raw_discovery_ic": raw_discovery["mean"],
        "raw_discovery_hac_t": raw_discovery["hac_t"],
        "raw_validation_ic": raw_validation["mean"],
        "raw_validation_hac_t": raw_validation["hac_t"],
        "median_pair_count": float(controlled_count.median(skipna=True)),
        "raw_median_pair_count": float(raw_count.median(skipna=True)),
        "stable_lead": stable,
    }
