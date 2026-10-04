#!/usr/bin/env python3
"""Round 012 driver: mechanism family "dual momentum & execution noise".

Headline hypothesis (first time tested): absolute-vs-relative dual momentum,
RET_20 - CATEGORY_MOM_20 -- excess momentum over the category persists while
category beta-following fades. Plus five spread mechanisms on the same theme
of separating signal from noise. All endpoints non-shelf atoms, all pairs new,
reuses declared.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_012"

base.CANDIDATES = [
    {
        "id": "Q1",
        "operator": "rank_spread",
        "left": {"name": "RET_20", "source": "directional_trend"},
        "right": {"name": "CATEGORY_MOM_20", "source": "category_state"},
        "mechanism": "dual_momentum_absolute_vs_relative",
        "hypothesis": "经典双重动量：自身20日趋势减类别20日动量=相对强度。自身强于类别(信号高)=超额动量由个体资金/信息驱动、可延续；类别强而自身弱(信号低)=纯贝塔跟随，随板块回落时无缓冲。声明复用：RET_20(R3交互中拒绝；W5入选候选以其为右端做漂移拆分——机制不同，去重门将实证分离度)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Q2",
        "operator": "rank_spread",
        "left": {"name": "TREND_RET_VOLADJ_20", "source": "directional_trend"},
        "right": {"name": "VOLUME_Z_60", "source": "trading_activity"},
        "mechanism": "trend_vs_volume_noise",
        "hypothesis": "波动调整趋势与放量之差=趋势中的噪音含量：趋势强而量能平稳(信号高)=低噪音趋势、定价有序，延续；趋势由量能爆炸推动(信号低)=噪音趋势、情绪驱动，回归。两原子均未用于任何组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Q3",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_DEV_20", "source": "downside_risk"},
        "right": {"name": "DOWNSIDE_BETA_20", "source": "market_sensitivity"},
        "mechanism": "idiosyncratic_downside_share",
        "hypothesis": "自身下行偏差减下行贝塔=特质下行占比：下行偏差高而系统性下行敏感低(信号高)=特质性下行风险(个体问题、无系统性补偿)，走弱；下行偏差低而贝塔高(信号低)=纯系统暴露，随市场修复回补。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Q4",
        "operator": "rank_spread",
        "left": {"name": "VAR_RATIO_20_120", "source": "serial_dependence"},
        "right": {"name": "RANGE_ACTIVITY_ELASTICITY_20", "source": "uncertainty_activity"},
        "mechanism": "trend_component_elasticity_gap",
        "hypothesis": "方差比(趋势分量占比)与活跃弹性之差=趋势分量纯度：趋势分量占优而弹性低(信号高)=低噪有序趋势，延续；弹性高(信号低)=活跃度被放大成波幅的情绪行情，回归。声明复用：RANGE_ACTIVITY_ELASTICITY_20(X2 spread中拒绝)；配对对象与机制不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Q5",
        "operator": "rank_spread",
        "left": {"name": "RETURN_SKEW_60", "source": "return_tail_shape"},
        "right": {"name": "FIRST_HOUR_VWAP_DEVIATION", "source": "intraday_vwap_position"},
        "mechanism": "skew_premium_morning_gap",
        "hypothesis": "收益偏度与早盘VWAP溢价之差=尾部结构与开盘情绪的匹配：正偏而早盘溢价低(信号高)=平静中含上行尾部机会、开盘未透支，看涨；负偏而早盘溢价高(信号低)=情绪开盘透支尾部风险，回吐。两原子均未用于任何组合。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Q6",
        "operator": "rank_spread",
        "left": {"name": "PATH_EFFICIENCY_20", "source": "path_efficiency"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "quiet_path_efficiency",
        "hypothesis": "路径质量与量能不稳定之差=安静的效率：趋势路径平滑而量能节奏平稳(信号高)=安静的有效趋势、低摩擦定价，延续；路径质量由剧烈量能不稳换来(信号低)=噪音驱动的表面趋势，回归。声明复用：LOG_AMOUNT_VOL_20(U1交互中拒绝)；构造类与机制不同。预期正方向。",
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
