"""Referee v3 self-test (2026-09-21): T1 column-order perturbation, T2 random labels, T3 injected signal, T4 re-score of round_673. Run from a lane workspace: python referee_selftest.py"""
import sys, json, importlib.util, numpy as np, pandas as pd
import os
ws=os.environ.get("ETF_WS", str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_sonnet_mining_20260920/workspace"))  # round_673 plan lives here
# the driver must be imported from a workspace (ROOT is derived from its path); we import the Sonnet lane copy (round_673 families live there) and
# assert it is byte-identical to the tracked entry so the test covers the committed engine.
import hashlib
TRACKED=str(Path(__file__).resolve().parents[6] / "frameworks/etf_rotation/scripts/research/pi_glm_mining/round_drivers/pi_round002_mine.py")
DRIVER=os.environ.get("ETF_DRIVER", str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research/pi_round002_mine.py"))
_h=lambda f: hashlib.sha256(open(f,"rb").read()).hexdigest()
assert _h(DRIVER)==_h(TRACKED), f"driver under test differs from tracked entry: {DRIVER}"
print("driver sha == tracked sha:", _h(TRACKED)[:12])
spec=importlib.util.spec_from_file_location("eng", DRIVER); eng=importlib.util.module_from_spec(spec); sys.argv=["x"]; spec.loader.exec_module(eng)
eng.ROUND_ID="round_996"
panels, elig, syms, forward = eng._load_context(); elig_all=eng.build_pit_eligibility(panels, eng.MIN_HISTORY, True)
eng.load_builtin_families()
plan=json.load(open(f"{ws}/outputs/round_673/PLAN.json")); cands=plan["candidates"]
ranked=eng._build_atoms(panels, elig_all, syms, plan)  # plan carries the locked input_hashes required by v4 caches
sigs={c["id"]: eng.materialize_expression(eng._expression_spec(c), ranked) for c in cands}
E=elig_all[syms]
def ref(sig, fwd, d): return eng._topk_referee(sig, fwd, E, d)
# T1: column-order perturbation
rng=np.random.default_rng(7); perm=list(rng.permutation(syms))
maxdiff=0.0
for c in cands[:8]:
    a=ref(sigs[c["id"]], forward[5], float(c["expected_sign"]))
    b=ref(sigs[c["id"]][perm], forward[5][perm], float(c["expected_sign"]))
    for k in ("topk_excess_disc_bp","topk_t_block5_disc","topk_excess_audit_bp","topk_p_at_3_disc"):
        maxdiff=max(maxdiff, abs(a[k]-b[k]))
print(f"T1 tie/column-order perturbation: max |diff| over 8 candidates x 4 stats = {maxdiff:.2e}  ->", "PASS" if maxdiff<1e-9 else "FAIL")
# T2: random labels — circularly shift the forward panel in time by random offsets (keeps its autocorrelation), 200 draws over 16 candidates
passes=0; holm_passes=0; total=0
for draw in range(60):   # 60 independent circular shifts (was 12)
    off=int(rng.integers(60, len(forward[5])-60))
    fshift=pd.DataFrame(np.roll(forward[5].to_numpy(float), off, axis=0), index=forward[5].index, columns=forward[5].columns)
    ts=[]
    for c in cands:
        r=ref(sigs[c["id"]], fshift, float(c["expected_sign"])); total+=1
        passes+= int(r["topk_gate_pass"]); ts.append(r["topk_t_block5_disc"])
    from scipy.stats import norm
    p=[norm.sf(t) if np.isfinite(t) else 1.0 for t in ts]; order=np.argsort(p); m=len(p)
    for i,idx in enumerate(order):
        if p[idx] <= 0.05/(m-i): holm_passes+=1
        else: break
print(f"T2 random labels (time-shifted forward, {total} candidate-draws): gate-7 pass rate {passes/total:.1%}, Holm-round pass rate {holm_passes/total:.1%}  ->", "PASS" if passes/total<=0.02 and holm_passes/total<=0.02 else "CHECK")
# T3: injected signal = rank of true forward return + noise (should pass with direction +1)
noise=pd.DataFrame(rng.normal(0,1.0,forward[5].shape), index=forward[5].index, columns=forward[5].columns)
inj=(forward[5].rank(axis=1,pct=True)+0.8*noise).where(E)
r=ref(inj, forward[5], 1.0)
print(f"T3 injected signal (POWER test only; bypasses the leak gate by design): disc t {r['topk_t_block5_disc']:.2f}, audit bp {r['topk_excess_audit_bp']:.1f} t {r['topk_t_block_audit']:.2f}, gate {r['topk_gate_pass']}  ->", "PASS" if r["topk_gate_pass"] else "FAIL")
# T4 (sanity): real round_673 admissions under new referee (preregistered direction, audit t, Holm)
print(f"T4 round_673 under referee {eng.REFEREE_VERSION} (16 preregistered):")
rows=[]
for c in cands:
    r=ref(sigs[c["id"]], forward[5], float(c["expected_sign"])); r["id"]=c["id"]; rows.append(r)
from scipy.stats import norm
p=[norm.sf(r["topk_t_block5_disc"]) if np.isfinite(r["topk_t_block5_disc"]) else 1.0 for r in rows]; order=np.argsort(p); m=len(p); holm=[False]*m
for i,idx in enumerate(order):
    if p[idx] <= 0.05/(m-i): holm[idx]=True
    else: break
for r,h in zip(rows,holm):
    if r["topk_gate_pass"] or h or r["topk_t_block5_disc"]>2:
        print(f"  {r['id'][:32]:32s} disc t {r['topk_t_block5_disc']:5.2f} hac {r['topk_t_hac_disc']:5.2f} | audit {r['topk_excess_audit_bp']:6.1f}bp t {r['topk_t_block_audit']:5.2f} | gate7 {r['topk_gate_pass']} holm {h}")
