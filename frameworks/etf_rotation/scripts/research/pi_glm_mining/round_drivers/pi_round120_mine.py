#!/usr/bin/env python3
"""Round 120 driver: stage 18 step 3 — lunch pairing batch 4 (24 pairs).
Lunch x auction/impact untested domain. All-new pairs, cross-family only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_120"

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
ID = "impact_decay_1m"
AU = "auction_1m"

P = [
    ("CM01", LG, "HIVOL_RET5_20", ID, "lunchgap_hivol",
     "CM01 主控点 1：高量后收益 × 午间跳空（双臂 t0.55/0.71），延续。"),
    ("CM02", LG, "LOVOL_RET5_20", ID, "lunchgap_lovol",
     "点 1：低量后延续 × 午间跳空（双臂 t0.72/1.42），延续。"),
    ("CM03", LG, "PRICE_POSITION_20", "price_location", "lunchgap_pp",
     "点 1：获利位置 × 午间跳空，延续。"),
    ("CM04", LG, "TICK_IMBALANCE_20", "bar_size_order_flow", "lunchgap_tick",
     "点 1：主买不平衡 × 午间跳空，延续。"),
    ("CM05", LG, "AUC_CLOSE_VOLSHARE_20", AU, "lunchgap_closevol",
     "点 1：收盘竞价份额 × 午间跳空，延续。"),
    ("CM06", LG, "AUC_VARIANCE_RATIO_20", AU, "lunchgap_varratio",
     "点 1：开收方差比 × 午间跳空，延续。"),
    ("CM07", LG, "AUC_OPEN_ABSORB_20", AU, "lunchgap_absorb",
     "点 1：开盘吸收度 × 午间跳空，延续。"),
    ("CM08", LG, "AUC_POST_OPEN_REVERT_20", AU, "lunchgap_revert",
     "点 1：开盘冲击回复 × 午间跳空，延续。"),
    ("CM09", LR, "HIVOL_RET5_20", ID, "lunchrevert_hivol",
     "点 1：高量后收益 × 午间回复，延续。"),
    ("CM10", LR, "PRICE_POSITION_20", "price_location", "lunchrevert_pp",
     "点 1：获利位置 × 午间回复，延续。"),
    ("CM11", LR, "CHIP_RANGE_90_60", "cost_distribution", "lunchrevert_chip",
     "点 1：筹码集中 × 午间回复，延续。"),
    ("CM12", LR, "AUC_CLOSE_VOLSHARE_20", AU, "lunchrevert_closevol",
     "点 1：收盘竞价份额 × 午间回复，延续。"),
    ("CM13", LR, "AUC_VARIANCE_RATIO_20", AU, "lunchrevert_varratio",
     "点 1：开收方差比 × 午间回复，延续。"),
    ("CM14", LR, "AUC_POST_OPEN_REVERT_20", AU, "lunchrevert_openrevert",
     "点 1：开盘冲击回复 × 午间回复，延续。"),
    ("CM15", LR, "AUC_OPEN_ABSORB_20", AU, "lunchrevert_absorb",
     "点 1：开盘吸收度 × 午间回复，延续。"),
    ("CM16", LR, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "lunchrevert_close5",
     "点 1：收盘确认 × 午间回复，延续。"),
    ("CM17", GA, "HIVOL_RET5_20", ID, "gapabs_hivol",
     "点 1：高量后收益 × 跳空幅度，延续。"),
    ("CM18", GA, "AUC_CLOSE_VOLSHARE_20", AU, "gapabs_closevol",
     "点 1：收盘竞价份额 × 跳空幅度，延续。"),
    ("CM19", GA, "AUC_VARIANCE_RATIO_20", AU, "gapabs_varratio",
     "点 1：开收方差比 × 跳空幅度，延续。"),
    ("CM20", GA, "TICK_IMBALANCE_20", "bar_size_order_flow", "gapabs_tick",
     "点 1：主买不平衡 × 跳空幅度，延续。"),
    ("CM21", GA, "AUC_DISCOVERY_SHIFT_20", AU, "gapabs_disc",
     "点 1：价格发现重心 × 跳空幅度，延续。"),
    ("CM22", PR, "AUC_DISCOVERY_SHIFT_20", AU, "prerun_disc",
     "点 1：价格发现重心 × 午前抢跑，延续。"),
    ("CM23", PO, "LOVOL_RET5_20", ID, "postrun_lovol",
     "点 1：低量后延续 × 午后抢跑，延续。"),
    ("CM24", RC, "AUC_CLOSE_VOLSHARE_20", AU, "amcorr_closevol",
     "点 1：收盘竞价份额 × 时段相关，延续。"),
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
    plan["pairing_note"] = "第 18 阶段配对第 4 批：lunch×auction/impact 未测域；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage18

if __name__ == "__main__":
    base.main()

