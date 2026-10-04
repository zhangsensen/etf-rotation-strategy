"""Controller acceptance tests for the 2026-09-21 referee fixes (A6 label availability, A7 exit purge,
full-block t, identity discovery floor, plan seal rejection)."""
import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_mining_referee import topk_series, purge_by_exit, block_t, fractional_topk_weights
from etf_strategy.core.etf_identity import identity_gate
from etf_strategy.core.etf_mining_campaign import write_plan_seal, verify_plan_seal


def _panel(n_days=30, n=10, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2024-01-01", periods=n_days)
    cols = [f"E{i}" for i in range(n)]
    sig = pd.DataFrame(rng.normal(size=(n_days, n)), index=idx, columns=cols)
    fwd = pd.DataFrame(rng.normal(size=(n_days, n)) * 0.01, index=idx, columns=cols)
    elig = pd.DataFrame(True, index=idx, columns=cols)
    return sig, fwd, elig


def test_a6_missing_label_never_promotes_fourth_name():
    sig, fwd, elig = _panel()
    day = sig.index[5]
    top_name = sig.loc[day].idxmax()
    fwd.loc[day, top_name] = np.nan            # exit price missing for the D-day top name
    out = topk_series(sig, fwd, elig, direction=1.0, k=3, min_names=8)
    w = out.signal_weights.loc[day]
    assert w[top_name] == 1.0                 # still selected on D-known information
    assert np.isnan(out.excess.loc[day])      # the day is dropped, not re-ranked
    assert out.dropped_label_days == 1


def test_a7_purge_by_exit_keeps_only_signals_whose_exit_is_inside_window():
    cal = pd.bdate_range("2024-01-01", periods=40)
    s = pd.Series(1.0, index=cal)
    end = cal[29]
    kept = purge_by_exit(s.loc[:end], cal, end, offset_sessions=7)
    assert kept.index.max() == cal[29 - 7]
    assert len(kept) == 30 - 7


def test_block_t_uses_full_blocks_only():
    s = pd.Series(np.r_[np.ones(10), 100.0, 100.0], index=pd.bdate_range("2024-01-01", periods=12))
    t, n = block_t(s, 5)
    assert n == 2                             # the 2-day tail block is not counted


def test_identity_gate_requires_discovery_floor_when_given():
    table = pd.DataFrame({"discovery_ic": [0.0001, 0.02], "seen_audit_ic": [0.02, 0.02]})
    assert identity_gate(table, 1.0, 0.01) is True
    assert identity_gate(table, 1.0, 0.01, 0.01) is False


def test_a2_plan_seal_rejects_tampering(tmp_path):
    plan = tmp_path / "PLAN.json"
    plan.write_text('{"candidates": [{"id": "X"}]}')
    write_plan_seal(plan)
    assert verify_plan_seal(plan)
    plan.write_text('{"candidates": [{"id": "Y"}]}')
    assert not verify_plan_seal(plan)


def test_fractional_weights_independent_of_column_order():
    sig, fwd, elig = _panel(n=8)
    sig.iloc[:, :] = np.round(sig.to_numpy(), 0)   # force ties
    w1 = fractional_topk_weights(sig, 3, min_names=8)
    perm = list(reversed(sig.columns))
    w2 = fractional_topk_weights(sig[perm], 3, min_names=8)[sig.columns]
    assert np.allclose(w1.to_numpy(), w2.to_numpy())
    assert np.allclose(w1.sum(axis=1).to_numpy(), 3.0)


# ---- v4.2 additions (Codex P0/P1/P2 review of f02d40df) ----
from etf_strategy.core.etf_mining_referee import block_t_calendar


def test_block_t_calendar_requires_complete_sessions():
    cal = pd.bdate_range("2024-01-01", periods=20)
    s = pd.Series(1.0, index=cal)
    s.iloc[7] = np.nan                      # one missing session inside block 2
    s.iloc[[0, 5, 10, 15]] = [1.0, 2.0, 3.0, 4.0]
    t, n = block_t_calendar(s, cal, 5)
    assert n == 3                           # block 2 (sessions 5-9) is excluded, the other three kept
    t_obs, n_obs = block_t(s.dropna(), 5)   # observation-count blocks would re-pack the gap
    assert n_obs == 3 and n == 3            # same count here, but the members differ:
    assert t != t_obs                       # calendar blocks keep 2,3,4 vs packed blocks shift by one session


def test_run_end_verification_rejects_plan_changed_mid_run(tmp_path, monkeypatch):
    import importlib.util, sys
    ws = "/home/sensen/dev/projects/gpu_ml-coral/runtime_outputs/etf_pi_glm_mining_20260919/workspace"
    drv = f"{ws}/frameworks/etf_rotation/scripts/research/pi_round002_mine.py"
    if not Path(drv).exists():
        pytest.skip("pi workspace not present")
    spec = importlib.util.spec_from_file_location("eng_t", drv); eng = importlib.util.module_from_spec(spec)
    old_argv = sys.argv; sys.argv = [drv]
    try:
        spec.loader.exec_module(eng)
    finally:
        sys.argv = old_argv
    plan_path = tmp_path / "PLAN.json"
    plan_path.write_text('{"candidates": [], "engine_hashes": {}}')
    write_plan_seal(plan_path)
    sha = eng._hash(plan_path)
    plan_path.write_text('{"candidates": [{"id": "Z"}], "engine_hashes": {}}')   # tampered during the run
    with pytest.raises(ValueError):
        eng._verify_run_end(plan_path, sha, {})
    # pending caches: discard removes temp files and never touches the final path
    final = tmp_path / "atoms" / "k.parquet"; final.parent.mkdir()
    tmp = eng._pending_path(final); tmp.write_text("x")
    eng._PENDING_CACHE.append((tmp, final))
    assert eng._discard_pending_caches() == 1 and not tmp.exists() and not final.exists()
    tmp.write_text("x"); eng._PENDING_CACHE.append((tmp, final))
    assert eng._finalize_pending_caches() == 1 and final.exists() and not tmp.exists()


from pathlib import Path  # noqa: E402  (used above)


def test_v43_expression_builder_matches_current_grammar_signature():
    import ast
    from dataclasses import fields

    from etf_strategy.core.etf_factor_grammar import ExpressionSpec

    allowed_keywords = {field.name for field in fields(ExpressionSpec)}
    drivers = (
        Path(__file__).parents[1]
        / "scripts/research/pi_glm_mining/round_drivers/pi_round002_mine.py",
        Path(__file__).parents[1]
        / "scripts/research/pi_glm_mining/round_drivers/sonnet/pi_round002_mine.py",
    )
    for driver in drivers:
        tree = ast.parse(driver.read_text())
        builder = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_expression_spec"
        )
        call = next(node for node in ast.walk(builder) if isinstance(node, ast.Call))
        assert {kw.arg for kw in call.keywords} <= allowed_keywords


def test_v43_report_does_not_claim_missing_scan_or_correction_artifacts():
    drivers = (
        Path(__file__).parents[1]
        / "scripts/research/pi_glm_mining/round_drivers/pi_round002_mine.py",
        Path(__file__).parents[1]
        / "scripts/research/pi_glm_mining/round_drivers/sonnet/pi_round002_mine.py",
    )
    for driver in drivers:
        source = driver.read_text()
        assert "静态扫描见 future_leak_scan_" not in source
        assert "残差诊断已删除（见 correction.json）" not in source


def test_newey_west_t_calendar_equals_plain_when_no_gaps_and_differs_with_gaps():
    from etf_strategy.core.etf_mining_referee import newey_west_t, newey_west_t_calendar
    rng = np.random.default_rng(3); cal = pd.bdate_range("2024-01-01", periods=300)
    s = pd.Series(rng.normal(size=300) + 0.05, index=cal)
    assert abs(newey_west_t(s, 4) - newey_west_t_calendar(s, cal, 4)) < 1e-9
    g = s.copy(); g.iloc[::7] = np.nan            # gaps: plain HAC packs observations, calendar HAC keeps session distance
    assert np.isfinite(newey_west_t_calendar(g, cal, 4))
    assert newey_west_t(g.dropna(), 4) != newey_west_t_calendar(g, cal, 4)


def test_newey_west_t_calendar_gap_formula_is_cross_sum_over_count():
    """With gaps, gamma_j must equal sum_{available pairs} d_t d_{t-j} / count (Codex round-4)."""
    from etf_strategy.core.etf_mining_referee import newey_west_t_calendar
    cal = pd.bdate_range("2024-01-01", periods=60)
    rng = np.random.default_rng(11); x = pd.Series(rng.normal(size=60) + 0.2, index=cal); x.iloc[[3, 17, 30, 44]] = np.nan
    lag = 4
    v = x.to_numpy(); present = np.isfinite(v); count = present.sum(); mean = v[present].mean(); d = np.where(present, v - mean, 0.0)
    lrv = (d[present] @ d[present]) / count
    for j in range(1, lag + 1):
        both = present[j:] & present[:-j]
        lrv += 2.0 * (1 - j / (lag + 1.0)) * ((d[j:][both] @ d[:-j][both]) / count)
    expected = mean / np.sqrt(lrv / count)
    assert abs(newey_west_t_calendar(x, cal, lag) - expected) < 1e-12
