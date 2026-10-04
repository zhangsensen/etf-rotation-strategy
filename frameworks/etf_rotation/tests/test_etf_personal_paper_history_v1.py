"""Synthetic timing and accounting tests for descriptive history replay."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts/research/replay_etf_personal_paper_history_v1.py"
spec = importlib.util.spec_from_file_location("replay_etf_personal_paper_history_v1", SCRIPT)
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)


def fixture():
    groups = {f"g{i}": {"members": [f"s{i}a", f"s{i}b"] if i < 6 else [f"s{i}"]}
              for i in range(8)}
    symbols = [symbol for spec in groups.values() for symbol in spec["members"]]
    signals = pd.DatetimeIndex(["2026-03-12", "2026-03-13"])
    dates = pd.DataFrame({"entry_date": pd.to_datetime(["2026-03-16", "2026-03-17"]),
                          "exit_date": pd.to_datetime(["2026-03-23", "2026-03-24"])}, index=signals)
    calendar = pd.DatetimeIndex(sorted(set(dates.entry_date) | set(dates.exit_date)))
    prices = pd.DataFrame(100.0, index=calendar, columns=symbols)
    prices.loc[dates.exit_date] = 110.0
    daily_vol = pd.DataFrame(100.0, index=calendar, columns=symbols)
    minute_vol = daily_vol.copy()
    score = pd.DataFrame([range(8), range(8)], index=signals, columns=groups, dtype=float)
    return groups, dates, prices, daily_vol, minute_vol, score


def test_history_config_frozen_and_partial_march_matures():
    history.validate_config(yaml.safe_load(history.CONFIG.read_text()))
    with pytest.raises(ValueError, match="fixed definition"):
        history.validate_config({**history.EXPECTED, "horizon": 4})
    groups, dates, prices, vol, minute, score = fixture()
    legs, cohorts = history.replay_rows("factor", score, groups, dates, prices, prices,
                                        vol, minute, pd.Timestamp("2026-03-24"))
    assert len(cohorts) == 2
    assert cohorts.month_status.eq("PARTIAL_MONTH").all()
    assert cohorts.n_closed.sum() == 4
    assert np.allclose(cohorts.theoretical_gross_account_contribution, .02)
    assert np.allclose(cohorts.gross_account_contribution, .02)
    assert np.allclose(cohorts.b8_account_contribution, .02)
    result = history.summarize_period("factor", "2026_COLD", cohorts, legs, None)
    assert result["n_signal_sleeves"] == 2
    assert result["theoretical_excess_b8_hac_n"] == 2
    assert result["illustrative_10bp_net_excess_b8_hac_n"] == 2
    with pytest.raises(ValueError, match="mature"):
        history.replay_rows("factor", score, groups, dates, prices, prices,
                            vol, minute, pd.Timestamp("2026-03-23"))


def test_history_rows_match_forward_paper_mapping_for_closed_month():
    groups, dates, prices, vol, minute, score = fixture()
    hist_legs, hist = history.replay_rows("factor", score, groups, dates, prices,
                                          prices, vol, minute, pd.Timestamp("2026-04-01"))
    fwd_legs, fwd = history.paper.paper_rows(
        {"evaluation_month": "2026-03", "selected_candidates": ["factor"]},
        {"factor": score}, groups, dates, prices, prices, vol, minute,
        pd.Timestamp("2026-04-01"))
    assert hist_legs.status.tolist() == fwd_legs.status.tolist()
    for column in ("selected_groups", "gross_account_contribution",
                   "executed_one_way_turnover", "b8_account_contribution",
                   "b14_account_contribution"):
        assert hist[column].tolist() == fwd[column].tolist()


def test_incomplete_score_cash_and_unpriced_exit_keeps_theory():
    groups, dates, prices, vol, minute, score = fixture()
    score.loc[dates.index[0], "g0"] = np.nan
    minute.loc[pd.Timestamp("2026-03-24"), "s7"] = 0
    legs, cohorts = history.replay_rows("factor", score, groups, dates, prices, prices,
                                        vol, minute, pd.Timestamp("2026-03-24"))
    assert cohorts.iloc[0].signal_status == "INCOMPLETE_SELECTED_SCORE_CASH"
    assert cohorts.iloc[0].gross_account_contribution == 0
    assert cohorts.iloc[1].n_unpriced_exit == 1
    assert pd.isna(cohorts.iloc[1].gross_account_contribution)
    result = history.summarize_period("factor", "2026_COLD", cohorts, legs, None)
    assert result["status"] == "UNPRICED_PERIOD_RESULT"
    assert result["gross_account_pnl_contribution"] is None
    assert result["theoretical_adjusted_open_gross_account_contribution"] == pytest.approx(.02)
    assert result["illustrative_10bp_net_excess_b8_hac_t_lag10_report_only"] is None
    assert result["illustrative_10bp_net_excess_b8_hac_n"] == 0


def test_uncomputable_is_not_zero_return():
    result = history.summarize_period("range_flow_20_40_1", "FULL_COLD",
                                      pd.DataFrame(), pd.DataFrame(), None)
    assert result["status"] == "UNCOMPUTABLE_PRE2025_SHARE_SOURCE"
    assert result["historical_ic"] is None
    assert "gross_account_pnl_contribution" not in result
