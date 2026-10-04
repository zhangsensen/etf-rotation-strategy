#!/usr/bin/env python3
"""Round 065 driver: stage 11 round 10 (entering streak: 1 zero round, r064).
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

base.ROUND_ID = "round_065"

base.CANDIDATES = [
    {
        "id": "AN1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "bigbar_not_primary",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，r053 门 7 入选：+0.083/+0.055/t=2.92）；B=份额变化-收益相关（一级流解释力）。假设：高强度活动而一级流不解释价格（信号高）=活动非申赎映射（二级自主配置），延续；一级解释力强（信号低）=活动是申赎机械。声明：BIGBAR_VOL_SHARE_20(AE1/AG1/AH1/AI1 入选)第9次；SHARE_RET_CORR_20(X6/M1/K4/R5/Y3/W3 入选/Y3)第12次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AN2",
        "operator": "rank_spread",
        "left": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "profile_anomaly_resilient",
        "hypothesis": "两腿角色：A=量分布距离（活动轮廓异常，r053 门 7 最强：+0.095/+0.044/t=4.04）；B=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）。假设：轮廓异常而回复力高（信号高）=异常活动落在高弹性微结构（吸收良好），延续。声明：VOL_PROFILE_DISTANCE(AE3/AF2/AG1/AH3/AI2)第8次；RESILIENCY_20(U5/V4/X4/AB3/AE5/AI1 入选/AK3 原稿/AK5/AL2/AL3 入选)第14次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AN3",
        "operator": "rank_spread",
        "left": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "right": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "no_damage_persistent_participation",
        "hypothesis": "两腿角色：A=最差单日收益（极端损伤，r053 门 7 入选：+0.064/+0.065/t=2.18）；B=量自相关（量的持续性，Z2 右腿）。假设：最差单日不极端而量持续（信号高）=无损伤的持续参与（配置盘），延续；量不持续（信号低）=参与是脉冲噪声。声明：WORST_DAY_20(AE1/AF1/AG6/AH4/AI3)第6次；VOL_AUTOCORR_20(Z2 右腿/AE6/AG5/AK2 原稿)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AN4",
        "operator": "rank_spread",
        "left": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "profile_anomaly_trend",
        "hypothesis": "两腿角色：A=量分布距离（活动轮廓异常，r053 门 7 最强）；B=缺口修复率 60 日（趋势持续强度，r053 门 7 入选：−0.060/−0.043/t=2.59）。假设：轮廓异常而缺口不修复（信号高）=异常活动伴随趋势持续（定向推进），延续；缺口快速修复（信号低）=异常无趋势支持。声明：VOL_PROFILE_DISTANCE(AE3/AF2/AG1/AH3/AI2/AN2)第9次；GAP_FILL_FRACTION_60(AE4/AG2/AI4 入选)第7次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AN5",
        "operator": "rank_spread",
        "left": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "open_config_acf_confirm",
        "hypothesis": "两腿角色：A=开盘 30 分钟量占比（开盘配置机制，F1 右腿）；B=5 日收益一阶自相关符号（短期动量确认，T5 左腿）。假设：开盘配置占比高而收益自相关为正（信号高）=开盘机制伴随短期动量确认（延续性），延续。声明：OPEN30_VOL_SHARE_20(F1 右腿/AF6 入选/AG6/AJ2/AM1)第6次；SIGN_ACF1_5(T5 左腿/AE4/AF4/AH5)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AN6",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "directional_skew_resilient",
        "hypothesis": "两腿角色：A=大 bar 方向偏度（大单方向一致性，Z2 左腿）；B=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）。假设：方向偏度明确而回复力高（信号高）=方向性大单被弹性吸收（有序执行），延续。声明：BIGBAR_DIR_SKEW_20(Z2 左腿/AG3)第4次；RESILIENCY_20(U5/V4/X4/AB3/AE5/AI1 入选/AK3 原稿/AK5/AL2/AL3 入选/AN2)第15次。预期正方向。",
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
