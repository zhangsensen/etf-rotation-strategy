#!/usr/bin/env python3
"""Round 003 driver: reuses the corrected round_002 runner (hard leak gates,
fail-closed dedup, provenance, canonical cross-round expression dedup) with a
new preregistered candidate list. No gate, surface, population or label change.

Novelty discipline for round_003:
- every pair is atom-level new (canonical hash dedup covers round_001+round_002
  plans, v9 135 atomics, shelf 16 keys -- asserted at plan time);
- every mechanism name is new; none is a window-variant of a prior failure
  mechanism (round_001 trend/path/gap/overreaction/tail-net-vol/lead-lag-chain;
  round_002 closing-execution, marking-pressure, info-timing, opening-liquidity,
  flow-quality, position-tail, rotation-expansion, drift-regime);
- reuse of an atom with a DIFFERENT partner family and a DIFFERENT mechanism is
  declared explicitly in the hypothesis field, never silent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_003"

base.CANDIDATES = [
    {
        "id": "U1",
        "operator": "rank_interaction",
        "left": {"name": "FIRST_HOUR_TURNOVER_SHARE", "source": "intraday_turnover_shape"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "participation_timing_liquidity_noise",
        "hypothesis": "早盘换手占比度量参与者赶在开盘执行的强度；在日度成交额波动率低(流动性节奏平稳)的品种上，早盘占比高代表稳定的机构配置节奏、信息定价充分，短期延续；在成交额剧烈波动的品种上，早盘集中是脉冲性抢筹/恐慌换手，随后衰减。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U2",
        "operator": "rank_interaction",
        "left": {"name": "INTRADAY_SIGN_FLIP_RATE", "source": "intraday_trend_consistency"},
        "right": {"name": "CATEGORY_MOM_20", "source": "category_state"},
        "mechanism": "contested_chase_in_category_trend",
        "hypothesis": "日内方向翻转率高=品种内部多空拉锯、缺乏共识；当所属类别中期动量强时，拉锯品种是轮动资金尚未完成的补涨候选，随后被跟进(正)；类别动量弱时拉锯只是无主震荡。交互(翻转率x类别动量)预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U3",
        "operator": "rank_interaction",
        "left": {"name": "WICK_IMBALANCE", "source": "daily_candle"},
        "right": {"name": "AMOUNT_RATIO_5_20", "source": "trading_activity"},
        "mechanism": "rejection_wick_with_participation",
        "hypothesis": "日K影线不对称(一端被明确拒绝)只有在放量(5日/20日量比扩张)时才是真实的承接/拒绝信号，缩量影线是噪声毛刺；放量拒绝后的短期价格向被确认的方向修复。与round_001 E1不同：E1是多日趋势x成交额水平z的拥挤度，此处左端是K线形态而非趋势。影线方向语义决定符号，方向最终由发现期确定。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U4",
        "operator": "rank_interaction",
        "left": {"name": "PEER_LEAD_BETA_20", "source": "cross_etf_lead_lag"},
        "right": {"name": "INTRADAY_RETURN_KURTOSIS", "source": "intraday_return_distribution"},
        "mechanism": "peer_contagion_fat_tail",
        "hypothesis": "对同类peer的领先beta高=品种处于同组信息传导链上游；日内收益峭度高=日内极端波动频繁。高传导x肥尾共振时跨品种冲击在日内集中爆发、信息未定价完，次日延续；峭度低时传导已被平滑定价。与round_001 E6不同：E6是市场级领先beta x 隔夜-日内承接，此处是peer级传导 x 日内肥尾形态。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U5",
        "operator": "rank_interaction",
        "left": {"name": "ASSET_LEAD_MARKET_CORR_20", "source": "cross_etf_lead_lag"},
        "right": {"name": "AFTERNOON_TURNOVER_SHARE", "source": "intraday_turnover_shape"},
        "mechanism": "market_leader_afternoon_repositioning",
        "hypothesis": "品种领先市场的相关结构(ASSET_LEAD_MARKET_CORR)=其价格包含先于市场的信息；领先品种午后换手占比升高=敏感资金在午后重新布局、信息持续释放，短期延续；跟随品种午后放量则是尾随拥挤、易回吐。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U6",
        "operator": "rank_interaction",
        "left": {"name": "VAR_RATIO_5_60", "source": "serial_dependence"},
        "right": {"name": "BREAKOUT_ATR_20", "source": "price_location"},
        "mechanism": "variance_ratio_breakout_quality",
        "hypothesis": "方差比(5日相对60日)刻画趋势性方差分量：方差比高(趋势分量占优)时临近20日高点的突破更可能是真突破、短期延续；方差比低(均值回归分量占优)时临高点是假突破、回吐。突破质量由趋势状态放大。与round_001 E4不同：E4是符号自相关x波动加速的过度反应，此处是方差比x位置突破的质量判定。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U7",
        "operator": "rank_interaction",
        "left": {"name": "CLOSE_LOCATION_DAILY", "source": "daily_candle"},
        "right": {"name": "RETURN_SKEW_60", "source": "return_tail_shape"},
        "mechanism": "closing_location_tail_skew",
        "hypothesis": "收盘位于日内区间高位=买方控制收尾；近60日收益偏度为负(尾部受损、偶发深跌)时，强势收盘代表修复性买盘在吸纳尾部风险，短期延续；偏度为正(偶发大涨)时的强势收盘是过热尾部，易回吐。交互(收盘位x偏度)预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "U8",
        "operator": "rank_interaction",
        "left": {"name": "VOL_CONCENTRATION", "source": "intraday_volatility_structure"},
        "right": {"name": "BENCHMARK_RESIDUAL_VOL_60", "source": "market_sensitivity"},
        "mechanism": "vol_timing_idio_noise",
        "hypothesis": "波动在日内高度集中(单段爆发)且特质波动高=孤立冲击(个别资金行为)，随后均值回归；集中波动发生在低特质波动品种上则是市场级信息的快速定价，延续。交互(集中度x特质波动)的危害随特质波动升高，预期负方向。",
        "expected_sign": -1,
    },
]


_orig_assert = base._assert_not_window_variant


def _assert_not_window_variant_all(draft, _prior_plan=None) -> None:
    """Check atom-pair and mechanism-name novelty against ALL prior round
    plans, not just the first one."""
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
