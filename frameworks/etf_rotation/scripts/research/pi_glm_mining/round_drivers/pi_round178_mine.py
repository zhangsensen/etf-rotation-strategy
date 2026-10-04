#!/usr/bin/env python3
"""Round 178 driver: stage 41 second batch — SB atoms as RIGHT legs with 12
confirmed left legs (3 lefts per SB atom, caps binding)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_178"

SB = "session_direction_bet_1m"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": SB},
        "mechanism": f"s41b_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _pair("SE19", "PV_ELASTICITY_20", "impact_decay_1m", "SB_MORN_BET_20", "簇 PV：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE20", "RP_UW_CHG_20", "replication_volume_free_v1", "SB_MORN_BET_20", "簇 RP：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE21", "ON_SKEW_20", "overnight_structure_1d", "SB_MORN_BET_20", "簇 ON：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE22", "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "SB_OPEN_BET_20", "簇 LBAR：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE23", "AUC_VARIANCE_RATIO_20", "auction_1m", "SB_OPEN_BET_20", "簇 AUC：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE24", "ULCER_20", "downside_risk", "SB_OPEN_BET_20", "簇 ULCER：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE25", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d", "SB_TAIL_BET_20", "簇 LHA：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE26", "GAP_FILL_RATE_20", "overnight_structure_1d", "SB_TAIL_BET_20", "簇 GAP：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE27", "CHIP_RANGE_90_60", "cost_distribution", "SB_TAIL_BET_20", "簇 CHIP：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE28", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "SB_LUNCH_WR_MINUS_INT_20", "簇 RP：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE29", "PD_D1_CHG_20", "price_delay", "SB_LUNCH_WR_MINUS_INT_20", "簇 PD：确认左腿 × SB 机制右腿（3 用顶格）。"),
    _pair("SE30", "MA_LUNCH_DIR_BET", "mechanism_atoms_v1", "SB_LUNCH_WR_MINUS_INT_20", "簇 MA：确认左腿 × SB 机制右腿（3 用顶格）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s41b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage41_session_direction_bet_b2"
    plan["family_note"] = (
        "第 41 阶段第二批：SB 原子转右腿 × 12 确认左腿（每 SB 3 用顶格）。批后第 41 阶段配对枚举为零。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s41b

if __name__ == "__main__":
    base.main()
