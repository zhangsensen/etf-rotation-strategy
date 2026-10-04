"""Synthetic tests: economic failure cannot erase IC evidence."""
import importlib.util
from pathlib import Path
import pandas as pd

path = Path(__file__).resolve().parents[1] / 'scripts/research/report_group_ic_evidence.py'
spec = importlib.util.spec_from_file_location('ic_report', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_ic_and_reverse_are_separate_from_economics():
    data = pd.DataFrame(dict(n=[400, 400, 226], ranking_supported=[True, False, False],
                             budget_diagnostic_pass=[False]*3, economic_metrics_pass=[False, True, True],
                             ic_mean=[.05, -.08, .05], ic_hac_t=[2.2, -2.5, 2.5],
                             ic_block_t=[2.2, -2.5, 2.5]))
    result = module.classify(data)
    assert result.ic_evidence_status.tolist() == ['IC_LEAD_ONLY', 'REVERSE_WATCH_NOT_VALIDATED', 'INSUFFICIENT_COVERAGE']
    assert result.economic_supported.tolist() == [False, True, False]
    assert not result.ic_budget_supported.any()
    pd.testing.assert_series_equal(result.ic_mean, data.ic_mean)
