"""The editable candidate cannot make earlier scores depend on future bars."""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
import sys
import json
import time

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/research"))
from run_etf_autoresearch_ic import causal_scores
from audit_etf_autoresearch_novelty import audit, read_prefix, require_latest_inventory
from cycle_etf_autoresearch import choose, compare, cycle, validate_parent_seed
from etf_strategy.core import etf_group_discovery as engine


def test_candidate_prefix_and_future_perturbation_gate() -> None:
    dates = pd.bdate_range("2025-01-01", periods=50)
    close = pd.DataFrame({"a": np.arange(1, 51, dtype=float)}, index=dates)
    panels = {"close": close}
    cut = dates[30]
    good = SimpleNamespace(DIRECTION=1, score=lambda p: p["close"].rolling(5).mean())
    pd.testing.assert_frame_equal(causal_scores(good, panels, cut), good.score(panels))
    leaking = SimpleNamespace(DIRECTION=1, score=lambda p: p["close"].shift(-1))
    with pytest.raises(AssertionError):
        causal_scores(leaking, panels, cut)


def test_evaluation_period_conditional_future_leak_is_rejected() -> None:
    dates = pd.bdate_range("2024-12-02", "2025-02-14")
    close = pd.DataFrame({"a": np.arange(1, len(dates) + 1, dtype=float)}, index=dates)

    def conditional_score(panels):
        score = panels["close"].rolling(3).mean()
        score.loc[score.index >= pd.Timestamp("2025-01-01")] = panels["close"].shift(-1)
        return score

    with pytest.raises(AssertionError):
        causal_scores(SimpleNamespace(DIRECTION=1, score=conditional_score),
                      {"close": close}, pd.Timestamp("2024-12-31"))


def test_fixed_open_to_open_label_starts_after_signal() -> None:
    dates = pd.bdate_range("2025-01-01", periods=10)
    opening = pd.DataFrame({"a": np.arange(100, 110, dtype=float)}, index=dates)
    labels, timing = engine.labels({"open": opening}, 2, 5)
    assert timing.loc[dates[0], "entry_date"] == dates[2]
    assert timing.loc[dates[0], "exit_date"] == dates[7]
    assert labels.loc[dates[0], "a"] == pytest.approx(107 / 102 - 1)


def test_novelty_reader_stops_at_cold_cutoff(tmp_path) -> None:
    path = tmp_path / "scores.csv"
    path.write_text("signal_date,g1,g2\n2026-03-24,1,2\n2026-03-25,bad,secret\n")
    old = read_prefix(path)
    assert old.index.tolist() == [pd.Timestamp("2026-03-24")]


def test_ic_observation_and_redundancy_are_separate() -> None:
    trial = {"n": 287, "ic": 0.08}
    paired = {"n": 287, "delta_ic": 0.02}
    novelty = {"nearest": [{"candidate": "old_flow", "mean_abs_daily_rank_corr": 0.96}]}
    assert choose(trial, novelty, paired)[0] == "positive_ic_review"
    novelty["nearest"][0]["mean_abs_daily_rank_corr"] = 0.3
    assert choose(trial, novelty, paired)[0] == "positive_ic_review"


def test_diverse_ic_lead_does_not_need_to_beat_momentum_baseline() -> None:
    novelty = {"nearest": []}
    paired = {"n": 240, "delta_ic": -0.02}
    assert choose({"n": 287, "ic": 0.06}, novelty, paired)[0] == "positive_ic_review"
    assert choose({"n": 287, "ic": 0.005}, novelty, paired)[0] == "weak_positive_ic"
    assert choose({"n": 287, "ic": -0.02}, novelty, paired)[0] == "negative_ic_watch"
    assert choose({"n": 0, "ic": float("nan")}, novelty, paired)[0] == "uncomputable_ic"


def test_experiment_budget_interrupts_stuck_candidate(tmp_path, monkeypatch) -> None:
    import run_etf_autoresearch_ic as driver
    monkeypatch.setattr(driver, "TIME_BUDGET_SECONDS", 0.02)
    monkeypatch.setattr(driver, "_run_with_budget", lambda *_: time.sleep(0.2))
    with pytest.raises(TimeoutError, match="five-minute experiment budget"):
        driver.run("stuck_candidate", tmp_path)


def test_cycle_records_preflight_failure_as_an_attempt(tmp_path, monkeypatch) -> None:
    import cycle_etf_autoresearch as driver
    monkeypatch.setattr(driver, "require_latest_inventory",
                        lambda *_: (_ for _ in ()).throw(ValueError("stale inventory")))
    with pytest.raises(ValueError, match="stale inventory"):
        cycle("failed_preflight", tmp_path, tmp_path / "baseline", tmp_path / "inventory.csv",
              tmp_path / "runs")
    attempt = json.loads((tmp_path / "attempts/failed_preflight.json").read_text())
    assert attempt["status"] == "FAILED"
    assert attempt["stage"] == "preflight"


def test_cycle_records_post_evaluation_failure_as_an_attempt(tmp_path, monkeypatch) -> None:
    import cycle_etf_autoresearch as driver
    monkeypatch.setattr(driver, "require_latest_inventory", lambda *_: None)

    def fake_run(run_id, output_root):
        (output_root / run_id).mkdir()
        for name in ("result.json", "daily_ic.csv", "group_scores.csv"):
            (output_root / run_id / name).write_text("{}")
        return {"candidate": "autoresearch_example"}

    monkeypatch.setattr(driver, "run", fake_run)
    monkeypatch.setattr(driver, "audit",
                        lambda *_: (_ for _ in ()).throw(ValueError("missing prior score")))
    with pytest.raises(ValueError, match="missing prior score"):
        cycle("failed_novelty", tmp_path, tmp_path / "baseline", tmp_path / "inventory.csv",
              tmp_path / "runs")
    attempt = json.loads((tmp_path / "attempts/failed_novelty.json").read_text())
    assert attempt["status"] == "FAILED"
    assert attempt["stage"] == "novelty"


def test_compare_requires_same_ic_implementation(tmp_path) -> None:
    base, trial = tmp_path / "base", tmp_path / "trial"
    base.mkdir()
    trial.mkdir()
    shared = {"evaluator_sha256": "same", "implementation_sha256": {"core.py": "first"},
              "python_version": "3", "pandas_version": "2", "numpy_version": "2",
              "input_sha256": {}, "groups_sha256": "g", "universe_sha256": "u"}
    (base / "result.json").write_text(json.dumps(shared))
    (trial / "result.json").write_text(json.dumps({**shared,
                                                   "implementation_sha256": {"core.py": "changed"}}))
    with pytest.raises(ValueError, match="fixed evaluation inputs"):
        compare(base, trial)


def test_novelty_includes_prior_local_trials(tmp_path) -> None:
    root = tmp_path / "trials"
    prior, current = root / "prior", root / "current"
    prior.mkdir(parents=True)
    current.mkdir()
    dates = pd.bdate_range("2025-01-01", periods=60)
    scores = pd.DataFrame({f"g{i}": [float(i)] * len(dates) for i in range(8)}, index=dates)
    scores.to_csv(prior / "group_scores.csv", index_label="signal_date")
    scores.to_csv(current / "group_scores.csv", index_label="signal_date")
    (prior / "result.json").write_text(json.dumps({"candidate": "autoresearch_prior",
                                                   "family": "example"}))
    inventory = tmp_path / "all_factors.csv"
    inventory.write_text("source_run,candidate,family\n")
    result = audit(current, inventory, tmp_path / "runs")
    assert result["nearest"][0]["candidate"] == "autoresearch_prior"
    assert result["nearest"][0]["source"] == "local_trial"
    assert result["nearest"][0]["mean_abs_daily_rank_corr"] == pytest.approx(1)


def test_parent_seed_must_reproduce_formal_signed_ranks(tmp_path) -> None:
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    runs = tmp_path / "runs"
    formal = runs / "formal"
    formal.mkdir(parents=True)
    dates = pd.bdate_range("2025-01-01", periods=60)
    scores = pd.DataFrame({f"g{i}": [float(i)] * len(dates) for i in range(8)}, index=dates)
    scores.to_csv(baseline / "group_scores.csv", index_label="signal_date")
    scores.to_csv(formal / "scores_parent_20.csv", index_label="signal_date")
    inventory = tmp_path / "all_factors.csv"
    inventory.write_text("candidate,definition_id,family,source_run\n"
                         "parent_20,parent-definition,price_trend,formal\n")
    matched = validate_parent_seed(baseline, inventory, runs, "parent_20")
    assert matched["definition_id"] == "parent-definition"
    assert matched["seed_min_rank_corr"] == pytest.approx(1)
    scores[["g0", "g7"]] = scores[["g7", "g0"]].to_numpy()
    scores.to_csv(baseline / "group_scores.csv", index_label="signal_date")
    with pytest.raises(ValueError, match="signed ranks"):
        validate_parent_seed(baseline, inventory, runs, "parent_20")


def test_cycle_rejects_stale_inventory_pointer(tmp_path) -> None:
    import json
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "one").mkdir()
    (runs / "one" / "PLAN.json").write_text(json.dumps({"cumulative_registered_definitions": 554}))
    current = tmp_path / "current"
    current.mkdir()
    (current / "all_factors.csv").write_text("candidate\n")
    stale = tmp_path / "stale"
    stale.mkdir()
    (stale / "all_factors.csv").write_text("candidate\n")
    (tmp_path / "IC_INVENTORY_LATEST.json").write_text(
        json.dumps({"snapshot": str(current), "registered_budget_count": 554}))
    require_latest_inventory(current / "all_factors.csv", runs)
    with pytest.raises(ValueError, match="stale"):
        require_latest_inventory(stale / "all_factors.csv", runs)
