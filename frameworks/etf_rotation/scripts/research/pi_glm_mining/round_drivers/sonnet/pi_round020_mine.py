#!/usr/bin/env python3
"""Round 020 driver: six spreads, each with >=1 new-family atom, all pairs
atom-level new. After 19 rounds every new-family atom has been paired once;
this batch combines them with each other or with once/burnt old partners
(all reuse declared). Structural themes: participation hygiene vs chronic
stress, organic vs pulsed execution, cost relocation confirmation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_020"

base.CANDIDATES = [
    {
        "id": "E1",
        "operator": "rank_spread",
        "left": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "overhang_vs_event_participation",
        "hypothesis": "上方套牢厚度与异常放量频率之差=结构脆弱度：套牢厚而spike稀少(信号高)=慢性阻力+无事件承接的阴跌结构，走弱；套牢薄而spike活跃(信号低)=事件驱动但结构干净的活跃市场，修复。声明复用：两原子分别于D2/D3与C1中拒绝；配对与机制不同。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "E2",
        "operator": "rank_spread",
        "left": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "trend_breadth_vs_pulse",
        "hypothesis": "尾5方向一致性与量熵之差=趋势的参与广度：一致性高而量熵高(信号高)=趋势由广泛分散的参与贯彻到收盘，健康延续；一致性弱而熵低(信号低)=单一资金脉冲主导的日内，回归。CLOSE5_DAY_CONSIST_20为最后未配对的新家族原子。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "E3",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "RET_ACF2_20", "source": "serial_dependence"},
        "mechanism": "organic_momentum_vs_bigbar_pulse",
        "hypothesis": "大bar量占比与二阶动量记忆之差=动量的执行来源：大bar少而记忆强(信号高)=分散换手维持的有机动量，健康延续；大bar主导而记忆弱(信号低)=大单脉冲强行推动、无持续接力。声明复用：RET_ACF2_20(X2中拒绝)；BIGBAR_VOL_SHARE_20(C3入选候选左端，此处为右端、机制不同)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "E4",
        "operator": "rank_spread",
        "left": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "entropy_vs_chronic_ulcer",
        "hypothesis": "量熵与溃疡指标之差=参与的卫生状态：熵高而溃疡低(信号高)=均匀参与且无慢性失血，健康上行延续；熵低而溃疡深(信号低)=脉冲出清式慢性下跌，脆弱。声明：ULCER_20与波动shelf存在冗余墙风险（若过门预计撞墙）；VOL_ENTROPY_20(C6/D1中拒绝)复用。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "E5",
        "operator": "rank_spread",
        "left": {"name": "COST_CENTER_SHIFT_20", "source": "cost_distribution"},
        "right": {"name": "RET_60", "source": "directional_trend"},
        "mechanism": "cost_relocation_trend_confirmation",
        "hypothesis": "成本重心位移与中期动量之差=成本抬升的趋势确认：成本上移而动量强(信号高)=新筹码在更高价位形成且趋势确认，延续；成本上移而动量弱(信号低)=高位堆积无趋势支撑，派发回归。声明复用：RET_60(Y1/D4中拒绝)；COST_CENTER_SHIFT_20(D5/D6中拒绝)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "E6",
        "operator": "rank_spread",
        "left": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "close_accumulation_vs_profit_taking",
        "hypothesis": "尾盘量占比与获利盘之差=收盘行为的性质：尾量集中而获利盘低(信号高)=低位尾盘吸筹(知情资金低位建仓)，修复延续；获利盘高而尾量集中(信号低)=高位尾盘兑现，回吐。声明复用：CLOSE30_VOL_SHARE_20(D6中拒绝)、PROFIT_RATIO_60(C4中拒绝)。预期正方向。",
        "expected_sign": 1,
    },
]

_orig_assert = base._assert_not_window_variant


def _assert_not_window_variant_all(draft, _prior_plan=None) -> None:
    """Check atom-pair and mechanism-name novelty against ALL prior round plans."""
    for plan_path in base._previous_round_plans():
        _orig_assert(draft, json.loads(plan_path.read_text()))


base._assert_not_window_variant = _assert_not_window_variant_all


if __name__ == "__main__":
    base.main()
