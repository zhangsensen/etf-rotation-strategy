#!/usr/bin/env python3
"""Send one Feishu text alert per distinct state for the ETF pi mining line.

Usage: controller_alert.py <state_key> <message>
Webhook: FEISHU_STRATEGY_HEALTH_WEBHOOK_URL from ~/.config/gpu_ml/strategy_health_feishu.env
(the strategy-health channel already used by the stop-card notifications).
Dedup: the same state_key is not re-sent until it clears (see clear_alert).
Honors GPU_ML_NO_NOTIFY=1 (test-pollution kill switch).
"""
import json, os, sys, urllib.request
from pathlib import Path

STATE = Path(os.environ.get("ETF_RUN_DIR", str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_pi_glm_mining_20260919"))) / "controller_alerts.json"
ENV = Path.home() / ".config/gpu_ml/strategy_health_feishu.env"

def _webhook():
    if not ENV.exists(): return None
    for line in ENV.read_text().splitlines():
        if line.startswith("FEISHU_STRATEGY_HEALTH_WEBHOOK_URL="):
            return line.split("=", 1)[1].strip().strip('"')
    return None

def main():
    key, msg = sys.argv[1], sys.argv[2]
    sent = json.loads(STATE.read_text()) if STATE.exists() else {}
    if key == "clear":
        for k in msg.split(","): sent.pop(k, None)
        STATE.write_text(json.dumps(sent)); return
    if key in sent: return
    if os.environ.get("GPU_ML_NO_NOTIFY") == "1": print("notify-skip: GPU_ML_NO_NOTIFY"); return
    url = _webhook()
    if not url: print("notify-skip: no webhook"); return
    body = json.dumps({"msg_type": "text", "content": {"text": f"[ETF pi 挖掘线] {msg}"}}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}), timeout=10)
        sent[key] = msg[:120]; STATE.write_text(json.dumps(sent, ensure_ascii=False)); print("alert sent:", key)
    except Exception as exc:  # network failures must not break the tick
        print("notify-failed:", exc)

if __name__ == "__main__":
    main()
