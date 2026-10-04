#!/usr/bin/env python3
"""Round 016 driver: five spreads from the remaining fresh/burnt-once atoms.

Batch-size note: only five non-redundant falsifiable hypotheses remain. The
other slots would re-skin burnt atoms; padding is manufacturing output.
Current contract state: rounds 012/013(+015) gate-7 zero streak = 1; a third
consecutive zero round triggers MECHANISM_EXHAUSTED per the contract.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_016"

base.CANDIDATES = [
    {
        "id": "W1",
        "operator": "rank_spread",
        "left": {"name": "MARKET_LEAD_BETA_60", "source": "cross_etf_lead_lag"},
        "right": {"name": "CURRENT_DD_60", "source": "downside_risk"},
        "mechanism": "transmission_intact_vs_broken",
        "hypothesis": "市场领先贝塔与自身回撤之差=传导通道完整性：领先传导强而回撤浅(信号高)=信息传导通道完好的市场领先品种，行情延续；回撤深(信号低)=通道断裂、领先地位已被破坏。MARKET_LEAD_BETA_60为最后未测lead-lag原子；CURRENT_DD_60(U4中仅差门7的t=1.77/4.1bp)复用。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W2",
        "operator": "rank_spread",
        "left": {"name": "ASSET_LEAD_MARKET_CORR_60", "source": "cross_etf_lead_lag"},
        "right": {"name": "CLOSE_VWAP_DEVIATION", "source": "intraday_vwap_position"},
        "mechanism": "anticipation_vs_realization_premium",
        "hypothesis": "领先市场相关与收盘溢价之差=信息的预期/兑现状态：领先相关高而溢价低(信号高)=信息源强但尚未在价格兑现，前瞻看涨；溢价高而领先弱(信号低)=无信息支撑的溢价，回吐。声明复用：CLOSE_VWAP_DEVIATION(round_015 U1/U2中两次拒绝)；配对对象与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W3",
        "operator": "rank_spread",
        "left": {"name": "SESSION_MEAN_60", "source": "daily_candle"},
        "right": {"name": "PEER_LEAD_NETWORK_CORR_60", "source": "cross_etf_lead_lag"},
        "mechanism": "drift_vs_network_consensus",
        "hypothesis": "时段漂移与网络中枢之差=上行是否依赖网络共识：漂移正而中枢低(信号高)=无网络共识的独立配置上行，延续；中枢高而漂移弱(信号低)=网络定价已完成、无新信息。声明复用：SESSION_MEAN_60(U3中仅差发现块t)、PEER_LEAD_NETWORK_CORR_60未用于组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W4",
        "operator": "rank_spread",
        "left": {"name": "PEER_LEAD_NETWORK_CORR_60", "source": "cross_etf_lead_lag"},
        "right": {"name": "CURRENT_DD_20", "source": "downside_risk"},
        "mechanism": "hub_health_gap",
        "hypothesis": "网络中枢与自身回撤之差=枢纽健康度：中枢高而回撤浅(信号高)=信息枢纽功能完好，传导溢价延续；中枢高而回撤深(信号低)=枢纽已受损、传导逻辑失效。声明复用：CURRENT_DD_20(round_002 W4双回撤差中拒绝)；配对对象与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W5",
        "operator": "rank_spread",
        "left": {"name": "VOLUME_RATIO_5_20", "source": "trading_activity"},
        "right": {"name": "GAP_MEAN_60", "source": "daily_candle"},
        "mechanism": "intraday_vs_overnight_flow",
        "hypothesis": "量比与跳空流之差=资金的作用时段：量比扩张而跳空流弱(信号高)=交易时段资金主导(可跟踪的连续行为)，延续；跳空流主导而量比弱(信号低)=隔夜事件一次性定价，无后续。声明复用：VOLUME_RATIO_5_20(U3/Y4中拒绝)、GAP_MEAN_60未用于组合(近亲GAP_MEAN_20在V6中拒绝)。预期正方向。",
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
