import numpy as np
import pandas as pd
from etf_strategy.core.etf_group_preflight import inspect_feature_coverage


def test_missing_fixed_member_and_tied_scores_are_not_rankable():
    dates = pd.date_range('2025-01-01', periods=25)
    groups = {f'g{i}': {'members': [f'e{i}']} for i in range(8)}
    groups['g0']['members'].append('extra')
    cols = [f'e{i}' for i in range(8)] + ['extra']
    valid = pd.DataFrame(np.tile(np.arange(9), (25, 1)), index=dates, columns=cols)
    broken = valid.copy()
    broken['extra'] = np.nan
    tied = valid * 0 + 1
    sparse = valid.copy()
    sparse.iloc[1:] = np.nan
    cfg = dict(entry_lag=2, horizon=5, evaluation_start='2025-01-01', as_of='2025-01-25')
    out = inspect_feature_coverage(dict(valid=valid, broken=broken, tied=tied, sparse=sparse), groups, cfg)
    assert out['valid']['rankable_8group_dates'] == 18
    assert not out['broken']['structurally_eligible']
    assert out['broken']['complete_8group_dates'] == 0
    assert out['tied']['complete_8group_dates'] == 18
    assert not out['tied']['structurally_eligible']
    assert out['sparse']['structurally_eligible']  # No hidden sample-size gate.
    assert all(not value['labels_read'] for value in out.values())
    assert not inspect_feature_coverage({'valid': valid}, groups, cfg,
        pd.Series(False, index=dates))['valid']['structurally_eligible']
