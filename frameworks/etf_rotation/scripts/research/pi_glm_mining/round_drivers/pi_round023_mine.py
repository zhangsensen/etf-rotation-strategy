#!/usr/bin/env python3
"""Round 023 driver: the last three untested new-family pairings with any
falsifiable mechanism story.

Streak entering: 0 (round_018 C3 interrupted). Batch size 3, not 6: every
other remaining pairing would be burnt-atom re-skins without a distinct
mechanism -- padding is manufacturing output. If this round is zero at gate 7
the streak reaches 1; the contract's exhaustion bar (3 consecutive) remains
the governing rule.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_023"

base.CANDIDATES = [
    {
        "id": "V1",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "CURRENT_DD_60", "source": "downside_risk"},
        "mechanism": "active_intact_market",
        "hypothesis": "异常放量频率与自身回撤之差=市场活跃与结构健康的匹配：spike频繁而回撤浅(信号高)=事件活跃且结构无损伤的市场，参与者充分博弈、定价连续，延续；spike少而回撤深(信号低)=死市场阴跌，无博弈价值。声明复用：VOL_SPIKE_FREQ_20(C1/E1中仅差门7)、CURRENT_DD_60(U4中仅差门7的t=1.77、W1中拒绝)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "V2",
        "operator": "rank_spread",
        "left": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "MARKET_LEAD_BETA_60", "source": "cross_etf_lead_lag"},
        "mechanism": "close_activity_independence",
        "hypothesis": "尾盘量占比与市场领先贝塔之差=收盘活动的独立性：尾量集中而市场领先贝塔低(信号高)=收盘定价由个体信息驱动(非市场传导)，信息延续；尾量随市场贝塔放大(信号低)=市场尾盘行为的贝塔镜像，无自身信息。声明复用：CLOSE30_VOL_SHARE_20(D6中拒绝)、MARKET_LEAD_BETA_60(W1中拒绝)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "V3",
        "operator": "rank_spread",
        "left": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "SESSION_RETURN", "source": "daily_candle"},
        "mechanism": "close_marking_vs_health",
        "hypothesis": "尾盘量占比与时段收益之差=收盘行为的性质：尾量集中而时段收益弱(信号高)=尾盘拉抬弥补日内疲弱(标记行为)，回吐；时段强而尾量集中(信号低)=强势收尾的健康确认，延续。声明复用：CLOSE30_VOL_SHARE_20同V2、SESSION_RETURN(T6中审计归零拒绝)。预期负方向。",
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
