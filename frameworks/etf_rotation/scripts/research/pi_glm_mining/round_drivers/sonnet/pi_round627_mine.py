#!/usr/bin/env python3
"""Round 627 driver: S30 stage (main controller directive, 2026-09-21) --
third batch of mechanism atoms, inspired by pi lane's stage-37 pairings
(CO36, CK04, CJ16, CZ01/CY95, CR08, CQ31). New family mechanism_atoms_v3
(5 new atoms, heavily reusing already-built atoms via resolve_family()
per the controller's efficiency directive -- see the family module's
docstring). The 6th source mechanism (CZ01/CY95) is not rebuilt: it is
byte-identical to S27's ON_TROUGH_RECOVERY_MATCH_20
(overnight_intraday_mismatch_v1), reused directly here as S30A6.

Small-sample pilot (3 symbols) ran in 28.07s; full 14-symbol run
extrapolated ~2.2 min, well under the controller's 10-minute threshold
-- ran directly without further optimization.

Atom health (round_627_atom_health): disc_ic strongest for
FIRST30_BUCKET_SHARE_20 (-0.115), but corr_vs_ref=0.85 against
OPEN30_VOL_SHARE_20 (shadow, both measure first-30-min volume
concentration) -- dedup risk at pairing stage. PM_POSTRUN_DAY_CONSIST_20
vs S29's PM_FRONTRUN_RET_CONSIST_20 corr=0.20 (independent despite
conceptual similarity -- level-vs-mean-deviation-consistency captures a
different slice than the raw level itself). Other 3 atoms <0.25 corr vs
reference (independent).

6 atomic tests + 15 pairs (3 right legs per left atom, pairing
discipline respected, fresh S30 counters). Right legs: strong
previously-validated atoms not yet used this stage, redundancy-magnet
atoms excluded per standing memory."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_627"

_VT_SPLIT = {"name": "VT_AUTOCORR_ACTIVITY_SPLIT_20", "source": "mechanism_atoms_v3"}
_AM_PRERUN = {"name": "AM_PRERUN_CLOSE5_CONSIST_20", "source": "mechanism_atoms_v3"}
_PM_POSTRUN = {"name": "PM_POSTRUN_DAY_CONSIST_20", "source": "mechanism_atoms_v3"}
_FIRST30 = {"name": "FIRST30_BUCKET_SHARE_20", "source": "mechanism_atoms_v3"}
_HAR_PV_SPLIT = {"name": "HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20", "source": "mechanism_atoms_v3"}
_TROUGH_MATCH = {"name": "ON_TROUGH_RECOVERY_MATCH_20", "source": "overnight_intraday_mismatch_v1"}

_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_UW_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_VT_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}

base.CANDIDATES = [
    # ---- 6 atomic tests ----
    {"id": "S30A1", "operator": "atomic", "left": _VT_SPLIT, "right": _VT_SPLIT,
     "mechanism": "s30_vt_autocorr_activity_split_atomic",
     "hypothesis": "VT_AUTOCORR_ACTIVITY_SPLIT_20（VT_AUTOCORR_20 按当日成交量分半，高低活动日差，40 日窗口）单原子门 7 重裁。体检 disc_ic −0.009（弱），corr_vs_ref=0.06（独立）。来自 CO36 机制。",
     "expected_sign": -1},
    {"id": "S30A2", "operator": "atomic", "left": _AM_PRERUN, "right": _AM_PRERUN,
     "mechanism": "s30_am_prerun_close5_consist_atomic",
     "hypothesis": "AM_PRERUN_CLOSE5_CONSIST_20（LUNCH_PRE_RUN_20 偏离方向与尾 5 分钟收益符号一致率，20 日均值）单原子门 7 重裁。体检 disc_ic 0.044，corr_vs_ref=0.25（独立）。来自 CK04 机制。",
     "expected_sign": 1},
    {"id": "S30A3", "operator": "atomic", "left": _PM_POSTRUN, "right": _PM_POSTRUN,
     "mechanism": "s30_pm_postrun_day_consist_atomic",
     "hypothesis": "PM_POSTRUN_DAY_CONSIST_20（LUNCH_POST_RUN_20 偏离方向与当日收益符号一致率，20 日均值）单原子门 7 重裁。体检 disc_ic 0.018，与 S29 PM_FRONTRUN_RET_CONSIST_20 corr=0.20（独立，尽管概念相近）。来自 CJ16 机制。",
     "expected_sign": 1},
    {"id": "S30A4", "operator": "atomic", "left": _FIRST30, "right": _FIRST30,
     "mechanism": "s30_first30_bucket_share_atomic",
     "hypothesis": "FIRST30_BUCKET_SHARE_20（首 30 分钟成交量桶数/全日桶数，20 日均值）单原子门 7 重裁。体检 disc_ic −0.115（本批最强），与 OPEN30_VOL_SHARE_20 corr=0.85（shadow，预警冗余风险）。来自 CR08 机制。",
     "expected_sign": -1},
    {"id": "S30A5", "operator": "atomic", "left": _HAR_PV_SPLIT, "right": _HAR_PV_SPLIT,
     "mechanism": "s30_har_resid_pv_elasticity_split_atomic",
     "hypothesis": "HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20（HAR 残差正负分组的 PV_ELASTICITY_20 之差，40 日窗口）单原子门 7 重裁。体检 disc_ic −0.032，corr_vs_ref=0.06（独立）。来自 CQ31 机制。",
     "expected_sign": -1},
    # S30A6 (ON_TROUGH_RECOVERY_MATCH_20 atomic reuse) dropped: engine's plan-time
    # canonical-hash guard confirmed this exact atomic candidate already exists in
    # a prior round (round_614, S27) -- CZ01/CY95's mechanism was already atomically
    # gate-7 tested there under the same definition, no need to re-test.
    # ---- 15 pairs (3 right legs per left atom, pairing discipline) ----
    {"id": "S30P1", "operator": "rank_spread", "left": _VT_SPLIT, "right": _R_ULCER,
     "mechanism": "s30_p1", "hypothesis": "VT_AUTOCORR_ACTIVITY_SPLIT_20 × R_ULCER_20（S26R）。方向由发现期定。", "expected_sign": -1},
    {"id": "S30P2", "operator": "rank_spread", "left": _VT_SPLIT, "right": _D1_LEVEL,
     "mechanism": "s30_p2", "hypothesis": "VT_AUTOCORR_ACTIVITY_SPLIT_20 × D1_LEVEL_60（S20）。方向由发现期定。", "expected_sign": -1},
    {"id": "S30P3", "operator": "rank_spread", "left": _VT_SPLIT, "right": _UW_CHG,
     "mechanism": "s30_p3", "hypothesis": "VT_AUTOCORR_ACTIVITY_SPLIT_20 × UNDERWATER_FRAC_CHG_20（S7，本线历史最强单原子）。方向由发现期定。", "expected_sign": -1},
    {"id": "S30P4", "operator": "rank_spread", "left": _AM_PRERUN, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s30_p4", "hypothesis": "AM_PRERUN_CLOSE5_CONSIST_20 × R_LOG_AMOUNT_VOL_20（S26R）。方向由发现期定。", "expected_sign": 1},
    {"id": "S30P5", "operator": "rank_spread", "left": _AM_PRERUN, "right": _VT_GINI,
     "mechanism": "s30_p5", "hypothesis": "AM_PRERUN_CLOSE5_CONSIST_20 × VT_BUCKET_GINI_20（S24）。方向由发现期定。", "expected_sign": 1},
    {"id": "S30P6", "operator": "rank_spread", "left": _AM_PRERUN, "right": _NOISE_VAR,
     "mechanism": "s30_p6", "hypothesis": "AM_PRERUN_CLOSE5_CONSIST_20 × NOISE_VAR_20（S5）。方向由发现期定。", "expected_sign": 1},
    {"id": "S30P7", "operator": "rank_spread", "left": _PM_POSTRUN, "right": _R_ULCER,
     "mechanism": "s30_p7", "hypothesis": "PM_POSTRUN_DAY_CONSIST_20 × R_ULCER_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30P8", "operator": "rank_spread", "left": _PM_POSTRUN, "right": _D1_LEVEL,
     "mechanism": "s30_p8", "hypothesis": "PM_POSTRUN_DAY_CONSIST_20 × D1_LEVEL_60。方向由发现期定。", "expected_sign": 1},
    {"id": "S30P9", "operator": "rank_spread", "left": _PM_POSTRUN, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s30_p9", "hypothesis": "PM_POSTRUN_DAY_CONSIST_20 × R_LOG_AMOUNT_VOL_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30P10", "operator": "rank_spread", "left": _FIRST30, "right": _UW_CHG,
     "mechanism": "s30_p10", "hypothesis": "FIRST30_BUCKET_SHARE_20 × UNDERWATER_FRAC_CHG_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S30P11", "operator": "rank_spread", "left": _FIRST30, "right": _VT_GINI,
     "mechanism": "s30_p11", "hypothesis": "FIRST30_BUCKET_SHARE_20 × VT_BUCKET_GINI_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S30P12", "operator": "rank_spread", "left": _FIRST30, "right": _NOISE_VAR,
     "mechanism": "s30_p12", "hypothesis": "FIRST30_BUCKET_SHARE_20 × NOISE_VAR_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S30P13", "operator": "rank_spread", "left": _HAR_PV_SPLIT, "right": _R_ULCER,
     "mechanism": "s30_p13", "hypothesis": "HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20 × R_ULCER_20（右腿不含 PV_ELASTICITY_20 以避免与左腿内部构造同源）。方向由发现期定。", "expected_sign": -1},
    {"id": "S30P14", "operator": "rank_spread", "left": _HAR_PV_SPLIT, "right": _D1_LEVEL,
     "mechanism": "s30_p14", "hypothesis": "HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20 × D1_LEVEL_60。方向由发现期定。", "expected_sign": -1},
    {"id": "S30P15", "operator": "rank_spread", "left": _HAR_PV_SPLIT, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s30_p15", "hypothesis": "HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20 × R_LOG_AMOUNT_VOL_20。本轮末条。方向由发现期定。", "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
