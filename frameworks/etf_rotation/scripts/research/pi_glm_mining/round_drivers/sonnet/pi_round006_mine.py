#!/usr/bin/env python3
"""Round 006 driver: reuses the corrected round_002 runner with six
preregistered cross-family SPREAD expressions.

Round_005 lesson being applied: the spread (level-removing) construction class
produced the first admitted candidates (2/6) while all 34 interaction-class
expressions across rounds 001-005 failed. This batch stays in the spread class
with entirely new mechanisms; interaction-style retries are deliberately not
included.

Novelty discipline: all six pairs are atom-level new (cumulative canonical
dedup vs rounds 001-005, v9 atomics, shelf keys); all mechanism names are new;
reused atoms are declared in the hypothesis field.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_006"

base.CANDIDATES = [
    {
        "id": "X1",
        "operator": "rank_spread",
        "left": {"name": "MONEY_PRESSURE_60", "source": "price_volume_coupling"},
        "right": {"name": "BENCHMARK_RESIDUAL_VOL_20", "source": "market_sensitivity"},
        "mechanism": "quiet_accumulation_gap",
        "hypothesis": "持续净资金压力与特质波动之差度量建仓的隐蔽程度：净压力高而特质波动低=资金在不惊动定价的情况下有序吸筹(执行隐蔽)，信息未释放完、短期延续；压力伴随高特质波动=抢筹暴露、定价已透支，回归。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X2",
        "operator": "rank_spread",
        "left": {"name": "VOLUME_Z_60", "source": "trading_activity"},
        "right": {"name": "RANGE_ACTIVITY_ELASTICITY_20", "source": "uncertainty_activity"},
        "mechanism": "volume_impact_efficiency_gap",
        "hypothesis": "放量与波幅弹性之差度量执行效率：高换手而单位活跃度引起的波幅低=大单被深度簿平稳吸收(被动/机构执行)，筹码转移有序、行情延续；弹性高=活跃度转化为剧烈波幅(情绪放大)，过热回归。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X3",
        "operator": "rank_spread",
        "left": {"name": "PRICE_POSITION_120", "source": "price_location"},
        "right": {"name": "CURRENT_DD_20", "source": "downside_risk"},
        "mechanism": "trend_position_short_pullback",
        "hypothesis": "120日价格位置减去20日回撤浅度：长窗口位置极高而短窗口回撤偏深的组合(信号低值区)是上升趋势中的回调买点，短期修复为正；两者皆强(信号高值区)是全面强势但透支。若回调修复成立，信号与短期回报负相关。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "X4",
        "operator": "rank_spread",
        "left": {"name": "RETURN_CONCENTRATION_60", "source": "return_concentration"},
        "right": {"name": "CATEGORY_BREADTH_MA20", "source": "category_state"},
        "mechanism": "concentration_breadth_gap",
        "hypothesis": "收益集中度与类别广度之差区分行情驱动源：高集中而低广度(分化环境中的孤立爆发)=自身信息驱动、未扩散完、延续；高集中而高广度(普涨环境的贝塔脉冲)=随板块共振消退。信号高值区(高集中低广度)延续。与round_004 V1不同：V1是价格位置x广度交互，此处是收益集中度对广度的spread。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X5",
        "operator": "rank_spread",
        "left": {"name": "MARKET_LEAD_CORR_20", "source": "cross_etf_lead_lag"},
        "right": {"name": "RET_ACF1_20", "source": "serial_dependence"},
        "mechanism": "exogenous_vs_endogenous_momentum_source",
        "hypothesis": "领先市场的相关结构(外生信息源强度)减自身收益自相关(内生趋势惯性)=动量驱动源类型：外生传导占优的品种在持续接收市场先行信息、定价延续；纯内生自相关的品种靠自身惯性、临近衰竭。外生强于内生(信号高)延续。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X6",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_PATH_EFFICIENCY", "source": "intraday_return_path"},
        "right": {"name": "PATH_EFFICIENCY_10", "source": "path_efficiency"},
        "mechanism": "path_quality_scale_gap",
        "hypothesis": "日内路径质量与10日路径质量之差=趋势质量的尺度错位：日内高效而日线低效(信号高)=新的有序行情刚出现(状态转换早期)，延续；日线高效而日内低效(信号低)=老趋势衰竭、日内开始失序。与round_001 E2不同：E2是路径效率x中期方向交互，此处是同度量跨尺度的spread。PATH_EFFICIENCY族为复用、构造类与机制不同。预期正方向。",
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
