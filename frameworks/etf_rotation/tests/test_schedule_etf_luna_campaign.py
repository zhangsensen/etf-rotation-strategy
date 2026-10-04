import importlib.util
import json
from pathlib import Path

import pytest

FILE = Path(__file__).resolve().parents[1] / 'scripts/research/schedule_etf_luna_campaign.py'
SPEC = importlib.util.spec_from_file_location('scheduled_luna', FILE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def put(root, name, status, completed=20, requested=20):
    path = root / 'campaigns' / name / 'summary.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'status': status, 'completed_rounds': completed, 'requested_rounds': requested,
        'candidates_per_round': 4, 'mode': 'open', 'model': 'gpt-6-luna',
        'reviewer': 'gpt-6.1-sol', 'scheduling_policy': MODULE.POLICY,
        'rounds': [{'round': i, 'status': 'COMPLETED'} for i in range(1, completed + 1)]}))


def test_completed_predecessor_can_start_only_once(tmp_path):
    put(tmp_path, 'prior', 'COMPLETED')
    assert MODULE.disposition(tmp_path, 'prior', 'new') == 'START'
    put(tmp_path, 'new', 'COMPLETED')
    assert MODULE.disposition(tmp_path, 'prior', 'new') == 'DONE'


@pytest.mark.parametrize('status', ['RUNNING', 'INTERRUPTED', 'PAUSED_SYSTEM_ERROR'])
def test_incomplete_campaigns_are_not_replayed(tmp_path, status):
    put(tmp_path, 'prior', status, 2)
    with pytest.raises(RuntimeError, match='Predecessor did not complete'):
        MODULE.disposition(tmp_path, 'prior', 'new')
    put(tmp_path, 'prior', 'COMPLETED')
    put(tmp_path, 'new', status, 2)
    with pytest.raises(RuntimeError, match='already exists'):
        MODULE.disposition(tmp_path, 'prior', 'new')


def test_missing_predecessor_does_not_start(tmp_path):
    with pytest.raises(RuntimeError, match='missing'):
        MODULE.disposition(tmp_path, 'prior', 'new')


def test_five_round_predecessor_can_launch_fifty_once(tmp_path, monkeypatch):
    put(tmp_path, 'prior5', 'COMPLETED', completed=5, requested=5)
    monkeypatch.setattr(MODULE, 'OUTPUT', tmp_path)
    monkeypatch.setattr(MODULE.sys, 'argv', ['schedule', '--after', 'prior5',
        '--campaign-id', 'new50', '--rounds', '50'])
    calls = []
    def execute(command, **kwargs):
        calls.append(command)
        assert command[command.index('--rounds') + 1] == '50'
        assert command[command.index('--campaign-id') + 1] == 'new50'
        assert '--resume' not in command
        put(tmp_path, 'new50', 'COMPLETED', completed=50, requested=50)
    monkeypatch.setattr(MODULE.subprocess, 'run', execute)
    MODULE.main()
    MODULE.main()
    assert len(calls) == 1
    assert MODULE.state(tmp_path, 'prior5')['completed_rounds'] == 5


def test_check_only_does_not_start_work_and_changed_budget_is_rejected(tmp_path, monkeypatch):
    put(tmp_path, 'prior5', 'COMPLETED', completed=5, requested=5)
    monkeypatch.setattr(MODULE, 'OUTPUT', tmp_path)
    monkeypatch.setattr(MODULE.sys, 'argv', ['schedule', '--after', 'prior5',
        '--campaign-id', 'new50', '--rounds', '50', '--check-only'])
    monkeypatch.setattr(MODULE.subprocess, 'run', lambda *_a, **_k: pytest.fail('read-only preflight'))
    MODULE.main()
    assert MODULE.state(tmp_path, 'new50') is None
    put(tmp_path, 'new50', 'COMPLETED', completed=20, requested=20)
    with pytest.raises(RuntimeError, match='contract changed: requested_rounds'):
        MODULE.main()


@pytest.mark.parametrize('status', ['EVALUATING', 'OUTCOME_OPENED', 'RESULT_READY', 'PAUSED_SYSTEM_ERROR'])
def test_unsealed_opened_result_never_resumes(tmp_path, status):
    summary = {'status': 'INTERRUPTED', 'scheduling_policy': MODULE.POLICY,
               'rounds': [{'status': status, 'run_id': 'opened', 'stage': 'result_saved'}]}
    assert not MODULE.can_resume(summary, tmp_path)


def test_unopened_interruption_can_resume_but_repair_and_transport_exhaustion_pause(tmp_path):
    summary = {'status': 'INTERRUPTED', 'scheduling_policy': MODULE.POLICY,
               'rounds': [{'status': 'FROZEN'}]}
    assert MODULE.can_resume(summary, tmp_path)
    summary['rounds'][0]['repair_pending'] = True
    assert not MODULE.can_resume(summary, tmp_path)
    summary['rounds'][0]['repair_pending'] = False
    summary['interruptions'] = [{'error': 'model transport retry budget exhausted'}]
    assert not MODULE.can_resume(summary, tmp_path)
