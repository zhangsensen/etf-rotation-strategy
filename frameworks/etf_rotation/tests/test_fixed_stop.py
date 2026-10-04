"""Real broker tests of protection, gap fills and interaction with rotation."""
import backtrader as bt
import numpy as np
import pandas as pd
import pytest

from etf_strategy.auditor.core.engine import GenericStrategy, PandasData
from etf_strategy.core.fixed_stop import load_fixed_stop


def simulate(*, loss=.05, gap=False, activation=None, rotate=False, stop_day=3):
    dates = pd.bdate_range("2026-01-05", periods=9)
    a = pd.DataFrame({"open": 100., "high": 101., "low": 99.,
                      "close": 100., "volume": 10000.}, index=dates)
    # Entry-day low deliberately crosses the line: T+1 protection must not sell.
    a.loc[dates[2], "low"] = 90.
    a.loc[dates[stop_day], ["open", "high", "low", "close"]] = (
        [90., 94., 88., 92.] if gap else [98., 100., 94., 99.])
    b = pd.DataFrame({"open": 100., "high": 101., "low": 99.,
                      "close": 100., "volume": 10000.}, index=dates)
    scores = pd.DataFrame({"A": 2., "B": 1.}, index=dates)
    if rotate:
        scores.loc[dates[2]:, "B"] = 3.
    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.broker.setcash(100000.)
    cerebro.broker.setcommission(commission=.002)
    cerebro.broker.set_checksubmit(False)
    cerebro.broker.set_coo(True)
    for name, frame in [("A", a), ("B", b)]:
        cerebro.adddata(PandasData(dataname=frame, name=name))
    cerebro.addstrategy(GenericStrategy, scores=scores, etf_codes=["A", "B"],
                        pos_size=1, lookback=1, rebalance_schedule=[1, 3, 6],
                        use_t1_open=True, dynamic_leverage_enabled=False,
                        sizing_commission_rate=.002, delta_rank=0 if rotate else .1,
                        min_hold_days=0 if rotate else 9, etf_stop_loss=loss,
                        etf_stop_start_date=activation)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="returns")
    strategy = cerebro.run()[0]
    return strategy, dates


def test_intraday_stop_overrides_min_hold_and_arms_only_next_session():
    s, dates = simulate()
    event, = s.stop_events
    assert event["submitted_date"] == str(dates[2].date())
    assert event["execution_date"] == str(dates[3].date())
    assert event["execution_price"] == 95.
    assert event["commission"] > 0
    assert not event["gap_through"]
    assert not any(o["type"] == "BUY" and o["date"] == dates[3].date() for o in s.orders)
    assert not any(o["type"] == "BUY" and o["ticker"] == "A"
                   and o["date"] == dates[4].date() for o in s.orders)
    # Stop really liquidated the position; no stale shadow holdings or short sale.
    assert s.getposition(s.etf_map["A"]).size >= 0
    assert len([o for o in s.orders if o["reason"] == "fixed_stop"]) == 1


def test_gap_fills_at_open_and_can_lose_more_than_five_percent():
    s, _ = simulate(gap=True)
    event, = s.stop_events
    assert event["execution_price"] == 90.
    assert event["price_return"] == pytest.approx(-.10)
    assert event["gap_through"]


def test_disabled_stop_retains_legacy_holdings():
    s, _ = simulate(loss=0)
    assert s.stop_events == []
    assert all(o["type"] == "BUY" for o in s.orders)


def test_activation_does_not_change_previous_returns():
    baseline, _ = simulate(loss=0)
    protected, dates = simulate(activation="2026-01-09", stop_day=4)
    comparison, _ = simulate(loss=0, stop_day=4)
    before = dates[4].to_pydatetime()
    a = comparison.analyzers.returns.get_analysis()
    b = protected.analyzers.returns.get_analysis()
    assert {d: v for d, v in a.items() if d < before} == {d: v for d, v in b.items() if d < before}
    assert protected.stop_events[0]["execution_date"] == str(dates[4].date())


def test_rotation_cancels_protection_without_double_selling():
    s, dates = simulate(rotate=True, stop_day=4)
    assert s.stop_events == []
    sells = [o for o in s.orders if o["type"] == "SELL"]
    assert len(sells) == 1
    assert sells[0]["date"] == dates[4].date()
    assert s.getposition(s.etf_map["A"]).size == 0


@pytest.mark.parametrize("value", [-.1, 1, float("nan"), float("inf")])
def test_invalid_config_is_rejected(value):
    with pytest.raises(ValueError):
        load_fixed_stop({"backtest": {"risk_control": {"etf_stop_loss": value}}})


def test_config_is_not_a_dead_field():
    assert load_fixed_stop({"backtest": {"risk_control": {"etf_stop_loss": .05}}})["etf_stop_loss"] == .05
    assert load_fixed_stop({"backtest": {"risk_control": {"enabled": False, "etf_stop_loss": .05}}})["etf_stop_loss"] == 0
    assert load_fixed_stop({"backtest": {"risk_control": {"etf_stop_enabled": False, "etf_stop_loss": .05}}})["etf_stop_loss"] == 0


@pytest.mark.parametrize("gap", [False, True])
def test_vec_and_bt_agree_on_actual_stop_effect(gap):
    from batch_vec_backtest import run_vec_backtest
    from etf_strategy.core.utils.rebalance import generate_rebalance_schedule

    dates = pd.bdate_range("2025-01-01", periods=260)
    close = np.full((260, 2), 100.)
    opens = close.copy()
    highs = close + 1
    lows = close - 1
    lows[256, 0] = 90.  # Entry-day dip must not cause a sale in either engine.
    lows[257, 0] = 89. if gap else 95.  # equality must trigger
    opens[257, 0] = 90. if gap else 98.
    close[257, 0] = 92. if gap else 99.
    scores = pd.DataFrame({"A": 2., "B": 1.}, index=dates)
    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.broker.setcash(100000.)
    cerebro.broker.setcommission(commission=.002)
    cerebro.broker.set_checksubmit(False)
    cerebro.broker.set_coo(True)
    for n, name in enumerate(["A", "B"]):
        df = pd.DataFrame({"open": opens[:, n], "high": highs[:, n],
                           "low": lows[:, n], "close": close[:, n],
                           "volume": 10000.}, index=dates)
        cerebro.adddata(PandasData(dataname=df, name=name))
    cerebro.addstrategy(GenericStrategy, scores=scores, etf_codes=["A", "B"],
                        rebalance_schedule=generate_rebalance_schedule(260, 252, 5),
                        pos_size=1, lookback=252, use_t1_open=True,
                        dynamic_leverage_enabled=False, sizing_commission_rate=.002,
                        delta_rank=.1, min_hold_days=9, etf_stop_loss=.05)
    s = cerebro.run()[0]
    result = run_vec_backtest(scores.to_numpy()[:, :, None], close, opens, highs, lows,
                             np.ones(260), [0], freq=5, pos_size=1,
                             initial_capital=100000., commission_rate=.002, lookback=252,
                             use_t1_open=True, delta_rank=.1, min_hold_days=9,
                             etf_stop_loss=.05, stop_on_rebalance_only=True)
    assert result[-1]["fixed_stop_count"] == len(s.stop_events) == 1
    # Legacy BT applies a 1e-6 sizing safety margin; VEC does not.
    assert result[0][-1] == pytest.approx(s.broker.getvalue(), abs=.02)
    assert s.stop_events[0]["execution_price"] == (90. if gap else 95.)
