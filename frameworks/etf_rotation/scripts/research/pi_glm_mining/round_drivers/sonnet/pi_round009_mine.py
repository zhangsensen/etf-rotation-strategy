#!/usr/bin/env python3
"""Round 009 driver: new limited mechanism family "execution premium &
migration confirmation" -- six spreads, all atom-level new pairs.

Design constraints from accumulated failures:
- spread class only (3/16 admitted vs 0/27 interactions);
- avoid quantities dominated by volatility/beta LEVELS (Z6/W3/E5 all hit the
  shelf redundancy wall at |corr|~0.70-0.85);
- no variants of admitted W1/W5/Z5, no gap-theme (three strikes), no
  category-breadth template reuse (V1/X4 rejected);
- reused atoms declared per hypothesis.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_009"

base.CANDIDATES = [
    {
        "id": "Y1",
        "operator": "rank_spread",
        "left": {"name": "DIST_HIGH_20_VOLADJ", "source": "price_location"},
        "right": {"name": "RET_60", "source": "directional_trend"},
        "mechanism": "strength_recency_gap",
        "hypothesis": "距高点与中期动量之差度量强度的新近性：接近20日高点而60日动量弱(信号低)=新高刚启动、新信息定价早期，延续为正；远离高点而动量强(信号高)=趋势老化、透支，衰竭。信号与短期回报负相关。两原子均为首次配对；RET_60未用于任何组合。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Y2",
        "operator": "rank_spread",
        "left": {"name": "LAST_HOUR_TURNOVER_SHARE", "source": "intraday_turnover_shape"},
        "right": {"name": "RANGE_ACF1_20", "source": "range_memory"},
        "mechanism": "event_closing_vs_crowded_closing",
        "hypothesis": "尾盘参与强度减波动自相关=尾盘放量的性质判定：尾盘换手占比高而波动未处于簇状态(ACF低)=离散事件信息在收盘段到达，次日延续；波动簇中(ACF高)的尾盘参与少=趋势无接力、拥挤末端回归。信号高(事件性尾盘)延续、信号低(无接力簇)走弱。声明复用：LAST_HOUR_TURNOVER_SHARE(R1交互中拒绝)、RANGE_ACF1_20(V4交互中拒绝)；构造类与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Y3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_RETURN_KURTOSIS", "source": "intraday_return_distribution"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "idiosyncratic_fat_tail_regime",
        "hypothesis": "品种日内肥尾与类别波动之差=肥尾的归属判定：品种日内极端波动频繁而类别平静(信号高)=孤立个体事件风险、未扩散定价，回归；类别本身动荡中的肥尾=环境性波动、非个体信息。信号高回归。声明复用：INTRADAY_RETURN_KURTOSIS(U4交互中拒绝)；构造类与配对对象不同。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Y4",
        "operator": "rank_spread",
        "left": {"name": "BODY_TO_RANGE", "source": "daily_candle"},
        "right": {"name": "VOLUME_Z_20", "source": "trading_activity"},
        "mechanism": "body_conviction_volume_gap",
        "hypothesis": "K线实体占比与放量之差度量执行的坚决程度：实体大而缩量(信号高)=知情资金静默有序执行、无跟风噪音，延续；实体小而放量(信号低)=犹豫拉锯换手，回归。声明相邻性：WICK_IMBALANCE(U3)是影线拒绝x量比交互，此处是实体方向占比x量水平z的spread。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Y5",
        "operator": "rank_spread",
        "left": {"name": "TAIL_TURNOVER_PRICE_IMPACT", "source": "intraday_turnover_asymmetry"},
        "right": {"name": "AMIHUD_60", "source": "price_volume_coupling"},
        "mechanism": "closing_execution_premium_gap",
        "hypothesis": "尾盘换手价格冲击减常态冲击成本=收盘段执行溢价：尾盘单位换手推动力大而常态成本低(信号高)=信息资金在收盘段集中执行、成本结构允许其隐秘建仓，短期延续；常态成本本身就高(信号低)=无补偿、冲击即摩擦。与W1不同：W1是早盘换手份额x早盘波动份额(时点结构)，此处是尾盘冲击弹性x日线冲击成本(定价结构)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Y6",
        "operator": "rank_spread",
        "left": {"name": "AMOUNT_RATIO_20_60", "source": "trading_activity"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "steady_expansion_premium",
        "hypothesis": "量能扩张与量能不稳定之差=扩张质量：量比抬升而成交额节奏平稳(信号高)=持续有序吸筹，延续；扩张伴随剧烈不稳(信号低)=脉冲性抢筹/恐慌换手，回归。声明复用：AMOUNT_RATIO_20_60(V5交互中拒绝)、LOG_AMOUNT_VOL_20(U1交互中拒绝)；构造类与机制不同。预期正方向。",
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
