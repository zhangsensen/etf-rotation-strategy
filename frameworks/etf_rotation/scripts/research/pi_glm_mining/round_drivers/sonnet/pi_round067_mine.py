#!/usr/bin/env python3
"""Round 067 driver: stage 11 round 12 (entering streak: 1 zero round, r066).
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

base.ROUND_ID = "round_067"

base.CANDIDATES = [
    {
        "id": "AP1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "bigbar_trend_gap",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，r053 门 7 入选：+0.083/+0.055/t=2.92）；B=缺口修复率 60 日（趋势持续强度，r053 门 7 入选：−0.060/−0.043/t=2.59）。假设：高强度活动而缺口不修复（信号高）=活动伴随趋势持续（定向推进），延续。声明：BIGBAR_VOL_SHARE_20(AE1/AG1/AH1/AI1 入选)第10次；GAP_FILL_FRACTION_60(AE4/AG2/AI4 入选)第9次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AP2",
        "operator": "rank_spread",
        "left": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "profile_anomaly_acf_confirm",
        "hypothesis": "两腿角色：A=量分布距离（活动轮廓异常，r053 门 7 最强：+0.095/+0.044/t=4.04）；B=5 日收益一阶自相关符号（短期动量确认，T5 左腿）。假设：轮廓异常而收益自相关为正（信号高）=异常活动伴随短期动量确认（延续性），延续。声明：VOL_PROFILE_DISTANCE(AE3/AF2/AG1/AH3/AI2/AN2 入选/AN4)第11次；SIGN_ACF1_5(T5 左腿/AE4/AF4/AH5)第7次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AP3",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "dense_events_profile_anomaly",
        "hypothesis": "两腿角色：A=量 spike 频率（事件密集度，BB1 左腿）；B=量分布距离（活动轮廓异常，r053 门 7 最强）。假设：事件密集而轮廓异常（信号高）=密集事件伴随轮廓偏离（真实活动异常），延续。声明：VOL_SPIKE_FREQ_20(BB1 左腿/AF5/AG3/AH4/AI4)第9次；VOL_PROFILE_DISTANCE(AE3/AF2/AG1/AH3/AI2/AN2 入选/AN4/AP2)第12次。注意：本对两腿族名不同（intraday_volume_profile_1m vs intraday_profile_deviation），跨族成立。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AP4",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "resilient_no_damage",
        "hypothesis": "两腿角色：A=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）；B=最差单日收益（极端损伤，r053 门 7 入选：+0.064/+0.065/t=2.18）。假设：回复力高而最差单日不极端（信号高）=弹性微结构+无极端损伤（双重干净），延续。声明：RESILIENCY_20(U5/V4/X4/AB3/AE5/AI1 入选/AK3 原稿/AK5/AL2/AL3 入选/AN2 入选/AN6 入选)第16次；WORST_DAY_20(AE1/AF1/AG6/AH4/AI3)第10次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AP5",
        "operator": "rank_spread",
        "left": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "persistent_volume_trend",
        "hypothesis": "两腿角色：A=量自相关（量的持续性，Z2 右腿）；B=缺口修复率 60 日（趋势持续强度，r053 门 7 入选）。假设：量持续而缺口不修复（信号高）=持续参与伴随趋势持续（延续性环境），延续。声明：VOL_AUTOCORR_20(Z2 右腿/AE6/AG5)第6次；GAP_FILL_FRACTION_60(AE4/AG2/AI4 入选)第10次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AP6",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "directional_skew_high_position",
        "hypothesis": "两腿角色：A=大 bar 方向偏度（大单方向一致性，Z2 左腿）；B=价格 20 日区间位置（价格高低位，F2 右腿）。假设：方向偏度明确而价格处于高位（信号高）=方向性大单+获利位置（强势确认），延续。声明：BIGBAR_DIR_SKEW_20(Z2 左腿/AG3/AN6 入选)第6次；PRICE_POSITION_20(F2 右腿/AL1/AL4)第6次。预期正方向。",
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
