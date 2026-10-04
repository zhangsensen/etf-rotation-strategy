#!/usr/bin/env python3
"""Round 166 driver: stage 34 third (final enumerable) batch.
Left legs (first stage-34 batch): FP_CHG_UP_20 (8 rights, pairwise diff
families), FP_CHG_CROSS_20 (3 rights); plus ON_SKEW_20 x FP_DOWN_20 (last
right-leg slot). All other FP right-leg slots exhausted in r164/r165.
Total = 12 (floor); after this batch stage-34 pairings are enumerated out."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_166"

FP = "first_passage_times_1m"


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"s34c_{left.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    # FP_CHG_UP_20 as left (8 rights, pairwise different families)
    _pair("DB36", "FP_CHG_UP_20", FP, "ON_PREM_20", "overnight_structure_1d",
     "簇 FP_CHG_UP：上行首达加速 × 隔夜溢价。"),
    _pair("DB37", "FP_CHG_UP_20", FP, "PRICE_POSITION_20", "price_location",
     "簇 FP_CHG_UP：上行首达加速 × 价格位置高。"),
    _pair("DB38", "FP_CHG_UP_20", FP, "RP_UW_CHG_20", "replication_volume_free_v1",
     "簇 FP_CHG_UP：上行首达加速 × 水下改善。"),
    _pair("DB39", "FP_CHG_UP_20", FP, "TICK_IMBALANCE_20", "bar_size_order_flow",
     "簇 FP_CHG_UP：上行首达加速 × 主买不平衡。"),
    _pair("DB40", "FP_CHG_UP_20", FP, "ULCER_20", "downside_risk",
     "簇 FP_CHG_UP：上行首达加速 × 溃疡低。"),
    _pair("DB41", "FP_CHG_UP_20", FP, "CHIP_RANGE_90_60", "cost_distribution",
     "簇 FP_CHG_UP：上行首达加速 × 筹码区间。"),
    _pair("DB42", "FP_CHG_UP_20", FP, "SCL_DFA_RET_20", "scaling_memory_1m",
     "簇 FP_CHG_UP：上行首达加速 × 路径趋势度。"),
    _pair("DB43", "FP_CHG_UP_20", FP, "VOL_USHAPE_20", "realized_measures_1m",
     "簇 FP_CHG_UP：上行首达加速 × 量 U 型弱。"),
    # FP_CHG_CROSS_20 as left (3 rights)
    _pair("DB44", "FP_CHG_CROSS_20", FP, "RESILIENCY_20", "liquidity_commonality_1m",
     "簇 FP_CHG_CROSS：穿越频率变化 × 微结构弹性。"),
    _pair("DB45", "FP_CHG_CROSS_20", FP, "GAP_FILL_RATE_20", "overnight_structure_1d",
     "簇 FP_CHG_CROSS：穿越频率变化 × 跳空回补。"),
    _pair("DB46", "FP_CHG_CROSS_20", FP, "VT_BUCKET_GINI_20", "volume_time_1m",
     "簇 FP_CHG_CROSS：穿越频率变化 × 到达不均。"),
    # FP_DOWN last right slot
    _pair("DB47", "ON_SKEW_20", "overnight_structure_1d", "FP_DOWN_20", FP,
     "簇 ON_SKEW：隔夜偏度 × 下行首达慢。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s34c(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage34_first_passage_times_batch3"
    plan["family_note"] = (
        "第 34 阶段第三批（最后可枚举批）：FP_CHG_UP/FP_CHG_CROSS 首次作左腿；"
        "右腿用量核验（FP_DOWN 第 3 槽 ON_SKEW×FP_DOWN；其余 FP 右腿槽位 r164/r165 已满）。"
        "12 条 = 每轮下限；本批后第 34 阶段合法配对枚举为零。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s34c

if __name__ == "__main__":
    base.main()
