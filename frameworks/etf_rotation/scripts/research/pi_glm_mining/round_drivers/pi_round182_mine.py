#!/usr/bin/env python3
"""Round 182 driver: stage 44 close-out — remaining legal pairs: EDGE_TIME_BIAS
as right leg x 3 confirmed lefts. Splits (CHIP/BB_RES) excluded from the legal
enumeration with r181 evidence (23-30 valid days, structural gate-1 failure).
Remaining legal pairs = 3 < 12 -> exhaustion declared this round per 17:00."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_182"

MA = "mechanism_atoms_v2"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": MA},
        "mechanism": f"s44z_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _pair("TE13", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d", "MA2_EDGE_TIME_BIAS_20",
     "簇 LHA：52 周锚 × 大 bar 时点偏置。"),
    _pair("TE14", "VT_BUCKET_GINI_20", "volume_time_1m", "MA2_EDGE_TIME_BIAS_20",
     "簇 VT_GINI：到达不均 × 大 bar 时点偏置。"),
    _pair("TE15", "AUC_VARIANCE_RATIO_20", "auction_1m", "MA2_EDGE_TIME_BIAS_20",
     "簇 AUC：开盘方差比 × 大 bar 时点偏置。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s44z(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage44_closeout"
    plan["family_note"] = (
        "第 44 阶段收口：EDGE_TIME_BIAS 右腿 3 槽最后消费。splits（CHIP/BB_RES）凭 r181 证据"
        "（有效样本 23-30 天，结构性门 1 失败）从合法枚举剔除；PREUP_PERM_ENT 影子已剔。"
        "剩余合法配对 3 < 12 → 本轮按 17:00 条款宣布第 44 阶段穷尽。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s44z

if __name__ == "__main__":
    base.main()
