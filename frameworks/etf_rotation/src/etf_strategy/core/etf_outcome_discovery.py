"""Outcome-driven candidate discovery for the ETF rotation research domain.

This module is deliberately upstream of the referee.  It uses executable
forward returns only to learn which already-causal atom ranks distinguish the
same-date winners from losers.  The emitted candidate formulae contain atom
names and rank operators only; labels never enter factor materialization.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from typing import Mapping

import numpy as np
import pandas as pd

from .etf_family_referee import common_sample_spearman
from .etf_marginal_ic import STATUS_EVALUATED, residualize_scores_diagnostic
from .etf_mining_referee import (
    fractional_topk_weights,
    newey_west_t_calendar,
    purge_by_exit,
)


@dataclass(frozen=True, order=True)
class DiscoveryAtom:
    name: str
    source: str
    family: str
    config: str = ""


@dataclass(frozen=True)
class DiscoverySettings:
    top_k: int = 3
    min_names: int = 8
    horizon: int = 5
    entry_lag: int = 2
    min_days: int = 360
    min_year_days: int = 60
    min_eligible_years: int = 2
    min_year_direction_agreement: float = 2.0 / 3.0
    direction_fit_end: str | None = None
    min_direction_fit_days: int = 120
    max_atomic_candidates: int = 6
    max_candidates_per_family: int = 1
    pair_pool_size: int = 20
    max_pair_candidates: int = 4
    max_abs_leg_rank_corr: float = 0.80
    min_pair_score_gain: float = 0.0

    def validate(self) -> None:
        if self.top_k < 1 or self.min_names < 2 * self.top_k:
            raise ValueError("require min_names >= 2 * top_k")
        if self.horizon < 1 or self.entry_lag < 1:
            raise ValueError("horizon and entry_lag must be positive")
        if (
            self.min_days < 1
            or self.min_year_days < 1
            or self.min_eligible_years < 1
            or self.min_direction_fit_days < 1
        ):
            raise ValueError("discovery coverage thresholds must be positive")
        if not 0.0 <= self.min_year_direction_agreement <= 1.0:
            raise ValueError("min_year_direction_agreement must be in [0, 1]")
        if self.max_atomic_candidates < 0 or self.max_candidates_per_family < 1:
            raise ValueError("atomic candidate limit must be nonnegative; family limit must be positive")
        if self.pair_pool_size < 2 or self.max_pair_candidates < 0:
            raise ValueError("pair candidate limits are invalid")
        if not 0.0 <= self.max_abs_leg_rank_corr <= 1.0:
            raise ValueError("max_abs_leg_rank_corr must be in [0, 1]")


def winner_loser_spread(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    *,
    top_k: int,
    min_names: int,
) -> pd.Series:
    """Daily winner-minus-loser feature mean with tie-neutral outcome weights.

    Outcome membership is formed from the full eligible return cross-section.
    A missing label drops the date; it never replaces a winner with another
    name.  Missing signal values among selected names also drop the date.
    """
    if top_k < 1 or min_names < 2 * top_k:
        raise ValueError("require min_names >= 2 * top_k")
    forward = forward_return.reindex_like(signal).replace([np.inf, -np.inf], np.nan)
    eligible = eligibility.reindex_like(signal).fillna(False)
    score = signal.replace([np.inf, -np.inf], np.nan)
    known_count = eligible.sum(axis=1)
    label_complete = (~eligible | forward.notna()).all(axis=1)
    usable = known_count.ge(min_names) & label_complete
    outcome = forward.where(eligible)
    winner = fractional_topk_weights(outcome, top_k, min_names=min_names)
    loser = fractional_topk_weights(-outcome, top_k, min_names=min_names)
    selected = winner.add(loser).gt(0.0)
    signal_complete = (~selected | score.notna()).all(axis=1)
    winner_mean = score.fillna(0.0).mul(winner).sum(axis=1) / float(top_k)
    loser_mean = score.fillna(0.0).mul(loser).sum(axis=1) / float(top_k)
    return (winner_mean - loser_mean).where(usable & signal_complete).rename("winner_loser_spread")


def mean_abs_daily_rank_corr(
    left: pd.DataFrame,
    right: pd.DataFrame,
    eligibility: pd.DataFrame,
    *,
    min_names: int,
) -> float:
    """Mean absolute same-date rank correlation on the common finite sample."""
    daily, _ = common_sample_spearman(left, right, eligibility, min_names)
    clean = daily.dropna()
    return float(clean.abs().mean()) if len(clean) else float("nan")


def _profile_signal(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    controls: Mapping[str, pd.DataFrame],
    *,
    settings: DiscoverySettings,
    discovery_start: pd.Timestamp,
    discovery_end: pd.Timestamp,
    calendar: pd.Index,
    candidate_name: str | None,
) -> dict[str, object]:
    raw_spread = winner_loser_spread(
        signal,
        forward_return,
        eligibility,
        top_k=settings.top_k,
        min_names=settings.min_names,
    ).loc[discovery_start:discovery_end]
    raw_spread = purge_by_exit(
        raw_spread, calendar, discovery_end, settings.entry_lag + settings.horizon
    )
    daily_ic, _ = common_sample_spearman(
        signal, forward_return, eligibility, settings.min_names
    )
    daily_ic = purge_by_exit(
        daily_ic.loc[discovery_start:discovery_end],
        calendar,
        discovery_end,
        settings.entry_lag + settings.horizon,
    )

    controlled_signal = signal
    control_status = "NOT_REQUESTED"
    if controls:
        controlled_signal, _, control_status = residualize_scores_diagnostic(
            signal,
            controls,
            candidate_name=candidate_name,
            min_pairs=settings.min_names,
        )
    controlled_spread = winner_loser_spread(
        controlled_signal,
        forward_return,
        eligibility,
        top_k=settings.top_k,
        min_names=settings.min_names,
    ).loc[discovery_start:discovery_end]
    controlled_spread = purge_by_exit(
        controlled_spread, calendar, discovery_end, settings.entry_lag + settings.horizon
    )
    controlled_daily_ic, _ = common_sample_spearman(
        controlled_signal, forward_return, eligibility, settings.min_names
    )
    controlled_daily_ic = purge_by_exit(
        controlled_daily_ic.loc[discovery_start:discovery_end],
        calendar,
        discovery_end,
        settings.entry_lag + settings.horizon,
    )

    direction_end = (
        pd.Timestamp(settings.direction_fit_end)
        if settings.direction_fit_end is not None
        else discovery_end
    )
    if direction_end < discovery_start or direction_end > discovery_end:
        raise ValueError("direction_fit_end must be inside the discovery surface")
    if settings.direction_fit_end is None:
        raw_direction_sample = raw_spread
        controlled_direction_sample = controlled_spread
        raw_evidence = raw_spread
        controlled_evidence = controlled_spread
        raw_ic_evidence = daily_ic
        controlled_ic_evidence = controlled_daily_ic
    else:
        raw_direction_sample = purge_by_exit(
            raw_spread.loc[:direction_end],
            calendar,
            direction_end,
            settings.entry_lag + settings.horizon,
        )
        controlled_direction_sample = purge_by_exit(
            controlled_spread.loc[:direction_end],
            calendar,
            direction_end,
            settings.entry_lag + settings.horizon,
        )
        evidence_index = calendar[calendar > direction_end]
        if len(evidence_index) == 0:
            raise ValueError("direction_fit_end leaves no discovery evidence surface")
        evidence_start = pd.Timestamp(evidence_index[0])
        raw_evidence = raw_spread.loc[evidence_start:]
        controlled_evidence = controlled_spread.loc[evidence_start:]
        raw_ic_evidence = daily_ic.loc[evidence_start:]
        controlled_ic_evidence = controlled_daily_ic.loc[evidence_start:]

    raw_direction_clean = raw_direction_sample.dropna()
    controlled_direction_clean = controlled_direction_sample.dropna()
    raw_clean = raw_evidence.dropna()
    controlled_clean = controlled_evidence.dropna()
    raw_mean = float(raw_clean.mean()) if len(raw_clean) else float("nan")
    controlled_mean = (
        float(controlled_clean.mean()) if len(controlled_clean) else float("nan")
    )
    if not controls:
        controlled_mean = raw_mean
        controlled_evidence = raw_evidence
        controlled_clean = raw_clean
        controlled_direction_sample = raw_direction_sample
        controlled_direction_clean = raw_direction_clean
        controlled_ic_evidence = raw_ic_evidence
    raw_direction_fit_mean = (
        float(raw_direction_clean.mean()) if len(raw_direction_clean) else float("nan")
    )
    controlled_direction_fit_mean = (
        float(controlled_direction_clean.mean())
        if len(controlled_direction_clean)
        else float("nan")
    )
    raw_direction = (
        int(np.sign(raw_direction_fit_mean))
        if np.isfinite(raw_direction_fit_mean)
        else 0
    )
    controlled_direction = (
        int(np.sign(controlled_direction_fit_mean))
        if np.isfinite(controlled_direction_fit_mean)
        else 0
    )
    eligible_years = 0
    matching_years = 0
    year_means: dict[str, float | None] = {}
    for year, values in controlled_evidence.groupby(controlled_evidence.index.year):
        clean = values.dropna()
        mean = float(clean.mean()) if len(clean) else float("nan")
        year_means[str(int(year))] = mean if np.isfinite(mean) else None
        if len(clean) >= settings.min_year_days:
            eligible_years += 1
            matching_years += int(controlled_direction != 0 and np.sign(mean) == controlled_direction)
    year_agreement = (
        float(matching_years / eligible_years) if eligible_years else float("nan")
    )
    raw_t = newey_west_t_calendar(raw_evidence, calendar, settings.horizon - 1)
    controlled_t = newey_west_t_calendar(
        controlled_evidence, calendar, settings.horizon - 1
    )
    mean_ic = (
        float(raw_ic_evidence.dropna().mean())
        if raw_ic_evidence.notna().any()
        else float("nan")
    )
    controlled_mean_ic = (
        float(controlled_ic_evidence.dropna().mean())
        if controlled_ic_evidence.notna().any()
        else float("nan")
    )
    score_parts = [abs(value) for value in (raw_t, controlled_t) if np.isfinite(value)]
    discovery_score = min(score_parts) if score_parts else float("nan")
    stable = bool(
        len(raw_clean) >= settings.min_days
        and len(controlled_clean) >= settings.min_days
        and len(raw_direction_clean) >= settings.min_direction_fit_days
        and len(controlled_direction_clean) >= settings.min_direction_fit_days
        and raw_direction != 0
        and raw_direction == controlled_direction
        and np.sign(raw_mean) == controlled_direction
        and np.sign(controlled_mean) == controlled_direction
        and np.isfinite(mean_ic)
        and np.sign(mean_ic) == controlled_direction
        and np.isfinite(controlled_mean_ic)
        and np.sign(controlled_mean_ic) == controlled_direction
        and eligible_years >= settings.min_eligible_years
        and np.isfinite(year_agreement)
        and year_agreement >= settings.min_year_direction_agreement
        and (not controls or control_status == STATUS_EVALUATED)
    )
    return {
        "raw_days": int(len(raw_clean)),
        "controlled_days": int(len(controlled_clean)),
        "direction_fit_end": str(direction_end.date()),
        "raw_direction_fit_days": int(len(raw_direction_clean)),
        "controlled_direction_fit_days": int(len(controlled_direction_clean)),
        "raw_direction_fit_mean": raw_direction_fit_mean,
        "controlled_direction_fit_mean": controlled_direction_fit_mean,
        "raw_mean_spread": raw_mean,
        "controlled_mean_spread": controlled_mean,
        "raw_t_hac": raw_t,
        "controlled_t_hac": controlled_t,
        "mean_ic": mean_ic,
        "controlled_mean_ic": controlled_mean_ic,
        "raw_direction": raw_direction,
        "direction": controlled_direction,
        "eligible_years": eligible_years,
        "matching_years": matching_years,
        "year_direction_agreement": year_agreement,
        "year_mean_spread": year_means,
        "control_status": control_status,
        "discovery_score": discovery_score,
        "stable_lead": stable,
    }


def profile_atoms(
    ranked_atoms: Mapping[str, pd.DataFrame],
    atom_definitions: Mapping[str, DiscoveryAtom],
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    *,
    controls: Mapping[str, pd.DataFrame] | None,
    settings: DiscoverySettings,
    discovery_start: str | pd.Timestamp,
    discovery_end: str | pd.Timestamp,
) -> pd.DataFrame:
    """Profile causal atom ranks against same-date future winner/loser labels."""
    settings.validate()
    if set(ranked_atoms) != set(atom_definitions):
        raise ValueError("ranked_atoms and atom_definitions must have identical names")
    if not ranked_atoms:
        raise ValueError("at least one ranked atom is required")
    controls = controls or {}
    start, end = pd.Timestamp(discovery_start), pd.Timestamp(discovery_end)
    rows: list[dict[str, object]] = []
    for name in sorted(ranked_atoms):
        atom = atom_definitions[name]
        metrics = _profile_signal(
            ranked_atoms[name],
            forward_return,
            eligibility,
            controls,
            settings=settings,
            discovery_start=start,
            discovery_end=end,
            calendar=forward_return.index,
            candidate_name=name,
        )
        rows.append({**asdict(atom), **metrics})
    return pd.DataFrame(rows).sort_values(
        ["stable_lead", "discovery_score", "name"],
        ascending=[False, False, True],
        kind="stable",
    ).reset_index(drop=True)


def _atomic_candidate(sequence: int, atom: DiscoveryAtom, row: pd.Series) -> dict[str, object]:
    leg = {
        "name": atom.name,
        "source": atom.source,
        "family": atom.family,
        "config": atom.config,
    }
    direction = int(row["direction"])
    return {
        "id": f"DD{sequence:03d}",
        "operator": "atomic",
        "left": dict(leg),
        "right": dict(leg),
        "mechanism": f"outcome_profile:{atom.family}",
        "hypothesis": (
            f"Discovery winner/loser profiling found {atom.name} consistently "
            f"{'higher' if direction > 0 else 'lower'} among future H{int(row['horizon'])} winners "
            "after cross-sectional baseline controls."
        ),
        "expected_sign": direction,
        "discovery_evidence": row["evidence"],
    }


def distill_candidates(
    profiles: pd.DataFrame,
    ranked_atoms: Mapping[str, pd.DataFrame],
    atom_definitions: Mapping[str, DiscoveryAtom],
    forward_return: pd.DataFrame,
    eligibility: pd.DataFrame,
    *,
    controls: Mapping[str, pd.DataFrame] | None,
    settings: DiscoverySettings,
    discovery_start: str | pd.Timestamp,
    discovery_end: str | pd.Timestamp,
) -> tuple[list[dict[str, object]], pd.DataFrame]:
    """Distill stable outcome profiles into bounded atomic and spread formulae."""
    settings.validate()
    required = {"name", "family", "direction", "discovery_score", "stable_lead"}
    if not required <= set(profiles):
        raise ValueError(f"profiles missing columns: {sorted(required - set(profiles))}")
    stable = profiles.loc[profiles["stable_lead"].astype(bool)].copy()
    stable = stable.loc[stable["direction"].isin([-1, 1])]
    stable = stable.sort_values(
        ["discovery_score", "name"], ascending=[False, True], kind="stable"
    )

    chosen_rows: list[pd.Series] = []
    family_counts: dict[str, int] = {}
    if settings.max_atomic_candidates:
        for _, row in stable.iterrows():
            family = str(row["family"])
            if family_counts.get(family, 0) >= settings.max_candidates_per_family:
                continue
            chosen_rows.append(row)
            family_counts[family] = family_counts.get(family, 0) + 1
            if len(chosen_rows) >= settings.max_atomic_candidates:
                break

    candidates: list[dict[str, object]] = []
    for sequence, row in enumerate(chosen_rows, start=1):
        atom = atom_definitions[str(row["name"])]
        evidence = {
            key: row[key]
            for key in (
                "raw_days", "controlled_days", "direction_fit_end",
                "raw_direction_fit_days", "controlled_direction_fit_days",
                "raw_direction_fit_mean", "controlled_direction_fit_mean", "raw_mean_spread",
                "controlled_mean_spread", "raw_t_hac", "controlled_t_hac",
                "mean_ic", "controlled_mean_ic", "eligible_years", "matching_years",
                "year_direction_agreement", "discovery_score",
            )
        }
        enriched = row.copy()
        enriched["horizon"] = settings.horizon
        enriched["evidence"] = evidence
        candidates.append(_atomic_candidate(sequence, atom, enriched))

    pair_rows: list[dict[str, object]] = []
    pool = list(stable.head(settings.pair_pool_size).itertuples(index=False))
    profile_by_name = profiles.set_index("name")
    start, end = pd.Timestamp(discovery_start), pd.Timestamp(discovery_end)
    for first, second in combinations(pool, 2):
        if str(first.family) == str(second.family) or int(first.direction) == int(second.direction):
            continue
        positive, negative = (first, second) if int(first.direction) > 0 else (second, first)
        left_name, right_name = str(positive.name), str(negative.name)
        corr = mean_abs_daily_rank_corr(
            ranked_atoms[left_name].loc[start:end],
            ranked_atoms[right_name].loc[start:end],
            eligibility.loc[start:end],
            min_names=settings.min_names,
        )
        if not np.isfinite(corr) or corr > settings.max_abs_leg_rank_corr:
            continue
        signal = ranked_atoms[left_name] - ranked_atoms[right_name]
        metrics = _profile_signal(
            signal,
            forward_return,
            eligibility,
            controls or {},
            settings=settings,
            discovery_start=start,
            discovery_end=end,
            calendar=forward_return.index,
            candidate_name=None,
        )
        leg_score = max(
            float(profile_by_name.loc[left_name, "discovery_score"]),
            float(profile_by_name.loc[right_name, "discovery_score"]),
        )
        gain = float(metrics["discovery_score"]) - leg_score
        if not metrics["stable_lead"] or int(metrics["direction"]) != 1:
            continue
        if not np.isfinite(gain) or gain < settings.min_pair_score_gain:
            continue
        pair_rows.append(
            {
                "left": left_name,
                "right": right_name,
                "left_family": str(positive.family),
                "right_family": str(negative.family),
                "mean_abs_leg_rank_corr": corr,
                "leg_best_score": leg_score,
                "pair_score_gain": gain,
                **metrics,
            }
        )
    pair_frame = pd.DataFrame(pair_rows)
    if len(pair_frame):
        pair_frame = pair_frame.sort_values(
            ["discovery_score", "left", "right"],
            ascending=[False, True, True],
            kind="stable",
        )
        kept_family_pairs: set[tuple[str, str]] = set()
        for row in pair_frame.itertuples(index=False):
            family_pair = tuple(sorted((str(row.left_family), str(row.right_family))))
            if family_pair in kept_family_pairs:
                continue
            left, right = atom_definitions[str(row.left)], atom_definitions[str(row.right)]
            sequence = len(candidates) + 1
            evidence = {
                key: getattr(row, key)
                for key in (
                    "raw_days", "controlled_days", "direction_fit_end",
                    "raw_direction_fit_days", "controlled_direction_fit_days",
                    "raw_direction_fit_mean", "controlled_direction_fit_mean", "raw_mean_spread",
                    "controlled_mean_spread", "raw_t_hac", "controlled_t_hac",
                    "mean_ic", "controlled_mean_ic", "eligible_years", "matching_years",
                    "year_direction_agreement", "discovery_score",
                    "mean_abs_leg_rank_corr", "leg_best_score", "pair_score_gain",
                )
            }
            candidates.append(
                {
                    "id": f"DD{sequence:03d}",
                    "operator": "rank_spread",
                    "left": asdict(left),
                    "right": asdict(right),
                    "mechanism": f"outcome_profile:{left.family}_minus_{right.family}",
                    "hypothesis": (
                        f"Future H{settings.horizon} winners show high {left.name} and low "
                        f"{right.name}; their rank spread improves the controlled discovery "
                        "profile over either standalone leg."
                    ),
                    "expected_sign": 1,
                    "discovery_evidence": evidence,
                }
            )
            kept_family_pairs.add(family_pair)
            if len(kept_family_pairs) >= settings.max_pair_candidates:
                break
    return candidates, pair_frame
