#!/usr/bin/env python3
"""Round 108 driver: stage 17 extension pairing batch 2 (24 pairs).
CX12 skeleton rotation (ONPREM x remaining verticals), ONCONT/GAPFILL
remaining legs, and overnight x impact/largebar/volume_time newxnew."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_108"

ON = "overnight_structure_1d"
ID = "impact_decay_1m"
LB = "largebar_footprint_1m"
VT = "volume_time_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


OP = "ON_PREM_20"   # CX12 骨架（+41.3bp）
OC = "ON_CONT_20"
G = "GAP_FILL_RATE_20"

P = [
    ("CY01", OP, "TICK_IMBALANCE_20", "bar_size_order_flow", "onprem_buyflow",
     "CX12 骨架轮换：隔夜溢价 × 主买不平衡（−0.0116/+0.0002/t1.01/+4.7bp），延续。"),
    ("CY02", OP, "RESILIENCY_20", "liquidity_commonality_1m", "onprem_resilient",
     "骨架轮换：隔夜溢价 × 微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp），延续。"),
    ("CY03", OP, "GAP_FILL_FRACTION_60", "gap_repair", "onprem_trend_persist",
     "骨架轮换：隔夜溢价 × 趋势持续（−0.0597/−0.0430/t2.59/+9.8bp），延续。"),
    ("CY04", OP, "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "onprem_profile_anomaly",
     "骨架轮换：隔夜溢价 × 量轮廓异常（+0.0952/+0.0442/t4.04/+10.1bp），延续。"),
    ("CY05", OP, "CHIP_RANGE_90_60", "cost_distribution", "onprem_chip_lock",
     "骨架轮换：隔夜溢价 × 筹码集中（−0.0574/−0.0620/t0.70/+14.6bp），延续。"),
    ("CY06", OP, "ULCER_20", "downside_risk", "onprem_healthy",
     "骨架轮换：隔夜溢价 × 溃疡浅（−0.0415/−0.0607/t0.76/+10.7bp），延续。"),
    ("CY07", OP, "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "onprem_open_config",
     "骨架轮换：隔夜溢价 × 开盘配置（−0.1038/−0.0489/t3.30/−10.5bp），延续。"),
    ("CY08", OC, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "oncont_close_confirm",
     "CX14 骨架轮换：隔夜延续度 × 收盘确认（−0.0233/−0.0313/t−0.30/+27.3bp），延续。"),
    ("CY09", OC, "PRICE_POSITION_20", "price_location", "oncont_high_position",
     "骨架轮换：隔夜延续度 × 获利位置（+0.0128/+0.0275/t1.64/+8.5bp），延续。"),
    ("CY10", OC, "LOG_AMOUNT_VOL_20", "liquidity_variability", "oncont_high_activity",
     "骨架轮换：隔夜延续度 × 高活跃（+0.0661/+0.0701/t2.23/+36.8bp），延续。"),
    ("CY11", OC, "RESILIENCY_20", "liquidity_commonality_1m", "oncont_resilient",
     "骨架轮换：隔夜延续度 × 微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp），延续。"),
    ("CY12", OC, "GAP_FILL_FRACTION_60", "gap_repair", "oncont_trend_persist",
     "骨架轮换：隔夜延续度 × 趋势持续（−0.0597/−0.0430/t2.59/+9.8bp），延续。"),
    ("CY13", OC, "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "oncont_bigbar_strength",
     "骨架轮换：隔夜延续度 × 大 bar 强度（+0.0832/+0.0548/t2.92/+41.6bp），延续。"),
    ("CY14", OC, "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "oncont_profile_anomaly",
     "骨架轮换：隔夜延续度 × 量轮廓异常（+0.0952/+0.0442/t4.04/+10.1bp），延续。"),
    ("CY15", G, "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "gapfill_bigbar_strength",
     "CX12 骨架轮换：跳空消化 × 大 bar 强度（+0.0832/+0.0548/t2.92/+41.6bp），延续。"),
    ("CY16", G, "SIGN_ACF1_5", "serial_dependence", "gapfill_acf_confirm",
     "骨架轮换：跳空消化 × 动量确认（−0.0211/+0.0070/t0.12/+3.9bp），延续。"),
    ("CY17", G, "PRICE_POSITION_20", "price_location", "gapfill_high_position",
     "骨架轮换：跳空消化 × 获利位置（+0.0128/+0.0275/t1.64/+8.5bp），延续。"),
    ("CY18", G, "CHIP_RANGE_90_60", "cost_distribution", "gapfill_chip_lock",
     "骨架轮换：跳空消化 × 筹码集中（−0.0574/−0.0620/t0.70/+14.6bp），延续。"),
    ("CY19", OP, "PV_ELASTICITY_20", ID, "onprem_elasticity",
     "跨新家族：隔夜溢价 × 量价弹性（CA1 入选 −0.1249/−0.0638/t4.00/+52.3bp），延续。"),
    ("CY20", OC, "PV_ELASTICITY_20", ID, "oncont_elasticity",
     "跨新家族：隔夜延续度 × 量价弹性（CA1 入选），延续。"),
    ("CY21", G, "PV_ELASTICITY_20", ID, "gapfill_elasticity",
     "跨新家族：跳空消化 × 量价弹性（CA1 入选），延续。"),
    ("CY22", OP, "LBAR_CLOCK_STD_20", LB, "onprem_clock_anomaly",
     "跨新家族：隔夜溢价 × 体量钟离散（BF1 入选 −0.0883/−0.0259/t3.12/+9.6bp），延续。"),
    ("CY23", OC, "LBAR_CLOCK_STD_20", LB, "oncont_clock_anomaly",
     "跨新家族：隔夜延续度 × 体量钟离散（BF1 入选），延续。"),
    ("CY24", OP, "VT_AUTOCORR_20", VT, "onprem_vt_autocorr",
     "跨新家族：隔夜溢价 × 体量时间趋势自相关（DA2 入选 −0.0822/−0.0363/t2.32/+17.9bp），延续。"),
]

base.CANDIDATES = [
    _pair(cid, left, ON, right, rsrc, mech, hyp) for cid, left, right, rsrc, mech, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage17(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage17_overnight_pairing"
    plan["pairing_note"] = "第 17 阶段扩展配对第 2 批：CX12 骨架轮换 + 跨新家族；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
