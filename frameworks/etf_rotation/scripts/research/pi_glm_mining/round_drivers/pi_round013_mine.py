#!/usr/bin/env python3
"""Round 013 driver: mechanism family "independence & compensation hygiene".

Six spreads, all endpoints non-shelf, all pairs new, reused atoms declared.
Applied lessons: spread class; avoid shelf-parent endpoints; no variants of
admitted N6 (or demoted W1/W5/Z5/Y3); audit persistence (v2.1 gate: audit
excess >= 5 bp) is the binding constraint -- every hypothesis here is about a
structural, persistent premium rather than a one-regime effect.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_013"

base.CANDIDATES = [
    {
        "id": "S1",
        "operator": "rank_spread",
        "left": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "right": {"name": "PEER_LEAD_CORR_20", "source": "cross_etf_lead_lag"},
        "mechanism": "independence_vs_peer_coupling_position",
        "hypothesis": "价格位置与组内耦合之差=强度的独立性：位置强而组内耦合低(信号高)=独立于同类资金流的alpha行情，延续；位置靠组内联动维持(信号低)=无自身信息、随组回落。两原子均未用于任何组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "S2",
        "operator": "rank_spread",
        "left": {"name": "AMOUNT_Z_60", "source": "trading_activity"},
        "right": {"name": "TAIL_Q10_20", "source": "return_tail_shape"},
        "mechanism": "attention_tail_hygiene",
        "hypothesis": "活跃度与左尾深度之差=关注度的尾部卫生：高关注而无深左尾(信号高)=注意力已透支且尾部风险未暴露，回归；低关注而有深左尾(信号低)=无人问津的受伤品种、出清后修复。声明复用：AMOUNT_Z_60(E1交互中拒绝的是AMOUNT_Z_20)。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "S3",
        "operator": "rank_spread",
        "left": {"name": "UPSIDE_BETA_60", "source": "market_sensitivity"},
        "right": {"name": "FIRST_HOUR_VWAP_DEVIATION", "source": "intraday_vwap_position"},
        "mechanism": "convexity_morning_hygiene",
        "hypothesis": "上行弹性与早盘溢价之差=凸性的开盘卫生：上行弹性高而早盘溢价低(信号高)=上行期权未被开盘情绪透支，上涨日有超额弹性，看涨；早盘溢价高而弹性低(信号低)=情绪开盘、无弹性支撑，回吐。声明复用：FIRST_HOUR_VWAP_DEVIATION(Q5中拒绝)；配对对象与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "S4",
        "operator": "rank_spread",
        "left": {"name": "MORNING_VWAP_DEVIATION", "source": "intraday_vwap_position"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "uncompensated_tail_premium",
        "hypothesis": "早盘溢价与左尾深度之差=溢价对尾部的补偿：早盘溢价高而近期左尾深(信号高)=平静假象下尾部风险未获补偿，回吐；溢价低而尾部浅(信号低)=谨慎定价、无透支。声明复用：WORST_DAY_20(Z6 spread中因与波动shelf冗余拒绝；此处配对对象是早盘溢价而非波幅，机制为补偿结构)。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "S5",
        "operator": "rank_spread",
        "left": {"name": "PEER_LEAD_BETA_60", "source": "cross_etf_lead_lag"},
        "right": {"name": "AMOUNT_RATIO_5_20", "source": "trading_activity"},
        "mechanism": "unnoticed_peer_sensitivity",
        "hypothesis": "组内敏感与量比之差=被发现程度：组内敏感高而量比低(信号高)=未被市场发现的同类信息传导通道，信息补定价、延续；量比高而敏感低(信号低)=无差别高关注、无传导优势。声明复用：AMOUNT_RATIO_5_20(U3交互中拒绝)；构造类与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "S6",
        "operator": "rank_spread",
        "left": {"name": "LAST_HOUR_TURNOVER_SHARE", "source": "intraday_turnover_shape"},
        "right": {"name": "CATEGORY_MOM_60", "source": "category_state"},
        "mechanism": "closing_participation_against_category_wind",
        "hypothesis": "尾盘参与与类别风向之差=逆风承接：尾盘换手占比高而类别中期动量弱(信号高)=逆风向的知情尾盘承接(个体信息逆板块到达)，延续；类别顺风而无尾盘接力(信号低)=贝塔行情无自身信息。声明复用：LAST_HOUR_TURNOVER_SHARE(R1交互中拒绝)、CATEGORY_MOM_60(Z5 spread入选后v2降级；此处为右端参照、机制不同)。预期正方向。",
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
