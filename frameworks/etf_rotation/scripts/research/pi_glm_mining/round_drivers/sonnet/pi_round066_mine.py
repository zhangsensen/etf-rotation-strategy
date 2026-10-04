#!/usr/bin/env python3
"""Round 066 driver: stage 11 round 11 (AN2/AN6 admitted in r065, streak = 0).
Six NEW cross-family pairs from the 20-atom verified pool; all mechanism
names new; W3/Z1/7-atomic + AI1/AI4/AI6/AN2/AN6 admitted vectors in the
dedup reference set. Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_066"

base.CANDIDATES = [
    {
        "id": "AO1",
        "operator": "rank_spread",
        "left": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "no_damage_trend",
        "hypothesis": "两腿角色：A=最差单日收益（极端损伤，r053 门 7 入选：+0.064/+0.065/t=2.18）；B=缺口修复率 60 日（趋势持续强度，r053 门 7 入选：−0.060/−0.043/t=2.59）。假设：最差单日不极端而缺口不修复（信号高）=无极端损伤且趋势持续（干净趋势），延续。声明：WORST_DAY_20(AE1/AF1/AG6/AH4/AI3)第7次；GAP_FILL_FRACTION_60(AE4/AG2/AI4 入选)第8次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AO2",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "concentrated_execution_calm_category",
        "hypothesis": "两腿角色：A=大 bar 时点集中度（机构执行节奏，r053 入选：−0.097/−0.046/t=2.55）；B=类别 20 日波动（环境噪声，r053 门 7 入选：−0.071/−0.065/t=2.42）。假设：集中执行而类别平静（信号高）=机构执行非环境投机（有主体），延续；类别高波动（信号低）=执行被投机淹没。声明：BIGBAR_EDGE_CONC_20(AE5/AF3/AK2/AK4)第18次；CATEGORY_VOL_20(T4/Y3/N4/U2/AE3/AF4/AG4/AI5)第9次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AO3",
        "operator": "rank_spread",
        "left": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "profile_anomaly_no_damage",
        "hypothesis": "两腿角色：A=量分布距离（活动轮廓异常，r053 门 7 最强：+0.095/+0.044/t=4.04）；B=最差单日收益（极端损伤，r053 门 7 入选）。假设：轮廓异常而最差单日不极端（信号高）=异常活动无损伤（信息驱动），延续；最差日极端（信号低）=异常是损伤。声明：VOL_PROFILE_DISTANCE(AE3/AF2/AG1/AH3/AI2/AN2 入选)第10次；WORST_DAY_20(AE1/AF1/AG6/AH4/AI3)第8次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AO4",
        "operator": "rank_spread",
        "left": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "open_config_resilient",
        "hypothesis": "两腿角色：A=开盘 30 分钟量占比（开盘配置机制，F1 右腿）；B=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）。假设：开盘配置占比高而回复力高（信号高）=开盘配置落在高弹性微结构（吸收良好），延续；回复力低（信号低）=开盘活动造成持久冲击。声明：OPEN30_VOL_SHARE_20(F1 右腿/AF6 入选/AG6/AJ2/AM1)第7次；RESILIENCY_20(U5/V4/X4/AB3/AE5/AI1 入选/AK3 原稿/AK5/AL2/AL3 入选/AN2 入选)第15次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AO5",
        "operator": "rank_spread",
        "left": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "rhythm_profitable_position",
        "hypothesis": "两腿角色：A=日内 U 形 RV 占比（配置节律，r053 门 7 入选：−0.083/−0.089/t=2.12）；B=价格 20 日区间位置（价格高低位，F2 右腿）。假设：节律存在而价格处于高位（信号高）=盈利位置上的配置节律（健康配置），延续；价格低位（信号低）=节律是低位挣扎。声明：VOL_USHAPE_20(T2/S4/AE2/AF1/AG2/AI5)第9次；PRICE_POSITION_20(F2 右腿/AL1/AL4)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AO6",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "directional_skew_no_damage",
        "hypothesis": "两腿角色：A=大 bar 方向偏度（大单方向一致性，Z2 左腿）；B=最差单日收益（极端损伤，r053 门 7 入选）。假设：方向偏度明确而最差单日不极端（信号高）=方向性大单无极端损伤（有序执行），延续。声明：BIGBAR_DIR_SKEW_20(Z2 左腿/AG3/AN6 入选)第5次；WORST_DAY_20(AE1/AF1/AG6/AH4/AI3)第9次。预期正方向。",
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
