"""Keep one Pi RPC process/session across mining batches; compact at 65%."""
from pathlib import Path
import datetime
import argparse
import fcntl
import json
import os
import queue
import signal
import subprocess
import threading
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run-dir', required=True, type=Path)
args = parser.parse_args()
R = args.run_dir.resolve()
W = R / 'workspace'
THRESHOLD = 65.0
EVENTS = queue.Queue()
PROC = None
ROUND = None
CONTEXT = {}
SESSION = None
PRIOR_PID = None
CURRENT_STATUS = 'STARTING'
LAST_HEARTBEAT = 0.0


def state(status, **extra):
    global CURRENT_STATUS
    CURRENT_STATUS = status
    payload = dict(status=status, round=ROUND, model='zai/glm-5.3-flash',
                   supervisor_pid=os.getpid(), worker_pid=PROC.pid if PROC else None,
                   session_file=SESSION, context_usage=CONTEXT, previous_worker_pid=PRIOR_PID,
                   compact_at_percent=THRESHOLD, mode='persistent_rpc_same_session',
                   updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    payload.update(extra)
    tmp = R / 'supervisor_status.tmp'
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    tmp.replace(R / 'supervisor_status.json')


def heartbeat():
    """Publish liveness independently from round-boundary state changes."""
    global LAST_HEARTBEAT
    now = time.monotonic()
    if now - LAST_HEARTBEAT < 30:
        return
    payload = {
        'status': CURRENT_STATUS,
        'round': ROUND,
        'supervisor_pid': os.getpid(),
        'worker_pid': PROC.pid if PROC else None,
        'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    tmp = R / 'supervisor_heartbeat.tmp'
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    tmp.replace(R / 'supervisor_heartbeat.json')
    LAST_HEARTBEAT = now


def alive(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().split(') ')[1][0] != 'Z'
    except FileNotFoundError:
        return False


def read_events():
    for line in PROC.stdout:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        EVENTS.put(event)
    EVENTS.put({'type': 'process_exit'})


def send(kind, **kw):
    ident = f'{kind}-{time.monotonic_ns()}'
    PROC.stdin.write(json.dumps(dict(type=kind, id=ident, **kw), ensure_ascii=False) + '\n')
    PROC.stdin.flush()
    return ident


def event(timeout=10):
    heartbeat()
    if (R / 'STOP').exists():
        raise InterruptedError('STOP file')
    try:
        e = EVENTS.get(timeout=timeout)
    except queue.Empty:
        heartbeat()
        if PROC.poll() is not None:
            raise RuntimeError(f'Pi exited {PROC.returncode}')
        return {}
    if e.get('type') == 'process_exit':
        raise RuntimeError('Pi stdout closed')
    if e.get('type') in ('agent_settled', 'auto_compaction_start', 'auto_compaction_end'):
        with (R / 'rpc_events.jsonl').open('a') as f:
            f.write(json.dumps({'time':time.time(), 'round':ROUND, 'type':e['type']})+'\n')
    if e.get('type') == 'message_end':
        m = e.get('message', {})
        if m.get('role') == 'assistant':
            with (R / 'rpc_assistant.jsonl').open('a') as f:
                f.write(json.dumps({'round':ROUND, 'message':m}, ensure_ascii=False)+'\n')
    return e


def request(kind, timeout=60, **kw):
    ident = send(kind, **kw)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        e = event()
        if e.get('type') == 'response' and e.get('id') == ident:
            if not e.get('success'):
                raise RuntimeError(f'{kind}: {e.get("error")}')
            return e.get('data', {})
    raise TimeoutError(kind)


def update_usage():
    global CONTEXT, SESSION
    stats = request('get_session_stats')
    CONTEXT = stats.get('contextUsage', {})
    SESSION = stats.get('sessionFile', SESSION)
    with (R / 'context_usage.jsonl').open('a') as f:
        f.write(json.dumps({'time':time.time(), 'round':ROUND, 'session':SESSION,
                            'contextUsage':CONTEXT, 'cumulativeTokens':stats.get('tokens')})+'\n')


def run_prompt(message):
    ident = send('prompt', message=message)
    deadline = time.monotonic() + 3600
    while time.monotonic() < deadline:
        e = event()
        if e.get('type') == 'response' and e.get('id') == ident and not e.get('success'):
            raise RuntimeError(e.get('error'))
        if e.get('type') == 'agent_settled':
            return
    send('abort')
    raise TimeoutError('No settled compute batch after 60 minutes')


def completed(n):
    dest = W / 'outputs' / f'round_{n:03d}'
    exhausted_path = dest / 'MECHANISM_EXHAUSTED.json'
    if exhausted_path.exists():
        exhausted = json.loads(exhausted_path.read_text())
        if exhausted.get('status') != 'MECHANISM_EXHAUSTED':
            raise ValueError(f'Invalid exhaustion artifact: {exhausted_path}')
        return exhausted
    s = json.loads((dest/'STATUS.json').read_text())
    is_census = (
        int(s.get('n_preregistered', -1)) == 0
        and bool(s.get('mechanism_status'))
        and bool(s.get('census_summary'))
    )
    if is_census:
        record = {
            'round': n,
            'n_tested': 0,
            'n_gate_pass': 0,
            'status_path': str(dest/'STATUS.json'),
            'evidence': 'mechanism_census_not_exhaustion_permission',
        }
        history = R/'completed_rounds.jsonl'
        recorded = (
            {json.loads(line)['round'] for line in history.read_text().splitlines()}
            if history.exists() else set()
        )
        if n not in recorded:
            with history.open('a') as f:
                f.write(json.dumps(record)+'\n')
        return s
    if int(s['n_preregistered']) <= 0 or not (dest/'candidate_metrics.csv').exists():
        raise ValueError('No completed compute batch')
    record = {'round':n, 'n_tested':s['n_preregistered'], 'n_gate_pass':s.get('n_gate_pass'),
              'status_path':str(dest/'STATUS.json'), 'evidence':'worker_report_pending_controller_review'}
    history = R/'completed_rounds.jsonl'
    recorded = {json.loads(line)['round'] for line in history.read_text().splitlines()} if history.exists() else set()
    if n not in recorded:
        with history.open('a') as f:
            f.write(json.dumps(record)+'\n')
    return s


def stop_for_exhaustion(result):
    """Persist a clean wait state so the Dagu schedule cannot spin."""
    marker = R / 'MECHANISM_EXHAUSTED'
    marker.write_text(json.dumps({
        'round': ROUND,
        'source': str(W / 'outputs' / f'round_{ROUND:03d}' / 'MECHANISM_EXHAUSTED.json'),
        'reason': result.get('reason'),
        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2))
    state('WAITING_FOR_NEW_MECHANISM', reason=result.get('reason'), marker=str(marker))


def main():
    global PROC, ROUND, SESSION, PRIOR_PID
    lock = (R/'persistent.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    migration = json.loads((R/'migration.json').read_text())
    checkpoint = R/'supervisor_status.json'
    if checkpoint.exists():
        saved = json.loads(checkpoint.read_text())
        if saved.get('session_file'):
            migration = dict(round=saved['round'], session_file=saved['session_file'],
                previous_worker_pid=saved.get('worker_pid') or saved.get('previous_worker_pid') or 0)
    ROUND = migration['round']
    SESSION = migration['session_file']
    PRIOR_PID = migration['previous_worker_pid']
    state('DRAINING_CURRENT_BATCH')
    while alive(migration['previous_worker_pid']):
        if (R/'STOP').exists():
            raise InterruptedError('STOP file while draining')
        time.sleep(3)
    while (
        (W/'outputs'/f'round_{ROUND:03d}'/'STATUS.json').exists()
        or (W/'outputs'/f'round_{ROUND:03d}'/'MECHANISM_EXHAUSTED.json').exists()
    ):
        try:
            result = completed(ROUND)
            if result.get('status') == 'MECHANISM_EXHAUSTED':
                stop_for_exhaustion(result)
                return
            ROUND += 1
        except (FileNotFoundError, KeyError, ValueError):
            break  # Resume the same session and finish the interrupted batch.
    stderr = (R/'rpc.stderr.log').open('a')
    PROC = subprocess.Popen(['pi','--mode','rpc','--provider','zai','--model','glm-5.3-flash',
        '--thinking','high','--no-extensions','--no-skills','--no-context-files',
        '--session',SESSION], cwd=W, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=stderr, text=True, bufsize=1, start_new_session=True)
    threading.Thread(target=read_events, daemon=True).start()
    info = request('get_state')
    if info.get('model',{}).get('id') != 'glm-5.3-flash':
        raise RuntimeError('Unexpected model in resumed session')
    request('set_auto_compaction', enabled=True)
    update_usage()
    first = True
    failures = 0
    while not (R/'STOP').exists():
        percent = CONTEXT.get('percent')
        if percent is not None and percent >= THRESHOLD:
            state('COMPACTING')
            request('compact', timeout=900, customInstructions=(
                '保留ETF冻结人口/时钟/门槛/数据隔离；所有已测表达式、失败原因及产物路径；'
                '已选候选与未测机制队列；数值与证据等级严格区分，严禁把重复实验当新发现。'
                '文件是完整账本，摘要保持下一批可直接运行。'))
            update_usage()
        instruction = (f'继续独立ETF挖掘：本次 round_{ROUND:03d}，输出 outputs/round_{ROUND:03d}。'
            '复用当前会话已掌握的代码、合同和失败经验，禁止从头重读整个工程。'
            '先锁定此前未测的有限新假设，再实算；不要只回复计划。'
            '已有PLAN或部分产物则恢复本批，不能覆盖预注册计划。'
            '完成本批STATUS.json、candidate_metrics.csv及REPORT.md后简报，主控会在同一会话立即接续。'
            '字段兼容 n_preregistered/n_gate_pass/leak_checks。'
            '所有历史尝试累计去重；保持发现层候选身份，不动门槛，不把窗口变体当新家族。'
            '若连续两次同类计算故障则重建单候选最小路径；无新机制则明确说明，不制造重复产出。')
        instruction += (
            f' 若现有冻结输入面确已没有未测且可证伪的新机制，必须写 '
            f'outputs/round_{ROUND:03d}/MECHANISM_EXHAUSTED.json，至少包含 '
            'status="MECHANISM_EXHAUSTED"、reason、tested_scope、next_required_input；'
            '该终态不伪造 PLAN、STATUS 或 candidate_metrics.csv。'
        )
        instruction += (
            ' 机制盘点的零候选 STATUS 可以作为单独一轮记账，但不等于穷尽许可；'
            '若盘点仍显示合法未测表达式，下一轮必须选择一个新的、有限、可证伪机制实算。'
            '仅凭已测少量手选表达式，不得宣布整个两原子空间穷尽；不得重复同一盘点。'
        )
        directive = R / 'CONTROLLER_DIRECTIVE.md'  # controller steers pi without a restart
        if directive.exists():
            instruction += '\n' + directive.read_text()
        if first:
            instruction = ((R/'CONTINUATION.md').read_text()+'\n用户新要求覆盖此前逐批启动安排：'
                '现在同一个RPC进程、同一个会话连续挖多批，只在实际上下文65%时压缩。'
                '无需自己退出进程/开新会话；不要为了凑长度输出冗余内容。\n'+instruction)
            first = False
        state('RUNNING')
        run_prompt(instruction)
        update_usage()
        try:
            result = completed(ROUND)
            if result.get('status') == 'MECHANISM_EXHAUSTED':
                stop_for_exhaustion(result)
                return
            failures = 0
            ROUND += 1
        except (FileNotFoundError, KeyError, ValueError) as exc:
            failures += 1
            if failures >= 2:
                raise RuntimeError(f'Two turns without completed compute batch: {exc}')
        state('BATCH_COMPLETE_CONTINUING', consecutive_incomplete=failures)


if __name__ == '__main__':
    def terminate(signum, frame):
        raise InterruptedError(f'signal {signum}; checkpoint retained for Dagu restart')
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        main()
    except BlockingIOError:
        print('Existing mining supervisor owns lock; no duplicate worker started.', flush=True)
    except InterruptedError as exc:
        state('STOPPED', reason=str(exc))
    except Exception as exc:
        state('INSTRUMENT_BLOCKED', reason=str(exc))
        raise
    finally:
        if PROC is not None and PROC.poll() is None:
            os.killpg(PROC.pid, signal.SIGTERM)
