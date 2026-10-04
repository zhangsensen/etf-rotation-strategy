import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_group_luna_rounds_b import DIRECTIONS, build_atoms


def _panels(n=100):
    idx = pd.date_range("2025-01-01", periods=n, freq="B")
    t = np.arange(n, dtype=float)
    cols = [f"e{i:02d}" for i in range(14)]
    rets = np.column_stack([
        0.0003 * (i - 6.5) + 0.004 * np.sin(t / (2.7 + i * 0.11) + i)
        + 0.0015 * np.cos(t / (4.1 + i * 0.07))
        for i in range(14)
    ])
    close = pd.DataFrame(40.0 * np.cumprod(1.0 + rets, axis=0), index=idx, columns=cols)
    activity = np.column_stack([
        0.12 * np.sin(t / (3.2 + i * 0.09) + i / 3.0)
        + 0.06 * np.cos(t / (5.3 + i * 0.05) - i / 2.0)
        for i in range(14)
    ])
    amount = pd.DataFrame(
        np.exp(13.0 + 0.003 * t[:, None] + activity) * (1.0 + 0.01 * np.arange(14)[None, :]),
        index=idx, columns=cols,
    )
    return {"close": close, "amount": amount}


def _cfg(*names):
    return {"windows": [20], "mechanisms": {name: {"direction": DIRECTIONS[name]} for name in names}}


def _activity(p):
    log_amount = np.log(p["amount"].where(p["amount"] > 0))
    return log_amount - log_amount.shift(1).rolling(20, min_periods=20).mean()


def test_selected_outputs_and_l41_beta_match_independent_reference():
    p = _panels()
    names = ("l41_peer_amount_to_return_beta", "l45_peer_flow_lagged_correlation")
    out = build_atoms(p, _cfg(*names))
    assert set(out) == {f"{name}_20" for name in names}

    activity = _activity(p)
    returns = p["close"].pct_change(fill_method=None)
    at = p["close"].index[-1]
    pos = p["close"].index.get_loc(at)
    member = p["close"].columns[3]
    peer = activity.iloc[pos - 20:pos, [i for i in range(14) if i != 3]].mean(axis=1).to_numpy()
    own_return = returns[member].iloc[pos - 19:pos + 1].to_numpy()
    # Beta at t pairs r[t-19:t] with peer_activity[t-20:t-1].
    x = activity.iloc[pos - 20:pos, [i for i in range(14) if i != 3]].mean(axis=1).to_numpy()
    y = returns[member].iloc[pos - 19:pos + 1].to_numpy()
    expected = np.mean((x - x.mean()) * (y - y.mean())) / np.var(x, ddof=0)
    assert np.isfinite(peer).all() and np.isfinite(own_return).all()
    np.testing.assert_allclose(out["l41_peer_amount_to_return_beta_20"].loc[at, member], expected)


def test_correlation_spread_and_peer_activity_breadth_match_hand_formulas():
    p = _panels()
    names = (
        "l41_peer_amount_return_correlation",
        "l42_peer_flow_impact_spread",
        "l43_peer_amount_inflow_breadth",
    )
    out = build_atoms(p, _cfg(*names))
    activity = _activity(p)
    returns = p["close"].pct_change(fill_method=None)
    at = p["close"].index[-1]
    pos = p["close"].index.get_loc(at)
    j = 5
    cols = [k for k in range(14) if k != j]
    peer = activity.iloc[:, cols].mean(axis=1)
    x = peer.iloc[pos - 20:pos].to_numpy()
    y = returns.iloc[pos - 19:pos + 1, j].to_numpy()
    np.testing.assert_allclose(
        out["l41_peer_amount_return_correlation_20"].loc[at].iloc[j],
        np.corrcoef(x, y)[0, 1], rtol=1e-10, atol=1e-12,
    )

    x_now = peer.iloc[pos - 19:pos + 1].to_numpy()
    signed_beta = np.cov(x_now, y, ddof=0)[0, 1] / np.var(x_now, ddof=0)
    absolute_x = np.abs(x_now)
    absolute_beta = np.cov(absolute_x, y, ddof=0)[0, 1] / np.var(absolute_x, ddof=0)
    np.testing.assert_allclose(
        out["l42_peer_flow_impact_spread_20"].loc[at].iloc[j],
        signed_beta - absolute_beta, rtol=1e-10, atol=1e-12,
    )

    positive = activity.gt(0.0).astype(float)
    expected_breadth = positive.iloc[pos - 19:pos + 1, cols].mean(axis=1).mean()
    np.testing.assert_allclose(
        out["l43_peer_amount_inflow_breadth_20"].loc[at].iloc[j],
        expected_breadth, rtol=1e-10, atol=1e-12,
    )


def test_all_candidates_prefix_future_perturbation_and_scale_invariance():
    p = _panels()
    names = tuple(DIRECTIONS)
    cfg = _cfg(*names)
    baseline = build_atoms(p, cfg)
    cut = p["close"].index[72]
    prefix = build_atoms({k: v.loc[:cut] for k, v in p.items()}, cfg)
    changed = {k: v.copy() for k, v in p.items()}
    for frame in changed.values():
        frame.loc[frame.index > cut] *= 3.71
    future = build_atoms(changed, cfg)
    for key, frame in baseline.items():
        pd.testing.assert_frame_equal(frame.loc[:cut], prefix[key], check_exact=False, rtol=1e-10, atol=1e-12)
        pd.testing.assert_frame_equal(frame.loc[:cut], future[key].loc[:cut], check_exact=False, rtol=1e-10, atol=1e-12)

    scaled = {k: v.copy() for k, v in p.items()}
    scaled["close"] *= 19.0
    scaled["amount"] *= np.linspace(0.3, 7.0, 14)[None, :]
    scale_out = build_atoms(scaled, cfg)
    for key, frame in baseline.items():
        pd.testing.assert_frame_equal(frame, scale_out[key], check_exact=False, rtol=2e-9, atol=2e-11)


def test_missing_member_invalidates_fixed_pool_and_bad_values_are_nan():
    p = _panels()
    cfg = _cfg("l41_peer_amount_to_return_beta", "l43_peer_amount_inflow_breadth")
    missing = {k: v.copy() for k, v in p.items()}
    missing["amount"].iloc[40, 4] = np.nan
    out = build_atoms(missing, cfg)
    assert out["l41_peer_amount_to_return_beta_20"].iloc[40:61].isna().all().all()
    bad = {k: v.copy() for k, v in p.items()}
    bad["amount"].iloc[50, 2] = 0.0
    assert build_atoms(bad, cfg)["l43_peer_amount_inflow_breadth_20"].iloc[50].isna().all()
    bad_close = {k: v.copy() for k, v in p.items()}
    bad_close["close"].iloc[50, 2] = 0.0
    assert build_atoms(bad_close, cfg)["l41_peer_amount_to_return_beta_20"].iloc[50].isna().all()


def test_extreme_state_minimum_count_and_tied_threshold_are_explicit():
    p = _panels()
    cfg = _cfg("l41_peer_flow_reversal_beta")
    p["amount"].iloc[:, :] = 100.0
    # Zero-variance predictors make the beta undefined even though >= threshold
    # includes all tied zero shocks; denominator handling must remain NaN.
    out = build_atoms(p, cfg)["l41_peer_flow_reversal_beta_20"]
    assert out.isna().all().all()


def test_partial_regression_returns_nan_for_collinear_inputs():
    p = _panels(80)
    t = np.arange(len(p["close"]), dtype=float)
    common = np.exp(12.0 + 0.02 * np.sin(t / 3.0))
    p["amount"] = pd.DataFrame(np.repeat(common[:, None], 14, axis=1), index=p["close"].index, columns=p["close"].columns)
    out = build_atoms(p, _cfg("l42_amount_neutral_peer_response"))["l42_amount_neutral_peer_response_20"]
    assert out.isna().all().all()


def test_requires_fixed_pool_and_frozen_direction():
    p = _panels()
    one_less = {k: v.iloc[:, :-1] for k, v in p.items()}
    with pytest.raises(ValueError, match="fixed 14-member"):
        build_atoms(one_less, _cfg("l41_peer_amount_to_return_beta"))
    bad = {"windows": [20], "mechanisms": {"l42_peer_flow_impact_spread": {"direction": -1}}}
    with pytest.raises(ValueError, match="direction mismatch"):
        build_atoms(p, bad)
