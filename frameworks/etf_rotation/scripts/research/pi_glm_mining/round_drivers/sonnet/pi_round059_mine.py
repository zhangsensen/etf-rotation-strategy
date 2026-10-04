#!/usr/bin/env python3
"""Round 059 driver: stage 11 round 4 (entering streak: 1 zero round, r058).
Six NEW cross-family pairs from the 20-atom verified pool; all mechanism
names new; W3/Z1/7-atomic admitted vectors in the dedup reference set.
Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_059"

base.CANDIDATES = [
    {
        "id": "AH1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "bigbar_persistent_participation",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，r053 门 7 入选：+0.083/+0.055/t=2.92）；B=量自相关（量的持续性，Z2 右腿）。假设：高强度活动伴随持续参与（信号高）=定向活动有连续资金支持（非脉冲），延续。声明：BIGBAR_VOL_SHARE_20(AE1/AG1)第3次；VOL_AUTOCORR_20(Z2 右腿/AE6/AG5)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AH2",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "concentrated_execution_trend",
        "hypothesis": "两腿角色：A=大 bar 时点集中度（机构执行节奏，r053 入选：−0.097/−0.046/t=2.55）；B=缺口修复率 60 日（趋势持续强度，r053 入选：−0.060/−0.043/t=2.59）。假设：集中执行且缺口不修复（信号高）=机构执行与趋势持续同在，延续。声明：BIGBAR_EDGE_CONC_20(AE5/AF3)第11次；GAP_FILL_FRACTION_60(AE4/AG2)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AH3",
        "operator": "rank_spread",
        "left": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "buyflow_with_profile_anomaly",
        "hypothesis": "两腿角色：A=1m tick-rule 主买不平衡（定向买流，F1 左腿）；B=量分布距离（活动轮廓异常，r053 门 7 最强：+0.095/+0.044/t=4.04）。假设：定向买流伴随轮廓异常（信号高）=信息驱动的活动（非噪声），延续。声明：TICK_IMBALANCE_20(F1/T1/AC4/Q4/AE2)第7次；VOL_PROFILE_DISTANCE(AE3/AF2/AG1)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AH4",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "dense_events_no_damage",
        "hypothesis": "两腿角色：A=量 spike 频率（事件密集度，BB1 左腿）；B=最差单日收益（极端损伤，r053 门 7 入选：+0.064/+0.065/t=2.18）。假设：事件密集而最差单日不极端（信号高）=频繁事件无损伤（信息丰富环境），延续；最差日极端（信号低）=事件是损伤。声明：VOL_SPIKE_FREQ_20(BB1 左腿/AF5/AG3)第4次；WORST_DAY_20(AE1/AF1/AG6)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AH5",
        "operator": "rank_spread",
        "left": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "close_confirm_with_acf",
        "hypothesis": "两腿角色：A=尾 5 分钟与全日方向一致性（收盘确认，F2 左腿）；B=5 日收益一阶自相关符号（短期动量确认，T5 左腿）。假设：收盘确认与短期动量同正（信号高）=日内动量获得收盘与自相关双重确认，延续。声明：CLOSE5_DAY_CONSIST_20(F2 左腿/Q4)第3次；SIGN_ACF1_5(T5 左腿/AE4/AF4)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AH6",
        "operator": "rank_spread",
        "left": {"name": "ULCER_20", "source": "downside_risk"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "healthy_structure_rhythm_ushape",
        "hypothesis": "两腿角色：A=20 日溃疡（慢性失血，BB1 右腿）；B=日内 U 形 RV 占比（配置节律，r053 门 7 入选）。假设：溃疡浅而节律存在（信号高）=健康结构中的配置节律（事件被正常定价），延续；溃疡深（信号低）=节律是失血挣扎。声明：ULCER_20(BB1 右腿/AF3)第3次；VOL_USHAPE_20(T2/S4/AE2/AF1/AG2)第5次。注意：AH6 首稿与已入选 BB1（VOL_SPIKE×ULCER）完全重复，被 plan 级哈希去重正确拦截后换腿重写。预期正方向。",
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
