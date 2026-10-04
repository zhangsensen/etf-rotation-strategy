#!/usr/bin/env python3
"""Round 145 driver: stage 26 batch 2 — LHA-as-right x 2 fresh left legs
per atom = 12 pairs (= floor; fresh-left pool exhausted at 14). All unordered
pairs new vs r144. After this round stage-26 pairing enumeration = 0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_145"

LHA = "long_horizon_anchors_1d"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": LHA},
        "mechanism": f"lha2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


LS = "liquidity_commonality_1m"
LV = "liquidity_variability"
CD = "cost_distribution"
ID = "impact_decay_1m"
BF = "bar_size_order_flow"
AU = "auction_1m"
VT = "volume_time_1m"
ID2 = "impact_decay_1m"
SCL = "scaling_memory_1m"
LB = "largebar_footprint_1m"
PL = "price_location"
OS = "overnight_structure_1d"

P = [
    ("CZ29", "RESILIENCY_20", LS, "LHA_NEAR_LOW_20",
     "簇 RESILIENCY：微结构弹性 × 远离下锚（CY59 同腿反向取向）。"),
    ("CZ30", "LOG_AMOUNT_VOL_20", LV, "LHA_NEAR_LOW_20",
     "簇 LOG_AMOUNT：高活跃 × 远离下锚。"),
    ("CZ31", "CHIP_RANGE_90_60", CD, "LHA_AGE_HIGH_20",
     "簇 CHIP_RANGE：筹码集中 × 锚新鲜度（CY61 同腿 t4.89 骨架）。"),
    ("CZ32", "IMP_PERM_SHARE_20", ID, "LHA_AGE_HIGH_20",
     "簇 IMP_PERM：冲击永久份额 × 锚新鲜度。"),
    ("CZ33", "CLOSE5_DAY_CONSIST_20", BF, "LHA_AGE_LOW_20",
     "簇 CLOSE5：收盘确认 × 低锚新鲜度（CK04 同腿反向取向）。"),
    ("CZ34", "AUC_VARIANCE_RATIO_20", AU, "LHA_AGE_LOW_20",
     "簇 VAR_RATIO：波动配置 × 低锚新鲜度（CM06 同腿反向取向）。"),
    ("CZ35", "VT_BUCKET_GINI_20", VT, "LHA_POS_DIVERG_20",
     "簇 VT_GINI：桶到达 Gini × 长短锚分歧（CN08 同腿反向取向）。"),
    ("CZ36", "PV_ELASTICITY_20", ID2, "LHA_POS_DIVERG_20",
     "簇 PV_ELAST：量价弹性 × 长短锚分歧（CA1 同腿）。"),
    ("CZ37", "SCL_DFA_ABS_20", SCL, "LHA_NEWHIGH_20",
     "簇 DFA_ABS：|r| 长记忆 × 新高密度（CU02 同腿反向取向）。"),
    ("CZ38", "LBAR_CLOCK_STD_20", LB, "LHA_NEWHIGH_20",
     "簇 LBAR_CLOCK：体量钟离散 × 新高密度（BF1 同腿反向取向）。"),
    ("CZ39", "PRICE_POSITION_20", PL, "LHA_POS_DIVERG_20",
     "簇 PRICE_POSITION：20 日位置 × 长短锚分歧——同族跨窗口对话。"),
    ("CZ40", "ON_CONT_20", OS, "LHA_AGE_LOW_20",
     "簇 ON_CONT：隔夜延续度 × 低锚新鲜度（CT20 同腿反向取向）。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage26(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage26_long_horizon_anchors"
    plan["pairing_note"] = (
        "第 26 阶段配对第 2 批：LHA 作右腿 × 2 新左腿/原子 = 12 条（恰达下限，"
        "新左腿池仅余 14）；簇 ID = 左腿名；本批后阶段配对枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage26

if __name__ == "__main__":
    base.main()
