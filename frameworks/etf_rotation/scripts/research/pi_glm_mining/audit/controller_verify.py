#!/usr/bin/env python3
"""Controller-side cross-check of a round's gate-7 admissions.

For each admitted candidate in <round_dir>/STATUS.json: rebuild the signal with
the live engine copy in the audit workspace, score top-K vs 14-EW on the same
label, and compare with the numbers pi wrote. Also emits year-by-year and K=2.
Writes <round_dir>/controller_verification.json (read-only w.r.t. pi's files
otherwise). Exit 2 if any pi-vs-controller number differs by > 0.05 bp or
> 0.01 in t/precision.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

round_dir = Path([a for a in sys.argv[1:] if not a.startswith("--")][0]).resolve()
OUT_NAME = "controller_verification.json"
# lane-aware (E22): the round lives in <run_dir>/workspace/outputs/round_NNN; verify against THAT lane's
# engine + family configs (Sonnet builds families the pi workspace never sees).
LIVE_WS = round_dir.parents[1]
_PI_LIVE = Path(str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_pi_glm_mining_20260919/workspace"))
AUDIT_WS = (_PI_LIVE.parent / "audit_rerun_round002_bea695d0/workspace") if LIVE_WS == _PI_LIVE else (LIVE_WS.parent / "audit_verify_ws/workspace")
AUDIT_WS.mkdir(parents=True, exist_ok=True)
K = 3

# refresh engine copy from live workspace (read-only copy), then import
import shutil
shutil.copytree(LIVE_WS / "frameworks", AUDIT_WS / "frameworks", dirs_exist_ok=True)
sys.path.insert(0, str(AUDIT_WS / "frameworks/etf_rotation/scripts/research"))
import pi_round002_mine as eng  # noqa: E402

status = json.loads((round_dir / "STATUS.json").read_text())
plan_path = round_dir / "PLAN.json"
if not plan_path.exists():  # blocked/void rounds carry no plan
    (round_dir / "controller_verification.json").write_text(json.dumps({"round_id": status.get("round_id"), "verdict": "NOT_APPLICABLE", "reason": "no PLAN.json (blocked/void round)"}, ensure_ascii=False, indent=2))
    print("no PLAN.json; nothing to verify"); sys.exit(0)
plan = json.loads(plan_path.read_text())
cands = {c["id"]: c for c in plan["candidates"]}
if "candidates" not in status:  # probe/census rounds carry no candidate table; nothing to cross-check
    (round_dir / "controller_verification.json").write_text(json.dumps({"round_id": status.get("round_id"), "verdict": "NOT_APPLICABLE", "reason": "STATUS has no candidates table (probe/census round)"}, ensure_ascii=False, indent=2))
    print("no candidates table; nothing to verify"); sys.exit(0)
ALL = "--all" in sys.argv  # replication rounds: verify every preregistered candidate, not only admissions
admitted = [c for c in status["candidates"] if ALL or c.get("gate_pass")]
if ALL:
    OUT_NAME = "controller_verification_all.json"
if not admitted:
    # write a marker so the tick can mark the round seen (E24: rounds with n_gate_pass=null,
    # e.g. Sonnet's data-outage BLOCKED rounds, retried verification every tick forever)
    (round_dir / "controller_verification.json").write_text(json.dumps({"round_id": status.get("round_id"), "verdict": "NOT_APPLICABLE", "reason": "no admitted candidates"}, ensure_ascii=False, indent=2))
    print("no admitted candidates; nothing to verify"); sys.exit(0)

panels, eligibility, symbols, forward = eng._load_context()
eng.load_builtin_families()
all_elig = eng.build_pit_eligibility(panels, eng.MIN_HISTORY, True)
plan_obj = json.loads((round_dir / "PLAN.json").read_text())
from etf_strategy.core.etf_mining_campaign import verify_plan_seal as _vseal  # noqa: E402
_hashf = lambda pth: __import__("hashlib").sha256(pth.read_bytes()).hexdigest()
REPLAY_ONLY = (
    not _vseal(round_dir / "PLAN.json")
    or status.get("plan_sha256") != _hashf(round_dir / "PLAN.json")
    or status.get("referee_version") != getattr(eng, "REFEREE_VERSION", None)
)
if "input_hashes" not in plan_obj:
    (round_dir / (OUT_NAME if ALL else "controller_verification.json")).write_text(json.dumps({"round_id": status.get("round_id"), "verdict": "NOT_APPLICABLE", "reason": "pre-v4 PLAN without locked input hashes; use the historical rejudge tools"}, ensure_ascii=False, indent=2))
    print("pre-v4 PLAN; not verifiable under v4.1"); sys.exit(0)
ranked = eng._build_atoms(panels, all_elig, symbols, {**plan_obj, "candidates": [cands[c["id"]] for c in admitted]}, use_cache=False)
from etf_strategy.core.etf_mining_referee import topk_series as _topk, block_t_calendar as _bt, purge_by_exit as _purge  # noqa: E402

def h_profile(sig, direction):
    """H10/H20 audit-window top-3 excess with exit purge and calendar blocks of H sessions (v4.1 semantics)."""
    out = {}
    for h in (10, 20):
        ser = _topk(sig, forward[h], eligibility, direction=direction, k=K, min_names=max(eng.MIN_PAIRS, K + 1)).excess
        cal = forward[h].index
        aud = _purge(ser.loc[eng.AUDIT_START:eng.AUDIT_END], cal, eng.AUDIT_END, eng.LAG + h)
        out[f"k3_audit_h{h}_bp_blockH"] = float(aud.dropna().mean() * 1e4) if aud.notna().any() else float("nan")
        out[f"k3_audit_h{h}_t_blockH"] = _bt(aud, cal, max(5, h))[0]
    return out

out = {"round_id": status["round_id"], "verified_at_utc": pd.Timestamp.now("UTC").isoformat(), "referee_version": getattr(eng, "REFEREE_VERSION", "?"),
       "lane_referee_version": status.get("referee_version"), "plan_seal_ok": _vseal(round_dir / "PLAN.json"), "status_plan_sha_ok": status.get("plan_sha256") == _hashf(round_dir / "PLAN.json"),
       "mode": "REPLAY_ONLY (lane round produced by another referee version or unsealed plan; numbers are a re-evaluation, not a cross-check)" if REPLAY_ONLY else "CROSS_CHECK", "candidates": []}
mismatch = False
for c in admitted:
    direction = float(c["direction"])
    sig = eng.materialize_expression(eng._expression_spec(cands[c["id"]]), ranked)
    rec = {"id": c["id"], "expression": c["expression"], "direction": direction}
    # H5: the engine's own referee (fractional ties, exit purge, calendar blocks, HAC) -- identical code path
    ref = eng._topk_referee(sig, forward[eng.PRIMARY], eligibility, direction)
    rec.update({
        "k3_disc_excess_bp": ref["topk_excess_disc_bp"], "k3_disc_t_block5": ref["topk_t_block5_disc"], "k3_disc_t_hac": ref.get("topk_t_hac_disc"),
        "k3_audit_excess_bp": ref["topk_excess_audit_bp"], "k3_audit_t_block5": ref.get("topk_t_block_audit"), "k3_audit_t_hac": ref.get("topk_t_hac_audit"),
        "k3_disc_p_at_k": ref["topk_p_at_3_disc"], "k3_audit_p_at_k": ref["topk_p_at_3_audit"],
        "k3_disc_p_baseline": ref["topk_p_baseline_disc"], "k3_audit_p_baseline": ref["topk_p_baseline_audit"],
        "dropped_label_days": ref.get("topk_dropped_label_days"), "topk_gate_pass_v41": bool(ref.get("topk_gate_pass")),
    })
    rec.update(h_profile(sig, direction))
    ex = ref["_topk_excess_series"]
    cal5 = forward[eng.PRIMARY].index
    ex_all = _purge(ex.loc[eng.DISCOVERY_START:eng.AUDIT_END], cal5, eng.AUDIT_END, eng.LAG + eng.PRIMARY)
    rec["yearly"] = {int(y): {"days": int(g.notna().sum()), "excess_bp": float(g.dropna().mean() * 1e4) if g.notna().any() else float("nan"), "t_block5": _bt(g, cal5, eng.PRIMARY)[0]} for y, g in ex_all.groupby(ex_all.index.year)}
    # compare with the lane's recorded numbers (only meaningful when the round was produced by the same referee version)
    cmp = {}
    # full decision set (Codex round-2 P1): means, both block-t, both HAC, precision, campaign, gate
    for pk, ck, tol in (("topk_excess_disc_bp", "k3_disc_excess_bp", 0.05), ("topk_t_block5_disc", "k3_disc_t_block5", 0.01),
                        ("topk_t_hac_disc", "k3_disc_t_hac", 0.01), ("topk_excess_audit_bp", "k3_audit_excess_bp", 0.05),
                        ("topk_t_block_audit", "k3_audit_t_block5", 0.01), ("topk_t_hac_audit", "k3_audit_t_hac", 0.01),
                        ("topk_p_at_3_disc", "k3_disc_p_at_k", 0.01), ("topk_p_at_3_audit", "k3_audit_p_at_k", 0.01)):
        if pk in c and c[pk] is not None and np.isfinite(c[pk]) and rec.get(ck) is not None and np.isfinite(rec[ck]):
            d = abs(float(c[pk]) - rec[ck]); cmp[pk] = {"pi": float(c[pk]), "controller": rec[ck], "abs_diff": d, "ok": d <= tol}
            mismatch |= d > tol
    for bk, ck in (("campaign_pass", "campaign_pass_v42"), ("topk_gate_pass", "topk_gate_pass_v41")):
        if bk in c and c[bk] is not None:
            rec.setdefault("campaign_pass_v42", bool(ref.get("campaign_pass")))
            ok_b = bool(c[bk]) == bool(rec[ck]); cmp[bk] = {"pi": bool(c[bk]), "controller": bool(rec[ck]), "ok": ok_b}; mismatch |= not ok_b
    if REPLAY_ONLY:
        mismatch = False   # a replay cannot "mismatch" a different referee; the report carries mode=REPLAY_ONLY
    rec["pi_vs_controller"] = cmp
    rec["all_years_same_sign"] = bool(len({np.sign(v["excess_bp"]) for v in rec["yearly"].values() if np.isfinite(v["excess_bp"])}) == 1)
    out["candidates"].append(rec)
out["verdict"] = ("REPLAY_ONLY" if REPLAY_ONLY else ("MISMATCH" if mismatch else "CONSISTENT"))
(round_dir / (OUT_NAME if ALL else "controller_verification.json")).write_text(json.dumps(out, ensure_ascii=False, indent=2, default=float))
for r in out["candidates"]:
    print(f"{r['id']}: k3 disc {r['k3_disc_excess_bp']:.1f}bp t{r['k3_disc_t_block5']:.2f} hac{(r['k3_disc_t_hac'] or float('nan')):.2f} | audit {r['k3_audit_excess_bp']:.1f}bp t{(r['k3_audit_t_block5'] or float('nan')):.2f} | H10/H20 audit t {r['k3_audit_h10_t_blockH']:.2f}/{r['k3_audit_h20_t_blockH']:.2f} | dropped {r['dropped_label_days']} | v4.1 gate {r['topk_gate_pass_v41']} | vs lane: {'OK' if all(v['ok'] for v in r['pi_vs_controller'].values()) else 'MISMATCH'}")
print("verdict:", out["verdict"])
sys.exit(2 if mismatch else 0)
