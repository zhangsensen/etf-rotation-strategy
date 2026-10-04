#!/usr/bin/env python3
"""Round 625 driver: S29 stage (main controller directive, 2026-09-21) --
second batch of mechanism atoms. New family mechanism_atoms_v2 (6 atoms,
self-contained, no cross-family imports): MFI_EXTREME_UNDERWATER_SKEW_20,
MFI_EXTREME_FWD5_RET_20 (from S27B5/WA1/NI1's shared MFI_EXTREME_FRAC_20
right leg), ON_UNDERWATER_SPLIT_20 (from UE3/UE1's overnight-share x
underwater mechanism), REL_UNDERWATER_CATEGORY_20 (from FC3's
underwater-vs-category-dispersion pairing), PM_FRONTRUN_RET_CONSIST_20
(from LB7's afternoon-volume x BEST_DAY pairing), BESTDAY_BUCKET_COUNT_RATIO_20
(from XC5's bucket-count x BEST_DAY pairing).

Atom health (round_625_atom_health): disc_ic strongest for
MFI_EXTREME_UNDERWATER_SKEW_20 (0.098) and REL_UNDERWATER_CATEGORY_20
(-0.101); both also show corr_vs_ref >=0.7 against their inspiration
atom (MFI_EXTREME_FRAC_20 corr=0.74, UNDERWATER_FRAC_20 corr=0.82) --
flagged shadow, dedup risk at pairing stage noted in REPORT. The other 4
atoms are <0.12 corr vs their reference (independent new slices).

This round: 6 atomic tests + 18 pairs (3 right legs per left atom,
pairing discipline respected: each left atom's batch <=8, each right leg
reused <=3 times). Right legs are strong previously-validated atoms from
different families (redundancy-magnet atoms PERM_ENTROPY_RET_20 /
CONTINUOUS_BETA_60 / RCOV_N_SHARE_20 / MSPE_5M_20 / BETA_HF_20 excluded
per standing memory). Exploratory pairs -- direction determined by
discovery period, not pre-committed."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_625"

_MFI_UW_SKEW = {"name": "MFI_EXTREME_UNDERWATER_SKEW_20", "source": "mechanism_atoms_v2"}
_MFI_FWD5 = {"name": "MFI_EXTREME_FWD5_RET_20", "source": "mechanism_atoms_v2"}
_ON_SPLIT = {"name": "ON_UNDERWATER_SPLIT_20", "source": "mechanism_atoms_v2"}
_REL_UW_CAT = {"name": "REL_UNDERWATER_CATEGORY_20", "source": "mechanism_atoms_v2"}
_PM_FRONTRUN = {"name": "PM_FRONTRUN_RET_CONSIST_20", "source": "mechanism_atoms_v2"}
_BESTDAY_BUCKET = {"name": "BESTDAY_BUCKET_COUNT_RATIO_20", "source": "mechanism_atoms_v2"}

_PV_ELASTICITY = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_VOV_HAR = {"name": "S28_VOV_HAR_RESID_20", "source": "pi_repl_s28"}
_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_LUNCH_GAP = {"name": "LUNCH_GAP_20", "source": "lunch_break_1m"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}

base.CANDIDATES = [
    # ---- 6 atomic tests ----
    {"id": "S29A1", "operator": "atomic", "left": _MFI_UW_SKEW, "right": _MFI_UW_SKEW,
     "mechanism": "s29_mfi_extreme_underwater_skew_atomic",
     "hypothesis": "MFI_EXTREME_UNDERWATER_SKEW_20（MFI 极值 bar 出现在水下 vs 水上时段的占比差，20 日均值）单原子门 7 重裁。体检 disc_ic 0.098（本批最强），与 MFI_EXTREME_FRAC_20 corr=0.74（shadow，同源）。来自 S27B5/WA1/NI1 共享右腿。",
     "expected_sign": 1},
    {"id": "S29A2", "operator": "atomic", "left": _MFI_FWD5, "right": _MFI_FWD5,
     "mechanism": "s29_mfi_extreme_fwd5_ret_atomic",
     "hypothesis": "MFI_EXTREME_FWD5_RET_20（MFI 极值 bar 后 5 bar 收益均值，20 日均值）单原子门 7 重裁。体检 disc_ic −0.032，与 MFI_EXTREME_FRAC_20 corr=0.11（独立切面）。",
     "expected_sign": -1},
    {"id": "S29A3", "operator": "atomic", "left": _ON_SPLIT, "right": _ON_SPLIT,
     "mechanism": "s29_on_underwater_split_atomic",
     "hypothesis": "ON_UNDERWATER_SPLIT_20（隔夜方差占比高低分半的水下占比差，40 日窗口）单原子门 7 重裁。体检 disc_ic −0.044，与 UNDERWATER_FRAC_20 corr=0.05（独立切面）。来自 UE3/UE1 机制。",
     "expected_sign": -1},
    {"id": "S29A4", "operator": "atomic", "left": _REL_UW_CAT, "right": _REL_UW_CAT,
     "mechanism": "s29_rel_underwater_category_atomic",
     "hypothesis": "REL_UNDERWATER_CATEGORY_20（本 ETF 水下占比相对 sleeve 同类别均值之差，20 日均值）单原子门 7 重裁。体检 disc_ic −0.101（本批第二强），与 UNDERWATER_FRAC_20 corr=0.82（shadow，同源）。来自 FC3 机制。",
     "expected_sign": -1},
    {"id": "S29A5", "operator": "atomic", "left": _PM_FRONTRUN, "right": _PM_FRONTRUN,
     "mechanism": "s29_pm_frontrun_ret_consist_atomic",
     "hypothesis": "PM_FRONTRUN_RET_CONSIST_20（午后抢跑量偏离方向与当日收益符号一致率，20 日均值）单原子门 7 重裁。体检 disc_ic −0.051，与 LUNCH_POST_RUN_20 corr=0.01（独立切面）。来自 LB7 机制。",
     "expected_sign": 1},
    {"id": "S29A6", "operator": "atomic", "left": _BESTDAY_BUCKET, "right": _BESTDAY_BUCKET,
     "mechanism": "s29_bestday_bucket_count_ratio_atomic",
     "hypothesis": "BESTDAY_BUCKET_COUNT_RATIO_20（窗口最大收益日成交量桶数/窗口均值，20 日窗口）单原子门 7 重裁。体检 disc_ic −0.028，与 VT_BUCKET_COUNT_20 corr=0.07（独立切面）。来自 XC5 机制。",
     "expected_sign": -1},
    # ---- 18 pairs (3 right legs per left atom, pairing discipline) ----
    {"id": "S29P1", "operator": "rank_spread", "left": _MFI_UW_SKEW, "right": _PV_ELASTICITY,
     "mechanism": "s29_p1", "hypothesis": "MFI_EXTREME_UNDERWATER_SKEW_20 × PV_ELASTICITY_20（S14/pi_pv_elasticity_1m）。方向由发现期定。", "expected_sign": 1},
    {"id": "S29P2", "operator": "rank_spread", "left": _MFI_UW_SKEW, "right": _D1_LEVEL,
     "mechanism": "s29_p2", "hypothesis": "MFI_EXTREME_UNDERWATER_SKEW_20 × D1_LEVEL_60（S20/price_delay）。方向由发现期定。", "expected_sign": 1},
    {"id": "S29P3", "operator": "rank_spread", "left": _MFI_UW_SKEW, "right": _VOV_HAR,
     "mechanism": "s29_p3", "hypothesis": "MFI_EXTREME_UNDERWATER_SKEW_20 × S28_VOV_HAR_RESID_20（S28/pi_repl_s28，本线唯一 S28 入选左腿）。方向由发现期定。", "expected_sign": 1},
    {"id": "S29P4", "operator": "rank_spread", "left": _MFI_FWD5, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s29_p4", "hypothesis": "MFI_EXTREME_FWD5_RET_20 × R_LOG_AMOUNT_VOL_20（S26R/repl_volume_core_a）。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P5", "operator": "rank_spread", "left": _MFI_FWD5, "right": _LUNCH_GAP,
     "mechanism": "s29_p5", "hypothesis": "MFI_EXTREME_FWD5_RET_20 × LUNCH_GAP_20（S22/lunch_break_1m）。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P6", "operator": "rank_spread", "left": _MFI_FWD5, "right": _VT_AUTOCORR,
     "mechanism": "s29_p6", "hypothesis": "MFI_EXTREME_FWD5_RET_20 × VT_AUTOCORR_20（S24/volume_time_1m）。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P7", "operator": "rank_spread", "left": _ON_SPLIT, "right": _PV_ELASTICITY,
     "mechanism": "s29_p7", "hypothesis": "ON_UNDERWATER_SPLIT_20 × PV_ELASTICITY_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P8", "operator": "rank_spread", "left": _ON_SPLIT, "right": _R_ULCER,
     "mechanism": "s29_p8", "hypothesis": "ON_UNDERWATER_SPLIT_20 × R_ULCER_20（S26R/repl_volume_core_b）。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P9", "operator": "rank_spread", "left": _ON_SPLIT, "right": _D1_LEVEL,
     "mechanism": "s29_p9", "hypothesis": "ON_UNDERWATER_SPLIT_20 × D1_LEVEL_60。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P10", "operator": "rank_spread", "left": _REL_UW_CAT, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s29_p10", "hypothesis": "REL_UNDERWATER_CATEGORY_20 × R_LOG_AMOUNT_VOL_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P11", "operator": "rank_spread", "left": _REL_UW_CAT, "right": _VT_AUTOCORR,
     "mechanism": "s29_p11", "hypothesis": "REL_UNDERWATER_CATEGORY_20 × VT_AUTOCORR_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P12", "operator": "rank_spread", "left": _REL_UW_CAT, "right": _VOV_HAR,
     "mechanism": "s29_p12", "hypothesis": "REL_UNDERWATER_CATEGORY_20 × S28_VOV_HAR_RESID_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P13", "operator": "rank_spread", "left": _PM_FRONTRUN, "right": _LUNCH_GAP,
     "mechanism": "s29_p13", "hypothesis": "PM_FRONTRUN_RET_CONSIST_20 × LUNCH_GAP_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29P14", "operator": "rank_spread", "left": _PM_FRONTRUN, "right": _R_ULCER,
     "mechanism": "s29_p14", "hypothesis": "PM_FRONTRUN_RET_CONSIST_20 × R_ULCER_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29P15", "operator": "rank_spread", "left": _PM_FRONTRUN, "right": _PV_ELASTICITY,
     "mechanism": "s29_p15", "hypothesis": "PM_FRONTRUN_RET_CONSIST_20 × PV_ELASTICITY_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29P16", "operator": "rank_spread", "left": _BESTDAY_BUCKET, "right": _D1_LEVEL,
     "mechanism": "s29_p16", "hypothesis": "BESTDAY_BUCKET_COUNT_RATIO_20 × D1_LEVEL_60。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P17", "operator": "rank_spread", "left": _BESTDAY_BUCKET, "right": _VOV_HAR,
     "mechanism": "s29_p17", "hypothesis": "BESTDAY_BUCKET_COUNT_RATIO_20 × S28_VOV_HAR_RESID_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S29P18", "operator": "rank_spread", "left": _BESTDAY_BUCKET, "right": _R_ULCER,
     "mechanism": "s29_p18", "hypothesis": "BESTDAY_BUCKET_COUNT_RATIO_20 × R_ULCER_20。本轮末条。方向由发现期定。", "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
