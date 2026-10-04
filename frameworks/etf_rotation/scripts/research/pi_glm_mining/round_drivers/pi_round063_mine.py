#!/usr/bin/env python3
"""Round 063 driver: stage 11 round 8. Entering streak: 2 zero rounds
(r061/r062) — a third triggers stage-11 exhaustion. Six NEW cross-family
pairs from the 20-atom verified pool (PRICE_POSITION_20 first deployment);
all mechanism names new; W3/Z1/7-atomic admitted vectors in the dedup
reference set. Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_063"

base.CANDIDATES = [
    {
        "id": "AL1",
        "operator": "rank_spread",
        "left": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "price_position_trend_confirm",
        "hypothesis": "两腿角色：A=价格 20 日区间位置（价格高低位，F2 右腿）；B=缺口修复率 60 日（趋势持续强度，r053 门 7 入选：−0.060/−0.043/t=2.59）。假设：价格处于区间高位且缺口不修复（信号高）=高位定价与趋势持续互相确认，延续；价格低位（信号低）=低位+趋势弱。声明：PRICE_POSITION_20(F2 右腿)第2次；GAP_FILL_FRACTION_60(AE4/AG2/AI4 入选)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AL2",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "dense_events_resilient",
        "hypothesis": "两腿角色：A=量 spike 频率（事件密集度，BB1 左腿）；B=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）。假设：事件密集而回复力高（信号高）=密集事件被高弹性微结构吸收（无持久冲击），延续；回复力低（信号低）=事件造成持久损伤。声明：VOL_SPIKE_FREQ_20(BB1 左腿/AF5/AG3/AH4/AI4)第7次；RESILIENCY_20(U5/V4/X4/AB3/AE5/AI1 入选/AK3 原稿/AK5)第13次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AL3",
        "operator": "rank_spread",
        "left": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "active_resilient_liquidity",
        "hypothesis": "两腿角色：A=对数成交额（活跃水平，T5 右腿）；B=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）。假设：活跃水平高而回复力高（信号高）=高活跃落在高弹性微结构（深度流动性吸收活跃），延续；回复力低（信号低）=活跃造成持久冲击。声明：LOG_AMOUNT_VOL_20(T5 右腿/AC6/AF6 入选/AG4)第5次；RESILIENCY_20(U5/V4/X4/AB3/AE5/AI1 入选/AK3/AK5/AL2)第14次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AL4",
        "operator": "rank_spread",
        "left": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "independent_pricing_profitable_position",
        "hypothesis": "两腿角色：A=份额变化-收益相关（一级流解释力）；B=价格 20 日区间位置。假设：一级流不解释价格而价格处于区间高位（信号高）=定价独立于申赎且资产在盈利位置（自主定价的健康资产），延续；价格低位（信号低）=低位+申赎主导。声明：SHARE_RET_CORR_20(X6/M1/K4/R5/Y3/W3 入选/Y3)第11次；PRICE_POSITION_20(F2 右腿/AL1)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AL5",
        "operator": "rank_spread",
        "left": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "rhythm_acf_confirmed",
        "hypothesis": "两腿角色：A=日内 U 形 RV 占比（配置节律，r053 门 7 入选：−0.083/−0.089/t=2.12）；B=5 日收益一阶自相关符号（短期动量确认，T5 左腿）。假设：节律存在且收益自相关为正（信号高）=节律活动伴随正自相关（动量延续），延续。声明：VOL_USHAPE_20(T2/S4/AE2/AF1/AG2/AI5)第8次；SIGN_ACF1_5(T5 左腿/AE4/AF4/AH5)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AL6",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "concentrated_execution_no_damage",
        "hypothesis": "两腿角色：A=大 bar 时点集中度（机构执行节奏，r053 入选：−0.097/−0.046/t=2.55）；B=最差单日收益（极端损伤，r053 门 7 入选：+0.064/+0.065/t=2.18）。假设：集中执行而最差单日不极端（信号高）=集中执行无极端损伤（有序机构活动），延续；最差日极端（信号低）=执行伴随损伤。声明：BIGBAR_EDGE_CONC_20(AE5/AF3/AK2/AK4)第16次；WORST_DAY_20(AE1/AF1/AG6/AH4/AI3)第7次。预期正方向。",
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
