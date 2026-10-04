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


v8_space = fam("mechanism_atoms_v8_split_tier2")
lunch_pre_run = fam("pi_lunch_prerun_1m")["LUNCH_PRE_RUN_20"][symbols]
vfp_ulcer_shift = fam("repl_pi37_core_v1")["R_VFP_ULCER_SHIFT_20"][symbols]
resiliency = fam("liquidity_commonality_1m")["RESILIENCY_20"][symbols]
gap_dd_consumption = fam("overnight_intraday_mismatch_v1", DUMMY_1D)["GAP_DD_CONSUMPTION_RATIO_20"][symbols]
close5_consist = fam("bar_size_order_flow")["CLOSE5_DAY_CONSIST_20"][symbols]
ret1 = panels["close"][symbols].pct_change()
ret20 = panels["close"][symbols].pct_change(20)

ORIGINALS = {
    "LUNCHPR_TURNOVER_SPLIT_20": ("LUNCH_PRE_RUN_20", lunch_pre_run),
    "LUNCHPR_ONGAP_SPLIT_20B": ("LUNCH_PRE_RUN_20", lunch_pre_run),
    "VFPULCER_TURNOVER_SPLIT_20": ("R_VFP_ULCER_SHIFT_20", vfp_ulcer_shift),
    "VFPULCER_NOISECHG_SPLIT_20": ("R_VFP_ULCER_SHIFT_20", vfp_ulcer_shift),
    "RESIL_ONGAP_SPLIT_20": ("RESILIENCY_20", resiliency),
    "RESIL_AMIHUD_SPLIT_20": ("RESILIENCY_20", resiliency),
    "GAPDD_TURNOVER_SPLIT_20": ("GAP_DD_CONSUMPTION_RATIO_20", gap_dd_consumption),
    "CLOSE5_NOISECHG_SPLIT_20": ("CLOSE5_DAY_CONSIST_20", close5_consist),
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
    c_orig = rank_corr(v8_space[name][symbols], orig_frame)
    c_ret1 = rank_corr(v8_space[name][symbols], ret1)
    c_ret20 = rank_corr(v8_space[name][symbols], ret20)
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

df = pd.DataFrame(rows)
OUT = base.WORKSPACE_OUTPUTS / "round_685"
OUT.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT / "atom_health.csv", index=False)
print("wrote", OUT / "atom_health.csv")
