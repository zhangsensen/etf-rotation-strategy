#!/usr/bin/env python3
"""Round 122 driver: stage 18 step 3 — lunch pairing batch 6 (24 pairs).
Identity-near-miss leg swaps + lunch x overnight/impact remaining domain."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_122"

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
ON = "overnight_structure_1d"

P = [
    ("CO01", LG, "IMP_DECAY_SLOPE_20", ID, "lunchgap_decay",
     "CN06/07 identity 族换腿：午间跳空 × 冲击衰减斜率，延续。"),
    ("CO02", LG, "PV_SIGNFLIP_20", ID, "lunchgap_signflip",
     "identity 族换腿：午间跳空 × 量价符号翻转，延续。"),
    ("CO03", LG, "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "lunchgap_bec",
     "identity 族换腿：午间跳空 × 大 bar 时点集中，延续。"),
    ("CO04", LG, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "lunchgap_close5",
     "identity 族换腿：午间跳空 × 收盘确认，延续。"),
    ("CO05", LG, "ON_PREM_20", ON, "lunchgap_onprem",
     "跨扩展族（新×新）：午间跳空 × 隔夜溢价（CY07/CZ01 同腿），延续。"),
    ("CO06", LG, "SHARE_RET_CORR_20", "fund_flow", "lunchgap_share",
     "identity 族换腿：午间跳空 × 一级流解释力，延续。"),
    ("CO07", LR, "IMP_PERM_SHARE_20", ID, "lunchrevert_perm",
     "CN13 identity 族换腿：午间回复 × 冲击永久份额，延续。"),
    ("CO08", LR, "IMP_DECAY_SLOPE_20", ID, "lunchrevert_decay",
     "CN13 骨架（t3.52）换腿：午间回复 × 冲击衰减斜率，延续。"),
    ("CO09", LR, "PV_SIGNFLIP_20", ID, "lunchrevert_signflip",
     "CN13 骨架换腿：午间回复 × 量价符号翻转，延续。"),
    ("CO10", LR, "SIGN_ACF1_5", "serial_dependence", "lunchrevert_acf",
     "REVERT 残余：午间回复 × 动量确认，延续。"),
    ("CO11", LR, "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "lunchrevert_vpd",
     "REVERT 残余：午间回复 × 量轮廓异常，延续。"),
    ("CO12", LR, "SHARE_RET_CORR_20", "fund_flow", "lunchrevert_share",
     "REVERT 残余：午间回复 × 一级流解释力，延续。"),
    ("CO13", LR, "VT_AUTOCORR_20", "volume_time_1m", "lunchrevert_vtacf",
     "REVERT 残余：午间回复 × 体量时间自相关（DA2 同腿，影子风险已记），延续。"),
    ("CO14", GA, "AUC_OPEN_ABSORB_20", "auction_1m", "gapabs_absorb",
     "GA 残余：跳空幅度 × 开盘吸收度，延续。"),
    ("CO15", GA, "IMP_DECAY_SLOPE_20", ID, "gapabs_decay",
     "GA 残余：跳空幅度 × 冲击衰减斜率，延续。"),
    ("CO16", GA, "PV_SIGNFLIP_20", ID, "gapabs_signflip",
     "GA 残余：跳空幅度 × 量价符号翻转，延续。"),
    ("CO17", GA, "ON_PREM_20", ON, "gapabs_onprem",
     "跨扩展族（新×新）：跳空幅度 × 隔夜溢价，延续。"),
    ("CO18", GA, "VT_TAIL_MOM_20", "volume_time_1m", "gapabs_vttail",
     "GA 残余：跳空幅度 × 尾桶动量，延续。"),
    ("CO19", RC, "IMP_DECAY_SLOPE_20", ID, "amcorr_decay",
     "RC 残余：时段相关 × 冲击衰减斜率，延续。"),
    ("CO20", RC, "AUC_OPEN_ABSORB_20", "auction_1m", "amcorr_absorb",
     "RC 残余：时段相关 × 开盘吸收度，延续。"),
    ("CO21", RC, "ON_PREM_20", ON, "amcorr_onprem",
     "跨扩展族（新×新）：时段相关 × 隔夜溢价，延续。"),
    ("CO22", PR, "IMP_DECAY_SLOPE_20", ID, "prerun_decay",
     "PR 残余：午前抢跑 × 冲击衰减斜率，延续。"),
    ("CO23", PR, "ON_PREM_20", ON, "prerun_onprem",
     "跨扩展族（新×新）：午前抢跑 × 隔夜溢价，延续。"),
    ("CO24", PO, "PV_ELASTICITY_20", ID, "postrun_elastic",
     "PO 残余：午后抢跑 × 量价弹性（CA1 同腿），延续。"),
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
    plan["pairing_note"] = "第 18 阶段配对第 6 批：identity 近失族换腿 + lunch×overnight/impact 残余；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage18

if __name__ == "__main__":
    base.main()
