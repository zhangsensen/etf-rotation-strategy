"""Synthetic provenance and availability regressions; no market data or labels."""
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/research'))
import etf_autoresearch_score_preflight as pre
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_etf_autoresearch_workflow_execution import setup_case, one_spec, approve, source
import etf_autoresearch_workflow as wf


def surface_case(tmp_path, monkeypatch):
    new, old = tmp_path / 'new.py', tmp_path / 'old.py'
    new.write_text('new'); old.write_text('old')
    frame = pd.DataFrame({'g1': [1., 2.], 'g2': [2., 1.]}, index=pd.date_range('2025-01-01', periods=2))
    known = pd.Series([True, True], index=frame.index)
    contract = {'input_manifest': {'profile': 'synthetic', 'source_sha256': {'x': 'hash'}}}
    run = tmp_path / 'old'; run.mkdir()
    (run / 'result.json').write_text(json.dumps({**contract, 'candidate_sha256': pre.fixed.digest(old)}))
    frame.to_csv(run / 'group_scores.csv', index_label='signal_date')
    (run / 'evaluation_complete.json').write_text('{}')
    monkeypatch.setattr(pre, 'validate_result', lambda *a: None)
    monkeypatch.setattr(pre, 'score_surface', lambda *a: (frame.copy(), known.copy(), contract))
    return new, old, frame, known, contract, [{'run_id': 'old', 'code_path': str(old)}]


def test_exact_match_requires_etf_known_mask(tmp_path, monkeypatch):
    new, old, frame, known, contract, rows = surface_case(tmp_path, monkeypatch)
    assert pre.check_exact_scores(new, 'daily', tmp_path, rows)['duplicate_of']['run_id'] == 'old'
    # Group aggregation may hide a missing ETF member; same group scores do not suffice.
    def scores(path, profile):
        mask = known.copy()
        if path == old:
            mask.iloc[0] = False
        return frame.copy(), mask, contract
    monkeypatch.setattr(pre, 'score_surface', scores)
    assert pre.check_exact_scores(new, 'daily', tmp_path, rows)['duplicate_of'] is None


@pytest.mark.parametrize('difference', ['manifest', 'index', 'sign', 'missing_source', 'missing_seal'])
def test_unproven_or_different_history_never_suppresses(tmp_path, monkeypatch, difference):
    new, old, frame, known, contract, rows = surface_case(tmp_path, monkeypatch)
    if difference == 'manifest':
        (tmp_path / 'old/result.json').write_text('{}')
    elif difference == 'missing_source':
        rows[0].pop('code_path')
    elif difference == 'missing_seal':
        (tmp_path / 'old/evaluation_complete.json').unlink()
    else:
        def scores(path, profile):
            f = frame.copy()
            if path == old:
                if difference == 'sign': f *= -1
                else: f.index = f.index + pd.Timedelta(days=1)
            return f, known, contract
        monkeypatch.setattr(pre, 'score_surface', scores)
    assert pre.check_exact_scores(new, 'daily', tmp_path, rows)['duplicate_of'] is None


@pytest.mark.parametrize('error', [ValueError('shape'), KeyError('panel'), AssertionError('prefix'), TimeoutError('score budget')])
def test_candidate_error_continues_batch(tmp_path, monkeypatch, error):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def proposer(ctx, directory, model):
        return {'rationale': 'test', 'source_code': source(f'r{ctx["round"]}', ctx['assigned_family_plan']['family_key'], ctx['round']+2)}
    def check(path, *args):
        if 'r01' in str(path):
            raise pre.CandidateScoreError(str(error))
        return {'duplicate_of': None}
    result = wf.workflow('candidate_error', 2, 1, ['daily'], root, inventory, runs,
                         mode='open', propose=proposer, review=approve, evaluate=evaluate,
                         planner=one_spec, score_check=check)
    assert [r['status'] for r in result['rounds']] == ['FAILED', 'COMPLETED']
    assert result['rounds'][0]['outcome_opened'] is False
    assert not (root / result['rounds'][0]['run_id']).exists()


def test_system_error_pauses_before_labels(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def check(*args): raise ValueError('data contract drift')
    def proposer(ctx, *args):
        return {'rationale': 'test', 'source_code': source('broken', ctx['assigned_family_plan']['family_key'])}
    with pytest.raises(ValueError, match='contract drift'):
        wf.workflow('data_error', 2, 1, ['daily'], root, inventory, runs,
                    mode='open', propose=proposer, review=approve, evaluate=evaluate,
                    planner=one_spec, score_check=check)
    result = json.loads((root / 'campaigns/data_error/summary.json').read_text())
    assert result['status'] == 'PAUSED_SYSTEM_ERROR'
    assert result['rounds'][0]['outcome_opened'] is False


def test_preflight_sees_same_round_completed_history(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    completed = []
    monkeypatch.setattr(wf, 'context_for_proposer', lambda *_: {'historical_formal_definitions': [], 'local_completed_candidates': list(completed)})
    def planner(ctx, *args):
        return [dict(one_spec(ctx, *args)[0], family_key=f'f{i}') for i in range(2)]
    def proposer(ctx, *args):
        return {'rationale': 'test', 'source_code': source(f'c{ctx["slot"]}', ctx['assigned_family_plan']['family_key'], 4+ctx['slot'])}
    def eval_one(*args, **kwargs):
        result = evaluate(*args, **kwargs)
        completed.append({'run_id': args[0]})
        return result
    history_sizes = []
    def check(path, profile, output, history):
        history_sizes.append(len(history))
        return {'duplicate_of': history[0] if history else None}
    summary = wf.workflow('same_round', 1, 2, ['daily'], root, inventory, runs, mode='open',
                          propose=proposer, review=approve, evaluate=eval_one, planner=planner, score_check=check)
    assert history_sizes == [0, 1]
    assert [r['status'] for r in summary['rounds']] == ['COMPLETED', 'DUPLICATE']
    assert summary['rounds'][1]['outcome_opened'] is False


@pytest.mark.parametrize('failure', [ValueError('candidate score calendar invalid'), KeyError('panel'), AssertionError('causality'), TimeoutError('candidate timeout')])
def test_score_stage_classifies_candidate_failures(tmp_path, monkeypatch, failure):
    groups = tmp_path / 'groups.yaml'; groups.write_text('groups: {}')
    frame = pd.DataFrame({'ETF': [1., 2.]}, index=pd.date_range('2025-01-01', periods=2))
    monkeypatch.setattr(pre.fixed, 'GROUPS', groups)
    monkeypatch.setattr(pre.fixed.pd, 'read_parquet', lambda *a, **k: pd.DataFrame({'trade_date': frame.index}))
    monkeypatch.setattr(pre.fixed, 'load_canonical_daily', lambda *a, **k: {key: frame for key in ('close','open','high','low','amount','volume')})
    monkeypatch.setattr(pre.fixed.engine, 'validate_groups', lambda *a: None)
    monkeypatch.setattr(pre.fixed, 'digest', lambda *a: 'synthetic')
    def fail(*a, **k): raise failure
    monkeypatch.setattr(pre, 'bounded_call', fail)
    with pytest.raises(pre.CandidateScoreError): pre.score_surface(tmp_path / 'candidate.py', 'daily')
    monkeypatch.setattr(pre.fixed, 'load_canonical_daily', fail)
    with pytest.raises(type(failure)) as caught: pre.score_surface(tmp_path / 'candidate.py', 'daily')
    assert not isinstance(caught.value, pre.CandidateScoreError)


def test_formula_identity_is_signed_and_not_a_skip_gate(tmp_path, monkeypatch):
    positive = source('one', 'f1')
    assert wf.formula_hash(positive) != wf.formula_hash(positive.replace('DIRECTION = 1', 'DIRECTION = -1'))
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def planner(ctx, *args):
        return [dict(one_spec(ctx, *args)[0], family_key=f'f{i}') for i in range(2)]
    def proposer(ctx, *args):
        return {'rationale': 'synthetic', 'source_code': source(f'c{ctx["slot"]}', ctx['assigned_family_plan']['family_key'])}
    summary = wf.workflow('same_ast', 1, 2, ['daily'], root, inventory, runs, mode='open',
                          propose=proposer, review=approve, evaluate=evaluate, planner=planner, score_check=lambda *a: {'duplicate_of': None})
    assert [r['source_formula_seen'] for r in summary['rounds']] == [False, True]
    assert all(r['status'] == 'COMPLETED' for r in summary['rounds'])


@pytest.mark.parametrize('case, expected', [('missing_member', 0), ('ties', 0), ('rounded_ties', 0), ('one_day', 1)])
def test_structural_preflight_preserves_sparse_but_blocks_zero(tmp_path, monkeypatch, case, expected):
    new, old, frame, known, contract, rows = surface_case(tmp_path, monkeypatch)
    if case == 'missing_member': known[:] = False
    elif case == 'ties': frame[:] = 1.
    elif case == 'rounded_ties':
        frame['g1'] = 1.; frame['g2'] = 1. + 1e-14
    else: known.iloc[0] = False
    receipt = pre.check_exact_scores(new, 'daily', tmp_path, [])
    assert receipt['rankable_signal_days'] == expected
    assert receipt['structural_failure'] == ('ZERO_RANKABLE_DATES' if expected == 0 else None)


def test_zero_rankable_candidate_does_not_open_labels_or_stop_batch(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path, monkeypatch)
    def proposer(ctx, *args):
        return {'rationale': 'test', 'source_code': source(f'r{ctx["round"]}', ctx['assigned_family_plan']['family_key'], ctx['round']+2)}
    def check(path, *args):
        return {'structural_failure': 'ZERO_RANKABLE_DATES' if 'r01' in str(path) else None,
                'rankable_signal_days': 0 if 'r01' in str(path) else 1, 'duplicate_of': None}
    summary = wf.workflow('zero_rankable', 2, 1, ['daily'], root, inventory, runs, mode='open',
                          propose=proposer, review=approve, evaluate=evaluate, planner=one_spec, score_check=check)
    assert [r['status'] for r in summary['rounds']] == ['FAILED', 'COMPLETED']
    assert summary['rounds'][0]['reason_code'] == 'ZERO_RANKABLE_DATES'
    assert summary['rounds'][0]['outcome_opened'] is False
    assert summary['evaluated_count'] == 1
    assert not (root / summary['rounds'][0]['run_id']).exists()


def test_prelabel_overlap_tracks_negative_correlation_and_effective_dates(tmp_path):
    dates = pd.date_range('2025-01-01', periods=70)
    scores = pd.DataFrame([[1., 2., 3.]] * len(dates), index=dates, columns=['a','b','c'])
    path = tmp_path / 'old.csv';(-scores).to_csv(path,index_label='signal_date')
    known = pd.Series(True,index=dates);known.iloc[:20] = False
    result = pre.diagnose_overlap(scores,known,[{'candidate':'old','score_path':str(path)}])
    assert result['nearest']['n'] == 50
    assert result['nearest']['mean_signed_daily_rank_corr'] == pytest.approx(-1)
    assert result['classification'] == 'HIGH_RANK_OVERLAP'
    assert result['labels_opened'] is False
    known.iloc[:40] = False
    assert pre.diagnose_overlap(scores,known,[{'candidate':'old','score_path':str(path)}])['classification'] == 'UNKNOWN'


def test_high_prelabel_overlap_still_evaluates_and_keeps_signed_ic(tmp_path, monkeypatch):
    root, inventory, runs, evaluate = setup_case(tmp_path,monkeypatch)
    def proposer(ctx,*_):
        return {'rationale':'synthetic','source_code':source('overlap','family_r1')}
    receipt = {'duplicate_of':None,'score_overlap':{'classification':'HIGH_RANK_OVERLAP','nearest':{'mean_abs_daily_rank_corr':.98}}}
    s=wf.workflow('overlap_not_gate',1,1,['daily'],root,inventory,runs,mode="open",
        propose=proposer,review=approve,evaluate=evaluate,planner=one_spec,score_check=lambda *_:receipt)
    assert s['rounds'][0]['status'] == 'COMPLETED'
    assert s['rounds'][0]['ic'] == .02
    assert s['rounds'][0]['prelabel_overlap']['classification'] == 'HIGH_RANK_OVERLAP'
