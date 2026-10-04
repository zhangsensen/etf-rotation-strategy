from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from etf_strategy.core.etf_outcome_discovery import (
    DiscoveryAtom,
    DiscoverySettings,
    distill_candidates,
    profile_atoms,
    winner_loser_spread,
)


def _synthetic() -> tuple[
    dict[str, pd.DataFrame],
    dict[str, DiscoveryAtom],
    pd.DataFrame,
    pd.DataFrame,
]:
    rng = np.random.default_rng(20260921)
    dates = pd.bdate_range("2021-01-04", periods=540)
    symbols = [f"E{i:02d}" for i in range(10)]
    driver = pd.DataFrame(
        rng.normal(size=(len(dates), len(symbols))), index=dates, columns=symbols
    )
    control = pd.DataFrame(
        rng.normal(size=(len(dates), len(symbols))), index=dates, columns=symbols
    )
    noise = pd.DataFrame(
        rng.normal(size=(len(dates), len(symbols))), index=dates, columns=symbols
    )
    forward = 0.04 * driver - 0.03 * noise + 0.005 * control + pd.DataFrame(
        rng.normal(scale=0.01, size=driver.shape), index=dates, columns=symbols
    )
    eligibility = pd.DataFrame(True, index=dates, columns=symbols)
    atoms = {
        "POS": driver.rank(axis=1, pct=True),
        "NEG": noise.rank(axis=1, pct=True),
        "NULL": pd.DataFrame(
            rng.normal(size=driver.shape), index=dates, columns=symbols
        ).rank(axis=1, pct=True),
        "CTRL": control.rank(axis=1, pct=True),
    }
    definitions = {
        "POS": DiscoveryAtom("POS", "positive_source", "positive_family", "positive.yaml"),
        "NEG": DiscoveryAtom("NEG", "negative_source", "negative_family", "negative.yaml"),
        "NULL": DiscoveryAtom("NULL", "null_source", "null_family", "null.yaml"),
        "CTRL": DiscoveryAtom("CTRL", "control_source", "control_family", "control.yaml"),
    }
    return atoms, definitions, forward, eligibility


def _settings() -> DiscoverySettings:
    return DiscoverySettings(
        top_k=2,
        min_names=8,
        horizon=5,
        entry_lag=2,
        min_days=300,
        min_year_days=80,
        min_eligible_years=2,
        min_year_direction_agreement=1.0,
        max_atomic_candidates=3,
        max_candidates_per_family=1,
        pair_pool_size=4,
        max_pair_candidates=2,
        max_abs_leg_rank_corr=0.8,
        min_pair_score_gain=-100.0,
    )


def test_winner_loser_spread_is_tie_neutral_and_column_order_invariant() -> None:
    date = pd.DatetimeIndex(["2024-01-02"])
    signal = pd.DataFrame([[0.1, 0.5, 0.9, 0.5]], index=date, columns=list("ABCD"))
    forward = pd.DataFrame([[0.0, 1.0, 1.0, -1.0]], index=date, columns=list("ABCD"))
    eligible = pd.DataFrame(True, index=date, columns=list("ABCD"))
    first = winner_loser_spread(signal, forward, eligible, top_k=1, min_names=4)
    order = list("DCBA")
    second = winner_loser_spread(
        signal[order], forward[order], eligible[order], top_k=1, min_names=4
    )
    assert np.isclose(first.iloc[0], second.iloc[0])
    assert np.isclose(first.iloc[0], 0.2)


def test_profiles_find_planted_winner_and_loser_atoms_after_control() -> None:
    atoms, definitions, forward, eligibility = _synthetic()
    profiles = profile_atoms(
        atoms,
        definitions,
        forward,
        eligibility,
        controls={"CTRL": atoms["CTRL"]},
        settings=_settings(),
        discovery_start=forward.index.min(),
        discovery_end=forward.index.max(),
    ).set_index("name")
    assert bool(profiles.loc["POS", "stable_lead"])
    assert int(profiles.loc["POS", "direction"]) == 1
    assert profiles.loc["POS", "controlled_mean_ic"] > 0
    assert bool(profiles.loc["NEG", "stable_lead"])
    assert int(profiles.loc["NEG", "direction"]) == -1
    assert profiles.loc["NEG", "controlled_mean_ic"] < 0
    assert not bool(profiles.loc["CTRL", "stable_lead"])


def test_future_labels_after_discovery_end_do_not_change_proposal() -> None:
    atoms, definitions, forward, eligibility = _synthetic()
    settings = _settings()
    cutoff = forward.index[419]

    def run(labels: pd.DataFrame):
        profiles = profile_atoms(
            atoms,
            definitions,
            labels,
            eligibility,
            controls={"CTRL": atoms["CTRL"]},
            settings=settings,
            discovery_start=forward.index.min(),
            discovery_end=cutoff,
        )
        candidates, pairs = distill_candidates(
            profiles,
            atoms,
            definitions,
            labels,
            eligibility,
            controls={"CTRL": atoms["CTRL"]},
            settings=settings,
            discovery_start=forward.index.min(),
            discovery_end=cutoff,
        )
        return profiles, candidates, pairs

    first_profiles, first_candidates, first_pairs = run(forward)
    changed = forward.copy()
    changed.loc[changed.index > cutoff] = changed.loc[changed.index > cutoff] * -1000.0
    second_profiles, second_candidates, second_pairs = run(changed)
    pd.testing.assert_frame_equal(first_profiles, second_profiles)
    pd.testing.assert_frame_equal(first_pairs, second_pairs)
    assert first_candidates == second_candidates


def test_direction_is_frozen_on_earlier_fit_surface() -> None:
    atoms, definitions, forward, eligibility = _synthetic()
    cutoff = forward.index[219]
    settings = replace(
        _settings(),
        direction_fit_end=str(cutoff.date()),
        min_direction_fit_days=120,
        min_days=250,
    )

    def run(labels: pd.DataFrame) -> pd.DataFrame:
        return profile_atoms(
            atoms,
            definitions,
            labels,
            eligibility,
            controls={"CTRL": atoms["CTRL"]},
            settings=settings,
            discovery_start=forward.index.min(),
            discovery_end=forward.index.max(),
        ).set_index("name")

    first = run(forward)
    changed = forward.copy()
    changed.loc[changed.index > cutoff] *= -1.0
    second = run(changed)
    assert first.loc["POS", "direction"] == second.loc["POS", "direction"]
    assert np.isclose(
        first.loc["POS", "controlled_direction_fit_mean"],
        second.loc["POS", "controlled_direction_fit_mean"],
    )


def test_distillation_emits_factor_only_formulae_and_data_driven_spread() -> None:
    atoms, definitions, forward, eligibility = _synthetic()
    settings = _settings()
    profiles = profile_atoms(
        atoms,
        definitions,
        forward,
        eligibility,
        controls={"CTRL": atoms["CTRL"]},
        settings=settings,
        discovery_start=forward.index.min(),
        discovery_end=forward.index.max(),
    )
    candidates, _ = distill_candidates(
        profiles,
        atoms,
        definitions,
        forward,
        eligibility,
        controls={"CTRL": atoms["CTRL"]},
        settings=settings,
        discovery_start=forward.index.min(),
        discovery_end=forward.index.max(),
    )
    assert candidates
    assert all("forward" not in str(candidate).lower() for candidate in candidates)
    assert any(
        candidate["operator"] == "rank_spread"
        and candidate["left"]["name"] == "POS"
        and candidate["right"]["name"] == "NEG"
        for candidate in candidates
    )
