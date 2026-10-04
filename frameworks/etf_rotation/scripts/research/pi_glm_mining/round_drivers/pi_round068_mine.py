#!/usr/bin/env python3
"""Round 068 driver: stage 11 round 13. Entering streak: 2 zero rounds
(r066/r067) — a third triggers stage-11 exhaustion. Six NEW cross-family
pairs from the 20-atom verified pool; all mechanism names new; W3/Z1/7
atomic + AI1/AI4/AI6/AN2/AN6 admitted vectors in the dedup reference set.
Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_068"

base.CANDIDATES = [
    {
        "id": "AQ1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "bigbar_dense_events",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，r053 门 7 入选：+0.083/+0.055/t=2.92）；B=量 spike 频率（事件密集度，BB1 左腿）。假设：高强度活动伴随事件密集（信号高）=定向活动与事件节律同在（真实活动环境），延续。声明：BIGBAR_VOL_SHARE_20(AE1/AG1/AH1/AI1 入选)第11次；VOL_SPIKE_FREQ_20(BB1 左腿/AF5/AG3/AH4/AI4)第9次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AQ2",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "bigbar_high_activity",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度）；B=对数成交额（活跃水平，T5 右腿）。假设：高强度活动与高活跃水平并存（信号高）=大 bar 是活跃环境的自然产物（非异常爆发），延续；低活跃（信号低）=大 bar 是孤立异常。声明：BIGBAR_VOL_SHARE_20(AE1/AG1/AH1/AI1 入选)第12次；LOG_AMOUNT_VOL_20(T5 右腿/AC6/AF6 入选/AG4)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AQ3",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "directional_skew_calm_category",
        "hypothesis": "两腿角色：A=大 bar 方向偏度（大单方向一致性，Z2 左腿）；B=类别 20 日波动（环境噪声，r053 门 7 入选：−0.071/−0.065/t=2.42）。假设：方向偏度明确而类别平静（信号高）=方向性大单非环境噪声（自身信息），延续；类别高波动（信号低）=偏度被环境淹没。声明：BIGBAR_DIR_SKEW_20(Z2 左腿/AG3/AN6 入选)第6次；CATEGORY_VOL_20(T4/Y3/N4/U2/AE3/AF4/AG4/AI5)第10次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AQ4",
        "operator": "rank_spread",
        "left": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "buyflow_high_position",
        "hypothesis": "两腿角色：A=1m tick-rule 主买不平衡（定向买流，F1 左腿）；B=价格 20 日区间位置（价格高低位，F2 右腿）。假设：主买流强而价格处于高位（信号高）=买流+获利位置（强势确认），延续；价格低位（信号低）=买流是低位自救。声明：TICK_IMBALANCE_20(F1/T1/AC4/Q4/AE2/AH3/AJ4)第10次；PRICE_POSITION_20(F2 右腿/AL1/AL4)第7次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AQ5",
        "operator": "rank_spread",
        "left": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "close_confirm_gap_trend",
        "hypothesis": "两腿角色：A=尾 5 分钟与全日方向一致性（收盘确认，F2 左腿）；B=缺口修复率 60 日（趋势持续强度，r053 门 7 入选：−0.060/−0.043/t=2.59）。假设：收盘确认强而缺口不修复（信号高）=收盘确认与趋势持续互相支持，延续。声明：CLOSE5_DAY_CONSIST_20(F2 左腿/Q4/AH5)第5次；GAP_FILL_FRACTION_60(AE4/AG2/AI4 入选)第11次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AQ6",
        "operator": "rank_spread",
        "left": {"name": "ULCER_20", "source": "downside_risk"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "healthy_structure_gap_trend",
        "hypothesis": "两腿角色：A=20 日溃疡（慢性失血，BB1 右腿）；B=缺口修复率 60 日（趋势持续强度，r053 门 7 入选）。假设：溃疡浅而缺口不修复（信号高）=健康结构中的趋势持续（非失血性趋势），延续；溃疡深（信号低）=趋势是失血。声明：ULCER_20(W6/AF3/AJ1)第3次；GAP_FILL_FRACTION_60(AE4/AG2/AI4 入选)第11次。预期正方向。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage11(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage11_verified_atom_pairing"
    plan["pairing_note"] = (
        "第 11 阶段：仅在已通过门 7 的原子与历史入选组合腿（共 20 原子）之间定向配对；"
        "REPORT 每条并列两腿单原子的门 7 数字与增量 = 组合 − max(两腿)；"
        "去重参照集含 9 组合 + 7 atomic + AN2/AN6 入选向量"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage11

if __name__ == "__main__":
    base.main()
