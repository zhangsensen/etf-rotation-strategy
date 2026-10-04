#!/usr/bin/env python3
"""Round 157 driver: stage 31 batch 2 — RPF/VFP-as-right x 3 fresh left legs
per atom = 24 pairs (all left legs pairwise distinct; every unordered pair new
vs r156 and stage-27 history). After this round stage-31 pairing enumeration = 0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_157"

RPF = "replication_volume_free_v1"
VFP = "volume_free_path_v1"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": RPF if right.startswith("RP_") else VFP},
        "mechanism": f"vf2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


SD = "serial_dependence"
CD = "cost_distribution"
RT = "return_tail_shape"
BF = "bar_size_order_flow"
DR = "downside_risk"
OS = "overnight_structure_1d"
LS = "liquidity_commonality_1m"
LV = "liquidity_variability"
SCL = "scaling_memory_1m"
ID = "impact_decay_1m"
LB = "largebar_footprint_1m"

P = [
    ("CY86", "SIGN_ACF1_5", SD, "RP_PERM_ENT_D3_20",
     "簇 SIGN_ACF：收益动量 × 低排列熵。"),
    ("CY87", "CHIP_RANGE_90_60", CD, "RP_PERM_ENT_D3_20",
     "簇 CHIP_RANGE：筹码集中 × 低排列熵。"),
    ("CY88", "WORST_DAY_20", RT, "RP_PERM_ENT_D3_20",
     "簇 WORST_DAY：无极端损伤 × 低排列熵。"),
    ("CY89", "TICK_IMBALANCE_20", BF, "RP_PERM_ENT_D4_20",
     "簇 TICK_IMB：主买不平衡 × 低排列熵(d4)。"),
    ("CY90", "ULCER_20", DR, "RP_PERM_ENT_D4_20",
     "簇 ULCER：健康结构 × 低排列熵(d4)。"),
    ("CY91", "GAP_FILL_RATE_20", OS, "RP_PERM_ENT_D4_20",
     "簇 GAP_FILL：缺口修复率 × 低排列熵(d4)。"),
    ("CY92", "CHIP_RANGE_90_60", CD, "RP_PERM_ENT_D3_60",
     "簇 CHIP_RANGE：筹码集中 × 慢速排列熵。"),
    ("CY93", "RESILIENCY_20", LS, "RP_PERM_ENT_D3_60",
     "簇 RESILIENCY：微结构弹性 × 慢速排列熵。"),
    ("CY94", "TICK_IMBALANCE_20", BF, "RP_UW_CHG_20",
     "簇 TICK_IMB：主买不平衡 × 水下变化。"),
    ("CY95", "ON_PREM_20", OS, "RP_UW_CHG_20",
     "簇 ON_PREM：隔夜溢价 × 水下变化（CZ01 同腿反向取向）。"),
    ("CY96", "LBAR_CLOCK_STD_20", LB, "RP_UW_CHG_20",
     "簇 LBAR_CLOCK：体量钟离散 × 水下变化（BF1 同腿反向取向）。"),
    ("CY97", "ULCER_20", DR, "RP_UW_LVL_20",
     "簇 ULCER：健康结构 × 低水下水平。"),
    ("CY98", "TICK_IMBALANCE_20", BF, "RP_UW_LVL_20",
     "簇 TICK_IMB：主买不平衡 × 低水下水平。"),
    ("CY99", "LOG_AMOUNT_VOL_20", LV, "RP_UW_LVL_20",
     "簇 LOG_AMOUNT：高活跃 × 低水下水平。"),
    ("CY100", "SIGN_ACF1_5", SD, "RP_UW_CHG_60",
     "簇 SIGN_ACF：收益动量 × 水下变化60。"),
    ("CY101", "CHIP_RANGE_90_60", CD, "RP_UW_CHG_60",
     "簇 CHIP_RANGE：筹码集中 × 水下变化60。"),
    ("CY102", "RESILIENCY_20", LS, "RP_UW_CHG_60",
     "簇 RESILIENCY：微结构弹性 × 水下变化60。"),
    ("CY103", "SIGN_ACF1_5", SD, "VFP_ULCER_SHIFT_20",
     "簇 SIGN_ACF：收益动量 × 低回撤恶化。"),
    ("CY104", "CHIP_RANGE_90_60", CD, "VFP_ULCER_SHIFT_20",
     "簇 CHIP_RANGE：筹码集中 × 低回撤恶化。"),
    ("CY105", "SCL_DFA_RET_20", SCL, "VFP_ULCER_SHIFT_20",
     "簇 DFA_RET：路径平滑 × 低回撤恶化（CY09 同腿反向取向）。"),
    ("CY106", "TICK_IMBALANCE_20", BF, "VFP_RECOVERY_20",
     "簇 TICK_IMB：主买不平衡 × 快恢复。"),
    ("CY107", "CHIP_RANGE_90_60", CD, "VFP_RECOVERY_20",
     "簇 CHIP_RANGE：筹码集中 × 快恢复。"),
    ("CY108", "ULCER_20", DR, "VFP_RECOVERY_20",
     "簇 ULCER：健康结构 × 快恢复。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage31(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage31_volume_free_path"
    plan["pairing_note"] = (
        "第 31 阶段配对第 2 批：RPF/VFP 作右腿 × 3 新左腿/原子 = 24 条"
        "（24 簇各 1 条，全部新无序对）；本批后阶段配对枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage31

if __name__ == "__main__":
    base.main()
