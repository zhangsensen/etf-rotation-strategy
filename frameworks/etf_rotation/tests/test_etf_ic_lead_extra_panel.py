"""Synthetic checks for the observation-only eleven-lead panel."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/build_etf_ic_lead_extra_panel.py"
spec = importlib.util.spec_from_file_location("build_etf_ic_lead_extra_panel", SCRIPT)
extra = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extra)


def test_catalog_is_exact_missing_set_and_frozen_directions():
    from etf_strategy.core.etf_ic_monthly_factory import load_contract

    v4, _ = load_contract(extra.V4)
    assert len(extra.SOURCES) == 11
    assert not set(extra.SOURCES).intersection(v4["candidate_catalog"])
    assert {name for name, (_kind, _run, sign) in extra.SOURCES.items() if sign < 0} == {
        "beta_asymmetry_60", "peer_corr_network_change_60", "OVERHEAD_TURNOVER_20"
    }
    for candidate in extra.SOURCES:
        extra._definition(candidate)


def test_breadth_single_member_and_missing_member_are_causal():
    dates = pd.bdate_range("2026-01-02", periods=8)
    close = pd.DataFrame({"one": [100, 101, 102, 103, 104, 105, 106, 107],
                          "two": [100, 99, 98, 97, np.nan, 96, 97, 98]}, index=dates)
    groups = {"solo": {"members": ["one"]}, "pair": {"members": ["one", "two"]}}
    score = extra._breadth_score(close, groups)
    assert score.loc[dates[5], "solo"] == 1.0
    assert pd.isna(score.loc[dates[5], "pair"])
    changed = close.copy()
    changed.loc[dates[-1], "one"] = 99999
    pd.testing.assert_frame_equal(score.loc[:dates[-2]], extra._breadth_score(changed, groups).loc[:dates[-2]])


def test_ic_requires_complete_eight_groups_and_matured_exit():
    dates = pd.bdate_range("2026-10-05", periods=10)
    groups = {f"g{i}": {"members": [f"s{i}"]} for i in range(8)}
    scores = pd.DataFrame(np.tile(np.arange(8), (10, 1)), index=dates, columns=list(groups))
    returns = scores.rename(columns={f"g{i}": f"s{i}" for i in range(8)}) / 100
    labels = pd.DataFrame({"entry_date": dates + pd.offsets.BDay(2),
                           "exit_date": dates + pd.offsets.BDay(7)}, index=dates)
    known = pd.Series(True, index=dates)
    as_of = dates[7]
    ic = extra._matured_ic(scores, returns, groups, known, labels, as_of)
    assert ic.loc[dates[0]] == pytest.approx(1.0)
    assert ic.iloc[1:].isna().all()
    scores.loc[dates[0], "g0"] = np.nan
    assert pd.isna(extra._matured_ic(scores, returns, groups, known, labels, as_of).iloc[0])


def test_saved_score_comparison_fails_on_unrevised_mismatch(monkeypatch):
    dates = pd.bdate_range("2025-01-02", periods=3)
    saved = pd.DataFrame({"g": [1.0, 2.0, 3.0]}, index=dates)
    monkeypatch.setattr(extra, "_saved_score", lambda candidate: saved)
    monkeypatch.setattr(extra, "_source_revised", lambda candidate: False)
    candidate = "breadth_5"
    assert extra._repro_check(candidate, saved.copy())["status"] == "MATCH"
    changed = saved.copy()
    changed.iloc[1, 0] = 2.5
    with pytest.raises(ValueError, match="unrevised source score mismatch"):
        extra._repro_check(candidate, changed)


def test_extra_panel_is_idempotent_and_rejects_changed_daily_ic(tmp_path):
    idx = pd.bdate_range("2026-10-01", periods=2)
    ic = pd.DataFrame({"a": [0.1, np.nan]}, index=idx)
    result = {"as_of": "2026-10-02", "version": "test_v1", "v4_contract_sha256": "x",
              "daily_ic": ic, "label_dates": pd.DataFrame({"entry_date": idx}, index=idx),
              "scores": {"a": pd.DataFrame({"g": [1.0, 2.0]}, index=idx)},
              "coverage": [], "reproducibility": []}
    saved = extra.persist_extra(result, tmp_path)
    assert extra.persist_extra(result, tmp_path) == saved
    changed = {**result, "daily_ic": ic + 0.1}
    with pytest.raises(AssertionError):
        extra.persist_extra(changed, tmp_path)
