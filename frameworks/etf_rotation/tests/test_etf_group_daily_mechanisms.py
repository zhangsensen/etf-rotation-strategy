import numpy as np
import pandas as pd
import yaml

from etf_strategy.core.etf_group_daily_mechanisms import build_atoms, leakage_checks
from etf_strategy.core.etf_group_discovery import aggregate


def _cfg():
    return yaml.safe_load(open("frameworks/etf_rotation/configs/group_ic_batch2_20260922.yaml"))


def _panels(n=25):
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    close = pd.DataFrame({"a": np.linspace(100, 125, n), "b": np.linspace(80, 92, n)}, index=idx)
    open_ = close.copy()
    open_.iloc[1:, 0] = close.iloc[:-1, 0].to_numpy() * 1.02
    open_.iloc[1:, 1] = close.iloc[:-1, 1].to_numpy() * 0.98
    return {"open": open_, "close": close}


def test_exact_formulas_and_zero_denominator():
    panels = _panels()
    out = build_atoms(panels, _cfg())
    close, open_ = panels["close"], panels["open"]
    gap = open_.div(close.shift(1)) - 1
    session = close.div(open_) - 1
    expected = (gap.abs() * session).rolling(20, min_periods=20).sum().div(
        gap.pow(2).rolling(20, min_periods=20).sum().replace(0, np.nan)
    )
    pd.testing.assert_frame_equal(out["shock_session_response_20"], expected)
    ret = close.pct_change(fill_method=None)
    q = ret.clip(upper=0).abs().shift(1)
    expected_recovery = (q * ret).rolling(20, min_periods=20).sum().div(
        (q.pow(2)).rolling(20, min_periods=20).sum().replace(0, np.nan)
    )
    pd.testing.assert_frame_equal(out["downshock_recovery_20"], expected_recovery)

    flat = {k: v.copy() for k, v in panels.items()}
    flat["open"].iloc[1:] = flat["close"].iloc[:-1].to_numpy()
    assert out["shock_session_response_20"].iloc[-1].notna().all()
    assert build_atoms(flat, _cfg())["shock_session_response_20"].iloc[-1].isna().all()


def test_missing_propagates_and_member_aggregation_is_fixed():
    panels = _panels(35)
    panels["close"].iloc[10, 0] = np.nan
    out = build_atoms(panels, _cfg())
    assert out["shock_session_response_20"].iloc[20, 0] != out["shock_session_response_20"].iloc[20, 0]
    groups = {"multi": {"members": ["a", "b"]}, "single": {"members": ["a"]}}
    group = aggregate(out["shock_session_response_20"], groups)
    assert group.loc[group.index[20], "multi"] != group.loc[group.index[20], "multi"]
    assert group.loc[group.index[34], "single"] == out["shock_session_response_20"].iloc[34, 0]


def test_prefix_future_perturbation_and_scale_invariance():
    panels = _panels()
    assert all(leakage_checks(panels, _cfg(), "2025-01-18").values())
    scaled = {k: v * 17.0 for k, v in panels.items()}
    original = build_atoms(panels, _cfg())
    scaled_out = build_atoms(scaled, _cfg())
    for name in original:
        pd.testing.assert_frame_equal(original[name], scaled_out[name], check_exact=False, rtol=1e-10, atol=1e-12)


def test_nonempty_downshock_formula_prefix_and_missing_history():
    idx = pd.date_range('2025-01-01', periods=80)
    returns = np.tile([.02, -.01, .005, -.03], 20)
    close = pd.DataFrame({'a': 100 * np.cumprod(1 + returns)}, index=idx)
    open_ = close.shift(1) * 1.004
    open_.iloc[0] = close.iloc[0]
    panels = {'open': open_, 'close': close}
    atoms = build_atoms(panels, _cfg())
    assert all(a.iloc[40].notna().all() for a in atoms.values())
    ret = close.a.pct_change(fill_method=None).to_numpy()
    numerator = sum(max(-ret[t-1], 0) * ret[t] for t in range(60, 80))
    denominator = sum(max(-ret[t-1], 0)**2 for t in range(60, 80))
    np.testing.assert_allclose(atoms['downshock_recovery_20'].iloc[-1, 0], numerator/denominator)
    assert all(leakage_checks(panels, _cfg(), idx[50]).values())
    broken = {k: v.copy() for k, v in panels.items()}
    broken['close'].iloc[45, 0] = np.nan
    assert build_atoms(broken, _cfg())['downshock_recovery_20'].iloc[50, 0] != build_atoms(broken, _cfg())['downshock_recovery_20'].iloc[50, 0]
