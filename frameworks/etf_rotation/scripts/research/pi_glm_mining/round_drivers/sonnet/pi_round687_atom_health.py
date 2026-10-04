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
CBETA_CFG = {"frequency": "1m", "benchmark_symbols": ["510300.SH", "510500.SH"]}


def fam(name, cfg=DUMMY_1M):
    return resolve_family(name).builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, cfg)


v9_space = fam("mechanism_atoms_v9_split_right")
gap_dd_consumption = fam("overnight_intraday_mismatch_v1", DUMMY_1D)["GAP_DD_CONSUMPTION_RATIO_20"][symbols]
continuous_beta = fam("jump_continuous_beta", CBETA_CFG)["CONTINUOUS_BETA_60"][symbols]
gapdd_turnover_split = fam("mechanism_atoms_v8_split_tier2")["GAPDD_TURNOVER_SPLIT_20"][symbols]
ret1 = panels["close"][symbols].pct_change()
ret20 = panels["close"][symbols].pct_change(20)

ORIGINALS = {
    "GAPDD_ONGAP_SPLIT_20B": ("GAP_DD_CONSUMPTION_RATIO_20", gap_dd_consumption),
    "CBETA_TURNOVER_SPLIT_20": ("CONTINUOUS_BETA_60", continuous_beta),
    "CBETA_ONGAP_SPLIT_20": ("CONTINUOUS_BETA_60", continuous_beta),
}


def rank_corr(a, b, stride=5):
    a2 = a.iloc[::stride].rank(axis=1, pct=True).stack()
    b2 = b.iloc[::stride].rank(axis=1, pct=True).stack()
    df = pd.concat({"a": a2, "b": b2}, axis=1).dropna()
    if len(df) == 0:
        return float("nan")
    return float(df["a"].corr(df["b"]))


rows = []
for name, (orig_name, orig_frame) in ORIGINALS.items():
    c_orig = rank_corr(v9_space[name][symbols], orig_frame)
    c_ret1 = rank_corr(v9_space[name][symbols], ret1)
    c_ret20 = rank_corr(v9_space[name][symbols], ret20)
    flag = []
    if abs(c_orig) >= 0.7:
        flag.append("shadow_of_original")
    if abs(c_ret1) >= 0.7:
        flag.append("ret1_shadow")
    if abs(c_ret20) >= 0.7:
        flag.append("ret20_shadow")
    row = {"atom": name, "vs_original": orig_name, "corr_vs_original": round(c_orig, 4),
           "corr_vs_ret1": round(c_ret1, 4), "corr_vs_ret20": round(c_ret20, 4),
           "flag": ";".join(flag) if flag else "ok"}
    rows.append(row)
    print(row)

# Cross-check: GAPDD_ONGAP_SPLIT_20B vs the already-existing GAPDD_TURNOVER_SPLIT_20 (same base stat, different condition)
c_cross = rank_corr(v9_space["GAPDD_ONGAP_SPLIT_20B"][symbols], gapdd_turnover_split)
print({"atom": "GAPDD_ONGAP_SPLIT_20B", "vs": "GAPDD_TURNOVER_SPLIT_20 (S70, same base diff condition)", "corr": round(c_cross, 4)})

df = pd.DataFrame(rows)
OUT = base.WORKSPACE_OUTPUTS / "round_687"
OUT.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT / "atom_health.csv", index=False)
print("wrote", OUT / "atom_health.csv")
