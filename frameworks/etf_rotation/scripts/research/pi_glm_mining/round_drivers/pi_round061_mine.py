#!/usr/bin/env python3
"""Round 061 driver: stage 11 round 6 (3 admissions in r060, streak = 0).
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

base.ROUND_ID = "round_061"

base.CANDIDATES = [
    {
        "id": "AJ1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "bigbar_healthy_bleed_free",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，r053 门 7 入选：+0.083/+0.055/t=2.92）；B=20 日溃疡（慢性失血）。假设：高强度活动而溃疡浅（信号高）=活动无慢性失血背景（健康结构中的定向活动），延续；溃疡深（信号低）=活动是失血挣扎。声明：BIGBAR_VOL_SHARE_20(AE1/AG1/AH1/AI1 入选)第5次；ULCER_20(W6/AF3)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AJ2",
        "operator": "rank_spread",
        "left": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "profile_anomaly_open_config",
        "hypothesis": "两腿角色：A=量分布距离（活动轮廓异常，r053 门 7 最强：+0.095/+0.044/t=4.04）；B=开盘 30 分钟量占比（开盘配置机制，F1 右腿）。假设：轮廓异常伴随开盘配置占比高（信号高）=异常来自开盘配置时段的机构活动，延续。声明：VOL_PROFILE_DISTANCE(AE3/AF2/AG1/AH3)第5次；OPEN30_VOL_SHARE_20(F1 右腿/AF6 入选/AG6)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AJ3",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "bigbar_ushape_config_intensity",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度）；B=日内 U 形 RV 占比（配置节律）。假设：强度与节律并存（信号高）=开收盘配置时段承载定向大 bar 活动（机构建仓节奏），延续。声明：BIGBAR_VOL_SHARE_20(AE1/AG1/AH1/AI1 入选)第6次；VOL_USHAPE_20(T2/S4/AE2/AF1/AG2/AI5)第7次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AJ4",
        "operator": "rank_spread",
        "left": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "buyflow_trend_confirmed",
        "hypothesis": "两腿角色：A=1m tick-rule 主买不平衡（定向买流，F1 左腿）；B=缺口修复率 60 日（趋势持续强度，r053 门 7 入选：−0.060/−0.043/t=2.59）。假设：主买流强而缺口不修复（信号高）=买流方向与趋势持续互相确认，延续；缺口快速修复（信号低）=买流是逆趋势的短期回补。声明：TICK_IMBALANCE_20(F1/T1/AC4/Q4/AE2/AH3)第8次；GAP_FILL_FRACTION_60(AE4/AG2/AI4 入选)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AJ5",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "resilient_config_rhythm",
        "hypothesis": "两腿角色：A=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）；B=日内 U 形 RV 占比（配置节律）。假设：回复力高而节律存在（信号高）=节律活动落在高弹性微结构（配置盘微结构），延续。声明：RESILIENCY_20(U5/V4/X4/AB3/AE5/AI1 入选)第10次；VOL_USHAPE_20(T2/S4/AE2/AF1/AG2/AI5)第8次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AJ6",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "concentrated_execution_not_primary",
        "hypothesis": "两腿角色：A=大 bar 时点集中度（机构执行节奏，r053 入选：−0.097/−0.046/t=2.55）；B=份额变化-收益相关（一级流解释力）。假设：集中执行而一级流不解释价格（信号高）=执行来自二级自主配置（非申赎机械），延续；一级解释力强（信号低）=执行是申赎映射。声明：BIGBAR_EDGE_CONC_20(AE5/AF3)第13次；SHARE_RET_CORR_20(X6/M1/K4/R5/Y3/W3 入选/Y3)第9次。预期正方向。",
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
