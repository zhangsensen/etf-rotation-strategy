"""The outer loop keeps only an IC improvement and records every attempt."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/research"))
import run_etf_autoresearch_campaign as campaign


def source(name: str, window: int) -> str:
    return ("import pandas as pd\n"
            f'CANDIDATE_ID = "autoresearch_{name}"\n'
            'FAMILY = "price_trend"\nDIRECTION = 1\nDESCRIPTION = "test"\n'
            'def score(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:\n'
            f'    return panels["close"].pct_change({window}, fill_method=None)\n')


def write_result(path: Path, code: str, ic: float) -> None:
    path.mkdir(parents=True)
    shared = {"evaluator_sha256": "fixed", "implementation_sha256": {"core": "fixed"},
              "python_version": "3", "pandas_version": "2", "numpy_version": "2",
              "input_sha256": {}, "groups_sha256": "g", "universe_sha256": "u"}
    (path / "result.json").write_text(json.dumps({**shared, "candidate_sha256": sha256(code.encode()).hexdigest(),
                                                   "candidate": "autoresearch_test", "family": "price_trend",
                                                   "ic": ic, "hac_t": 2.0, "n": 3}))
    pd.DataFrame({"signal_date": ["2025-01-01", "2025-01-02", "2025-01-03"],
                  "ic": [ic] * 3}).to_csv(path / "daily_ic.csv", index=False)


def test_two_rounds_keep_then_revert(tmp_path, monkeypatch) -> None:
    seed = source("seed", 20)
    candidate = tmp_path / "candidate.py"
    candidate.write_text(seed)
    monkeypatch.setattr(campaign, "CANDIDATE", candidate)
    baseline = tmp_path / "baseline"
    write_result(baseline, seed, 0.02)
    proposals = iter([source("better", 15), source("worse", 30)])

    def propose(_context, _round_dir, _model):
        return {"rationale": "test a different window", "source_code": next(proposals)}

    def evaluate(run_id, output_root, *_args):
        code = candidate.read_text()
        ic = 0.04 if "better" in code else 0.01
        write_result(output_root / run_id, code, ic)
        return {"decision": "positive_ic_review"}

    result = campaign.run_campaign("testloop", 2, baseline, tmp_path / "inventory.csv",
                                   tmp_path / "runs", tmp_path / "out", None,
                                   propose=propose, evaluate=evaluate)
    assert [row["keep"] for row in result["rounds"]] == [True, False]
    assert result["champion_run"] == "testloop_r01"
    assert candidate.read_text() == source("better", 15)
    assert (tmp_path / "out/campaigns/testloop/r02/candidate.py").exists()
    assert json.loads((tmp_path / "out/campaigns/testloop/summary.json").read_text())["formal_registration"] is False


def test_failed_proposal_restores_seed_and_stops_after_two(tmp_path, monkeypatch) -> None:
    seed = source("seed", 20)
    candidate = tmp_path / "candidate.py"
    candidate.write_text(seed)
    monkeypatch.setattr(campaign, "CANDIDATE", candidate)
    baseline = tmp_path / "baseline"
    write_result(baseline, seed, 0.02)

    def propose(_context, _round_dir, _model):
        return {"rationale": "invalid", "source_code": source("bad", 5) + '\nopen("secret")\n'}

    result = campaign.run_campaign("failure", 5, baseline, tmp_path / "inventory.csv",
                                   tmp_path / "runs", tmp_path / "out", None, propose=propose)
    assert len(result["rounds"]) == 2
    assert result["stop_reason"] == "two consecutive failed rounds"
    assert candidate.read_text() == seed
    assert all(row["status"] == "FAILED" for row in result["rounds"])


def test_start_requires_exact_baseline_source(tmp_path, monkeypatch) -> None:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(source("other", 15))
    monkeypatch.setattr(campaign, "CANDIDATE", candidate)
    baseline = tmp_path / "baseline"
    write_result(baseline, source("seed", 20), 0.02)
    with pytest.raises(ValueError, match="does not match baseline"):
        campaign.run_campaign("mismatch", 1, baseline, tmp_path / "inventory.csv",
                              tmp_path / "runs", tmp_path / "out", None)


def test_numeric_datetime_conversion_is_not_io():
    code = source('dates', 20).replace(
        '    return panels["close"].pct_change(20, fill_method=None)',
        '    dates = pd.to_datetime(panels["close"].index)\n    return panels["close"].pct_change(20, fill_method=None)')
    assert campaign.validate_source(code)['CANDIDATE_ID'] == 'autoresearch_dates'
    unsafe = code.replace('dates = pd.to_datetime(panels["close"].index)',
                          'panels["close"].to_pickle("forbidden.pkl")')
    with pytest.raises(ValueError, match='I/O'):
        campaign.validate_source(unsafe)


@pytest.mark.parametrize('body, syntax', [
    ('raise TypeError("bad panel")', 'Raise'),
    ('return panels["close"].rolling(20).apply(lambda x: x.mean())', 'Lambda'),
])
def test_declared_unsupported_syntax_stays_blocked(body, syntax):
    code = source('invalid_interface', 20).replace(
        'return panels["close"].pct_change(20, fill_method=None)', body)
    assert syntax in campaign.SCORE_CONTRACT['unsupported_syntax']
    with pytest.raises(ValueError, match=syntax):
        campaign.validate_source(code)


def test_negative_hypothesis_raw_score_contract_matches_evaluator(tmp_path):
    from run_etf_autoresearch_ic import load_candidate, causal_scores
    code = source('negative_raw', 1).replace('DIRECTION = 1', 'DIRECTION = -1')
    snapshot = tmp_path / 'candidate.py'
    snapshot.write_text(code)
    campaign.validate_source(code)
    close = pd.DataFrame({'A': [10., 11., 12.], 'B': [20., 18., 17.]},
                         index=pd.date_range('2024-01-01', periods=3))
    got = causal_scores(load_candidate(snapshot), {'close': close}, close.index[1])
    pd.testing.assert_frame_equal(got, -close.pct_change(fill_method=None))
