#!/usr/bin/env bash
# One controller tick (runs from Dagu every 5 min, idempotent):
#  1. exhaustion -> apply next staged directive and restart the mining DAG
#  2. new rounds with admissions -> controller_verify (skip if already verified)
#  3. refresh untested-pairs feed, archive code (only when a new round landed)
set -uo pipefail
ROOT=/home/sensen/dev/projects/gpu_ml-coral; R=${ETF_RUN_DIR:-$ROOT/runtime_outputs/etf_pi_glm_mining_20260919}; A=$ROOT/frameworks/etf_rotation/scripts/research/pi_glm_mining/audit
PY=$ROOT/.venv/bin/python; cd $ROOT
if [ -f "$R/MECHANISM_EXHAUSTED" ]; then
  adv=$(bash $A/controller_advance.sh 2>&1 | tail -1); echo "$adv"
  case "$adv" in QUEUE_EMPTY*) $PY $A/controller_alert.py queue_empty "队列空，线停在 WAITING_FOR_NEW_MECHANISM（$adv）。需要主控/USER 放阶段文件或定口径。";; ADVANCED*|REJECTED*) $PY $A/controller_alert.py clear queue_empty;; esac
fi
new=0
MIG=$([ -f $R/migration.json ] && $PY -c "import json;print(int(json.load(open('$R/migration.json'))['round']))" || echo 0)
for d in $(ls $R/workspace/outputs | grep '^round_' | sort); do
  f=$R/workspace/outputs/$d/STATUS.json; [ -f "$f" ] || continue
  [ "${d#round_}" -lt "$MIG" ] 2>/dev/null && continue   # inherited copies from another lane
  grep -qx "$d" $R/controller_seen_rounds 2>/dev/null && continue
  new=1
  npass=$($PY -c "import json;print(json.load(open('$f')).get('n_gate_pass') or 0)")
  if [ "$npass" != "0" ] && [ ! -f "$R/workspace/outputs/$d/controller_verification.json" ]; then
    # E27: verification runs DETACHED (heavy families take 15+ min and were blocking the tick and the
    # stage advance). One verify per round at a time (pid lock); the round stays unseen until the file lands.
    lock="$R/workspace/outputs/$d/controller_verify.pid"
    if [ -f "$lock" ] && kill -0 "$(cat "$lock" 2>/dev/null)" 2>/dev/null; then echo "VERIFY_PENDING $d (pid $(cat "$lock"))"; continue; fi
    if [ -f "$lock" ]; then echo "VERIFY_FAILED $d (see controller_verify.stderr); retrying"; fi
    nohup timeout 3600 $PY $A/controller_verify.py "$R/workspace/outputs/$d" >"$R/workspace/outputs/$d/controller_verify.log" 2>"$R/workspace/outputs/$d/controller_verify.stderr" &
    echo $! > "$lock"; echo "VERIFY_STARTED $d (pid $!)"; continue
  fi
  if [ "$npass" != "0" ]; then
    tail -1 "$R/workspace/outputs/$d/controller_verify.log" 2>/dev/null | sed "s/^/VERIFY $d: /"; rm -f "$R/workspace/outputs/$d/controller_verify.pid"
    grep -q '"verdict": "MISMATCH"' "$R/workspace/outputs/$d/controller_verification.json" && $PY $A/controller_alert.py "mismatch_$d" "$d 入选候选交叉验证 MISMATCH，需人工核。"
  fi
  echo "$d" >> $R/controller_seen_rounds
  echo "TICK: $d landed n_pass=$npass"
done
if [ "$new" = "1" ]; then $PY $A/build_untested_pairs.py 2>&1 | tail -3 | sed 's/^/PAIRS: /'; bash $ROOT/frameworks/etf_rotation/scripts/research/pi_glm_mining/archive_pi_code.sh >/dev/null 2>&1; fi
# backfill (E25): admitted rounds that predate the verifier get cross-checked one per tick
bf=$(for d in $(ls $R/workspace/outputs | grep '^round_' | sort); do f=$R/workspace/outputs/$d/STATUS.json; [ -f "$f" ] || continue; [ "${d#round_}" -lt "$MIG" ] 2>/dev/null && continue; [ -f "$R/workspace/outputs/$d/controller_verification.json" ] && continue; n=$($PY -c "import json;print(json.load(open('$f')).get('n_gate_pass') or 0)"); [ "$n" != "0" ] && { echo $d; break; }; done)
if [ -n "$bf" ] && ! pgrep -f "[c]ontroller_verify.py $R/" >/dev/null; then nohup timeout 3600 $PY $A/controller_verify.py "$R/workspace/outputs/$bf" >"$R/workspace/outputs/$bf/controller_verify.log" 2>"$R/workspace/outputs/$bf/controller_verify.stderr" & echo "BACKFILL_VERIFY_STARTED $bf (pid $!)"; fi
# hourly self-test (E25): schema/guard/pairs/engine/data/queue/supervisor regression over both lanes
if [ "$(date +%M)" -lt 5 ] && [ "${ETF_ARCHIVE_LANE:-pi}" = "pi" ]; then
  st=$(timeout 1500 $PY $A/controller_selftest.py --quick 2>&1 | tail -1); echo "SELFTEST: $st"
  case "$st" in *FAILED*) $PY $A/controller_alert.py selftest_failed "主控自检失败：$st";; *) $PY $A/controller_alert.py clear selftest_failed;; esac
fi
# heartbeat guard: RUNNING but heartbeat > 10 min old -> log (Dagu's own */5 restart of the mining DAG handles a dead supervisor)
$PY - <<'P'
import json,datetime,pathlib
import os; R=pathlib.Path(os.environ.get('ETF_RUN_DIR','/home/sensen/dev/projects/gpu_ml-coral/runtime_outputs/etf_pi_glm_mining_20260919'))
try:
    d=json.load(open(R/'supervisor_status.json')); h=json.load(open(R/'supervisor_heartbeat.json'))
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(h['updated_at'])).total_seconds()
    print(f"STATE {d['status']} round {d['round']} ctx {(d.get('context_usage') or {}).get('percent') or 0:.1f}% heartbeat_age {int(age)}s")
    if d['status']=='RUNNING' and age>600:
        print('WARN heartbeat stale > 600s'); import subprocess; subprocess.run([sys.executable if False else '/home/sensen/dev/projects/gpu_ml-coral/.venv/bin/python','/home/sensen/dev/projects/gpu_ml-coral/frameworks/etf_rotation/scripts/research/pi_glm_mining/audit/controller_alert.py','heartbeat_stale',f'supervisor 心跳 {int(age)}s 未更新（RUNNING round {d["round"]}），可能卡死。'])
    if d['status']=='INSTRUMENT_BLOCKED':
        import subprocess; subprocess.run(['/home/sensen/dev/projects/gpu_ml-coral/.venv/bin/python','/home/sensen/dev/projects/gpu_ml-coral/frameworks/etf_rotation/scripts/research/pi_glm_mining/audit/controller_alert.py','instrument_blocked',f'supervisor INSTRUMENT_BLOCKED: {str(d.get("reason",""))[:150]}'])
except Exception as e: print('STATE unreadable',e)
P
