#!/usr/bin/env python3
"""Round 664 (S59, main controller directive 2026-09-21): representative
selection for the remaining 6 mechanism clusters (S57 already handled
the drawdown-geometry cluster). Computes pairwise rank corr (discovery
+ audit windows, stride=5) and daily top-3 overlap across the 23 named
candidates spanning the 6 clusters, then applies the same "跨实现成立→
三视界→2025正→换手低" sequential filter used in S57 to pick each
cluster's representative."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as eng  # noqa: E402
from etf_strategy.core.family_registry import load_builtin_families, resolve_family  # noqa: E402

OUT = eng.WORKSPACE_OUTPUTS / "round_664"
OUT.mkdir(parents=True, exist_ok=True)

# id -> (cluster, direction, [(atom, source), ...])
CANDIDATES = {
    # 1m 量事件簇
    "XB1": ("vol_event", -1.0, [("VT_AUTOCORR_20", "volume_time_1m"), ("VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m")]),
    "VA3": ("vol_event", -1.0, [("BEST_DAY_60_XVOL", "upside_tail"), ("VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m")]),
    "NI1": ("vol_event", 1.0, [("MFI_EXTREME_FRAC_20", "accumulation_distribution_1m"), ("VOL_USHAPE_20", "realized_measures_1m")]),
    "S26R2BB1": ("vol_event", 1.0, [("R2_VOL_SPIKE_FREQ_20", "repl_volume_core_v2a"), ("R_ULCER_20", "repl_volume_core_b")]),
    "S26R2Z2": ("vol_event", 1.0, [("R2_BIGBAR_DIR_SKEW_20", "repl_volume_core_v2a"), ("R2_VOL_AUTOCORR_20", "repl_volume_core_v2b")]),
    "S26RA2": ("vol_event", 1.0, [("R_BIGBAR_VOL_SHARE_20", "repl_volume_core_b")]),
    "S26R2A1": ("vol_event", 1.0, [("R2_VOL_SPIKE_FREQ_20", "repl_volume_core_v2a")]),
    "S54P_UWCAT_H": ("vol_event", 1.0, [("REL_UNDERWATER_CATEGORY_CHG_20", "category_relative_geometry"), ("R_VOL_SPIKE_FREQ_20", "repl_volume_core_a")]),
    # 隔夜跳空 x MFI 簇
    "S27B5": ("overnight_mfi", -1.0, [("GAP_DD_CONSUMPTION_RATIO_20", "overnight_intraday_mismatch_v1"), ("MFI_EXTREME_FRAC_20", "accumulation_distribution_1m")]),
    "UE3": ("overnight_mfi", 1.0, [("YZ_OVERNIGHT_SHARE_20", "range_based_vol_1m"), ("UNDERWATER_FRAC_CHG_20", "intraday_drawdown_1m")]),
    "S47D3": ("overnight_mfi", -1.0, [("OVERNIGHT_SHARE_PMCONSIST_SPLIT_20", "mechanism_atoms_v4"), ("MFI_EXTREME_FRAC_20", "accumulation_distribution_1m")]),
    # 排列熵簇
    "PA1": ("entropy", -1.0, [("PERM_ENTROPY_RET_20", "permutation_entropy_1m")]),
    "R_MA27": ("entropy", 1.0, [("PERM_ENTROPY_RET_20", "permutation_entropy_1m"), ("R_LUNCH_DIR_BET_20", "repl_pi37_core_v1")]),
    "UE1": ("entropy", 1.0, [("YZ_OVERNIGHT_SHARE_20", "range_based_vol_1m"), ("MSPE_5M_20", "complexity_measures_1m")]),
    "CB1": ("entropy", 1.0, [("DAYS_SINCE_NR7_20", "range_contraction_cycle"), ("PATH_EFFICIENCY_20", "path_efficiency")]),
    # 午间簇
    "S14_CK04": ("lunch", 1.0, [("LUNCH_PRE_RUN_20", "pi_lunch_prerun_1m"), ("CLOSE5_DAY_CONSIST_20", "bar_size_order_flow")]),
    "LB7": ("lunch", 1.0, [("LUNCH_POST_RUN_20", "lunch_break_1m"), ("BEST_DAY_20", "upside_tail")]),
    "S28CJ16": ("lunch", -1.0, [("LUNCH_POST_RUN_20", "lunch_break_1m"), ("R_LOG_AMOUNT_VOL_20", "repl_volume_core_a")]),
    "S28CK20": ("lunch", 1.0, [("LUNCH_GAP_20", "lunch_break_1m"), ("R_ULCER_20", "repl_volume_core_b")]),
    # 成交量时间簇
    "R2_CR08": ("vol_time", 1.0, [("R2_VT_BUCKET_COUNT_SHIFT_20", "repl_vt_bucket_precise_v1"), ("R2_OPEN30_VOL_SHARE_20", "repl_overnight_core_v2b")]),
    "XC5": ("vol_time", -1.0, [("VT_BUCKET_COUNT_SHIFT_20", "volume_time_1m"), ("BEST_DAY_20", "upside_tail")]),
    "WA1": ("vol_time", -1.0, [("VT_UNDERWATER_FRAC_20", "volume_time_drawdown"), ("MFI_EXTREME_FRAC_20", "accumulation_distribution_1m")]),
    # 微观结构噪声（单成员）
    "MH3": ("micro_noise", -1.0, [("NOISE_VAR_20", "microstructure_noise_1m"), ("ROLL_SPREAD_20", "microstructure_1m")]),
}

DISCOVERY_END = eng.DISCOVERY_END
AUDIT_START, AUDIT_END = eng.AUDIT_START, eng.AUDIT_END


def main() -> None:
    load_builtin_families()
    panels, eligibility_all, symbols, forward = eng._load_context()
    dates = panels["close"].index
    discovery_mask = dates <= DISCOVERY_END
    audit_mask = (dates >= AUDIT_START) & (dates <= AUDIT_END)

    space_cache: dict[str, dict] = {}

    def get_raw(name: str, source: str) -> pd.DataFrame:
        if source not in space_cache:
            mining = yaml.safe_load(eng._config_path(source).read_text())
            space_cache[source] = resolve_family(source).builder(panels, eligibility_all, eng.CANONICAL_ROOT, mining)
        return space_cache[source][name][symbols]

    signals: dict[str, pd.DataFrame] = {}
    for cid, (cluster, direction, atoms) in CANDIDATES.items():
        if len(atoms) == 1:
            raw = get_raw(*atoms[0])
            score = eng.cross_sectional_rank(raw, eligibility_all[symbols])
        else:
            (na, sa), (nb, sb) = atoms
            ra = eng.cross_sectional_rank(get_raw(na, sa), eligibility_all[symbols])
            rb = eng.cross_sectional_rank(get_raw(nb, sb), eligibility_all[symbols])
            score = ra - rb
        signals[cid] = (score * direction).where(eligibility_all[symbols])
        print(f"built {cid} ({cluster})")

    ids = list(CANDIDATES.keys())
    stride_disc = {cid: eng._stride_vector(signals[cid].loc[discovery_mask]) for cid in ids}

    def _audit_stride(df: pd.DataFrame) -> pd.Series:
        return df.iloc[:: eng.RANK_CORR_STRIDE].stack(future_stack=True)

    stride_audit = {cid: _audit_stride(signals[cid].loc[audit_mask]) for cid in ids}

    def _top3_overlap(a: pd.DataFrame, b: pd.DataFrame, mask) -> float:
        aa, bb = a.loc[mask], b.loc[mask]
        top_a = aa.rank(axis=1, ascending=False, method="first") <= 3
        top_b = bb.rank(axis=1, ascending=False, method="first") <= 3
        both_valid = aa.notna().sum(axis=1).ge(3) & bb.notna().sum(axis=1).ge(3)
        inter = (top_a & top_b & both_valid.to_frame().values).sum(axis=1)
        return float(inter.loc[both_valid].mean()) if both_valid.any() else float("nan")

    corr_disc = pd.DataFrame(index=ids, columns=ids, dtype=float)
    corr_audit = pd.DataFrame(index=ids, columns=ids, dtype=float)
    overlap_disc = pd.DataFrame(index=ids, columns=ids, dtype=float)
    for i in ids:
        for j in ids:
            corr_disc.loc[i, j] = eng._pairwise_pearson(stride_disc[i], stride_disc[j])
            frame = pd.DataFrame({"a": stride_audit[i], "b": stride_audit[j]})
            v = frame.corr(min_periods=50)
            corr_audit.loc[i, j] = float(v.loc["a", "b"]) if np.isfinite(v.loc["a", "b"]) else float("nan")
            overlap_disc.loc[i, j] = _top3_overlap(signals[i], signals[j], discovery_mask)

    corr_disc.to_csv(OUT / "pairwise_rank_corr_discovery.csv")
    corr_audit.to_csv(OUT / "pairwise_rank_corr_audit.csv")
    overlap_disc.to_csv(OUT / "top3_overlap_discovery.csv")

    print("\n--- discovery-window rank corr matrix ---")
    print(corr_disc.round(2).to_string())
    print("\n--- audit-window rank corr matrix ---")
    print(corr_audit.round(2).to_string())


if __name__ == "__main__":
    main()
