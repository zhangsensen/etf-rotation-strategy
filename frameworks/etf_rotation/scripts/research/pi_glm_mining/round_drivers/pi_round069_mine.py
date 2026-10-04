#!/usr/bin/env python3
"""Round 069 driver: stage 11 round 14. Entering streak: 2 zero rounds
(r067/r068) — a third triggers stage-11 exhaustion. Six NEW cross-family
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

base.ROUND_ID = "round_069"

base.CANDIDATES = [
    {
        "id": "AS1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "bigbar_high_position",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，r053 门 7 入选：+0.083/+0.055/t=2.92）；B=价格 20 日区间位置（价格高低位，F2 右腿）。假设：高强度活动而价格处于高位（信号高）=强度+获利位置（强势确认），延续；价格低位（信号低）=活动是低位自救。声明：BIGBAR_VOL_SHARE_20(AE1/AG1/AH1/AI1 入选)第13次；PRICE_POSITION_20(F2 右腿/AL1/AL4)第7次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AS2",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "concentrated_execution_high_activity",
        "hypothesis": "两腿角色：A=大 bar 时点集中度（机构执行节奏，r053 入选：−0.097/−0.046/t=2.55）；B=对数成交额（活跃水平，T5 右腿）。假设：集中执行而活跃水平高（信号高）=集中执行伴随高活跃（有主体），延续；低活跃（信号低）=执行是孤立异常。声明：BIGBAR_EDGE_CONC_20(AE5/AF3/AK2/AK4)第19次；LOG_AMOUNT_VOL_20(T5 右腿/AC6/AF6 入选/AG4)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AS3",
        "operator": "rank_spread",
        "left": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "buyflow_not_primary",
        "hypothesis": "两腿角色：A=1m tick-rule 主买不平衡（定向买流，F1 左腿）；B=份额变化-收益相关（一级流解释力）。假设：主买流强而一级流不解释价格（信号高）=买流非申赎驱动（二级自身买盘），延续；一级解释力强（信号低）=买流是申赎映射。声明：TICK_IMBALANCE_20(F1/T1/AC4/Q4/AE2/AH3/AJ4)第11次；SHARE_RET_CORR_20(X6/M1/K4/R5/Y3/W3 入选/Y3)第13次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AS4",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "dense_events_high_activity",
        "hypothesis": "两腿角色：A=量 spike 频率（事件密集度，BB1 左腿）；B=对数成交额（活跃水平，T5 右腿）。假设：事件密集而活跃水平高（信号高）=密集事件伴随高活跃（真实事件环境），延续。声明：VOL_SPIKE_FREQ_20(BB1 左腿/AF5/AG3/AH4/AI4)第10次；LOG_AMOUNT_VOL_20(T5 右腿/AC6/AF6 入选/AG4)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AS5",
        "operator": "rank_spread",
        "left": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "persistent_volume_high_position",
        "hypothesis": "两腿角色：A=量自相关（量的持续性，Z2 右腿）；B=价格 20 日区间位置（价格高低位，F2 右腿）。假设：量持续而价格处于高位（信号高）=持续参与伴随获利位置（强势确认），延续；价格低位（信号低）=持续参与是低位挣扎。声明：VOL_AUTOCORR_20(Z2 右腿/AE6/AG5/AN3)第5次；PRICE_POSITION_20(F2 右腿/AL1/AL4/AP6)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AS6",
        "operator": "rank_spread",
        "left": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "close_confirm_not_primary",
        "hypothesis": "两腿角色：A=尾 5 分钟与全日方向一致性（收盘确认，F2 左腿）；B=份额变化-收益相关（一级流解释力）。假设：收盘确认强而一级流不解释价格（信号高）=日内动量有收盘确认且非申赎驱动（二级自身定价），延续。声明：CLOSE5_DAY_CONSIST_20(F2 左腿/Q4/AH5)第5次；SHARE_RET_CORR_20(X6/M1/K4/R5/Y3/W3 入选/Y3)第12次。预期正方向。",
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
