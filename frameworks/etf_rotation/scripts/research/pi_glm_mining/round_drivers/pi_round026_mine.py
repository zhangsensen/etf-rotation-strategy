#!/usr/bin/env python3
"""Round 026 driver: five spreads -- the last untested new-family pairings.

Batch size 5 (not 6): the remaining slots have no distinct falsifiable
mechanism, only re-skins of tested failures. All pairs atom-level new; heavy
per-atom burn counts declared per hypothesis. Gate 7 v2.1; streak entering: 1
zero round (round_025).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_026"

base.CANDIDATES = [
    {
        "id": "AA1",
        "operator": "rank_spread",
        "left": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "mechanism": "uniform_flow_free_float",
        "hypothesis": "量熵与套牢厚度之差=流通结构的健康度：量分布均匀(参与分散)而上方套牢薄(信号高)=自由流通、无历史套牢结构的干净筹码，延续；量脉冲集中且套牢厚(信号低)=脉冲在阻力下空转，回归。声明：两原子分别已4次/3次配对拒绝；本配对全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AA2",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "mechanism": "scheduled_execution_clean_structure",
        "hypothesis": "大bar边缘集中与套牢厚度之差=执行环境与结构的匹配：执行定时集中于开盘/收盘而套牢薄(信号高)=机构规则执行+干净流通结构，定价高效，延续；套牢厚(信号高区)=历史阻力消耗执行，走弱。声明：BIGBAR_EDGE_CONC_20已3次配对、OVERHAND_THICKNESS_60已3次；本配对全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AA3",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "scheduled_accumulation_low_profit",
        "hypothesis": "定时执行与获利盘之差=建仓的位置属性：执行定时集中于开盘/收盘而获利盘低(信号高)=机构在低位规则性建仓(信息先行)，强延续；获利盘高而定时执行(信号高区)=高位规则兑现。信号低区(低执行+高获利)为拥挤顶部。声明：两原子分别已3次配对；本配对全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AA4",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "event_volume_low_profit",
        "hypothesis": "异常放量频率与获利盘之差=事件放量的位置属性：spike频繁而获利盘低(信号高)=低位事件放量(事件驱动建仓)，修复延续；获利盘高而spike频繁(信号高区)=高位事件兑现。信号低区(低频+低获利)为死市场。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AA5",
        "operator": "rank_spread",
        "left": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "CURRENT_DD_20", "source": "downside_risk"},
        "mechanism": "uniform_flow_current_health",
        "hypothesis": "量熵与当前回撤之差=参与均匀度与结构健康的匹配：量分布均匀而当前回撤浅(信号高)=均匀参与+结构无损伤，健康延续；熵低而回撤深(信号低)=脉冲参与+结构受损，走弱。声明：VOL_ENTROPY_20已4次配对、CURRENT_DD_20已2次配对(W4/Z4-016)——原AA5(PRICE_VS_AVGCOST_20 x ULCER_20)与round_025 G2同对被去重网拦截后换入的本配对为全新原子对。预期正方向。",
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
