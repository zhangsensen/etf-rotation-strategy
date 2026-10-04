import numpy as np
import pandas as pd
import yaml

from etf_strategy.core.etf_group_daily_rounds import build_atoms, leakage_checks


ROOT = "frameworks/etf_rotation/"
CONFIG = ROOT + "configs/group_ic_reverse_realized_vol_term_structure_20260922.yaml"


def _panels(n=80):
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    # Nonlinear paths avoid a zero-volatility denominator while remaining
    # deterministic and small enough for a synthetic unit test.
    steps_a = np.array([0.004, -0.002, 0.006, -0.003, 0.001] * (n // 5 + 1))[:n]
    steps_b = np.array([-0.003, 0.005, -0.001, 0.004, -0.002] * (n // 5 + 1))[:n]
    close = pd.DataFrame(
        {"a": 100 * np.cumprod(1 + steps_a), "b": 80 * np.cumprod(1 + steps_b)},
        index=idx,
    )
    open_ = close * (1 - 0.001)
    high = pd.concat((open_, close), axis=0).groupby(level=0).max() * 1.01
    low = pd.concat((open_, close), axis=0).groupby(level=0).min() * 0.99
    return {"open": open_, "high": high, "low": low, "close": close}


def _cfg():
    with open(CONFIG) as handle:
        return yaml.safe_load(handle)


def test_post_result_reverse_is_explicit_and_flips_only_direction():
    cfg = _cfg()
    assert cfg["notes"]["candidate_name"] == "reverse_realized_vol_term_structure_5_20"
    spec = cfg["mechanisms"]["reverse_realized_vol_term_structure_5"]
    assert spec["direction"] == 1
    assert spec["parent_candidate"] == "realized_vol_term_structure_5_20"
    assert spec["parent_direction"] == -1
    assert spec["direction_source"] == "POST_RESULT_REVERSE"
    assert spec["independent_confirmation"] is False

    panels = _panels()
    reverse = build_atoms(panels, cfg)["reverse_realized_vol_term_structure_5_20"]
    returns = panels["close"].pct_change(fill_method=None)
    raw = returns.rolling(5, min_periods=5).std().div(
        returns.rolling(20, min_periods=20).std()
    )
    pd.testing.assert_frame_equal(reverse, raw)


def test_reverse_is_scale_invariant_complete_window_and_prefix_safe():
    panels = _panels()
    cfg = _cfg()
    output = build_atoms(panels, cfg)["reverse_realized_vol_term_structure_5_20"]
    assert output.iloc[:19].isna().all().all()
    assert output.iloc[30:].notna().any().any()
    assert all(leakage_checks(panels, cfg, panels["close"].index[60]).values())

    scaled = {key: value.copy() for key, value in panels.items()}
    for key in ("open", "high", "low", "close"):
        scaled[key] *= 17.0
    scaled_output = build_atoms(scaled, cfg)["reverse_realized_vol_term_structure_5_20"]
    pd.testing.assert_frame_equal(output, scaled_output, check_exact=False, rtol=1e-10, atol=1e-12)


def test_reverse_propagates_missing_price_window_and_zero_denominator():
    cfg = _cfg()
    panels = _panels()
    panels["close"].iloc[25, 0] = np.nan
    output = build_atoms(panels, cfg)["reverse_realized_vol_term_structure_5_20"]
    assert pd.isna(output.iloc[30, 0])

    flat = _panels()
    flat["close"]["a"] = 100.0
    flat_output = build_atoms(flat, cfg)["reverse_realized_vol_term_structure_5_20"]
    assert pd.isna(flat_output.iloc[-1, 0])
