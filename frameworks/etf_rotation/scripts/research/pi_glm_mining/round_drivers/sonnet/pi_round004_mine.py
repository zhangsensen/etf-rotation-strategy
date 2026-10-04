#!/usr/bin/env python3
"""Round 004 driver: reuses the corrected round_002 runner with a limited set
of six preregistered, previously-untested expressions.

Novelty discipline for round_004 (cumulative dedup at plan time):
- all six pairs are atom-level new vs round_001/002/003 plans, v9 135 atomics
  and the 16 shelf keys (canonical, swap/sign-symmetric hashing);
- all mechanism names are new; none is a window variant of a prior failure
  mechanism. Explicitly avoided families: trend x activity-level (E1), trend
  quality x direction (E2), gap-resonance (E3/E6), sign-ACF x vol-accel (E4),
  tail-minus-vol (E5), VWAP-marking x short-term-trend (R2/R8), flow-quality
  resonance (R5), money-pressure x intraday-PV (R5 family).
- category_state appears only as an external regime conditioner (breadth,
  dispersion) on atoms whose families never met it before.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_004"

base.CANDIDATES = [
    {
        "id": "V1",
        "operator": "rank_interaction",
        "left": {"name": "DIST_HIGH_60_VOLADJ", "source": "price_location"},
        "right": {"name": "CATEGORY_BREADTH_MA20", "source": "category_state"},
        "mechanism": "near_high_in_broad_category",
        "hypothesis": "接近60日波动调整高点(强势结构)且类别广度高(多数成员站在均线上方)时，强势是板块级共识资金流的一部分、动量延续；广度低(分化行情)时的近高点品种是孤雁，由个体事件推高、易回落。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "V2",
        "operator": "rank_interaction",
        "left": {"name": "SESSION_MEAN_20", "source": "daily_candle"},
        "right": {"name": "MARKET_CORR_20", "source": "market_sensitivity"},
        "mechanism": "persistent_session_drift_market_coupling",
        "hypothesis": "近20日日内时段(非隔夜)收益均值度量持续的日内买盘倾向；与市场相关度高时，该漂移反映系统性配置资金在交易时段的持续流入，延续性强；低相关品种的日内正漂移是个体资金行为，易反转。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "V3",
        "operator": "rank_interaction",
        "left": {"name": "RETURN_CONCENTRATION_20", "source": "return_concentration"},
        "right": {"name": "CATEGORY_DISPERSION_60", "source": "category_state"},
        "mechanism": "idiosyncratic_concentration_in_dispersion",
        "hypothesis": "收益集中于少数大日(集中度高)且类别内离散度高(分化行情)时，该品种行情由自身特定信息驱动、独立于板块共振，信息未扩散完、延续性强；类别一致行情中的高集中是共振脉冲，随后消退。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "V4",
        "operator": "rank_interaction",
        "left": {"name": "RANGE_ACF1_20", "source": "range_memory"},
        "right": {"name": "INTRADAY_TREND_CONSISTENCY", "source": "intraday_trend_consistency"},
        "mechanism": "vol_cluster_intraday_persistence",
        "hypothesis": "波幅自相关高=波动处于持续簇状态(有主流行情)；波动簇内的日内趋势一致性好=方向与波动同时有序，趋势行情健康、短期延续；波动簇内日内乱序(翻转频繁)=无序震荡、消耗。交互(波动记忆x日内方向质量)预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "V5",
        "operator": "rank_interaction",
        "left": {"name": "PEER_LEAD_NETWORK_CORR_20", "source": "cross_etf_lead_lag"},
        "right": {"name": "AMOUNT_RATIO_20_60", "source": "trading_activity"},
        "mechanism": "network_central_volume_surge",
        "hypothesis": "peer网络领先相关度高=品种处于同类信息传导网络的中枢；中枢品种的量比扩张(20日/60日成交额比)是组级信息扩散的源头，短期领涨/领跌延续；边缘品种的放量是尾随跟风、易回吐。与round_003 U5不同：U5是领先市场结构x午后换手时点，此处是网络中枢度x量比扩张。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "V6",
        "operator": "rank_interaction",
        "left": {"name": "GAP_MEAN_20", "source": "daily_candle"},
        "right": {"name": "FIRST_HOUR_VWAP_DEVIATION", "source": "intraday_vwap_position"},
        "mechanism": "regular_gap_first_hour_absorption",
        "hypothesis": "20日平均跳空(带符号)度量规则性隔夜信息流(如跨境/商品联动的系统性隔夜定价)；规则性跳空品种的首小时VWAP溢价=隔夜信息在开盘段被有效吸收、方向得到确认，日内与次日延续；无跳空惯例品种的首小时溢价是开盘噪声。与round_001 E3/E6不同：那两个是gap_volatility/gap_response家族的跳空-日内相关结构，此处是daily_candle跳空均值x日内VWAP位置的吸收确认。交互预期正方向。",
        "expected_sign": 1,
    },
]

_orig_assert = base._assert_not_window_variant


def _assert_not_window_variant_all(draft, _prior_plan=None) -> None:
    """Check atom-pair and mechanism-name novelty against ALL prior round plans."""
    for plan_path in base._previous_round_plans():
        _orig_assert(draft, json.loads(plan_path.read_text()))


base._assert_not_window_variant = _assert_not_window_variant_all

_orig_snapshot = base._snapshot


def _snapshot_with_base(output, plan):
    hashes = _orig_snapshot(output, plan)
    base_script = Path(base.__file__).resolve()
    target = output / "snapshots" / base_script.name
    if not target.exists():
        import shutil

        shutil.copy2(base_script, target)
    hashes[f"script:{base_script.name}"] = base._hash(base_script)
    return hashes


base._snapshot = _snapshot_with_base

if __name__ == "__main__":
    base.main()
