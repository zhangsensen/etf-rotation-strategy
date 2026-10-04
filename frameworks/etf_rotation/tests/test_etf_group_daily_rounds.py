import numpy as np
import pandas as pd
import pytest
import yaml

from etf_strategy.core.etf_group_daily_rounds import build_atoms, build_paired_legs, leakage_checks


ROOT = "frameworks/etf_rotation/"


def _panels(n=80):
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    close = pd.DataFrame({"a": np.linspace(100, 130, n), "b": np.linspace(80, 100, n)}, index=idx)
    open_ = close * 0.99
    high = pd.concat((open_, close), axis=0).groupby(level=0).max() * 1.01
    low = pd.concat((open_, close), axis=0).groupby(level=0).min() * 0.99
    volume = pd.DataFrame({"a": np.linspace(1000, 2000, n), "b": np.linspace(800, 1600, n)}, index=idx)
    amount = volume * close
    return {"open": open_, "high": high, "low": low, "close": close, "volume": volume, "amount": amount}


def _varied_panels(n=80):
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    t = np.arange(n, dtype=float)
    returns = pd.DataFrame({
        "a": 0.004 + 0.002 * np.sin(t / 3.0),
        "b": -0.001 + 0.003 * np.cos(t / 4.0),
        "c": 0.002 * np.sin(t / 5.0) - 0.001 * np.cos(t / 7.0),
    }, index=idx)
    close = 100.0 * (1.0 + returns).cumprod()
    columns = len(close.columns)
    open_scale = np.repeat(1.0 + 0.0005 * np.cos(t[:, None] / 2.0), columns, axis=1)
    open_ = close.shift(1).fillna(close.iloc[0]) * open_scale
    span = np.repeat(0.006 + 0.003 * (1.0 + np.sin(t[:, None] / 6.0)), columns, axis=1)
    high = pd.DataFrame(np.maximum(open_.to_numpy(), close.to_numpy()) * (1.0 + span), index=idx, columns=close.columns)
    low = pd.DataFrame(np.minimum(open_.to_numpy(), close.to_numpy()) * (1.0 - span), index=idx, columns=close.columns)
    volume_values = np.repeat(1200.0 + 250.0 * (1.0 + np.cos(t[:, None] / 4.0)), columns, axis=1)
    volume = pd.DataFrame(volume_values, index=idx, columns=close.columns)
    amount = volume * close
    return {"open": open_, "high": high, "low": low, "close": close, "volume": volume, "amount": amount}


def _cfg(name):
    return yaml.safe_load(open(f"{ROOT}configs/{name}_20260922.yaml"))


@pytest.mark.parametrize("name,formula", [
    ("group_ic_round3", "wick_demand_20"),
    ("group_ic_round4", "clv_volume_pressure_20"),
    ("group_ic_round5", "lagged_volume_return_corr_20"),
])
def test_one_exact_plus_one_and_full_window(name, formula):
    cfg = _cfg(name)
    assert list(cfg["mechanisms"]) == [formula.removesuffix("_20")]
    assert cfg["mechanisms"][formula.removesuffix("_20")]["direction"] == 1
    out = build_atoms(_panels(), cfg)[formula]
    assert out.iloc[:19].isna().all().all()
    assert out.iloc[19:].notna().any().any()


def test_wick_demand_hand_calculation():
    idx = pd.date_range("2025-01-01", periods=20, freq="D")
    p = {
        "open": pd.DataFrame(10.0, index=idx, columns=["a"]),
        "close": pd.DataFrame(10.0, index=idx, columns=["a"]),
        "high": pd.DataFrame(11.0, index=idx, columns=["a"]),
        "low": pd.DataFrame(8.0, index=idx, columns=["a"]),
        "volume": pd.DataFrame(100.0, index=idx, columns=["a"]),
    }
    out = build_atoms(p, _cfg("group_ic_round3"))["wick_demand_20"]
    np.testing.assert_allclose(out.iloc[-1, 0], 1.0 / 3.0)
    p["low"].iloc[:, 0] = 9.0
    p["high"].iloc[:, 0] = 12.0
    negative = build_atoms(p, _cfg("group_ic_round3"))["wick_demand_20"]
    np.testing.assert_allclose(negative.iloc[-1, 0], -1.0 / 3.0)


@pytest.mark.parametrize("cfg_name", ["group_ic_round3", "group_ic_round4", "group_ic_round5"])
def test_prefix_future_scale_and_missing(cfg_name):
    p = _panels(80)
    cfg = _cfg(cfg_name)
    assert build_atoms(p, cfg)[next(iter(cfg["mechanisms"])) + "_20"].iloc[60:].notna().any().any()
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())
    scaled = {k: v.copy() for k, v in p.items()}
    for k in ("open", "high", "low", "close"):
        scaled[k] *= 17.0
    scaled["volume"] *= 13.0
    original, rescaled = build_atoms(p, cfg), build_atoms(scaled, cfg)
    for key in original:
        pd.testing.assert_frame_equal(original[key], rescaled[key], check_exact=False, rtol=1e-10, atol=1e-12)
    broken = {k: v.copy() for k, v in p.items()}
    broken["close"].iloc[25, 0] = np.nan
    broken_out = build_atoms(broken, cfg)[next(iter(original))]
    assert broken_out.iloc[30, 0] != broken_out.iloc[30, 0]


def test_all_nan_is_not_a_vacuous_pass():
    p = _panels(25)
    for frame in p.values():
        frame.iloc[:, :] = np.nan
    for cfg_name in ("group_ic_round3", "group_ic_round4", "group_ic_round5"):
        out = build_atoms(p, _cfg(cfg_name))
        assert out and all(frame.isna().all().all() for frame in out.values())


def _batch6_cfg():
    return _cfg("group_ic20_batch6")


def _batch7_cfg():
    return _cfg("group_ic20_batch7")


def _batch9_daily_cfg():
    return _cfg("group_ic20_batch9_daily")


def _batch9_minute_cfg():
    return _cfg("group_ic20_batch9_minute")


def _batch10_daily_cfg():
    return _cfg("group_ic20_batch10_daily")


def _batch11_cfg():
    return _cfg("group_ic20_batch11")


def _batch13_cfg():
    return _cfg("group_ic20_batch13")


def _batch14_daily_cfg():
    return yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch14_daily_20260923.yaml"))


def _batch15_daily_cfg():
    return yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch15_daily_20260923.yaml"))


def test_batch7_exact_whitelist_directions_and_full_windows():
    cfg = _batch7_cfg()
    assert cfg["prior_registered"] == 134
    assert cfg["budget_cap"] == 138
    assert cfg["external_registered_definitions"] == 8
    assert list(cfg["mechanisms"]) == [
        "market_residual_skew",
        "direction_range_coupling",
        "amount_concentration",
        "amount_innovation_return_beta",
    ]
    assert [cfg["mechanisms"][name]["direction"] for name in cfg["mechanisms"]] == [1, 1, -1, 1]
    out = build_atoms(_varied_panels(), cfg)
    assert list(out) == [
        "market_residual_skew_20",
        "direction_range_coupling_20",
        "amount_concentration_20",
        "amount_innovation_return_beta_20",
    ]
    assert out["market_residual_skew_20"].iloc[:20].isna().all().all()
    assert out["direction_range_coupling_20"].iloc[:20].isna().all().all()
    assert out["amount_concentration_20"].iloc[:19].isna().all().all()
    assert out["amount_innovation_return_beta_20"].iloc[:20].isna().all().all()
    assert all(frame.iloc[30:].notna().all().all() for frame in out.values())


def test_batch7_hand_formulas_and_frozen_negative_direction():
    p = _varied_panels()
    cfg = _batch7_cfg()
    out = build_atoms(p, cfg)
    close, high, low, amount = p["close"], p["high"], p["low"], p["amount"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    residual = returns.sub(returns.mean(axis=1).where(all_members), axis=0).where(all_members, axis=0)
    mean = residual.rolling(20, min_periods=20).mean()
    second = residual.pow(2).rolling(20, min_periods=20).mean()
    third = residual.pow(3).rolling(20, min_periods=20).mean()
    m2 = (second - mean.pow(2)).clip(lower=0.0)
    expected_skew = (third - 3.0 * mean * second + 2.0 * mean.pow(3)).div(m2.pow(1.5).where(m2.gt(0)))
    expected_skew = expected_skew.where(_complete_window_for_test(residual.notna()))
    pd.testing.assert_frame_equal(out["market_residual_skew_20"], expected_skew)

    q = (high - low).div(close.shift(1))
    expected_range = returns.rolling(20, min_periods=20).corr(q)
    pd.testing.assert_frame_equal(out["direction_range_coupling_20"], expected_range)

    total = amount.rolling(20, min_periods=20).sum()
    expected_concentration = -amount.pow(2).rolling(20, min_periods=20).sum().div(total.pow(2))
    expected_concentration = expected_concentration.where(_complete_window_for_test(amount.gt(0)))
    pd.testing.assert_frame_equal(out["amount_concentration_20"], expected_concentration)

    x = np.log(amount).diff()
    mean_x = x.rolling(20, min_periods=20).mean()
    mean_r = returns.rolling(20, min_periods=20).mean()
    covariance = (x * returns).rolling(20, min_periods=20).mean() - mean_x * mean_r
    variance = x.pow(2).rolling(20, min_periods=20).mean() - mean_x.pow(2)
    expected_beta = covariance.div(variance.where(variance.gt(0)))
    expected_beta = expected_beta.where(_complete_window_for_test(x.notna() & returns.notna()))
    pd.testing.assert_frame_equal(out["amount_innovation_return_beta_20"], expected_beta)
    np.testing.assert_allclose(out["amount_concentration_20"].iloc[-1, 0], expected_concentration.iloc[-1, 0])


def _complete_window_for_test(complete, window=20):
    return complete.astype(float).rolling(window, min_periods=window).sum().eq(window)


def test_batch7_missing_prefix_future_and_canonical_amount():
    p = _varied_panels()
    cfg = _batch7_cfg()
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())
    broken = {k: v.copy() for k, v in p.items()}
    broken["close"].iloc[30, 0] = np.nan
    broken_out = build_atoms(broken, cfg)
    assert broken_out["market_residual_skew_20"].iloc[49].isna().all()
    assert broken_out["direction_range_coupling_20"].iloc[49, 0] != broken_out["direction_range_coupling_20"].iloc[49, 0]
    broken_amount = {k: v.copy() for k, v in p.items()}
    broken_amount["amount"].iloc[30, 0] = 0.0
    amount_out = build_atoms(broken_amount, cfg)
    assert amount_out["amount_concentration_20"].iloc[49, 0] != amount_out["amount_concentration_20"].iloc[49, 0]
    assert amount_out["amount_innovation_return_beta_20"].iloc[49, 0] != amount_out["amount_innovation_return_beta_20"].iloc[49, 0]
    changed_volume = {k: v.copy() for k, v in p.items()}
    changed_volume["volume"] *= 37.0
    volume_out = build_atoms(changed_volume, cfg)
    for name in ("amount_concentration_20", "amount_innovation_return_beta_20"):
        pd.testing.assert_frame_equal(build_atoms(p, cfg)[name], volume_out[name])


def test_batch9_daily_exact_whitelist_directions_and_full_windows():
    cfg = _batch9_daily_cfg()
    assert cfg["prior_registered"] == 141
    assert cfg["budget_cap"] == 143
    assert cfg["external_registered_definitions"] == 8
    assert list(cfg["mechanisms"]) == [
        "market_residual_abs_cluster",
        "range_to_return_lead",
    ]
    assert [cfg["mechanisms"][name]["direction"] for name in cfg["mechanisms"]] == [-1, 1]
    out = build_atoms(_varied_panels(), cfg)
    assert list(out) == ["market_residual_abs_cluster_20", "range_to_return_lead_20"]
    assert out["market_residual_abs_cluster_20"].iloc[:20].isna().all().all()
    assert out["range_to_return_lead_20"].iloc[:20].isna().all().all()
    assert all(frame.iloc[30:].notna().all().all() for frame in out.values())


def test_batch9_daily_hand_formulas_negative_direction_and_missing_market_reference():
    p = _varied_panels()
    cfg = _batch9_daily_cfg()
    out = build_atoms(p, cfg)
    returns = p["close"].pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    residual = returns.sub(market, axis=0).where(all_members, axis=0)
    z = residual.abs()
    lagged = z.shift(1)
    complete = lagged.notna() & z.notna()
    expected_cluster = lagged.rolling(20, min_periods=20).corr(z)
    expected_cluster = (-expected_cluster).where(_complete_window_for_test(complete))
    pd.testing.assert_frame_equal(out["market_residual_abs_cluster_20"], expected_cluster)

    daily_range = (p["high"] - p["low"]).div(p["close"].shift(1))
    pair_complete = daily_range.shift(1).notna() & returns.notna()
    expected_lead = daily_range.shift(1).rolling(20, min_periods=20).corr(returns)
    expected_lead = expected_lead.where(_complete_window_for_test(pair_complete))
    pd.testing.assert_frame_equal(out["range_to_return_lead_20"], expected_lead)

    broken = {key: value.copy() for key, value in p.items()}
    broken["close"].iloc[30, 0] = np.nan
    broken_out = build_atoms(broken, cfg)
    assert broken_out["market_residual_abs_cluster_20"].iloc[49].isna().all()
    assert broken_out["market_residual_abs_cluster_20"].iloc[60].notna().all()
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())


def test_batch9_minute_split_config_contract():
    cfg = _batch9_minute_cfg()
    assert cfg["source_type"] == "minute"
    assert cfg["prior_registered"] == 143
    assert cfg["budget_cap"] == 146
    assert cfg["new_definitions"] == 3
    assert cfg["external_registered_definitions"] == 8
    assert list(cfg["mechanisms"]) == [
        "minute_range_persistence",
        "minute_signed_flow_persistence",
        "minute_range_skew",
    ]
    assert [cfg["mechanisms"][name]["direction"] for name in cfg["mechanisms"]] == [-1, 1, -1]


def test_batch6_exact_whitelist_and_all_six_outputs():
    cfg = _batch6_cfg()
    assert len(cfg["mechanisms"]) == 6
    out = build_atoms(_panels(), cfg)
    assert list(out) == [
        "market_residual_downside_20",
        "body_transition_asymmetry_20",
        "realized_vol_term_structure_5_20",
        "amount_signed_imbalance_20",
        "amount_return_asymmetry_20",
        "return_acceleration_5_20",
    ]
    for name, frame in out.items():
        assert frame.iloc[:19].isna().all().all()
        # A monotone fixture has no positive/negative body transitions, so
        # the transition-asymmetry denominator is intentionally undefined.
        if name != "body_transition_asymmetry_20":
            assert frame.iloc[30:].notna().any().any()


def test_batch6_market_residual_requires_all_members_and_amount_is_canonical():
    p = _panels(80)
    cfg = _batch6_cfg()
    # The production population has 14 members; one missing return invalidates
    # every residual on that date, then only the affected trailing windows.
    extra = {f"x{i}": p["close"]["a"] * (1.0 + i / 100.0) for i in range(12)}
    for key in ("open", "high", "low", "close", "volume", "amount"):
        p[key] = p[key].join(pd.DataFrame(extra, index=p[key].index))
    p["close"].iloc[30, 7] = np.nan
    out = build_atoms(p, cfg)
    assert out["market_residual_downside_20"].iloc[30].isna().all()
    assert out["market_residual_downside_20"].iloc[49].isna().all()
    assert out["market_residual_downside_20"].iloc[60].notna().all()

    # Amount formulas must not silently use volume.  Changing only volume
    # leaves both canonical-amount atoms unchanged.
    changed = {k: v.copy() for k, v in p.items()}
    changed["volume"] *= 37.0
    original = build_atoms(p, cfg)
    volume_changed = build_atoms(changed, cfg)
    for name in ("amount_signed_imbalance_20", "amount_return_asymmetry_20"):
        pd.testing.assert_frame_equal(original[name], volume_changed[name])
    zero_amount = {k: v.copy() for k, v in p.items()}
    zero_amount["amount"].iloc[25, 0] = 0.0
    zero_out = build_atoms(zero_amount, cfg)
    assert zero_out["amount_signed_imbalance_20"].iloc[44, 0] != zero_out["amount_signed_imbalance_20"].iloc[44, 0]
    assert zero_out["amount_return_asymmetry_20"].iloc[44, 0] != zero_out["amount_return_asymmetry_20"].iloc[44, 0]
    assert zero_out["amount_signed_imbalance_20"].iloc[60, 0] == original["amount_signed_imbalance_20"].iloc[60, 0]


def test_batch6_hand_formulas_scale_and_leakage():
    p = _panels(80)
    cfg = _batch6_cfg()
    out = build_atoms(p, cfg)
    close, amount = p["close"], p["amount"]
    returns = close.pct_change(fill_method=None)
    expected_accel = returns.rolling(5, min_periods=5).mean() - returns.rolling(20, min_periods=20).mean()
    pd.testing.assert_frame_equal(out["return_acceleration_5_20"], expected_accel)
    expected_asi = (amount * np.sign(returns)).rolling(20, min_periods=20).sum().div(
        amount.rolling(20, min_periods=20).sum()
    )
    pd.testing.assert_frame_equal(out["amount_signed_imbalance_20"], expected_asi)
    expected_ara_num = (amount * returns).rolling(20, min_periods=20).sum()
    expected_ara_den = (amount * returns.abs()).rolling(20, min_periods=20).sum()
    expected_ara = expected_ara_num.div(expected_ara_den.where(expected_ara_den.ne(0)))
    pd.testing.assert_frame_equal(out["amount_return_asymmetry_20"], expected_ara)
    raw_rvts = returns.rolling(5, min_periods=5).std().div(
        returns.rolling(20, min_periods=20).std()
    )
    pd.testing.assert_frame_equal(out["realized_vol_term_structure_5_20"], -raw_rvts)
    all_members = returns.notna().all(axis=1)
    market = returns.mean(axis=1).where(all_members)
    residual = returns.sub(market, axis=0).where(all_members, axis=0)
    raw_mrd = np.sqrt(residual.clip(upper=0).pow(2).rolling(20, min_periods=20).mean())
    pd.testing.assert_frame_equal(out["market_residual_downside_20"], -raw_mrd)
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())

    scaled = {k: v.copy() for k, v in p.items()}
    for key in ("open", "high", "low", "close"):
        scaled[key] *= 17.0
    scaled["volume"] *= 13.0
    scaled["amount"] *= 29.0
    scaled_out = build_atoms(scaled, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], scaled_out[name], check_exact=False, rtol=1e-10, atol=1e-12)


def test_batch6_body_transition_uses_nineteen_transitions_per_twenty_states():
    idx = pd.date_range("2025-01-01", periods=45, freq="D")
    close = pd.DataFrame(index=idx)
    open_ = pd.DataFrame(index=idx)
    state_a = ([-1] * 10) + ([1] * 10) + ([-1] * 10) + ([1] * 15)
    state_b = ([1] * 10) + ([-1] * 10) + ([1] * 10) + ([-1] * 15)
    for col, pattern in {"a": state_a, "b": state_b}.items():
        open_[col] = 100.0
        close[col] = 100.0 + np.asarray(pattern[:45], dtype=float)
    high = pd.concat((open_, close), axis=0).groupby(level=0).max() + 1.0
    low = pd.concat((open_, close), axis=0).groupby(level=0).min() - 1.0
    amount = pd.DataFrame(100.0, index=idx, columns=close.columns)
    panels = {"open": open_, "high": high, "low": low, "close": close, "amount": amount}
    out = build_atoms(panels, _batch6_cfg())["body_transition_asymmetry_20"]
    # At the first mature date, 20 body states provide 19 transitions;
    # subsequent mature dates remain valid instead of being masked as 20.
    assert out.iloc[19:].notna().all().all()
    np.testing.assert_allclose(out.iloc[19, 0], 0.1)
    np.testing.assert_allclose(out.iloc[19, 1], -0.1)


def test_batch10_daily_exact_whitelist_directions_and_full_windows():
    cfg = _batch10_daily_cfg()
    assert cfg["prior_registered"] == 146
    assert cfg["budget_cap"] == 149
    assert cfg["external_registered_definitions"] == 8
    assert list(cfg["mechanisms"]) == [
        "market_residual_downshock_recovery",
        "market_residual_range_return_lead",
        "market_residual_amount_beta",
    ]
    assert [cfg["mechanisms"][name]["direction"] for name in cfg["mechanisms"]] == [1, 1, 1]
    out = build_atoms(_varied_panels(), cfg)
    assert list(out) == [
        "market_residual_downshock_recovery_20",
        "market_residual_range_return_lead_20",
        "market_residual_amount_beta_20",
    ]
    assert out["market_residual_downshock_recovery_20"].iloc[:21].isna().all().all()
    assert out["market_residual_range_return_lead_20"].iloc[:20].isna().all().all()
    assert out["market_residual_amount_beta_20"].iloc[:20].isna().all().all()
    assert out["market_residual_downshock_recovery_20"].iloc[30:, 1:].notna().all().all()
    assert all(out[name].iloc[30:].notna().all().all() for name in (
        "market_residual_range_return_lead_20", "market_residual_amount_beta_20"
    ))


def test_batch10_daily_hand_formulas_and_canonical_amount():
    p = _varied_panels()
    out = build_atoms(p, _batch10_daily_cfg())
    close, high, low, amount = p["close"], p["high"], p["low"], p["amount"]
    returns = close.pct_change(fill_method=None)
    all_members = returns.notna().all(axis=1)
    residual = returns.sub(returns.mean(axis=1).where(all_members), axis=0).where(all_members, axis=0)
    previous_down = residual.shift(1).clip(upper=0).abs()
    expected_recovery = previous_down.mul(residual).rolling(20, min_periods=20).sum().div(
        previous_down.pow(2).rolling(20, min_periods=20).sum()
    )
    expected_recovery = expected_recovery.where(
        _complete_window_for_test(previous_down.notna() & residual.notna())
    )
    pd.testing.assert_frame_equal(out["market_residual_downshock_recovery_20"], expected_recovery)

    q = (high - low).div(close.shift(1))
    expected_range = q.shift(1).rolling(20, min_periods=20).corr(residual)
    expected_range = expected_range.where(
        _complete_window_for_test(q.shift(1).notna() & residual.notna())
    )
    pd.testing.assert_frame_equal(out["market_residual_range_return_lead_20"], expected_range)

    x = np.log(amount).diff()
    mean_x = x.rolling(20, min_periods=20).mean()
    mean_u = residual.rolling(20, min_periods=20).mean()
    covariance = (x * residual).rolling(20, min_periods=20).mean() - mean_x * mean_u
    variance = x.pow(2).rolling(20, min_periods=20).mean() - mean_x.pow(2)
    expected_beta = covariance.div(variance.where(variance.gt(0)))
    expected_beta = expected_beta.where(_complete_window_for_test(x.notna() & residual.notna()))
    pd.testing.assert_frame_equal(out["market_residual_amount_beta_20"], expected_beta)

    changed_volume = {k: v.copy() for k, v in p.items()}
    changed_volume["volume"] *= 37.0
    pd.testing.assert_frame_equal(
        out["market_residual_amount_beta_20"],
        build_atoms(changed_volume, _batch10_daily_cfg())["market_residual_amount_beta_20"],
    )
    zero_amount = {k: v.copy() for k, v in p.items()}
    zero_amount["amount"].iloc[30, 0] = 0.0
    assert pd.isna(build_atoms(zero_amount, _batch10_daily_cfg())[
        "market_residual_amount_beta_20"
    ].iloc[49, 0])


def test_batch10_daily_residual_missing_prefix_future_and_scale():
    p = _varied_panels()
    cfg = _batch10_daily_cfg()
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())
    broken = {k: v.copy() for k, v in p.items()}
    broken["close"].iloc[30, 0] = np.nan
    broken_out = build_atoms(broken, cfg)
    for name in cfg["mechanisms"]:
        assert pd.isna(broken_out[f"{name}_20"].iloc[49, 0])
    assert broken_out["market_residual_downshock_recovery_20"].iloc[70, 1:].notna().all()
    for name in ("market_residual_range_return_lead", "market_residual_amount_beta"):
        assert broken_out[f"{name}_20"].iloc[70].notna().all()
    scaled = {k: v.copy() for k, v in p.items()}
    for key in ("open", "high", "low", "close"):
        scaled[key] *= 17.0
    scaled["volume"] *= 13.0
    scaled["amount"] *= 29.0
    scaled_out = build_atoms(scaled, cfg)
    for name in build_atoms(p, cfg):
        pd.testing.assert_frame_equal(build_atoms(p, cfg)[name], scaled_out[name], check_exact=False,
                                      rtol=1e-10, atol=1e-12)


def test_batch11_exact_whitelist_directions_and_20_pair_boundary():
    cfg = _batch11_cfg()
    assert cfg["discovery_surface"] == "2025_POST_OUTCOME_DISCOVERY"
    assert cfg["prior_registered"] == 151
    assert cfg["budget_cap"] == 154
    assert cfg["external_registered_definitions"] == 8
    assert list(cfg["mechanisms"]) == [
        "intraday_body_ar1", "wick_body_coupling", "close_location_dispersion"
    ]
    assert [cfg["mechanisms"][name]["direction"] for name in cfg["mechanisms"]] == [1, -1, -1]
    p20 = _varied_panels(20)
    out20 = build_atoms(p20, cfg)
    assert out20["intraday_body_ar1_20"].isna().all().all()
    assert out20["wick_body_coupling_20"].iloc[:19].isna().all().all()
    assert out20["close_location_dispersion_20"].iloc[:19].isna().all().all()
    p21 = _varied_panels(21)
    out21 = build_atoms(p21, cfg)
    assert out21["intraday_body_ar1_20"].iloc[19].isna().all()
    assert out21["intraday_body_ar1_20"].iloc[20].notna().all()
    assert out21["wick_body_coupling_20"].iloc[19].notna().all()
    assert out21["close_location_dispersion_20"].iloc[19].notna().all()


def test_batch11_hand_formulas_and_frozen_directions():
    p = _varied_panels(80)
    out = build_atoms(p, _batch11_cfg())
    open_, high, low, close = (p[key] for key in ("open", "high", "low", "close"))
    body = close.div(open_).sub(1.0)
    expected_ar1 = body.rolling(20, min_periods=20).corr(body.shift(1))
    expected_ar1 = expected_ar1.where(
        _complete_window_for_test(body.notna() & body.shift(1).notna())
    )
    pd.testing.assert_frame_equal(out["intraday_body_ar1_20"], expected_ar1)

    wick = (
        (np.minimum(open_.to_numpy(), close.to_numpy()) - low.to_numpy())
        - (high.to_numpy() - np.maximum(open_.to_numpy(), close.to_numpy()))
    )
    wick = pd.DataFrame(wick, index=open_.index, columns=open_.columns).div(
        (high - low).where((high - low).ne(0))
    )
    expected_coupling = wick.rolling(20, min_periods=20).corr(body)
    expected_coupling = -expected_coupling.where(
        _complete_window_for_test(wick.notna() & body.notna())
    )
    pd.testing.assert_frame_equal(out["wick_body_coupling_20"], expected_coupling)

    location = (2.0 * close - high - low).div((high - low).where((high - low).ne(0)))
    expected_dispersion = -location.rolling(20, min_periods=20).std()
    expected_dispersion = expected_dispersion.where(
        _complete_window_for_test(location.notna())
    )
    pd.testing.assert_frame_equal(out["close_location_dispersion_20"], expected_dispersion)


def test_batch11_zero_range_zero_variance_nan_propagation_and_leakage():
    p = _varied_panels(80)
    cfg = _batch11_cfg()
    zero_range = {key: value.copy() for key, value in p.items()}
    zero_range["high"].iloc[25, 0] = zero_range["low"].iloc[25, 0]
    zero_range_out = build_atoms(zero_range, cfg)
    assert pd.isna(zero_range_out["wick_body_coupling_20"].iloc[44, 0])
    assert pd.isna(zero_range_out["close_location_dispersion_20"].iloc[44, 0])

    zero_variance = {key: value.copy() for key, value in p.items()}
    zero_variance["open"].iloc[:, 0] = 100.0
    zero_variance["close"].iloc[:, 0] = 100.0
    zero_variance["high"].iloc[:, 0] = 101.0
    zero_variance["low"].iloc[:, 0] = 99.0
    zero_variance_out = build_atoms(zero_variance, cfg)
    assert pd.isna(zero_variance_out["intraday_body_ar1_20"].iloc[40, 0])
    assert pd.isna(zero_variance_out["wick_body_coupling_20"].iloc[40, 0])
    assert zero_variance_out["close_location_dispersion_20"].iloc[40, 0] == 0.0

    broken = {key: value.copy() for key, value in p.items()}
    broken["close"].iloc[30, 0] = np.nan
    broken_out = build_atoms(broken, cfg)
    for name in cfg["mechanisms"]:
        assert pd.isna(broken_out[f"{name}_20"].iloc[49, 0])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())


def _expected_batch13_corr(left, right, complete):
    mean_left = left.rolling(20, min_periods=20).mean()
    mean_right = right.rolling(20, min_periods=20).mean()
    covariance = (
        left.mul(right).rolling(20, min_periods=20).mean()
        - mean_left * mean_right
    )
    variance_left = (
        left.pow(2).rolling(20, min_periods=20).mean()
        - mean_left.pow(2)
    ).clip(lower=0.0)
    variance_right = (
        right.pow(2).rolling(20, min_periods=20).mean()
        - mean_right.pow(2)
    ).clip(lower=0.0)
    denominator = (variance_left * variance_right).pow(0.5)
    return covariance.div(denominator.where(denominator.gt(0))).where(
        _complete_window_for_test(complete)
    )


def test_batch13_exact_whitelist_directions_and_20_day_boundary():
    cfg = _batch13_cfg()
    assert cfg["discovery_surface"] == "2025_POST_OUTCOME_DISCOVERY"
    assert cfg["prior_registered"] == 155
    assert cfg["budget_cap"] == 158
    assert cfg["external_registered_definitions"] == 8
    assert cfg["new_definitions"] == 3
    assert list(cfg["mechanisms"]) == [
        "gap_body_magnitude_coupling",
        "amount_gap_shock_response_corr",
        "range_body_absorption_corr",
    ]
    assert [cfg["mechanisms"][name]["direction"] for name in cfg["mechanisms"]] == [-1, -1, -1]
    out = build_atoms(_varied_panels(), cfg)
    assert list(out) == [
        "gap_body_magnitude_coupling_20",
        "amount_gap_shock_response_corr_20",
        "range_body_absorption_corr_20",
    ]
    for value in out.values():
        assert value.iloc[:19].isna().all().all()
        assert value.iloc[19:].notna().any().any()


def test_batch13_hand_formulas_negative_directions_and_canonical_amount():
    p = _varied_panels()
    cfg = _batch13_cfg()
    out = build_atoms(p, cfg)
    open_, high, low, close, amount = (
        p[key] for key in ("open", "high", "low", "close", "amount")
    )
    previous_close = close.shift(1)
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0)
    body = close.div(open_.where(open_.ne(0))).sub(1.0)
    gap_complete = gap.notna() & body.notna()
    expected_gap_body = -_expected_batch13_corr(gap.abs(), body.abs(), gap_complete)
    pd.testing.assert_frame_equal(out["gap_body_magnitude_coupling_20"], expected_gap_body)

    valid_amount = amount.gt(0)
    innovation = np.log(amount.where(valid_amount)).diff()
    amount_complete = gap_complete & innovation.notna() & valid_amount
    expected_amount_gap = -_expected_batch13_corr(
        innovation, gap.abs(), amount_complete
    )
    pd.testing.assert_frame_equal(
        out["amount_gap_shock_response_corr_20"], expected_amount_gap
    )

    daily_range = (high - low).div(previous_close.where(previous_close.ne(0)))
    range_complete = gap_complete & daily_range.notna()
    expected_range_body = -_expected_batch13_corr(
        daily_range, body.abs(), range_complete
    )
    pd.testing.assert_frame_equal(
        out["range_body_absorption_corr_20"], expected_range_body
    )

    # Canonical amount is used; changing volume alone cannot change the atom.
    changed_volume = {key: value.copy() for key, value in p.items()}
    changed_volume["volume"] *= 37.0
    volume_out = build_atoms(changed_volume, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], volume_out[name])


def test_batch13_amount_range_zero_variance_nan_and_missing_propagation():
    p = _varied_panels()
    cfg = _batch13_cfg()

    zero_amount = {key: value.copy() for key, value in p.items()}
    zero_amount["amount"].iloc[30, 0] = 0.0
    zero_out = build_atoms(zero_amount, cfg)
    assert pd.isna(zero_out["amount_gap_shock_response_corr_20"].iloc[49, 0])
    assert pd.notna(zero_out["amount_gap_shock_response_corr_20"].iloc[51, 0])

    zero_prev_close = {key: value.copy() for key, value in p.items()}
    zero_prev_close["close"].iloc[30, 0] = 0.0
    zero_range_out = build_atoms(zero_prev_close, cfg)
    assert pd.isna(zero_range_out["range_body_absorption_corr_20"].iloc[49, 0])
    assert pd.notna(zero_range_out["range_body_absorption_corr_20"].iloc[51, 0])

    constant = {key: value.copy() for key, value in p.items()}
    constant["open"].iloc[:, 0] = 100.0
    constant["close"].iloc[:, 0] = 101.0
    constant["high"].iloc[:, 0] = 102.0
    constant["low"].iloc[:, 0] = 99.0
    constant["amount"].iloc[:, 0] = 1000.0
    constant_out = build_atoms(constant, cfg)
    for name in cfg["mechanisms"]:
        assert pd.isna(constant_out[f"{name}_20"].iloc[40, 0])

    broken = {key: value.copy() for key, value in p.items()}
    broken["close"].iloc[30, 0] = np.nan
    broken_out = build_atoms(broken, cfg)
    for name in cfg["mechanisms"]:
        assert pd.isna(broken_out[f"{name}_20"].iloc[49, 0])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())


def test_batch14_daily_whitelist_directions_window_and_budget():
    cfg = _batch14_daily_cfg()
    expected = [
        "gap_excess_kurtosis", "clv_autocorr", "gap_abs_change",
        "range_gap_abs_corr", "amount_abs_body_corr", "amount_clv_abs_corr",
        "clv_excess_kurtosis", "wick_abs_kurtosis", "wick_abs_change",
        "amount_innovation_excess_kurtosis", "amount_innovation_abs_change",
        "body_wick_abs_corr", "gap_signed_body_corr",
        "range_body_ratio_dispersion",
    ]
    assert cfg["discovery_surface"] == "2025_DIRECTION_DISCOVERY_ONLY"
    assert cfg["as_of"] == "2025-12-31"
    assert cfg["prior_registered"] == 158
    assert cfg["budget_cap"] == 172
    assert cfg["new_definitions"] == 14
    assert cfg["external_registered_definitions"] == 8
    assert list(cfg["mechanisms"]) == expected
    assert [cfg["mechanisms"][name]["direction"] for name in expected] == [1] * 14
    out = build_atoms(_varied_panels(), cfg)
    assert list(out) == [f"{name}_20" for name in expected]
    assert all(value.iloc[:19].isna().all().all() for value in out.values())
    assert all(value.iloc[30:].notna().any().any() for value in out.values())


def test_batch14_daily_hand_formulas_amount_source_and_positive_direction():
    p = _varied_panels()
    cfg = _batch14_daily_cfg()
    out = build_atoms(p, cfg)
    open_, high, low, close, amount = (
        p[key] for key in ("open", "high", "low", "close", "amount")
    )
    previous_close = close.shift(1)
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0)
    body = close.div(open_.where(open_.ne(0))).sub(1.0)
    daily_range = (high - low).div(previous_close.where(previous_close.ne(0)))
    clv = (2 * close - high - low).div((high - low).where((high - low).gt(0)))
    price_range = high - low
    body_low = pd.DataFrame(np.minimum(open_.to_numpy(), close.to_numpy()), index=open_.index, columns=open_.columns)
    body_high = pd.DataFrame(np.maximum(open_.to_numpy(), close.to_numpy()), index=open_.index, columns=open_.columns)
    wick = ((body_low - low) - (high - body_high)).div(price_range.where(price_range.gt(0)))
    valid_amount = amount.gt(0)
    innovation = np.log(amount.where(valid_amount)).diff()

    complete = gap.notna() & body.notna()
    pd.testing.assert_frame_equal(
        out["range_gap_abs_corr_20"],
        _expected_batch13_corr(daily_range, gap.abs(), complete & daily_range.notna()),
    )
    pd.testing.assert_frame_equal(
        out["clv_autocorr_20"],
        _expected_batch13_corr(clv, clv.shift(1), clv.notna() & clv.shift(1).notna()),
    )
    amount_complete = innovation.notna() & body.notna()
    pd.testing.assert_frame_equal(
        out["amount_abs_body_corr_20"],
        _expected_batch13_corr(innovation, body.abs(), amount_complete),
    )
    gap_change = gap.diff().abs()
    expected_gap_change = gap_change.rolling(20, min_periods=20).mean().where(
        gap_change.notna().rolling(20, min_periods=20).sum().eq(20)
    )
    pd.testing.assert_frame_equal(out["gap_abs_change_20"], expected_gap_change)
    wick_change = wick.abs().diff().abs()
    expected_wick_change = wick_change.rolling(20, min_periods=20).mean().where(
        wick_change.notna().rolling(20, min_periods=20).sum().eq(20)
    )
    pd.testing.assert_frame_equal(out["wick_abs_change_20"], expected_wick_change)
    ratio = body.abs().div(daily_range.abs().where(daily_range.abs().gt(0)))
    expected_ratio_dispersion = ratio.rolling(20, min_periods=20).std().where(
        ratio.notna().rolling(20, min_periods=20).sum().eq(20)
    )
    pd.testing.assert_frame_equal(
        out["range_body_ratio_dispersion_20"], expected_ratio_dispersion
    )
    # Formula uses canonical amount; changing volume alone is immaterial.
    changed_volume = {key: value.copy() for key, value in p.items()}
    changed_volume["volume"] *= 37.0
    volume_out = build_atoms(changed_volume, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], volume_out[name])


def test_batch14_daily_zero_variance_missing_and_prefix_future_propagation():
    p = _varied_panels()
    cfg = _batch14_daily_cfg()
    constant = {key: value.copy() for key, value in p.items()}
    constant["open"].iloc[:, 0] = 100.0
    constant["close"].iloc[:, 0] = 101.0
    constant["high"].iloc[:, 0] = 102.0
    constant["low"].iloc[:, 0] = 99.0
    constant["amount"].iloc[:, 0] = 1000.0
    constant_out = build_atoms(constant, cfg)
    for name in (
        "gap_excess_kurtosis", "clv_autocorr", "range_gap_abs_corr",
        "amount_abs_body_corr", "amount_clv_abs_corr", "clv_excess_kurtosis",
        "wick_abs_kurtosis", "amount_innovation_excess_kurtosis",
        "body_wick_abs_corr", "gap_signed_body_corr",
    ):
        assert pd.isna(constant_out[f"{name}_20"].iloc[40, 0])

    zero_amount = {key: value.copy() for key, value in p.items()}
    zero_amount["amount"].iloc[30, 0] = 0.0
    zero_out = build_atoms(zero_amount, cfg)
    for name in ("amount_abs_body_corr", "amount_clv_abs_corr",
                 "amount_innovation_excess_kurtosis", "amount_innovation_abs_change"):
        assert pd.isna(zero_out[f"{name}_20"].iloc[49, 0])
        assert pd.notna(zero_out[f"{name}_20"].iloc[60, 0])

    broken = {key: value.copy() for key, value in p.items()}
    broken["close"].iloc[30, 0] = np.nan
    broken_out = build_atoms(broken, cfg)
    for name in (
        "gap_excess_kurtosis", "clv_autocorr", "gap_abs_change",
        "range_gap_abs_corr", "amount_abs_body_corr", "amount_clv_abs_corr",
        "clv_excess_kurtosis", "wick_abs_kurtosis", "wick_abs_change",
        "body_wick_abs_corr", "gap_signed_body_corr",
        "range_body_ratio_dispersion",
    ):
        assert pd.isna(broken_out[f"{name}_20"].iloc[49, 0])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())


def test_batch14_stage2_daily_aliases_equal_raw_times_frozen_sign():
    p = _varied_panels()
    raw_cfg = _batch14_daily_cfg()
    aliases = {
        "d2025_gap_excess_kurtosis": ("gap_excess_kurtosis", -1),
        "d2025_clv_autocorr": ("clv_autocorr", 1),
        "d2025_gap_abs_change": ("gap_abs_change", 1),
        "d2025_range_gap_abs_corr": ("range_gap_abs_corr", -1),
        "d2025_amount_abs_body_corr": ("amount_abs_body_corr", 1),
        "d2025_amount_clv_abs_corr": ("amount_clv_abs_corr", 1),
        "d2025_clv_excess_kurtosis": ("clv_excess_kurtosis", 1),
        "d2025_wick_abs_kurtosis": ("wick_abs_kurtosis", -1),
        "d2025_wick_abs_change": ("wick_abs_change", -1),
        "d2025_amount_innovation_excess_kurtosis": (
            "amount_innovation_excess_kurtosis", -1
        ),
        "d2025_amount_innovation_abs_change": ("amount_innovation_abs_change", 1),
        "d2025_body_wick_abs_corr": ("body_wick_abs_corr", -1),
        "d2025_gap_signed_body_corr": ("gap_signed_body_corr", -1),
        "d2025_range_body_ratio_dispersion": ("range_body_ratio_dispersion", 1),
    }
    alias_cfg = {"windows": [20], "mechanisms": {
        name: {"direction": sign} for name, (_, sign) in aliases.items()
    }}
    raw_out = build_atoms(p, raw_cfg)
    alias_out = build_atoms(p, alias_cfg)
    for alias, (raw, sign) in aliases.items():
        pd.testing.assert_frame_equal(
            alias_out[f"{alias}_20"], raw_out[f"{raw}_20"] * sign
        )
    assert all(leakage_checks(p, alias_cfg, p["close"].index[60]).values())


def test_batch14_stage2_daily_config_contracts():
    expected = {
        "group_ic20_batch14_stage2_daily_a_20260923": (174, 181),
        "group_ic20_batch14_stage2_daily_b_20260923": (181, 188),
    }
    for name, (prior, cap) in expected.items():
        cfg = yaml.safe_load(open(f"{ROOT}configs/{name}.yaml"))
        assert cfg["discovery_surface"] == "2025_POST_IC_DIRECTION"
        assert cfg["non_independent_confirmation"] is True
        assert cfg["as_of"] == "2026-09-17"
        assert cfg["evaluation_start"] == "2025-01-01"
        assert cfg["prior_registered"] == prior
        assert cfg["budget_cap"] == cap
        assert cfg["new_definitions"] == 7
        assert cfg["external_registered_definitions"] == 8
        assert len(cfg["mechanisms"]) == 7
        assert all(name.startswith("d2025_") for name in cfg["mechanisms"])


def test_batch15_daily_whitelist_budget_direction_and_window():
    cfg = _batch15_daily_cfg()
    expected = [
        "gap_lag_body_corr", "gap_lag_abs_body_corr", "range_lag_abs_body_corr",
        "amount_lag_abs_body_corr", "gap_conditional_body_asymmetry",
        "amount_conditional_body_asymmetry", "clv_abs_tail_share",
        "body_sign_entropy", "gap_sign_entropy", "clv_sign_transition_rate",
        "amount_innovation_sign_entropy", "range_share_entropy",
    ]
    assert cfg["discovery_surface"] == "2025_DIRECTION_DISCOVERY_ONLY"
    assert cfg["as_of"] == "2025-12-31"
    assert cfg["prior_registered"] == 190
    assert cfg["budget_cap"] == 202
    assert cfg["new_definitions"] == 12
    assert cfg["external_registered_definitions"] == 8
    assert list(cfg["mechanisms"]) == expected
    assert [cfg["mechanisms"][name]["direction"] for name in expected] == [1] * 12
    out = build_atoms(_varied_panels(), cfg)
    assert list(out) == [f"{name}_20" for name in expected]
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(frame.iloc[30:].notna().any().any() for frame in out.values())


def test_batch15_daily_lagged_conditional_entropy_and_range_hand_formulas():
    p = _varied_panels()
    cfg = _batch15_daily_cfg()
    out = build_atoms(p, cfg)
    open_, high, low, close, amount = (
        p[key] for key in ("open", "high", "low", "close", "amount")
    )
    previous_close = close.shift(1)
    gap = open_.div(previous_close.where(previous_close.ne(0))).sub(1.0)
    body = close.div(open_).sub(1.0)
    daily_range = (high - low).div(previous_close.where(previous_close.ne(0)))
    clv = (2 * close - high - low).div((high - low).where((high - low).gt(0)))
    innovation = np.log(amount.where(amount.gt(0))).diff()
    pd.testing.assert_frame_equal(
        out["gap_lag_body_corr_20"],
        _expected_batch13_corr(gap.shift(1), body, gap.shift(1).notna() & body.notna()),
    )
    pd.testing.assert_frame_equal(
        out["range_lag_abs_body_corr_20"],
        _expected_batch13_corr(
            daily_range.shift(1), body.abs(),
            daily_range.shift(1).notna() & body.notna(),
        ),
    )
    pos = gap.gt(0) & body.notna()
    neg = gap.le(0) & body.notna()
    pc = pos.astype(float).rolling(20, min_periods=1).sum()
    nc = neg.astype(float).rolling(20, min_periods=1).sum()
    expected_cond = (
        body.abs().where(pos).rolling(20, min_periods=1).sum().div(pc.where(pc.gt(0)))
        - body.abs().where(neg).rolling(20, min_periods=1).sum().div(nc.where(nc.gt(0)))
    ).where(
        (body.notna() & gap.notna()).astype(float).rolling(20, min_periods=20).sum().eq(20)
        & pc.gt(0) & nc.gt(0)
    )
    pd.testing.assert_frame_equal(out["gap_conditional_body_asymmetry_20"], expected_cond)
    p_body = body.gt(0).astype(float).rolling(20, min_periods=20).mean().clip(1e-12, 1 - 1e-12)
    expected_entropy = -(p_body * np.log(p_body) + (1 - p_body) * np.log(1 - p_body))
    pd.testing.assert_frame_equal(out["body_sign_entropy_20"], expected_entropy)

    def entropy_window(values):
        total = values.sum()
        p_range = values / total
        return -(p_range * np.log(np.where(p_range > 0, p_range, 1.0))).sum() / np.log(20)
    expected_range_entropy = daily_range.abs().rolling(20, min_periods=20).apply(
        entropy_window, raw=True
    )
    pd.testing.assert_frame_equal(out["range_share_entropy_20"], expected_range_entropy)


def test_batch15_daily_condition_missing_zero_variance_and_prefix():
    p = _varied_panels()
    cfg = _batch15_daily_cfg()
    one_sided = {key: value.copy() for key, value in p.items()}
    one_sided["open"] = one_sided["close"].shift(1) * 1.01
    one_sided_out = build_atoms(one_sided, cfg)
    assert pd.isna(one_sided_out["gap_conditional_body_asymmetry_20"].iloc[40, 0])
    broken = {key: value.copy() for key, value in p.items()}
    broken["close"].iloc[30, 0] = np.nan
    broken_out = build_atoms(broken, cfg)
    for name in (
        "gap_lag_body_corr", "gap_lag_abs_body_corr", "range_lag_abs_body_corr",
        "amount_lag_abs_body_corr", "gap_conditional_body_asymmetry",
        "amount_conditional_body_asymmetry", "clv_abs_tail_share", "body_sign_entropy",
        "gap_sign_entropy", "clv_sign_transition_rate", "range_share_entropy",
    ):
        assert pd.isna(broken_out[f"{name}_20"].iloc[49, 0])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())


def test_batch15_clv_boundary_rounding_scale_and_prefix():
    idx = pd.date_range("2025-01-01", periods=80, freq="D")
    close = pd.DataFrame(100.0, index=idx, columns=["a"])
    open_ = close.copy()
    high_values = np.where(np.arange(80) % 2 == 0, 100.333333333333, 101.0)
    high = pd.DataFrame(high_values, index=idx, columns=["a"])
    low = pd.DataFrame(99.0, index=idx, columns=["a"])
    amount = pd.DataFrame(1000.0, index=idx, columns=["a"])
    p = {"open": open_, "high": high, "low": low, "close": close,
         "amount": amount, "volume": amount}
    cfg = {"windows": [20], "mechanisms": {
        "clv_abs_tail_share": {"direction": 1},
        "clv_sign_transition_rate": {"direction": 1},
    }}
    out = build_atoms(p, cfg)
    scaled = {key: value.copy() for key, value in p.items()}
    for key in ("open", "high", "low", "close"):
        scaled[key] *= 17.0
    scaled_out = build_atoms(scaled, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], scaled_out[name])
    # The rounded boundary value exactly 0.5 is excluded by the strict > rule.
    assert out["clv_abs_tail_share_20"].iloc[-1, 0] == pytest.approx(0.0)
    assert all(leakage_checks(p, cfg, idx[60]).values())


def test_batch15_daily_rejudge_config_contract():
    cfg = yaml.safe_load(open(
        f"{ROOT}configs/group_ic20_batch15_daily_rejudge_20260923.yaml"
    ))
    raw = _batch15_daily_cfg()
    assert cfg["rejudge_of"] == "group_ic20_batch15_daily_20260923"
    assert cfg["prior_registered"] == 202
    assert cfg["budget_cap"] == 202
    assert cfg["new_definitions"] == 0
    assert cfg["external_registered_definitions"] == 8
    assert cfg["mechanisms"] == raw["mechanisms"]


def test_batch15_stage2_daily_aliases_equal_raw_times_each_direction():
    p = _varied_panels()
    raw_cfg = _batch15_daily_cfg()
    aliases = {
        "d2025_gap_lag_body_corr": ("gap_lag_body_corr", 1),
        "d2025_gap_lag_abs_body_corr": ("gap_lag_abs_body_corr", -1),
        "d2025_range_lag_abs_body_corr": ("range_lag_abs_body_corr", -1),
        "d2025_amount_lag_abs_body_corr": ("amount_lag_abs_body_corr", -1),
        "d2025_gap_conditional_body_asymmetry": ("gap_conditional_body_asymmetry", 1),
        "d2025_amount_conditional_body_asymmetry": ("amount_conditional_body_asymmetry", 1),
        "d2025_clv_abs_tail_share": ("clv_abs_tail_share", -1),
        "d2025_body_sign_entropy": ("body_sign_entropy", -1),
        "d2025_gap_sign_entropy": ("gap_sign_entropy", -1),
        "d2025_clv_sign_transition_rate": ("clv_sign_transition_rate", -1),
        "d2025_amount_innovation_sign_entropy": ("amount_innovation_sign_entropy", 1),
        "d2025_range_share_entropy": ("range_share_entropy", -1),
    }
    alias_cfg = {"windows": [20], "mechanisms": {
        name: {"direction": sign} for name, (_, sign) in aliases.items()
    }}
    raw_out = build_atoms(p, raw_cfg)
    alias_out = build_atoms(p, alias_cfg)
    for alias, (raw, sign) in aliases.items():
        pd.testing.assert_frame_equal(alias_out[f"{alias}_20"], raw_out[f"{raw}_20"] * sign)
    assert all(leakage_checks(p, alias_cfg, p["close"].index[60]).values())


def test_batch15_stage2_daily_config_contracts():
    expected = {
        "group_ic20_batch15_stage2_daily_a_20260923.yaml": (206, 212),
        "group_ic20_batch15_stage2_daily_b_20260923.yaml": (212, 218),
    }
    for filename, (prior, cap) in expected.items():
        cfg = yaml.safe_load(open(f"{ROOT}configs/{filename}"))
        assert cfg["purpose"] == "seen_history_discovery_only"
        assert cfg["discovery_surface"] == "2025_POST_IC_DIRECTION"
        assert cfg["as_of"] == "2026-09-17"
        assert cfg["evaluation_start"] == "2025-01-01"
        assert cfg["prior_registered"] == prior
        assert cfg["budget_cap"] == cap
        assert cfg["new_definitions"] == 6
        assert cfg["external_registered_definitions"] == 8
        assert len(cfg["mechanisms"]) == 6
        assert all(name.startswith("d2025_") for name in cfg["mechanisms"])


def test_batch16_daily_states_hand_formulas_scale_and_prefix():
    p = _varied_panels()
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch16_daily_20260923.yaml"))
    out = build_atoms(p, cfg)
    assert list(out) == [f"{name}_20" for name in cfg["mechanisms"]]
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(frame.iloc[30:].notna().any().any() for frame in out.values())
    open_, high, low, close = (p[key] for key in ("open", "high", "low", "close"))
    previous_close = close.shift(1)
    gap = open_.div(previous_close).sub(1.0)
    body = close.div(open_).sub(1.0)
    close_return = close.div(previous_close).sub(1.0)
    complete = close_return.notna() & body.notna()
    expected_switch = (np.sign(close_return) != np.sign(body)).astype(float).rolling(
        20, min_periods=20
    ).mean().where(complete.astype(float).rolling(20, min_periods=20).sum().eq(20))
    pd.testing.assert_frame_equal(out["overnight_intraday_switch_rate_20"], expected_switch)
    expected_repair = (-np.sign(gap) * body).rolling(20, min_periods=20).mean().where(
        (gap.notna() & body.notna()).astype(float).rolling(20, min_periods=20).sum().eq(20)
    )
    pd.testing.assert_frame_equal(out["gap_repair_signed_magnitude_20"], expected_repair)
    scaled = {key: value.copy() for key, value in p.items()}
    for key in ("open", "high", "low", "close"):
        scaled[key] *= 13.0
    scaled_out = build_atoms(scaled, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], scaled_out[name])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())


def test_batch16_daily_config_contract():
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch16_daily_20260923.yaml"))
    expected = [
        "overnight_intraday_switch_rate", "gap_repair_signed_magnitude",
        "gap_repair_completion_rate", "body_wick_rejection_rate",
    ]
    assert list(cfg["mechanisms"]) == expected
    assert cfg["purpose"] == "seen_history_discovery_only"
    assert cfg["discovery_surface"] == "2025_DIRECTION_DISCOVERY_ONLY"
    assert cfg["as_of"] == "2025-12-31"
    assert cfg["prior_registered"] == 222
    assert cfg["budget_cap"] == 226
    assert cfg["new_definitions"] == 4
    assert cfg["external_registered_definitions"] == 8
    assert [cfg["mechanisms"][name]["direction"] for name in expected] == [1] * 4


def test_batch16_stage2_daily_aliases_equal_raw_and_config_contract():
    p = _varied_panels()
    raw_names = [
        "overnight_intraday_switch_rate", "gap_repair_signed_magnitude",
        "gap_repair_completion_rate", "body_wick_rejection_rate",
    ]
    aliases = {f"d2025_{name}": (name, 1) for name in raw_names}
    raw_cfg = {"windows": [20], "mechanisms": {
        name: {"direction": 1} for name in raw_names
    }}
    alias_cfg = {"windows": [20], "mechanisms": {
        name: {"direction": sign} for name, (_, sign) in aliases.items()
    }}
    raw_out = build_atoms(p, raw_cfg)
    alias_out = build_atoms(p, alias_cfg)
    for alias, (raw, sign) in aliases.items():
        pd.testing.assert_frame_equal(
            alias_out[f"{alias}_20"], raw_out[f"{raw}_20"] * sign
        )
    assert all(leakage_checks(p, alias_cfg, p["close"].index[60]).values())
    for filename, prior, cap, count in [
        ("group_ic20_batch16_stage2_daily_20260923.yaml", 238, 242, 4),
    ]:
        cfg = yaml.safe_load(open(f"{ROOT}configs/{filename}"))
        assert cfg["purpose"] == "seen_history_discovery_only"
        assert cfg["discovery_surface"] == "2025_POST_IC_DIRECTION"
        assert cfg["as_of"] == "2026-09-17"
        assert cfg["evaluation_start"] == "2025-01-01"
        assert cfg["prior_registered"] == prior
        assert cfg["budget_cap"] == cap
        assert cfg["new_definitions"] == count
        assert cfg["external_registered_definitions"] == 8
        assert [cfg["mechanisms"][name]["direction"] for name in cfg["mechanisms"]] == [1] * count


def test_batch17_daily_amount_shock_hand_formula_scale_and_prefix():
    p = _varied_panels()
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch17_daily_20260923.yaml"))
    out = build_atoms(p, cfg)
    assert list(out) == [f"{name}_20" for name in cfg["mechanisms"]]
    open_, high, low, close, amount = (p[key] for key in ("open", "high", "low", "close", "amount"))
    previous_close = close.shift(1)
    body = close.div(open_).sub(1.0).round(12)
    daily_range = (high - low).div(previous_close).round(12)
    innovation = np.log(amount).diff().round(12)
    shock = innovation.abs()
    denominator = body.abs() + daily_range
    state = shock * body.abs().div(denominator.where(denominator > 0))
    complete = innovation.notna() & body.notna() & daily_range.notna() & amount.gt(0)
    expected = state.rolling(20, min_periods=20).mean().where(
        complete.astype(float).rolling(20, min_periods=20).sum().eq(20)
    )
    pd.testing.assert_frame_equal(out["amount_shock_body_efficiency_20"], expected)
    scaled = {key: value.copy() for key, value in p.items()}
    for key in ("open", "high", "low", "close", "amount"):
        scaled[key] *= 17.0
    scaled_out = build_atoms(scaled, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], scaled_out[name])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())


def test_batch17_daily_config_contract():
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch17_daily_20260923.yaml"))
    assert cfg["purpose"] == "seen_history_discovery_only"
    assert cfg["discovery_surface"] == "2025_DIRECTION_DISCOVERY_ONLY"
    assert cfg["as_of"] == "2025-12-31"
    assert cfg["prior_registered"] == 254
    assert cfg["budget_cap"] == 260
    assert cfg["new_definitions"] == 6
    assert cfg["external_registered_definitions"] == 8
    assert len(cfg["mechanisms"]) == 6
    assert all(item["direction"] == 1 for item in cfg["mechanisms"].values())


def test_batch17_stage2_daily_aliases_equal_raw_times_direction():
    p = _varied_panels()
    aliases = {
        "d2025_amount_shock_body_efficiency": ("amount_shock_body_efficiency", 1),
        "d2025_amount_shock_wick_rejection": ("amount_shock_wick_rejection", 1),
        "d2025_amount_shock_direction_alignment": ("amount_shock_direction_alignment", 1),
        "d2025_amount_shock_close_location_alignment": ("amount_shock_close_location_alignment", 1),
        "d2025_amount_shock_gap_repair": ("amount_shock_gap_repair", -1),
        "d2025_amount_shock_close_extremity": ("amount_shock_close_extremity", 1),
    }
    raw = build_atoms(p, {"windows": [20], "mechanisms": {
        n: {"direction": 1} for n, _ in aliases.values()
    }})
    alias = build_atoms(p, {"windows": [20], "mechanisms": {
        n: {"direction": s} for n, (_, s) in aliases.items()
    }})
    for a, (r, s) in aliases.items():
        pd.testing.assert_frame_equal(alias[f"{a}_20"], raw[f"{r}_20"] * s)
    assert all(leakage_checks(p, {"windows": [20], "mechanisms": {
        n: {"direction": s} for n, (_, s) in aliases.items()
    }}, p["close"].index[60]).values())


def test_batch18_residual_states_hand_formula_scale_and_prefix():
    p = _varied_panels()
    names = [
        "market_residual_mean", "market_residual_upside_mean",
        "market_residual_downside_mean", "market_residual_sign_imbalance",
        "market_residual_path_efficiency", "market_residual_sign_persistence",
        "market_residual_turning_rate", "market_residual_tail_share",
        "market_residual_market_beta", "market_residual_range_absorption",
    ]
    cfg = {"windows": [20], "mechanisms": {n: {"direction": 1} for n in names}}
    out = build_atoms(p, cfg)
    assert list(out) == [f"{name}_20" for name in names]
    returns = p["close"].pct_change(fill_method=None)
    market = returns.mean(axis=1)
    residual = returns.sub(market, axis=0)
    expected = residual.rolling(20, min_periods=20).sum().div(
        residual.abs().rolling(20, min_periods=20).sum()
    )
    pd.testing.assert_frame_equal(out["market_residual_path_efficiency_20"], expected)
    scaled = {key: value.copy() for key, value in p.items()}
    for key in ("open", "high", "low", "close"):
        scaled[key] *= 19.0
    scaled_out = build_atoms(scaled, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], scaled_out[name])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())


def test_batch18_daily_config_contract():
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch18_daily_20260923.yaml"))
    assert cfg["purpose"] == "seen_history_discovery_only"
    assert cfg["discovery_surface"] == "2025_DIRECTION_DISCOVERY_ONLY"
    assert cfg["as_of"] == "2025-12-31"
    assert cfg["prior_registered"] == 286
    assert cfg["budget_cap"] == 296
    assert cfg["new_definitions"] == 10
    assert cfg["external_registered_definitions"] == 8
    assert len(cfg["mechanisms"]) == 10


def test_batch18_stage2_aliases_equal_raw_times_direction_and_screens():
    p = _varied_panels()
    aliases = {
        "d2025_market_residual_mean": ("market_residual_mean", 1),
        "d2025_market_residual_upside_mean": ("market_residual_upside_mean", 1),
        "d2025_market_residual_downside_mean": ("market_residual_downside_mean", 1),
        "d2025_market_residual_sign_imbalance": ("market_residual_sign_imbalance", 1),
        "d2025_market_residual_path_efficiency": ("market_residual_path_efficiency", 1),
        "d2025_market_residual_sign_persistence": ("market_residual_sign_persistence", -1),
        "d2025_market_residual_turning_rate": ("market_residual_turning_rate", 1),
        "d2025_market_residual_tail_share": ("market_residual_tail_share", 1),
        "d2025_market_residual_market_beta": ("market_residual_market_beta", 1),
        "d2025_market_residual_range_absorption": ("market_residual_range_absorption", -1),
    }
    raw_cfg = {"windows": [20], "mechanisms": {n: {"direction": 1} for n, _ in aliases.values()}}
    alias_cfg = {"windows": [20], "mechanisms": {n: {"direction": s} for n, (_, s) in aliases.items()}}
    raw = build_atoms(p, raw_cfg); alias = build_atoms(p, alias_cfg)
    for a, (r, s) in aliases.items():
        pd.testing.assert_frame_equal(alias[f"{a}_20"], raw[f"{r}_20"] * s)
    assert all(leakage_checks(p, alias_cfg, p["close"].index[60]).values())
    for fn, prior, cap in [("group_ic20_batch18_stage2_daily_a_20260923.yaml", 296, 301), ("group_ic20_batch18_stage2_daily_b_20260923.yaml", 301, 306)]:
        cfg = yaml.safe_load(open(f"{ROOT}configs/{fn}"))
        assert cfg["purpose"] == "seen_history_discovery_only"
        assert cfg["discovery_surface"] == "2025_POST_IC_DIRECTION"
        assert cfg["as_of"] == "2026-09-17"
        assert (cfg["prior_registered"], cfg["budget_cap"], cfg["new_definitions"]) == (prior, cap, 5)
        assert cfg["external_registered_definitions"] == 8
        assert set(cfg["screens"]) == {"min_days", "min_year_days", "min_positive_years", "min_ic", "min_ic_hac_t", "min_ic_block_t", "min_excess8_hac_t", "alpha", "max_abs_rank_corr"}


def test_batch19_tail_states_hand_formula_scale_and_prefix():
    p = _varied_panels()
    names = [
        "body_positive_run_mean", "body_negative_run_mean", "gap_positive_run_mean",
        "gap_negative_run_mean", "clv_extreme_recovery_rate", "range_shock_compression_rate",
        "amount_price_tail_mismatch_rate", "gap_body_tail_direction_asymmetry",
        "range_shock_body_absorption", "amount_tail_clv_alignment",
    ]
    cfg = {"windows": [20], "mechanisms": {n: {"direction": 1} for n in names}}
    out = build_atoms(p, cfg)
    assert list(out) == [f"{name}_20" for name in names]
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(frame.iloc[40:].notna().any().any() for frame in out.values())
    scaled = {key: value.copy() for key, value in p.items()}
    for key in ("open", "high", "low", "close", "amount"):
        scaled[key] *= 23.0
    scaled_out = build_atoms(scaled, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], scaled_out[name])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())


def test_batch19_daily_config_contract():
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch19_daily_20260923.yaml"))
    assert cfg["purpose"] == "seen_history_discovery_only"
    assert cfg["discovery_surface"] == "2025_DIRECTION_DISCOVERY_ONLY"
    assert cfg["as_of"] == "2025-12-31"
    assert cfg["prior_registered"] == 306
    assert cfg["budget_cap"] == 316
    assert cfg["new_definitions"] == 10
    assert cfg["external_registered_definitions"] == 8
    assert len(cfg["mechanisms"]) == 10
    assert set(cfg["screens"]) == {"min_days", "min_year_days", "min_positive_years", "min_ic", "min_ic_hac_t", "min_ic_block_t", "min_excess8_hac_t", "alpha", "max_abs_rank_corr"}


def test_batch19_stage2_aliases_equal_raw_times_direction_and_screens():
    p = _varied_panels()
    aliases = {
        "d2025_body_positive_run_mean": ("body_positive_run_mean", 1),
        "d2025_body_negative_run_mean": ("body_negative_run_mean", -1),
        "d2025_gap_positive_run_mean": ("gap_positive_run_mean", 1),
        "d2025_gap_negative_run_mean": ("gap_negative_run_mean", 1),
        "d2025_clv_extreme_recovery_rate": ("clv_extreme_recovery_rate", 1),
        "d2025_range_shock_compression_rate": ("range_shock_compression_rate", 1),
        "d2025_amount_price_tail_mismatch_rate": ("amount_price_tail_mismatch_rate", -1),
        "d2025_gap_body_tail_direction_asymmetry": ("gap_body_tail_direction_asymmetry", 1),
        "d2025_range_shock_body_absorption": ("range_shock_body_absorption", 1),
        "d2025_amount_tail_clv_alignment": ("amount_tail_clv_alignment", -1),
    }
    raw_cfg = {"windows": [20], "mechanisms": {n: {"direction": 1} for n, _ in aliases.values()}}
    alias_cfg = {"windows": [20], "mechanisms": {n: {"direction": s} for n, (_, s) in aliases.items()}}
    raw = build_atoms(p, raw_cfg); alias = build_atoms(p, alias_cfg)
    for a, (r, s) in aliases.items():
        pd.testing.assert_frame_equal(alias[f"{a}_20"], raw[f"{r}_20"] * s)
    assert all(leakage_checks(p, alias_cfg, p["close"].index[60]).values())
    for fn, prior, cap in [("group_ic20_batch19_stage2_daily_a_20260923.yaml", 316, 321), ("group_ic20_batch19_stage2_daily_b_20260923.yaml", 321, 326)]:
        cfg = yaml.safe_load(open(f"{ROOT}configs/{fn}"))
        assert cfg["purpose"] == "seen_history_discovery_only"
        assert cfg["discovery_surface"] == "2025_POST_IC_DIRECTION"
        assert cfg["as_of"] == "2026-09-17"
        assert (cfg["prior_registered"], cfg["budget_cap"], cfg["new_definitions"]) == (prior, cap, 5)
        assert cfg["external_registered_definitions"] == 8
        assert set(cfg["screens"]) == {"min_days", "min_year_days", "min_positive_years", "min_ic", "min_ic_hac_t", "min_ic_block_t", "min_excess8_hac_t", "alpha", "max_abs_rank_corr"}


def test_batch20_event_state_machine_scale_and_prefix():
    p = _varied_panels()
    names = list(yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch20_daily_20260923.yaml"))["mechanisms"])
    cfg = {"windows": [20], "mechanisms": {n: {"direction": 1} for n in names}}
    out = build_atoms(p, cfg)
    assert list(out) == [f"{name}_20" for name in names]
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(frame.iloc[40:].notna().any().any() for frame in out.values())
    scaled = {key: value.copy() for key, value in p.items()}
    for key in ("open", "high", "low", "close", "amount"):
        scaled[key] *= 29.0
    scaled_out = build_atoms(scaled, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], scaled_out[name])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())


def test_batch20_config_contract():
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch20_daily_20260923.yaml"))
    assert cfg["purpose"] == "seen_history_discovery_only"
    assert cfg["discovery_surface"] == "2025_DIRECTION_DISCOVERY_ONLY"
    assert cfg["as_of"] == "2025-12-31"
    assert (cfg["prior_registered"], cfg["budget_cap"], cfg["new_definitions"]) == (326, 338, 12)
    assert cfg["external_registered_definitions"] == 8
    assert len(cfg["mechanisms"]) == 12
    assert set(cfg["screens"]) == {"min_days", "min_year_days", "min_positive_years", "min_ic", "min_ic_hac_t", "min_ic_block_t", "min_excess8_hac_t", "alpha", "max_abs_rank_corr"}


def test_batch20_stage2_aliases_equal_raw_times_direction_and_duplicate_is_explicit():
    p = _varied_panels()
    aliases = {
        "d2025_gap_shock_range_recovery": ("gap_shock_range_recovery", 1),
        "d2025_gap_shock_clv_recovery": ("gap_shock_clv_recovery", 1),
        "d2025_amount_shock_range_contraction": ("amount_shock_range_contraction", 1),
        "d2025_wick_rejection_body_continuation": ("wick_rejection_body_continuation", 1),
        "d2025_range_shock_gap_absorption": ("range_shock_gap_absorption", 1),
        "d2025_range_shock_clv_absorption": ("range_shock_clv_absorption", 1),
        "d2025_extreme_body_amount_normalization": ("extreme_body_amount_normalization", 1),
        "d2025_amount_shock_clv_recovery": ("amount_shock_clv_recovery", 1),
        "d2025_gap_shock_body_reversal": ("gap_shock_body_reversal", -1),
        "d2025_range_shock_body_recovery": ("range_shock_body_recovery", 1),
        "d2025_wick_rejection_range_compression": ("wick_rejection_range_compression", 1),
        "d2025_body_shock_amount_normalization": ("body_shock_amount_normalization", 1),
    }
    raw_cfg = {"windows": [20], "mechanisms": {raw: {"direction": 1} for raw, _ in aliases.values()}}
    alias_cfg = {"windows": [20], "mechanisms": {alias: {"direction": sign} for alias, (_, sign) in aliases.items()}}
    raw = build_atoms(p, raw_cfg)
    alias = build_atoms(p, alias_cfg)
    for alias_name, (raw_name, sign) in aliases.items():
        pd.testing.assert_frame_equal(alias[f"{alias_name}_20"], raw[f"{raw_name}_20"] * sign)
    pd.testing.assert_frame_equal(
        raw["extreme_body_amount_normalization_20"],
        raw["body_shock_amount_normalization_20"],
    )
    assert all(leakage_checks(p, alias_cfg, p["close"].index[60]).values())


def test_batch20_stage2_daily_config_contracts():
    expected = [
        ("group_ic20_batch20_stage2_daily_a_20260923.yaml", 338, 344),
        ("group_ic20_batch20_stage2_daily_b_20260923.yaml", 344, 350),
    ]
    for filename, prior, cap in expected:
        cfg = yaml.safe_load(open(f"{ROOT}configs/{filename}"))
        assert cfg["purpose"] == "seen_history_discovery_only"
        assert cfg["discovery_surface"] == "2025_POST_IC_DIRECTION"
        assert cfg["as_of"] == "2026-09-17"
        assert cfg["evaluation_start"] == "2025-01-01"
        assert (cfg["prior_registered"], cfg["budget_cap"], cfg["new_definitions"]) == (prior, cap, 6)
        assert cfg["external_registered_definitions"] == 8
        assert len(cfg["mechanisms"]) == 6
        assert set(cfg["screens"]) == {"min_days", "min_year_days", "min_positive_years", "min_ic", "min_ic_hac_t", "min_ic_block_t", "min_excess8_hac_t", "alpha", "max_abs_rank_corr"}


def test_batch21_range_shock_responses_scale_complete_and_prefix():
    p = _varied_panels()
    names = list(yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch21_daily_20260923.yaml"))["mechanisms"])
    cfg = {"windows": [20], "mechanisms": {name: {"direction": 1} for name in names}}
    out = build_atoms(p, cfg)
    assert list(out) == [f"{name}_20" for name in names]
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(frame.iloc[40:].notna().any().any() for frame in out.values())
    scaled = {key: value.copy() for key, value in p.items()}
    for key in ("open", "high", "low", "close", "amount"):
        scaled[key] *= 31.0
    scaled_out = build_atoms(scaled, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], scaled_out[name])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())
    missing_amount = {key: value for key, value in p.items() if key != "amount"}
    with pytest.raises(KeyError, match="amount"):
        build_atoms(missing_amount, cfg)


def test_batch21_daily_config_contract():
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch21_daily_20260923.yaml"))
    assert cfg["purpose"] == "seen_history_discovery_only"
    assert cfg["discovery_surface"] == "2025_DIRECTION_DISCOVERY_ONLY"
    assert cfg["as_of"] == "2025-12-31"
    assert cfg["evaluation_start"] == "2025-01-01"
    assert (cfg["prior_registered"], cfg["budget_cap"], cfg["new_definitions"]) == (350, 358, 8)
    assert cfg["external_registered_definitions"] == 8
    assert len(cfg["mechanisms"]) == 8
    assert set(cfg["screens"]) == {"min_days", "min_year_days", "min_positive_years", "min_ic", "min_ic_hac_t", "min_ic_block_t", "min_excess8_hac_t", "alpha", "max_abs_rank_corr"}


def test_batch21_stage2_aliases_equal_raw_times_direction_and_prefix():
    p = _varied_panels()
    aliases = {
        "d2025_range_shock_amount_normalization": ("range_shock_amount_normalization", -1),
        "d2025_range_shock_amount_tail_persistence": ("range_shock_amount_tail_persistence", 1),
        "d2025_range_shock_amount_sign_persistence": ("range_shock_amount_sign_persistence", -1),
        "d2025_range_shock_amount_to_range_ratio": ("range_shock_amount_to_range_ratio", 1),
        "d2025_range_shock_wick_rejection": ("range_shock_wick_rejection", 1),
        "d2025_range_shock_direction_efficiency": ("range_shock_direction_efficiency", 1),
        "d2025_range_shock_range_persistence": ("range_shock_range_persistence", 1),
        "d2025_range_shock_wick_absorption": ("range_shock_wick_absorption", -1),
    }
    raw_cfg = {"windows": [20], "mechanisms": {raw: {"direction": 1} for raw, _ in aliases.values()}}
    alias_cfg = {"windows": [20], "mechanisms": {alias: {"direction": sign} for alias, (_, sign) in aliases.items()}}
    raw = build_atoms(p, raw_cfg)
    alias = build_atoms(p, alias_cfg)
    for alias_name, (raw_name, sign) in aliases.items():
        pd.testing.assert_frame_equal(alias[f"{alias_name}_20"], raw[f"{raw_name}_20"] * sign)
    assert all(leakage_checks(p, alias_cfg, p["close"].index[60]).values())


def test_batch21_stage2_daily_config_contract():
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch21_stage2_daily_20260923.yaml"))
    assert cfg["purpose"] == "seen_history_discovery_only"
    assert cfg["discovery_surface"] == "2025_POST_IC_DIRECTION"
    assert cfg["as_of"] == "2026-09-17"
    assert cfg["evaluation_start"] == "2025-01-01"
    assert (cfg["prior_registered"], cfg["budget_cap"], cfg["new_definitions"]) == (358, 366, 8)
    assert cfg["external_registered_definitions"] == 8
    assert len(cfg["mechanisms"]) == 8
    assert set(cfg["screens"]) == {"min_days", "min_year_days", "min_positive_years", "min_ic", "min_ic_hac_t", "min_ic_block_t", "min_excess8_hac_t", "alpha", "max_abs_rank_corr"}


def test_batch22_prior_event_responses_scale_complete_and_prefix():
    p = _varied_panels()
    names = list(yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch22_daily_20260923.yaml"))["mechanisms"])
    cfg = {"windows": [20], "mechanisms": {name: {"direction": 1} for name in names}}
    out = build_atoms(p, cfg)
    assert list(out) == [f"{name}_20" for name in names]
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(frame.iloc[40:].notna().any().any() for frame in out.values())
    scaled = {key: value.copy() for key, value in p.items()}
    for key in ("open", "high", "low", "close", "amount"):
        scaled[key] *= 37.0
    scaled_out = build_atoms(scaled, cfg)
    for name in out:
        pd.testing.assert_frame_equal(out[name], scaled_out[name])
    assert all(leakage_checks(p, cfg, p["close"].index[60]).values())
    missing_amount = {key: value for key, value in p.items() if key != "amount"}
    with pytest.raises(KeyError, match="amount"):
        build_atoms(missing_amount, cfg)


def test_batch22_daily_config_contract():
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch22_daily_20260923.yaml"))
    assert cfg["purpose"] == "seen_history_discovery_only"
    assert cfg["discovery_surface"] == "2025_DIRECTION_DISCOVERY_ONLY"
    assert cfg["as_of"] == "2025-12-31"
    assert cfg["evaluation_start"] == "2025-01-01"
    assert (cfg["prior_registered"], cfg["budget_cap"], cfg["new_definitions"]) == (366, 372, 6)
    assert cfg["external_registered_definitions"] == 8
    assert len(cfg["mechanisms"]) == 6
    assert set(cfg["screens"]) == {"min_days", "min_year_days", "min_positive_years", "min_ic", "min_ic_hac_t", "min_ic_block_t", "min_excess8_hac_t", "alpha", "max_abs_rank_corr"}


def test_batch22_stage2_aliases_equal_raw_times_direction_and_prefix():
    p = _varied_panels()
    aliases = {
        "d2025_gap_shock_wick_rejection": ("gap_shock_wick_rejection", 1),
        "d2025_amount_shock_wick_absorption": ("amount_shock_wick_absorption", 1),
        "d2025_clv_extreme_direction_efficiency": ("clv_extreme_direction_efficiency", 1),
        "d2025_body_shock_wick_repair": ("body_shock_wick_repair", 1),
        "d2025_gap_shock_direction_efficiency": ("gap_shock_direction_efficiency", -1),
        "d2025_clv_extreme_wick_rejection": ("clv_extreme_wick_rejection", 1),
    }
    raw_cfg = {"windows": [20], "mechanisms": {raw: {"direction": 1} for raw, _ in aliases.values()}}
    alias_cfg = {"windows": [20], "mechanisms": {alias: {"direction": sign} for alias, (_, sign) in aliases.items()}}
    raw = build_atoms(p, raw_cfg)
    alias = build_atoms(p, alias_cfg)
    for alias_name, (raw_name, sign) in aliases.items():
        pd.testing.assert_frame_equal(alias[f"{alias_name}_20"], raw[f"{raw_name}_20"] * sign)
    assert all(leakage_checks(p, alias_cfg, p["close"].index[60]).values())


def test_batch22_stage2_daily_config_contract():
    cfg = yaml.safe_load(open(f"{ROOT}configs/group_ic20_batch22_stage2_daily_20260923.yaml"))
    assert cfg["purpose"] == "seen_history_discovery_only"
    assert cfg["discovery_surface"] == "2025_POST_IC_DIRECTION"
    assert cfg["as_of"] == "2026-09-17"
    assert cfg["evaluation_start"] == "2025-01-01"
    assert (cfg["prior_registered"], cfg["budget_cap"], cfg["new_definitions"]) == (372, 378, 6)
    assert cfg["external_registered_definitions"] == 8
    assert len(cfg["mechanisms"]) == 6
    assert set(cfg["screens"]) == {"min_days", "min_year_days", "min_positive_years", "min_ic", "min_ic_hac_t", "min_ic_block_t", "min_excess8_hac_t", "alpha", "max_abs_rank_corr"}


def test_batch20_composite_exposes_both_standalone_legs():
    panels = _varied_panels()
    cfg = {
        "windows": [20],
        "mechanisms": {
            "d2025_range_shock_clv_absorption": {
                "direction": 1,
                "raw_formula": "range_shock_clv_absorption_20",
            }
        },
    }
    composite = build_atoms(panels, cfg)["d2025_range_shock_clv_absorption_20"]
    legs = build_paired_legs(
        panels, cfg, "d2025_range_shock_clv_absorption_20"
    )
    assert legs is not None and set(legs) == {"event", "response"}
    joint = (legs["event"].notna() & legs["response"].notna() & composite.notna())
    assert joint.iloc[40:].any().any()
    assert not composite.equals(legs["event"])
    assert not composite.equals(legs["response"])
