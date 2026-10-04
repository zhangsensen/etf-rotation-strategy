import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/research/audit_ic_lead_redundancy.py'
SPEC = importlib.util.spec_from_file_location('lead_redundancy', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_external_repo_relative_and_main_run_paths():
    relative = 'runtime_outputs/etf_rotation_research/external8'
    assert MODULE.resolve_run(relative) == MODULE.ROOT / relative
    assert MODULE.resolve_run('main_run') == MODULE.ROOT / 'runtime_outputs/etf_rotation_research/runs/main_run'


def test_absolute_correlation_is_averaged_before_sign_cancellation():
    dates = pd.date_range('2026-01-01', periods=4)
    a = pd.DataFrame(np.tile(np.arange(8), (4, 1)), index=dates)
    b = a.mul([1, -1, 1, -1], axis=0)
    result = MODULE.compare_scores(a, b)
    np.testing.assert_allclose(result['mean_abs_daily_rank_corr'], 1, atol=1e-14)
    np.testing.assert_allclose(result['mean_signed_daily_rank_corr'], 0, atol=1e-14)
    assert result['redundancy_annotation']


def test_only_common_complete_nonconstant_dates_enter_comparison():
    dates = pd.date_range('2026-01-01', periods=4)
    a = pd.DataFrame(np.tile(np.arange(8, dtype=float), (4, 1)), index=dates)
    b = a.iloc[1:].copy()
    b.iloc[1, 0] = np.nan
    b.iloc[2] = 1
    result = MODULE.compare_scores(a, b)
    assert result['common_rankable_days'] == 1
    assert result['first_signal'] == result['last_signal'] == '2026-01-02'
