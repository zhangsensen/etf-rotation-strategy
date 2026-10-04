import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research"))
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/src"))
import pi_round002_mine as base
from etf_strategy.core.family_registry import load_builtin_families, resolve_family
import numpy as np
import pandas as pd

panels, eligibility_all, symbols, forward = base._load_context()
load_builtin_families()
DUMMY_1M = {"frequency": "1m"}

def fam(name):
    return resolve_family(name).builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, DUMMY_1M)

new_atoms = fam("cost_distribution_1m_sonnet")
NEW_NAMES = ["CGO_1M_20", "CGO_1M_60", "UNDERWATER_VOL_SHARE_1M_60", "COST_CONC_1M_60", "MODE_DIST_1M_60", "COST_SKEW_1M_60"]

close = panels["close"][symbols]
ret1 = close.pct_change()
ret1_neg = (-ret1).clip(lower=0.0)
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
cgo_1d = fam("capital_gains_overhang_1d")
cgo60_1d = cgo_1d["CGO_60"][symbols]
gain_1d = cgo_1d["GAIN_OVERHANG_60"][symbols]
loss_1d = cgo_1d["LOSS_OVERHANG_60"][symbols]
rp_change_1d = cgo_1d["RP_CHANGE_20"][symbols]

REF_SERIES = {
    "ret1": ret1,
    "max(-ret1,0)": ret1_neg,
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
    "CGO_60_1d(S63,VOIDED)": cgo60_1d,
    "GAIN_OVERHANG_60_1d(S63,VOIDED)": gain_1d,
    "LOSS_OVERHANG_60_1d(S63,VOIDED)": loss_1d,
    "RP_CHANGE_20_1d(S63)": rp_change_1d,
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
        c = rank_corr(atom, ref_frame)
        row[ref_name] = round(c, 4)
    rows.append(row)
    print(name, row)

df = pd.DataFrame(rows).set_index("atom")

# shadow flags
shadow_cols = list(REF_SERIES.keys())
def flag(row):
    hits = [c for c in shadow_cols if abs(row[c]) >= 0.7]
    return ";".join(hits) if hits else "ok"
df["shadow_flag"] = df.apply(flag, axis=1)

OUT = base.WORKSPACE_OUTPUTS / "round_676"
OUT.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT / "atom_health.csv")
print(df[["shadow_flag"]])

# turnover median report (real PIT turnover, per E30 correction)
from etf_strategy.core.families.cost_distribution_1m_sonnet import _pit_fund_shares, _daily_bucket_frame
turnover_medians = {}
for sym in symbols:
    daily = _daily_bucket_frame(base.CANONICAL_ROOT, sym, panels["close"].index.max())
    if daily.empty:
        continue
    vol_re = panels["volume"][sym].reindex(daily.index)
    fs = _pit_fund_shares(base.CANONICAL_ROOT, sym, daily.index)
    to = (vol_re / fs.replace(0, np.nan))
    turnover_medians[sym] = float(to.median())
print("turnover medians (target 0.5%-10%):", turnover_medians)
pd.Series(turnover_medians, name="turnover_median").to_csv(OUT / "turnover_medians.csv")
print("wrote", OUT / "atom_health.csv", "and turnover_medians.csv")
