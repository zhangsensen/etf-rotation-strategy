#!/usr/bin/env python3
"""Round 051 driver: stage-9 round 2 (entering streak: 1 zero round, r050).
Deploys the one still-unused leg (GRANGER_IN_DEGREE_20) plus second uses of
peer/cross-dependence legs with fresh partners. Six rank_spread pairs, all
atom-level new, all mechanism names new. Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_051"

base.CANDIDATES = [
    {
        "id": "Q1",
        "operator": "rank_spread",
        "left": {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "peer_deviation_profit_reversal",
        "hypothesis": "两腿角色：A=对同伴篓子残差的 60 日累计 z（相对价值偏离，GGR 2006；Avellaneda–Lee 2010）；B=获利盘比例。假设：偏离 z 高而获利盘高（信号高）=盈利资产上的冲击性偏离（无基本面恶化），均值回复，反转；获利盘低（信号低）=偏离是基本面恶化的开始。声明：PEER_RESID_Z_20(P1)第2次；PROFIT_RATIO_60(R1/S4/U1/V5/W2/X5/Z1 入选)第8次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Q2",
        "operator": "rank_spread",
        "left": {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"},
        "right": {"name": "PRIMARY_SHARE_20", "source": "fund_flow"},
        "mechanism": "peer_deviation_secondary_widening",
        "hypothesis": "两腿角色：A=同伴残差 20 日动量（偏离仍在扩大）；B=一级市场量占比（申赎机械流）。假设：残差动量大而一级占比低（信号高）=二级自身的偏离扩大（个体行情真扩展），延续；一级占比高（信号低）=扩大是申赎映射。声明：PEER_RESID_MOM_20(P3)第2次；PRIMARY_SHARE_20(Y6/X4/M4/K1/R4/V1)第7次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Q3",
        "operator": "rank_spread",
        "left": {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"},
        "right": {"name": "CATEGORY_MOM_60", "source": "category_state"},
        "mechanism": "peer_deviation_tailwind_persistent",
        "hypothesis": "两腿角色：A=同伴残差的 OU 半衰期（偏离持续性，Avellaneda–Lee 2010 框架）；B=类别 60 日动量（顺风环境）。假设：半衰期长而类别动量强（信号高）=顺风环境中的持续偏离（重定价被环境确认），延续；逆风（信号低）=偏离将被环境拉回。声明：PEER_OU_HALFLIFE_20(P2)第2次；CATEGORY_MOM_60(T6/W4 条件腿)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Q4",
        "operator": "rank_spread",
        "left": {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "follower_absorbing_buyflow",
        "hypothesis": "两腿角色：A=Granger 网络入度（被多数同伴领先，Billio–Getmansky–Lo–Pelizzon 2012 代理，价格接受者）；B=1m tick-rule 主买不平衡（定向买流）。假设：入度高而主买不平衡高（信号高）=价格接受者在吸收定向买流（买流有追随者结构），延续；入度低（信号低）=买流是自身信息（不同机制）。声明：GRANGER_IN_DEGREE_20 首次价差腿；TICK_IMBALANCE_20(F1/T1/AC4)第4次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Q5",
        "operator": "rank_spread",
        "left": {"name": "GRANGER_OUT_DEGREE_20", "source": "cross_dependence_1m"},
        "right": {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"},
        "mechanism": "informed_leader",
        "hypothesis": "两腿角色：A=Granger 网络出度（领先同伴数量，价格发现者）；B=VPIN（知情交易概率，Easley–López de Prado–O'Hara 2012）。假设：出度高而 VPIN 高（信号高）=信息源头在知情资金处（领先性有信息含量），延续；VPIN 低（信号低）=领先性是流动性噪声。声明：GRANGER_OUT_DEGREE_20(P4)第2次；VPIN_CLOSE_20(N1/K1/AC5)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Q6",
        "operator": "rank_spread",
        "left": {"name": "NET_SPILLOVER_20", "source": "cross_dependence_1m"},
        "right": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "mechanism": "spillover_leader_profitable",
        "hypothesis": "两腿角色：A=净溢出（对池的滞后相关出-入差，Diebold–Yilmaz 2014 代理）；B=价格/平均成本−1（获利位置）。假设：净溢出为正而价格高于成本（信号高）=盈利资产上的方向信息源，延续；净溢出为负（信号低）=价格接受者。声明：NET_SPILLOVER_20(P5)第2次；PRICE_VS_AVGCOST_20(D1/V3/W4/X2/AA1)第7次。预期正方向。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage9(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage9_peer_relative_cross_dependence"
    plan["pit_note"] = (
        "同伴篓子（60 日相关 top-3）与 Granger 网络估计只用 <=D 的 bar/日数据，每日重定；"
        "PEER_RELSTR_Z_20 因 shadow（0.72 vs SESSION_MEAN_20）未入候选；"
        "泄漏门物理截断/扰动副本含基准与池内 1m 文件"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage9

if __name__ == "__main__":
    base.main()
