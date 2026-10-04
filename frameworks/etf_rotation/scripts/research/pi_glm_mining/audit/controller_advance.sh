#!/usr/bin/env bash
# On MECHANISM_EXHAUSTED: validate the declaration (exhaustion_guard.py); if
# invalid, archive as REJECTED, append a rejection note to the directive and
# restart the mining DAG. If valid, archive the marker, advance the checkpoint,
# append the next staged directive from DIRECTIVE_QUEUE (alphabetical) and
# restart. Prints one line; QUEUE_EMPTY leaves the line waiting.
set -euo pipefail
ROOT=/home/sensen/dev/projects/gpu_ml-coral; R=${ETF_RUN_DIR:-$ROOT/runtime_outputs/etf_pi_glm_mining_20260919}
A=$ROOT/frameworks/etf_rotation/scripts/research/pi_glm_mining/audit
export DAGU_HOME=/home/sensen/.config/dagu-gpuml
[ -f "$R/MECHANISM_EXHAUSTED" ] || { echo "NO_MARKER"; exit 0; }
rnd=$(python3 -c "import json;print(json.load(open('$R/MECHANISM_EXHAUSTED'))['round'])")
stamp=$(date +%H%M%S)

bump_checkpoint() {  # $1 = round, $2 = reason
  python3 - "$R" "$1" "$2" <<'PY'
import json, sys
R, rnd, reason = sys.argv[1], int(sys.argv[2]), sys.argv[3]
p = f"{R}/supervisor_status.json"; d = json.load(open(p))
d["round"] = rnd + 1; d["status"] = "REOPENED_BY_CONTROLLER"; d["reason"] = reason
json.dump(d, open(p, "w"), ensure_ascii=False, indent=2)
PY
}

verdict=$(python3 "$A/exhaustion_guard.py" "$R")
# controller-manual acceptance (logged in the directive): CONTROLLER_ACCEPT_EXHAUSTION="<reason>"
if [ -n "${CONTROLLER_ACCEPT_EXHAUSTION:-}" ]; then echo "（主控手动接受穷尽，$(date '+%F %T')）round_$(printf %03d "$rnd")：$CONTROLLER_ACCEPT_EXHAUSTION（守卫原判 $verdict）" >> "$R/CONTROLLER_DIRECTIVE.md"; verdict=OK; fi
if [ "$verdict" != "OK" ]; then
  mv "$R/MECHANISM_EXHAUSTED" "$R/MECHANISM_EXHAUSTED.round$(printf %03d "$rnd").REJECTED.$stamp"
  bump_checkpoint "$rnd" "exhaustion rejected by guard: $verdict"
  {
    echo
    echo "（主控驳回，$(date '+%F %T')）round_$(printf %03d "$rnd") 的穷尽宣布无效：$verdict。按\"当前生效\"块执行：先实现并验证阶段算子；只有连续 3 轮门 7 零入选才算穷尽。"
  } >> "$R/CONTROLLER_DIRECTIVE.md"
  nohup dagu start ${ETF_MINING_DAG:-/home/sensen/.config/dagu-gpuml/dags/etf_pi_glm_mining.yaml} >/dev/null 2>&1 &
  echo "REJECTED round=$rnd $verdict"; exit 0
fi

next=$(ls "$R/DIRECTIVE_QUEUE"/*.md 2>/dev/null | grep -v "/applied_" | sort -V | head -1 || true)
if [ -z "$next" ]; then echo "QUEUE_EMPTY round=$rnd (line stays WAITING_FOR_NEW_MECHANISM)"; exit 0; fi
mv "$R/MECHANISM_EXHAUSTED" "$R/MECHANISM_EXHAUSTED.round$(printf %03d "$rnd").archived.$stamp"
bump_checkpoint "$rnd" "auto-advance after round $rnd exhaustion"
python3 - "$R" "$rnd" <<'PY'
import json, sys, datetime
R, rnd = sys.argv[1], int(sys.argv[2])
open(f"{R}/completed_rounds.jsonl", "a").write(json.dumps({
    "round": f"MECHANISM_EXHAUSTED_round{rnd:03d}", "n_tested": 0, "n_gate_pass": 0,
    "status_path": f"{R}/workspace/outputs/round_{rnd:03d}/MECHANISM_EXHAUSTED.json",
    "evidence": "auto_advanced_by_controller",
    "at": datetime.datetime.now(datetime.timezone.utc).isoformat()}) + "\n")
PY
cat "$next" >> "$R/CONTROLLER_DIRECTIVE.md"; mv "$next" "$R/DIRECTIVE_QUEUE/applied_$(basename "$next")"
nohup dagu start ${ETF_MINING_DAG:-/home/sensen/.config/dagu-gpuml/dags/etf_pi_glm_mining.yaml} >/dev/null 2>&1 &
echo "ADVANCED round=$rnd applied=$(basename "$next")"
