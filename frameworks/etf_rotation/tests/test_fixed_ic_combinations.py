import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/research/study_fixed_ic_combinations.py'
SPEC = importlib.util.spec_from_file_location('fixed_combinations', SCRIPT)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_selector_excludes_unmatured_and_future_labels():
    dates = pd.bdate_range('2025-01-01', periods=160)
    start = dates[140]
    timing = pd.DataFrame({'exit_date': pd.Series(dates, index=dates).shift(-7)}, index=dates)
    ic = pd.DataFrame({'a': .1, 'b': .05, 'unseasoned': np.nan}, index=dates)
    ic.loc[dates[-20:], 'unseasoned'] = 1
    ordered, train = M.choose(ic, timing, start)
    changed = ic.copy()
    changed.loc[timing.exit_date.ge(start) | (dates >= start), 'b'] = 100
    new_order, new_train = M.choose(changed, timing, start)
    assert ordered == new_order == ['a', 'b']
    pd.testing.assert_frame_equal(train, new_train)
    assert timing.reindex(train.index).exit_date.max() < start


def test_ic_keeps_relative_precision_ties_and_complete_group_requirement():
    dates = pd.date_range('2025-01-01', periods=2)
    score = pd.DataFrame(np.tile(np.arange(8)*1e-11, (2, 1)), index=dates, columns=M.GROUPS)
    labels = score * 1e9
    labels.iloc[1, 0] = np.nan
    ic = M.rank_ic(score, labels)
    np.testing.assert_allclose(ic.iloc[0], 1)
    assert pd.isna(ic.iloc[1])


def test_prefix_loader_does_not_parse_cold_value_rows(tmp_path):
    path = tmp_path / 'scores.csv'
    path.write_text('signal_date,g\n2026-03-13,1\n2026-03-25,SECRET_COLD_VALUE\n')
    result = M.read_prefix(path, pd.Timestamp('2026-03-24'))
    assert result.g.tolist() == [1]


def test_null_preserves_dates_and_each_day_return_values():
    labels = pd.DataFrame(np.arange(240).reshape(30, 8), index=pd.bdate_range('2025-01-01', periods=30))
    shuffled = M.null_labels(labels, 9)
    pd.testing.assert_index_equal(labels.index, shuffled.index)
    np.testing.assert_array_equal(np.sort(labels.to_numpy(), axis=1), np.sort(shuffled.to_numpy(), axis=1))
