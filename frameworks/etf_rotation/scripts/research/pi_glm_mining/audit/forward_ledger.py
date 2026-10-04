#!/usr/bin/env python3
"""Forward ledger for gate-7 admitted single factors (paper, read-only).

Each trading day after registration (2026-09-19) records, per admitted factor:
the signal date D, the top-3 ETFs by score, and later fills in the realized
label open(D+2)->open(D+7) for the top-3 and for the 14-EW pool. Nothing here
is a strategy: no positions, no weights, no costs; it is the out-of-sample
continuation of the same referee. Dates before REGISTRATION are never written,
so the sealed 2025-05 -> registration window stays untouched.
"""
from __future__ import annotations
import json, glob, sys, shutil
from pathlib import Path
import numpy as np, pandas as pd

REGISTRATION = pd.Timestamp("2026-09-19")
K = 3
import os
_PI = Path(str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_pi_glm_mining_20260919"))
RUN = Path(os.environ.get("ETF_RUN_DIR", str(_PI)))  # lane-aware: run once per lane (each lane owns its families)
LIVE_WS = RUN / "workspace"
AUDIT_WS = (_PI / "audit_rerun_round002_bea695d0/workspace") if RUN == _PI else (RUN / "audit_verify_ws/workspace")
AUDIT_WS.mkdir(parents=True, exist_ok=True)
OUT = RUN / "forward"; OUT.mkdir(exist_ok=True)
MIG = int(json.loads((RUN / "migration.json").read_text()).get("round", 0)) if (RUN / "migration.json").exists() else 0
shutil.copytree(LIVE_WS / "frameworks", AUDIT_WS / "frameworks", dirs_exist_ok=True)
sys.path.insert(0, str(AUDIT_WS / "frameworks/etf_rotation/scripts/research"))
import pi_round002_mine as eng  # noqa: E402

# controller void list: admissions that passed the referee mechanically but were voided by the
# controller on audit (E30: degenerate one-day-return shadows). {round_id: [ids]} + reasons.
_vf = RUN / "CONTROLLER_VOID.json"
_vj = json.loads(_vf.read_text()) if _vf.exists() else {}
VOID = {k: v["ids"] for k, v in _vj.items()}
VOID_REASON = {k: v.get("reason", "") for k, v in _vj.items()}
# cluster representative swaps (fix 2, 2026-09-21): same-round higher-audit member rejected only
# by fixed-order dedup is co-tracked as the cluster's representative next to the admitted one.
_sf = RUN / "CLUSTER_REPRESENTATIVE_SWAPS.json"
SWAPS = json.loads(_sf.read_text()) if _sf.exists() else {}

# admitted under gate 7 (rounds >= 012 carry topk fields; earlier admissions were demoted by referee v2)
admitted = []
for st in sorted(glob.glob(str(LIVE_WS / "outputs/round_*/STATUS.json"))):
    s = json.loads(Path(st).read_text()); n = int(s["round_id"].split("_")[1])
    if n < 12 or n < MIG: continue
    if not (Path(st).parent / "PLAN.json").exists(): continue
    plan = {c["id"]: c for c in json.loads((Path(st).parent / "PLAN.json").read_text())["candidates"]}
    # controller re-verification under the CURRENT engine/gate: drop candidates that no longer pass
    # (round_021 F1/F2 were admitted under gate-7 v1 and fail the discovery t>=2 gate today)
    cv = Path(st).parent / "controller_verification.json"
    verified = {}
    if cv.exists():
        for v in json.loads(cv.read_text()).get("candidates", []):
            verified[v["id"]] = (v.get("k3_disc_t_block5") or 0) >= 2.0 and (v.get("k3_audit_excess_bp") or 0) >= 5.0
    for c in s.get("candidates", []):
        if c.get("gate_pass"):
            if c["id"] in VOID.get(s["round_id"], []):
                print(f"skip {s['round_id']}:{c['id']} (controller VOID: {VOID_REASON.get(s['round_id'], '')})"); continue
            if c["id"] in verified and not verified[c["id"]]:
                print(f"skip {s['round_id']}:{c['id']} (fails current gate on controller re-verification)"); continue
            admitted.append(dict(key=f"{s['round_id']}:{c['id']}", cand=plan[c["id"]], direction=float(c["direction"]), expression=c["expression"]))
            rep = SWAPS.get(s["round_id"], {}).get(c["id"])
            if rep and rep["representative"] in plan:
                rc = next((x for x in s.get("candidates", []) if x["id"] == rep["representative"]), None)
                if rc is not None:
                    admitted.append(dict(key=f"{s['round_id']}:{rep['representative']}(rep of {c['id']})", cand=plan[rep["representative"]],
                                         direction=float(rc["direction"]), expression=rc["expression"]))
# manually include T5 (round_014) if not present via the loop (it is >=12, so it is)
if not admitted: print("no gate-7 admissions"); sys.exit(0)

# latest completed trading day in the canonical root
cov = pd.read_csv(str(Path(__file__).resolve().parents[6] / "data/etf_rotation_v1/coverage.csv"))
latest = pd.to_datetime(cov[cov.period == "1d"]["latest"]).min().normalize()
eng.AS_OF = latest.strftime("%Y-%m-%d")
panels, eligibility, symbols, forward = eng._load_context()
eng.load_builtin_families()
all_elig = eng.build_pit_eligibility(panels, eng.MIN_HISTORY, True)
ranked = eng._build_atoms(panels, all_elig, symbols, {"candidates": [a["cand"] for a in admitted]})
fwd = forward[eng.PRIMARY].where(eligibility)
opens = panels["open"][symbols]

ledger_path = OUT / "forward_ledger.csv"
old = pd.DataFrame()
if ledger_path.exists() and ledger_path.stat().st_size > 1:  # a first run before any realized label leaves a 1-byte file
    try:
        old = pd.read_csv(ledger_path, parse_dates=["signal_date"])
    except pd.errors.EmptyDataError:
        old = pd.DataFrame()
rows = []
for a in admitted:
    sig = (eng.materialize_expression(eng._expression_spec(a["cand"]), ranked) * a["direction"]).where(eligibility)
    for d in sig.index[sig.index >= REGISTRATION]:
        row_sig = sig.loc[d].dropna()
        if len(row_sig) < max(eng.MIN_PAIRS, K + 1): continue
        top = list(row_sig.sort_values(ascending=False).index[:K])
        f = fwd.loc[d] if d in fwd.index else pd.Series(dtype=float)
        top_ret = float(f[top].mean()) if f[top].notna().all() else np.nan
        ew_ret = float(f[row_sig.index].mean()) if f[row_sig.index].notna().all() else np.nan
        rows.append(dict(factor=a["key"], expression=a["expression"], signal_date=d, top3=",".join(top), n_eligible=len(row_sig),
                         top3_fwd5=top_ret, ew_fwd5=ew_ret, excess_bp=(top_ret - ew_ret) * 1e4 if np.isfinite(top_ret) and np.isfinite(ew_ret) else np.nan,
                         as_of=eng.AS_OF))
new = pd.DataFrame(rows)
# merge: keep newest computation per (factor, signal_date) so pending labels get filled in
merged = pd.concat([old, new]).drop_duplicates(subset=["factor", "signal_date"], keep="last").sort_values(["factor", "signal_date"]) if len(old) else new
merged.to_csv(ledger_path, index=False)
latest_rows = new[new.signal_date == new.signal_date.max()][["factor", "expression", "signal_date", "top3"]] if len(new) else new
(OUT / "latest_picks.json").write_text(latest_rows.to_json(orient="records", date_format="iso", force_ascii=False, indent=2) if len(new) else "[]")
filled = merged.dropna(subset=["excess_bp"]) if len(merged) else merged
summary = filled.groupby("factor").excess_bp.agg(["count", "mean"]).round(2) if len(filled) else "no realized labels yet"
print(f"as_of {eng.AS_OF} | factors {len(admitted)} | ledger rows {len(merged)} | realized rows {len(filled)}")
print(summary)
if len(new): print(latest_rows.to_string(index=False))
