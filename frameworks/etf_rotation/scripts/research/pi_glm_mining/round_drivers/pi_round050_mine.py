#!/usr/bin/env python3
"""Round 050 driver: stage-9 round 1 (peer relative value + cross-ETF
dependence, literature-backed; stage-8 exhaustion archived, counter reset).
Six rank_spread pairs, each with >=1 leg from the two new families; all
pairs atom-level new; burnt legs declared; PEER_RELSTR_Z_20 shadow-excluded.
Gate 7 v2.1; atoms leak-cached after health-run build."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_050"

base.CANDIDATES = [
    {
        "id": "P1",
        "operator": "rank_spread",
        "left": {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "peer_deviation_resilient_reversal",
        "hypothesis": "两腿角色：A=对同伴篓子回归残差的 60 日累计 z（相对价值偏离，Gatev–Goetzmann–Rouwenhorst 2006；Avellaneda–Lee 2010）；B=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）。假设：偏离 z 高而回复力高（信号高）=偏离被高弹性微结构定价（冲击性偏离），将均值回复，反转；回复力低（信号低）=偏离是结构性重定价。声明：PEER_RESID_Z_20 首次价差腿；RESILIENCY_20(U5/V4/X4/AB3/Z1 入选)第6次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "P2",
        "operator": "rank_spread",
        "left": {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"},
        "right": {"name": "ULCER_60", "source": "downside_risk"},
        "mechanism": "persistent_deviation_healthy_structure",
        "hypothesis": "两腿角色：A=同伴残差的 OU 半衰期（均值回复速度的倒数，Avellaneda–Lee 2010 框架）；B=60 日溃疡（慢性失血）。假设：半衰期长而溃疡浅（信号高）=健康结构中的持续性偏离=结构性重定价（非失血），延续；溃疡深（信号低）=偏离伴随失血。声明：PEER_OU_HALFLIFE_20 首次价差腿；ULCER_60(Y1/Z4/K6/T5/W6)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "P3",
        "operator": "rank_spread",
        "left": {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"},
        "right": {"name": "CATEGORY_DISPERSION_20", "source": "category_state"},
        "mechanism": "peer_deviation_dispersion_confirmed",
        "hypothesis": "两腿角色：A=同伴残差 20 日动量（偏离是否仍在扩大）；B=类别 20 日分化（个体行情强度）。假设：残差动量大而类别分化大（信号高）=个体偏离被类别分化确认（真个体行情），延续；分化小（信号低）=偏离是噪声。声明：PEER_RESID_MOM_20 首次价差腿；CATEGORY_DISPERSION_20(B3/W3 条件腿+W5)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "P4",
        "operator": "rank_spread",
        "left": {"name": "GRANGER_OUT_DEGREE_20", "source": "cross_dependence_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "granger_leader_in_calm_category",
        "hypothesis": "两腿角色：A=Granger 网络出度（1m 滞后 1 拍相关网络中领先同伴的数量，Billio–Getmansky–Lo–Pelizzon 2012 代理）；B=类别 20 日波动（环境噪声）。假设：出度高而类别平静（信号高）=领先性来自自身信息（价格发现者），延续；类别高波动（信号低）=领先性被环境噪声淹没。声明：GRANGER_OUT_DEGREE_20 首次价差腿；CATEGORY_VOL_20(T4/Y3/N4/U2)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "P5",
        "operator": "rank_spread",
        "left": {"name": "NET_SPILLOVER_20", "source": "cross_dependence_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "net_spillover_profit_leader",
        "hypothesis": "两腿角色：A=净溢出（对池的滞后相关出-入差，Diebold–Yilmaz 2014 方向性溢出代理）；B=获利盘比例。假设：净溢出为正而获利盘高（信号高）=盈利资产上的价格发现者（方向信息源），延续；净溢出为负（信号低）=被领先的价格接受者。声明：NET_SPILLOVER_20 首次价差腿；PROFIT_RATIO_60(R1/S4/U1/V5/W2/X5/Z1 入选)第7次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "P6",
        "operator": "rank_spread",
        "left": {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "decoupling_not_primary_driven",
        "hypothesis": "两腿角色：A=对 14 只等权 1m 收益相关性的 20 日变化（依赖度漂移）；B=份额变化-收益相关（一级流解释力）。假设：依赖度下降而一级流不解释价格（信号高）=与池脱钩且非申赎映射（独立行情启动），延续；一级流主导（信号低）=脱钩是申赎冲击的假象。声明：DEP_DRIFT_20 首次价差腿；SHARE_RET_CORR_20(X6/M1/K4/R5/W3 入选/Y3)第6次——去重门自动检验与 W3 向量的相关。预期正方向。",
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
