#!/usr/bin/env python3
"""Round 039 driver: stage-7 round 2 (entering streak: 1 zero round, r038).
Deploys the three still-unused realized-measure legs (BPV_RV_RATIO_20,
RKURT_20, VOL_USHAPE_20) plus second uses with fresh partners. Six
rank_spread pairs, all atom-level new, all mechanism names new. Gate 7 v2.1;
all atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_039"

base.CANDIDATES = [
    {
        "id": "T1",
        "operator": "rank_spread",
        "left": {"name": "BPV_RV_RATIO_20", "source": "realized_measures_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "continuous_buy_pressure",
        "hypothesis": "两腿角色：A=BPV/RV（Barndorff-Nielsen & Shephard 2004，比值高=连续扩散波动、无跳跃）；B=1m tick-rule 主买不平衡。假设：连续波动主导而主买不平衡高（信号高）=定向买流以平滑方式推动（无跳跃噪声），延续；跳跃主导（信号低）=买流靠事件冲击，不可持续。声明：BPV_RV_RATIO_20 首次价差腿；TICK_IMBALANCE_20(F1 左腿)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "T2",
        "operator": "rank_spread",
        "left": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "right": {"name": "STREAK_DAYS", "source": "fund_flow"},
        "mechanism": "ushape_absorbed_inflow",
        "hypothesis": "两腿角色：A=日内 U 形 RV 占比（开/收盘段波动集中=流动性节律而非随机噪声）；B=连续净申购天数（一级承接方向）。假设：U 形占比高且连续净申购（信号高）=开收盘波动被一级承接吸收（健康节律），延续；无承接（信号低）=节律波动失血。声明：VOL_USHAPE_20 首次价差腿；STREAK_DAYS(T5/N3/K3)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "T3",
        "operator": "rank_spread",
        "left": {"name": "RKURT_20", "source": "realized_measures_1m"},
        "right": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "mechanism": "fat_tails_unconfirmed_close",
        "hypothesis": "两腿角色：A=已实现峰度（Amaya–Christoffersen–Jacobs–Vasquez 2015，日内厚尾）；B=尾 5 分钟与全日方向一致性（收盘确认）。假设：峰度高而收盘确认低（信号高）=日内极端事件未被收盘确认（噪声尾），极端不延续，反转走弱；收盘确认高（信号低）=极端被定价确认。声明：RKURT_20 首次价差腿；CLOSE5_DAY_CONSIST_20(F2 左腿)第2次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "T4",
        "operator": "rank_spread",
        "left": {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "rhythmic_concentrated_chips",
        "hypothesis": "两腿角色：A=同时段收益持续性（Heston–Korajczyk–Sadka 2010，日内节奏记忆）；B=90% 筹码区间宽度（筹码集中度）。假设：节奏持续而筹码区间窄（信号高）=筹码集中+执行节奏稳定=机构控盘结构，延续；筹码发散（信号低）=节奏被分散持有者噪声打断。声明：HKS_SLOT_PERSIST_20(R4)第2次；CHIP_RANGE_90_60(C3 左腿)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "T5",
        "operator": "rank_spread",
        "left": {"name": "TAIL30_BETA_FULL_20", "source": "intraday_periodicity"},
        "right": {"name": "ULCER_60", "source": "downside_risk"},
        "mechanism": "close_leadership_healthy",
        "hypothesis": "两腿角色：A=尾 30 分钟收益对全日收益的 20 日回归 β（收盘段定调力）；B=60 日溃疡（慢性失血）。假设：收盘定调强而溃疡浅（信号高）=健康结构的收盘动量（次日被定价），延续；溃疡深（信号低）=定调是失血中的脉冲，不可信。声明：TAIL30_BETA_FULL_20(R5)第2次；ULCER_60(Y1/Z4/K6)第3次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "T6",
        "operator": "rank_spread",
        "left": {"name": "BPV_RV_RATIO_20", "source": "realized_measures_1m"},
        "right": {"name": "PREMIUM_Z_20", "source": "nav_premium"},
        "mechanism": "smooth_regime_no_overhang",
        "hypothesis": "两腿角色：A=BPV/RV（连续波动占比）；B=折溢价 20 日 z（情绪透支）。假设：连续波动主导而溢价 z 低（信号高）=平滑无跳跃的环境且无情绪透支，风险定价合理，延续；溢价 z 高（信号低）=情绪透支叠加跳跃风险。声明：BPV_RV_RATIO_20 第2次（T1 为另一构造）；PREMIUM_Z_20(N5/K2)第3次。预期负方向。",
        "expected_sign": -1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_realized(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage7_realized_measures_periodicity"
    plan["pit_note"] = (
        "已实现测度/周期性原子只用 <=D 的完整交易日 1m bar；LM 跳跃 sigma 只用前一日 bar；"
        "泄漏门物理截断/扰动副本含基准文件；全部原子泄漏缓存命中"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_realized

if __name__ == "__main__":
    base.main()
