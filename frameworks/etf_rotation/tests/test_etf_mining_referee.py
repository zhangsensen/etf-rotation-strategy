from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_mining_campaign import (
    canonical_expression_hashes,
    canonical_plan_count,
    verify_plan_seal,
    write_plan_seal,
    write_plan_with_budget,
)
from etf_strategy.core.etf_mining_referee import (
    campaign_bonferroni_pass,
    fractional_topk_weights,
    holm_rejections,
    newey_west_t,
    paired_increment_stats,
    topk_series,
)


def test_fractional_topk_is_column_order_invariant() -> None:
    scores = pd.DataFrame(
        [[4.0, 3.0, 3.0, 1.0], [1.0, 1.0, 1.0, 1.0]],
        columns=list("ABCD"),
    )
    expected = fractional_topk_weights(scores, 2, min_names=4)
    permuted = fractional_topk_weights(scores[list("DCBA")], 2, min_names=4)
    pd.testing.assert_frame_equal(expected, permuted[list("ABCD")])
    np.testing.assert_allclose(expected.sum(axis=1), 2.0)
    np.testing.assert_allclose(expected.iloc[0].to_numpy(), [1.0, 0.5, 0.5, 0.0])
    np.testing.assert_allclose(expected.iloc[1].to_numpy(), 0.5)


def test_topk_series_is_tie_neutral_for_signal_and_outcome() -> None:
    index = pd.date_range("2024-01-01", periods=2)
    signal = pd.DataFrame([[3, 2, 2, 1], [1, 1, 1, 1]], index=index, columns=list("ABCD"))
    forward = pd.DataFrame([[0.4, 0.2, 0.2, 0.0], [0.1, 0.1, 0.1, 0.1]], index=index, columns=list("ABCD"))
    eligibility = pd.DataFrame(True, index=index, columns=list("ABCD"))
    base = topk_series(signal, forward, eligibility, direction=1.0, k=2, min_names=4)
    permuted = topk_series(
        signal[list("CADB")],
        forward[list("CADB")],
        eligibility[list("CADB")],
        direction=1.0,
        k=2,
        min_names=4,
    )
    pd.testing.assert_series_equal(base.excess, permuted.excess)
    pd.testing.assert_series_equal(base.precision, permuted.precision)


def test_holm_and_campaign_budget() -> None:
    assert holm_rejections([0.001, 0.02, 0.5], 0.05) == [True, True, False]
    passed, pvalue = campaign_bonferroni_pass(5.0, alpha=0.05, hypothesis_budget=6000)
    assert passed
    assert pvalue < 0.05 / 6000
    failed, _ = campaign_bonferroni_pass(3.0, alpha=0.05, hypothesis_budget=6000)
    assert not failed


def test_paired_increment_uses_difference_series() -> None:
    index = pd.date_range("2023-01-01", periods=500)
    leg = pd.Series(np.sin(np.arange(500) / 7.0) * 0.001, index=index)
    candidate = leg + 0.001
    stats = paired_increment_stats(
        candidate,
        leg,
        discovery_end=pd.Timestamp("2023-10-31"),
        audit_start=pd.Timestamp("2023-11-01"),
        audit_end=pd.Timestamp("2024-05-14"),
        horizon=5,
    )
    assert abs(stats["discovery_bp"] - 10.0) < 1e-10
    assert abs(stats["audit_bp"] - 10.0) < 1e-10


def test_newey_west_t_rejects_short_series() -> None:
    assert np.isnan(newey_west_t(pd.Series([0.1] * 10), 4))


def test_campaign_budget_counts_only_canonical_rounds(tmp_path) -> None:
    roots = (tmp_path / "pi", tmp_path / "sonnet")
    for root, name, count in (
        (roots[0], "round_001", 2),
        (roots[0], "round_001_replay", 50),
        (roots[1], "round_002", 1),
    ):
        path = root / name
        path.mkdir(parents=True)
        (path / "PLAN.json").write_text(json.dumps({"candidates": [{}] * count}))
    assert canonical_plan_count(roots) == 3
    new_plan = roots[1] / "round_003/PLAN.json"
    new_plan.parent.mkdir()
    used = write_plan_with_budget(
        new_plan,
        {"candidates": [{}, {}]},
        output_roots=roots,
        lock_path=tmp_path / "campaign.lock",
        budget=5,
    )
    assert used == 5
    with pytest.raises(RuntimeError, match="campaign budget exceeded"):
        write_plan_with_budget(
            roots[0] / "round_004/PLAN.json",
            {"candidates": [{}]},
            output_roots=roots,
            lock_path=tmp_path / "campaign.lock",
            budget=5,
        )


def test_campaign_budget_deduplicates_linked_plan_across_roots(tmp_path) -> None:
    roots = (tmp_path / "history", tmp_path / "lane")
    original = roots[0] / "round_001/PLAN.json"
    original.parent.mkdir(parents=True)
    original.write_text(json.dumps({"candidates": [{}, {}, {}]}))
    linked = roots[1] / "round_001/PLAN.json"
    linked.parent.mkdir(parents=True)
    linked.symlink_to(original)

    assert canonical_plan_count(roots) == 3


def test_plan_seal_detects_post_registration_edit(tmp_path) -> None:
    plan_path = tmp_path / "PLAN.json"
    plan_path.write_text('{"candidates": []}')
    assert write_plan_seal(plan_path) == tmp_path / "PLAN.sha256"
    assert verify_plan_seal(plan_path)
    plan_path.write_text('{"candidates": [{"id": "late"}]}')
    assert not verify_plan_seal(plan_path)


def test_campaign_lock_rejects_cross_lane_duplicate_expression(tmp_path) -> None:
    roots = (tmp_path / "pi", tmp_path / "sonnet")
    old = roots[0] / "round_001/PLAN.json"
    old.parent.mkdir(parents=True)
    old.write_text(json.dumps({"candidates": [{}], "expression_hashes": {"A": "same"}}))
    assert canonical_expression_hashes(roots) == {"same"}
    new = roots[1] / "round_002/PLAN.json"
    new.parent.mkdir(parents=True)
    with pytest.raises(RuntimeError, match="already planned"):
        write_plan_with_budget(
            new,
            {"candidates": [{}], "expression_hashes": {"B": "same"}},
            output_roots=roots,
            lock_path=tmp_path / "campaign.lock",
            budget=10,
        )
