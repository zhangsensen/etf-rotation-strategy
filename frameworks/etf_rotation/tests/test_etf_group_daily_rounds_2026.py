import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_group_daily_rounds import build_atoms, leakage_checks


DIRECTIONS = {
    "bipower_jump_share": -1,
    "market_coskewness": 1,
    "ohlc_range_overlap": -1,
    "intraday_body_utilization": 1,
    "downside_semivariance_share": -1,
    "squared_return_ar1": -1,
    "overnight_variance_share": -1,
    "close_extrema_time_order": 1,
    "downside_price_impact_share": -1,
    "peer_lag_return_beta": 1,
}


def _panels(n=90):
    dates = pd.date_range("2025-01-01", periods=n)
    t = np.arange(n, dtype=float)
    cols = [f"ETF{i:02d}" for i in range(14)]
    close = pd.DataFrame(
        {
            c: (80.0 + 3.0 * j)
            * np.cumprod(1.0 + 0.004 * np.sin(0.21 * t + j * 0.31) + 0.001 * np.cos(0.13 * t + j))
            for j, c in enumerate(cols)
        },
        index=dates,
    )
    intraday = pd.DataFrame(
        {c: 0.003 * np.sin(0.17 * t + j * 0.27) for j, c in enumerate(cols)},
        index=dates,
    )
    open_ = close / (1.0 + intraday)
    high = pd.DataFrame(
        np.maximum(open_.to_numpy(), close.to_numpy()) * (1.0 + 0.006 + 0.001 * np.sin(t[:, None] + np.arange(14))),
        index=dates,
        columns=cols,
    )
    low = pd.DataFrame(
        np.minimum(open_.to_numpy(), close.to_numpy()) * (1.0 - 0.006 - 0.001 * np.cos(t[:, None] + np.arange(14))),
        index=dates,
        columns=cols,
    )
    amount = pd.DataFrame(
        {c: 1000.0 * (1.2 + 0.2 * np.sin(0.11 * t + j)) for j, c in enumerate(cols)},
        index=dates,
    )
    return {"open": open_, "high": high, "low": low, "close": close, "amount": amount}


def _cfg(names=None):
    names = tuple(names or DIRECTIONS)
    return {
        "windows": [20],
        "mechanisms": {name: {"direction": DIRECTIONS[name]} for name in names},
    }


def _reference(panels):
    close, open_, high, low, amount = (panels[k] for k in ("close", "open", "high", "low", "amount"))
    r = close.pct_change(fill_method=None)
    r20 = r.iloc[-20:].to_numpy()
    out = {}

    rv = np.square(r20[:, 0]).sum()
    bv = (np.pi / 2.0) * (20.0 / 19.0) * np.abs(r20[1:, 0] * r20[:-1, 0]).sum()
    out["bipower_jump_share"] = max(rv - bv, 0.0) / rv

    peer = r.iloc[-20:].drop(columns=close.columns[0]).mean(axis=1).to_numpy()
    own = r20[:, 0]
    xc, yc = own - own.mean(), peer - peer.mean()
    out["market_coskewness"] = np.mean(xc * yc**2) / (np.sqrt(np.mean(xc**2)) * np.mean(yc**2))

    h, l = high.iloc[-21:, 0].to_numpy(), low.iloc[-21:, 0].to_numpy()
    overlaps = np.maximum(0.0, np.minimum(h[1:], h[:-1]) - np.maximum(l[1:], l[:-1]))
    unions = np.maximum(h[1:], h[:-1]) - np.minimum(l[1:], l[:-1])
    out["ohlc_range_overlap"] = np.mean(overlaps / unions)

    o, c = open_.iloc[-20:, 0].to_numpy(), close.iloc[-20:, 0].to_numpy()
    h, l = high.iloc[-20:, 0].to_numpy(), low.iloc[-20:, 0].to_numpy()
    out["intraday_body_utilization"] = np.mean(np.abs(c - o) / (h - l))

    down = np.minimum(r20[:, 0], 0.0)
    out["downside_semivariance_share"] = np.square(down).sum() / np.square(r20[:, 0]).sum()

    squared = np.square(r.iloc[:, 0].to_numpy())
    x, y = squared[-20:], squared[-21:-1]
    out["squared_return_ar1"] = np.corrcoef(x, y)[0, 1]

    gaps = np.log(open_.iloc[-20:, 0].to_numpy() / close.iloc[-21:-1, 0].to_numpy())
    bodies = np.log(close.iloc[-20:, 0].to_numpy() / open_.iloc[-20:, 0].to_numpy())
    out["overnight_variance_share"] = np.square(gaps).sum() / (np.square(gaps).sum() + np.square(bodies).sum())

    values = close.iloc[-20:, 0].to_numpy()
    rel = values / values[-1]
    hi_t = np.flatnonzero(np.isclose(rel, rel.max(), rtol=1e-12, atol=0.0)).mean()
    lo_t = np.flatnonzero(np.isclose(rel, rel.min(), rtol=1e-12, atol=0.0)).mean()
    out["close_extrema_time_order"] = (hi_t - lo_t) / 19.0

    amt = amount.iloc[-20:, 0].to_numpy()
    impact = np.abs(r20[:, 0]) / amt
    down_impact = np.maximum(-r20[:, 0], 0.0) / amt
    out["downside_price_impact_share"] = down_impact.sum() / impact.sum()

    peer_all = r.iloc[-21:, 1:].mean(axis=1).to_numpy()
    peer_lag, own_now = peer_all[:-1], r.iloc[-20:, 0].to_numpy()
    out["peer_lag_return_beta"] = np.mean((own_now - own_now.mean()) * (peer_lag - peer_lag.mean())) / np.var(peer_lag)
    return out


def test_ten_atoms_match_hand_computed_last_date_values():
    panels = _panels()
    actual = build_atoms(panels, _cfg())
    expected = _reference(panels)
    for name, raw in expected.items():
        assert actual[f"{name}_20"].columns.size == 14
        assert actual[f"{name}_20"].iloc[-1, 0] == pytest.approx(raw * DIRECTIONS[name], rel=1e-9, abs=1e-11)


def test_daily_atoms_are_price_scale_invariant_and_prefix_safe():
    panels = _panels()
    original = build_atoms(panels, _cfg())
    scaled = {key: frame.copy() for key, frame in panels.items()}
    member_scales = np.linspace(0.25, 4.0, 14)
    for key in ("open", "high", "low", "close"):
        scaled[key] = scaled[key].mul(member_scales, axis=1)
    scaled_out = build_atoms(scaled, _cfg())
    for name in original:
        pd.testing.assert_frame_equal(original[name], scaled_out[name], check_exact=False, rtol=1e-9, atol=1e-11)
    assert all(leakage_checks(panels, _cfg(), panels["close"].index[65]).values())


def test_daily_atoms_propagate_missingness_and_peer_features_require_all_14():
    panels = _panels()
    panels["close"].iloc[50, 4] = np.nan
    out = build_atoms(panels, _cfg())
    assert pd.isna(out["downside_semivariance_share_20"].iloc[55, 4])
    assert pd.notna(out["downside_semivariance_share_20"].iloc[80, 4])
    assert out["market_coskewness_20"].iloc[55].isna().all()
    assert out["peer_lag_return_beta_20"].iloc[55].isna().all()

    with pytest.raises(ValueError, match="fixed 14-member population"):
        build_atoms({key: value.iloc[:, :13] for key, value in _panels().items()}, _cfg(["market_coskewness"]))
