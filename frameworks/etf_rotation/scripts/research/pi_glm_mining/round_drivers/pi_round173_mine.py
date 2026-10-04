#!/usr/bin/env python3
"""Round 173 driver: stage 37 second batch — mechanism atoms as RIGHT legs
with 18 confirmed left legs (3 lefts per MA atom, cap binding)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_173"

MA = "mechanism_atoms_v1"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": MA},
        "mechanism": f"s37b_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _pair("MA24", "PV_ELASTICITY_20", "impact_decay_1m", "MA_VTAC_SPLIT", "簇 PV：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA25", "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "MA_VTAC_SPLIT", "簇 LBAR：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA26", "AM_PM_RV_RATIO_20", "lunch_break_1m", "MA_VTAC_SPLIT", "簇 ON：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA27", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "MA_LUNCH_DIR_BET", "簇 RP：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA28", "TICK_IMBALANCE_20", "bar_size_order_flow", "MA_LUNCH_DIR_BET", "簇 TICK：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA29", "VFP_RECOVERY_20", "volume_free_path_v1", "MA_LUNCH_DIR_BET", "簇 VFP：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA30", "PD_D1_CHG_20", "price_delay", "MA_PRERUN_TAIL_MATCH", "簇 PD：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA31", "RCC_BB_SQUEEZE_20", "range_contraction_cycle", "MA_PRERUN_TAIL_MATCH", "簇 RCC：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA32", "ULCER_20", "downside_risk", "MA_PRERUN_TAIL_MATCH", "簇 ULCER：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA33", "SCL_DFA_RET_20", "scaling_memory_1m", "MA_GAP_DD_EAT", "簇 SCL：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA34", "GAP_FILL_RATE_20", "overnight_structure_1d", "MA_GAP_DD_EAT", "簇 GAP：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA35", "CHIP_RANGE_90_60", "cost_distribution", "MA_GAP_DD_EAT", "簇 CHIP：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA36", "ON_SKEW_20", "overnight_structure_1d", "MA_OPEN_BUCKET_SHARE", "簇 ON：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA37", "PRICE_POSITION_20", "price_location", "MA_OPEN_BUCKET_SHARE", "簇 PRICE：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA38", "RESILIENCY_20", "liquidity_commonality_1m", "MA_OPEN_BUCKET_SHARE", "簇 RESILIENCY：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA39", "RP_UW_CHG_20", "replication_volume_free_v1", "MA_HAR_ELAST_SPLIT", "簇 RP：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA40", "VT_BUCKET_GINI_20", "volume_time_1m", "MA_HAR_ELAST_SPLIT", "簇 VT：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
    _pair("MA41", "AUC_VARIANCE_RATIO_20", "auction_1m", "MA_HAR_ELAST_SPLIT", "簇 AUC：确认左腿 × 机制原子右腿（S27 侧写验证）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s37b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage37_mechanism_atoms_b2"
    plan["family_note"] = (
        "第 37 阶段第二批：MA 原子转右腿，6 原子 × 3 左腿顶格 = 18。全部跨族，左腿为本阶段首批。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s37b

if __name__ == "__main__":
    base.main()
