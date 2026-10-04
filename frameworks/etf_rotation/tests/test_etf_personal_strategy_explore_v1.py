"""Synthetic no-lookahead and full-account accounting checks for the frozen exploration."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/explore_etf_personal_strategy_v1.py"
spec = importlib.util.spec_from_file_location("explore_etf_personal_strategy_v1", SCRIPT)
explore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(explore)


def groups14():
    return {f"g{i}": {"members": [f"s{i}a", f"s{i}b"] if i < 6 else [f"s{i}"]}
            for i in range(8)}


def test_frozen_spec_and_weekly_signal_uses_D_only():
    explore.validate_config(yaml.safe_load(explore.CONFIG.read_text()))
    groups = groups14()
    calendar = pd.bdate_range("2024-01-01", "2024-01-26")
    score = pd.DataFrame([range(8)] * len(calendar), index=calendar, columns=groups,
                         dtype=float)
    intervals, decisions = explore.schedule_weekly(calendar, score, groups, pd.Timestamp("2024-01-01"))
    assert intervals[0]["signal_date"] == pd.Timestamp("2024-01-01")
    assert intervals[0]["entry_date"] == pd.Timestamp("2024-01-03")
    assert intervals[0]["exit_date"] == pd.Timestamp("2024-01-10")
    assert intervals[0]["selected_groups"] == "g7|g6"
    future_revised = score.copy()
    future_revised.loc[calendar[1]:] = list(reversed(range(8)))
    future_intervals, _ = explore.schedule_weekly(calendar, future_revised, groups,
                                                   pd.Timestamp("2024-01-01"))
    assert future_intervals[0]["selected_groups"] == intervals[0]["selected_groups"]
    assert all(row["status"] in {"RANKED", "SKIPPED_ACTIVE_SLEEVE"} for row in decisions)


def test_monthly_trend_uses_trailing_close_and_marks_open_cold():
    groups = groups14()
    symbols = [s for spec in groups.values() for s in spec["members"]]
    calendar = pd.bdate_range("2023-10-02", "2024-03-22")
    close = pd.DataFrame(np.arange(len(calendar), dtype=float)[:, None] + 100,
                         index=calendar, columns=["x"]).reindex(columns=symbols)
    close.loc[:, :] = (np.arange(len(calendar)) + 100)[:, None]
    intervals, decisions = explore.schedule_monthly(calendar, close, groups, pd.Timestamp("2024-01-01"))
    assert intervals[0]["signal_date"] == pd.Timestamp("2024-01-01")
    assert intervals[0]["entry_date"] == pd.Timestamp("2024-01-03")
    assert set(intervals[0]["selected_groups"].split("|")) == set(groups)
    assert intervals[-1]["status"] == "PARTIAL_OPEN"
    revised = close.copy()
    revised.loc[calendar[calendar > pd.Timestamp("2024-01-01")]] *= .1
    future_intervals, _ = explore.schedule_monthly(calendar, revised, groups, pd.Timestamp("2024-01-01"))
    assert future_intervals[0]["selected_groups"] == intervals[0]["selected_groups"]
    assert decisions[0]["status"] == "TREND_ELIGIBLE"


def test_net_rebalance_cost_and_blocked_entry_vs_exit():
    opens = pd.Series({"a": 100.0, "b": 100.0})
    shares, cash, turnover, status = explore._rebalance({}, 1.0, opens, {"a": .5, "b": .5}, .001,
                                                       {"a": True, "b": False})
    assert status == "MISSED_BUY_CASH"
    assert "b" not in shares and cash > .49
    assert turnover == pytest.approx(shares["a"] * 100)
    shares, cash, turnover, status = explore._rebalance(shares, cash, opens, {}, .001,
                                                       {"a": False})
    assert status == "UNPRICED_EXIT_OR_REBALANCE"
    assert turnover == 0


def test_nav_compounds_nonoverlapping_intervals_and_invalid_sale_stops_path():
    calendar = pd.bdate_range("2024-01-01", "2024-01-10")
    symbols = ["a", "b"]
    adjusted_open = pd.DataFrame(100.0, index=calendar, columns=symbols)
    adjusted_close = adjusted_open.copy()
    adjusted_close.loc[calendar[3]:, "a"] = 110.0
    adjusted_open.loc[calendar[3]:, "a"] = 110.0
    adjusted_close.loc[calendar[6]:, "a"] = 121.0
    adjusted_open.loc[calendar[6]:, "a"] = 121.0
    raw_vol = pd.DataFrame(100.0, index=calendar, columns=symbols)
    intervals = [
        {"signal_date": calendar[0], "entry_date": calendar[1], "exit_date": calendar[3],
         "weights": {"a": 1.0}, "b8_weights": {"a": 1.0}, "b14_weights": {"a": 1.0}},
        {"signal_date": calendar[3], "entry_date": calendar[4], "exit_date": calendar[6],
         "weights": {"a": 1.0}, "b8_weights": {"a": 1.0}, "b14_weights": {"a": 1.0}},
    ]
    daily, events = explore.simulate(intervals, "strategy", calendar, adjusted_open,
                                     adjusted_close, adjusted_open, raw_vol, raw_vol, 0, False)
    assert daily.nav.iloc[-1] == pytest.approx(1.21)
    assert events.one_way_turnover_fraction.sum() == pytest.approx(4.0)
    blocked = raw_vol.copy()
    blocked.loc[calendar[3], "a"] = 0
    invalid, invalid_events = explore.simulate(intervals, "strategy", calendar, adjusted_open,
                                               adjusted_close, adjusted_open, raw_vol,
                                               blocked, 10, True)
    assert invalid.nav.loc[invalid.date >= calendar[3]].isna().all()
    assert invalid_events.status.eq("UNPRICED_EXIT_OR_REBALANCE").any()
