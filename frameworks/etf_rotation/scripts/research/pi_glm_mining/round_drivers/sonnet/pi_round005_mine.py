#!/usr/bin/env python3
"""Round 005 driver: reuses the corrected round_002 runner with SIX
preregistered cross-family SPREAD expressions.

Construction-class note (honest answer to MECHANISM_EXHAUSTED risk):
28 prior expressions were multiplicative rank interactions (plus one spread).
The grammar's rank_spread class (rank(a) - rank(b)) removes the shared level
component and tests CONDITIONAL/differencing mechanisms, which no prior round
probed. This round is entirely spread-class; if these also fail, the two-atom
space within existing providers is exhausted and the next honest output is
MECHANISM_EXHAUSTED.

Novelty discipline: all six pairs are atom-level new (cumulative canonical
dedup vs rounds 001-004, v9 atomics, shelf keys); all mechanism names are new;
reused atoms are declared in the hypothesis field.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_005"

base.CANDIDATES = [
    {
        "id": "W1",
        "operator": "rank_spread",
        "left": {"name": "FIRST_HOUR_TURNOVER_SHARE", "source": "intraday_turnover_shape"},
        "right": {"name": "MORNING_VOL_SHARE", "source": "intraday_volatility_structure"},
        "mechanism": "participation_volatility_timing_gap",
        "hypothesis": "换手时点与波动时点之差度量开盘段的市场深度状态：早盘换手占比高而早盘波动占比低=大量参与被平稳吸收(有深度的知情承接)，短期延续；早盘波动占比高而换手占比低=稀薄订单簿上的无承接波动，回归。差值(spread)直接剥离两族共有的日内时间水平。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W2",
        "operator": "rank_spread",
        "left": {"name": "TURNOVER_CONCENTRATION", "source": "intraday_turnover_shape"},
        "right": {"name": "VOL_CONCENTRATION", "source": "intraday_volatility_structure"},
        "mechanism": "volume_vs_volatility_concentration_gap",
        "hypothesis": "成交集中度高于波动集中度=集中放量被平稳定价(机构大单执行、深度充足)，行情真实、延续；波动集中度高于成交集中度=少量资金在薄簿上制造价格冲击，事件噪声、回归。差值剥离'集中'这一共同水平，仅保留量/波不匹配的净信息。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W3",
        "operator": "rank_spread",
        "left": {"name": "PEER_LEAD_BETA_20", "source": "cross_etf_lead_lag"},
        "right": {"name": "MARKET_BETA_20", "source": "market_sensitivity"},
        "mechanism": "peer_minus_market_transmission",
        "hypothesis": "对peer的领先传导减去对市场的传导=组内信息传播强度(剥离整体市场敏感度后的净同类传导)。净同类传导高的品种由同类资金轮动驱动、行情独立于大盘指数，短期延续性来自组内信息扩散而非贝塔。与round_001 E6不同：E6是市场领先beta x 隔夜承接交互；此处是spread剥离后的组内-市场传导差。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W4",
        "operator": "rank_spread",
        "left": {"name": "CURRENT_DD_20", "source": "downside_risk"},
        "right": {"name": "CATEGORY_CURRENT_DD_20", "source": "category_state"},
        "mechanism": "idiosyncratic_drawdown_gap",
        "hypothesis": "自身回撤减去类别平均回撤=个体相对板块的回撤差：个体回撤浅于类别=相对强势(板块下跌时抗跌)，资金护盘真实、强者恒强延续；个体深于类别=自身负面事件(非板块贝塔)，修复慢。spread剥离板块共同回撤水平。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W5",
        "operator": "rank_spread",
        "left": {"name": "SESSION_MEAN_20", "source": "daily_candle"},
        "right": {"name": "RET_20", "source": "directional_trend"},
        "mechanism": "session_vs_total_drift_split",
        "hypothesis": "20日日内时段收益均值减去20日全日收益=把动量拆分为'交易时段漂移'与'隔夜跳空积累'：动量主要由日内时段贡献(差值高)时是交易时段持续买盘建仓，真实资金、短期延续；主要由隔夜贡献(差值低)时是隔夜事件一次性定价，易回吐。与round_002 R3不同：R3是波动时点x趋势方向交互；此处是session对全日动量的残差剥离(spread类)，且RET_20为复用原子、构造类不同。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W6",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_REALIZED_VOL", "source": "intraday_return_path"},
        "right": {"name": "REALIZED_VOL_20", "source": "downside_risk"},
        "mechanism": "intraday_vs_daily_vol_gap",
        "hypothesis": "日内已实现波动与20日日线波动之差=波动的时间尺度错位：日内相对波动升高(近期盘中活动加剧而长期波动未变)是分歧/事件驱动的状态转换早期，随后短期回归；差值为负(日内平静于长期水平)是低关注期。与round_001 E5不同：E5是尾部日减波动的'尾部净修复'；此处是同尺度日内-日线波动期限差。REALIZED_VOL_20为复用原子、构造类与机制不同。预期负方向。",
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
