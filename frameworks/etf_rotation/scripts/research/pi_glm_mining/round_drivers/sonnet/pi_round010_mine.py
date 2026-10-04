#!/usr/bin/env python3
"""Round 010 driver: mechanism family "regime-conditioned execution quality".

Design rules validated over rounds 005-009 and applied here:
- spread class only;
- BOTH endpoints are non-shelf atoms (shelf-parent spreads died at the 0.70
  wall three times: W3/Y5/E5, plus Z6);
- no variants of admitted W1/W5/Z5/Y3, no gap theme, no breadth template;
- reused atoms declared per hypothesis.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_010"

base.CANDIDATES = [
    {
        "id": "N1",
        "operator": "rank_spread",
        "left": {"name": "FIRST_HOUR_SHARE_REL_20", "source": "intraday_turnover_shape"},
        "right": {"name": "VOL_ACCEL_5_20", "source": "downside_risk"},
        "mechanism": "activity_front_running_vs_vol_accel",
        "hypothesis": "早盘活跃度相对自身20日基线的抬升与波动加速之差=建仓的隐蔽程度：活动前移而波动未加速(信号高)=知情资金有序前移建仓、未被市场察觉，延续；活动前移伴随波动加速(信号低)=抢筹暴露、定价透支，回归。声明复用：VOL_ACCEL_5_20(E4交互中拒绝)；构造类与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "N2",
        "operator": "rank_spread",
        "left": {"name": "CLOSE_LOCATION_DAILY", "source": "daily_candle"},
        "right": {"name": "AFTERNOON_VWAP_DEVIATION", "source": "intraday_vwap_position"},
        "mechanism": "late_marking_divergence",
        "hypothesis": "收盘位于日内区间高位而午后价格偏离成交重心低(信号高)=尾盘拉升脱离实际成交密集区，标记行为而非真实买盘，短期回吐；收盘位置高且午后溢价同步高(信号低)=全天实质买盘，延续。声明复用：CLOSE_LOCATION_DAILY(U7 spread中因幅度不足拒绝)；配对对象与机制不同。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "N3",
        "operator": "rank_spread",
        "left": {"name": "MAX_DD_60", "source": "downside_risk"},
        "right": {"name": "CATEGORY_VOL_60", "source": "category_state"},
        "mechanism": "drawdown_scar_regime",
        "hypothesis": "自身历史最大回撤与类别波动之差=回撤疤痕的归属：疤痕深而类别平静(信号高)=个体脆弱性未被环境解释、风险源仍在，继续走弱；疤痕由类别动荡解释(信号低)=环境性回撤，随环境平静修复。两原子均未用于任何组合。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "N4",
        "operator": "rank_spread",
        "left": {"name": "RET_ACF2_20", "source": "serial_dependence"},
        "right": {"name": "INTRADAY_SIGN_FLIP_RATE", "source": "intraday_trend_consistency"},
        "mechanism": "cross_scale_momentum_memory",
        "hypothesis": "多日动量记忆(二阶自相关)与日内拉锯之差=动量的跨尺度一致性：记忆强而日内翻转少(信号高)=全尺度有序趋势，延续；记忆强但日内持续拉锯(信号低)=趋势被日内交易消耗，回归。声明相邻性：X5是外生/内生来源对比(仅LOSO拒绝)；此处是自身记忆的跨尺度确认，非来源对比。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "N5",
        "operator": "rank_spread",
        "left": {"name": "BREAKOUT_ATR_60", "source": "price_location"},
        "right": {"name": "RANGE_ACTIVITY_ELASTICITY_60", "source": "uncertainty_activity"},
        "mechanism": "orderly_breakout_elasticity_gap",
        "hypothesis": "突破强度与活跃弹性之差=突破的执行质量：临近高点突破而单位活跃度波幅低(信号高)=深度承接下的有序突破，延续；弹性高(信号低)=情绪化情绪突破、薄簿放大，回归。声明复用：BREAKOUT_ATR_20(U6交互中拒绝)、RANGE_ACTIVITY_ELASTICITY_60(R8交互中拒绝)；构造类与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "N6",
        "operator": "rank_spread",
        "left": {"name": "MONEY_PRESSURE_5", "source": "price_volume_coupling"},
        "right": {"name": "MARKET_CORR_60", "source": "market_sensitivity"},
        "mechanism": "independent_pressure_premium",
        "hypothesis": "净资金压力与市场耦合之差=资金行为的独立性：压力强而与市场相关度低(信号高)=独立于大盘的自有逻辑资金(配置/事件驱动)，信息个体化、延续；压力随市场联动(信号低)=贝塔流、无个体信息。声明相邻性：X1是资金压力x特质波动(已见审计反向拒绝)；此处配对对象是市场耦合而非特质波动。预期正方向。",
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
