#!/usr/bin/env python3
"""Round 038 driver: stage-7 round 1 (realized measures 1m + intraday
periodicity, literature-backed; stage-6 exhaustion archived, counter reset).
Six rank_spread pairs, each with >=1 leg from the two new families; all
pairs atom-level new; burnt legs declared. LM_JUMP_COUNT_20 excluded
(32 valid discovery days < gate minimum). Gate 7 v2.1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_038"

base.CANDIDATES = [
    {
        "id": "R1",
        "operator": "rank_spread",
        "left": {"name": "JV_RV_SHARE_20", "source": "realized_measures_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "jump_with_profit_structure",
        "hypothesis": "两腿角色：A=跳跃变差份额 JV/RV（Barndorff-Nielsen & Shephard 2004，波动中的跳跃成分）；B=获利盘比例（成本结构）。假设：跳跃份额高而获利盘高（信号高）=上升成本结构中的信息跳跃（好消息跳跃），跳跃后延续；获利盘低（信号低）=下跌结构中的跳跃，崩坏。声明：JV_RV_SHARE_20 首次价差腿；PROFIT_RATIO_60(C4-030 等条件化)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R2",
        "operator": "rank_spread",
        "left": {"name": "RS_MINUS_20", "source": "realized_measures_1m"},
        "right": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "mechanism": "downside_vol_open_overhead",
        "hypothesis": "两腿角色：A=已实现半方差之差 RS⁺−RS⁻（Barndorff-Nielsen–Kinnebrock–Shephard 2010，下行动能）；B=上方套牢厚度。假设：下行半方差占优而套牢薄（信号高）=日内下行是波动吸收、上方无套牢封顶，上行空间打开，修复延续；套牢厚（信号低）=下行叠加结构性抛压。声明：RS_MINUS_20 首次价差腿；OVERHAND_THICKNESS_60(D2/D3/E1/AA1/AA2/N6)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R3",
        "operator": "rank_spread",
        "left": {"name": "RSKEW_20", "source": "realized_measures_1m"},
        "right": {"name": "TAIL_Q10_20", "source": "return_tail_shape"},
        "mechanism": "positive_intraday_skew_clean_tail",
        "hypothesis": "两腿角色：A=已实现偏度（Amaya–Christoffersen–Jacobs–Vasquez 2015，日内不对称）；B=日线左尾深度。假设：日内右偏而左尾浅（信号高）=温和上行的日内结构且无尾部损伤，延续；日内左偏（信号低）=日内下行动能。声明：RSKEW_20 首次价差腿；TAIL_Q10_20(S2/BB6/X5/M2)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R4",
        "operator": "rank_spread",
        "left": {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"},
        "right": {"name": "PRIMARY_SHARE_20", "source": "fund_flow"},
        "mechanism": "slot_rhythm_secondary",
        "hypothesis": "两腿角色：A=同时段收益持续性（Heston–Korajczyk–Sadka 2010，日内节奏记忆）；B=一级市场量占比。假设：时段节奏持续而一级占比低（信号高）=节奏是二级自身机构执行（可预测的日内配置盘），延续；一级占比高（信号低）=节奏是申赎冲击的机械模式。声明：HKS_SLOT_PERSIST_20 首次价差腿；PRIMARY_SHARE_20(Y6/X4/M4/K1)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R5",
        "operator": "rank_spread",
        "left": {"name": "TAIL30_BETA_FULL_20", "source": "intraday_periodicity"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "tail_sets_day_secondary",
        "hypothesis": "两腿角色：A=尾 30 分钟收益对全日收益的 20 日回归 β（收盘段定调力）；B=份额变化-收益相关（一级流解释力）。假设：收盘段定调强而一级流不解释价格（信号高）=收盘动量由二级自身产生（次日延续的定调盘），延续；一级解释力强（信号低）=定调是申赎映射。声明：TAIL30_BETA_FULL_20 首次价差腿；SHARE_RET_CORR_20(X6/M1/K4)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R6",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"},
        "right": {"name": "PREMIUM", "source": "nav_premium"},
        "mechanism": "overnight_compensation_no_premium",
        "hypothesis": "两腿角色：A=隔夜-日内收益 20 日均值差（Lou–Polk–Skouras 2019，持有时段补偿结构）；B=折溢价（情绪透支）。假设：隔夜强于日内而溢价低（信号高）=持有补偿结构健康且无情绪透支，隔夜持有者被合理补偿，延续；溢价高（信号低）=日内情绪推高透支隔夜补偿。声明：OVERNIGHT_INTRA_DIFF_20 首次价差腿（体检 0.61 vs GAP_MEAN_20，未 shadow）；PREMIUM(X1/X3/N1/M6)第4次。预期正方向。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_realized(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage7_realized_measures_periodicity"
    plan["pit_note"] = (
        "已实现测度原子只用 <=D 的完整交易日 1m bar；LM 跳跃 sigma 只用前一日 bar（PIT）；"
        "泄漏门物理截断/扰动副本含基准文件；LM_JUMP_COUNT_20 因有效日不足未入候选"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_realized

if __name__ == "__main__":
    base.main()
