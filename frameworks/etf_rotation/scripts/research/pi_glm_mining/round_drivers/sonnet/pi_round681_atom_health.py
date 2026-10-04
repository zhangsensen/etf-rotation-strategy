import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research"))
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/src"))
import pi_round002_mine as base
from etf_strategy.core.family_registry import load_builtin_families, resolve_family
import pandas as pd

panels, eligibility_all, symbols, forward = base._load_context()
load_builtin_families()
DUMMY_1M = {"frequency": "1m"}

def fam(name):
    return resolve_family(name).builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, DUMMY_1M)

v7_space = fam("mechanism_atoms_v7_split_volume")
vol_spike = fam("intraday_volume_profile_1m")["VOL_SPIKE_FREQ_20"][symbols]
vt_autocorr = fam("volume_time_1m")["VT_AUTOCORR_20"][symbols]
mfi_extreme = fam("accumulation_distribution_1m")["MFI_EXTREME_FRAC_20"][symbols]
bigbar_vol_share = fam("bar_size_order_flow")["BIGBAR_VOL_SHARE_20"][symbols]
r2_vol_autocorr = fam("repl_volume_core_v2b")["R2_VOL_AUTOCORR_20"][symbols]
ret1 = panels["close"][symbols].pct_change()

ORIGINALS = {
    "VOLSPIKE_ONGAP_SPLIT_20": ("VOL_SPIKE_FREQ_20", vol_spike),
    "VOLSPIKE_MAXDD_SPLIT_20": ("VOL_SPIKE_FREQ_20", vol_spike),
    "VTAC_NOISECHG_SPLIT_20": ("VT_AUTOCORR_20", vt_autocorr),
    "VTAC_AMIHUD_SPLIT_20": ("VT_AUTOCORR_20", vt_autocorr),
    "MFIEXT_ONGAP_SPLIT_20": ("MFI_EXTREME_FRAC_20", mfi_extreme),
    "MFIEXT_MAXDD_SPLIT_20": ("MFI_EXTREME_FRAC_20", mfi_extreme),
    "BIGBARVOL_NOISECHG_SPLIT_20": ("BIGBAR_VOL_SHARE_20", bigbar_vol_share),
    "R2VOLAC_AMIHUD_SPLIT_20": ("R2_VOL_AUTOCORR_20", r2_vol_autocorr),
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
    c_orig = rank_corr(v7_space[name][symbols], orig_frame)
    c_ret1 = rank_corr(v7_space[name][symbols], ret1)
    flag = []
    if abs(c_orig) >= 0.7:
        flag.append("shadow_of_original")
    if abs(c_ret1) >= 0.7:
        flag.append("ret1_shadow")
    row = {"atom": name, "vs_original": orig_name, "corr_vs_original": round(c_orig, 4),
           "corr_vs_ret1": round(c_ret1, 4), "flag": ";".join(flag) if flag else "ok"}
    rows.append(row)
    print(row)

df = pd.DataFrame(rows)
OUT = base.WORKSPACE_OUTPUTS / "round_681"
OUT.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT / "atom_health.csv", index=False)
print("wrote", OUT / "atom_health.csv")
