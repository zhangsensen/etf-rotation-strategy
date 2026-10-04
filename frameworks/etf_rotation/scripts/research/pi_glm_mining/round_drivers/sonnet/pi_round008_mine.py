#!/usr/bin/env python3
"""Round 008 driver: one new limited falsifiable mechanism family per the
supervisor rule (census showed legal untested space, so exhaustion is NOT
claimable): "compensation & migration structure".

Umbrella hypothesis: short-term price pressure is monetizable only when a
compensation channel (liquidity provision reward, position migration, convexity,
coherence mismatch, mispricing-vs-category, pulse-vs-chronic structure) is
present. All six are spreads (the productive construction class: 2/13 admitted
vs 0/27 interactions), all cross-family, all pairs atom-level new, reused atoms
declared per hypothesis.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_008"

base.CANDIDATES = [
    {
        "id": "Z1",
        "operator": "rank_spread",
        "left": {"name": "RET_5", "source": "directional_trend"},
        "right": {"name": "AMIHUD_60", "source": "price_volume_coupling"},
        "mechanism": "reversal_harvest_liquidity_supply",
        "hypothesis": "短期反转的可收割性由流动性补偿决定：深跌发生在低冲击成本品种(AMIHUD低=价差小)时，提供流动性的补偿最小、反转由信息驱动而非补偿驱动；深跌发生在高冲击成本品种时，反转主要来自流动性提供者的价差补偿，可修复。信号=近期收益减非流动性(信号低=深跌+高补偿)预期未来正，即信号与短期回报负相关。声明复用：RET_5(R2交互中拒绝)、AMIHUD族(R4交互中拒绝)；构造类与机制不同(补偿结构 vs 标记压力/开盘成本)。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Z2",
        "operator": "rank_spread",
        "left": {"name": "VOLUME_RATIO_20_60", "source": "trading_activity"},
        "right": {"name": "PRICE_POSITION_120", "source": "price_location"},
        "mechanism": "volume_migration_position",
        "hypothesis": "放量与价格位置之差度量筹码迁移方向：量比扩张而长窗位置低=底部承接换手(筹码由弱手转强手)，行情真实、延续；缩量而位置高=顶部惯性、无承接，回归。信号高(放量+低位)延续、信号低(缩量+高位)回归。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z3",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_DEV_60", "source": "downside_risk"},
        "right": {"name": "UPSIDE_BETA_20", "source": "market_sensitivity"},
        "mechanism": "downside_upside_convexity_gap",
        "hypothesis": "下行偏差与上行贝塔之差度量收益分布的凸性错配：下行偏差高而上行弹性低(信号高)=凹形风险结构、跌时放大涨时缺失，风险未被补偿、继续走弱；下行偏差低而上行弹性高(信号低)=凸形结构、涨时放大跌时收敛，正偏补偿。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Z4",
        "operator": "rank_spread",
        "left": {"name": "PRICE_AMOUNT_CORR_20", "source": "price_volume_coupling"},
        "right": {"name": "INTRADAY_PV_RETURN_TURNOVER_CORR", "source": "intraday_price_volume_shock"},
        "mechanism": "volume_price_coherence_scale_gap",
        "hypothesis": "日线与日内量价耦合之差=量价关系的尺度错位：日线正相关而日内负相关(信号高)=长线配置资金持续买入、日内交易者向其出货，吸筹结构、延续；日线负相关而日内正相关(信号低)=日内投机推动、长线不认，回归。与round_002 R5不同：R5是日内量价相关x资金压力交互，此处是与日线量价相关的尺度差(spread)。INTRADAY_PV_RETURN_TURNOVER_CORR为复用原子、构造类与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z5",
        "operator": "rank_spread",
        "left": {"name": "CURRENT_DD_60", "source": "downside_risk"},
        "right": {"name": "CATEGORY_MOM_60", "source": "category_state"},
        "mechanism": "idiosyncratic_drawdown_vs_category_trend",
        "hypothesis": "自身长窗回撤减类别动量=错杀程度：自身回撤深而类别动量强(信号低)=板块环境未坏下的个体错杀，板块资金回流带动修复，未来正；自身回撤浅而类别动量弱(信号高)=独立强势但失去板块支撑。信号与未来回报负相关。声明相邻性：W4是回撤x类别回撤(双回撤水平差,弱信号拒绝)，此处对象是类别动量而非回撤，机制为错杀修复而非相对强势。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Z6",
        "operator": "rank_spread",
        "left": {"name": "DAILY_RANGE_PCT", "source": "daily_candle"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "pulse_tail_vs_chronic_range",
        "hypothesis": "日常波幅与最差单日之差区分尾部性质：波幅小而最差日深(信号低)=一次性脉冲冲击而非持续高波动，事件出清后修复，未来正；波幅大而最差日浅(信号高)=慢性混乱波动、持续消耗，负。声明复用：WORST_DAY_60在E5 spread中拒绝(与波动shelf冗余0.85)；此处窗口不同、对手是日内波幅而非波动水平、机制为脉冲-慢性区分。预期负方向。",
        "expected_sign": -1,
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
