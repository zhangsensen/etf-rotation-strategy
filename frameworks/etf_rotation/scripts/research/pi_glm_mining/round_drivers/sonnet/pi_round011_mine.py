#!/usr/bin/env python3
"""Round 011 driver: mechanism family "maturity & attribution".

Six spreads, all endpoints non-shelf atoms (the Y5/N3 wall lesson), all pairs
atom-level new, mechanism names new, reused atoms declared. Family hypothesis:
whether a short-horizon price behaviour continues depends on the MATURITY of
the trend it belongs to and the ATTRIBUTION of its risk (individual vs
category/environment).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_011"

base.CANDIDATES = [
    {
        "id": "P1",
        "operator": "rank_spread",
        "left": {"name": "RET_ACF1_5", "source": "serial_dependence"},
        "right": {"name": "PRICE_POSITION_120", "source": "price_location"},
        "mechanism": "trend_maturity_memory_gap",
        "hypothesis": "短窗动量记忆与长期价格位置之差=趋势成熟度：记忆强而长窗位置不高(信号高)=趋势处于早期、定价未完成，延续；记忆衰减而位置极高(信号低)=晚期趋势、透支，回归。两原子均未用于任何组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "P2",
        "operator": "rank_spread",
        "left": {"name": "MAX_DD_20", "source": "downside_risk"},
        "right": {"name": "RETURN_SKEW_20", "source": "return_tail_shape"},
        "mechanism": "drawdown_skew_asymmetry",
        "hypothesis": "近期最大回撤与收益偏度之差=风险的形状：回撤深且偏度为负(信号低)=持续恶化的左尾，走弱；回撤浅且偏度为正(信号高)=右偏结构、上行尾开放，健康。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "P3",
        "operator": "rank_spread",
        "left": {"name": "VOL_ACCEL_5_20", "source": "downside_risk"},
        "right": {"name": "INTRADAY_SIGN_FLIP_RATE", "source": "intraday_trend_consistency"},
        "mechanism": "directional_vol_accel",
        "hypothesis": "波动加速与日内拉锯之差=波动的方向性归属：波动加速而日内方向有序(信号高)=趋势性波动(方向性行情放大)，延续；加速且日内拉锯(信号低)=混沌噪音波动，回归。声明复用：两原子分别于E4/N4交互中拒绝；构造类与配对不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "P4",
        "operator": "rank_spread",
        "left": {"name": "RET_ACF2_60", "source": "serial_dependence"},
        "right": {"name": "CATEGORY_CURRENT_DD_20", "source": "category_state"},
        "mechanism": "momentum_memory_in_category_health",
        "hypothesis": "动量记忆与类别回撤之差=动量的环境健康度：记忆强而类别回撤浅(信号高)=健康环境中的持续动量，延续；记忆强但类别深处回撤(信号低)=逆环境的危险动量，随环境恶化。两原子均未用于任何组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "P5",
        "operator": "rank_spread",
        "left": {"name": "DIST_HIGH_60_VOLADJ", "source": "price_location"},
        "right": {"name": "FIRST_HOUR_SHARE_REL_60", "source": "intraday_turnover_shape"},
        "mechanism": "early_accumulation_vs_chase",
        "hypothesis": "距高点与早盘相对活跃度之差=参与时机与位置的匹配：距离远(低位)而早盘相对活跃抬升(信号高)=低位早段吸筹，延续；距离近(高位)而早盘抢筹(信号低)=追高拥挤，回归。声明相邻性：Y1是距离x60日动量(仅LOSO拒绝)；此处配对对象是早盘相对活跃度，机制为参与时机匹配。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "P6",
        "operator": "rank_spread",
        "left": {"name": "BODY_TO_RANGE", "source": "daily_candle"},
        "right": {"name": "CATEGORY_MOM_5", "source": "category_state"},
        "mechanism": "leadership_body_vs_category_flow",
        "hypothesis": "自身实体坚决度与类别短动量之差=领先性：实体坚决而类别动量未起(信号高)=领先板块一步的个体行情、信息先行，延续；类别动量强而自身实体弱(信号低)=被动跟随贝塔、无自身信息，随板块回落。声明复用：BODY_TO_RANGE(Y4 spread中拒绝)；配对对象与机制不同。预期正方向。",
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
