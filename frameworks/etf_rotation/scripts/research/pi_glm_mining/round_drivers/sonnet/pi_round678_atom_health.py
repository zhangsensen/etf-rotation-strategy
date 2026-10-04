import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research"))
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/src"))
import pi_round002_mine as base
from etf_strategy.core.family_registry import load_builtin_families, resolve_family
from etf_strategy.core.families.cgo_true_turnover_v2_sonnet import _pit_fund_shares
import numpy as np
import pandas as pd

panels, eligibility_all, symbols, forward = base._load_context()
load_builtin_families()
DUMMY_1M = {"frequency": "1m"}
DUMMY_1D = {"frequency": "1d"}

def fam(name, cfg=DUMMY_1M):
    return resolve_family(name).builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, cfg)

new_atoms = fam("cgo_true_turnover_v2_sonnet", DUMMY_1D)
NEW_NAMES = ["CGO_60", "CGO_250", "GAIN_OVERHANG_60", "LOSS_OVERHANG_60", "UW_SHARE_250", "RP_CHANGE_20"]

close = panels["close"][symbols]
ret1 = close.pct_change()
ret1_neg = (-ret1).clip(lower=0.0)
ret1_pos = ret1.clip(lower=0.0)
ret20 = close.pct_change(20)
ret60 = close.pct_change(60)

price_position = fam("repl_overnight_core_v2b")["R2_PRICE_POSITION_20"][symbols]
r_vfp_ulcer = fam("repl_pi37_core_v1")["R_VFP_ULCER_SHIFT_20"][symbols]
underwater_frac_chg = fam("intraday_drawdown_1m")["UNDERWATER_FRAC_CHG_20"][symbols]
r2_vt_bucket = fam("repl_vt_bucket_precise_v1")["R2_VT_BUCKET_COUNT_SHIFT_20"][symbols]
r2_open30 = fam("repl_overnight_core_v2b")["R2_OPEN30_VOL_SHARE_20"][symbols]
yz_overnight = fam("range_based_vol_1m")["YZ_OVERNIGHT_SHARE_20"][symbols]
lunch_pre_run = fam("pi_lunch_prerun_1m")["LUNCH_PRE_RUN_20"][symbols]
close5_consist = fam("bar_size_order_flow")["CLOSE5_DAY_CONSIST_20"][symbols]
perm_entropy = fam("permutation_entropy_1m")["PERM_ENTROPY_RET_20"][symbols]
gap_dd_consumption = fam("overnight_intraday_mismatch_v1")["GAP_DD_CONSUMPTION_RATIO_20"][symbols]

REF_SERIES = {
    "ret1": ret1,
    "max(-ret1,0)": ret1_neg,
    "max(ret1,0)": ret1_pos,
    "ret20": ret20,
    "ret60": ret60,
    "R2_PRICE_POSITION_20": price_position,
    "R_VFP_ULCER_SHIFT_20(DD48leg)": r_vfp_ulcer,
    "UNDERWATER_FRAC_CHG_20(DD48/UE3leg)": underwater_frac_chg,
    "R2_VT_BUCKET_COUNT_SHIFT_20(CR08leg)": r2_vt_bucket,
    "R2_OPEN30_VOL_SHARE_20(CR08leg)": r2_open30,
    "YZ_OVERNIGHT_SHARE_20(UE3leg)": yz_overnight,
    "LUNCH_PRE_RUN_20(CK04leg)": lunch_pre_run,
    "CLOSE5_DAY_CONSIST_20(CK04leg)": close5_consist,
}


def rank_corr(a: pd.DataFrame, b: pd.DataFrame, stride=5):
    a2 = a.iloc[::stride].rank(axis=1, pct=True).stack()
    b2 = b.iloc[::stride].rank(axis=1, pct=True).stack()
    df = pd.concat({"a": a2, "b": b2}, axis=1).dropna()
    if len(df) == 0:
        return float("nan")
    return float(df["a"].corr(df["b"]))


rows = []
for name in NEW_NAMES:
    atom = new_atoms[name][symbols]
    row = {"atom": name}
    for ref_name, ref_frame in REF_SERIES.items():
        row[ref_name] = round(rank_corr(atom, ref_frame), 4)
    rows.append(row)
    print(name, row)

df = pd.DataFrame(rows).set_index("atom")
shadow_cols = ["ret1", "max(-ret1,0)", "max(ret1,0)"] + [c for c in REF_SERIES if c not in ("ret1", "max(-ret1,0)", "max(ret1,0)", "ret20", "ret60")]
def flag(row):
    hits = [c for c in shadow_cols if abs(row[c]) >= 0.7]
    return ";".join(hits) if hits else "ok"
df["shadow_flag"] = df.apply(flag, axis=1)

OUT = base.WORKSPACE_OUTPUTS / "round_678"
OUT.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT / "atom_health.csv")
print(df[["shadow_flag"]])

turnover_medians = {}
for sym in symbols:
    fs = _pit_fund_shares(base.CANONICAL_ROOT, sym, panels["close"].index)
    to = (panels["volume"][sym] / fs.replace(0, np.nan))
    turnover_medians[sym] = float(to.median())
print("turnover medians (target 0.5%-10%):", turnover_medians)
pd.Series(turnover_medians, name="turnover_median").to_csv(OUT / "turnover_medians.csv")
print("wrote", OUT / "atom_health.csv", "and turnover_medians.csv")
