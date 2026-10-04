"""Synthetic configuration contracts; no raw market data or mining runs."""
import pytest
from etf_strategy.core.etf_group_run_rules import (
    FIXED_FIELDS, FIXED_SCREENS, validate_ic_discovery_config,
)


def config():
    return {**FIXED_FIELDS, 'start': '2023-07-27', 'screens': dict(FIXED_SCREENS)}


def test_explicit_window_distinct_from_history_start():
    validate_ic_discovery_config(config())
    legacy = config()
    del legacy['evaluation_start']
    with pytest.raises(ValueError, match='evaluation_start'):
        validate_ic_discovery_config(legacy)


def test_earlier_cutoff_preserves_cold_guard():
    from etf_strategy.core.etf_group_run_rules import enforce_cold_holdout
    import pandas as pd
    cfg = {**config(), 'as_of': '2026-03-24'}
    validate_ic_discovery_config(cfg)
    cal = pd.bdate_range('2025-01-01', '2026-09-23')
    assert enforce_cold_holdout(cfg, cal, None) == 'COLD_OK'
    cfg['as_of'] = '2026-09-17'
    validate_ic_discovery_config(cfg)
    with pytest.raises(ValueError, match='cold holdout'):
        enforce_cold_holdout(cfg, cal, None)


@pytest.mark.parametrize('value', [None, False, 20260324, '2026-02-30', '2024-12-31', '2026-03-24T00:00:00'])
def test_invalid_earlier_cutoff_rejected(value):
    with pytest.raises(ValueError, match='as_of'):
        validate_ic_discovery_config({**config(), 'as_of': value})


@pytest.mark.parametrize('key,value', [
    ('evaluation_start', '2023-07-27'), ('as_of', '2026-09-21'),
    ('entry_lag', 0), ('horizon', 20), ('top_k', 3), ('hac_lag', 5),
    ('purpose', 'certification'),
])
def test_scope_changes_fail_closed(key, value):
    cfg = config()
    cfg[key] = value
    with pytest.raises(ValueError, match=key):
        validate_ic_discovery_config(cfg)


def test_2025_direction_discovery_has_narrow_as_of_exception():
    cfg = config()
    cfg['discovery_surface'] = '2025_DIRECTION_DISCOVERY_ONLY'
    cfg['as_of'] = '2025-12-31'
    validate_ic_discovery_config(cfg)
    cfg['as_of'] = '2025-12-30'
    with pytest.raises(ValueError, match='as_of'):
        validate_ic_discovery_config(cfg)


@pytest.mark.parametrize('key,value', [
    ('min_days', 226), ('min_ic_hac_t', 1.5), ('min_ic', 0),
    ('min_ic_block_t', float('nan')), ('min_year_days', None),
    ('max_abs_rank_corr', 1), ('alpha', .1),
])
def test_no_silent_gate_relaxation(key, value):
    cfg = config()
    cfg['screens'][key] = value
    with pytest.raises(ValueError, match=key):
        validate_ic_discovery_config(cfg)


def test_interaction_threshold_is_explicit():
    cfg = config()
    cfg['source_type'] = 'interaction'
    with pytest.raises(ValueError, match='paired_min_hac_t'):
        validate_ic_discovery_config(cfg)
    cfg['paired_min_hac_t'] = 2.0
    validate_ic_discovery_config(cfg)


def _calendar(n=400):
    import pandas as pd
    return pd.bdate_range('2025-01-01', periods=n)


def test_cold_holdout_blocks_recent_as_of():
    from etf_strategy.core.etf_group_run_rules import enforce_cold_holdout, COLD_HOLDOUT_SESSIONS
    cal = _calendar()
    cfg = {**config(), 'as_of': str(cal[-1].date())}
    with pytest.raises(ValueError, match='cold holdout'):
        enforce_cold_holdout(cfg, cal, None)
    cfg['as_of'] = str(cal[-1 - COLD_HOLDOUT_SESSIONS].date())
    assert enforce_cold_holdout(cfg, cal, None) == 'COLD_OK'
    cfg['as_of'] = str(cal[-COLD_HOLDOUT_SESSIONS].date())
    with pytest.raises(ValueError):
        enforce_cold_holdout(cfg, cal, None)


def test_cold_holdout_exemptions_are_explicit():
    from etf_strategy.core.etf_group_run_rules import enforce_cold_holdout
    cal = _calendar()
    cfg = {**config(), 'as_of': str(cal[-1].date())}
    assert enforce_cold_holdout({**cfg, 'rejudge_of': 'old_run'}, cal, None) == 'REJUDGE_EXEMPT'
    with pytest.raises(ValueError):
        enforce_cold_holdout(cfg, cal, {'holdout_release': {'registered_candidates': []}})
    ok = {'holdout_release': {'registered_candidates': ['a_20'], 'user_request': 'open holdout'}}
    assert enforce_cold_holdout(cfg, cal, ok) == 'HOLDOUT_RELEASE'
