"""Synthetic regression tests for the window-only frozen-score replay."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

PATH = Path(__file__).resolve().parents[1] / 'scripts/research/rejudge_etf_groups_2025.py'
spec = importlib.util.spec_from_file_location('rejudge2025', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_window_keeps_calendar_and_purges_exit():
    dates = pd.to_datetime(['2024-12-31', '2025-01-02', '2025-12-30'])
    frame = pd.DataFrame({'exit_date': pd.to_datetime(['2025-01-09', '2025-01-13', '2026-01-09']),
                          'ic': [1., 2., 3.], 'excess8': [1., 2., 3.]}, index=dates)
    result = module.window(frame, '2025-01-01', '2025-12-31')
    assert len(result) == 2
    assert result.ic.iloc[0] == 2
    assert np.isnan(result.ic.iloc[1])


def test_budget_is_separate_and_b14_is_not_gate():
    row = dict(n=400, ic_mean=.03, ic_hac_t=2.1, ic_block_t=2.2,
               all_eligible_years_positive=True, positive_years=2, min_leave_group_ic=.01,
               excess8_mean=.001, excess8_hac_t=2.1, excess14_hac_t=-10,
               ic_p_normal_one_sided=.02)
    screens = dict(min_days=360, min_ic=.01, min_ic_hac_t=2, min_ic_block_t=2,
                   min_positive_years=2, min_excess8_hac_t=2, alpha=.05)
    result = module.layers(row, screens, 96)
    assert result['ranking_supported'] and result['economic_metrics_pass']
    assert not result['budget_diagnostic_pass']
    row['n'] = 359
    result = module.layers(row, screens, 96)
    assert result['ranking_metrics_pass'] and not result['ranking_supported']
    assert result['coverage_status'] == 'INSUFFICIENT'


def test_parent_comparison_preserves_candidate_coverage():
    dates = pd.date_range('2025-01-02', periods=3)
    scores = pd.DataFrame([[1, 2, 3, 4]] * 3, index=dates)
    labels = scores / 100
    reference = pd.DataFrame({'ic': [1., np.nan, 1.]}, index=dates)
    result = module.score_metrics(scores, labels, reference, 2)
    assert result.ic.notna().tolist() == [True, False, True]
    np.testing.assert_allclose(result.excess8.dropna(), .01)
