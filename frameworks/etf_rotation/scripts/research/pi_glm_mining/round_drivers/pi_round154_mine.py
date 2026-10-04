#!/usr/bin/env python3
"""Round 154 driver: stage 30 batch 2 — LM-as-right x 3 fresh left legs
per atom = 15 pairs (all left legs pairwise distinct; every unordered pair
new vs r153). After this round stage-30 pairing enumeration = 0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_154"

LM = "liquidity_momentum"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": LM},
        "mechanism": f"lm2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


DR = "downside_risk"
BF = "bar_size_order_flow"
LV = "liquidity_variability"
SD = "serial_dependence"
CD = "cost_distribution"
ID = "impact_decay_1m"
LS = "liquidity_commonality_1m"
RT = "return_tail_shape"
SCL = "scaling_memory_1m"
OS = "overnight_structure_1d"
IVP = "intraday_volume_profile_1m"
VT = "volume_time_1m"
ID2 = "impact_decay_1m"
LB = "largebar_footprint_1m"
BF2 = "bar_size_order_flow"

P = [
    ("CZ78", "ULCER_20", DR, "LM_AMIHUD_RATIO_20_60",
     "簇 ULCER：健康结构 × 非流动性动量（CZ68 同腿反向取向）。"),
    ("CZ79", "TICK_IMBALANCE_20", BF, "LM_AMIHUD_RATIO_20_60",
     "簇 TICK_IMB：主买不平衡 × 非流动性动量。"),
    ("CZ80", "LOG_AMOUNT_VOL_20", LV, "LM_AMIHUD_RATIO_20_60",
     "簇 LOG_AMOUNT：高活跃 × 非流动性动量。"),
    ("CZ81", "SIGN_ACF1_5", SD, "LM_AMIHUD_LOGCHG_20",
     "簇 SIGN_ACF：收益动量 × 流动性冲击（CZ70 同腿反向取向）。"),
    ("CZ82", "CHIP_RANGE_90_60", CD, "LM_AMIHUD_LOGCHG_20",
     "簇 CHIP_RANGE：筹码集中 × 流动性冲击。"),
    ("CZ83", "PV_ELASTICITY_20", ID, "LM_AMIHUD_LOGCHG_20",
     "簇 PV_ELAST：量价弹性 × 流动性冲击（CA1 同腿反向取向）。"),
    ("CZ84", "RESILIENCY_20", LS, "LM_UNEXP_AMIHUD_20",
     "簇 RESILIENCY：微结构弹性 × 意外非流动性。"),
    ("CZ85", "WORST_DAY_20", RT, "LM_UNEXP_AMIHUD_20",
     "簇 WORST_DAY：无极端损伤 × 意外非流动性。"),
    ("CZ86", "SCL_DFA_RET_20", SCL, "LM_UNEXP_AMIHUD_20",
     "簇 DFA_RET：路径平滑 × 意外非流动性（CY09 同腿反向取向）。"),
    ("CZ87", "ON_CONT_20", OS, "LM_ROLL_CHG_20",
     "簇 ON_CONT：隔夜延续度 × 价差变化。"),
    ("CZ88", "OPEN30_VOL_SHARE_20", IVP, "LM_ROLL_CHG_20",
     "簇 OPEN30：开盘配置 × 价差变化（CL09 同腿反向取向）。"),
    ("CZ89", "VT_BUCKET_GINI_20", VT, "LM_ROLL_CHG_20",
     "簇 VT_GINI：桶到达 Gini × 价差变化（CN08 同腿反向取向）。"),
    ("CZ90", "IMP_PERM_SHARE_20", ID2, "LM_LIQ_RET_CORR_20",
     "簇 IMP_PERM：冲击永久份额 × 流动性冲击反应（CY52 同腿骨架）。"),
    ("CZ91", "LBAR_CLOCK_STD_20", LB, "LM_LIQ_RET_CORR_20",
     "簇 LBAR_CLOCK：体量钟离散 × 流动性冲击反应（BF1 同腿反向取向）。"),
    ("CZ92", "CLOSE5_DAY_CONSIST_20", BF2, "LM_LIQ_RET_CORR_20",
     "簇 CLOSE5：收盘确认 × 流动性冲击反应（CK04 同腿反向取向）。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage30(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage30_liquidity_momentum"
    plan["pairing_note"] = (
        "第 30 阶段配对第 2 批：LM 作右腿 × 3 新左腿/原子 = 15 条"
        "（15 簇各 1 条，全部新无序对）；本批后阶段配对枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage30

if __name__ == "__main__":
    base.main()
