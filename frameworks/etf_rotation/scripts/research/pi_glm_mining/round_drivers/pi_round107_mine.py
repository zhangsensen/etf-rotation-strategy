#!/usr/bin/env python3
"""Round 107 driver: stage 17 extension pairing batch 1 (18 pairs).
overnight_structure_1d atoms (GAP_FILL_RATE/ON_PREM/ON_CONT — the three
non-shadow atoms) x verified pool legs. All-new pairs, cross-family."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_107"

ON = "overnight_structure_1d"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


G = "GAP_FILL_RATE_20"   # −0.0437/−0.0320/t1.48/+19.9bp（AF1，零 shadow）
OP = "ON_PREM_20"        # +0.0213/+0.0135/t0.86/+1.6bp（AF2，零 shadow）
OC = "ON_CONT_20"        # −0.0375/+0.0308/t1.15/−5.3bp（零 shadow）

P = [
    ("CX01", G, "LOG_AMOUNT_VOL_20", "liquidity_variability", "gapfill_high_activity",
     "跳空消化频率 × 高活跃（+0.0661/+0.0701/t2.23/+36.8bp）：活跃环境的跳空消化，延续。"),
    ("CX02", G, "GAP_FILL_FRACTION_60", "gap_repair", "gapfill_trend_persist",
     "跳空消化频率 × 缺口修复趋势（−0.0597/−0.0430/t2.59/+9.8bp）：双缺口结构同向，延续。"),
    ("CX03", G, "WORST_DAY_20", "return_tail_shape", "gapfill_no_damage",
     "跳空消化频率 × 无极端损伤（+0.0635/+0.0648/t2.18/+16.2bp）：消化在健康结构中，延续。"),
    ("CX04", G, "RESILIENCY_20", "liquidity_commonality_1m", "gapfill_resilient",
     "跳空消化频率 × 微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）：消化在有回复力的市场，延续。"),
    ("CX05", G, "TICK_IMBALANCE_20", "bar_size_order_flow", "gapfill_buyflow",
     "跳空消化频率 × 主买不平衡（−0.0116/+0.0002/t1.01/+4.7bp）：消化由买流完成，延续。"),
    ("CX06", G, "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "gapfill_profile_anomaly",
     "跳空消化频率 × 量轮廓异常（+0.0952/+0.0442/t4.04/+10.1bp）：消化伴随轮廓异常，延续。"),
    ("CX07", OP, "LOG_AMOUNT_VOL_20", "liquidity_variability", "onprem_high_activity",
     "隔夜溢价 × 高活跃（+0.0661/+0.0701/t2.23/+36.8bp）：隔夜溢价在高活跃环境，延续。"),
    ("CX08", OP, "WORST_DAY_20", "return_tail_shape", "onprem_no_damage",
     "隔夜溢价 × 无极端损伤（+0.0635/+0.0648/t2.18/+16.2bp）：溢价无损伤配对，延续。"),
    ("CX09", OP, "SIGN_ACF1_5", "serial_dependence", "onprem_acf_confirm",
     "隔夜溢价 × 动量确认（−0.0211/+0.0070/t0.12/+3.9bp）：溢价与动量同向，延续。"),
    ("CX10", OP, "PRICE_POSITION_20", "price_location", "onprem_high_position",
     "隔夜溢价 × 获利位置（+0.0128/+0.0275/t1.64/+8.5bp）：溢价叠加获利位置，延续。"),
    ("CX11", OP, "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "onprem_bigbar_strength",
     "隔夜溢价 × 大 bar 强度（+0.0832/+0.0548/t2.92/+41.6bp）：溢价叠加活动强度，延续。"),
    ("CX12", OP, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "onprem_close_confirm",
     "隔夜溢价 × 收盘确认（−0.0233/−0.0313/t−0.30/+27.3bp）：溢价与收盘确认，延续。"),
    ("CX13", OC, "TICK_IMBALANCE_20", "bar_size_order_flow", "oncont_buyflow",
     "隔夜延续度 × 主买不平衡（−0.0116/+0.0002/t1.01/+4.7bp）：延续由买流支撑，延续。"),
    ("CX14", OC, "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "oncont_events",
     "隔夜延续度 × 事件密集（+0.0804/+0.0595/t2.76/+50.7bp）：延续伴随事件密集，延续。"),
    ("CX15", OC, "SIGN_ACF1_5", "serial_dependence", "oncont_acf_confirm",
     "隔夜延续度 × 动量确认（−0.0211/+0.0070/t0.12/+3.9bp）：日内延续与日间动量同向，延续。"),
    ("CX16", OC, "CHIP_RANGE_90_60", "cost_distribution", "oncont_chip_lock",
     "隔夜延续度 × 筹码集中（−0.0574/−0.0620/t0.70/+14.6bp）：延续在集中盘上，延续。"),
    ("CX17", OC, "WORST_DAY_20", "return_tail_shape", "oncont_no_damage",
     "隔夜延续度 × 无极端损伤（+0.0635/+0.0648/t2.18/+16.2bp）：延续无损伤，延续。"),
    ("CX18", OC, "ULCER_20", "downside_risk", "oncont_healthy",
     "隔夜延续度 × 溃疡浅（−0.0415/−0.0607/t0.76/+10.7bp）：延续在健康结构，延续。"),
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
    plan["pairing_note"] = "第 17 阶段扩展配对第 1 批：overnight_structure_1d 新腿 × 已验证腿；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
