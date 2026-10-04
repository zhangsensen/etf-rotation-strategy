"""No live auth, market data or real ledger: synthetic bound-batch review tests."""
from copy import deepcopy
import pytest
from etf_strategy.core.etf_group_run_rules import candidate_ids, validate_batch_approval


def inputs():
    cfg = {'windows': [5, 20], 'mechanisms': {'synthetic': {'direction': 1}},
           'external_registered_definitions': 8, 'budget_cap': 106}
    approval = {'reviewer': 'master', 'scope': 'fixed14_eight_groups',
                'stage': 'IC_DISCOVERY_ONLY', 'run_id': 'test', 'config_sha256': 'digest',
                'user_request': 'synthetic request', 'prior_registered': 104,
                'max_new_definitions': 2, 'candidate_ids': ['synthetic_5', 'synthetic_20'],
                'budget_cap': 106}
    return cfg, approval


def test_exact_batch_review():
    cfg, approval = inputs()
    assert validate_batch_approval(cfg, 'digest', 'test', approval) == approval['candidate_ids']


@pytest.mark.parametrize('key,value', [('run_id', 'other'), ('config_sha256', 'changed'),
    ('max_new_definitions', 8), ('prior_registered', 96), ('budget_cap', 999),
    ('candidate_ids', ['other']), ('user_request', ''), ('scope', 'stocks')])
def test_cannot_reuse_or_expand_review(key, value):
    cfg, approval = inputs()
    approval[key] = value
    with pytest.raises(ValueError):
        validate_batch_approval(cfg, 'digest', 'test', approval)


def test_missing_approval_and_dropped_external_search():
    cfg, approval = inputs()
    with pytest.raises(ValueError):
        validate_batch_approval(cfg, 'digest', 'test', None)
    changed = deepcopy(cfg)
    changed['external_registered_definitions'] = 0
    with pytest.raises(ValueError):
        validate_batch_approval(changed, 'digest', 'test', approval)


def test_new_round_carries_prior_completed_batches():
    cfg, approval = inputs()
    cfg.update(source_type='daily_rounds', prior_registered=106, budget_cap=108)
    approval.update(prior_registered=106, budget_cap=108)
    assert validate_batch_approval(cfg, 'digest', 'test', approval) == approval['candidate_ids']
    cfg['prior_registered'] = 104
    approval.update(prior_registered=104, budget_cap=106)
    cfg['budget_cap'] = 106
    with pytest.raises(ValueError, match='completed batch2'):
        validate_batch_approval(cfg, 'digest', 'test', approval)


def test_cross_source_campaign_extension_carries_current_ledger():
    cfg, approval = inputs()
    cfg.update(source_type='minute', campaign_extension=True,
               prior_registered=110, budget_cap=112)
    approval.update(prior_registered=110, budget_cap=112)
    assert validate_batch_approval(cfg, 'digest', 'test', approval) == approval['candidate_ids']
    cfg['prior_registered'] = 108
    approval.update(prior_registered=108, budget_cap=110)
    cfg['budget_cap'] = 110
    with pytest.raises(ValueError, match='all completed registrations'):
        validate_batch_approval(cfg, 'digest', 'test', approval)


def test_outcome_candidate_ids_are_exact_not_double_suffixed():
    cfg = {'source_type':'daily_outcome', 'windows':[20],
           'mechanisms':{'VAR_RATIO_5_60':{'direction':1},
                         'RETURN_AUTOCOV_20':{'direction':1}}}
    assert candidate_ids(cfg) == ['VAR_RATIO_5_60', 'RETURN_AUTOCOV_20']


def test_rejudge_reuses_candidates_without_new_budget():
    cfg, approval = inputs()
    cfg.update(source_type='daily_outcome', campaign_extension=True,
               prior_registered=133, budget_cap=133,
               rejudge_of='failed_parent')
    approval.update(prior_registered=133, budget_cap=133,
                    max_new_definitions=0, rejudge_of='failed_parent',
                    candidate_ids=candidate_ids(cfg))
    assert validate_batch_approval(cfg, 'digest', 'test', approval) == approval['candidate_ids']
    approval['budget_cap'] = 135
    with pytest.raises(ValueError, match='budget mismatch'):
        validate_batch_approval(cfg, 'digest', 'test', approval)


def test_direction_discovery_allows_frozen_library_up_to_sixteen():
    cfg, approval = inputs()
    cfg.update(
        windows=[20],
        mechanisms={f'raw_{i}': {'direction': 1} for i in range(16)},
        source_type='daily_rounds', campaign_extension=True,
        discovery_surface='2025_DIRECTION_DISCOVERY_ONLY',
        prior_registered=158, budget_cap=174,
    )
    approval.update(
        stage='2025_DIRECTION_DISCOVERY_ONLY', prior_registered=158,
        budget_cap=174, max_new_definitions=16,
        candidate_ids=candidate_ids(cfg),
    )
    assert validate_batch_approval(cfg, 'digest', 'test', approval) == approval['candidate_ids']
