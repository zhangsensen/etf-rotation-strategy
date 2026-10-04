import sys, json
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research"))
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/src"))
import numpy as np
import pandas as pd
import pi_round002_mine as base
from etf_strategy.core.etf_family_referee import block_means

OUT = base.WORKSPACE_OUTPUTS / "round_681"
plan = json.loads((OUT / "PLAN.json").read_text())
metrics = pd.read_csv(OUT / "candidate_metrics.csv")

panels, eligibility_all, symbols, forward = base._load_context()
ranked = base._build_atoms(panels, eligibility_all, symbols, plan)
eligibility = eligibility_all[symbols]

TARGETS = ["S67P_VOLSPIKE_MAXDD_SPLIT_20"]
cand_by_id = {c["id"]: c for c in plan["candidates"]}


def audit_block_t(sig: pd.DataFrame, fwd: pd.DataFrame, direction: float, k: int = 3, min_pairs: int = base.MIN_PAIRS, horizon: int = base.PRIMARY):
    s = (sig * direction).where(eligibility)
    f = fwd.where(eligibility)
    valid = s.notna() & f.notna()
    s, f = s.where(valid), f.where(valid)
    n = valid.sum(axis=1)
    ok = n >= max(min_pairs, k + 1)
    top_mask = s.rank(axis=1, ascending=False, method="first") <= k
    top_ret = f.where(top_mask).mean(axis=1).where(ok)
    ew_ret = f.mean(axis=1).where(ok)

    def _stats(excess: pd.Series):
        excess = excess.dropna()
        if len(excess) == 0:
            return float("nan"), float("nan")
        blocks = block_means(excess.to_frame("x"), max(base.PRIMARY, horizon))["x"].dropna()
        t_val = (
            float(blocks.mean() / (blocks.std(ddof=1) / np.sqrt(len(blocks))))
            if len(blocks) > 3
            else float("nan")
        )
        return float(excess.mean() * 1e4), t_val

    excess = top_ret - ew_ret
    disc_bp, disc_t = _stats(excess.loc[: base.DISCOVERY_END])
    aud_bp, aud_t = _stats(excess.loc[base.AUDIT_START : base.AUDIT_END])
    return disc_bp, disc_t, aud_bp, aud_t


ret1 = panels["close"][symbols].pct_change()
rows = []
for cid in TARGETS:
    cand = cand_by_id[cid]
    spec = base._expression_spec(cand)
    signal = base.materialize_expression(spec, ranked)
    direction = float(metrics.loc[metrics["candidate_id"] == cid, "direction"].iloc[0])
    row = {"candidate_id": cid, "expression": spec.readable, "direction": direction}
    for h in (5, 20):
        disc_bp, disc_t, aud_bp, aud_t = audit_block_t(signal, forward[h], direction, horizon=h)
        row[f"h{h}_disc_bp"] = round(disc_bp, 2)
        row[f"h{h}_disc_t"] = round(disc_t, 3)
        row[f"h{h}_audit_bp"] = round(aud_bp, 2)
        row[f"h{h}_audit_t"] = round(aud_t, 3)

    sig_full = signal[symbols]
    a2 = sig_full.iloc[::5].rank(axis=1, pct=True).stack()
    b2 = ret1.iloc[::5].rank(axis=1, pct=True).stack()
    df = pd.concat({"a": a2, "b": b2}, axis=1).dropna()
    row["ret1_shadow_corr"] = round(float(df["a"].corr(df["b"])), 4)
    rows.append(row)
    print(row)

pd.DataFrame(rows).to_csv(OUT / "h_backfill.csv", index=False)
print("wrote", OUT / "h_backfill.csv")
