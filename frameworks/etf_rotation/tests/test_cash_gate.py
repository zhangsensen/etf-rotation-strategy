"""Cash must be an executable portfolio state, with no same-bar look-ahead."""
import numpy as np
import pandas as pd
import pytest
import backtrader as bt

from etf_strategy.core.cash_gate import apply_cash_gate, load_cash_gate
from etf_strategy.auditor.core.engine import GenericStrategy, PandasData


def config(mode="dual_worst", start=None, exposure="cap_retained"):
    return {"backtest": {
        "exposure_control": {"mode": exposure},
        "cash_gate": {"mode": mode, "start_date": start},
        "timing": {"enabled": True, "extreme_position": .1},
        "regime_gate": {"enabled": True, "mode": "volatility",
                        "volatility": {"exposures": [1., .7, .4, .1]}},
    }}


def test_only_existing_joint_worst_state_maps_to_cash():
    dates = pd.bdate_range("2026-01-05", periods=5)
    adjusted, audit = apply_cash_gate([1., .1, .1, 1., .1], [1., .4, .1, .1, .1], dates, config())
    assert adjusted.tolist() == pytest.approx([1., .04, 0., .1, 0.])
    assert audit.risk_off.tolist() == [False, False, True, False, True]


def test_activation_preserves_prefix_and_does_not_shift_again():
    dates = pd.bdate_range("2026-01-05", periods=5)
    adjusted, audit = apply_cash_gate(np.full(5, .1), np.full(5, .1), dates,
                                      config(start=str(dates[3].date())))
    assert adjusted.tolist() == pytest.approx([.01, .01, .01, 0., 0.])
    assert audit.risk_off.tolist() == [False, False, False, True, True]


def test_cash_gate_requires_a_real_liquidation_executor():
    with pytest.raises(ValueError, match="cap_retained"):
        load_cash_gate(config(exposure="legacy"))


def test_zero_target_liquidates_and_later_reenters_at_scheduled_open():
    dates = pd.bdate_range("2026-01-05", periods=8)
    frame = pd.DataFrame({"open": 100., "high": 101., "low": 99., "close": 100.,
                          "volume": 10000.}, index=dates)
    scores = pd.DataFrame({"A": 2., "B": 1.}, index=dates)
    timing = pd.Series(1., index=dates)
    timing.loc[dates[3]:dates[4]] = 0.  # deliberately between scheduled rebalances
    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.broker.setcash(100000.)
    cerebro.broker.setcommission(commission=.002)
    cerebro.broker.set_checksubmit(False)
    cerebro.broker.set_coo(True)
    for name in ["A", "B"]:
        cerebro.adddata(PandasData(dataname=frame.copy(), name=name))
    cerebro.addstrategy(GenericStrategy, scores=scores, timing=timing, etf_codes=["A", "B"],
                        pos_size=1, lookback=1, rebalance_schedule=[1, 5], use_t1_open=True,
                        dynamic_leverage_enabled=False, min_hold_days=9, delta_rank=.1,
                        sizing_commission_rate=.002, exposure_control="cap_retained",
                        cash_gate_mode="dual_worst")
    cash = cerebro.run()[0]
    sells = [o for o in cash.orders if o["type"] == "SELL"]
    assert len(sells) == 1 and sells[0]["date"] == dates[4].date()
    assert sells[0]["reason"] == "cash_exit"
    buys = [o for o in cash.orders if o["type"] == "BUY"]
    assert len(buys) == 2 and buys[1]["date"] == dates[6].date()
    assert cash.getposition(cash.etf_map["A"]).size > 0
    assert cash.cash_gate_events[0]["signal_date"] == str(dates[3].date())
    assert cash.cash_gate_events[0]["execution_date"] == str(dates[4].date())
    assert cash.cash_gate_events[0]["executions"][0]["ticker"] == "A"
