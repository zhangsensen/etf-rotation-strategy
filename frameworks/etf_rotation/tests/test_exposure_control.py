"""Test actual position reductions and same-session protective-order interaction."""
import backtrader as bt
import pandas as pd
import pytest

from etf_strategy.auditor.core.engine import GenericStrategy, PandasData
from etf_strategy.core.exposure_control import retained_scale


def test_scale_accounts_for_mixed_sell_fees():
    values, rates = {"A": 800., "B": 100.}, {"A": .002, "B": .005}
    scale = retained_scale(100., values, rates, .1)
    fees = sum(values[t] * (1 - scale) * rates[t] for t in values)
    assert sum(values.values()) * scale / (1000 - fees) == pytest.approx(.1)
    assert retained_scale(100., values, rates, 0.) == 0
    assert retained_scale(100., values, rates, 1.) == 1


def run_case(mode="cap_retained", stop=False, gap=False, activation=None, target=.1, recover=False):
    dates = pd.bdate_range("2026-01-05", periods=8)
    frame = pd.DataFrame({"open": 100., "high": 101., "low": 99., "close": 100., "volume": 10000.}, index=dates)
    if stop:
        # The retained overnight position is reduced at open and can still stop
        # later in the same session. The original full-size stop must be canceled.
        frame.loc[dates[4], "low"] = 89. if gap else 94.
        frame.loc[dates[4], "open"] = 90. if gap else 100.
        frame.loc[dates[4], "close"] = 92. if gap else 99.
    scores = pd.DataFrame({"A": 2., "B": 1.}, index=dates)
    timing = pd.Series(1., index=dates)
    timing.loc[dates[3]:] = target
    if recover:
        timing.loc[dates[5]:] = 1.
    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.broker.setcash(100000.)
    cerebro.broker.setcommission(commission=.002)
    cerebro.broker.set_checksubmit(False)
    cerebro.broker.set_coo(True)
    for name in ["A", "B"]:
        cerebro.adddata(PandasData(dataname=frame.copy(), name=name))
    cerebro.addstrategy(GenericStrategy, scores=scores, timing=timing, etf_codes=["A", "B"],
                        pos_size=1, lookback=1, rebalance_schedule=[1, 3, 5] if recover else [1, 3], use_t1_open=True,
                        dynamic_leverage_enabled=False, min_hold_days=9, delta_rank=.1,
                        sizing_commission_rate=.002, etf_stop_loss=.05 if stop else 0,
                        exposure_control=mode, exposure_start_date=activation)
    s = cerebro.run()[0]
    return s, dates


def test_existing_holding_is_reduced_despite_nine_day_lock():
    legacy, _ = run_case(mode="legacy")
    fixed, dates = run_case()
    assert legacy.exposure_events[-1]["planned_exposure"] > .99
    assert fixed.exposure_events[-1]["planned_exposure"] == pytest.approx(.1)
    assert fixed.getposition(fixed.etf_map["A"]).size * 100 / fixed.broker.getvalue() == pytest.approx(.1)
    reduced = [o for o in fixed.orders if o["reason"] == "exposure_reduce"]
    assert len(reduced) == 1 and reduced[0]["date"] == dates[4].date()
    assert fixed.margin_failures == 0


@pytest.mark.parametrize("gap", [False, True])
def test_resized_stop_protects_remaining_shares_without_short_sale(gap):
    s, dates = run_case(stop=True, gap=gap)
    reductions = [o for o in s.orders if o["reason"] == "exposure_reduce"]
    stops = [o for o in s.orders if o["reason"] == "fixed_stop"]
    buys = [o for o in s.orders if o["type"] == "BUY"]
    assert len(reductions) == len(stops) == len(buys) == 1
    assert buys[0]["size"] + reductions[0]["size"] + stops[0]["size"] == pytest.approx(0)
    assert stops[0]["price"] == pytest.approx(90. if gap else 95.)
    assert reductions[0]["date"] == stops[0]["date"] == dates[4].date()
    assert s.getposition(s.etf_map["A"]).size == 0
    assert s.broker.getcash() == pytest.approx(s.broker.getvalue())


def test_zero_target_liquidates_without_duplicate_stop():
    s, _ = run_case(stop=True, target=0.)
    assert len([o for o in s.orders if o["type"] == "SELL"]) == 1
    assert s.stop_events == []
    assert s.getposition(s.etf_map["A"]).size == 0


def test_future_activation_preserves_legacy_exposure():
    s, _ = run_case(activation="2026-02-01")
    assert s.exposure_events[-1]["planned_exposure"] > .99
    assert not any(o["reason"] == "exposure_reduce" for o in s.orders)
