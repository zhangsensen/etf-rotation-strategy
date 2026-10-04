"""Durable execution helpers; never change factor scores or IC arithmetic."""
from __future__ import annotations
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import signal
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def immutable_source(path, source):
    path = Path(path)
    if path.exists():
        if path.read_text() != source:
            raise ValueError(f'frozen source mismatch: {path}')
        return
    with path.open('x') as handle:
        handle.write(source)
        handle.flush()
        os.fsync(handle.fileno())


def reference_id(campaign, profile, source, contract):
    key = json.dumps([profile, hashlib.sha256(source.encode()).hexdigest(), contract], sort_keys=True)
    return campaign + '_ref_' + hashlib.sha256(key.encode()).hexdigest()


def seal_result(directory):
    directory = Path(directory)
    names = ('result.json', 'daily_ic.csv', 'group_scores.csv')
    value = {'files': {name: sha(directory / name) for name in names}}
    path = directory / 'evaluation_complete.json'
    if path.exists() and json.loads(path.read_text()) != value:
        raise ValueError('evaluation result hash mismatch')
    atomic(path, value)


def validate_result(directory, source_hash, profile, root, *, legacy=False):
    directory, root = Path(directory), Path(root)
    marker = directory / 'evaluation_complete.json'
    if not marker.exists() and not legacy:
        raise ValueError('evaluation completion receipt missing')
    if marker.exists():
        receipt = json.loads(marker.read_text())
        if set(receipt['files']) != {'result.json', 'daily_ic.csv', 'group_scores.csv'}:
            raise ValueError('evaluation completion receipt incomplete')
        if any(sha(directory / name) != digest for name, digest in receipt['files'].items()):
            raise ValueError('evaluation result hash mismatch')
    result = json.loads((directory / 'result.json').read_text())
    if result['candidate_sha256'] != source_hash or result.get('input_profile', 'daily') != profile:
        raise ValueError('reference source/profile mismatch')
    from run_etf_autoresearch_ic import GROUPS, UNIVERSE
    import run_etf_autoresearch_ic as evaluator
    if (result.get('python_version') != evaluator.sys.version or
            result.get('pandas_version') != evaluator.pd.__version__ or
            result.get('numpy_version') != evaluator.np.__version__):
        raise ValueError('evaluation runtime contract mismatch')
    if (result['evaluator_sha256'] != sha(root / 'frameworks/etf_rotation/scripts/research/run_etf_autoresearch_ic.py')
            or result['groups_sha256'] != sha(GROUPS) or result['universe_sha256'] != sha(UNIVERSE)):
        raise ValueError('evaluation contract mismatch')
    for name, digest in {**result['input_sha256'], **result['implementation_sha256']}.items():
        path = Path(name) if Path(name).is_absolute() else root / name
        if sha(path) != digest:
            raise ValueError(f'evaluation input/implementation hash mismatch: {name}')
    for name in ('daily_ic.csv', 'group_scores.csv'):
        if not (directory / name).is_file():
            raise ValueError('evaluation output missing')
    return result


def validate_preflight_result(directory, receipt):
    """The evaluated scores and inputs must be those checked before labels opened."""
    directory = Path(directory)
    result = json.loads((directory / 'result.json').read_text())
    if any(result.get(key) != value for key, value in receipt['contract'].items()):
        raise ValueError('preflight/evaluation input contract mismatch')
    if result.get('candidate_sha256') != receipt['candidate_sha256']:
        raise ValueError('preflight/evaluation candidate source mismatch')
    if sha(directory / 'group_scores.csv') != receipt['score_sha256']:
        raise ValueError('preflight/evaluation score hash mismatch')
    return result


class EvaluationTimeout(TimeoutError):
    pass


def _worker(pipe, function, args, kwargs):
    os.setsid()
    try:
        pipe.send((True, function(*args, **kwargs)))
    except BaseException as exc:
        pipe.send((False, exc))
    finally:
        pipe.close()


def bounded_call(function, *args, timeout=300, **kwargs):
    context = multiprocessing.get_context('spawn')
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(sender, function, args, kwargs))
    process.start()
    sender.close()
    try:
        if not receiver.poll(timeout):
            raise EvaluationTimeout(f'evaluation exceeded {timeout} seconds')
        success, value = receiver.recv()
        if not success:
            raise value
        return value
    finally:
        if process.is_alive():
            process.join(timeout=1)
        if process.is_alive():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                process.kill()
        process.join()
        receiver.close()


def evaluation_contract(diagnostics):
    import run_etf_autoresearch_ic as evaluator
    paths = [Path(evaluator.__file__), evaluator.GROUPS, evaluator.UNIVERSE,
             evaluator.DATA / '1d/510300.SH.parquet']
    for item in json.loads(evaluator.UNIVERSE.read_text())['etfs']:
        if item['role'] == 'candidate':
            paths.extend(evaluator.DATA / folder / (item['ts_code'] + '.parquet')
                         for folder in ('1d', 'adj_factor'))
    paths.extend(Path(module.__file__) for module in (evaluator.engine, evaluator.etf_mining_referee,
                                                     evaluator.etf_rank_utils, evaluator.canonical_data))
    return {'files': {str(p): sha(p) for p in paths},
            'inputs': {k: v.get('input_manifest') for k, v in (diagnostics or {}).items()},
            'python': evaluator.sys.version, 'pandas': evaluator.pd.__version__,
            'numpy': evaluator.np.__version__}


def migrate_legacy_reference_failure(output, campaign):
    """One audited correction for the proven pre-evaluation v6 seed collision."""
    output = Path(output)
    summary_path = output / 'campaigns' / campaign / 'summary.json'
    summary = json.loads(summary_path.read_text())
    changed = []
    for row in summary['rounds']:
        if row.get('status') != 'PAUSED_SYSTEM_ERROR':
            continue
        if row.get('error') != 'PAUSED_SYSTEM_ERROR: baseline seed failed: resumed reference source differs':
            raise ValueError('not the audited legacy reference collision')
        if (output / row['run_id']).exists() or (output / 'attempts' / (row['run_id'] + '.json')).exists():
            raise ValueError('candidate invocation exists; cannot declare it unopened')
        source = Path(row['source_path'])
        if sha(source) != row['candidate_sha256'] or not row.get('review', {}).get('approved'):
            raise ValueError('frozen source or approval does not match')
        changed.append({'run_id': row['run_id'], 'previous_status': row['status'],
                        'previous_outcome_opened': row.get('outcome_opened'), 'error': row['error'],
                        'candidate_sha256': row['candidate_sha256'],
                        'evidence': 'baseline-only failure; no evaluation invocation or output directory'})
        row.update(status='FROZEN', stage='reviewed', candidate_evaluation_started=False,
                   legacy_outcome_flag_corrected=True)
    if not changed:
        return False
    receipt = summary_path.parent / 'legacy_reference_recovery.json'
    if receipt.exists():
        raise ValueError('migration receipt already exists; inspect instead of repeating')
    atomic(receipt, {'changes': changed, 'old_summary_sha256': sha(summary_path)})
    summary['status'] = 'INTERRUPTED'
    summary.setdefault('migrations', []).append(str(receipt))
    atomic(summary_path, summary)
    return True
