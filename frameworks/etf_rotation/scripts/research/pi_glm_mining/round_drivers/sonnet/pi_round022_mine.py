#!/usr/bin/env python3
"""Round 022 driver: five spreads from remaining low-burn pairings.

All contain >=1 new-family atom; partners are once-used old atoms (declared).
This is likely the last batch with honest non-variant hypotheses; the next
rounds will need either new infrastructure or MECHANISM_EXHAUSTED.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_022"

base.CANDIDATES = [
    {
        "id": "Z1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "open_execution_vs_close_marking",
        "hypothesis": "大bar边缘集中与尾量占比之差=执行时点的定价含义：大bar集中于开盘/收盘两端而尾量占比低(信号高)=开盘定价型机构参与(信息执行)，当日信息定价充分，延续；尾量占比高而边缘集中低(信号低)=收盘标记式放量，回归。两原子各一次烧毁(C2/D6)，均声明。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z2",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "discrete_event_vs_machine_flow",
        "hypothesis": "大bar方向与量自相关之差=大bar的信息含量判定：大bar方向明确而量连续性差(信号高)=离散信息事件驱动的知情大单，延续；量高度机器式连续而大bar方向混沌(信号低)=无信息的流量噪音。声明复用：BIGBAR_DIR_SKEW_20(C5/D5中拒绝)、VOL_AUTOCORR_20(C2中仅差门7的t=1.40)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z3",
        "operator": "rank_spread",
        "left": {"name": "ASSET_LEAD_MARKET_CORR_60", "source": "cross_etf_lead_lag"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "leadership_premium_vs_chronic_pain",
        "hypothesis": "领先市场相关与溃疡指标之差=领先地位的健康度：领先相关高而自身无痛(信号高)=市场信息源且结构健康，领先溢价延续；溃疡深(信号低)=自身慢性受损、领先地位失效。声明：ULCER_20与波动shelf有冗余墙风险（过门预计撞墙）；ASSET_LEAD_MARKET_CORR_60(W2中拒绝)复用。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z4",
        "operator": "rank_spread",
        "left": {"name": "PEER_LEAD_NETWORK_CORR_60", "source": "cross_etf_lead_lag"},
        "right": {"name": "SESSION_RETURN", "source": "daily_candle"},
        "mechanism": "hub_pullback_repair",
        "hypothesis": "网络中枢与当日时段收益之差=枢纽的回调性质：中枢高而时段走弱(信号低)=枢纽品种的非自身性回调(组内资金暂离)，修复延续；中枢高且时段强(信号高)=枢纽领涨，同样延续。两形态皆映射正未来，预期正方向。声明复用：PEER_LEAD_NETWORK_CORR_60(W3/W4中拒绝)、SESSION_RETURN(T6中拒绝)。",
        "expected_sign": 1,
    },
    {
        "id": "Z5",
        "operator": "rank_spread",
        "left": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "ASSET_LEAD_MARKET_CORR_60", "source": "cross_etf_lead_lag"},
        "mechanism": "endogenous_order_vs_exogenous_coupling",
        "hypothesis": "量自相关与领先市场相关之差=参与的来源：量节奏内生有序而市场耦合低(信号高)=自身节奏驱动的配置行情，延续；领先耦合强而量乱(信号低)=外生传导的被动跟随。声明复用：VOL_AUTOCORR_20(C2中仅差门7的t=1.40)、ASSET_LEAD_MARKET_CORR_60(W2中拒绝)。预期正方向。",
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
