import numpy as np
import pandas as pd

from etf_strategy.core.etf_group_luna_rounds_f import build_atoms


OHLC_NAME = "l71_range_lag1_autocorrelation_20"
AMOUNT_NAME = "l71_amount_anomaly_lag1_autocorrelation_20"
CFG = {
    "windows": [20],
    "mechanisms": {
        "l71_range_lag1_autocorrelation": {"direction": -1},
        "l71_amount_anomaly_lag1_autocorrelation": {"direction": 1},
    },
}


def _panels(n=100):
    rng = np.random.default_rng(31)
    index = pd.bdate_range("2024-01-02", periods=n)
    columns = [f"ETF{i:02d}" for i in range(14)]
    base = 100.0 * np.exp(np.cumsum(rng.normal(0.0002, 0.002, size=(n, 14)), axis=0))
    width = np.empty((n, 14))
    width[0] = 0.006
    for t in range(1, n):
        width[t] = 0.62 * width[t - 1] + 0.38 * rng.uniform(0.002, 0.025, size=14)
    open_ = base * 0.999
    close = base * 1.001
    high = np.maximum(open_, close) + base * width / 2
    low = np.minimum(open_, close) - base * width / 2
    log_amount = np.empty((n, 14))
    log_amount[0] = np.log(1e8)
    innovations = rng.normal(0.0, 0.18, size=(n, 14))
    for t in range(1, n):
        log_amount[t] = 0.68 * log_amount[t - 1] + (1 - 0.68) * np.log(1e8) + innovations[t]
    arrays = {
        "open": open_, "high": high, "low": low, "close": close,
        "amount": np.exp(log_amount),
    }
    return {key: pd.DataFrame(value, index=index, columns=columns) for key, value in arrays.items()}


def _scores(panels):
    return build_atoms(panels, CFG)


def test_scores_match_manual_twenty_pair_calculations():
    panels = _panels()
    out = _scores(panels)
    col, t = "ETF00", 60

    daily_range = (panels["high"][col] - panels["low"][col]) / panels["close"][col].shift(1)
    expected_range = -np.corrcoef(
        daily_range.iloc[t - 19:t + 1], daily_range.shift(1).iloc[t - 19:t + 1]
    )[0, 1]
    assert np.isclose(out[OHLC_NAME].loc[panels["close"].index[t], col], expected_range)

    log_amount = np.log(panels["amount"][col])
    anomaly = pd.Series(np.nan, index=log_amount.index)
    for i in range(20, len(log_amount)):
        anomaly.iloc[i] = log_amount.iloc[i] - log_amount.iloc[i - 20:i].mean()
    expected_amount = np.corrcoef(
        anomaly.iloc[t - 19:t + 1], anomaly.shift(1).iloc[t - 19:t + 1]
    )[0, 1]
    assert np.isclose(out[AMOUNT_NAME].loc[panels["close"].index[t], col], expected_amount)
    assert out[OHLC_NAME].iloc[:21].isna().all().all()
    assert out[AMOUNT_NAME].iloc[:40].isna().all().all()


def test_empty_and_zero_variance_inputs_return_nan():
    panels = _panels()
    empty = {key: frame * np.nan for key, frame in panels.items()}
    empty_out = _scores(empty)
    assert empty_out[OHLC_NAME].isna().all().all()
    assert empty_out[AMOUNT_NAME].isna().all().all()

    flat = {key: frame.copy() for key, frame in panels.items()}
    for key, value in {"open": 10.0, "high": 10.5, "low": 9.5, "close": 10.0}.items():
        flat[key].iloc[:, 0] = value
    flat["amount"].iloc[:, 0] = 1e8
    flat_out = _scores(flat)
    assert flat_out[OHLC_NAME]["ETF00"].isna().all()
    assert flat_out[AMOUNT_NAME]["ETF00"].isna().all()


def test_missing_observation_invalidates_every_dependent_window():
    panels = _panels()
    broken = {key: frame.copy() for key, frame in panels.items()}
    broken["high"].iloc[50, 0] = broken["low"].iloc[50, 0] - 1.0
    broken["amount"].iloc[50, 1] = np.nan
    out = _scores(broken)
    assert out[OHLC_NAME].iloc[50:71, 0].isna().all()
    expected = _scores(panels)[OHLC_NAME]
    assert np.isclose(out[OHLC_NAME].iloc[49, 0], expected.iloc[49, 0])
    assert np.isclose(out[OHLC_NAME].iloc[71, 0], expected.iloc[71, 0])
    assert out[AMOUNT_NAME].iloc[50:91, 1].isna().all()


def test_both_scores_are_invariant_to_common_price_or_amount_scale():
    panels = _panels()
    base = _scores(panels)
    scaled = {key: frame * 11.0 for key, frame in panels.items()}
    rescaled = _scores(scaled)
    for name in (OHLC_NAME, AMOUNT_NAME):
        assert np.allclose(base[name], rescaled[name], equal_nan=True, rtol=1e-12, atol=1e-12)


def test_prefix_and_future_perturbation_do_not_change_past_scores():
    panels = _panels()
    full = _scores(panels)
    cutoff = 65
    truncated = {key: frame.iloc[:cutoff + 1].copy() for key, frame in panels.items()}
    truncated_out = _scores(truncated)
    perturbed = {key: frame.copy() for key, frame in panels.items()}
    for frame in perturbed.values():
        frame.iloc[cutoff + 1:] *= 1.7
    perturbed_out = _scores(perturbed)
    for name in (OHLC_NAME, AMOUNT_NAME):
        assert np.allclose(full[name].iloc[:cutoff + 1], truncated_out[name], equal_nan=True)
        assert np.allclose(full[name].iloc[:cutoff + 1], perturbed_out[name].iloc[:cutoff + 1], equal_nan=True)
