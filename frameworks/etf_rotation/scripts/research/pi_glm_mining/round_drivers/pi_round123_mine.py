#!/usr/bin/env python3
"""Round 123 driver: stage 18 step 3 — lunch pairing batch 7 (24 pairs).
Remaining untested lunch verticals (VT/auction/overnight legs). Zero streak 1/3."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_123"

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
LG = "LUNCH_GAP_20"
LR = "LUNCH_REVERT15_20"

P = [
    ("CP01", LG, "VT_SKEW_20", "volume_time_1m", "lunchgap_vtskew",
     "LG×VT 残余：午间跳空 × 体量时间偏度，延续。"),
    ("CP02", LG, "VT_TAIL_MOM_20", "volume_time_1m", "lunchgap_vttail",
     "LG×VT 残余：午间跳空 × 尾桶动量，延续。"),
    ("CP03", LG, "VT_BUCKET_COUNT_SHIFT_20", "volume_time_1m", "lunchgap_vtcount",
     "LG×VT 残余：午间跳空 × 活跃度趋势，延续。"),
    ("CP04", LG, "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "lunchgap_lbar",
     "LG×LBAR 残余：午间跳空 × 体量钟离散（BF1 同腿），延续。"),
    ("CP05", LG, "VT_RV_RATIO_20", "volume_time_1m", "lunchgap_vtrv",
     "LG×VT 残余：午间跳空 × 体量波动集中，延续。"),
    ("CP06", LG, "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "lunchgap_open30",
     "LG×profile 残余：午间跳空 × 开盘配置（CL09 同腿），延续。"),
    ("CP07", LR, "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "lunchrevert_bec",
     "LR 残余：午间回复 × 大 bar 时点集中，延续。"),
    ("CP08", LR, "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "lunchrevert_dirskew",
     "LR 残余：午间回复 × 方向偏度，延续。"),
    ("CP09", LR, "AUC_DISCOVERY_SHIFT_20", "auction_1m", "lunchrevert_disc",
     "LR 残余：午间回复 × 价格发现重心，延续。"),
    ("CP10", LR, "VT_RV_RATIO_20", "volume_time_1m", "lunchrevert_vtrv",
     "LR 残余：午间回复 × 体量波动集中，延续。"),
    ("CP11", LR, "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "lunchrevert_lbar",
     "LR 残余：午间回复 × 体量钟离散，延续。"),
    ("CP12", LR, "ON_CONT_20", "overnight_structure_1d", "lunchrevert_oncont",
     "LR×overnight 残余：午间回复 × 隔夜延续度，延续。"),
    ("CP13", GA, "VT_BUCKET_COUNT_SHIFT_20", "volume_time_1m", "gapabs_vtcount",
     "GA×VT 残余：跳空幅度 × 活跃度趋势，延续。"),
    ("CP14", GA, "VT_RV_RATIO_20", "volume_time_1m", "gapabs_vtrv",
     "GA×VT 残余：跳空幅度 × 体量波动集中，延续。"),
    ("CP15", GA, "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "gapabs_lbar",
     "GA×LBAR 残余：跳空幅度 × 体量钟离散，延续。"),
    ("CP16", GA, "ON_CONT_20", "overnight_structure_1d", "gapabs_oncont",
     "GA×overnight 残余：跳空幅度 × 隔夜延续度，延续。"),
    ("CP17", GA, "GAP_FILL_RATE_20", "overnight_structure_1d", "gapabs_gapfill",
     "GA×overnight 残余：跳空幅度 × 缺口修复率（CN03 同腿），延续。"),
    ("CP18", GA, "SHARE_RET_CORR_20", "fund_flow", "gapabs_share",
     "GA 残余：跳空幅度 × 一级流解释力，延续。"),
    ("CP19", RC, "VT_BUCKET_GINI_20", "volume_time_1m", "amcorr_vtgini",
     "RC×VT 残余：时段相关 × 桶到达 Gini，延续。"),
    ("CP20", RC, "VT_TAIL_MOM_20", "volume_time_1m", "amcorr_vttail",
     "RC×VT 残余：时段相关 × 尾桶动量，延续。"),
    ("CP21", RC, "VT_BUCKET_COUNT_SHIFT_20", "volume_time_1m", "amcorr_vtcount",
     "RC×VT 残余：时段相关 × 活跃度趋势，延续。"),
    ("CP22", RC, "ON_CONT_20", "overnight_structure_1d", "amcorr_oncont",
     "RC×overnight 残余：时段相关 × 隔夜延续度，延续。"),
    ("CP23", PR, "VT_BUCKET_GINI_20", "volume_time_1m", "prerun_vtgini",
     "PR×VT 残余：午前抢跑 × 桶到达 Gini，延续。"),
    ("CP24", PO, "AUC_DISCOVERY_SHIFT_20", "auction_1m", "postrun_disc",
     "PO 残余：午后抢跑 × 价格发现重心，延续。"),
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
    plan["pairing_note"] = "第 18 阶段配对第 7 批：lunch 残余未测域（VT/auction/overnight）；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage18

if __name__ == "__main__":
    base.main()
