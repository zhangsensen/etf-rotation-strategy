#!/usr/bin/env python3
"""Round 018 driver: line reopened with three locally derived families
(cost_distribution from 1d panels; bar_size_order_flow and
intraday_volume_profile_1m from 1m bars -- first 1m use in this line).

All six candidates contain at least one new-family atom (three new x new,
three new x old). New-atom health check (single-atom IC + shelf rank corr):
outputs/round_018/atom_health.csv -- zero shadow atoms (max |corr| 0.61).
Gate 7 v2.1 applies; leak hard gates cover the 1m frequency via physical
truncation/perturbation copies.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_018"

base.CANDIDATES = [
    {
        "id": "C1",
        "operator": "rank_spread",
        "left": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "orderly_accumulation_flow_profile",
        "hypothesis": "1m主动买卖不平衡与异常放量频率之差=吸筹的秩序：主买净流入强而异常spike稀少(信号高)=持续有序吸筹、无事件驱动，延续；主买弱而spike频繁(信号低)=事件驱动出货/恐慌，回归。新x新组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "C2",
        "operator": "rank_spread",
        "left": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "mechanism": "volume_order_vs_pulse_execution",
        "hypothesis": "量自相关与大bar边缘集中之差=参与的执行形态：量连续有序而大bar不集中于开盘/收盘(信号高)=全天均匀参与的机构配置盘，延续；量无序且边缘脉冲集中(信号低)=脉冲式执行/收盘抢筹，回归。新x新组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "C3",
        "operator": "rank_spread",
        "left": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "chip_dispersion_organic_execution",
        "hypothesis": "筹码分散度与大bar量占比之差=筹码转移的有机性：筹码分散而大bar少(信号高)=筹码经分散换手自然转移(无集中执行痕迹)，健康延续；筹码集中且大bar主导(信号低)=集中执行/单一资金主导，脆弱回归。新x新组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "C4",
        "operator": "rank_spread",
        "left": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "right": {"name": "RET_120", "source": "directional_trend"},
        "mechanism": "profit_crowding_vs_long_trend",
        "hypothesis": "获利盘比例与长期动量之差=获利拥挤度：获利盘高而长期动量弱(信号高)=老趋势末端的全员获利拥挤，抛压回归；获利低而动量强(信号低)=套牢解放初期、上行动能未耗尽。声明复用：RET_120(E2交互中拒绝)；构造类与机制不同。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "C5",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "right": {"name": "DOWNSIDE_BETA_60", "source": "market_sensitivity"},
        "mechanism": "informed_bigbar_vs_downside_beta",
        "hypothesis": "大bar方向偏度与下行贝塔之差=大资金的逆风信息含量：大bar买方向而下行敏感低(信号高)=逆市场下跌的知情大单买入，强延续；大bar卖方向且高下行敏感(信号低)=恐慌出货随市场。声明复用：DOWNSIDE_BETA_60(U1/U4中拒绝)；构造类与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "C6",
        "operator": "rank_spread",
        "left": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "AMIHUD_60", "source": "price_volume_coupling"},
        "mechanism": "uniform_volume_liquidity_premium",
        "hypothesis": "量分布熵与冲击成本之差=可执行环境：量分布均匀(高熵)而冲击成本低(信号高)=深度充足的均匀参与环境，机构可有序执行、行情健康，延续；量脉冲集中且高成本(信号低)=薄簿冲击、脆弱。声明复用：AMIHUD_60(Z1/Y5中拒绝)；构造类与机制不同。预期正方向。",
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
