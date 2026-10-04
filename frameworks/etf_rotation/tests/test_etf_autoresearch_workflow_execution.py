import json
from pathlib import Path
import sys

import pytest

RESEARCH = Path(__file__).resolve().parents[1] / 'scripts/research'
sys.path.insert(0, str(RESEARCH))
import etf_autoresearch_workflow as wf


@pytest.mark.parametrize('mode', ['mixed', 'explore', 'refine'])
def test_retired_modes_fail_before_creating_a_campaign(tmp_path, mode):
    with pytest.raises(ValueError, match='open mode only'):
        wf.workflow('retired', 1, 4, ['daily'], tmp_path / 'out',
                    tmp_path / 'inventory.csv', tmp_path / 'runs', mode=mode)
    assert not (tmp_path / 'out').exists()


@pytest.mark.parametrize('error', [ValueError('model request too large'), RuntimeError('503 unavailable'),
                                  TimeoutError('planner timed out'), OSError('cannot persist model reply')])
def test_planning_fault_never_consumes_empty_rounds_or_opens_labels(tmp_path, monkeypatch, error):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    calls = []
    def broken(ctx, *_):
        calls.append(ctx['round'])
        raise error
    def forbidden(*args, **kwargs):
        pytest.fail('planning failure must not implement or evaluate a candidate')
    kwargs = dict(planner=broken, propose=forbidden, review=forbidden, evaluate=forbidden)
    with pytest.raises(RuntimeError, match='PAUSED_SYSTEM_ERROR'):
        wf.workflow('plan_fault', 20, 4, ['daily'], root, inventory, runs, **kwargs)
    state = json.loads((root / 'campaigns/plan_fault/summary.json').read_text())
    assert state['status'] == 'PAUSED_SYSTEM_ERROR'
    assert state.get('completed_rounds', 0) == 0 and state['empty_rounds'] == 0
    assert state['progress']['planning_error_rounds'] == [1]
    with pytest.raises(RuntimeError, match='PAUSED_SYSTEM_ERROR'):
        wf.workflow('plan_fault', 20, 4, ['daily'], root, inventory, runs, resume=True, **kwargs)
    assert calls == [1]  # Resume cannot reissue an exhausted request silently.


def test_partial_planner_success_is_preserved_when_backup_request_fails(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def planner(ctx, *_):
        if ctx['planning_attempt'] == 2:
            raise ValueError('model request too large')
        return one_spec(ctx, None, None)
    with pytest.raises(RuntimeError, match='PAUSED_SYSTEM_ERROR'):
        wf.workflow('partial', 20, 4, ['daily'], root, inventory, runs,
                    planner=planner, review=approve, evaluate=evaluate)
    directory = root / 'campaigns/partial'
    assert len(json.loads((directory / 'planning_r01_attempt1/result.json').read_text())['specs']) == 1
    state = json.loads((directory / 'summary.json').read_text())
    assert state['round_records'][0]['preserved_proposals'] == 1
    assert state['evaluated_count'] == 0 and not state['progress']['complete']


def test_open_discovery_does_not_need_unrelated_seed(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def proposer(ctx, *_):
        return {'rationale': 'test', 'source_code': source('open_without_seed', ctx['assigned_family_plan']['family_key'])}
    def evaluator(*args, **kwargs):
        assert args[2] is None
        return evaluate(*args, **kwargs)
    state = wf.workflow('no_seed', 1, 1, ['daily'], root, inventory, runs,
                        propose=proposer, planner=one_spec, review=approve, evaluate=evaluator)
    assert state['progress']['complete'] and state['numeric_ic_count'] == 1


def test_implementation_transport_failure_pauses_without_consuming_round(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def proposer(*_):
        raise RuntimeError('model service unavailable')
    with pytest.raises(RuntimeError, match='implementation model failed'):
        wf.workflow('implementation_fault', 20, 1, ['daily'], root, inventory, runs,
                    propose=proposer, planner=one_spec, review=approve, evaluate=evaluate)
    state = json.loads((root / 'campaigns/implementation_fault/summary.json').read_text())
    assert state['status'] == 'PAUSED_SYSTEM_ERROR'
    assert state['evaluated_count'] == 0 and state.get('completed_rounds', 0) == 0


def test_console_progress_keeps_signed_result_without_reprinting_history():
    row = {'run_id': 'trial', 'status': 'COMPLETED', 'ic': -.02, 'hac_t': -1.1, 'n': 287,
           'family_plan': {'formula': 'x' * 50000}, 'prelabel_overlap': {'skipped': ['x'] * 1000}}
    event = wf.progress_event(row)
    assert event['ic'] == -.02 and event['n'] == 287
    assert 'family_plan' not in event and 'prelabel_overlap' not in event
    assert len(json.dumps(event)) < 200


def source(candidate, family, window=5):
    return f'''import pandas as pd\nCANDIDATE_ID = "autoresearch_{candidate}"\nFAMILY = "{family}"\nDIRECTION = 1\nDESCRIPTION = "rolling return"\ndef score(panels):\n    return panels["close"].pct_change({window}, fill_method=None)\n'''


def setup_case(tmp_path, monkeypatch):
    root, runs = tmp_path / 'out', tmp_path / 'runs'
    inventory = tmp_path / 'inventory.csv'
    inventory.write_text('candidate,family\n')
    runs.mkdir()
    monkeypatch.setattr(wf, 'require_latest_inventory', lambda *_: None)
    monkeypatch.setattr(wf, 'describe_profiles', lambda *_: {'daily': {'available': True, 'approved': True}})
    monkeypatch.setattr(wf, 'context_for_proposer', lambda *_: {'historical_formal_definitions': [], 'local_completed_candidates': []})
    monkeypatch.setattr(wf, 'family_history', lambda *_: {'recent_round_families': [], 'family_attempt_counts': {}, 'aliases': {}, 'unsuccessful_refinements': {}})

    def evaluate(run_id, output_root, baseline, inventory_path, runs_root, candidate_path=None, input_profile=None):
        assert baseline is None
        out = output_root / run_id
        out.mkdir(parents=True, exist_ok=True)
        metadata = wf.validate_source(Path(candidate_path).read_text())
        (out / 'result.json').write_text(json.dumps({'run_id': run_id, 'candidate': metadata['CANDIDATE_ID'], 'family': metadata['FAMILY'], 'ic': .02, 'hac_t': 1, 'n': 20, 'yearly': {}}))
        return {'decision': 'positive_ic_review'}

    return root, inventory, runs, evaluate


def one_spec(context, directory, model):
    family = f"family_r{context['round']}"
    return [{'family_key': family, 'mechanism': 'rolling return', 'distinct_from': 'other',
             'why_distinct': 'different hypothesis', 'input_profile': 'daily', 'direction': 1,
             'formula': 'rolling close return'}]


def approve(items, directory, model):
    return {x['run_id']: {'run_id': x['run_id'], 'approved': True, 'reason': 'accepted',
                           'canonical_family': x['planned_family'], 'reason_code': 'approved', 'repairable': False}
            for x in items}


def test_rejected_rounds_continue_to_later_round(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    evaluated = []
    def proposer(ctx, directory, model):
        fam = ctx['assigned_family_plan']['family_key']
        return {'rationale': 'test', 'source_code': source(f'candidate_{ctx["round"]}', fam, 5 + ctx['round'])}
    def reviewer(items, directory, model):
        if items[0]['round'] <= 2:
            x = items[0]
            return {x['run_id']: {'run_id': x['run_id'], 'approved': False, 'reason': 'technical mismatch',
                                  'canonical_family': x['planned_family'], 'reason_code': 'technical_mismatch', 'repairable': False}}
        return approve(items, directory, model)
    def count_eval(*args, **kwargs):
        evaluated.append(args[0]); return evaluate(*args, **kwargs)
    summary = wf.workflow('reject_continue', 3, 1, ['daily'], root, inventory, runs,
                          mode='open', propose=proposer, review=reviewer, evaluate=count_eval,
                          planner=one_spec)
    assert [x['status'] for x in summary['rounds']] == ['REJECTED', 'REJECTED', 'COMPLETED']
    assert len(evaluated) == 1
    assert summary['evaluated_rounds'] == 1 and summary['positive_ic_count'] == 1


def test_empty_round_gets_one_alternate_planning_attempt_then_campaign_continues(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    calls = []
    def planner(ctx, directory, model):
        calls.append((ctx['round'], ctx.get('planning_attempt', 1)))
        return [] if ctx['round'] == 1 else one_spec(ctx, directory, model)
    def proposer(ctx, directory, model):
        family = ctx['assigned_family_plan']['family_key']
        return {'rationale': 'test', 'source_code': source('candidate_empty_test', family)}
    summary = wf.workflow('empty_continue', 2, 1, ['daily'], root, inventory, runs,
                          mode='open', propose=proposer, review=approve, evaluate=evaluate,
                          planner=planner)
    assert calls == [(1, 1), (1, 2), (2, 1)]
    assert summary['empty_rounds'] == 1
    assert summary['evaluated_rounds'] == 1
    assert summary['round_records'][0]['status'] == 'EMPTY'


def test_repair_preserves_formula_direction_and_saves_both_hashes(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    proposal_calls = []
    def proposer(ctx, directory, model):
        proposal_calls.append(ctx)
        fam = ctx['assigned_family_plan']['family_key']
        code = source('repair_same_formula', fam)
        if not ctx.get('repair_only'):
            code = code.replace('return panels["close"].pct_change(5, fill_method=None)', 'return (')
        return {'rationale': 'repaired' if ctx.get('repair_only') else 'original', 'source_code': code}
    review_calls = []
    def reviewer(items, directory, model):
        review_calls.append(items)
        if len(review_calls) == 1:
            x = items[0]
            return {x['run_id']: {'run_id': x['run_id'], 'approved': False, 'reason': 'shape issue',
                                  'canonical_family': x['planned_family'], 'reason_code': 'shape', 'repairable': True}}
        return approve(items, directory, model)
    summary = wf.workflow('repair_once', 1, 1, ['daily'], root, inventory, runs,
                          mode='open', propose=proposer, review=reviewer, evaluate=evaluate,
                          planner=one_spec)
    row = summary['rounds'][0]
    assert row['repair_used'] is True
    assert Path(row['original_source_path']).exists() and Path(row['repaired_source_path']).exists()
    assert row['original_candidate_sha256'] != row['repaired_candidate_sha256']
    assert len(proposal_calls) == 2 and row['status'] == 'COMPLETED'
    campaign_dir = root / 'campaigns/repair_once'
    assert (campaign_dir / 'review_r01_initial.json').exists()
    assert (campaign_dir / 'review_r01_final.json').exists()
    assert (Path(row['source_path']).parent / 'repair_attempt1/proposal.json').exists()


def test_repair_cannot_flip_planned_direction(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def proposer(ctx, directory, model):
        fam = ctx['assigned_family_plan']['family_key']
        code = source('direction_locked', fam)
        if not ctx.get('repair_only'):
            return {'rationale': 'original', 'source_code': code.replace('return panels["close"].pct_change(5, fill_method=None)', 'return (')}
        return {'rationale': 'bad repair', 'source_code': code.replace('DIRECTION = 1', 'DIRECTION = -1')}
    def reviewer(items, directory, model):
        x = items[0]
        return {x['run_id']: {'run_id': x['run_id'], 'approved': False, 'reason': 'syntax issue',
                              'canonical_family': x['planned_family'], 'reason_code': 'syntax', 'repairable': True}}
    summary = wf.workflow('direction_repair', 1, 1, ['daily'], root, inventory, runs,
                          mode='open', propose=proposer, review=reviewer, evaluate=evaluate,
                          planner=one_spec)
    assert summary['rounds'][0]['status'] == 'FAILED'
    assert 'frozen direction' in summary['rounds'][0]['error']
    assert summary['rounds'][0]['outcome_opened'] is False
    assert summary['evaluated_count'] == 0


def test_unknown_evaluator_error_pauses_and_resume_does_not_reopen_outcome(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    calls = []
    def proposer(ctx, directory, model):
        return {'rationale': 'test', 'source_code': source('paused_candidate', ctx['assigned_family_plan']['family_key'])}
    def broken(*args, **kwargs):
        calls.append(args[0]); raise OSError('calendar source unavailable')
    with pytest.raises(RuntimeError, match='PAUSED_SYSTEM_ERROR'):
        wf.workflow('paused_case', 1, 1, ['daily'], root, inventory, runs, mode='open',
                    propose=proposer, review=approve, evaluate=broken, planner=one_spec)
    summary_path = root / 'campaigns/paused_case/summary.json'
    state = json.loads(summary_path.read_text())
    assert state['status'] == 'PAUSED_SYSTEM_ERROR'
    assert state['rounds'][0]['outcome_opened'] is True
    with pytest.raises(RuntimeError):
        wf.workflow('paused_case', 1, 1, ['daily'], root, inventory, runs, mode='open',
                    propose=proposer, review=approve, evaluate=broken, planner=one_spec, resume=True)
    assert calls == [state['rounds'][0]['run_id']]


def test_resume_repaired_candidate_retries_review_not_proposal(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    proposals, reviews, evaluations = [], [], []
    def proposer(ctx, directory, model):
        proposals.append(ctx)
        code = source('resume_repair', ctx['assigned_family_plan']['family_key'])
        if not ctx.get('repair_only'):
            code = code.replace('return panels["close"].pct_change(5, fill_method=None)', 'return (')
        return {'rationale': 'test', 'source_code': code}
    def reviewer(items, directory, model):
        reviews.append(items)
        if len(reviews) == 1:
            x = items[0]
            return {x['run_id']: {'run_id': x['run_id'], 'approved': False,
                    'reason': 'syntax', 'canonical_family': x['planned_family'],
                    'reason_code': 'syntax', 'repairable': True}}
        if len(reviews) == 2:
            raise RuntimeError('review service unavailable')
        assert 'return (' in items[0]['repair_original_source']
        assert 'pct_change' in items[0]['source_code']
        return approve(items, directory, model)
    def count_eval(*args, **kwargs):
        evaluations.append(args[0])
        return evaluate(*args, **kwargs)
    kwargs = dict(mode='open', propose=proposer, review=reviewer,
                  evaluate=count_eval, planner=one_spec)
    with pytest.raises(RuntimeError, match='review service unavailable'):
        wf.workflow('resume_repair', 1, 1, ['daily'], root, inventory, runs, **kwargs)
    assert len(proposals) == 2 and not evaluations
    result = wf.workflow('resume_repair', 1, 1, ['daily'], root, inventory, runs,
                         resume=True, **kwargs)
    assert len(proposals) == 2 and len(evaluations) == 1
    assert result['rounds'][0]['status'] == 'COMPLETED'


def test_frozen_source_tampering_pauses_before_labels(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def proposer(ctx, directory, model):
        return {'rationale': 'test', 'source_code': source('tampered', ctx['assigned_family_plan']['family_key'])}
    def reviewer(items, directory, model):
        path = Path(items[0]['source_path'])
        path.write_text(path.read_text() + '\n# external edit\n')
        return approve(items, directory, model)
    with pytest.raises(RuntimeError, match='PAUSED_SYSTEM_ERROR'):
        wf.workflow('tampered', 1, 1, ['daily'], root, inventory, runs,
                    mode='open', propose=proposer, review=reviewer, evaluate=evaluate,
                    planner=one_spec)
    summary = json.loads((root / 'campaigns/tampered/summary.json').read_text())
    assert summary['status'] == 'PAUSED_SYSTEM_ERROR'
    assert summary['rounds'][0]['outcome_opened'] is False


def test_malformed_plan_uses_only_one_alternate_attempt(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    calls = []
    def planner(ctx, directory, model):
        calls.append(ctx['planning_attempt'])
        if len(calls) == 1:
            raise wf.PlannerResponseError('missing formula')
        return one_spec(ctx, directory, model)
    def proposer(ctx, directory, model):
        return {'rationale': 'test', 'source_code': source('alternate', ctx['assigned_family_plan']['family_key'])}
    summary = wf.workflow('alternate', 1, 1, ['daily'], root, inventory, runs,
                          mode='open', propose=proposer, review=approve, evaluate=evaluate,
                          planner=planner)
    assert calls == [1, 2] and summary['evaluated_count'] == 1


def test_review_records_requested_model(tmp_path, monkeypatch):
    def model_json(prompt, schema, directory, model, role):
        assert model == 'gpt-6.1-sol'
        assert 'shared_historical_formal_definitions' not in prompt
        return {'reviews': [{'run_id': 'one', 'approved': True, 'canonical_family': 'flow',
                             'reason': 'valid', 'reason_code': 'approved', 'repairable': False}]}
    monkeypatch.setattr(wf, 'model_json', model_json)
    result = wf.review_batch([{'run_id': 'one', 'mode': 'open', 'source_code': source('one', 'flow'),
                               'historical_formal_definitions': []}], tmp_path, 'gpt-6.1-sol')
    assert result['one']['reviewer_model'] == 'gpt-6.1-sol'


def test_completed_evaluation_resumes_bookkeeping_without_recalculation(tmp_path, monkeypatch):
    import etf_autoresearch_recovery as recovery
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    calls = []
    def proposer(ctx, directory, model):
        return {'rationale': 'test', 'source_code': source('receipt_resume', ctx['assigned_family_plan']['family_key'])}
    def counted(*args, **kwargs):
        calls.append(args[0])
        result = evaluate(*args, **kwargs)
        out = root / args[0]
        for name in ('daily_ic.csv', 'group_scores.csv'):
            (out / name).write_text('synthetic')
        recovery.seal_result(out)
        return result
    def validate(directory, *_args, **_kwargs):
        recovery.seal_result(directory)
        return json.loads((directory / 'result.json').read_text())
    monkeypatch.setattr(wf, 'validate_result', validate)
    failed = False
    def index(*_):
        nonlocal failed
        p = root / 'campaigns/receipt_resume/summary.json'
        if p.exists():
            saved = json.loads(p.read_text())
            if not failed and any(r['status'] == 'RESULT_READY' for r in saved['rounds']):
                failed = True
                raise OSError('bookkeeping unavailable')
    monkeypatch.setattr(wf, 'rebuild_library', index)
    kwargs = dict(mode='open', propose=proposer, review=approve,
                  evaluate=counted, planner=one_spec)
    with pytest.raises(OSError, match='bookkeeping unavailable'):
        wf.workflow('receipt_resume', 1, 1, ['daily'], root, inventory, runs, **kwargs)
    summary = wf.workflow('receipt_resume', 1, 1, ['daily'], root, inventory, runs, resume=True, **kwargs)
    assert summary['status'] == 'COMPLETED' and len(calls) == 1
    assert summary['rounds'][0]['ic'] == .02


def test_static_error_gets_repair_even_when_model_approves(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def proposer(ctx, *_):
        code = source('static_repair', ctx['assigned_family_plan']['family_key'])
        if not ctx.get('repair_only'):
            code += '\nREQUIRED_PANELS = ["close"]\n'
        else:
            assert 'top-level assignment' in ctx['repair_instruction']
        return {'rationale': 'same formula', 'source_code': code}
    result = wf.workflow('static_repair', 1, 1, ['daily'], root, inventory, runs,
        mode='open', propose=proposer, review=approve, evaluate=evaluate, planner=one_spec)
    assert result['rounds'][0]['status'] == 'COMPLETED'
    assert result['rounds'][0]['repair_used']


def test_partial_new_plan_uses_one_bounded_alternative_before_implementation(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    calls = []
    def planner(ctx, *_):
        calls.append(ctx['requested_count'])
        return [dict(one_spec(ctx, None, None)[0], family_key='first' if ctx['planning_attempt'] == 1 else 'second')]
    def proposer(ctx, *_):
        fam = ctx['assigned_family_plan']['family_key']
        return {'rationale': 'test', 'source_code': source(fam, fam, ctx['slot'] + 3)}
    result = wf.workflow('partial', 1, 4, ['daily'], root, inventory, runs,
        mode='open', propose=proposer, review=approve, evaluate=evaluate, planner=planner)
    assert calls == [4, 3]
    assert result['evaluated_count'] == 2


def test_plan_review_precedes_implementation_and_preserves_same_family_siblings(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    calls = []
    def planner(ctx, *_):
        return [{**one_spec(ctx, None, None)[0], 'family_key': family} for family in ('gold_alias', 'fx_alias')]
    def plan_review(slots, *_):
        calls.append(('plan', len(slots)))
        return {s['plan_id']: {'canonical_family': 'recovery', 'kind': 'NEW_FAMILY',
                              'math_kernel': 'custom', 'reason': 'same channel'} for s in slots}
    def proposer(ctx, *_):
        calls.append(('source', ctx['assigned_family_plan']['family_key']))
        return {'rationale': 'test', 'source_code': source('canonical', 'recovery')}
    summary = wf.workflow('plan_first', 1, 2, ['daily'], root, inventory, runs,
        mode='open', propose=proposer, review=approve, evaluate=evaluate,
        planner=planner, plan_review=plan_review)
    assert calls == [('plan', 2), ('source', 'recovery'), ('source', 'recovery')]
    assert summary['evaluated_rounds'] == 1
    frozen = json.loads((root/'campaigns/plan_first/plan_r01.json').read_text())
    assert len(frozen['slots']) == 2 and not frozen['classified_before_implementation']


def test_repair_review_does_not_revisit_unchanged_sibling(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    review_calls = []
    def planner(ctx, *_):
        return [{**one_spec(ctx, None, None)[0], 'family_key': f'family_{i}'} for i in range(2)]
    def proposer(ctx, *_):
        family = ctx['assigned_family_plan']['family_key']
        code = source(f'candidate_{family}', family, 5 if family=='family_0' else 7)
        if family=='family_1' and not ctx.get('repair_only'):
            code += '\n# defective input access\n'
        return {'rationale': 'test', 'source_code': code}
    def check(code, _):
        if 'defective input access' in code:
            raise KeyError('synthetic missing input')
        return {'status': 'PASS'}
    def reviewer(items, *_):
        review_calls.append([x['planned_family'] for x in items])
        return approve(items, None, None)
    summary = wf.workflow('repair_scope', 1, 2, ['daily'], root, inventory, runs,
        mode='open', propose=proposer, review=reviewer, evaluate=evaluate,
        planner=planner, implementation_check=check)
    assert review_calls == [['family_0', 'family_1'], ['family_1']]
    assert [r['status'] for r in summary['rounds']] == ['COMPLETED', 'COMPLETED']
    assert summary['rounds'][1]['repair_used']


def test_technical_review_cannot_reclassify_a_frozen_plan(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def plan_review(slots, *_):
        return {s['plan_id']: {'canonical_family': s['family_key'], 'kind': 'NEW_FAMILY',
                              'math_kernel': 'custom', 'reason': 'distinct channel'} for s in slots}
    def proposer(ctx, *_):
        family = ctx['assigned_family_plan']['family_key']
        return {'rationale': 'test', 'source_code': source('frozen_family', family)}
    def reviewer(items, *_):
        results = approve(items, None, None)
        for verdict in results.values():
            verdict['canonical_family'] = 'another_family'
        return results
    summary = wf.workflow('family_drift', 1, 1, ['daily'], root, inventory, runs,
        mode='open', propose=proposer, review=reviewer, evaluate=evaluate,
        planner=one_spec, plan_review=plan_review)
    assert summary['evaluated_rounds'] == 0
    assert summary['rounds'][0]['reason_code'] == 'FAMILY_REVIEW_DRIFT'


def test_open_search_accepts_full_batch_of_old_same_family_without_cooldown(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    monkeypatch.setattr(wf, 'context_for_proposer', lambda *_: {
        'historical_formal_definitions': [{'family': 'old', 'candidate': 'old_factor'}],
        'local_completed_candidates': []})
    monkeypatch.setattr(wf, 'family_history', lambda *_: {
        'recent_round_families': ['old'], 'family_attempt_counts': {'old': 50},
        'aliases': {}, 'unsuccessful_refinements': {'old': 10}})
    monkeypatch.setattr(wf, 'describe_profiles', lambda *_: {p:{'available':True,'approved':True} for p in ('daily','share')})
    contexts=[]
    def planner(ctx, *_):
        contexts.append(ctx)
        assert ctx['mode']=='open' and ctx['requested_count']==4
        assert ctx['forbidden_family_keys']==[]
        assert set(ctx['allowed_profiles'])=={'daily','share'}
        assert 'mechanism_focus' not in ctx and 'source_focus' not in ctx
        return [{**one_spec(ctx,None,None)[0], 'family_key':'old',
                 'novelty_basis':'bounded_variant', 'required_panels':['close'], 'formula':f'return window {i+2}'} for i in range(4)]
    monkeypatch.setattr(wf, 'plan_families', planner)
    def plan_review(slots, ctx, *_):
        assert ctx['mode']=='open'
        return {s['plan_id']:{'canonical_family':'old',
                'kind':'BATCH_DUPLICATE' if i else 'OLD_VARIANT',
                'math_kernel':'custom','reason':'same channel; distinct windows'} for i,s in enumerate(slots)}
    def proposer(ctx, *_):
        slot=ctx['slot']
        return {'rationale':'test','source_code':source(f'open_{slot}','old',slot+1)}
    summary=wf.workflow('open_history',1,4,['daily','share'],root,inventory,runs,
        propose=proposer,review=approve,evaluate=evaluate,plan_review=plan_review)
    assert len(contexts)==1
    assert summary['evaluated_open_candidates']==4
    assert summary['evaluated_explorations']==0  # Old families are not counted as new discoveries.
    assert summary['planning_diagnostics']['open_batch_requests']==1
    assert all(r['status']=='COMPLETED' for r in summary['rounds'])


def test_open_technical_review_does_not_offer_semantic_duplicate_rejection(tmp_path, monkeypatch):
    def model(prompt, schema, *_):
        assert 'This is OPEN search' in prompt
        assert 'duplicate' not in schema['properties']['reviews']['items']['properties']['reason_code']['enum']
        return {'reviews':[{'run_id':'candidate','approved':True,'canonical_family':'old',
            'reason':'valid','reason_code':'approved','repairable':False}]}
    monkeypatch.setattr(wf,'model_json',model)
    result=wf.review_batch([{'run_id':'candidate','mode':'open','family_plan':{'family_key':'old'}}],tmp_path,'gpt-6.1-sol')
    assert result['candidate']['approved']


def test_open_exact_score_duplicate_reuses_history_without_evaluation(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def proposer(ctx,*_):
        return {'rationale':'test','source_code':source('exact','family_r1')}
    def forbidden_eval(*_):
        pytest.fail('exact sealed score duplicate must not open labels again')
    result=wf.workflow('open_exact',1,1,['daily'],root,inventory,runs,
        propose=proposer,review=approve,evaluate=forbidden_eval,planner=one_spec,
        score_check=lambda *_:{'duplicate_of':'old_sealed_candidate'})
    assert result['rounds'][0]['status']=='DUPLICATE'
    assert result['evaluated_open_candidates']==0


def test_mislabeled_template_does_not_force_rewrite_of_custom_formula(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    proposals=[];reviews=[]
    def planner(ctx,*_):
        return [{**one_spec(ctx,None,None)[0], 'math_kernel':'conditional_ols'}]
    def proposer(ctx,*_):
        proposals.append(ctx)
        return {'rationale':'rolling return has no OLS kernel',
                'source_code':source('custom_not_conditional','family_r1')}
    def review(items,*_):
        reviews.extend(items)
        return approve(items,None,None)
    result=wf.workflow('template_fallback',1,1,['daily'],root,inventory,runs,
        propose=proposer,review=review,evaluate=evaluate,planner=planner)
    row=result['rounds'][0]
    assert row['status']=='COMPLETED' and len(proposals)==1
    assert not row.get('repair_used')
    assert reviews[0]['math_kernel_binding']['requested']=='conditional_ols'
    assert reviews[0]['math_kernel_binding']['effective']=='custom'


def test_custom_fallback_still_requires_formula_review(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def planner(ctx,*_):
        return [{**one_spec(ctx,None,None)[0], 'math_kernel':'conditional_ols'}]
    def proposer(ctx,*_):
        return {'rationale':'wrong formula','source_code':source('wrong_custom','family_r1')}
    def review(items,*_):
        return {i['run_id']:{'approved':False,'canonical_family':i['planned_family'],
                'reason':'does not match frozen formula','reason_code':'technical_mismatch','repairable':False} for i in items}
    result=wf.workflow('template_reject',1,1,['daily'],root,inventory,runs,
        propose=proposer,review=review,evaluate=evaluate,planner=planner)
    assert result['rounds'][0]['status']=='REJECTED'
    assert result['evaluated_open_candidates']==0
