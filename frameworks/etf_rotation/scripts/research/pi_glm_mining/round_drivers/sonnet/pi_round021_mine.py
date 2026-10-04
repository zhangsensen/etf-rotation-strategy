#!/usr/bin/env python3
"""Round 021 driver: the final five untested new-family pairings.

Streak entering: rounds 019/020 = 2 consecutive gate-7 zero rounds. If this
batch is also zero, the contract's 3-consecutive criterion is met and
MECHANISM_EXHAUSTED.json (+ RETROSPECTIVE.md per directive 18) will be written.
All five are new atom-pairs with declared burnt-once reuses.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_021"

base.CANDIDATES = [
    {
        "id": "F1",
        "operator": "rank_spread",
        "left": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "continuous_flow_vs_open_pulse",
        "hypothesis": "主买不平衡与早盘集中度之差=买盘的时间形态：主买强而参与分散全天(信号高)=全天持续买盘(非开盘脉冲)，健康延续；主买弱而开盘集中(信号低)=开盘脉冲后无接力，回归。声明复用：TICK_IMBALANCE_20(C1/D2中拒绝)、OPEN30_VOL_SHARE_20(D4中拒绝)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "F2",
        "operator": "rank_spread",
        "left": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "closing_confirmation_low_base",
        "hypothesis": "尾盘贯彻度与价格位置之差=趋势确认的仓位背景：贯彻强而位置低(信号高)=低位趋势贯彻到收盘(启动确认)，延续；位置高而贯彻弱(信号低)=高位犹豫、日内反复。声明复用：PRICE_POSITION_20(S4中拒绝)；CLOSE5_DAY_CONSIST_20(E2中拒绝)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "F3",
        "operator": "rank_spread",
        "left": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "right": {"name": "SESSION_RETURN", "source": "daily_candle"},
        "mechanism": "overhang_pain_intraday",
        "hypothesis": "套牢厚度与当日时段收益之差=阻力下的日内压力：套牢厚而时段走弱(信号低)=阴跌+上方阻力的双重压力，继续走弱；套牢厚而时段强(信号高)=逆阻力的解放买盘，强延续。声明复用：OVERHAND_THICKNESS_60(D2/D3中拒绝)、SESSION_RETURN(T6中审计归零拒绝)。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "F4",
        "operator": "rank_spread",
        "left": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "right": {"name": "TAIL_Q10_20", "source": "return_tail_shape"},
        "mechanism": "profit_tail_hygiene",
        "hypothesis": "获利盘与左尾深度之差=强势的尾部卫生：获利高而近期左尾浅(信号高)=强势且无近期尾部破坏，延续；获利低而左尾深(信号低)=套牢叠加新鲜尾部损伤，走弱。声明复用：PROFIT_RATIO_60(C4/E6中拒绝)、TAIL_Q10_20(S2中拒绝)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "F5",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "mechanism": "random_pulse_vs_scheduled_execution",
        "hypothesis": "spike频率与大bar边缘集中之差=参与的执行主体：盘中随机脉冲多而边缘定时执行少(信号高)=散户/随机参与主导，噪音回归；边缘定时执行为主(信号低)=机构规则单主导、定价有序。声明复用：VOL_SPIKE_FREQ_20(C1/E1中拒绝)、BIGBAR_EDGE_CONC_20(C2中仅差门7的t=1.40)。预期负方向。",
        "expected_sign": -1,
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
