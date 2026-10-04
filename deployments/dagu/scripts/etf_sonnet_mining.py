"""Persistent Claude Sonnet 5 mining lane driven by headless Claude Code.

One `claude -p` call per round, resuming the same session id, so the model keeps
its working memory across batches (Claude Code compacts on its own). Same
contract, engine and artifacts as the pi lane; separate run dir, outputs and
directive file. Checkpoint in supervisor_status.json; heartbeat every 30s;
STOP / MECHANISM_EXHAUSTED markers stop the loop; Dagu restarts it.
"""
from pathlib import Path
import argparse
import datetime
import fcntl
import json
import os
import re
import signal
import subprocess
import threading
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run-dir', required=True, type=Path)
parser.add_argument('--model', default='claude-sonnet-5')
parser.add_argument('--round-timeout', type=int, default=5400)
args = parser.parse_args()
R = args.run_dir.resolve()
W = R / 'workspace'
ROUND = None
SESSION = None
PROC = None


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def state(status, **extra):
    payload = dict(status=status, round=ROUND, model=f'claude-code/{args.model}', supervisor_pid=os.getpid(),
                   worker_pid=PROC.pid if PROC and PROC.poll() is None else None, session_id=SESSION,
                   mode='claude_code_headless_resume', updated_at=now())
    payload.update(extra)
    tmp = R / 'supervisor_status.tmp'
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    tmp.replace(R / 'supervisor_status.json')


def heartbeat_loop():
    while True:
        try:
            tmp = R / 'supervisor_heartbeat.tmp'
            tmp.write_text(json.dumps(dict(status='RUNNING', round=ROUND, supervisor_pid=os.getpid(),
                                           worker_pid=PROC.pid if PROC and PROC.poll() is None else None,
                                           updated_at=now())))
            tmp.replace(R / 'supervisor_heartbeat.json')
        except Exception:
            pass
        time.sleep(30)


def completed(n):
    dest = W / 'outputs' / f'round_{n:03d}'
    ex = dest / 'MECHANISM_EXHAUSTED.json'
    if ex.exists():
        e = json.loads(ex.read_text())
        if e.get('status') != 'MECHANISM_EXHAUSTED':
            raise ValueError('invalid exhaustion artifact')
        return e
    s = json.loads((dest / 'STATUS.json').read_text())
    # E28: a worker that reports the stage finished / queue empty without writing the exhaustion
    # artifact would otherwise be re-prompted every minute; treat those statuses as exhaustion.
    st = str(s.get('status', ''))
    if st.startswith(('QUEUE_EMPTY', 'STAGE_COMPLETE', 'STAGE_EXHAUSTED')) and not ex.exists():
        return {'status': 'MECHANISM_EXHAUSTED', 'reason': f'{st} (synthesized by supervisor from STATUS.json)', 'stage': s.get('stage')}
    if int(s.get('n_preregistered') or 0) <= 0 and not s.get('stage'):
        raise ValueError('No completed compute batch')
    rec = {'round': n, 'n_tested': s.get('n_preregistered'), 'n_gate_pass': s.get('n_gate_pass'),
           'status_path': str(dest / 'STATUS.json'), 'evidence': 'worker_report_pending_controller_review', 'lane': 'sonnet'}
    hist = R / 'completed_rounds.jsonl'
    seen = {json.loads(l)['round'] for l in hist.read_text().splitlines()} if hist.exists() else set()
    if n not in seen:
        with hist.open('a') as f:
            f.write(json.dumps(rec) + '\n')
    return s


INCOMPLETE = 0


def current_directive(md):
    """Opening note + standing controller rules + the newest stage block only.

    controller_advance.sh appends every stage block; older blocks are superseded
    ("本块覆盖上方") and stay in the file for audit, not in the prompt.
    """
    blocks = re.split(r'(?m)^(?=## )', md)
    standing = [b for b in blocks[1:] if b.startswith(('## ★ 主控口径更新', '## 主控引擎变更通告'))]
    stages = [b for b in blocks[1:] if b.startswith('## ★ 当前生效')]
    return blocks[0] + ''.join(standing) + (stages[-1] if stages else '')


def instruction():
    text = (f'继续独立 ETF 单因子挖掘：本轮 round_{ROUND:03d}，输出 outputs/round_{ROUND:03d}。'
            '先读本目录 CLAUDE.md（合同与流程）；复用已掌握的引擎与历史，禁止从头重读整个工程。'
            '先锁定此前未测的有限新假设，再实算；不要只回复计划。已有 PLAN 或部分产物则恢复本批，不能覆盖预注册计划。'
            '完成 STATUS.json、candidate_metrics.csv、REPORT.md 并跑归档脚本；收尾简报列本轮预注册数、过门数、异常与产物路径。')
    if INCOMPLETE:
        text = (f'【上一次调用在 round_{ROUND:03d} 未落地 STATUS.json 就返回了（你把计算放到了后台或提前收尾）。'
                'headless 模式下后台任务不会回调。请在本次调用内前台完成 round_{ROUND:03d} 的全部步骤直到 STATUS.json 写出。】\n\n' + text)
    d = R / 'CONTROLLER_DIRECTIVE.md'
    if d.exists():
        text += '\n\n' + current_directive(d.read_text())
    return text


def run_round():
    global PROC, SESSION
    cmd = ['claude', '-p', '--model', args.model, '--permission-mode', 'bypassPermissions',
           '--output-format', 'json', '--add-dir', str(Path(__file__).resolve().parents[3] / "data/etf_rotation_v1"),
           '--add-dir', str(Path(__file__).resolve().parents[3] / "frameworks/etf_rotation"),
           '--append-system-prompt', ('你运行在 headless 非交互模式：本次调用结束即回合结束，后台任务完成后不会再有回调。'
                                      '所有计算必须在前台同步执行直到本轮 STATUS.json 落地；禁止 run_in_background、禁止"等通知再继续"。'
                                      '长计算用前台命令 + 足够的 timeout；禁止 nohup/& 起后台再用 tail -f / sleep 轮询等日志（tail -f 永不退出，只会耗尽工具超时）。')]
    if SESSION:
        cmd += ['--resume', SESSION]
    # prompt goes over stdin: a trailing positional would be swallowed by the variadic --add-dir
    log = (R / 'rounds.log').open('a')
    PROC = subprocess.Popen(cmd, cwd=W, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True, start_new_session=True)
    state('RUNNING')
    try:
        out, _ = PROC.communicate(input=instruction(), timeout=args.round_timeout)
    except subprocess.TimeoutExpired:
        os.killpg(PROC.pid, signal.SIGTERM)
        raise TimeoutError(f'round {ROUND} exceeded {args.round_timeout}s')
    try:
        data = json.loads(out.strip().splitlines()[-1])
    except Exception:
        data = {'raw': out[-2000:]}
    SESSION = data.get('session_id', SESSION)
    with (R / 'round_results.jsonl').open('a') as f:
        f.write(json.dumps({'round': ROUND, 'time': now(), 'session_id': SESSION, 'cost_usd': data.get('total_cost_usd'),
                            'num_turns': data.get('num_turns'), 'is_error': data.get('is_error'),
                            'result_tail': str(data.get('result', data.get('raw', '')))[-1500:]}, ensure_ascii=False) + '\n')
    if data.get('is_error'):
        raise RuntimeError(f'claude -p error: {str(data.get("result"))[:300]}')


def main():
    global ROUND, SESSION
    lock = (R / 'persistent.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    ck = R / 'supervisor_status.json'
    if ck.exists():
        saved = json.loads(ck.read_text())
        ROUND = int(saved.get('round') or 1)
        SESSION = saved.get('session_id')
    else:
        ROUND = int(json.loads((R / 'migration.json').read_text())['round'])
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    # settle rounds finished before a restart
    while (W / 'outputs' / f'round_{ROUND:03d}' / 'STATUS.json').exists() or (W / 'outputs' / f'round_{ROUND:03d}' / 'MECHANISM_EXHAUSTED.json').exists():
        try:
            r = completed(ROUND)
            if r.get('status') == 'MECHANISM_EXHAUSTED':
                (R / 'MECHANISM_EXHAUSTED').write_text(json.dumps({'round': ROUND, 'source': str(W / 'outputs' / f'round_{ROUND:03d}' / 'MECHANISM_EXHAUSTED.json'), 'reason': r.get('reason'), 'created_at': now()}, ensure_ascii=False, indent=2))
                state('WAITING_FOR_NEW_MECHANISM', reason=r.get('reason'))
                return
            ROUND += 1
        except (FileNotFoundError, KeyError, ValueError):
            break
    global INCOMPLETE
    failures = 0
    while not (R / 'STOP').exists():
        INCOMPLETE = failures
        run_round()
        try:
            r = completed(ROUND)
            failures = 0
            if r.get('status') == 'MECHANISM_EXHAUSTED':
                (R / 'MECHANISM_EXHAUSTED').write_text(json.dumps({'round': ROUND, 'source': str(W / 'outputs' / f'round_{ROUND:03d}' / 'MECHANISM_EXHAUSTED.json'), 'reason': r.get('reason'), 'created_at': now()}, ensure_ascii=False, indent=2))
                state('WAITING_FOR_NEW_MECHANISM', reason=r.get('reason'))
                return
            ROUND += 1
        except (FileNotFoundError, KeyError, ValueError) as exc:
            failures += 1
            if failures >= 4:
                raise RuntimeError(f'Four calls without completed batch: {exc}')
        state('BATCH_COMPLETE_CONTINUING', consecutive_incomplete=failures)


if __name__ == '__main__':
    def terminate(signum, frame):
        # Raising from the handler did not unwind communicate() in practice (E20, 2026-09-20):
        # write the checkpoint, kill the worker's process group and exit directly.
        try:
            state('STOPPED', reason=f'signal {signum}; checkpoint retained')
        finally:
            if PROC is not None and PROC.poll() is None:
                try:
                    os.killpg(PROC.pid, signal.SIGTERM)
                except Exception:
                    pass
            os._exit(0)
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        main()
    except BlockingIOError:
        print('Existing sonnet supervisor owns lock; no duplicate started.', flush=True)
    except InterruptedError as exc:
        state('STOPPED', reason=str(exc))
    except Exception as exc:
        state('INSTRUMENT_BLOCKED', reason=str(exc))
        raise
    finally:
        if PROC is not None and PROC.poll() is None:
            os.killpg(PROC.pid, signal.SIGTERM)
