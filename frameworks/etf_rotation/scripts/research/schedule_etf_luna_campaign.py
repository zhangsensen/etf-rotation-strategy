"""One authorized Dagu campaign, with an immutable budget and safe restart checks."""
from __future__ import annotations

import argparse
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from etf_autoresearch_status import require_complete
from etf_autoresearch_workflow import POLICY

ROOT = Path(__file__).resolve().parents[4]
OUTPUT = ROOT / 'runtime_outputs/etf_autoresearch_ic'


def state(output: Path, campaign: str) -> dict | None:
    if not campaign.replace('_', '').replace('-', '').isalnum():
        raise ValueError('invalid campaign identifier')
    path = output / 'campaigns' / campaign / 'summary.json'
    return json.loads(path.read_text()) if path.exists() else None


def disposition(output: Path, predecessor: str, campaign: str, rounds: int = 20, width: int = 4) -> str:
    target = state(output, campaign)
    if target:
        require_target_contract(target, rounds, width)
        if target.get('status') == 'COMPLETED':
            require_complete(target, output / 'campaigns' / campaign)
            return 'DONE'
        raise RuntimeError('Target campaign already exists; inspect it before any explicit resume')
    previous = state(output, predecessor)
    if not previous:
        raise RuntimeError('Predecessor summary is missing')
    if previous.get('status') != 'COMPLETED':
        raise RuntimeError(f"Predecessor did not complete: {previous.get('status')}")
    if previous.get('completed_rounds') != previous.get('requested_rounds'):
        raise RuntimeError('Predecessor round budget is incomplete')
    require_complete(previous, output / 'campaigns' / predecessor)
    return 'START'


def require_target_contract(summary, rounds, width):
    expected = {'requested_rounds': rounds, 'candidates_per_round': width, 'mode': 'open',
                'model': 'gpt-6-luna', 'reviewer': 'gpt-6.1-sol', 'scheduling_policy': POLICY}
    for key, value in expected.items():
        if summary.get(key) != value:
            raise RuntimeError(f'Target campaign contract changed: {key}')


def can_resume(summary, output=OUTPUT):
    if summary.get('scheduling_policy') != POLICY:
        return False
    if summary.get('status') == 'COMPLETED':
        return False  # Finished campaigns are verified by the caller, never resumed.
    if any(r.get('status') == 'PLANNING_FAILED' for r in summary.get('round_records', [])):
        return False
    for row in summary.get('rounds', []):
        if row.get('repair_pending'):
            return False
        if row.get('status') == 'PAUSED_SYSTEM_ERROR' and row.get('stage') != 'result_saved':
            return False
        if row.get('status') in {'OUTCOME_OPENED', 'EVALUATING', 'RESULT_READY'} or (
                row.get('status') == 'PAUSED_SYSTEM_ERROR' and row.get('stage') == 'result_saved'):
            if not (output / row['run_id'] / 'evaluation_complete.json').exists():
                return False
    if summary.get('status') not in {'RUNNING', 'INTERRUPTED', 'PAUSED_SYSTEM_ERROR'}:
        return False
    if summary.get('status') == 'PAUSED_SYSTEM_ERROR' and not any(r.get('stage') == 'result_saved' for r in summary.get('rounds', [])):
        return False
    errors = summary.get('interruptions', [])
    if errors and any(token in errors[-1].get('error', '').lower() for token in
                      ('budget exhausted', 'authentication', 'unauthorized', 'request too large')):
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--after', required=True)
    parser.add_argument('--campaign-id', required=True)
    parser.add_argument('--rounds', type=int, required=True)
    parser.add_argument('--candidates-per-round', type=int, default=4)
    parser.add_argument('--check-only', action='store_true', help='validate launch state without starting a model or evaluation')
    args = parser.parse_args()
    if not 1 <= args.rounds <= 100 or not 1 <= args.candidates_per_round <= 8:
        raise ValueError('rounds must be 1..100 and candidates per round 1..8')
    if args.after == args.campaign_id:
        raise ValueError('New campaign must have a distinct identity')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / '.dagu-launch.lock').open('a') as launch:
        fcntl.flock(launch, fcntl.LOCK_EX | fcntl.LOCK_NB)
        deadline = time.monotonic() + 86400
        with (OUTPUT / '.campaign.lock').open('a') as research:
            while True:
                try:
                    fcntl.flock(research, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Research lock remained busy for 24 hours')
                    print(f'WAITING_LOCK: {args.campaign_id}', flush=True)
                    time.sleep(30)
            predecessor = state(OUTPUT, args.after)
            if not predecessor or predecessor.get('status') != 'COMPLETED':
                raise RuntimeError('Predecessor did not complete; it will not be launched or resumed')
            require_complete(predecessor, OUTPUT / 'campaigns' / args.after)
            previous = state(OUTPUT, args.campaign_id)
            if previous:
                require_target_contract(previous, args.rounds, args.candidates_per_round)
                if previous.get('status') == 'COMPLETED':
                    require_complete(previous, OUTPUT / 'campaigns' / args.campaign_id)
                    print('DONE: authorized campaign already complete; no additional budget', flush=True)
                    return
                if not can_resume(previous, OUTPUT):
                    raise RuntimeError('MANUAL_INSPECTION: no safe automatic recovery point')
            if args.check_only:
                print(json.dumps({'action': 'RESUME' if previous else 'START',
                    'campaign_id': args.campaign_id, 'rounds': args.rounds,
                    'candidates_per_round': args.candidates_per_round,
                    'after': args.after, 'model': 'gpt-6-luna', 'reviewer': 'gpt-6.1-sol',
                    'labels_opened': False}), flush=True)
                return
            fcntl.flock(research, fcntl.LOCK_UN)
        command = [sys.executable, '-u', str(Path(__file__).with_name('run_etf_autoresearch_campaign.py')),
                   '--campaign-id', args.campaign_id, '--rounds', str(args.rounds),
                   '--candidates-per-round', str(args.candidates_per_round),
                   '--mode', 'open', '--profiles', 'all', '--model', 'gpt-6-luna', '--reviewer', 'gpt-6.1-sol']
        if previous:
            command.append('--resume')
        print('STARTING: ' + ' '.join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
        completed = state(OUTPUT, args.campaign_id)
        if not completed:
            raise RuntimeError('INCOMPLETE: target summary missing')
        require_target_contract(completed, args.rounds, args.candidates_per_round)
        require_complete(completed, OUTPUT / 'campaigns' / args.campaign_id)
        print('COMPLETED: authorized campaign; no additional budget', flush=True)


if __name__ == '__main__':
    main()
