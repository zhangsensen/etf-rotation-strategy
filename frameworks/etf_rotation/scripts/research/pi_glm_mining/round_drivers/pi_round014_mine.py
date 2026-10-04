#!/usr/bin/env python3
"""Round 014 driver: final fresh-atom batch, spread class, non-shelf endpoints.

These are the last untested atoms with falsifiable two-atom mechanisms:
OVERNIGHT_GAP, SESSION_RETURN, SIGN_ACF1_5, RET_ACF2_20, TREND_RET_VOLADJ_60,
VOLUME_RATIO_5_20, MARKET_LEAD_CORR_60, PEER_LEAD_CORR_60,
CATEGORY_BREADTH_MA60, CATEGORY_CURRENT_DD_60. Burnt atoms are declared.
If this round yields zero gate-7 admissions it is the THIRD consecutive
zero-gate-7 round (after rounds 012/013) and the contract's exhaustion
criterion applies.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_014"

base.CANDIDATES = [
    {
        "id": "T1",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_GAP", "source": "daily_candle"},
        "right": {"name": "MORNING_VWAP_DEVIATION", "source": "intraday_vwap_position"},
        "mechanism": "overnight_recognition_vs_open_chase",
        "hypothesis": "隔夜跳空与早盘溢价之差=隔夜信息的开盘消化状态：隔夜正跳空而早盘价格低于VWAP(信号高)=跳空被开盘段抛压消化、追高者已离场，信息仍有空间，修复延续；隔夜负跳空而早盘抢跑追价(信号低)=开盘情绪透支，回落。声明：OVERNIGHT_GAP为最后未测的gap族原子；gap主题已三败(E3/E6/V6)，此为其最后可证伪形式。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "T2",
        "operator": "rank_spread",
        "left": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "right": {"name": "CATEGORY_BREADTH_MA60", "source": "category_state"},
        "mechanism": "order_independence_breadth",
        "hypothesis": "短窗符号持续与类别广度之差=秩序的独立来源：符号持续强而广度低(信号高)=分化行情中自身有序、信息独立于板块，延续；广度高时的符号惯性=普涨普跌的贝塔惯性，随环境逆转。声明复用：广度条件化(V1/X4)均已拒绝，此处为60日广度右端参照、机制为秩序独立性。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "T3",
        "operator": "rank_spread",
        "left": {"name": "TREND_RET_VOLADJ_60", "source": "directional_trend"},
        "right": {"name": "PEER_LEAD_CORR_60", "source": "cross_etf_lead_lag"},
        "mechanism": "voladj_trend_independence",
        "hypothesis": "波动调整趋势与组内耦合之差=独立高质量趋势：趋势强而组内耦合低(信号高)=不依赖同类资金流的独立alpha行情，延续；耦合高(信号低)=组内贝塔行情，无自身信息。声明相邻性：S4(位置x组内耦合)多门拒绝；此处左端为波调趋势、60窗。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "T4",
        "operator": "rank_spread",
        "left": {"name": "VOLUME_RATIO_5_20", "source": "trading_activity"},
        "right": {"name": "MARKET_LEAD_CORR_60", "source": "cross_etf_lead_lag"},
        "mechanism": "independent_volume_vs_market_coupling",
        "hypothesis": "量比与市场领先耦合之差=放量的独立性：放量而市场领先耦合低(信号高)=独立于大盘节奏的资金行为、含个体信息，延续；耦合高而缩量(信号低)=贝塔缩量、无自身信息。声明复用：VOLUME_RATIO_5_20(U3交互中拒绝)；构造类与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "T5",
        "operator": "rank_spread",
        "left": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "quiet_sign_persistence",
        "hypothesis": "符号持续与量能不稳之差=趋势的安静程度：符号持续强而量能节奏平稳(信号高)=低噪音有序趋势，延续；持续伴随量能剧烈不稳(信号低)=噪音维持的表面趋势，回归。声明：SIGN_ACF1_5为serial_dependence族最后未测短窗原子(该族E4/X5/P1/P4均已拒绝)；LOG_AMOUNT_VOL_20(Q6中拒绝)复用。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "T6",
        "operator": "rank_spread",
        "left": {"name": "SESSION_RETURN", "source": "daily_candle"},
        "right": {"name": "CATEGORY_CURRENT_DD_60", "source": "category_state"},
        "mechanism": "session_drift_in_category_health",
        "hypothesis": "当日时段收益与类别回撤之差=顺风程度：时段收益强而类别回撤浅(信号高)=健康环境中的顺风上行，延续；时段收益强而类别深处回撤(信号低)=逆环境的孤立强势，随环境继续恶化。两原子均未用于任何组合。预期正方向。",
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
