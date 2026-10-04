from etf_strategy.core.etf_group_confirmation import evidence_policy


def test_prior_direction_keeps_full_window_policy():
    assert evidence_policy({"version": "group_ic20_batch9_daily"}, "market_residual_abs_cluster_20") == (
        "PRIOR_DIRECTION_FULL_WINDOW"
    )


def test_2025_direction_uses_2026_only():
    cfg = {"version": "group_ic20_batch18_stage2", "discovery_surface": "2025_POST_IC_DIRECTION"}
    assert evidence_policy(cfg, "d2025_market_residual_mean_20") == (
        "2025_DIRECTION_2026_HISTORICAL_SEGMENT"
    )


def test_adaptive_range_shock_and_reverse_fail_closed():
    cfg = {"version": "group_ic20_batch20_stage2", "discovery_surface": "2025_POST_IC_DIRECTION"}
    assert evidence_policy(cfg, "d2025_range_shock_clv_absorption_20") == (
        "SEEN_2026_ADAPTIVE_NOT_CONFIRMATION"
    )
    assert evidence_policy(cfg, "reverse_illiquidity_5") == (
        "POST_RESULT_REVERSE_NOT_CONFIRMATION"
    )
