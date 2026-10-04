#!/usr/bin/env python3
"""Round 151 driver: stage 29 batch 2 — PD-as-right x 3 fresh left legs
per atom = 15 pairs (all left legs pairwise distinct; every unordered pair
new vs r150). After this round stage-29 pairing enumeration = 0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_151"

PD = "price_delay"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": PD},
        "mechanism": f"pd2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


DR = "downside_risk"
BF = "bar_size_order_flow"
LV = "liquidity_variability"
SD = "serial_dependence"
CD = "cost_distribution"
ID = "impact_decay_1m"
LS = "liquidity_commonality_1m"
VT = "volume_time_1m"
FF = "fund_flow"
RT = "return_tail_shape"
LB = "largebar_footprint_1m"
AU = "auction_1m"
IVP = "intraday_volume_profile_1m"
SCL = "scaling_memory_1m"
PL = "price_location"

P = [
    ("CZ53", "ULCER_20", DR, "PD_D1_D_20",
     "簇 ULCER：健康结构 × 低延迟（DA47 同腿反向取向）。"),
    ("CZ54", "TICK_IMBALANCE_20", BF, "PD_D1_D_20",
     "簇 TICK_IMB：主买不平衡 × 低延迟。"),
    ("CZ55", "LOG_AMOUNT_VOL_20", LV, "PD_D1_D_20",
     "簇 LOG_AMOUNT：高活跃 × 低延迟。"),
    ("CZ56", "SIGN_ACF1_5", SD, "PD_D2_D_20",
     "簇 SIGN_ACF：收益动量 × 低滞后占比（DA48 同腿反向取向）。"),
    ("CZ57", "CHIP_RANGE_90_60", CD, "PD_D2_D_20",
     "簇 CHIP_RANGE：筹码集中 × 低滞后占比。"),
    ("CZ58", "PV_ELASTICITY_20", ID, "PD_D2_D_20",
     "簇 PV_ELAST：量价弹性 × 低滞后占比（CA1 同腿反向取向）。"),
    ("CZ59", "RESILIENCY_20", LS, "PD_D1_CHG_20",
     "簇 RESILIENCY：微结构弹性 × 低吸收恶化（DA57 同腿反向取向）。"),
    ("CZ60", "VT_BUCKET_GINI_20", VT, "PD_D1_CHG_20",
     "簇 VT_GINI：桶到达 Gini × 低吸收恶化（CN08 同腿反向取向）。"),
    ("CZ61", "SHARE_RET_CORR_20", FF, "PD_D1_CHG_20",
     "簇 SHARE_RET：一级流解释力 × 低吸收恶化。"),
    ("CZ62", "WORST_DAY_20", RT, "PD_DIFF_20",
     "簇 WORST_DAY：无极端损伤 × 低吸收分歧。"),
    ("CZ63", "LBAR_CLOCK_STD_20", LB, "PD_DIFF_20",
     "簇 LBAR_CLOCK：体量钟离散 × 低吸收分歧（BF1 同腿反向取向）。"),
    ("CZ64", "AUC_CLOSE_VOLSHARE_20", AU, "PD_DIFF_20",
     "簇 CLOSE_VOLSHARE：收盘竞价份额 × 低吸收分歧。"),
    ("CZ65", "OPEN30_VOL_SHARE_20", IVP, "PD_LAG_SIGN_20",
     "簇 OPEN30：开盘配置 × 滞后符号（CL09 同腿反向取向）。"),
    ("CZ66", "SCL_DFA_RET_20", SCL, "PD_LAG_SIGN_20",
     "簇 DFA_RET：路径平滑 × 滞后符号（CY09 同腿反向取向）。"),
    ("CZ67", "PRICE_POSITION_20", PL, "PD_LAG_SIGN_20",
     "簇 PRICE_POSITION：获利位置 × 滞后符号。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage29(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage29_price_delay"
    plan["pairing_note"] = (
        "第 29 阶段配对第 2 批：PD 作右腿 × 3 新左腿/原子 = 15 条"
        "（15 簇各 1 条，全部新无序对）；本批后阶段配对枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage29

if __name__ == "__main__":
    base.main()
