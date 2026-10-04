import json
from pathlib import Path
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/research'))
import etf_autoresearch_recovery as recovery


def test_reference_identity_is_order_independent_and_contract_bound(tmp_path):
    a = recovery.reference_id('batch', 'daily', 'first', {'data': 'one'})
    b = recovery.reference_id('batch', 'daily', 'second', {'data': 'one'})
    assert a != b
    assert recovery.reference_id('batch', 'daily', 'first', {'data': 'one'}) == a
    assert recovery.reference_id('batch', 'daily', 'first', {'data': 'two'}) != a
    path = tmp_path / 'frozen.py'
    recovery.immutable_source(path, 'first')
    with pytest.raises(ValueError, match='mismatch'):
        recovery.immutable_source(path, 'second')
    assert path.read_text() == 'first'


def test_receipt_detects_result_modification(tmp_path):
    for name in ('result.json', 'daily_ic.csv', 'group_scores.csv'):
        (tmp_path / name).write_text('{}')
    recovery.seal_result(tmp_path)
    recovery.seal_result(tmp_path)
    (tmp_path / 'daily_ic.csv').write_text('modified')
    with pytest.raises(ValueError, match='hash mismatch'):
        recovery.seal_result(tmp_path)


def test_process_deadline_is_enforced():
    started = time.monotonic()
    with pytest.raises(recovery.EvaluationTimeout):
        recovery.bounded_call(time.sleep, 30, timeout=.05)
    assert time.monotonic() - started < 3
    assert recovery.bounded_call(sum, [1, 2], timeout=2) == 3


def migration_case(tmp_path):
    campaign = tmp_path / 'campaigns' / 'old'
    campaign.mkdir(parents=True)
    source = campaign / 'candidate.py'
    source.write_text('frozen')
    row = {'run_id': 'trial', 'status': 'PAUSED_SYSTEM_ERROR', 'outcome_opened': True,
           'error': 'PAUSED_SYSTEM_ERROR: baseline seed failed: resumed reference source differs',
           'source_path': str(source), 'candidate_sha256': recovery.sha(source), 'review': {'approved': True}}
    recovery.atomic(campaign / 'summary.json', {'rounds': [row], 'status': 'PAUSED_SYSTEM_ERROR'})
    return campaign


def test_migration_preserves_legacy_flag_and_records_correction(tmp_path):
    campaign = migration_case(tmp_path)
    assert recovery.migrate_legacy_reference_failure(tmp_path, 'old')
    result = json.loads((campaign / 'summary.json').read_text())
    assert result['rounds'][0]['outcome_opened'] is True
    assert result['rounds'][0]['candidate_evaluation_started'] is False
    assert result['rounds'][0]['status'] == 'FROZEN'
    assert (campaign / 'legacy_reference_recovery.json').exists()
    assert recovery.migrate_legacy_reference_failure(tmp_path, 'old') is False


@pytest.mark.parametrize('artifact', ['directory', 'attempt'])
def test_migration_refuses_possible_evaluation(tmp_path, artifact):
    migration_case(tmp_path)
    if artifact == 'directory':
        (tmp_path / 'trial').mkdir()
    else:
        (tmp_path / 'attempts').mkdir()
        (tmp_path / 'attempts/trial.json').write_text('{}')
    with pytest.raises(ValueError, match='invocation exists'):
        recovery.migrate_legacy_reference_failure(tmp_path, 'old')


def test_transport_retry_budget_persists_and_success_is_cached(tmp_path, monkeypatch):
    import run_etf_autoresearch_campaign as driver
    monkeypatch.setattr(time, 'sleep', lambda _: None)
    calls = []
    class Process:
        returncode = 1
        def __init__(self, command, **kwargs):
            calls.append(command)
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def communicate(self, *args, **kwargs): return '', '503 temporarily unavailable'
    monkeypatch.setattr(driver.subprocess, 'Popen', Process)
    with pytest.raises(RuntimeError, match='budget exhausted'):
        driver.model_json('same frozen request', {}, tmp_path, 'gpt-6.1-sol', 'review')
    with pytest.raises(RuntimeError, match='budget exhausted'):
        driver.model_json('same frozen request', {}, tmp_path, 'gpt-6.1-sol', 'review')
    assert len(calls) == 3
    assert all(command[command.index('--model') + 1] == 'gpt-6.1-sol' for command in calls)
    directory = next((tmp_path / 'review_requests').iterdir())
    recovery.atomic(directory / 'success.json', {'reviews': []})
    assert driver.model_json('same frozen request', {}, tmp_path, 'gpt-6.1-sol', 'review') == {'reviews': []}
    assert len(calls) == 3


def test_oversized_request_never_calls_model(tmp_path, monkeypatch):
    import run_etf_autoresearch_campaign as driver
    monkeypatch.setattr(driver.subprocess, 'Popen', lambda *_a, **_k: pytest.fail('must not send oversized request'))
    with pytest.raises(ValueError, match='too large'):
        driver.model_json('x' * 900001, {}, tmp_path, 'gpt-6.1-sol', 'review')
    receipt = json.loads((tmp_path / 'review_request_error.json').read_text())
    assert receipt['model_called'] is False and receipt['characters'] == 900001


@pytest.mark.parametrize('role,model,budget', [('review', 'gpt-6.1-sol', 300),
    ('plan_review', 'gpt-6.1-sol', 300), ('proposal', 'gpt-6-luna', 180),
    ('family_plan', 'gpt-6-luna', 180)])
def test_timeout_budget_is_role_specific_and_diagnostic_is_retained(tmp_path, monkeypatch, role, model, budget):
    import run_etf_autoresearch_campaign as driver
    monkeypatch.setattr(time, 'sleep', lambda _: None)
    monkeypatch.setattr(driver.os, 'killpg', lambda *_: None)
    calls = []
    class Process:
        pid = 123
        def __init__(self, *_a, **_k): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def communicate(self, prompt=None, timeout=None):
            if prompt is not None:
                calls.append(timeout)
                raise driver.subprocess.TimeoutExpired('codex', timeout)
            return '', 'bounded timeout diagnostic'
    monkeypatch.setattr(driver.subprocess, 'Popen', Process)
    with pytest.raises(RuntimeError, match='budget exhausted'):
        driver.model_json('frozen transport', {}, tmp_path, model, role)
    request = next((tmp_path / f'{role}_requests').iterdir())
    assert calls == [budget] * 3
    assert (request / 'attempt_1/stderr.txt').read_text() == 'bounded timeout diagnostic'
    state = json.loads((request / 'state.json').read_text())
    assert all(a['timeout_seconds'] == budget and a['elapsed_seconds'] >= 0 for a in state['attempts'])


@pytest.mark.parametrize('role,model', [('review', 'gpt-6-sol'), ('plan_review', 'gpt-6-luna'),
                                      ('review', 'gpt-5.6-sol'), ('plan_review', 'gpt-5.6-sol'),
                                      ('proposal', 'gpt-6.1-sol'), ('family_plan', 'gpt-6-sol')])
def test_model_roles_are_enforced_before_transport(tmp_path, monkeypatch, role, model):
    import run_etf_autoresearch_campaign as driver
    monkeypatch.setattr(driver.subprocess, 'Popen', lambda *_a, **_k: pytest.fail('wrong model role must not be called'))
    with pytest.raises(ValueError, match='requires'):
        driver.model_json('request', {}, tmp_path, model, role)


@pytest.mark.parametrize('mutation', ['inputs', 'source', 'scores'])
def test_evaluation_must_match_label_free_preflight(tmp_path, mutation):
    result = {'candidate_sha256': 'frozen-source', 'input_sha256': {'panel': 'frozen-data'}}
    (tmp_path / 'group_scores.csv').write_text('frozen scores')
    receipt = {'contract': {'input_sha256': result['input_sha256']},
               'candidate_sha256': 'frozen-source', 'score_sha256': recovery.sha(tmp_path / 'group_scores.csv')}
    (tmp_path / 'result.json').write_text(json.dumps(result))
    recovery.validate_preflight_result(tmp_path, receipt)
    if mutation == 'inputs':
        result['input_sha256'] = {'panel': 'changed-data'}
    elif mutation == 'source':
        result['candidate_sha256'] = 'changed-source'
    else:
        (tmp_path / 'group_scores.csv').write_text('changed scores')
    (tmp_path / 'result.json').write_text(json.dumps(result))
    with pytest.raises(ValueError, match='mismatch'):
        recovery.validate_preflight_result(tmp_path, receipt)
