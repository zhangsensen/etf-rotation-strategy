#!/usr/bin/env python3
"""Round 631 driver: S32 stage (main controller directive, 2026-09-21) --
deepen S29's REL_UNDERWATER_CATEGORY_20 mechanism. New family
category_relative_geometry (7 atoms, mostly cross-family reuse via
resolve_family() per the efficiency directive).

Atom health (round_631_atom_health): 5 of 7 atoms show HIGH corr vs
their absolute-level source atom (REL_MAXDD_CATEGORY_20 0.88,
REL_RECOVERY_TIME_CATEGORY_20 0.91, REL_ON_VAR_SHARE_CATEGORY_20 0.92,
REL_MFI_EXTREME_CATEGORY_20 0.93, REL_LUNCH_POSTRUN_CATEGORY_20 0.87 --
all shadow-flagged, corr_vs_ref >=0.7). This is a real finding: with
only 2 sleeve groups (technology n=8, auxiliary_rotation n=6) and
cross-sectional ranking done across all 14 symbols together, subtracting
a slowly-moving 2-group peer mean does NOT reliably decorrelate from the
raw level in rank-space unless within-group dispersion dominates
between-group dispersion (which was true for underwater_frac in S29,
but not for these 5 metrics). Only REL_UNDERWATER_CATEGORY_CHG_20 (0.30)
and REL_ON_PREM_CATEGORY_20 (0.46) are genuinely independent slices.

7 atomic tests + 14 pairs (2 right legs per left atom, pairing
discipline respected). Right legs prioritize R_LOG_AMOUNT_VOL_20 /
MFI_EXTREME_FRAC_20 / UNDERWATER_FRAC_CHG_20 per the directive's
explicit instruction, avoiding self-referential pairings where a new
atom's right leg is the same raw atom it was derived from (e.g.
REL_MFI_EXTREME_CATEGORY_20 is never paired against MFI_EXTREME_FRAC_20
itself)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_631"

_REL_UW_CHG = {"name": "REL_UNDERWATER_CATEGORY_CHG_20", "source": "category_relative_geometry"}
_REL_MAXDD = {"name": "REL_MAXDD_CATEGORY_20", "source": "category_relative_geometry"}
_REL_RECOVERY = {"name": "REL_RECOVERY_TIME_CATEGORY_20", "source": "category_relative_geometry"}
_REL_ON_PREM = {"name": "REL_ON_PREM_CATEGORY_20", "source": "category_relative_geometry"}
_REL_ON_VAR = {"name": "REL_ON_VAR_SHARE_CATEGORY_20", "source": "category_relative_geometry"}
_REL_MFI = {"name": "REL_MFI_EXTREME_CATEGORY_20", "source": "category_relative_geometry"}
_REL_LUNCH = {"name": "REL_LUNCH_POSTRUN_CATEGORY_20", "source": "category_relative_geometry"}

_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_MFI_EXTREME = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_UW_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_VT_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_HAR_RESID = {"name": "S28_VOV_HAR_RESID_20", "source": "pi_repl_s28"}

base.CANDIDATES = [
    # ---- 7 atomic tests ----
    {"id": "S32A1", "operator": "atomic", "left": _REL_UW_CHG, "right": _REL_UW_CHG,
     "mechanism": "s32_rel_underwater_chg_atomic",
     "hypothesis": "REL_UNDERWATER_CATEGORY_CHG_20（S29 REL_UNDERWATER_CATEGORY_20 的 20 日变化）单原子门 7 重裁。体检 disc_ic −0.069，corr_vs_ref=0.30（独立，非 shadow）。",
     "expected_sign": -1},
    {"id": "S32A2", "operator": "atomic", "left": _REL_MAXDD, "right": _REL_MAXDD,
     "mechanism": "s32_rel_maxdd_atomic",
     "hypothesis": "REL_MAXDD_CATEGORY_20（本 ETF 最大回撤 − 类别均值，20 日均值）单原子门 7 重裁。体检 disc_ic −0.091，与 INTRADAY_MAXDD_20 corr=0.88（shadow，冗余风险高）。",
     "expected_sign": -1},
    {"id": "S32A3", "operator": "atomic", "left": _REL_RECOVERY, "right": _REL_RECOVERY,
     "mechanism": "s32_rel_recovery_atomic",
     "hypothesis": "REL_RECOVERY_TIME_CATEGORY_20（恢复时间占比 − 类别均值，20 日均值）单原子门 7 重裁。体检 disc_ic −0.048，与 RECOVERY_TIME_FRAC_20 corr=0.91（shadow）。",
     "expected_sign": -1},
    {"id": "S32A4", "operator": "atomic", "left": _REL_ON_PREM, "right": _REL_ON_PREM,
     "mechanism": "s32_rel_on_prem_atomic",
     "hypothesis": "REL_ON_PREM_CATEGORY_20（隔夜收益 20 日均值 − 类别均值，本原子新建 ON_PREM_20 基础值——本线此前从未注册过该原子的裸 20 日均值级别）单原子门 7 重裁。体检 disc_ic 0.018，corr_vs_ref=0.46（独立，非 shadow）。",
     "expected_sign": 1},
    {"id": "S32A5", "operator": "atomic", "left": _REL_ON_VAR, "right": _REL_ON_VAR,
     "mechanism": "s32_rel_on_var_atomic",
     "hypothesis": "REL_ON_VAR_SHARE_CATEGORY_20（隔夜方差占比 − 类别均值，20 日均值）单原子门 7 重裁。体检 disc_ic 0.058，与 YZ_OVERNIGHT_SHARE_20 corr=0.92（shadow）。",
     "expected_sign": 1},
    {"id": "S32A6", "operator": "atomic", "left": _REL_MFI, "right": _REL_MFI,
     "mechanism": "s32_rel_mfi_atomic",
     "hypothesis": "REL_MFI_EXTREME_CATEGORY_20（MFI 极值占比 − 类别均值，20 日均值）单原子门 7 重裁。体检 disc_ic 0.093（本批最强），与 MFI_EXTREME_FRAC_20 corr=0.93（shadow）。",
     "expected_sign": 1},
    {"id": "S32A7", "operator": "atomic", "left": _REL_LUNCH, "right": _REL_LUNCH,
     "mechanism": "s32_rel_lunch_atomic",
     "hypothesis": "REL_LUNCH_POSTRUN_CATEGORY_20（午后抢跑量占比 − 类别均值，20 日均值）单原子门 7 重裁。体检 disc_ic 0.011，与 LUNCH_POST_RUN_20 corr=0.87（shadow）。",
     "expected_sign": 1},
    # ---- 14 pairs (2 right legs per left atom, priority rights per directive) ----
    {"id": "S32P1", "operator": "rank_spread", "left": _REL_UW_CHG, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s32_p1", "hypothesis": "REL_UNDERWATER_CATEGORY_CHG_20 × R_LOG_AMOUNT_VOL_20（主控优先右腿，S26R）。方向由发现期定。", "expected_sign": -1},
    {"id": "S32P2", "operator": "rank_spread", "left": _REL_UW_CHG, "right": _MFI_EXTREME,
     "mechanism": "s32_p2", "hypothesis": "REL_UNDERWATER_CATEGORY_CHG_20 × MFI_EXTREME_FRAC_20（主控优先右腿）。方向由发现期定。", "expected_sign": -1},
    {"id": "S32P3", "operator": "rank_spread", "left": _REL_MAXDD, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s32_p3", "hypothesis": "REL_MAXDD_CATEGORY_20 × R_LOG_AMOUNT_VOL_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S32P4", "operator": "rank_spread", "left": _REL_MAXDD, "right": _D1_LEVEL,
     "mechanism": "s32_p4", "hypothesis": "REL_MAXDD_CATEGORY_20 × D1_LEVEL_60（S20）。方向由发现期定。", "expected_sign": -1},
    {"id": "S32P5", "operator": "rank_spread", "left": _REL_RECOVERY, "right": _MFI_EXTREME,
     "mechanism": "s32_p5", "hypothesis": "REL_RECOVERY_TIME_CATEGORY_20 × MFI_EXTREME_FRAC_20（主控优先右腿）。方向由发现期定。", "expected_sign": -1},
    {"id": "S32P6", "operator": "rank_spread", "left": _REL_RECOVERY, "right": _VT_GINI,
     "mechanism": "s32_p6", "hypothesis": "REL_RECOVERY_TIME_CATEGORY_20 × VT_BUCKET_GINI_20（S24）。方向由发现期定。", "expected_sign": -1},
    {"id": "S32P7", "operator": "rank_spread", "left": _REL_ON_PREM, "right": _UW_CHG,
     "mechanism": "s32_p7", "hypothesis": "REL_ON_PREM_CATEGORY_20 × UNDERWATER_FRAC_CHG_20（主控优先右腿，本线历史最强单原子）。方向由发现期定。", "expected_sign": 1},
    {"id": "S32P8", "operator": "rank_spread", "left": _REL_ON_PREM, "right": _HAR_RESID,
     "mechanism": "s32_p8", "hypothesis": "REL_ON_PREM_CATEGORY_20 × S28_VOV_HAR_RESID_20（S28）。方向由发现期定。", "expected_sign": 1},
    {"id": "S32P9", "operator": "rank_spread", "left": _REL_ON_VAR, "right": _D1_LEVEL,
     "mechanism": "s32_p9", "hypothesis": "REL_ON_VAR_SHARE_CATEGORY_20 × D1_LEVEL_60。方向由发现期定。", "expected_sign": 1},
    {"id": "S32P10", "operator": "rank_spread", "left": _REL_ON_VAR, "right": _VT_GINI,
     "mechanism": "s32_p10", "hypothesis": "REL_ON_VAR_SHARE_CATEGORY_20 × VT_BUCKET_GINI_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S32P11", "operator": "rank_spread", "left": _REL_MFI, "right": _UW_CHG,
     "mechanism": "s32_p11", "hypothesis": "REL_MFI_EXTREME_CATEGORY_20 × UNDERWATER_FRAC_CHG_20（主控优先右腿，避免与 MFI_EXTREME_FRAC_20 自身配对造成同源冗余）。方向由发现期定。", "expected_sign": 1},
    {"id": "S32P12", "operator": "rank_spread", "left": _REL_MFI, "right": _HAR_RESID,
     "mechanism": "s32_p12", "hypothesis": "REL_MFI_EXTREME_CATEGORY_20 × S28_VOV_HAR_RESID_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S32P13", "operator": "rank_spread", "left": _REL_LUNCH, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s32_p13", "hypothesis": "REL_LUNCH_POSTRUN_CATEGORY_20 × R_LOG_AMOUNT_VOL_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S32P14", "operator": "rank_spread", "left": _REL_LUNCH, "right": _MFI_EXTREME,
     "mechanism": "s32_p14", "hypothesis": "REL_LUNCH_POSTRUN_CATEGORY_20 × MFI_EXTREME_FRAC_20。本轮末条。方向由发现期定。", "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
