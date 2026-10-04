#!/usr/bin/env python3
"""Round 118 driver: stage 18 step 3 — lunch pairing batch 2 (24 pairs).
Remaining lunch x verified-leg combinations. All-new pairs, cross-family."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_118"

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
    ("CK01", PR, "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "prerun_bigbar",
     "PRERUN 收尾：午前抢跑 × 大 bar 强度（+0.0832/+0.0548/t2.92/+41.6bp），延续。"),
    ("CK02", PR, "SIGN_ACF1_5", "serial_dependence", "prerun_acf",
     "PRERUN 收尾：午前抢跑 × 动量确认（−0.0211/+0.0070/t0.12/+3.9bp），延续。"),
    ("CK03", PR, "PRICE_POSITION_20", "price_location", "prerun_position",
     "PRERUN 收尾：午前抢跑 × 获利位置（+0.0128/+0.0275/t1.64/+8.5bp），延续。"),
    ("CK04", PR, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "prerun_close5",
     "PRERUN 收尾：午前抢跑 × 收盘确认（−0.0233/−0.0313/t−0.30/+27.3bp），延续。"),
    ("CK05", PO, "RESILIENCY_20", "liquidity_commonality_1m", "postrun_resilient",
     "POST_RUN 收尾：午后抢跑 × 微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp），延续。"),
    ("CK06", PO, "ULCER_20", "downside_risk", "postrun_healthy",
     "POST_RUN 收尾：午后抢跑 × 溃疡浅（−0.0415/−0.0607/t0.76/+10.7bp），延续。"),
    ("CK07", PO, "CHIP_RANGE_90_60", "cost_distribution", "postrun_chip",
     "POST_RUN 收尾：午后抢跑 × 筹码集中（−0.0574/−0.0620/t0.70/+14.6bp），延续。"),
    ("CK08", PO, "WORST_DAY_20", "return_tail_shape", "postrun_no_damage",
     "POST_RUN 收尾：午后抢跑 × 无极端损伤（+0.0635/+0.0648/t2.18/+16.2bp），延续。"),
    ("CK09", PO, "PRICE_POSITION_20", "price_location", "postrun_position",
     "POST_RUN 收尾：午后抢跑 × 获利位置（+0.0128/+0.0275/t1.64/+8.5bp），延续。"),
    ("CK10", PO, "SIGN_ACF1_5", "serial_dependence", "postrun_acf",
     "POST_RUN 收尾：午后抢跑 × 动量确认（−0.0211/+0.0070/t0.12/+3.9bp），延续。"),
    ("CK11", GA, "RESILIENCY_20", "liquidity_commonality_1m", "gapabs_resilient",
     "GAP_ABS 收尾：跳空幅度 × 微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp），延续。"),
    ("CK12", GA, "WORST_DAY_20", "return_tail_shape", "gapabs_no_damage",
     "GAP_ABS 收尾：跳空幅度 × 无极端损伤（+0.0635/+0.0648/t2.18/+16.2bp），延续。"),
    ("CK13", GA, "LOG_AMOUNT_VOL_20", "liquidity_variability", "gapabs_activity",
     "GAP_ABS 收尾：跳空幅度 × 高活跃（+0.0661/+0.0701/t2.23/+36.8bp），延续。"),
    ("CK14", GA, "SIGN_ACF1_5", "serial_dependence", "gapabs_acf",
     "GAP_ABS 收尾：跳空幅度 × 动量确认（−0.0211/+0.0070/t0.12/+3.9bp），延续。"),
    ("CK15", RC, "ULCER_20", "downside_risk", "amcorr_healthy",
     "RET_CORR 收尾：时段相关 × 溃疡浅（−0.0415/−0.0607/t0.76/+10.7bp），延续。"),
    ("CK16", RC, "PRICE_POSITION_20", "price_location", "amcorr_position",
     "RET_CORR 收尾：时段相关 × 获利位置（+0.0128/+0.0275/t1.64/+8.5bp），延续。"),
    ("CK17", RC, "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "amcorr_bigbar",
     "RET_CORR 收尾：时段相关 × 大 bar 强度（+0.0832/+0.0548/t2.92/+41.6bp），延续。"),
    ("CK18", RC, "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "amcorr_open30",
     "RET_CORR 收尾：时段相关 × 开盘配置（−0.1038/−0.0489/t3.30/−10.5bp），延续。"),
    ("CK19", LG, "CHIP_RANGE_90_60", "cost_distribution", "lunchgap_chip",
     "LUNCH_GAP 收尾：午间跳空 × 筹码集中（−0.0574/−0.0620/t0.70/+14.6bp），延续。"),
    ("CK20", LG, "ULCER_20", "downside_risk", "lunchgap_healthy",
     "LUNCH_GAP 收尾：午间跳空 × 健康结构，延续。"),
    ("CK21", LG, "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "lunchgap_profile",
     "LUNCH_GAP 收尾：午间跳空 × 量轮廓异常（+0.0952/+0.0442/t4.04/+10.1bp），延续。"),
    ("CK22", LG, "SIGN_ACF1_5", "serial_dependence", "lunchgap_acf",
     "LUNCH_GAP 收尾：午间跳空 × 动量确认（−0.0211/+0.0070/t0.12/+3.9bp），延续。"),
    ("CK23", LR, "LOG_AMOUNT_VOL_20", "liquidity_variability", "lunchrevert_activity",
     "LUNCH_REVERT 收尾：午间回复 × 高活跃（+0.0661/+0.0701/t2.23/+36.8bp），延续。"),
    ("CK24", LR, "TICK_IMBALANCE_20", "bar_size_order_flow", "lunchrevert_buyflow",
     "LUNCH_REVERT 收尾：午间回复 × 主买不平衡（−0.0116/+0.0002/t1.01/+4.7bp），延续。"),
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
    plan["pairing_note"] = "第 18 阶段配对第 2 批：lunch 各腿剩余垂直组合；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage18

if __name__ == "__main__":
    base.main()
