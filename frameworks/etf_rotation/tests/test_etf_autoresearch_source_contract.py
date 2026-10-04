"""Current candidate interface: causal shape, I/O restrictions and frozen sign."""
from __future__ import annotations

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
