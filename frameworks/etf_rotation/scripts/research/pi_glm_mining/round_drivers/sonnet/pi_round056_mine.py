#!/usr/bin/env python3
"""Round 056 driver: stage 11 = directed pairing among VERIFIED atoms only
(7 gate-7 single-atom passers + 13 admitted-combination legs, 20 atoms).
Cross-family pairs only; tested pairs excluded (verified against plan
history); dedup now also guards against shadowing either single leg (the
7 atomic admitted vectors sit in the reference set). Gate 7 v2.1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_056"

base.CANDIDATES = [
    {
        "id": "AE1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "bigbar_activity_no_extreme_damage",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，门 7 入选原子：发现 +0.083/审计 +0.055/t=2.92）；B=最差单日收益（极端损伤，门 7 入选原子：+0.064/+0.065/t=2.18）。假设：大 bar 活动高而最差单日不极端（信号高）=定向活动无极端损伤，延续；极端损伤（信号低）=活动是出逃。增量检验：组合 top-3 超额能否超过 max(两腿)。新配对（两腿均为 r053 门 7 入选原子，组合首次）。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AE2",
        "operator": "rank_spread",
        "left": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "ushape_rhythm_buyflow_aligned",
        "hypothesis": "两腿角色：A=日内 U 形 RV 占比（开收盘波动节律，r053 入选原子：−0.083/−0.089/t=2.12）；B=1m tick-rule 主买不平衡。假设：节律波动与主买流同向强（信号高）=活动节律与买流方向一致（配置节律真实），延续。声明：VOL_USHAPE_20(T2/S4)第3次；TICK_IMBALANCE_20(F1/T1/AC4/Q4)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AE3",
        "operator": "rank_spread",
        "left": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "profile_anomaly_in_calm_category",
        "hypothesis": "两腿角色：A=量分布距离（活动轮廓异常，r053 门 7 最强原子：+0.095/+0.044/t=4.04）；B=类别 20 日波动（环境噪声）。假设：活动轮廓异常而类别平静（信号高）=异常来自信息（非环境噪声），延续。声明：VOL_PROFILE_DISTANCE 首次价差腿（r053 入选原子）；CATEGORY_VOL_20(T4/Y3/N4/U2)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AE4",
        "operator": "rank_spread",
        "left": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "gap_persistence_acf_confirmation",
        "hypothesis": "两腿角色：A=缺口修复率 60 日（趋势持续强度，r053 入选原子：−0.060/−0.043/t=2.59）；B=5 日收益一阶自相关符号（短期动量确认，T5 左腿）。假设：缺口修复率低（缺口持续=趋势强）且收益自相关为正（信号高）=双重趋势确认，延续。声明：GAP_FILL_FRACTION_60 首次价差腿（r053 入选原子）；SIGN_ACF1_5(T5 左腿)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AE5",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "mechanism": "resilient_bigbar_concentration",
        "hypothesis": "两腿角色：A=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理，r043 门 7 组合 W3 的腿）；B=大 bar 时点集中度（机构执行节奏，r053 入选原子：−0.097/−0.046/t=2.55）。假设：回复力高且大 bar 集中（信号高）=机构化执行提供的弹性，延续。声明：RESILIENCY_20(U5/V4/X4/AB3，Z1 入选)第7次；BIGBAR_EDGE_CONC_20(C2/F5/Z1/G3/H4/W6/M5)第9次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AE6",
        "operator": "rank_spread",
        "left": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "right": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "active_persistent_participation",
        "hypothesis": "两腿角色：A=对数成交额（活跃水平，T5 右腿）；B=量自相关（量的持续性，Z2 右腿）。假设：活跃且量持续（信号高）=持续的真实参与（非脉冲式活动），延续；低活跃或不持续（信号低）=参与是脉冲噪声。声明：LOG_AMOUNT_VOL_20(T5 右腿)第2次；VOL_AUTOCORR_20(Z2 右腿)第2次。预期正方向。",
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
        "去重参照集含 9 组合 + 7 atomic 入选向量（两腿单原子影子自动被 ≥0.7 拒绝）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage11

if __name__ == "__main__":
    base.main()
