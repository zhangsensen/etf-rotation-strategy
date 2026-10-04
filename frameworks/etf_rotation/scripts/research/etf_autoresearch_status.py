"""Derive campaign progress from saved evidence, including legacy false completions."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


TERMINAL = {'COMPLETED', 'FAILED', 'REJECTED', 'DUPLICATE', 'DIVERSITY_SKIPPED'}


def campaign_progress(summary, directory=None):
    """Read-only reconciliation; never rewrite an opened historical summary."""
    rows = summary.get('rounds', [])
    records = summary.get('round_records', [])
    errors = {}
    plans = {}
    if directory is not None:
        recovered_plan_paths = {}
        for path in sorted(Path(directory).glob('plan_r*.json')):
            number = int(path.stem.removeprefix('plan_r'))
            plan = json.loads(path.read_text())
            plans[number] = plan
            recoverable_paths = set()
            for attempt in plan.get('planning_attempts', []):
                if not attempt.get('retryable_unsubmitted') or not attempt.get('path'):
                    continue
                attempt_dir = Path(attempt['path']).resolve()
                try:
                    receipt = json.loads((attempt_dir / 'family_plan_request_error.json').read_text())
                except (OSError, ValueError):
                    continue
                if receipt.get('error_type') == 'REQUEST_TOO_LARGE' and receipt.get('model_called') is False:
                    recoverable_paths.add(str(attempt_dir))
            recovered_plan_paths[number] = recoverable_paths
            has_successful_plan = isinstance(plan.get('slots'), list)
            failed = [a for a in plan.get('planning_attempts', []) if a.get('error')
                      and a.get('error_kind') != 'INVALID_RESPONSE'
                      and not (has_successful_plan and a.get('retryable_unsubmitted')
                               and a.get('path') and str(Path(a['path']).resolve()) in recoverable_paths)]
            if failed:
                errors[number] = failed
        # Paused rounds may not yet have a frozen plan.
        for path in sorted(Path(directory).glob('planning_r*_attempt*/result.json')):
            number = int(path.parent.name.split('_')[1][1:])
            outcome = json.loads(path.read_text())
            recovered = (number in plans and isinstance(plans[number].get('slots'), list)
                         and str(path.parent.resolve()) in recovered_plan_paths.get(number, set()))
            if outcome.get('error') and outcome.get('error_kind') != 'INVALID_RESPONSE' and not recovered:
                errors.setdefault(number, []).append({'path': str(path), 'error': outcome['error']})
    for record in records:
        if record.get('status') == 'PLANNING_FAILED':
            errors.setdefault(record['round'], []).append(record)
    for number, failures in errors.items():
        unique = {}
        for failure in failures:
            path = str(failure.get('path', ''))
            if path.endswith('/result.json'):
                path = path[:-len('/result.json')]
            key = str(Path(path).resolve()) if path else json.dumps(failure, sort_keys=True)
            unique[key] = failure
        errors[number] = list(unique.values())
    actual = set()
    for number in range(1, summary.get('requested_rounds', 0) + 1):
        if number in errors:
            continue
        batch = [r for r in rows if r.get('round') == number]
        plan = plans.get(number)
        expected = len(plan['slots']) if plan is not None else None
        if (batch and all(r.get('status') in TERMINAL for r in batch)
                and (expected is None or len(batch) == expected)):
            actual.add(number)
        elif any(r.get('round') == number and r.get('status') == 'EMPTY' for r in records):
            # A true empty round has a saved successful planning result, not an error.
            if plan is not None and not plan['slots'] and (plan.get('planning_attempts') or
                    (plan.get('mode') == 'refine' and plan.get('planning_disposition') == 'NO_ELIGIBLE_PARENT')):
                actual.add(number)
    requested = summary.get('requested_rounds', 0)
    complete = (requested > 0 and len(actual) == requested and not errors
                and summary.get('status') == 'COMPLETED')
    return {
        'recorded_status': summary.get('status'),
        'effective_status': 'COMPLETED' if complete else
                            'INCOMPLETE_PLANNING_ERROR' if errors else
                            'INCOMPLETE' if summary.get('status') == 'COMPLETED' else summary.get('status'),
        'requested_rounds': requested,
        'recorded_completed_rounds': summary.get('completed_rounds', 0),
        'verified_completed_rounds': len(actual),
        'rounds_with_candidates': len({r['round'] for r in rows if r.get('round') is not None}),
        'evaluated_rounds': len({r['round'] for r in rows if r.get('ic_recorded') and r.get('round') is not None}),
        'candidate_records': len(rows),
        'candidate_statuses': dict(Counter(r.get('status') for r in rows)),
        'planning_error_rounds': sorted(errors),
        'planning_failed_request_count': sum(len(v) for v in errors.values()),
        'planning_errors': errors,
        'remaining_rounds': [n for n in range(1, requested + 1) if n not in actual],
        'complete': complete,
    }


def require_complete(summary, directory):
    progress = campaign_progress(summary, directory)
    if not progress['complete']:
        raise RuntimeError('Campaign completion evidence incomplete: ' + json.dumps(progress, ensure_ascii=False))
    return progress
