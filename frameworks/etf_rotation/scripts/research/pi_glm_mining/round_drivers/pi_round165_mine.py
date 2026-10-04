#!/usr/bin/env python3
"""Round 165 driver: stage 34 second batch — FP atoms as RIGHT legs paired
with confirmed left legs (first batch for each left leg in stage 34).
Right-leg usage caps: FP_UP 3, FP_ASYM 3, FP_CROSS 3, FP_FALSE 3,
FP_DOWN 2, FP_CHG_UP 1, FP_CHG_CROSS 1. FP_UP_FRAC banned (low coverage)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_165"

FP = "first_passage_times_1m"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": FP},
        "mechanism": f"s34_{left.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _pair("DB20", "PV_ELASTICITY_20", "impact_decay_1m", "FP_UP_20",
     "簇 PV_ELASTICITY：量价弹性 × 上行首达快（CA1 同腿）。"),
    _pair("DB21", "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "FP_UP_20",
     "簇 LBAR_CLOCK_STD：量钟离散 × 上行首达快（CZ19 同腿）。"),
    # DB22 原为 ON_PREM×FP_UP——与 r164 DB10 交换对称同哈希，正确拦截；换 RP_PERM_ENT 左腿
    _pair("DB22", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "FP_UP_20",
     "簇 RP_PERM_ENT：排列熵低 × 上行首达快（DA41 同腿）。"),
    _pair("DB23", "RP_UW_CHG_20", "replication_volume_free_v1", "FP_ASYM_20",
     "簇 RP_UW_CHG：水下改善 × 方向首达不对称（DA44 同腿）。"),
    _pair("DB24", "PD_D1_CHG_20", "price_delay", "FP_ASYM_20",
     "簇 PD_D1_CHG：延迟改善 × 首达不对称（DA57 同腿）。"),
    _pair("DB25", "VT_BUCKET_GINI_20", "volume_time_1m", "FP_ASYM_20",
     "簇 VT_BUCKET_GINI：到达不均 × 首达不对称。"),
    _pair("DB26", "TICK_IMBALANCE_20", "bar_size_order_flow", "FP_CROSS_20",
     "簇 TICK_IMBALANCE：主买不平衡 × 低震荡。"),
    _pair("DB27", "SCL_DFA_RET_20", "scaling_memory_1m", "FP_CROSS_20",
     "簇 SCL_DFA_RET：趋势度 × 低震荡。"),
    _pair("DB28", "IMP_PERM_SHARE_20", "impact_decay_1m", "FP_CROSS_20",
     "簇 IMP_PERM_SHARE：永久冲击份额 × 低震荡。"),
    _pair("DB29", "GAP_FILL_RATE_20", "overnight_structure_1d", "FP_FALSE_20",
     "簇 GAP_FILL_RATE：跳空回补 × 低假突破。"),
    _pair("DB30", "RESILIENCY_20", "liquidity_commonality_1m", "FP_FALSE_20",
     "簇 RESILIENCY：微结构弹性 × 低假突破。"),
    _pair("DB31", "RCC_BB_SQUEEZE_20", "range_contraction_cycle", "FP_FALSE_20",
     "簇 RCC_BB_SQUEEZE：squeeze 深 × 低假突破。"),
    # DB32 原为 ULCER×FP_DOWN——与 r164 DB12 交换对称同哈希；CURRENT_DD_120 不存在；换 VFP_ULCER_SHIFT
    _pair("DB32", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", "FP_DOWN_20",
     "簇 VFP_ULCER_SHIFT：溃疡指数抬升 × 下行首达慢。"),
    _pair("DB33", "VFP_RECOVERY_20", "volume_free_path_v1", "FP_DOWN_20",
     "簇 VFP_RECOVERY：回撤恢复快 × 下行首达慢。"),
    _pair("DB34", "AUC_VARIANCE_RATIO_20", "auction_1m", "FP_CHG_UP_20",
     "簇 AUC_VARIANCE_RATIO：开盘方差比 × 上行首达加速。"),
    _pair("DB35", "CHIP_RANGE_90_60", "cost_distribution", "FP_CHG_CROSS_20",
     "簇 CHIP_RANGE：筹码区间 × 震荡降温。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s34b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage34_first_passage_times_batch2"
    plan["family_note"] = (
        "第 34 阶段第二批：FP 原子转右腿 × 确认左腿首批（每左腿本阶段一批）。右腿用量："
        "FP_UP 3 / FP_ASYM 3 / FP_CROSS 3 / FP_FALSE 3 / FP_DOWN 2 / FP_CHG_UP 1 / FP_CHG_CROSS 1；"
        "FP_UP_FRAC 低覆盖封配。16 条全跨族。FP 族原子缓存命中（r164 已建）。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s34b

if __name__ == "__main__":
    base.main()
