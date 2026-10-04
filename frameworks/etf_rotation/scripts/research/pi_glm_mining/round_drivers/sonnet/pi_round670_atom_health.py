import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research"))
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/src"))
import numpy as np
import pandas as pd
import pi_round002_mine as base
from etf_strategy.core.family_registry import load_builtin_families, resolve_family

panels, eligibility_all, symbols, forward = base._load_context()
load_builtin_families()

DUMMY = {"frequency": "1d"}


def resolved(source, freq="1d"):
    cfg = {"frequency": freq}
    return resolve_family(source).builder(panels, eligibility_all[symbols], base.CANONICAL_ROOT, cfg)


cgo_space = resolved("capital_gains_overhang_1d")
uw_chg = resolved("intraday_drawdown_1m", "1m")["UNDERWATER_FRAC_CHG_20"][symbols]
vol_spike = resolved("intraday_volume_profile_1m", "1m")["VOL_SPIKE_FREQ_20"][symbols]
vt_autocorr = resolved("volume_time_1m", "1m")["VT_AUTOCORR_20"][symbols]
lunch_post_run = resolved("lunch_break_1m", "1m")["LUNCH_POST_RUN_20"][symbols]

targets = {
    "CGO_60": cgo_space["CGO_60"][symbols],
    "GAIN_OVERHANG_60": cgo_space["GAIN_OVERHANG_60"][symbols],
    "LOSS_OVERHANG_60": cgo_space["LOSS_OVERHANG_60"][symbols],
    "RP_CHANGE_20": cgo_space["RP_CHANGE_20"][symbols],
}
refs = {
    "UNDERWATER_FRAC_CHG_20": uw_chg,
    "VOL_SPIKE_FREQ_20": vol_spike,
    "VT_AUTOCORR_20": vt_autocorr,
    "LUNCH_POST_RUN_20": lunch_post_run,
}

STRIDE = 5


def rank_corr(a: pd.DataFrame, b: pd.DataFrame) -> float:
    a2 = a.iloc[::STRIDE].rank(axis=1, pct=True).stack()
    b2 = b.iloc[::STRIDE].rank(axis=1, pct=True).stack()
    df = pd.concat({"a": a2, "b": b2}, axis=1).dropna()
    if len(df) < 100:
        return float("nan")
    return float(df["a"].corr(df["b"]))


rows = []
for tname, tframe in targets.items():
    row = {"atom": tname}
    for rname, rframe in refs.items():
        row[rname] = round(rank_corr(tframe, rframe), 3)
    rows.append(row)

print(pd.DataFrame(rows).to_string(index=False))
