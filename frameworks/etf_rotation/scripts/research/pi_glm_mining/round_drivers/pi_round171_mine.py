#!/usr/bin/env python3
"""Round 171 driver: stage 36 third batch — remaining 18 legal pairs after
orientation fix (higher-t left consumed -> swap orientation). All left/right
caps verified stage-wide."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_171"


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"s36c_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _pair("DD36", "RP_UW_CHG_20", "replication_volume_free_v1", "PD_D1_CHG_20", "price_delay",
     "簇 RP：无量水平对（取向按左批余量修正），t 和排序第 1。"),
    _pair("DD37", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", "RP_PERM_ENT_D3_20", "replication_volume_free_v1",
     "簇 VFP：无量水平对（取向按左批余量修正），t 和排序第 2。"),
    _pair("DD38", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "RP_PERM_ENT_D3_20", "replication_volume_free_v1",
     "簇 CLOSE5：无量水平对（取向按左批余量修正），t 和排序第 3。"),
    _pair("DD39", "AM_PM_RV_RATIO_20", "lunch_break_1m", "RP_PERM_ENT_D3_20", "replication_volume_free_v1",
     "簇 AM：无量水平对（取向按左批余量修正），t 和排序第 4。"),
    _pair("DD40", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", "PD_D1_CHG_20", "price_delay",
     "簇 VFP：无量水平对（取向按左批余量修正），t 和排序第 5。"),
    _pair("DD41", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d", "RP_UW_LVL_20", "replication_volume_free_v1",
     "簇 LHA：无量水平对（取向按左批余量修正），t 和排序第 6。"),
    _pair("DD42", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d", "ON_PREM_20", "overnight_structure_1d",
     "簇 LHA：无量水平对（取向按左批余量修正），t 和排序第 7。"),
    _pair("DD43", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", "AUC_VARIANCE_RATIO_20", "auction_1m",
     "簇 VFP：无量水平对（取向按左批余量修正），t 和排序第 8。"),
    _pair("DD44", "PRICE_POSITION_20", "price_location", "AUC_VARIANCE_RATIO_20", "auction_1m",
     "簇 PRICE：无量水平对（取向按左批余量修正），t 和排序第 9。"),
    _pair("DD45", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d", "RP_UW_CHG_20", "replication_volume_free_v1",
     "簇 LHA：无量水平对（取向按左批余量修正），t 和排序第 10。"),
    _pair("DD46", "AM_PM_RV_RATIO_20", "lunch_break_1m", "AUC_VARIANCE_RATIO_20", "auction_1m",
     "簇 AM：无量水平对（取向按左批余量修正），t 和排序第 11。"),
    _pair("DD47", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d", "SCL_DFA_RET_20", "scaling_memory_1m",
     "簇 LHA：无量水平对（取向按左批余量修正），t 和排序第 12。"),
    _pair("DD48", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", "RP_UW_CHG_20", "replication_volume_free_v1",
     "簇 VFP：无量水平对（取向按左批余量修正），t 和排序第 13。"),
    _pair("DD49", "RP_UW_CHG_20", "replication_volume_free_v1", "LUNCH_PRE_RUN_20", "lunch_break_1m",
     "簇 RP：无量水平对（取向按左批余量修正），t 和排序第 14。"),
    _pair("DD50", "RP_UW_CHG_20", "replication_volume_free_v1", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow",
     "簇 RP：无量水平对（取向按左批余量修正），t 和排序第 15。"),
    _pair("DD51", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d", "GAP_FILL_RATE_20", "overnight_structure_1d",
     "簇 LHA：无量水平对（取向按左批余量修正），t 和排序第 16。"),
    _pair("DD52", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", "RESILIENCY_20", "liquidity_commonality_1m",
     "簇 VFP：无量水平对（取向按左批余量修正），t 和排序第 17。"),
    _pair("DD53", "PRICE_POSITION_20", "price_location", "RESILIENCY_20", "liquidity_commonality_1m",
     "簇 PRICE：无量水平对（取向按左批余量修正），t 和排序第 18。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s36c(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage36_volume_free_crosspair_b3"
    plan["family_note"] = (
        "第 36 阶段第三批：取向修正枚举（高 t 左批耗尽则对调）后剩 18 条合法配对，全部纳入。"
        "左腿批：LHA 5 / RP_UW_CHG 4 / VFP_ULCER 4 / CLOSE5 1 / AM_PM 1 / PRICE_POSITION 2 / ON_PREM 0；"
        "右腿顶格：RP_PERM_ENT 3 / AUC 2→3 / SCL_DFA 1→3。批后阶段配对将枚举为零。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s36c

if __name__ == "__main__":
    base.main()
