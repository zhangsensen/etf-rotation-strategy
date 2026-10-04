import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_group_luna_rounds_c import DIRECTIONS, build_atoms


def _panels(n=100, members=14):
    rng = np.random.default_rng(46050)
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    cols = [f"e{i:02}" for i in range(members)]
    rets = rng.normal(0.0004, 0.009, (n, members))
    close = pd.DataFrame(100 * np.cumprod(1 + rets, axis=0), index=idx, columns=cols)
    prev = close.shift(1).fillna(close.iloc[0])
    op = prev * (1 + rng.normal(0, 0.003, (n, members)))
    op = pd.DataFrame(op, index=idx, columns=cols)
    width = rng.uniform(0.001, 0.014, (n, members))
    hi = pd.DataFrame(np.maximum(op.to_numpy(), close.to_numpy()) * (1 + width), index=idx, columns=cols)
    lo = pd.DataFrame(np.minimum(op.to_numpy(), close.to_numpy()) * (1 - width), index=idx, columns=cols)
    return {"open": op, "high": hi, "low": lo, "close": close}


def _cfg(names=None):
    names = list(DIRECTIONS) if names is None else names
    return {"windows": [20], "mechanisms": {name: {"direction": DIRECTIONS[name]} for name in names}}


def test_whitelist_selected_only_suffix_and_directions():
    names = ["l46_prior_channel_close_position", "l49_peer_gap_to_member_body_beta"]
    out = build_atoms(_panels(), _cfg(names))
    assert list(out) == [f"{name}_20" for name in names]
    assert out[names[0] + "_20"].iloc[-1].notna().any()
    assert out[names[1] + "_20"].iloc[-1].notna().any()
    bad = {"windows": [20], "mechanisms": {names[0]: {"direction": -1}}}
    with pytest.raises(ValueError, match="direction"):
        build_atoms(_panels(), bad)


def test_independent_references_channel_carry_inside_and_peer_lag():
    p = _panels()
    names = [
        "l46_prior_channel_close_position", "l47_prior_body_to_next_gap_corr",
        "l48_inside_day_rate", "l48_post_inside_return_contribution",
        "l49_peer_gap_to_member_body_beta", "l49_peer_gap_to_member_downside_range_beta",
        "l50_peer_body_to_member_gap_beta",
    ]
    out = build_atoms(p, _cfg(names))
    j, end = 0, len(p["close"]) - 1

    # Direct nested-window reference for the 20 daily positions, each against
    # the 20 prior sessions, then the prescribed 20-date mean.
    positions = []
    for t in range(end - 19, end + 1):
        prior_high = p["high"].iloc[t - 20:t, j].max()
        prior_low = p["low"].iloc[t - 20:t, j].min()
        positions.append((p["close"].iloc[t, j] - prior_low) / (prior_high - prior_low))
    np.testing.assert_allclose(out["l46_prior_channel_close_position_20"].iloc[end, j], np.mean(positions))

    # Hand reference for previous-session body return predicting today's gap.
    c, o = p["close"].iloc[:, j].to_numpy(), p["open"].iloc[:, j].to_numpy()
    body, gap = c / o - 1, o[1:] / c[:-1] - 1
    body_lag, gap_now = body[end - 20:end], gap[end - 20:end]
    np.testing.assert_allclose(out["l47_prior_body_to_next_gap_corr_20"].iloc[end, j], np.corrcoef(body_lag, gap_now)[0, 1])

    # Independent one-step relative-tie state and its next-day return product.
    inside = np.zeros(len(c), dtype=float)
    for t in range(1, len(c)):
        hp, lp = p["high"].iloc[t - 1, j], p["low"].iloc[t - 1, j]
        h, l = p["high"].iloc[t, j], p["low"].iloc[t, j]
        inside[t] = float(h / hp <= 1 + 1e-12 and l / lp >= 1 - 1e-12)
    np.testing.assert_allclose(out["l48_inside_day_rate_20"].iloc[end, j], -inside[end - 19:end + 1].mean())
    ret = c[1:] / c[:-1] - 1
    products = np.array([inside[t - 1] * ret[t - 1] for t in range(end - 19, end + 1)])
    np.testing.assert_allclose(out["l48_post_inside_return_contribution_20"].iloc[end, j], products.mean())

    # Full 14-member peer construction, lag and population OLS slope by hand.
    gaps = p["open"].to_numpy()[1:] / p["close"].to_numpy()[:-1] - 1
    bodies = p["close"].to_numpy() / p["open"].to_numpy() - 1
    x = np.delete(gaps, j, axis=1).mean(axis=1)
    y = bodies[:, j]
    xx, yy = x[end - 21:end - 1], y[end - 19:end + 1]
    beta = np.mean((xx - xx.mean()) * (yy - yy.mean())) / np.var(xx)
    np.testing.assert_allclose(out["l49_peer_gap_to_member_body_beta_20"].iloc[end, j], beta)

    downside = (p["open"].to_numpy() - p["low"].to_numpy()) / p["close"].shift(1).to_numpy()
    peer_gap = np.delete(gaps, j, axis=1).mean(axis=1)
    xx, yy = peer_gap[end - 21:end - 1], downside[end - 19:end + 1, j]
    beta = np.mean((xx - xx.mean()) * (yy - yy.mean())) / np.var(xx)
    np.testing.assert_allclose(out["l49_peer_gap_to_member_downside_range_beta_20"].iloc[end, j], -beta)

    peer_body = np.delete(bodies, j, axis=1).mean(axis=1)
    own_gap = p["open"].to_numpy()[:, j] / p["close"].shift(1).to_numpy()[:, j] - 1
    xx, yy = peer_body[end - 20:end], own_gap[end - 19:end + 1]
    beta = np.mean((xx - xx.mean()) * (yy - yy.mean())) / np.var(xx)
    np.testing.assert_allclose(out["l50_peer_body_to_member_gap_beta_20"].iloc[end, j], beta)


def test_prefix_future_perturbation_and_per_member_scale_invariance():
    p = _panels()
    names = list(DIRECTIONS)
    base = build_atoms(p, _cfg(names))
    cut = p["close"].index[67]
    prefix = build_atoms({k: v.loc[:cut] for k, v in p.items()}, _cfg(names))
    perturbed = {k: v.copy() for k, v in p.items()}
    for v in perturbed.values():
        v.loc[v.index > cut] *= 2.9
    future = build_atoms(perturbed, _cfg(names))
    scaled = {k: v.mul(np.linspace(0.007, 930.0, v.shape[1]), axis=1) for k, v in p.items()}
    scale_out = build_atoms(scaled, _cfg(names))
    for name in base:
        pd.testing.assert_frame_equal(base[name].loc[:cut], prefix[name], check_exact=False, rtol=1e-9, atol=1e-11)
        pd.testing.assert_frame_equal(base[name].loc[:cut], future[name].loc[:cut], check_exact=False, rtol=1e-9, atol=1e-11)
        pd.testing.assert_frame_equal(base[name], scale_out[name], check_exact=False, rtol=1e-8, atol=1e-10)


def test_missing_values_stay_missing_and_peer_rows_fail_closed():
    p = _panels()
    names = ["l46_prior_channel_close_position", "l48_inside_day_rate", "l49_peer_gap_to_member_body_beta"]
    p["high"].iloc[50, 3] = np.nan
    out = build_atoms(p, _cfg(names))
    # Own-symbol OHLC gap breaks local rolling windows; peer statistics fail
    # across all fixed members on any incomplete 14-member date.
    assert out["l46_prior_channel_close_position_20"].iloc[50:70, 3].isna().all()
    assert out["l48_inside_day_rate_20"].iloc[50:71, 3].isna().all()
    assert out["l49_peer_gap_to_member_body_beta_20"].iloc[50:71].isna().all().all()


def test_equal_range_boundaries_are_scale_invariant_relative_ties():
    n, members = 45, 14
    idx, cols = pd.date_range("2025-01-01", periods=n), [f"e{i:02}" for i in range(members)]
    scales = np.geomspace(0.002, 2000, members)
    hi = np.tile(102.0 * scales, (n, 1))
    lo = np.tile(98.0 * scales, (n, 1))
    op = np.tile(100.0 * scales, (n, 1))
    cl = np.tile(100.5 * scales, (n, 1))
    # Alternating sub-tolerance serialization noise must remain a boundary tie.
    eps = np.where(np.arange(n) % 2, 2e-13, -2e-13)[:, None]
    hi *= 1 + eps
    lo *= 1 - eps
    p = {k: pd.DataFrame(v, index=idx, columns=cols) for k, v in {"open": op, "high": hi, "low": lo, "close": cl}.items()}
    names = ["l48_inside_day_rate", "l48_outside_day_rate", "l46_intraday_upper_channel_penetration", "l46_upper_channel_close_acceptance", "l46_lower_channel_close_penetration"]
    out = build_atoms(p, _cfg(names))
    np.testing.assert_allclose(out[names[0] + "_20"].iloc[-1].to_numpy(), -1.0)
    np.testing.assert_allclose(out[names[1] + "_20"].iloc[-1].to_numpy(), 0.0)
    for name in names[2:]:
        np.testing.assert_allclose(out[name + "_20"].iloc[-1].to_numpy(), 0.0)


def test_zero_variance_and_missing_axes_fail_closed():
    p = _panels(55)
    for k in p:
        p[k].iloc[:, :] = 100.0
    names = ["l47_prior_body_to_next_gap_corr", "l49_peer_gap_to_member_body_beta"]
    out = build_atoms(p, _cfg(names))
    assert out[names[0] + "_20"].isna().all().all()
    assert out[names[1] + "_20"].isna().all().all()
    with pytest.raises(ValueError, match="14-member"):
        build_atoms({k: v.iloc[:, :8] for k, v in p.items()}, _cfg([names[1]]))
