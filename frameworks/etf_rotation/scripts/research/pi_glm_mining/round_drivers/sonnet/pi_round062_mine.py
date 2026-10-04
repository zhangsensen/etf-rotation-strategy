#!/usr/bin/env python3
"""Round 062 driver: stage 11 round 7 (entering streak: 1 zero round, r061).
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

base.ROUND_ID = "round_062"

base.CANDIDATES = [
    {
        "id": "AK1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "bigbar_calm_category",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，r053 门 7 入选：+0.083/+0.055/t=2.92）；B=类别 20 日波动（环境噪声，r053 门 7 入选：−0.071/−0.065/t=2.42）。假设：高强度活动而类别平静（信号高）=活动非环境投机噪声（定向配置），延续；类别高波动（信号低）=活动被投机淹没。声明：BIGBAR_VOL_SHARE_20(AE1/AG1/AH1/AI1 入选)第6次；CATEGORY_VOL_20(T4/Y3/N4/U2/AE3/AF4/AG4)第8次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AK2",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "concentrated_execution_profile_anomaly",
        "hypothesis": "两腿角色：A=大 bar 时点集中度（机构执行节奏，r053 入选：−0.097/−0.046/t=2.55）；B=量分布距离（活动轮廓异常，r053 门 7 最强：+0.095/+0.044/t=4.04）。假设：集中执行伴随轮廓异常（信号高）=机构执行的异常活动（有主体），延续。声明：BIGBAR_EDGE_CONC_20(AE5/AF3)第14次；VOL_PROFILE_DISTANCE(AE3/AF2/AG1/AH3/AI2)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AK3",
        "operator": "rank_spread",
        "left": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "close_confirm_resilient",
        "hypothesis": "两腿角色：A=尾 5 分钟与全日方向一致性（收盘确认，F2 左腿）；B=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）。假设：收盘确认强而回复力高（信号高）=日内动量获得收盘确认且微结构有弹性，延续。声明：CLOSE5_DAY_CONSIST_20(F2 左腿/Q4/AH5)第4次；RESILIENCY_20(U5/V4/X4/AB3/AE5/AI1 入选/AK3 原稿重复已换)第11次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AK4",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "concentrated_execution_ushape",
        "hypothesis": "两腿角色：A=大 bar 时点集中度（机构执行节奏）；B=日内 U 形 RV 占比（配置节律，r053 门 7 入选）。假设：集中执行与 U 形节律并存（信号高）=执行落在开收盘配置时段（有节奏的机构活动），延续；无节律（信号低）=执行随机化。声明：BIGBAR_EDGE_CONC_20(AE5/AF3/AK2)第15次；VOL_USHAPE_20(T2/S4/AE2/AF1/AG2/AI5)第8次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AK5",
        "operator": "rank_spread",
        "left": {"name": "ULCER_20", "source": "downside_risk"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "healthy_bleed_free_resilient",
        "hypothesis": "两腿角色：A=20 日溃疡（慢性失血，BB1 右腿）；B=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）。假设：溃疡浅而回复力高（信号高）=健康结构+高弹性（双重干净微结构），延续；溃疡深（信号低）=失血结构的弹性不可信。声明：ULCER_20(W6/AF3)第3次；RESILIENCY_20(U5/V4/X4/AB3/AE5/AI1 入选/AK3)第11次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AK6",
        "operator": "rank_spread",
        "left": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "no_damage_not_primary",
        "hypothesis": "两腿角色：A=最差单日收益（极端损伤，r053 门 7 入选：+0.064/+0.065/t=2.18）；B=份额变化-收益相关（一级流解释力）。假设：最差单日不极端而一级流不解释价格（信号高）=无损伤且非申赎驱动（干净微结构），延续；一级解释力强（信号低）=价格是申赎映射。声明：WORST_DAY_20(AE1/AF1/AG6/AH4/AI3)第6次；SHARE_RET_CORR_20(X6/M1/K4/R5/Y3/W3 入选/Y3)第10次。预期正方向。",
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
