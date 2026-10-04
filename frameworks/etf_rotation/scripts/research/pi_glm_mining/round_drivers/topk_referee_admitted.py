#!/usr/bin/env python3
"""Top-k rotation referee for admitted pi candidates (read-only audit).

Question asked: if each day we hold the k ETFs with the best score, how much
do we earn over the 14-ETF equal-weight pool, and is it distinguishable from
noise? Uses the engine's own frozen context: same label open(D+2)->open(D+7),
same eligibility, same atoms. Nothing here touches pi's outputs.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pi_round002_mine as eng  # noqa: E402
from etf_strategy.core.etf_family_referee import block_means, maxstat_block_signflip  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 3
LIVE = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
    str(Path(__file__).resolve().parents[6] / "runtime_outputs/etf_pi_glm_mining_20260919/workspace/outputs"))
OUT = HERE.parents[2] / "outputs" / f"topk_referee_k{K}"
OUT.mkdir(parents=True, exist_ok=True)

admitted = []
for st in sorted(LIVE.glob("round_*/STATUS.json")):
    s = json.loads(st.read_text())
    plan = json.loads((st.parent / "PLAN.json").read_text())
    cands = {c["id"]: c for c in plan["candidates"]}
    for c in s.get("candidates", []):
        if c.get("gate_pass"):
            admitted.append(dict(round=s["round_id"], id=c["id"], direction=float(c["direction"]),
                                 expression=c["expression"], cand=cands[c["id"]]))
print("admitted:", [(a["round"], a["id"]) for a in admitted])

panels, eligibility, symbols, forward = eng._load_context()
eng.load_builtin_families()
all_elig = eng.build_pit_eligibility(panels, eng.MIN_HISTORY, True)
ranked = eng._build_atoms(panels, all_elig, symbols, {"candidates": [a["cand"] for a in admitted]})
fwd = forward[eng.PRIMARY]

def window(s: pd.Series, lo=None, hi=None):
    return s.loc[lo:hi].dropna()

rows, excess_cols = [], {}
for a in admitted:
    sig = eng.materialize_expression(eng._expression_spec(a["cand"]), ranked) * a["direction"]
    sig = sig.where(eligibility)
    f = fwd.where(eligibility)
    valid = sig.notna() & f.notna()
    sig, f = sig.where(valid), f.where(valid)
    n = valid.sum(axis=1)
    ok = n >= max(eng.MIN_PAIRS, K + 1)
    top_mask = sig.rank(axis=1, ascending=False, method="first") <= K
    real_top = f.rank(axis=1, ascending=False, method="first") <= K
    top_ret = f.where(top_mask).mean(axis=1).where(ok)
    ew_ret = f.mean(axis=1).where(ok)
    excess = (top_ret - ew_ret)
    precision = ((top_mask & real_top).sum(axis=1) / K).where(ok)
    key = f"{a['round']}:{a['id']}"
    excess_cols[key] = excess
    for name, lo, hi in [("discovery", None, eng.DISCOVERY_END), ("seen_audit", eng.AUDIT_START, eng.AUDIT_END)]:
        e, p = window(excess, lo, hi), window(precision, lo, hi)
        blocks = block_means(e.to_frame("x"), eng.PRIMARY)["x"].dropna()  # non-overlapping 5-session blocks
        t_block = blocks.mean() / (blocks.std(ddof=1) / np.sqrt(len(blocks))) if len(blocks) > 3 else np.nan
        rows.append(dict(candidate=key, expression=a["expression"], window=name, days=len(e),
                         excess_5d_mean_bp=e.mean() * 1e4, excess_5d_median_bp=e.median() * 1e4,
                         hit_rate=(e > 0).mean(), t_block5=t_block,
                         precision_at_k=p.mean(), precision_baseline=K / n.loc[e.index].mean(),
                         annualized_excess_pct=e.mean() * (244 / eng.PRIMARY) * 100))

res = pd.DataFrame(rows)
mat = pd.DataFrame(excess_cols)
fam = {}
for name, lo, hi in [("discovery", None, eng.DISCOVERY_END), ("seen_audit", eng.AUDIT_START, eng.AUDIT_END)]:
    t, pv = maxstat_block_signflip(mat.loc[lo:hi], block_sessions=20, draws=2000)
    for k in mat.columns:
        fam[(k, name)] = (float(t[k]), float(pv[k]))
res["block20_t"] = [fam[(r.candidate, r.window)][0] for r in res.itertuples()]
res["maxstat_pvalue_familywise"] = [fam[(r.candidate, r.window)][1] for r in res.itertuples()]
res.to_csv(OUT / "topk_referee.csv", index=False)
mat.to_parquet(OUT / "daily_excess.parquet")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
cols = ["candidate", "window", "days", "excess_5d_mean_bp", "annualized_excess_pct", "hit_rate", "t_block5", "block20_t", "maxstat_pvalue_familywise", "precision_at_k", "precision_baseline"]
print(res[cols].round(4).to_string(index=False))
print("written:", OUT)
