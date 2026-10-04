#!/usr/bin/env python3
"""Round 064 driver: stage 11 round 9 (AL3 admitted in r063, streak = 0).
Six NEW cross-family pairs from the 20-atom verified pool; all mechanism
names new; W3/Z1/7-atomic + AI1/AI4/AI6 admitted vectors in the dedup
reference set. Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_064"

base.CANDIDATES = [
    {
        "id": "AM1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "bigbar_open_config",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，r053 门 7 入选：+0.083/+0.055/t=2.92）；B=开盘 30 分钟量占比（开盘配置机制，F1 右腿）。假设：高强度活动伴随开盘配置占比高（信号高）=活动锚定在开盘配置时段（机构节奏），延续。声明：BIGBAR_VOL_SHARE_20(AE1/AG1/AH1/AI1 入选)第7次；OPEN30_VOL_SHARE_20(F1 右腿/AF6 入选/AG6/AJ2)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AM2",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "concentrated_execution_open",
        "hypothesis": "两腿角色：A=大 bar 时点集中度（机构执行节奏，r053 入选：−0.097/−0.046/t=2.55）；B=开盘 30 分钟量占比（开盘配置机制，F1 右腿）。假设：集中执行伴随开盘配置占比高（信号高）=机构开盘集中执行（有锚点的节奏），延续。声明：BIGBAR_EDGE_CONC_20(AE5/AF3/AK2/AK4/AK3 原稿)第17次；OPEN30_VOL_SHARE_20(F1 右腿/AF6 入选/AG6/AJ2)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AM3",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "directional_skew_gap_trend",
        "hypothesis": "两腿角色：A=大 bar 方向偏度（大单方向一致性，Z2 左腿）；B=缺口修复率 60 日（趋势持续强度，r053 门 7 入选：−0.060/−0.043/t=2.59）。假设：方向偏度明确而缺口不修复（信号高）=大单方向与趋势持续互相确认，延续。声明：BIGBAR_DIR_SKEW_20(Z2 左腿/AG3)第3次；GAP_FILL_FRACTION_60(AE4/AG2/AI4 入选)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AM4",
        "operator": "rank_spread",
        "left": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "buyflow_calm_category",
        "hypothesis": "两腿角色：A=1m tick-rule 主买不平衡（定向买流，F1 左腿）；B=类别 20 日波动（环境噪声，r053 门 7 入选：−0.071/−0.065/t=2.42）。假设：定向买流强而类别平静（信号高）=非投机环境的定向买流（信息驱动），延续；类别高波动（信号低）=买流被环境噪声淹没。声明：TICK_IMBALANCE_20(F1/T1/AC4/Q4/AE2/AH3/AJ4)第9次；CATEGORY_VOL_20(T4/Y3/N4/U2/AE3/AF4/AG4/AI5)第9次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AM5",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "dense_events_high_position",
        "hypothesis": "两腿角色：A=量 spike 频率（事件密集度，BB1 左腿）；B=价格 20 日区间位置（价格高低位，F2 右腿）。假设：事件密集而价格处于高位（信号高）=盈利资产上的活跃事件（健康活跃），延续；价格低位（信号低）=事件是低位挣扎。声明：VOL_SPIKE_FREQ_20(BB1 左腿/AF5/AG3/AH4/AI4)第8次；PRICE_POSITION_20(F2 右腿/AL1/AL4)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AM6",
        "operator": "rank_spread",
        "left": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "close_confirm_no_damage",
        "hypothesis": "两腿角色：A=尾 5 分钟与全日方向一致性（收盘确认，F2 左腿）；B=最差单日收益（极端损伤，r053 门 7 入选：+0.064/+0.065/t=2.18）。假设：收盘确认强而最差单日不极端（信号高）=日内动量有收盘确认且无极端损伤，延续。声明：CLOSE5_DAY_CONSIST_20(F2 左腿/Q4/AH5)第5次；WORST_DAY_20(AE1/AF1/AG6/AH4/AI3)第6次。预期正方向。",
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
        "去重参照集含 9 组合 + 7 atomic 入选向量"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage11

if __name__ == "__main__":
    base.main()
