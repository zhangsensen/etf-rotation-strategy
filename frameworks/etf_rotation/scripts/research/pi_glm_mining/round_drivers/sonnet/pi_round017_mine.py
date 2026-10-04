#!/usr/bin/env python3
"""Round 017 driver: the final three falsifiable pairs from burnt-once atoms.

Streak status entering this round: rounds 015/016 had zero gate-7 admissions
(= 2 consecutive). Per ETF_ROTATION_CONTRACT_14.md, a THIRD consecutive zero
gate-7 round establishes the two-atom space as unfruitful; if this batch ends
with zero gate-7 admissions, MECHANISM_EXHAUSTED.json is written alongside.
All three mechanisms below are chronic-vs-event / memory-vs-event /
drift-vs-beta contrasts that have never been expressed; endpoints are
burnt-once atoms, declared.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_017"

base.CANDIDATES = [
    {
        "id": "X1",
        "operator": "rank_spread",
        "left": {"name": "ULCER_20", "source": "downside_risk"},
        "right": {"name": "OVERNIGHT_GAP", "source": "daily_candle"},
        "mechanism": "chronic_decline_vs_event_shock",
        "hypothesis": "溃疡指标(深度加权持续回撤)与一次性隔夜冲击之差=下跌的性质：慢性阴跌而隔夜无事件(信号高)=无出清节点的持续失血，继续走弱；溃疡浅而隔夜冲击大(信号低)=事件冲击型下跌，事件出清后修复。声明：ULCER_20与REALIZED_VOL_60shelf存在高相关风险，若过门预计撞冗余墙——仍为诚实证伪尝试。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "X2",
        "operator": "rank_spread",
        "left": {"name": "RET_ACF2_20", "source": "serial_dependence"},
        "right": {"name": "OVERNIGHT_GAP", "source": "daily_candle"},
        "mechanism": "memory_vs_overnight_events",
        "hypothesis": "二阶动量记忆与隔夜事件流之差=动量的可持续来源：记忆强而隔夜事件平静(信号高)=动量来自交易时段持续资金、可自我维持，延续；隔夜事件主导(信号低)=动量靠一次性隔夜定价、不可持续。声明：RET_ACF2_20(OVER... P4用RET_ACF2_60)、OVERNIGHT_GAP(T1中拒绝)均为单次烧毁原子。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X3",
        "operator": "rank_spread",
        "left": {"name": "SESSION_MEAN_60", "source": "daily_candle"},
        "right": {"name": "MARKET_BETA_60", "source": "market_sensitivity"},
        "mechanism": "drift_vs_market_beta_exhaustion",
        "hypothesis": "时段漂移与市场贝塔之差=上行的贝塔透支度：漂移正而贝塔低(信号高)=低贝塔的独立上行(配置盘驱动)，延续；漂移正而贝塔极高(信号低)=透支市场弹性的贝塔行情，市场回撤时放大下行。声明：SESSION_MEAN_60(U3中仅差发现块t)、MARKET_BETA_60(其20窗兄弟为shelf，60窗有冗余墙风险)。预期正方向。",
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
