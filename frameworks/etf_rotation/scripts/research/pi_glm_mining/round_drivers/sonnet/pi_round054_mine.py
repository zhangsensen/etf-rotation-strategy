#!/usr/bin/env python3
"""Round 054 driver: continuing under the stage-9 frame (peer relative value
+ cross dependence) after the master rejected the r053 exhaustion claim.
Counter: consecutive zero rounds since the last admission (r053's seven
atomic admissions) = 0. Six rank_spread pairs, each with >=1 stage-9 leg;
all pairs atom-level new, all mechanism names new. Gate 7 v2.1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_054"

base.CANDIDATES = [
    {
        "id": "AD1",
        "operator": "rank_spread",
        "left": {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"},
        "right": {"name": "ULCER_60", "source": "downside_risk"},
        "mechanism": "granger_follower_healthy_structure",
        "hypothesis": "两腿角色：A=Granger 网络入度（被多数同伴领先，价格接受者，BGLP 2012 代理）；B=60 日溃疡（慢性失血）。假设：入度高而溃疡浅（信号高）=健康结构中的稳定跟随者（接受价格但结构无恙），延续；溃疡深（信号低）=跟随者承受失血。声明：GRANGER_IN_DEGREE_20(Q4)第3次；ULCER_60(Y1/Z4/K6/T5/W6)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AD2",
        "operator": "rank_spread",
        "left": {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "deviation_widening_on_buyflow",
        "hypothesis": "两腿角色：A=同伴残差 20 日动量（偏离扩大中）；B=1m tick-rule 主买不平衡（定向买流）。假设：偏离扩大而主买不平衡高（信号高）=扩大由定向买流推动（资金支持的偏离），延续；买流弱（信号低）=扩大无资金支持。声明：PEER_RESID_MOM_20(P3/Q2)第4次；TICK_IMBALANCE_20(F1/T1/AC4/Q4)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AD3",
        "operator": "rank_spread",
        "left": {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"},
        "right": {"name": "CATEGORY_MOM_60", "source": "category_state"},
        "mechanism": "decoupling_with_category_tailwind",
        "hypothesis": "两腿角色：A=与等权池 1m 相关性的 20 日变化（依赖度漂移）；B=类别 60 日动量（顺风环境）。假设：依赖度下降而类别动量强（信号高）=独立行情启动且顺风（脱钩有环境支持），延续；逆风（信号低）=脱钩被环境压制。声明：DEP_DRIFT_20(P6/R5)第3次；CATEGORY_MOM_60(U3/AB3 条件腿)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AD4",
        "operator": "rank_spread",
        "left": {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "persistent_deviation_not_primary",
        "hypothesis": "两腿角色：A=同伴残差的 OU 半衰期（偏离持续性，Avellaneda–Lee 2010 框架）；B=份额变化-收益相关（一级流解释力）。假设：半衰期长而一级流不解释价格（信号高）=持续偏离非申赎映射（结构性重定价），延续；一级解释力强（信号低）=偏离是申赎机械产物。声明：PEER_OU_HALFLIFE_20(P2/Q3)第4次；SHARE_RET_CORR_20(X6/M1/K4/R5/Y3/W3 入选)第7次——去重门自动检验与 W3 向量的相关。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AD5",
        "operator": "rank_spread",
        "left": {"name": "NET_SPILLOVER_20", "source": "cross_dependence_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "spillover_concentrated_control",
        "hypothesis": "两腿角色：A=净溢出（对池的滞后相关出-入差，Diebold–Yilmaz 2014 代理，方向信息源）；B=90% 筹码区间宽度（筹码集中度）。假设：净溢出为正而筹码集中（信号高）=控盘资金的方向信息源（溢出有主体），延续；筹码发散（信号低）=溢出无主体。声明：NET_SPILLOVER_20(P5/Q6/R4)第4次；CHIP_RANGE_90_60(C3/T4/V3/Z5/AA3)第7次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AD6",
        "operator": "rank_spread",
        "left": {"name": "GRANGER_OUT_DEGREE_20", "source": "cross_dependence_1m"},
        "right": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "mechanism": "leader_profitable_pricing",
        "hypothesis": "两腿角色：A=Granger 网络出度（价格发现者，BGLP 2012 代理）；B=价格/平均成本−1（获利位置）。假设：出度高而价格高于成本（信号高）=价格发现者在获利资产上（信息源有持仓回报），延续；亏损位置（信号低）=领先性无持仓回报支持。声明：GRANGER_OUT_DEGREE_20(P4/Q5/R1)第4次；PRICE_VS_AVGCOST_20(D1/V3/W4/X2/AA1)第8次。预期正方向。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage9(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage9_peer_relative_cross_dependence_continued"
    plan["pit_note"] = (
        "同伴篓子（60 日相关 top-3）与 Granger 网络估计只用 <=D 的 bar/日数据，每日重定；"
        "W3/Z1 与 r053 七个 atomic 入选向量均进入去重参照集"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage9

if __name__ == "__main__":
    base.main()
