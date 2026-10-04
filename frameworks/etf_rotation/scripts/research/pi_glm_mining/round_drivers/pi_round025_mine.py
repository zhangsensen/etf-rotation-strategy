#!/usr/bin/env python3
"""Round 025 driver: six candidates picked from controller/untested_pairs.csv
(has_new_family_leg=True, tested=False), each with a fresh falsifiable
mechanism. All new-family atoms were health-checked in round_018
(outputs/round_018/atom_health.csv, zero shadow) and their burn counts are
declared per hypothesis. Gate 7 v2.1; atom/leak caches active.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_025"

base.CANDIDATES = [
    {
        "id": "G1",
        "operator": "rank_spread",
        "left": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "MARKET_LEAD_BETA_60", "source": "cross_etf_lead_lag"},
        "mechanism": "uniform_participation_vs_market_channel",
        "hypothesis": "量熵与市场领先贝塔之差=参与的来源渠道：量分布均匀(参与分散)而领先市场传导低(信号高)=非市场渠道的独立配置资金，延续；领先传导强而量脉冲集中(信号低)=贝塔渠道的脉冲行情，随市场回归。声明：VOL_ENTROPY_20已4次配对(C6/D1/E2/E4均拒绝)，首次配lead-lag族。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "G2",
        "operator": "rank_spread",
        "left": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "profit_hygiene_vs_chronic_pain",
        "hypothesis": "获利幅度与溃疡指标之差=获利结构的卫生：价格高于成本而自身无痛(信号高)=获利干净、无慢性失血抵消，延续；价格低于成本且溃疡深(信号低)=套牢叠加慢性失血，走弱。声明：PRICE_VS_AVGCOST_20已2次配对(D1/U1)；ULCER_20(X1中拒绝)有波动shelf冗余墙风险——过门预计撞墙，仍为诚实证伪。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "G3",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "CURRENT_DD_60", "source": "downside_risk"},
        "mechanism": "scheduled_execution_in_healthy_market",
        "hypothesis": "大bar边缘集中与自身回撤之差=执行环境健康度：执行定时(开盘/收盘)而回撤浅(信号高)=健康市场中的机构规则执行，延续；执行无定时且回撤深(信号低)=受损市场的无序交易。声明：BIGBAR_EDGE_CONC_20已3次配对(C2/F5/Z1)、CURRENT_DD_60(U4中仅差门7的t=1.77、W1)均拒绝；本配对全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "G4",
        "operator": "rank_spread",
        "left": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "right": {"name": "OVERNIGHT_GAP", "source": "daily_candle"},
        "mechanism": "profit_overnight_transparency",
        "hypothesis": "获利盘与隔夜跳空之差=获利的透明度：获利盘高而隔夜跳空仍为正(信号高)=隔夜渠道继续推高获利，透支回归；获利盘低而隔夜负跳空(信号低)=出清提供入场结构，修复。声明：PROFIT_RATIO_60已3次配对(C4/E6/F4)、OVERNIGHT_GAP(T1中拒绝)均为单次/多次烧毁原子，最后组合。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "G5",
        "operator": "rank_spread",
        "left": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "ASSET_LEAD_MARKET_CORR_60", "source": "cross_etf_lead_lag"},
        "mechanism": "close_activity_vs_market_channel",
        "hypothesis": "尾盘量占比与领先市场相关之差=尾盘行为的渠道：尾量集中而市场传导低(信号高)=收盘定价由个体信息驱动，延续；尾量随市场传导放大(信号低)=市场尾盘行为的贝塔镜像。声明：CLOSE30_VOL_SHARE_20已3次配对(D6/V2/V3)、ASSET_LEAD_MARKET_CORR_60(W2/Z3/Z5中拒绝)；本配对全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "G6",
        "operator": "rank_spread",
        "left": {"name": "COST_CENTER_SHIFT_20", "source": "cost_distribution"},
        "right": {"name": "PEER_LEAD_CORR_20", "source": "cross_etf_lead_lag"},
        "mechanism": "cost_relocation_independence",
        "hypothesis": "成本重心位移与组内耦合之差=成本抬升的独立性：成本上移快而组内耦合低(信号高)=独立于同类资金流的自身成本抬升(个体信息驱动)，延续；耦合高(信号低)=组内贝塔共同抬升，随板块。声明：COST_CENTER_SHIFT_20已3次配对(D5/D6/E5)、PEER_LEAD_CORR_20(S4中拒绝)；本配对全新。预期正方向。",
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
