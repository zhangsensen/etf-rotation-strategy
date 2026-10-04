#!/usr/bin/env python3
"""Round 015 driver: the last fresh-atom batch -- FOUR spreads.

After 14 rounds / 70 expressions, only four untested atoms with honest
mechanisms remain (CLOSE_VWAP_DEVIATION, RET_ACF1_60, SESSION_MEAN_60,
DOWNSIDE_BETA_60, RETURN_SKEW_20, CURRENT_DD_60). The batch size is 4, not 6+
-- the remaining slots have no non-redundant falsifiable hypotheses; padding
would be manufacturing output. All endpoints non-shelf, reused atoms declared.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_015"

base.CANDIDATES = [
    {
        "id": "U1",
        "operator": "rank_spread",
        "left": {"name": "CLOSE_VWAP_DEVIATION", "source": "intraday_vwap_position"},
        "right": {"name": "DOWNSIDE_BETA_60", "source": "market_sensitivity"},
        "mechanism": "independent_close_bid_vs_downside_beta",
        "hypothesis": "收盘溢价与下行贝塔之差=收盘买盘的独立性：溢价高而下行贝塔低(信号高)=独立于市场下行敏感的自身买盘(配置/事件驱动)，延续；溢价低而贝塔高(信号低)=随市场阴跌、无自身买盘。声明相邻性：N6入选为资金压力x市场耦合的独立溢价；此处是收盘溢价x下行贝塔，同主题不同量纲。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U2",
        "operator": "rank_spread",
        "left": {"name": "RET_ACF1_60", "source": "serial_dependence"},
        "right": {"name": "CLOSE_VWAP_DEVIATION", "source": "intraday_vwap_position"},
        "mechanism": "memory_unjustified_close_premium",
        "hypothesis": "动量记忆与收盘溢价之差=溢价的动量背书：记忆强而溢价低(信号高)=趋势由持续资金推动、收盘无抢筹，延续；记忆弱而溢价高(信号低)=无趋势背书的收盘拉抬，回吐。与U1同用CLOSE_VWAP_DEVIATION但方向假设相反，构成对溢价含义的双向检验。声明：serial_dependence族多处拒绝(仅T5左端入选)，RET_ACF1_60为该族最后未测原子。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U3",
        "operator": "rank_spread",
        "left": {"name": "SESSION_MEAN_60", "source": "daily_candle"},
        "right": {"name": "RETURN_SKEW_20", "source": "return_tail_shape"},
        "mechanism": "drift_skew_compensation",
        "hypothesis": "时段漂移与偏度之差=漂移的尾部补偿：漂移正而偏度负(信号高)=日内持续买盘在承担左尾风险，补偿不足、回吐；漂移弱而偏度正(信号低)=平静右偏、上行尾部未被发现，看涨。声明复用：SESSION_MEAN_60属W5家族(其20窗版本v2降级)——本假设是漂移x偏度补偿，非漂移对全日动量的拆分；RETURN_SKEW_20(P2中identity单项拒绝)。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "U4",
        "operator": "rank_spread",
        "left": {"name": "CURRENT_DD_60", "source": "downside_risk"},
        "right": {"name": "DOWNSIDE_BETA_60", "source": "market_sensitivity"},
        "mechanism": "drawdown_beta_hygiene",
        "hypothesis": "自身回撤与下行贝塔之差=回撤的系统性归因：回撤浅而下行贝塔高(信号高)=高敏感未兑现(市场未跌够)、悬顶风险，走弱；回撤深而贝塔低(信号低)=特质深跌、无系统暴露，修复。声明复用：CURRENT_DD_60未用于任何组合；W4用CURRENT_DD_20(双回撤差,弱拒绝)。预期负方向。",
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
