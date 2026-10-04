#!/usr/bin/env python3
"""Round 057 driver: stage 11 round 2 (entering streak: 1 zero round, r056).
Six NEW cross-family pairs from the 20-atom verified pool (gate-7 passers +
admitted-combination legs); all pairs atom-level new, all mechanism names
new; dedup guards against shadowing any single leg. Gate 7 v2.1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_057"

base.CANDIDATES = [
    {
        "id": "AF1",
        "operator": "rank_spread",
        "left": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "rhythm_vol_no_extreme_day",
        "hypothesis": "两腿角色：A=日内 U 形 RV 占比（开收盘波动节律，r053 入选原子）；B=最差单日收益（极端损伤，r053 入选原子）。假设：节律波动高而最差单日不极端（信号高）=波动是节律性配置活动而非损伤事件，延续。声明：VOL_USHAPE_20(AE2)第3次；WORST_DAY_20(AE1)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AF2",
        "operator": "rank_spread",
        "left": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "right": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "profile_anomaly_persistent_volume",
        "hypothesis": "两腿角色：A=量分布距离（活动轮廓异常，r053 门 7 最强原子 t=4.04）；B=量自相关（量的持续性，Z2 右腿）。假设：活动轮廓异常而量持续（信号高）=异常活动有持续性（机构而非脉冲），延续。声明：VOL_PROFILE_DISTANCE(P?/V3 首次价差后)第2次；VOL_AUTOCORR_20(Z2 右腿)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AF3",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "concentrated_execution_healthy",
        "hypothesis": "两腿角色：A=大 bar 时点集中度（机构执行节奏，r053 入选原子：−0.097/−0.046/t=2.55）；B=20 日溃疡（慢性失血）。假设：大 bar 集中而溃疡浅（信号高）=机构化执行且结构无失血，延续；溃疡深（信号低）=集中执行是出逃。声明：BIGBAR_EDGE_CONC_20(AE5)第10次；ULCER_20(BB1 右腿)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AF4",
        "operator": "rank_spread",
        "left": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "calm_category_individual_momentum",
        "hypothesis": "两腿角色：A=类别 20 日波动（环境噪声，r053 入选原子：−0.071/−0.065/t=2.42）；B=5 日收益一阶自相关符号（个体动量确认，T5 左腿）。假设：类别平静而个体收益自相关为正（信号高）=平静环境中的个体动量（自身趋势确认），延续。声明：CATEGORY_VOL_20(T4/Y3/N4/U2/AE3)第6次；SIGN_ACF1_5(T5 左腿/AE4)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AF5",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "active_events_secondary_origin",
        "hypothesis": "两腿角色：A=量 spike 频率（事件密集度，BB1 左腿）；B=份额变化-收益相关（一级流解释力）。假设：spike 频率高而一级流不解释价格（信号高）=活跃事件来自二级信息（非申赎），延续；一级解释力强（信号低）=事件是申赎冲击。声明：VOL_SPIKE_FREQ_20(BB1 左腿)第2次；SHARE_RET_CORR_20(X6/M1/K4/R5/Y3/W3 入选)第8次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AF6",
        "operator": "rank_spread",
        "left": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "open_auction_high_activity",
        "hypothesis": "两腿角色：A=开盘 30 分钟量占比（开盘配置机制，F1 右腿）；B=对数成交额（活跃水平，T5 右腿）。假设：开盘集中且整体活跃（信号高）=开盘配置机制运行良好（机构开盘建仓），延续；开盘占比低（信号低）=活跃无开盘锚点。声明：OPEN30_VOL_SHARE_20(F1 右腿)第2次；LOG_AMOUNT_VOL_20(T5 右腿/AC6)第3次。预期正方向。",
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
