#!/usr/bin/env python3
"""Round 027 driver: the final preregisterable pairings of the three-family
two-atom stage. Entering streak: 2 consecutive gate-7 zero rounds (025/026).
If this batch yields zero gate-7 admissions, the contract's exhaustion
criterion (3 consecutive) is met: MECHANISM_EXHAUSTED.json +
RETROSPECTIVE.md will be written in this directory and the 150-atom two-atom
space archived per directive 19 (conditional-operator stage is a controller
draft, activated by the controller, not self-activated here).

All six pairs are atom-level new; endpoints are heavily-used atoms, declared.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_027"

base.CANDIDATES = [
    {
        "id": "BB1",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "event_activity_vs_chronic_pain",
        "hypothesis": "异常放量频率与溃疡指标之差=下跌的性质：spike频繁而溃疡浅(信号高)=事件活跃市场无慢性失血，定价连续、延续；溃疡深(信号高区)=慢性痛中的脉冲，无出清价值。声明：SPIKE第3次、ULCER_20第3次配对(X1/E4中拒绝)，最后组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "BB2",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "MARKET_LEAD_CORR_60", "source": "cross_etf_lead_lag"},
        "mechanism": "independent_pulse_vs_market_channel",
        "hypothesis": "spike频率与市场领先耦合之差=脉冲的来源独立性：spike频繁而市场耦合低(信号高)=独立事件流的脉冲(个体信息到达)，延续；耦合高的市场联动脉冲无自身信息。声明：SPIKE第3次、MARKET_LEAD_CORR_60(T4中拒绝)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "BB3",
        "operator": "rank_spread",
        "left": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "right": {"name": "MARKET_LEAD_CORR_60", "source": "cross_etf_lead_lag"},
        "mechanism": "profit_independence_vs_market_channel",
        "hypothesis": "获利幅度与市场领先耦合之差=获利的来源独立性：获利高而市场耦合低(信号高)=独立行情的获利(个体资金/信息驱动)，延续；耦合高的获利=市场推动，随市场回归。声明：PRICE_VS_AVGCOST_20第3次(D1/U1/G2中拒绝)、MARKET_LEAD_CORR_60第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "BB4",
        "operator": "rank_spread",
        "left": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "right": {"name": "SESSION_RETURN", "source": "daily_candle"},
        "mechanism": "profit_taking_intraday_pressure",
        "hypothesis": "获利盘与当日时段收益之差=获利盘的日内压力：获利盘高而时段收益弱(信号高)=获利盘抛压主导当日，回吐；获利盘低而时段强(信号低)=建仓期、无抛压。声明：PROFIT_RATIO_60第5次(C4/E6/F4/AA3中拒绝)、SESSION_RETURN第3次(T6/Z4中拒绝)——最后组合。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "BB5",
        "operator": "rank_spread",
        "left": {"name": "COST_CENTER_SHIFT_20", "source": "cost_distribution"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "cost_chase_vs_chronic_pain",
        "hypothesis": "成本重心上移与溃疡之差=追高的健康度：成本上移快而溃疡深(信号高)=高位堆积新筹码+慢性失血，追高被套，走弱；成本上移而溃疡浅(信号低区)=健康上行的成本跟随。声明：COST_CENTER_SHIFT_20第4次(D5/D6/E5中拒绝)、ULCER_20第3次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "BB6",
        "operator": "rank_spread",
        "left": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "right": {"name": "TAIL_Q10_20", "source": "return_tail_shape"},
        "mechanism": "profit_tail_hygiene_cost_view",
        "hypothesis": "获利幅度与左尾深度之差=获利的尾部卫生（成本视角）：获利高而近期左尾浅(信号高)=干净获利、无新鲜尾部损伤，延续；获利低而左尾深(信号低)=套牢+新鲜尾部损伤，走弱。声明：PRICE_VS_AVGCOST_20第4次、TAIL_Q10_20第2次(S2中拒绝)——最后组合。预期正方向。",
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
