"""Synthetic paper-sleeve tests; no historical ETF labels or orders."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/run_etf_personal_paper_v1.py"
spec = importlib.util.spec_from_file_location("run_etf_personal_paper_v1", SCRIPT)
paper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paper)


def _fixture():
    groups = {f"g{i}": {"members": ([f"s{i}a", f"s{i}b"] if i < 6 else [f"s{i}"])}
              for i in range(8)}
    symbols = [s for g in groups.values() for s in g["members"]]
    signals = pd.DatetimeIndex(["2026-10-05", "2026-10-06"])
    entry = pd.DatetimeIndex(["2026-10-07", "2026-10-08"])
    exit_ = pd.DatetimeIndex(["2026-10-14", "2026-10-15"])
    calendar = entry.append(exit_)
    dates = pd.DataFrame({"entry_date": entry, "exit_date": exit_}, index=signals)
    adjusted = pd.DataFrame(100.0, index=calendar, columns=symbols)
    adjusted.loc[exit_] = 110.0
    raw_open = adjusted.copy()
    daily_volume = pd.DataFrame(1000.0, index=calendar, columns=symbols)
    first_volume = pd.DataFrame(100.0, index=calendar, columns=symbols)
    score = pd.DataFrame([range(8), range(8)], index=signals, columns=groups, dtype=float)
    scores = {"a": score.copy(), "b": score.copy()}
    frozen = {"evaluation_month": "2026-10", "selected_candidates": ["a", "b"]}
    return groups, dates, adjusted, raw_open, daily_volume, first_volume, scores, frozen


def test_frozen_config_and_freeze_identity():
    cfg = yaml.safe_load(paper.CONFIG.read_text())
    contract, digest = paper.load_contract(paper.ROOT / cfg["parent_contract"])
    paper.validate_paper_config(cfg, contract)
    with pytest.raises(ValueError, match="fixed definition changed"):
        paper.validate_paper_config({**cfg, "group_tie_break": "largest_symbol_first"}, contract)
    frozen = {"process_version": contract["process_version"], "contract_sha256": digest,
              "freeze_month": "2026-09", "evaluation_month": "2026-10",
              "train_end": "2026-09-30", "selected_candidates": ["a"],
              "candidate_catalog_sha256": paper._canonical_digest(contract["candidate_catalog"])}
    frozen["selected_candidates"] = contract["candidate_catalog"][:2]
    assert paper.validate_freeze(frozen, contract, digest) == "2026-10"
    with pytest.raises(ValueError, match="another v4 contract"):
        paper.validate_freeze({**frozen, "contract_sha256": "other"}, contract, digest)
    with pytest.raises(ValueError, match="month relationship"):
        paper.validate_freeze({**frozen, "evaluation_month": "2026-09"}, contract, digest)


def test_selected_score_incomplete_means_cash_not_one_factor_fallback():
    groups, dates, adjusted, raw_open, daily_volume, first_volume, scores, frozen = _fixture()
    signals = dates.index
    assert paper.rank_basket(scores, ["a", "b"], signals[0], groups) == ["g7", "g6"]
    scores["b"].loc[signals[0], "g0"] = np.nan
    assert paper.rank_basket(scores, ["a", "b"], signals[0], groups) == []
    legs, cohorts = paper.paper_rows(frozen, scores, groups, dates, adjusted, raw_open,
                                     daily_volume, first_volume, pd.Timestamp("2026-11-20"))
    assert cohorts.iloc[0].signal_status == "INCOMPLETE_SELECTED_SCORE_CASH"
    assert cohorts.iloc[0].n_closed == 0
    assert cohorts.iloc[0].gross_account_contribution == 0
    assert len(legs) == 2  # only the second signal produces two one-member group legs


def test_matured_h5_sleeve_turnover_gross_cost_and_benchmarks():
    groups, dates, adjusted, raw_open, daily_volume, first_volume, scores, frozen = _fixture()
    assert len([s for g in groups.values() for s in g["members"]]) == 14
    with pytest.raises(ValueError, match="fully closed"):
        paper.paper_rows(frozen, scores, groups, dates, adjusted, raw_open,
                         daily_volume, first_volume, pd.Timestamp("2026-10-31"))
    late_dates = dates.copy()
    late_dates.loc[late_dates.index[-1], "exit_date"] = pd.Timestamp("2026-11-10")
    with pytest.raises(ValueError, match="not all matured"):
        paper.paper_rows(frozen, scores, groups, late_dates, adjusted, raw_open,
                         daily_volume, first_volume, pd.Timestamp("2026-11-02"))
    legs, cohorts = paper.paper_rows(frozen, scores, groups, dates, adjusted, raw_open,
                                     daily_volume, first_volume, pd.Timestamp("2026-11-20"))
    assert len(legs) == 4
    assert set(legs.status) == {"CLOSED"}
    assert np.allclose(cohorts.gross_account_contribution, 0.02)
    assert np.allclose(cohorts.executed_one_way_turnover, 0.4)
    assert np.allclose(cohorts.illustrative_net_account_contribution, 0.0196)
    assert np.allclose(cohorts.b8_account_contribution, 0.02)
    assert np.allclose(cohorts.b14_account_contribution, 0.02)
    summary = paper.summarize(cohorts, legs)
    assert summary["gross_account_pnl_contribution"] == pytest.approx(0.04)
    assert summary["illustrative_10bp_net_account_pnl_contribution"] == pytest.approx(0.0392)
    assert summary["executed_one_way_turnover_account"] == pytest.approx(0.8)
    assert summary["break_even_cost_bps_per_side_vs_b8"] == pytest.approx(0)


def test_missed_open_is_cash_and_unpriced_exit_blocks_monthly_pnl():
    groups, dates, adjusted, raw_open, daily_volume, first_volume, scores, frozen = _fixture()
    first_volume.loc[pd.Timestamp("2026-10-07"), "s6"] = 0
    first_volume.loc[pd.Timestamp("2026-10-15"), "s7"] = 0
    legs, cohorts = paper.paper_rows(frozen, scores, groups, dates, adjusted, raw_open,
                                     daily_volume, first_volume, pd.Timestamp("2026-11-20"))
    assert set(legs.status) == {"CLOSED", "MISSED_ENTRY", "UNPRICED_EXIT"}
    assert cohorts.n_missed_entry.sum() == 1
    assert cohorts.n_unpriced_exit.sum() == 1
    assert pd.isna(cohorts.iloc[1].gross_account_contribution)
    summary = paper.summarize(cohorts, legs)
    assert summary["status"] == "UNPRICED_MONTHLY_RESULT"
    assert summary["gross_account_pnl_contribution"] is None
    assert summary["illustrative_10bp_net_account_pnl_contribution"] is None


def test_zero_frozen_selection_stays_cash_with_benchmarks_visible():
    groups, dates, adjusted, raw_open, daily_volume, first_volume, scores, frozen = _fixture()
    frozen["selected_candidates"] = []
    legs, cohorts = paper.paper_rows(frozen, scores, groups, dates, adjusted, raw_open,
                                     daily_volume, first_volume, pd.Timestamp("2026-11-20"))
    assert legs.empty
    assert cohorts.signal_status.eq("NO_SELECTED_FACTORS_CASH").all()
    result = paper.summarize(cohorts, legs)
    assert result["gross_account_pnl_contribution"] == 0
    assert result["executed_one_way_turnover_account"] == 0
    assert result["b8_gross_account_pnl_contribution"] == pytest.approx(0.04)


def test_opening_volume_requires_unique_0931_bar():
    minute = pd.DataFrame({"datetime": ["2026-10-07 09:31", "2026-10-07 09:32"],
                           "volume": [0.0, 100.0]})
    assert paper.opening_volume(minute).loc[pd.Timestamp("2026-10-07")] == 0
    with pytest.raises(ValueError, match="invalid first-minute"):
        paper.opening_volume(pd.concat([minute, minute.iloc[[0]]], ignore_index=True))
