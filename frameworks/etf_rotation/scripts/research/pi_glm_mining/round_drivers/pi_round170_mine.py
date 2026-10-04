#!/usr/bin/env python3
"""Round 170 driver: stage 36 second batch — next tier of the 88 legal
volume-free cross-family combos after r169 top-18. Stage discipline updated:
r169 consumed left batches (RP_PERM_ENT/PD_D1_CHG/VFP_RECOVERY/AUC) and
right caps (VFP_RECOVERY/RCC/LHA at 3)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_170"


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"s36b_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _pair("DD18", "RCC_BB_SQUEEZE_20", "range_contraction_cycle", "RP_UW_CHG_20", "replication_volume_free_v1",
     "簇 RCC：无量水平对次档，t 和排序。"),
    _pair("DD19", "RP_UW_LVL_20", "replication_volume_free_v1", "SCL_DFA_RET_20", "scaling_memory_1m",
     "簇 RP：无量水平对次档，t 和排序。"),
    _pair("DD20", "RP_UW_LVL_20", "replication_volume_free_v1", "VFP_ULCER_SHIFT_20", "volume_free_path_v1",
     "簇 RP：无量水平对次档，t 和排序。"),
    _pair("DD21", "ON_PREM_20", "overnight_structure_1d", "VFP_ULCER_SHIFT_20", "volume_free_path_v1",
     "簇 ON：无量水平对次档，t 和排序。"),
    _pair("DD22", "RP_UW_LVL_20", "replication_volume_free_v1", "GAP_FILL_RATE_20", "overnight_structure_1d",
     "簇 RP：无量水平对次档，t 和排序。"),
    _pair("DD23", "RCC_BB_SQUEEZE_20", "range_contraction_cycle", "RESILIENCY_20", "liquidity_commonality_1m",
     "簇 RCC：无量水平对次档，t 和排序。"),
    _pair("DD24", "RP_UW_LVL_20", "replication_volume_free_v1", "LUNCH_PRE_RUN_20", "lunch_break_1m",
     "簇 RP：无量水平对次档，t 和排序。"),
    _pair("DD25", "RP_UW_LVL_20", "replication_volume_free_v1", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow",
     "簇 RP：无量水平对次档，t 和排序。"),
    _pair("DD26", "RP_UW_LVL_20", "replication_volume_free_v1", "AM_PM_RV_RATIO_20", "lunch_break_1m",
     "簇 RP：无量水平对次档，t 和排序。"),
    _pair("DD27", "RCC_BB_SQUEEZE_20", "range_contraction_cycle", "VFP_ULCER_SHIFT_20", "volume_free_path_v1",
     "簇 RCC：无量水平对次档，t 和排序。"),
    _pair("DD28", "ON_PREM_20", "overnight_structure_1d", "AM_PM_RV_RATIO_20", "lunch_break_1m",
     "簇 ON：无量水平对次档，t 和排序。"),
    _pair("DD29", "RCC_BB_SQUEEZE_20", "range_contraction_cycle", "PRICE_POSITION_20", "price_location",
     "簇 RCC：无量水平对次档，t 和排序。"),
    _pair("DD30", "RCC_BB_SQUEEZE_20", "range_contraction_cycle", "GAP_FILL_RATE_20", "overnight_structure_1d",
     "簇 RCC：无量水平对次档，t 和排序。"),
    _pair("DD31", "RP_UW_CHG_20", "replication_volume_free_v1", "PRICE_POSITION_20", "price_location",
     "簇 RP：无量水平对次档，t 和排序。"),
    _pair("DD32", "RCC_BB_SQUEEZE_20", "range_contraction_cycle", "LUNCH_PRE_RUN_20", "lunch_break_1m",
     "簇 RCC：无量水平对次档，t 和排序。"),
    _pair("DD33", "RCC_BB_SQUEEZE_20", "range_contraction_cycle", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow",
     "簇 RCC：无量水平对次档，t 和排序。"),
    _pair("DD34", "RCC_BB_SQUEEZE_20", "range_contraction_cycle", "AM_PM_RV_RATIO_20", "lunch_break_1m",
     "簇 RCC：无量水平对次档，t 和排序。"),
    _pair("DD35", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d", "PRICE_POSITION_20", "price_location",
     "簇 LHA：无量水平对次档，t 和排序。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s36b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage36_volume_free_crosspair_b2"
    plan["family_note"] = (
        "第 36 阶段第二批：次档 18 条。左腿批量：RCC_BB_SQUEEZE 8（顶格）/ RP_UW_LVL 6 / "
        "ON_PREM 2 / RP_UW_CHG 1 / LHA 1；右腿 VFP_ULCER/AM_PM/PRICE_POSITION 顶格 3。"
        "剩余合法组合约 30 个，下一轮 <12 即穷尽。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s36b

if __name__ == "__main__":
    base.main()
