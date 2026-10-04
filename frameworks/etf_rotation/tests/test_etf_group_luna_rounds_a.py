import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_group_luna_rounds_a import DIRECTIONS, build_atoms


def _panels(n=110):
    rng = np.random.default_rng(20260923)
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    ret = 0.001 + 0.012 * np.sin(np.arange(n)[:, None] * 1.73) + rng.normal(0, 0.009, (n, 3))
    close = pd.DataFrame(100 * np.cumprod(1 + ret, axis=0), index=idx, columns=list("abc"))
    previous = close.shift(1).fillna(close.iloc[0])
    opening = previous * (1 + 0.004 * np.cos(np.arange(n)[:, None] * 0.61))
    opening = pd.DataFrame(opening, index=idx, columns=close.columns)
    high = pd.DataFrame(np.maximum(opening, close) * (1.002 + 0.001 * np.sin(np.arange(n)[:, None])), index=idx, columns=close.columns)
    low = pd.DataFrame(np.minimum(opening, close) * (0.998 - 0.001 * np.cos(np.arange(n)[:, None])), index=idx, columns=close.columns)
    return {"open": opening, "high": high, "low": low, "close": close}


def _cfg(names=None):
    names = list(DIRECTIONS) if names is None else names
    return {"mechanisms": {name: {"direction": DIRECTIONS[name]} for name in names}}


def test_whitelist_direction_suffix_and_nonempty_scores():
    out = build_atoms(_panels(), _cfg())
    assert list(out) == [f"{name}_20" for name in DIRECTIONS]
    assert all(frame.index.equals(_panels()["close"].index) for frame in out.values())
    assert all(frame.iloc[-1].notna().any() for frame in out.values())


def test_numpy_reference_drawdown_and_tail_formulas():
    p = _panels()
    out = build_atoms(p, _cfg([
        "l36_max_close_drawdown_depth", "l36_drawdown_recovery_fraction",
        "l36_drawdown_depth_concentration", "l37_upper_tail_mean_excess",
        "l37_lower_tail_mean_excess", "l37_tail_magnitude_asymmetry",
    ]))
    x = p["close"].iloc[-20:, 0].to_numpy()
    depths = []
    peaks = []
    peak = x[0]
    peak_i = 0
    for i, value in enumerate(x):
        if value > peak:
            peak, peak_i = value, i
        depths.append((peak - value) / peak)
        peaks.append((peak_i, i))
    max_i = int(np.argmax(depths))
    expected_dd = depths[max_i]
    selected_peak, selected_trough = peaks[max_i]
    expected_recovery = (x[-1] - x[selected_trough]) / (x[selected_peak] - x[selected_trough]) if expected_dd else 0.0
    np.testing.assert_allclose(out["l36_max_close_drawdown_depth_20"].iloc[-1, 0], -expected_dd)
    np.testing.assert_allclose(out["l36_drawdown_recovery_fraction_20"].iloc[-1, 0], expected_recovery)
    np.testing.assert_allclose(out["l36_drawdown_depth_concentration_20"].iloc[-1, 0], max(depths) / sum(depths))

    # A 20-return feature becomes available one row after its first close.
    r = p["close"].iloc[-21:, 0].pct_change(fill_method=None).dropna().to_numpy()
    q90, q10 = np.quantile(r, [0.9, 0.1], method="linear")
    upper, lower = r[r >= q90], r[r <= q10]
    np.testing.assert_allclose(out["l37_upper_tail_mean_excess_20"].iloc[-1, 0], upper.mean() - q90)
    np.testing.assert_allclose(out["l37_lower_tail_mean_excess_20"].iloc[-1, 0], -(q10 - lower.mean()))
    np.testing.assert_allclose(out["l37_tail_magnitude_asymmetry_20"].iloc[-1, 0], (upper.mean() + lower.mean()) / np.abs(r).mean())


def test_prefix_future_perturbation_and_price_scale_invariance():
    p = _panels()
    cut = p["close"].index[72]
    base = build_atoms(p, _cfg())
    prefix = {k: v.loc[:cut].copy() for k, v in p.items()}
    prefix_out = build_atoms(prefix, _cfg())
    perturbed = {k: v.copy() for k, v in p.items()}
    for frame in perturbed.values():
        frame.loc[frame.index > cut] *= 5.7
    future_out = build_atoms(perturbed, _cfg())
    scaled = {k: v * 37.0 for k, v in p.items()}
    scaled_out = build_atoms(scaled, _cfg())
    for name in base:
        pd.testing.assert_frame_equal(base[name].loc[:cut], prefix_out[name], check_exact=False, rtol=1e-10, atol=1e-12)
        pd.testing.assert_frame_equal(base[name].loc[:cut], future_out[name].loc[:cut], check_exact=False, rtol=1e-10, atol=1e-12)
        pd.testing.assert_frame_equal(base[name], scaled_out[name], check_exact=False, rtol=1e-9, atol=1e-11)


def test_missing_and_invalid_ohlc_never_become_zero_states():
    p = _panels()
    p["high"].iloc[50, 0] = np.nan
    p["low"].iloc[30, 1] = np.nan
    p["high"].iloc[70, 2] = p["close"].iloc[70, 2] * 0.5  # invalid high below close
    out = build_atoms(p, _cfg([
        "l38_open_excursion_balance_mean", "l40_gap_overshoot_frequency",
        "l40_gap_range_absorption", "l40_gap_range_extension",
    ]))
    assert out["l38_open_excursion_balance_mean_20"].iloc[49, 1] != out["l38_open_excursion_balance_mean_20"].iloc[49, 1]
    assert out["l38_open_excursion_balance_mean_20"].iloc[50, 1] == out["l38_open_excursion_balance_mean_20"].iloc[50, 1]
    assert out["l40_gap_overshoot_frequency_20"].iloc[69, 0] != out["l40_gap_overshoot_frequency_20"].iloc[69, 0]
    assert out["l40_gap_overshoot_frequency_20"].iloc[70, 2] != out["l40_gap_overshoot_frequency_20"].iloc[70, 2]
    assert out["l40_gap_range_absorption_20"].iloc[69, 0] != out["l40_gap_range_absorption_20"].iloc[69, 0]


def test_open_excursion_zero_tie_survives_adjustment_scale_and_float_noise():
    n = 45
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    columns = ["tiny", "ordinary", "large"]
    scales = np.array([0.0037, 1.0, 1837.0])
    open_values = np.broadcast_to(100.0 * scales, (n, len(scales))).copy()
    # Mathematically symmetric around Open. Tiny independent binary rounding
    # noise stands in for equivalent adjusted-price serialization paths.
    high_values = np.broadcast_to(101.0 * scales, (n, len(scales))).copy()
    low_values = np.broadcast_to(99.0 * scales, (n, len(scales))).copy()
    high_values *= (1.0 + np.array([2.0e-14, -1.0e-14, 1.0e-14]))
    low_values *= (1.0 + np.array([-1.0e-14, 2.0e-14, -2.0e-14]))
    close_values = np.broadcast_to(100.3 * scales, (n, len(scales))).copy()
    p = {
        "open": pd.DataFrame(open_values, index=idx, columns=columns),
        "high": pd.DataFrame(high_values, index=idx, columns=columns),
        "low": pd.DataFrame(low_values, index=idx, columns=columns),
        "close": pd.DataFrame(close_values, index=idx, columns=columns),
    }
    name = "l38_open_excursion_sign_switch_rate"
    atom = build_atoms(p, _cfg([name]))[f"{name}_20"]
    # The relative OHLC tie boundary canonicalizes each symmetric pair to a
    # tie, so there are no nonzero signs to switch.
    assert atom.iloc[19:].isna().all().all()


def test_tail_event_response_needs_full_history_and_minimum_event_counts():
    p = _panels()
    names = [name for name in DIRECTIONS if name.startswith("l39_")]
    out = build_atoms(p, _cfg(names))
    # 41 complete returns are required; the first close return is missing.
    for frame in out.values():
        assert frame.iloc[:41].isna().all().all()
    assert all(frame.iloc[41:].notna().any().any() for frame in out.values())
    broken = {k: v.copy() for k, v in p.items()}
    broken["close"].iloc[50, 0] = np.nan
    broken_out = build_atoms(broken, _cfg(names))
    assert all(frame.iloc[90, 0] != frame.iloc[90, 0] for frame in broken_out.values())


def test_zero_denominators_and_unknown_or_direction_mutation_fail_closed():
    p = _panels(50)
    p["close"].iloc[:, 0] = 100.0
    p["high"].iloc[:, 0] = 100.0
    p["low"].iloc[:, 0] = 100.0
    p["open"].iloc[:, 0] = 100.0
    out = build_atoms(p, _cfg([
        "l37_central_return_bias", "l38_open_excursion_balance_ar1",
        "l38_open_excursion_sign_switch_rate", "l40_gap_range_absorption",
    ]))
    assert out["l37_central_return_bias_20"].iloc[:, 0].isna().all()
    assert out["l38_open_excursion_balance_ar1_20"].iloc[:, 0].isna().all()
    assert out["l38_open_excursion_sign_switch_rate_20"].iloc[:, 0].isna().all()
    with pytest.raises(ValueError, match="unsupported"):
        build_atoms(p, {"mechanisms": {"l36_unknown": {"direction": 1}}})
    with pytest.raises(ValueError, match="direction mismatch"):
        build_atoms(p, {"mechanisms": {"l36_max_close_runup_depth": {"direction": -1}}})
