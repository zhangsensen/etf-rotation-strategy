import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research"))
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/src"))
import pi_round002_mine as base
from etf_strategy.core.family_registry import load_builtin_families, resolve_family
import pandas as pd

panels, eligibility_all, symbols, forward = base._load_context()
load_builtin_families()
DUMMY_1M = {"frequency": "1m"}
DUMMY_1D = {"frequency": "1d"}


def fam(name, cfg=DUMMY_1M):
    return resolve_family(name).builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, cfg)


rp_change = fam("cgo_true_turnover_v2_sonnet", DUMMY_1D)["RP_CHANGE_V2_20"][symbols]
close = panels["close"][symbols]
ret20 = close.pct_change(20)
ret60 = close.pct_change(60)
price_position_20 = fam("repl_overnight_core_v2b")["R2_PRICE_POSITION_20"][symbols]
price_position_250 = fam("price_position_controls", DUMMY_1D)["PRICE_POSITION_250"][symbols]


def rank_corr(a, b, stride=5):
    a2 = a.iloc[::stride].rank(axis=1, pct=True).stack()
    b2 = b.iloc[::stride].rank(axis=1, pct=True).stack()
    df = pd.concat({"a": a2, "b": b2}, axis=1).dropna()
    return float(df["a"].corr(df["b"]))


rows = {
    "ret20": rank_corr(rp_change, ret20),
    "ret60": rank_corr(rp_change, ret60),
    "PRICE_POSITION_20": rank_corr(rp_change, price_position_20),
    "PRICE_POSITION_250": rank_corr(rp_change, price_position_250),
}
for k, v in rows.items():
    print(f"corr(RP_CHANGE_V2_20, {k}) = {v:.4f}")

OUT = base.WORKSPACE_OUTPUTS / "round_684"
pd.Series(rows, name="corr_vs_RP_CHANGE_V2_20").to_csv(OUT / "rp_change_corr_profile.csv")
print("wrote", OUT / "rp_change_corr_profile.csv")
