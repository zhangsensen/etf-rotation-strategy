#!/usr/bin/env python3
"""Round 052 driver: stage-9 round 3. Entering streak: 2 consecutive gate-7
zero rounds (r050, r051) — a third triggers contract exhaustion. Six
rank_spread pairs, each with >=1 peer_relative_value/cross_dependence_1m leg
(second/third uses, fresh partners); all pairs atom-level new, all mechanism
names new. Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_052"

base.CANDIDATES = [
    {
        "id": "R1",
        "operator": "rank_spread",
        "left": {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"},
        "right": {"name": "GRANGER_OUT_DEGREE_20", "source": "cross_dependence_1m"},
        "mechanism": "leader_deviation_informational",
        "hypothesis": "两腿角色：A=对同伴篓子残差的 60 日累计 z（相对价值偏离，GGR 2006；Avellaneda–Lee 2010）；B=Granger 网络出度（价格发现者，BGLP 2012 代理）。假设：偏离由出度高者做出（信号高）=信息型偏离（将被定价而非回复），偏离方向延续；出度低者（信号低）的偏离是噪声，回复。声明：PEER_RESID_Z_20(P1/Q1)第3次；GRANGER_OUT_DEGREE_20(P4/Q5)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R2",
        "operator": "rank_spread",
        "left": {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"},
        "right": {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"},
        "mechanism": "informed_deviation_widening",
        "hypothesis": "两腿角色：A=同伴残差 20 日动量（偏离扩大中）；B=VPIN（知情交易概率，Easley–López de Prado–O'Hara 2012）。假设：偏离扩大而 VPIN 高（信号高）=知情驱动的偏离扩大，延续；VPIN 低（信号低）=扩大是流动性噪声。声明：PEER_RESID_MOM_20(P3/Q2)第3次；VPIN_CLOSE_20(N1/K1/AC5)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R3",
        "operator": "rank_spread",
        "left": {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "follower_profit_structure",
        "hypothesis": "两腿角色：A=Granger 网络入度（被多数同伴领先，价格接受者，BGLP 2012 代理）；B=获利盘比例。假设：入度高而获利盘高（信号高）=盈利资产上的稳定跟随结构（跟随成本最低），延续；获利盘低（信号低）=跟随结构不稳。声明：GRANGER_IN_DEGREE_20(Q4)第2次；PROFIT_RATIO_60(R1/S4/U1/V5/W2/X5/Q1/Z1 入选)第9次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R4",
        "operator": "rank_spread",
        "left": {"name": "NET_SPILLOVER_20", "source": "cross_dependence_1m"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "spillover_source_disciplined",
        "hypothesis": "两腿角色：A=净溢出（对池的滞后相关出-入差，Diebold–Yilmaz 2014 代理）；B=日内量分布熵（量的时间均匀度）。假设：净溢出为正而量熵低（信号高）=集中执行节奏中的方向信息源（机构化领先），延续；量熵高（信号低）=溢出是噪声外溢。声明：NET_SPILLOVER_20(P5/Q6)第3次；VOL_ENTROPY_20(AA1/AA5/M5/X3/Y2)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R5",
        "operator": "rank_spread",
        "left": {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"},
        "right": {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"},
        "mechanism": "decoupling_with_information",
        "hypothesis": "两腿角色：A=与等权池 1m 相关性的 20 日变化（依赖度漂移）；B=VPIN（知情交易概率）。假设：依赖度下降而 VPIN 高（信号高）=脱钩伴随知情集中（独立信息行情），延续；VPIN 低（信号低）=脱钩无信息内容。声明：DEP_DRIFT_20(P6)第2次；VPIN_CLOSE_20(N1/K1/AC5/R2)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R6",
        "operator": "rank_spread",
        "left": {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "deviation_on_buyflow",
        "hypothesis": "两腿角色：A=对同伴篓子残差的 60 日累计 z（相对价值偏离）；B=1m tick-rule 主买不平衡（定向买流）。假设：偏离 z 高而主买不平衡高（信号高）=偏离由定向买流推动（知情偏离），延续；主买弱（信号低）=偏离无资金支持。声明：PEER_RESID_Z_20(P1/Q1/R1)第4次；TICK_IMBALANCE_20(F1/T1/AC4/Q4)第5次。预期正方向。",
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
