#!/usr/bin/env python3
"""Round 060 driver: stage 11 round 5 (entering streak: 2 zero rounds,
r058/r059 — a third triggers stage-11 exhaustion). Six NEW cross-family
pairs from the 20-atom verified pool; all mechanism names new; W3/Z1/7
atomic admitted vectors in the dedup reference set. Gate 7 v2.1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_060"

base.CANDIDATES = [
    {
        "id": "AI1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "bigbar_in_resilient_microstructure",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，r053 门 7 入选：+0.083/+0.055/t=2.92）；B=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）。假设：高强度活动落在高弹性微结构（信号高）=冲击被吸收的定向活动，延续。声明：BIGBAR_VOL_SHARE_20(AE1/AG1/AH1)第4次；RESILIENCY_20(U5/V4/X4/AB3)第9次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AI2",
        "operator": "rank_spread",
        "left": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "profile_anomaly_healthy_bleed_free",
        "hypothesis": "两腿角色：A=量分布距离（活动轮廓异常，r053 门 7 最强：+0.095/+0.044/t=4.04）；B=20 日溃疡（慢性失血）。假设：轮廓异常而溃疡浅（信号高）=健康结构中的活动异常（信息而非失血），延续；溃疡深（信号低）=异常是失血。声明：VOL_PROFILE_DISTANCE(AE3/AF2/AG1/AH3)第5次；ULCER_20(W6/AF3)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AI3",
        "operator": "rank_spread",
        "left": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "buyflow_no_extreme_damage",
        "hypothesis": "两腿角色：A=1m tick-rule 主买不平衡（定向买流，F1 左腿）；B=最差单日收益（极端损伤，r053 门 7 入选：+0.064/+0.065/t=2.18）。假设：定向买流强而最差单日不极端（信号高）=买流无损伤（有序吸筹），延续；最差日极端（信号低）=买流是自救。声明：TICK_IMBALANCE_20(F1/T1/AC4/Q4/AE2)第8次；WORST_DAY_20(AE1/AF1/AG6/AH4)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AI4",
        "operator": "rank_spread",
        "left": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "gap_trend_with_events",
        "hypothesis": "两腿角色：A=缺口修复率 60 日（趋势持续强度，r053 门 7 入选：−0.060/−0.043/t=2.59）；B=量 spike 频率（事件密集度，BB1 左腿）。假设：缺口不修复而事件密集（信号高）=趋势中的持续信息事件（定向推进），延续；事件稀疏（信号低）=趋势惰性。声明：GAP_FILL_FRACTION_60(AE4/AG2)第3次；VOL_SPIKE_FREQ_20(BB1 左腿/AF5/AG3/AH4)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AI5",
        "operator": "rank_spread",
        "left": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "ushape_rhythm_calm_category",
        "hypothesis": "两腿角色：A=日内 U 形 RV 占比（配置节律，r053 门 7 入选：−0.083/−0.089/t=2.12）；B=类别 20 日波动（环境噪声，r053 门 7 入选：−0.071/−0.065/t=2.42）。假设：节律存在而类别平静（信号高）=平静环境中的配置节律（非投机环境），延续；类别高波动（信号低）=节律是投机噪声。声明：VOL_USHAPE_20(T2/S4/AE2/AF1/AG2)第6次；CATEGORY_VOL_20(T4/Y3/N4/U2/AE3/AF4/AG4)第8次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AI6",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "concentrated_execution_acf_confirm",
        "hypothesis": "两腿角色：A=大 bar 时点集中度（机构执行节奏，r053 入选：−0.097/−0.046/t=2.55）；B=5 日收益一阶自相关符号（短期动量确认，T5 左腿）。假设：集中执行与短期动量确认同在（信号高）=机构节奏获得动量确认，延续。声明：BIGBAR_EDGE_CONC_20(AE5/AF3)第12次；SIGN_ACF1_5(T5 左腿/AE4/AF4/AH5)第5次。预期正方向。",
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
