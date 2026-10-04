#!/usr/bin/env python3
"""Round 040 driver: stage-7 round 3. Entering streak: 2 consecutive gate-7
zero rounds (r038, r039) — a third triggers contract exhaustion. Six
rank_spread pairs, each with >=1 realized_measures_1m/intraday_periodicity
leg (second uses with fresh partners); all pairs atom-level new, all
mechanism names new. Gate 7 v2.1; all atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_040"

base.CANDIDATES = [
    {
        "id": "S1",
        "operator": "rank_spread",
        "left": {"name": "JV_RV_SHARE_20", "source": "realized_measures_1m"},
        "right": {"name": "SHARE_Z_60", "source": "fund_flow"},
        "mechanism": "jump_on_primary_inflow",
        "hypothesis": "两腿角色：A=跳跃变差份额（Barndorff-Nielsen & Shephard 2004，波动中的事件成分）；B=份额变化 z(60)（一级配置流强度）。假设：跳跃高而份额 z 高（信号高）=事件跳跃发生在配置资金进场中（知情事件驱动进场），延续；份额流出（信号低）=跳跃是失血事件。声明：JV_RV_SHARE_20(R1)第2次；SHARE_Z_60 首次价差腿。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "S2",
        "operator": "rank_spread",
        "left": {"name": "RS_MINUS_20", "source": "realized_measures_1m"},
        "right": {"name": "STREAK_DAYS", "source": "fund_flow"},
        "mechanism": "downside_absorbed_by_streak",
        "hypothesis": "两腿角色：A=下行半方差占优（Barndorff-Nielsen–Kinnebrock–Shephard 2010，日内下行动能）；B=连续净申购天数（一级承接）。假设：日内下行占优而连续净申购（信号高）=下行被一级持续承接（供给释放而非失血），修复延续；连续赎回（信号低）=下行无承接。声明：RS_MINUS_20(R2)第2次；STREAK_DAYS(T5/N3/K3/T2)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "S3",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "overnight_compensation_concentrated",
        "hypothesis": "两腿角色：A=隔夜-日内收益差（Lou–Polk–Skouras 2019，持有时段补偿）；B=90% 筹码区间宽度（筹码集中度）。假设：隔夜补偿强而筹码区间窄（信号高）=集中筹码的持有者收隔夜补偿（配置型持有），延续；筹码发散（信号低）=补偿结构无持有主体。声明：OVERNIGHT_INTRA_DIFF_20(R6)第2次；CHIP_RANGE_90_60(C3/T4)第3次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "S4",
        "operator": "rank_spread",
        "left": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "ushape_in_profit_structure",
        "hypothesis": "两腿角色：A=日内 U 形 RV 占比（开/收盘波动节律）；B=获利盘比例（成本结构）。假设：U 形节律强而获利盘高（信号高）=开收盘波动落在上升成本结构中（配置节律），延续；获利盘低（信号低）=节律波动是下跌结构的恐慌开收盘。声明：VOL_USHAPE_20(T2)第2次；PROFIT_RATIO_60(R1)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "S5",
        "operator": "rank_spread",
        "left": {"name": "TAIL30_BETA_FULL_20", "source": "intraday_periodicity"},
        "right": {"name": "PREMIUM", "source": "nav_premium"},
        "mechanism": "close_leadership_no_premium",
        "hypothesis": "两腿角色：A=尾 30 分钟对全日的 20 日回归 β（收盘段定调力）；B=折溢价（情绪透支）。假设：收盘定调强而溢价低（信号高）=二级自身收盘动量且无情绪透支，次日延续；溢价高（信号低）=定调是情绪推高的尾盘。声明：TAIL30_BETA_FULL_20(R5/T5)第3次；PREMIUM(X1/X3/N1/M6/R6)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "S6",
        "operator": "rank_spread",
        "left": {"name": "RSKEW_20", "source": "realized_measures_1m"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "secondary_skew_independence",
        "hypothesis": "两腿角色：A=已实现偏度（Amaya–Christoffersen–Jacobs–Vasquez 2015，日内不对称）；B=份额变化-收益相关（一级流解释力）。假设：日内右偏而一级流不解释价格（信号高）=二级自发的温和上行（非申赎映射），延续；一级解释力强（信号低）=偏度是申赎时点的机械产物。声明：RSKEW_20(R3)第2次；SHARE_RET_CORR_20(X6/M1/K4/R5)第4次。预期正方向。",
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
        "已实现测度/周期性原子只用 <=D 的完整交易日 1m bar；LM 跳跃 sigma 只用前一日 bar；"
        "泄漏门物理截断/扰动副本含基准文件；全部原子泄漏缓存命中"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_realized

if __name__ == "__main__":
    base.main()
