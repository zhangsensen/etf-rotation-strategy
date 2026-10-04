"""Write STATUS_OVERLAY.json beside each voided round's immutable STATUS.json (2026-09-21).
Usage: apply_void_overlay.py [run_dir ...]  (default both lanes)"""
import sys, json, datetime
from pathlib import Path
LANES=[Path(str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_pi_glm_mining_20260919")),
       Path(str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_sonnet_mining_20260920"))]
for R in ([Path(a) for a in sys.argv[1:]] or LANES):
    vf=R/"CONTROLLER_VOID.json"
    if not vf.exists(): continue
    n=0
    for rid, entry in json.loads(vf.read_text()).items():
        d=R/"workspace/outputs"/rid
        if not d.exists(): continue
        (d/"STATUS_OVERLAY.json").write_text(json.dumps({"round_id": rid, "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": "CONTROLLER_VOID.json", "note": "STATUS.json is immutable; these controller verdicts override gate_pass",
            "candidates": {cid: {"gate_pass": False, "controller_verdict": "VOID", "reason": entry.get("reason","")} for cid in entry.get("ids",[])}}, ensure_ascii=False, indent=1)); n+=1
    print(f"{R.name}: {n} overlays written")
