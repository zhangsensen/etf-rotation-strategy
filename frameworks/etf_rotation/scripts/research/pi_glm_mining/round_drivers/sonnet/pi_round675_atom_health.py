import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research"))
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/src"))
import pi_round002_mine as base
from etf_strategy.core.family_registry import load_builtin_families, resolve_family
import pandas as pd

panels, eligibility_all, symbols, forward = base._load_context()
load_builtin_families()

DUMMY_1M = {"frequency": "1m"}

v6_space = resolve_family("mechanism_atoms_v6_split").builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, DUMMY_1M)
uw_chg = resolve_family("intraday_drawdown_1m").builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, DUMMY_1M)["UNDERWATER_FRAC_CHG_20"][symbols]
perm_ent = resolve_family("permutation_entropy_1m").builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, DUMMY_1M)["PERM_ENTROPY_RET_20"][symbols]
lunch_post_run = resolve_family("lunch_break_1m").builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, DUMMY_1M)["LUNCH_POST_RUN_20"][symbols]
ulcer = resolve_family("intraday_pain_recovery_1m").builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, DUMMY_1M)["ULCER_INDEX_20"][symbols]
yz_share = resolve_family("range_based_vol_1m").builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, DUMMY_1M)["YZ_OVERNIGHT_SHARE_20"][symbols]
ret1 = panels["close"][symbols].pct_change()

ORIGINALS = {
    "UWCHG_TURNOVER_SPLIT_20": ("UNDERWATER_FRAC_CHG_20", uw_chg),
    "UWCHG_ONGAP_SPLIT_20": ("UNDERWATER_FRAC_CHG_20", uw_chg),
    "PERMENT_TURNOVER_SPLIT_20": ("PERM_ENTROPY_RET_20", perm_ent),
    "PERMENT_AMIHUD_SPLIT_20": ("PERM_ENTROPY_RET_20", perm_ent),
    "LUNCHPR_ONGAP_SPLIT_20": ("LUNCH_POST_RUN_20", lunch_post_run),
    "ULCER_NOISERATIO_SPLIT_20": ("ULCER_INDEX_20", ulcer),
    "ULCER_TURNOVER_SPLIT_20": ("ULCER_INDEX_20", ulcer),
    "YZSHARE_AMIHUD_SPLIT_20": ("YZ_OVERNIGHT_SHARE_20", yz_share),
}


def rank_corr(a, b, stride=5):
    a2 = a.iloc[::stride].rank(axis=1, pct=True).stack()
    b2 = b.iloc[::stride].rank(axis=1, pct=True).stack()
    df = pd.concat({"a": a2, "b": b2}, axis=1).dropna()
    return df["a"].corr(df["b"]), len(df)


rows = []
for name, (orig_name, orig_frame) in ORIGINALS.items():
    c_orig, n1 = rank_corr(v6_space[name][symbols], orig_frame)
    c_ret1, n2 = rank_corr(v6_space[name][symbols], ret1)
    shadow = "SHADOW" if abs(c_orig) >= 0.7 else "ok"
    row = {"atom": name, "vs_original": orig_name, "corr_vs_original": round(c_orig, 4),
           "corr_vs_ret1": round(c_ret1, 4), "flag": shadow}
    rows.append(row)
    print(row)

df = pd.DataFrame(rows)
OUT = base.WORKSPACE_OUTPUTS / "round_675"
df.to_csv(OUT / "atom_health.csv", index=False)
print("wrote", OUT / "atom_health.csv")
