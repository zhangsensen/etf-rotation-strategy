import numpy as np
import pandas as pd
import pytest

from etf_strategy.core import etf_group_luna_rounds_d as rounds


def _panels(n=45, members=14):
    idx = pd.bdate_range("2025-01-01", periods=n)
    cols = [f"E{i:02}" for i in range(members)]
    base = np.tile(np.linspace(100, 104, n)[:, None], (1, members))
    member_scale = np.arange(members)[None, :] * 0.1
    close = base + member_scale
    open_ = close * 0.999
    high = np.maximum(open_, close) * 1.01
    low = np.minimum(open_, close) * 0.99
    return {k: pd.DataFrame(v, index=idx, columns=cols) for k, v in {
        "open": open_, "high": high, "low": low, "close": close,
    }.items()}


def _run(panels, names):
    return rounds.build_atoms(panels, {"windows": [20], "mechanisms": {n: {"direction": rounds.DIRECTIONS[n]} for n in names}})


def test_breakout_rejection_depth_matches_hand_calculation():
    p = _panels(45, 14)
    # On the last date, break above the previous 20-day high but close beneath it.
    col = p["close"].columns[0]
    t = p["close"].index[-1]
    prior_h = p["high"].loc[:t].iloc[-21:-1, 0].max()
    prior_l = p["low"].loc[:t].iloc[-21:-1, 0].min()
    width = prior_h - prior_l
    p["high"].loc[t, col] = prior_h + width * 0.1
    p["close"].loc[t, col] = prior_h - width * 0.2
    p["open"].loc[t, col] = prior_h - width * 0.1
    got = _run(p, ["l61_upper_breakout_rejection_depth"])["l61_upper_breakout_rejection_depth_20"]
    # Independently calculate the final 20 raw event depths from the fixed formula.
    raw = []
    for response_date in p["close"].index[-20:]:
        pos = p["close"].index.get_loc(response_date)
        ph = p["high"].iloc[pos-20:pos, 0].max()
        pl = p["low"].iloc[pos-20:pos, 0].min()
        hh, cc = p["high"].iloc[pos, 0], p["close"].iloc[pos, 0]
        raw.append((ph-cc)/(ph-pl) if hh > ph and cc <= ph else 0.0)
    assert got.loc[t, col] == pytest.approx(-np.mean(raw))


def test_state_return_spread_is_conditional_difference():
    p = _panels(45, 14)
    # Construct inside states on response dates 26..45 and set response returns by state.
    col = p["close"].columns[0]
    for j in range(1, 45):
        prev_h, prev_l = p["high"].iloc[j - 1, 0], p["low"].iloc[j - 1, 0]
        if j % 2:
            p["high"].iloc[j, 0] = prev_h
            p["low"].iloc[j, 0] = prev_l
        else:
            p["high"].iloc[j, 0] = prev_h * 1.02
            p["low"].iloc[j, 0] = prev_l * 0.98
    got = _run(p, ["l64_post_inside_return_spread"])["l64_post_inside_return_spread_20"]
    returns, states = [], []
    for j in range(len(p["close"]) - 20, len(p["close"])):
        returns.append(p["close"].iloc[j, 0] / p["close"].iloc[j - 1, 0] - 1.0)
        states.append(
            p["high"].iloc[j - 1, 0] <= p["high"].iloc[j - 2, 0]
            and p["low"].iloc[j - 1, 0] >= p["low"].iloc[j - 2, 0]
        )
    inside_mean = np.mean([r for r, state in zip(returns, states) if state])
    outside_mean = np.mean([r for r, state in zip(returns, states) if not state])
    assert got.iloc[-1, 0] == pytest.approx(inside_mean - outside_mean)


def test_scores_are_scale_free_and_causal_prefix():
    p = _panels()
    names = ["l61_lower_breakdown_reclaim_depth", "l62_ohlc_peak_to_trough_drawdown", "l62_ohlc_trough_to_peak_runup", "l63_rejected_range_to_body_energy", "l63_lower_wick_to_upper_wick_energy", "l64_post_outside_return_spread", "l65_midrange_drift", "l65_gap_scaled_by_prior_range"]
    full = _run(p, names)
    scaled = _run({k: v * 7.3 for k, v in p.items()}, names)
    cut = {k: v.iloc[:-1] for k, v in p.items()}
    prefix = _run(cut, names)
    for key in full:
        pd.testing.assert_frame_equal(full[key], scaled[key], check_exact=False, rtol=1e-10, atol=1e-12)
        pd.testing.assert_series_equal(full[key].iloc[:-1, 0], prefix[key].iloc[:, 0], check_exact=False)


def test_wick_energy_formulas_match_hand_calculation():
    p = _panels(45, 14)
    # Use identical positive bodies and equal upper/lower wicks for member zero.
    for frame in p.values():
        frame.iloc[:, 0] = 100.0
    p["open"].iloc[:, 0] = 100.0
    p["close"].iloc[:, 0] = 101.0
    p["high"].iloc[:, 0] = 102.0
    p["low"].iloc[:, 0] = 99.0
    out = _run(p, ["l63_rejected_range_to_body_energy", "l63_lower_wick_to_upper_wick_energy"])
    assert out["l63_rejected_range_to_body_energy_20"].iloc[-1, 0] == pytest.approx(-2.0)
    assert out["l63_lower_wick_to_upper_wick_energy_20"].iloc[-1, 0] == pytest.approx(0.0)


def test_relative_boundary_ties_do_not_create_breaks_after_rescaling():
    p = _panels(45, 14)
    col = p["close"].columns[0]
    for frame in p.values():
        frame.iloc[:, 0] = 100.0
    p["open"].iloc[:, 0] = 100.0
    p["close"].iloc[:, 0] = 100.0
    p["high"].iloc[:, 0] = 101.0
    p["low"].iloc[:, 0] = 99.0
    p["high"].iloc[-1, 0] = 101.0 * (1.0 + 0.5e-12)
    names = ["l61_upper_breakout_rejection_depth", "l61_failed_break_directional_balance"]
    original = _run(p, names)
    scaled = _run({k: v * 17.0 for k, v in p.items()}, names)
    for key in original:
        assert original[key].iloc[-1, 0] == pytest.approx(0.0)
        assert original[key].iloc[-1, 0] == pytest.approx(scaled[key].iloc[-1, 0])


def test_invalid_bar_propagates_through_strict_window():
    p = _panels()
    names = ["l61_upper_breakout_rejection_depth", "l62_ohlc_peak_to_trough_drawdown", "l63_rejected_range_to_body_energy", "l64_post_inside_return_spread", "l65_midrange_drift"]
    p["high"].iloc[-3, 0] = np.nan
    out = _run(p, names)
    for key in out:
        assert pd.isna(out[key].iloc[-1, 0])
