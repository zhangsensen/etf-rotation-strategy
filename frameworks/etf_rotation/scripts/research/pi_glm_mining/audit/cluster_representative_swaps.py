"""Fix 2 (2026-09-21): the engine dedups in fixed preregistration order (first admitted wins),
while the contract says a cluster is represented by its highest-audit member. This script does
the contract's step at the controller layer, never touching engine outputs:

for every round, a candidate rejected ONLY for rank_correlation_redundancy against a candidate
admitted in the SAME round, with a higher audit excess (topk_excess_audit_bp) and discovery t >= 2,
becomes that cluster's representative. Output: <run>/CLUSTER_REPRESENTATIVE_SWAPS.json
{round_id: {admitted_id: {"representative": id, "audit_bp_admitted": x, "audit_bp_rep": y,
"disc_t_rep": t, "corr": c}}}. forward_ledger co-tracks the representative.
Usage: cluster_representative_swaps.py [--run-dir DIR]  (default both lanes)
"""
from __future__ import annotations
import argparse, csv, glob, json
from pathlib import Path

LANES = [Path(str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_pi_glm_mining_20260919")),
         Path(str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_sonnet_mining_20260920"))]

def f(x):
    try: return float(x)
    except (TypeError, ValueError): return float("nan")

def run(R: Path) -> dict:
    void = json.loads((R / "CONTROLLER_VOID.json").read_text()) if (R / "CONTROLLER_VOID.json").exists() else {}
    swaps: dict = {}
    for cm in sorted(glob.glob(str(R / "workspace/outputs/round_*/candidate_metrics.csv"))):
        rid = Path(cm).parent.name
        rows = list(csv.DictReader(open(cm)))
        if not rows or "gate_failures" not in rows[0]: continue
        voided = set(void.get(rid, {}).get("ids", []))
        admitted = {r["candidate_id"]: r for r in rows if r.get("gate_pass", "").lower() == "true" and r["candidate_id"] not in voided}
        for r in rows:
            if r.get("gate_failures") != "rank_correlation_redundancy": continue
            vs = r.get("max_abs_rank_corr_vs", "")
            if not vs.startswith(f"{rid}:"): continue          # only same-round order effects
            a = admitted.get(vs.split(":", 1)[1])
            if a is None: continue
            if f(r["topk_t_block5_disc"]) < 2.0 or f(r["topk_excess_audit_bp"]) < 5.0: continue
            if f(r["topk_excess_audit_bp"]) <= f(a["topk_excess_audit_bp"]): continue
            cur = swaps.setdefault(rid, {}).get(a["candidate_id"])
            if cur and cur["audit_bp_rep"] >= f(r["topk_excess_audit_bp"]): continue
            swaps.setdefault(rid, {})[a["candidate_id"]] = {
                "representative": r["candidate_id"], "expression": r["expression"],
                "audit_bp_admitted": round(f(a["topk_excess_audit_bp"]), 1),
                "audit_bp_rep": round(f(r["topk_excess_audit_bp"]), 1),
                "disc_t_rep": round(f(r["topk_t_block5_disc"]), 2), "corr": round(f(r["max_abs_rank_corr"]), 3)}
    (R / "CLUSTER_REPRESENTATIVE_SWAPS.json").write_text(json.dumps(swaps, ensure_ascii=False, indent=1))
    return swaps

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run-dir"); a = ap.parse_args()
    for R in ([Path(a.run_dir)] if a.run_dir else LANES):
        s = run(R)
        n = sum(len(v) for v in s.values())
        print(f"{R.name}: {n} swaps in {len(s)} rounds")
        for rid, m in s.items():
            for aid, e in m.items():
                print(f"  {rid}: {aid} ({e['audit_bp_admitted']}) -> {e['representative']} ({e['audit_bp_rep']}, t {e['disc_t_rep']}, corr {e['corr']})")
