import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_group_luna_rounds_e import DIRECTIONS, build_atoms


def _panels(n=100, members=14):
    rng = np.random.default_rng(66070)
    idx = pd.bdate_range("2025-01-01", periods=n)
    cols = [f"e{i:02}" for i in range(members)]
    ret = rng.normal(0.0003, 0.01, (n, members))
    close = pd.DataFrame(100 * np.cumprod(1 + ret, axis=0), index=idx, columns=cols)
    prev = close.shift(1).fillna(close.iloc[0])
    open_ = prev * (1 + rng.normal(0, 0.004, (n, members)))
    return {
        "close": close,
        "open": pd.DataFrame(open_, index=idx, columns=cols),
    }


def _cfg(names=None):
    names = list(DIRECTIONS) if names is None else names
    return {"windows": [20], "mechanisms": {n: {"direction": DIRECTIONS[n]} for n in names}}


def test_hand_formulas_for_rank_stats_and_robust_relative_return():
    p = _panels()
    names = [
        "l66_relative_rank_persistence", "l66_rank_upgrade_rate", "l66_rank_mobility",
        "l67_median_residual_return", "l67_trimmed_peer_relative_return",
        "l67_cross_sectional_relative_zscore",
    ]
    out = build_atoms(p, _cfg(names))
    ret = p["close"].pct_change(fill_method=None)
    rank = ret.rank(axis=1, method="average", pct=True)
    i, j = len(ret) - 1, 3
    np.testing.assert_allclose(
        out[names[0] + "_20"].iloc[i, j],
        np.corrcoef(rank.iloc[i - 19:i + 1, j], rank.iloc[i - 20:i, j])[0, 1],
    )
    delta = rank.iloc[i - 19:i + 1, j].to_numpy() - rank.iloc[i - 20:i, j].to_numpy()
    np.testing.assert_allclose(out[names[1] + "_20"].iloc[i, j], np.mean(delta > 0))
    np.testing.assert_allclose(out[names[2] + "_20"].iloc[i, j], -np.mean(np.abs(delta)))

    residual = ret.copy()
    for col in ret.columns:
        residual[col] = ret[col] - ret.drop(columns=col).mean(axis=1)
    np.testing.assert_allclose(out[names[3] + "_20"].iloc[i, j], np.median(residual.iloc[i - 19:i + 1, j]))
    peers = ret.iloc[i - 19:i + 1].drop(columns=ret.columns[j]).to_numpy()
    trimmed = np.sort(peers, axis=1)[:, 1:-1].mean(axis=1)
    np.testing.assert_allclose(out[names[4] + "_20"].iloc[i, j], np.mean(ret.iloc[i - 19:i + 1, j] - trimmed))
    std = ret.iloc[i - 19:i + 1].std(axis=1, ddof=0)
    z = (ret.iloc[i - 19:i + 1, j] - ret.iloc[i - 19:i + 1].mean(axis=1)) / std
    np.testing.assert_allclose(out[names[5] + "_20"].iloc[i, j], z.mean())


def test_conditional_statistics_match_hand_calculation_and_long_break_components():
    p = _panels(n=90)
    names = [n for n in DIRECTIONS if n.startswith(("l68_", "l69_", "l70_"))]
    out = build_atoms(p, _cfg(names))
    ret, close, open_ = p["close"].pct_change(fill_method=None), p["close"], p["open"]
    i, j = len(close) - 1, 2
    peer = (ret.sum(axis=1) - ret.iloc[:, j]) / 13
    residual = ret.iloc[:, j] - peer
    down = peer.iloc[i - 19:i + 1] < 0
    np.testing.assert_allclose(out["l68_down_market_relative_win_rate_20"].iloc[i, j], (ret.iloc[i - 19:i + 1, j][down] > peer.iloc[i - 19:i + 1][down]).mean())
    np.testing.assert_allclose(out["l68_down_market_relative_mean_20"].iloc[i, j], residual.iloc[i - 19:i + 1][down].mean())
    rank = ret.iloc[i - 19:i + 1].rank(axis=1, method="average", pct=True)
    np.testing.assert_allclose(out["l68_down_market_rank_20"].iloc[i, j], rank.iloc[:, j][down].mean())

    dates = close.index
    post = np.array([(dates[k] - dates[k - 1]).days >= 3 for k in range(i - 19, i + 1)])
    gap = open_.iloc[:, j] / close.iloc[:, j].shift(1) - 1
    body = close.iloc[:, j] / open_.iloc[:, j] - 1
    peer_gap = (open_.div(close.shift(1)) - 1).drop(columns=close.columns[j]).mean(axis=1)
    peer_body = (close.div(open_) - 1).drop(columns=close.columns[j]).mean(axis=1)
    assert post.any()
    np.testing.assert_allclose(out["l69_post_long_break_relative_return_20"].iloc[i, j], residual.iloc[i - 19:i + 1][post].mean())
    np.testing.assert_allclose(out["l69_post_long_break_gap_excess_20"].iloc[i, j], (gap - peer_gap).iloc[i - 19:i + 1][post].mean())
    np.testing.assert_allclose(out["l69_post_long_break_body_excess_20"].iloc[i, j], (body - peer_body).iloc[i - 19:i + 1][post].mean())

    prior = residual.shift(1).iloc[i - 19:i + 1] < 0
    current = residual.iloc[i - 19:i + 1]
    assert prior.any()
    np.testing.assert_allclose(out["l70_negative_residual_recovery_rate_20"].iloc[i, j], (current[prior] > 0).mean())
    np.testing.assert_allclose(out["l70_negative_residual_recovery_magnitude_20"].iloc[i, j], current[prior & (current > 0)].mean())
    np.testing.assert_allclose(out["l70_negative_residual_nextday_mean_20"].iloc[i, j], current[prior].mean())


def test_causal_prefix_scale_and_missingness_invariance():
    p = _panels()
    names = list(DIRECTIONS)
    base = build_atoms(p, _cfg(names))
    for name, frame in base.items():
        assert frame.notna().any().any(), f"{name} produced no computable synthetic values"
    cut = p["close"].index[62]
    prefix = build_atoms({k: v.loc[:cut] for k, v in p.items()}, _cfg(names))
    perturbed = {k: v.copy() for k, v in p.items()}
    for frame in perturbed.values():
        frame.loc[frame.index > cut] *= 3.7
    future = build_atoms(perturbed, _cfg(names))
    scales = np.geomspace(0.005, 1200, p["close"].shape[1])
    scaled = {k: v.mul(scales, axis=1) for k, v in p.items()}
    scaled_out = build_atoms(scaled, _cfg(names))
    for name in base:
        pd.testing.assert_frame_equal(base[name].loc[:cut], prefix[name], check_exact=False, rtol=1e-9, atol=1e-11)
        pd.testing.assert_frame_equal(base[name].loc[:cut], future[name].loc[:cut], check_exact=False, rtol=1e-9, atol=1e-11)
        pd.testing.assert_frame_equal(base[name], scaled_out[name], check_exact=False, rtol=1e-8, atol=1e-10)

    missing = {k: v.copy() for k, v in p.items()}
    missing["close"].iloc[50, 3] = np.nan
    out = build_atoms(missing, _cfg(names))
    for name in names:
        assert out[name + "_20"].iloc[50:71].isna().all().all()

    bad_open = {k: v.copy() for k, v in p.items()}
    bad_open["open"].iloc[65, 4] = 0.0
    open_out = build_atoms(bad_open, _cfg(["l69_post_long_break_gap_excess", "l69_post_long_break_body_excess"]))
    assert open_out["l69_post_long_break_gap_excess_20"].iloc[65:85].isna().all().all()
    assert open_out["l69_post_long_break_body_excess_20"].iloc[65:85].isna().all().all()


def test_validation_rejects_wrong_window_population_and_direction():
    p = _panels()
    with pytest.raises(ValueError, match="window 20"):
        build_atoms(p, {"windows": [5], "mechanisms": {"l66_rank_upgrade_rate": {"direction": 1}}})
    with pytest.raises(ValueError, match="14-member"):
        build_atoms({k: v.iloc[:, :8] for k, v in p.items()}, _cfg(["l66_rank_upgrade_rate"]))
    with pytest.raises(ValueError, match="direction"):
        build_atoms(p, {"windows": [20], "mechanisms": {"l66_rank_upgrade_rate": {"direction": -1}}})
