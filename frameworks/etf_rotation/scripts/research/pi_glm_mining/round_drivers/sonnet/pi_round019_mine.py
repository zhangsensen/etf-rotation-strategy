#!/usr/bin/env python3
"""Round 019 driver: six spreads on the still-unpaired new-family atoms
(PRICE_VS_AVGCOST_20, OVERHAND_THICKNESS_60, COST_CENTER_SHIFT_20,
CLOSE30_VOL_SHARE_20, OPEN30_VOL_SHARE_20, BIGBAR_DIR_SKEW_20,
VOL_ENTROPY_20) plus declared-reuse old partners. Gate 7 v2.1; 1m leak gates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_019"

base.CANDIDATES = [
    {
        "id": "D1",
        "operator": "rank_spread",
        "left": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "profitable_uniform_participation",
        "hypothesis": "获利幅度与量熵之差=获利的形成方式：价格高于平均成本而量分布均匀(信号高)=获利由全天均匀参与自然形成(无脉冲拉抬)，健康延续；获利伴随低熵脉冲(信号低)=脉冲拉抬形成的获利，回吐。新x新组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "D2",
        "operator": "rank_spread",
        "left": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "overhang_absorption_flow",
        "hypothesis": "上方套牢厚度与主动买 imbalance 之差=解放行为的强度：套牢厚而主买强(信号高)=资金逆套牢结构主动买入(解放/信息强)，强延续；套牢薄而主买弱(信号低)=无阻力无接力。声明复用：TICK_IMBALANCE_20(C1中仅差门7的t=1.08)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "D3",
        "operator": "rank_spread",
        "left": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "right": {"name": "SESSION_MEAN_60", "source": "daily_candle"},
        "mechanism": "overhang_rescue_with_drift",
        "hypothesis": "套牢厚度与时段漂移之差=解放行情的存在性：套牢厚而时段漂移正(信号高)=持续买盘在逆套牢结构上行(解放行情)，延续；套牢薄而漂移正(信号低)=无阻力惯性，随环境。声明复用：SESSION_MEAN_60(U3/W3中拒绝)；此处作为环境参照而非漂移拆分。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "D4",
        "operator": "rank_spread",
        "left": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "RET_60", "source": "directional_trend"},
        "mechanism": "early_participation_in_early_trend",
        "hypothesis": "早盘量占比与长期动量之差=参与时机与趋势位置：早盘量占比高而60日动量弱(信号高)=低位早段新资金进场，延续；早盘量占比随动量走高而下降(信号低)=趋势晚期参与枯竭。声明相邻性：Y1是距高点x60日动量(identity拒绝)；此处左端为1m早盘参与度。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "D5",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "right": {"name": "COST_CENTER_SHIFT_20", "source": "cost_distribution"},
        "mechanism": "quiet_bigbar_absorption",
        "hypothesis": "大bar方向与成本重心位移之差=吸筹的隐蔽度：大bar买方向而成本重心未上移(信号高)=大资金低位吸筹且未推高市场成本(隐蔽)，强延续；大bar买入伴随成本快速上移(信号低)=高调推高、透支。声明复用：BIGBAR_DIR_SKEW_20(C5中仅差门7的t=0.90)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "D6",
        "operator": "rank_spread",
        "left": {"name": "COST_CENTER_SHIFT_20", "source": "cost_distribution"},
        "right": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "cost_relocation_vs_close_pulse",
        "hypothesis": "成本重心位移与尾盘量占比之差=成本抬升的健康度：成本上移而尾盘量占比低(信号高)=成本靠盘中连续买入抬高(健康)，延续；成本上移靠尾盘脉冲(信号低)=拉尾盘式抬升，回归。两原子均未用于任何组合。预期正方向。",
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
