#!/usr/bin/env python3
"""Round 049 driver: stage-8 round 9. Entering streak: 2 consecutive gate-7
zero rounds (r047, r048) — a third triggers contract exhaustion. Six
rank_spread pairs, each with >=1 cojump_1m/liquidity_commonality_1m leg; all
pairs atom-level new, all mechanism names new; W3+Z1 admitted vectors in the
dedup reference set. Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_049"

base.CANDIDATES = [
    {
        "id": "AC1",
        "operator": "rank_spread",
        "left": {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "CATEGORY_BREADTH_MA20", "source": "category_state"},
        "mechanism": "idio_jump_in_broad_market",
        "hypothesis": "两腿角色：A=特异跳跃份额（Jacod–Todorov 2009，个体信息事件）；B=类别 20 日广度（普涨环境）。假设：特异跳跃高而广度高（信号高）=普涨环境中的个体信息事件（选股型事件），延续；广度低（信号低）=事件是普跌中的孤立挣扎。声明：IDIO_JUMP_SHARE_20(U2/V2/W4/X5/Y6/Z5/AB1)第8次；CATEGORY_BREADTH_MA20(B2/B5 条件腿)首次价差腿。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AC2",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"},
        "mechanism": "common_liq_low_impact",
        "hypothesis": "两腿角色：A=流动性共性 β（系统性流动性敏感，CRS 2000/KLvD 2012）；B=Kyle λ 代理（单位净流冲击，Kyle 1985/Hasbrouck 2009）。假设：共性 β 高而 λ 低（信号高）=系统性流动性敏感+低冲击（大盘成熟配置标的），延续；λ 高（信号低）=敏感叠加脆弱。声明：LIQ_COMMON_BETA_20(U4/W1/X2/Y3/Z2/AA4/AB5)第8次；KYLE_LAMBDA_20(N2/K3/U5)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AC3",
        "operator": "rank_spread",
        "left": {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "idio_shock_not_open_mechanics",
        "hypothesis": "两腿角色：A=特异流动性冲击（Amihud 残差 20 日 z，个体流动性事件）；B=开盘 30 分钟量占比（开盘集中机制）。假设：特异冲击高而开盘占比低（信号高）=个体事件非开盘集中机制（盘中真实流动性事件），延续；开盘集中（信号低）=事件是开盘机制的机械产物。声明：IDIO_LIQ_SHOCK_Z_20(U6/V5/X1/Y2/Z3/AB4)第8次；OPEN30_VOL_SHARE_20(F1 左腿)第2次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "AC4",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "resilient_buy_pressure",
        "hypothesis": "两腿角色：A=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）；B=1m tick-rule 主买不平衡（定向买流）。假设：回复力高而主买不平衡高（信号高）=定向买流被快速吸收回复（健康买压），延续；回复力低（信号低）=买流造成持久冲击。声明：RESILIENCY_20(U5/V4/X4/AB3，Z1 已入选——本对与之不同腿)第8次；TICK_IMBALANCE_20(F1 左腿/T1)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AC5",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"},
        "mechanism": "common_liq_informed",
        "hypothesis": "两腿角色：A=流动性共性 R²（系统性流动性解释力）；B=VPIN（知情交易概率，Easley–López de Prado–O'Hara 2012）。假设：共性 R² 高而 VPIN 高（信号高）=知情交易发生在系统流动性层面（池级信息），延续；VPIN 低（信号低）=共性定价无信息内容。声明：LIQ_COMMON_R2_20(V1/W5/X6/Y4/AA2)第6次；VPIN_CLOSE_20(N1/K1)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AC6",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "RS_MINUS_20", "source": "realized_measures_1m"},
        "mechanism": "cojump_downside_recovery",
        "hypothesis": "两腿角色：A=与池指数同分钟共跳比例（系统性信息事件）；B=下行半方差占优（BNKS 2010，日内下行动能）。假设：共跳高而下行占优（信号高）=系统性事件的下行侧（恐慌共跳后修复），修复延续；上行占优（信号低）=共跳是上行事件（不同机制）。声明：COJUMP_INDEX_SHARE_20(U1/V3/W6/X3/Z4/AA5/AB6)第8次；RS_MINUS_20(R2/S2)第3次。预期正方向。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_cojump(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage8_cojump_liquidity_commonality"
    plan["pit_note"] = (
        "共跳/流动性共性原子只用 <=D 的完整交易日 1m bar；跳跃 sigma 只用前一日 bar；"
        "池=14 只候选等权；泄漏门物理截断/扰动副本含基准与池内 1m 文件；"
        "W3/Z1 已入选，其向量进入去重参照集"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_cojump

if __name__ == "__main__":
    base.main()
