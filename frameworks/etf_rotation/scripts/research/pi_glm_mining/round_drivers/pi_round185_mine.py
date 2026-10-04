#!/usr/bin/env python3
"""Round 185 driver: stage 46 second batch — rel_category atoms as RIGHT legs
with 12 confirmed left legs (3 lefts per atom, caps binding)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_185"

RC = "rel_category_v1"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": RC},
        "mechanism": f"s46b_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _pair("TF17", "PV_ELASTICITY_20", "impact_decay_1m", "R_REL_UW_CATEGORY_CHG_20",
     "簇 PV_ELASTICITY：量价弹性 × 类内水下变化（CA1 同腿）。"),
    _pair("TF18", "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "R_REL_UW_CATEGORY_CHG_20",
     "簇 LBAR_CLOCK_STD：量钟离散 × 类内水下变化。"),
    _pair("TF19", "ON_SKEW_20", "overnight_structure_1d", "R_REL_UW_CATEGORY_CHG_20",
     "簇 ON_SKEW：隔夜偏度 × 类内水下变化。"),
    _pair("TF20", "TICK_IMBALANCE_20", "bar_size_order_flow", "R_REL_ULCER_CHG_20",
     "簇 TICK：主买不平衡 × 类内溃疡变化。"),
    _pair("TF21", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "R_REL_ULCER_CHG_20",
     "簇 RP_PERM_ENT：排列熵 × 类内溃疡变化（DA41 同腿）。"),
    _pair("TF22", "MA_GAP_DD_EAT", "mechanism_atoms_v1", "R_REL_ULCER_CHG_20",
     "簇 MA_GAP_DD：跳空被吃 × 类内溃疡变化。"),
    _pair("TF23", "GAP_FILL_RATE_20", "overnight_structure_1d", "R_REL_RECOVERY_CHG_20",
     "簇 GAP_FILL：跳空回补 × 类内恢复变化。"),
    _pair("TF24", "RESILIENCY_20", "liquidity_commonality_1m", "R_REL_RECOVERY_CHG_20",
     "簇 RESILIENCY：微结构弹性 × 类内恢复变化。"),
    _pair("TF25", "VFP_RECOVERY_20", "volume_free_path_v1", "R_REL_RECOVERY_CHG_20",
     "簇 VFP_RECOVERY：回撤恢复 × 类内恢复变化。"),
    _pair("TF26", "PD_D1_CHG_20", "price_delay", "R_REL_UW_BASKET_CHG_20",
     "簇 PD_D1_CHG：延迟改善 × 篮子相对水下变化（DA57 同腿）。"),
    _pair("TF27", "RP_UW_CHG_20", "replication_volume_free_v1", "R_REL_UW_BASKET_CHG_20",
     "簇 RCC_BB_SQUEEZE：squeeze × 篮子相对水下变化。"),
    _pair("TF28", "CHIP_RANGE_90_60", "cost_distribution", "R_REL_UW_BASKET_CHG_20",
     "簇 CHIP_RANGE：筹码区间 × 篮子相对水下变化。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s46b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage46_rel_category_b2"
    plan["family_note"] = (
        "第 46 阶段第二批：rel_category 原子转右腿 × 12 确认左腿（每原子 3 用顶格）。"
        "批后第 46 阶段配对枚举为零。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s46b

if __name__ == "__main__":
    base.main()
