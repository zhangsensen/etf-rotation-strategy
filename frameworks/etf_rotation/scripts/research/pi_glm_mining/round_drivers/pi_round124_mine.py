#!/usr/bin/env python3
"""Round 124 driver: stage 18 step 3 — lunch pairing batch 8 (24 pairs, final sweep).
Remaining PR/PO/RC/GA/LR verticals. Zero streak 2/3 — zero here exhausts stage 18."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_124"

LB = "lunch_break_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


PR = "LUNCH_PRE_RUN_20"
PO = "LUNCH_POST_RUN_20"
GA = "LUNCH_GAP_ABS_20"
RC = "AM_PM_RET_CORR_20"
LR = "LUNCH_REVERT15_20"

P = [
    ("CQ01", PR, "AUC_OPEN_VOLSHARE_20", "auction_1m", "prerun_openvol",
     "收官：午前抢跑 × 开盘竞价份额，延续。"),
    ("CQ02", PR, "AUC_CLOSE_CONSIST_20", "auction_1m", "prerun_closeconsist",
     "收官：午前抢跑 × 尾盘方向一致度，延续。"),
    ("CQ03", PR, "AUC_POST_OPEN_REVERT_20", "auction_1m", "prerun_openrevert",
     "收官：午前抢跑 × 开盘冲击回复，延续。"),
    ("CQ04", PR, "AUC_CLOSE_VOLSHARE_20", "auction_1m", "prerun_closevol",
     "收官：午前抢跑 × 收盘竞价份额，延续。"),
    ("CQ05", PR, "AUC_VARIANCE_RATIO_20", "auction_1m", "prerun_varratio",
     "收官：午前抢跑 × 开收方差比（CM06 同腿），延续。"),
    ("CQ06", PR, "VT_SKEW_20", "volume_time_1m", "prerun_vtskew",
     "收官：午前抢跑 × 体量时间偏度，延续。"),
    ("CQ07", PR, "VT_TAIL_MOM_20", "volume_time_1m", "prerun_vttail",
     "收官：午前抢跑 × 尾桶动量，延续。"),
    ("CQ08", PR, "VT_BUCKET_COUNT_SHIFT_20", "volume_time_1m", "prerun_vtcount",
     "收官：午前抢跑 × 活跃度趋势，延续。"),
    ("CQ09", PO, "IMP_DECAY_SLOPE_20", "impact_decay_1m", "postrun_decay",
     "收官：午后抢跑 × 冲击衰减斜率，延续。"),
    ("CQ10", PO, "PV_SIGNFLIP_20", "impact_decay_1m", "postrun_signflip",
     "收官：午后抢跑 × 量价符号翻转，延续。"),
    ("CQ11", PO, "AUC_OPEN_ABSORB_20", "auction_1m", "postrun_absorb",
     "收官：午后抢跑 × 开盘吸收度，延续。"),
    ("CQ12", PO, "AUC_POST_OPEN_REVERT_20", "auction_1m", "postrun_openrevert",
     "收官：午后抢跑 × 开盘冲击回复，延续。"),
    ("CQ13", PO, "AUC_VARIANCE_RATIO_20", "auction_1m", "postrun_varratio",
     "收官：午后抢跑 × 开收方差比（CM06 同腿），延续。"),
    ("CQ14", PO, "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "postrun_lbar",
     "收官：午后抢跑 × 体量钟离散，延续。"),
    ("CQ15", PO, "ON_CONT_20", "overnight_structure_1d", "postrun_oncont",
     "收官：午后抢跑 × 隔夜延续度，延续。"),
    ("CQ16", PO, "GAP_FILL_RATE_20", "overnight_structure_1d", "postrun_gapfill",
     "收官：午后抢跑 × 缺口修复率，延续。"),
    ("CQ17", RC, "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "amcorr_lbar",
     "收官：时段相关 × 体量钟离散，延续。"),
    ("CQ18", RC, "VT_RV_RATIO_20", "volume_time_1m", "amcorr_vtrv",
     "收官：时段相关 × 体量波动集中，延续。"),
    ("CQ19", RC, "GAP_FILL_RATE_20", "overnight_structure_1d", "amcorr_gapfill",
     "收官：时段相关 × 缺口修复率，延续。"),
    ("CQ20", RC, "AUC_POST_OPEN_REVERT_20", "auction_1m", "amcorr_openrevert",
     "收官：时段相关 × 开盘冲击回复，延续。"),
    ("CQ21", GA, "VT_AUTOCORR_20", "volume_time_1m", "gapabs_vtacf",
     "收官：跳空幅度 × 体量时间自相关（DA2 同腿），延续。"),
    ("CQ22", GA, "LOVOL_RET5_20", "impact_decay_1m", "gapabs_lovol",
     "收官：跳空幅度 × 低量后延续（GKM 腿），延续。"),
    ("CQ23", GA, "AUC_OPEN_VOLSHARE_20", "auction_1m", "gapabs_openvol",
     "收官：跳空幅度 × 开盘竞价份额，延续。"),
    ("CQ24", LR, "VT_SKEW_20", "volume_time_1m", "lunchrevert_vtskew",
     "收官：午间回复 × 体量时间偏度，延续。"),
]

base.CANDIDATES = [
    _pair(cid, left, LB, right, rsrc, mech, hyp) for cid, left, right, rsrc, mech, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage18(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage18_lunch_pairing"
    plan["pairing_note"] = "第 18 阶段配对第 8 批（收官扫尾）：PR/PO/RC/GA/LR 残余垂直；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage18

if __name__ == "__main__":
    base.main()
