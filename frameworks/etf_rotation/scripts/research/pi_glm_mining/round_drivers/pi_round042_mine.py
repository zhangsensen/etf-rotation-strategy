#!/usr/bin/env python3
"""Round 042 driver: stage-8 round 2 (entering streak: 1 zero round, r041).
Deploys the one still-unused leg (LIQ_COMMON_R2_20) plus second uses of the
other cojump/liquidity-commonality legs with fresh partners. Six rank_spread
pairs, all atom-level new, all mechanism names new. Gate 7 v2.1; atoms
leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_042"

base.CANDIDATES = [
    {
        "id": "V1",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "PRIMARY_SHARE_20", "source": "fund_flow"},
        "mechanism": "systematic_liquidity_not_primary",
        "hypothesis": "两腿角色：A=流动性共性 R²（1m Amihud 变化对池均值回归的拟合优度，Chordia–Roll–Subrahmanyam 2000；Karolyi–Lee–van Dijk 2012，系统性流动性驱动）；B=一级市场量占比（申赎机械流）。假设：共性 R² 高而一级占比低（信号高）=流动性变动由系统性因子驱动（配置盘特征），延续；一级占比高（信号低）=流动性变动是申赎机械映射。声明：LIQ_COMMON_R2_20 首次价差腿；PRIMARY_SHARE_20(Y6/X4/M4/K1/R4)第5次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "V2",
        "operator": "rank_spread",
        "left": {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "idio_jump_disciplined_rhythm",
        "hypothesis": "两腿角色：A=特异跳跃份额（Jacod–Todorov 2009，个体信息事件）；B=日内量分布熵（量的时间均匀度）。假设：特异跳跃高而量熵低（信号高）=量集中于固定节奏中的个体事件（机构信息执行），延续；量熵高（信号低）=跳跃被散户噪声稀释。声明：IDIO_JUMP_SHARE_20(U2)第2次；VOL_ENTROPY_20(AA1/AA5/M5)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "V3",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "mechanism": "cojump_profitable_position",
        "hypothesis": "两腿角色：A=与池指数同分钟共跳比例（系统性信息事件，Bollerslev–Law–Tauchen 2008）；B=价格/平均成本−1（获利位置）。假设：共跳高而价格高于成本（信号高）=系统性事件落在获利结构中（多头事件的确认），延续；价格低于成本（信号低）=事件冲击套牢结构，崩坏。声明：COJUMP_INDEX_SHARE_20(U1)第2次；PRICE_VS_AVGCOST_20(D1)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "V4",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "PREMIUM_Z_20", "source": "nav_premium"},
        "mechanism": "resilient_no_overhang",
        "hypothesis": "两腿角色：A=流动性回复力（冲击后 5 分钟回复比例，Kyle–Obizhaeva 2016 代理）；B=折溢价 20 日 z（情绪透支）。假设：回复力高而溢价 z 低（信号高）=弹性微结构且无情绪透支，冲击快速消化，延续；溢价 z 高（信号低）=弹性被情绪消耗。声明：RESILIENCY_20(U5)第2次；PREMIUM_Z_20(N5/K2/T6)第3次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "V5",
        "operator": "rank_spread",
        "left": {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "idio_shock_profitable_absorption",
        "hypothesis": "两腿角色：A=特异流动性冲击（Amihud 残差 20 日 z，个体流动性事件）；B=获利盘比例。假设：特异冲击高而获利盘高（信号高）=上升结构中的个体流动性事件（有序获利了结），延续；获利盘低（信号低）=冲击是下跌结构的失血。声明：IDIO_LIQ_SHOCK_Z_20(U6)第2次；PROFIT_RATIO_60(R1/S4/U1)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "V6",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"},
        "right": {"name": "SHARE_CHG_20", "source": "fund_flow"},
        "mechanism": "aligned_cojump_primary_confirm",
        "hypothesis": "两腿角色：A=共跳方向一致度（与池同向共跳占比，方向性系统事件）；B=份额 20 日变化率（一级配置流）。假设：共跳同向高而份额流入（信号高）=系统性方向事件被一级确认（真金白银同向），延续；份额流出（信号低）=同向事件无一级确认。声明：COJUMP_DIR_AGREE_20(U3)第2次；SHARE_CHG_20(X2/X5/U6)第3次。预期正方向。",
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
        "池=14 只候选等权；泄漏门物理截断/扰动副本含基准与池内 1m 文件"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_cojump

if __name__ == "__main__":
    base.main()
