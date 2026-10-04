from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from etf_strategy.core.etf_group_daily_outcome import (
    CANDIDATE_ATOMS,
    build_atoms,
    build_directional_outcome_scores,
    build_outcome_atoms,
)


CONFIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs/group_ic20_outcome_batch_20260922.yaml"
)


@pytest.fixture
def config():
    return yaml.safe_load(CONFIG_PATH.read_text())


def _panels(n: int = 100, columns: tuple[str, ...] = ("A", "B")):
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    returns = 0.003 * np.sin(np.arange(n) / 3.0) + 0.001 * np.cos(np.arange(n) / 7.0)
    base = 100.0 * np.cumprod(1.0 + returns)
    close = pd.DataFrame({c: base * (1.0 + i * 0.01) for i, c in enumerate(columns)}, index=dates)
    open_ = close * 0.997
    high_scale = pd.Series(1.01 + 0.0004 * np.sin(np.arange(n) / 5.0), index=dates)
    low_scale = pd.Series(0.99 - 0.0003 * np.cos(np.arange(n) / 4.0), index=dates)
    high = close.mul(high_scale, axis=0)
    low = close.mul(low_scale, axis=0)
    amount = pd.DataFrame(
        {
            c: (1_500.0 + 250.0 * np.sin(np.arange(n) / 6.0) + 75.0 * np.cos(np.arange(n) / 11.0))
            * (i + 1)
            for i, c in enumerate(columns)
        },
        index=dates,
    )
    return {"open": open_, "high": high, "low": low, "close": close, "amount": amount}


def _panels_from_returns(returns: np.ndarray):
    close = 100.0 * np.cumprod(1.0 + returns)
    dates = pd.date_range("2024-01-01", periods=len(close), freq="D")
    close = pd.DataFrame({"A": close}, index=dates)
    return {
        "open": close * 0.999,
        "high": close * 1.01,
        "low": close * 0.99,
        "close": close,
        "amount": pd.DataFrame({"A": np.full(len(close), 1_000.0)}, index=dates),
    }


def test_exact_eight_whitelist_and_shapes(config):
    assert config["source_type"] == "daily_outcome"
    assert config["campaign_extension"] is True
    assert config["prior_registered"] == 117
    assert config["budget_cap"] == 125
    assert config["windows"] == [20]
    assert [item["name"] for item in config["candidates"]] == list(CANDIDATE_ATOMS)

    panels = _panels()
    atoms = build_outcome_atoms(panels, config)
    assert tuple(atoms) == CANDIDATE_ATOMS
    assert all(frame.shape == panels["close"].shape for frame in atoms.values())


def test_var_ratio_matches_hand_formula_and_requires_64_observations(config):
    panels = _panels()
    atoms = build_outcome_atoms(panels, config)
    returns = panels["close"]["A"].pct_change(fill_method=None)
    sums5 = returns.rolling(5, min_periods=5).sum()
    expected = sums5.rolling(60, min_periods=60).var(ddof=1).iloc[-1] / (
        5.0 * returns.rolling(60, min_periods=60).var(ddof=1).iloc[-1]
    )
    assert atoms["VAR_RATIO_5_60"]["A"].iloc[-1] == pytest.approx(expected)
    assert atoms["VAR_RATIO_5_60"]["A"].first_valid_index() == panels["close"].index[64]


def test_autocov_direction_and_directional_score(config):
    positive = np.tile(np.repeat([0.01, -0.01], 10), 6)
    alternating = np.tile([0.01, -0.01], 60)
    positive_raw = build_outcome_atoms(_panels_from_returns(positive), config)
    alternating_raw = build_outcome_atoms(_panels_from_returns(alternating), config)
    assert positive_raw["RETURN_AUTOCOV_20"]["A"].iloc[-1] > 0
    assert alternating_raw["RETURN_AUTOCOV_20"]["A"].iloc[-1] < 0
    assert positive_raw["RETURN_AUTOCOV_20"]["A"].iloc[-1] > alternating_raw[
        "RETURN_AUTOCOV_20"
    ]["A"].iloc[-1]

    raw = build_outcome_atoms(_panels(), config)
    scores = build_directional_outcome_scores(_panels(), config)
    runner_scores = build_atoms(_panels(), config)
    for name, spec in config["mechanisms"].items():
        pd.testing.assert_frame_equal(scores[name], raw[name] * int(spec["direction"]))
        pd.testing.assert_frame_equal(runner_scores[name], raw[name] * int(spec["direction"]))

    # Explicitly exercise all four negative directions, not only one sample.
    negative = [name for name, spec in config["mechanisms"].items() if spec["direction"] == -1]
    assert negative == [
        "DOWN_UP_ACTIVITY_20",
        "SHOCK_ACTIVITY_RESPONSE_20",
        "VOL_RESPONSE_ASYMMETRY_20",
        "OVERHEAD_TURNOVER_20",
    ]


def test_nan_strict_propagation_and_zero_denominator(config):
    panels = _panels()
    panels["close"].iloc[70, 0] = np.nan
    atoms = build_outcome_atoms(panels, config)
    assert pd.isna(atoms["VAR_RATIO_5_60"]["A"].iloc[70])
    assert pd.isna(atoms["RETURN_AUTOCOV_20"]["A"].iloc[70])
    assert pd.isna(atoms["RETURN_CONCENTRATION_20"]["A"].iloc[70])

    constant = _panels()
    for name in ("close", "open", "high", "low"):
        constant[name] = constant[name].copy()
        constant[name].iloc[:, :] = 100.0
    zero_atoms = build_outcome_atoms(constant, config)
    assert zero_atoms["VAR_RATIO_5_60"].isna().all().all()
    assert zero_atoms["RETURN_CONCENTRATION_20"].isna().all().all()


def test_price_and_amount_scaling_invariance(config):
    panels = _panels()
    scaled = {name: frame.copy() for name, frame in panels.items()}
    for name in ("open", "high", "low", "close"):
        scaled[name] *= 17.0
    scaled["amount"] *= 23.0
    base = build_outcome_atoms(panels, config)
    other = build_outcome_atoms(scaled, config)
    for name in CANDIDATE_ATOMS:
        pd.testing.assert_frame_equal(base[name], other[name], check_exact=False, rtol=1e-10, atol=1e-12)

    # Canonical prefix reloads can use a different adjustment normalization
    # for each ETF. Cross-date price comparisons must remain invariant.
    per_symbol = {name: frame.copy() for name, frame in panels.items()}
    multipliers = pd.Series({"A": 0.137, "B": 83.0})
    for name in ("open", "high", "low", "close"):
        per_symbol[name] = per_symbol[name].mul(multipliers, axis=1)
    adjusted = build_outcome_atoms(per_symbol, config)
    pd.testing.assert_frame_equal(
        base["OVERHEAD_TURNOVER_20"], adjusted["OVERHEAD_TURNOVER_20"],
        check_exact=False, rtol=0, atol=0,
    )


def test_prefix_and_future_perturbation_are_invariant(config):
    panels = _panels()
    cut = panels["close"].index[70]
    full = build_outcome_atoms(panels, config)
    prefix = {name: frame.loc[:cut] for name, frame in panels.items()}
    changed = {name: frame.copy() for name, frame in panels.items()}
    for name, frame in changed.items():
        frame.loc[frame.index > cut] *= 7.1
    perturbed = build_outcome_atoms(changed, config)
    prefix_atoms = build_outcome_atoms(prefix, config)
    for name in CANDIDATE_ATOMS:
        pd.testing.assert_frame_equal(
            full[name].loc[:cut], prefix_atoms[name], check_exact=False, rtol=1e-10, atol=1e-12
        )
        pd.testing.assert_frame_equal(
            full[name].loc[:cut], perturbed[name].loc[:cut], check_exact=False,
            rtol=1e-10, atol=1e-12
        )


def test_config_rejects_wrong_source_or_candidate_whitelist(config):
    bad = dict(config)
    bad["source_type"] = "daily"
    with pytest.raises(ValueError, match="source_type"):
        build_outcome_atoms(_panels(), bad)
    bad = dict(config)
    bad["candidates"] = list(config["candidates"][:-1])
    with pytest.raises(ValueError, match="whitelist"):
        build_outcome_atoms(_panels(), bad)
    bad = yaml.safe_load(CONFIG_PATH.read_text())
    bad["mechanisms"]["DOWN_UP_ACTIVITY_20"]["direction"] = 1
    with pytest.raises(ValueError, match="direction whitelist"):
        build_outcome_atoms(_panels(), bad)
    bad = yaml.safe_load(CONFIG_PATH.read_text())
    bad["budget_cap"] = bad["prior_registered"] + 7
    with pytest.raises(ValueError, match="budget/rejudge"):
        build_outcome_atoms(_panels(), bad)
