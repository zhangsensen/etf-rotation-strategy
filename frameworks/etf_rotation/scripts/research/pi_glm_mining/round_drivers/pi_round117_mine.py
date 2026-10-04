#!/usr/bin/env python3
"""Round 117 driver: stage 18 step 3 — lunch pairing batch 1 (24 pairs).
Lunch skeleton vertical rotations + cross-new-family pairs (lunch x
overnight/impact/volume_time). All-new pairs, cross-family only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_117"

LB = "lunch_break_1m"
ID = "impact_decay_1m"
VT = "volume_time_1m"
ON = "overnight_structure_1d"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


PR = "LUNCH_PRE_RUN_20"
RC = "AM_PM_RET_CORR_20"
PO = "LUNCH_POST_RUN_20"

P = [
    ("CJ01", PR, "TICK_IMBALANCE_20", "bar_size_order_flow", "prerun_buyflow",
     "午前抢跑 × 主买不平衡，延续。"),
    ("CJ02", PR, "RESILIENCY_20", "liquidity_commonality_1m", "prerun_resilient",
     "午前抢跑 × 微结构弹性，延续。"),
    ("CJ03", PR, "GAP_FILL_FRACTION_60", "gap_repair", "prerun_trend",
     "午前抢跑 × 趋势持续，延续。"),
    ("CJ04", PR, "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "prerun_profile",
     "午前抢跑 × 量轮廓异常，延续。"),
    ("CJ05", PR, "CHIP_RANGE_90_60", "cost_distribution", "prerun_chip",
     "午前抢跑 × 筹码集中，延续。"),
    ("CJ06", PR, "ULCER_20", "downside_risk", "prerun_healthy",
     "午前抢跑 × 健康结构，延续。"),
    ("CJ07", PR, "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "prerun_open30",
     "午前抢跑 × 开盘配置，延续。"),
    ("CJ08", PR, "WORST_DAY_20", "return_tail_shape", "prerun_no_damage",
     "午前抢跑 × 无极端损伤，延续。"),
    ("CJ09", RC, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "amcorr_close_confirm",
     "时段相关 × 收盘确认，延续。"),
    ("CJ10", RC, "CHIP_RANGE_90_60", "cost_distribution", "amcorr_chip",
     "时段相关 × 筹码集中，延续。"),
    ("CJ11", RC, "TICK_IMBALANCE_20", "bar_size_order_flow", "amcorr_buyflow",
     "时段相关 × 主买不平衡，延续。"),
    ("CJ12", RC, "GAP_FILL_FRACTION_60", "gap_repair", "amcorr_trend",
     "时段相关 × 趋势持续，延续。"),
    ("CJ13", RC, LB, "PV_ELASTICITY_20", ID, "amcorr_elasticity",
     "新×新：时段相关 × 量价弹性（CA1 入选 −0.1249/−0.0638/t4.00/+52.3bp），延续。"),
    ("CJ14", PO, "TICK_IMBALANCE_20", "bar_size_order_flow", "postrun_buyflow",
     "午后抢跑 × 主买不平衡，延续。"),
    ("CJ15", PO, "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "postrun_events",
     "午后抢跑 × 事件密集，延续。"),
    ("CJ16", PO, "LOG_AMOUNT_VOL_20", "liquidity_variability", "postrun_activity",
     "午后抢跑 × 高活跃，延续。"),
    ("CJ17", "LUNCH_GAP_20", "LOG_AMOUNT_VOL_20", "liquidity_variability", "lunchgap_activity",
     "午间跳空 × 高活跃，延续。"),
    ("CJ18", "LUNCH_GAP_20", "IMP_PERM_SHARE_20", "impact_decay_1m", "lunchgap_permanence",
     "新×新：午间跳空 × 冲击永久份额（CA2 入选），延续。"),
    ("CJ19", "LUNCH_GAP_ABS_20", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "lunchgapabs_events",
     "午间跳空幅度 × 事件密集，延续。"),
    ("CJ20", "LUNCH_REVERT15_20", "ULCER_20", "downside_risk", "lunchrevert_healthy",
     "午间回复 × 健康结构，延续。"),
    ("CJ21", "ON_CONT_20", ON, "LUNCH_GAP_20", "lunch_break_1m", "oncont_lunchgap",
     "新×新（跨扩展族）：隔夜延续度 × 午间跳空，延续。"),
    ("CJ22", "ON_PREM_20", ON, "LUNCH_REVERT15_20", "lunch_break_1m", "onprem_lunchrevert",
     "新×新（跨扩展族）：隔夜溢价 × 午间回复，延续。"),
    ("CJ23", PR, "VT_AUTOCORR_20", VT, "prerun_vt_acf",
     "新×新（跨扩展族）：午前抢跑 × 体量时间趋势自相关（DA2 入选），延续。"),
    ("CJ24", PO, "VT_AUTOCORR_20", VT, "postrun_vt_acf",
     "新×新（跨扩展族）：午后抢跑 × 体量时间趋势自相关（DA2 入选），延续。"),
]

base.CANDIDATES = [
    _pair(rec[0], rec[1], LB, rec[2], rec[3], rec[4], rec[5])
    if len(rec) == 6 else _pair(*rec) for rec in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage18(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage18_lunch_pairing"
    plan["pairing_note"] = "第 18 阶段配对第 1 批：lunch 骨架垂直轮换 + 跨新家族（overnight/impact/volume_time）；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage18

if __name__ == "__main__":
    base.main()
