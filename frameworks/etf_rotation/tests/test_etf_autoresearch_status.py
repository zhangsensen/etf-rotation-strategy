import hashlib
import csv
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/research'))
from etf_autoresearch_status import campaign_progress, require_complete
from report_etf_autoresearch_campaign import report


def test_legacy_false_completion_is_reconciled_without_changing_history(tmp_path):
    directory = tmp_path / 'campaigns/legacy'
    directory.mkdir(parents=True)
    summary = {'campaign_id': 'legacy', 'status': 'COMPLETED', 'requested_rounds': 20,
               'completed_rounds': 20, 'rounds': [{'round': 1, 'run_id': 'r1', 'status': 'COMPLETED',
               'ic': -.015, 'hac_t': -.8, 'n': 12, 'ic_recorded': True,
               'family_plan': {'direction': 1, 'formula': 'frozen formula'}}],
               'round_records': [{'round': i, 'status': 'EMPTY'} for i in range(2, 21)]}
    path = directory / 'summary.json'
    path.write_text(json.dumps(summary))
    original_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    for i in range(2, 21):
        (directory / f'plan_r{i:02d}.json').write_text(json.dumps({
            'slots': [], 'planning_attempts': [{'error': 'model request too large'}]}))
    progress = campaign_progress(summary, directory)
    assert progress['verified_completed_rounds'] == 1
    assert progress['remaining_rounds'] == list(range(2, 21))
    assert progress['effective_status'] == 'INCOMPLETE_PLANNING_ERROR'
    with pytest.raises(RuntimeError, match='completion evidence incomplete'):
        require_complete(summary, directory)
    output = tmp_path / 'report'
    report(directory, output)
    assert '-0.015000' in (output / 'REPORT.md').read_text()
    assert 'frozen formula' in (output / 'candidates.csv').read_text()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original_hash


def test_genuine_empty_round_and_repaired_response_are_not_system_failures(tmp_path):
    summary = {'status': 'COMPLETED', 'requested_rounds': 1, 'completed_rounds': 1,
               'rounds': [], 'round_records': [{'round': 1, 'status': 'EMPTY'}]}
    (tmp_path / 'plan_r01.json').write_text(json.dumps({'slots': [], 'planning_attempts': [
        {'error': 'invalid response', 'error_kind': 'INVALID_RESPONSE'}, {'error': None}]}))
    assert campaign_progress(summary, tmp_path)['complete']


def test_unfinished_candidate_cannot_be_counted_as_completed_round(tmp_path):
    summary = {'status': 'COMPLETED', 'requested_rounds': 1, 'completed_rounds': 1,
               'rounds': [{'round': 1, 'status': 'COMPLETED'}, {'round': 1, 'status': 'FROZEN'}]}
    assert not campaign_progress(summary, tmp_path)['complete']


def test_candidate_report_keeps_lifecycle_status_separate_from_result_evidence(tmp_path):
    campaign = tmp_path / 'campaigns/c'
    campaign.mkdir(parents=True)
    summary = {'campaign_id': 'c', 'status': 'COMPLETED', 'requested_rounds': 1,
        'completed_rounds': 1, 'rounds': [{
            'round': 1, 'run_id': 'r1', 'candidate': 'factor_one', 'status': 'COMPLETED',
            'reason_code': 'approved', 'family_plan': {
                'direction': -1, 'formula': 'rank(amount.diff(5), axis=ETF)'}}],
        'round_records': []}
    (campaign / 'summary.json').write_text(json.dumps(summary))
    result_dir = tmp_path / 'r1'
    result_dir.mkdir()
    (result_dir / 'result.json').write_text(json.dumps({
        'run_id': 'r1', 'candidate': 'factor_one', 'status': 'SEEN_HISTORY_DISCOVERY_ONLY',
        'direction': -1, 'ic': -.023, 'hac_t': -2.2, 'n': 251,
        'first_signal': '2025-01-02', 'last_signal': '2026-03-24'}))

    output = tmp_path / 'report'
    report(campaign, output)
    with (output / 'candidates.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    row = rows[0]
    assert row['status'] == 'COMPLETED'
    assert row['result_evidence_status'] == 'SEEN_HISTORY_DISCOVERY_ONLY'
    assert row['formula'] == 'rank(amount.diff(5), axis=ETF)'
    assert row['direction'] == '-1'
    assert row['ic'] == '-0.023' and row['first_signal'] == '2025-01-02'


def test_request_error_is_counted_once_across_relative_and_absolute_references(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    directory = Path('campaigns/c')
    attempt = directory / 'planning_r01_attempt1'
    attempt.mkdir(parents=True)
    outcome = {'specs': [], 'error': 'request too large'}
    (attempt / 'result.json').write_text(json.dumps(outcome))
    (directory / 'plan_r01.json').write_text(json.dumps({'slots': [], 'planning_attempts': [
        {'path': str(attempt.resolve()), 'error': outcome['error']}]}))
    summary = {'status': 'COMPLETED', 'requested_rounds': 1,
               'rounds': [], 'round_records': [{'round': 1, 'status': 'EMPTY'}]}
    assert campaign_progress(summary, directory)['planning_failed_request_count'] == 1
