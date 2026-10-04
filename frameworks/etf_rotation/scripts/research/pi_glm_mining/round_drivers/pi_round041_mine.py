#!/usr/bin/env python3
"""Round 041 driver: stage-8 round 1 (cross-ETF cojump + liquidity
commonality, literature-backed; stage-7 exhaustion archived, counter reset).
Six rank_spread pairs, each with >=1 cojump_1m/liquidity_commonality_1m leg
(all seven legs fresh at first use); pairs atom-level new; burnt legs
declared. Gate 7 v2.1; atoms leak-cached after health-run build."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_041"

base.CANDIDATES = [
    {
        "id": "U1",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "systematic_jump_up_structure",
        "hypothesis": "两腿角色：A=与 14 只等权指数同分钟共跳比例（Bollerslev–Law–Tauchen 2008；Jacod–Todorov 2009，系统性信息事件）；B=获利盘比例（成本结构）。假设：共跳比例高而获利盘高（信号高）=上行结构中的系统性信息事件，事件后延续；获利盘低（信号低）=下行结构中的系统性冲击，崩坏。声明：COJUMP_INDEX_SHARE_20 首次价差腿；PROFIT_RATIO_60(R1/S4)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U2",
        "operator": "rank_spread",
        "left": {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "idiosyncratic_jump_in_calm_category",
        "hypothesis": "两腿角色：A=特异跳跃份额（非共跳跳跃变差/总跳跃变差，Jacod–Todorov 2009，个体信息事件）；B=类别 20 日波动（环境噪声）。假设：特异跳跃份额高而类别平静（信号高）=跳跃源于个体信息而非环境噪声，延续；类别高波动（信号低）=跳跃被环境淹没。声明：IDIO_JUMP_SHARE_20 首次价差腿；CATEGORY_VOL_20(T4/Y3/N4)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U3",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"},
        "right": {"name": "CATEGORY_MOM_60", "source": "category_state"},
        "mechanism": "aligned_cojump_in_category_momentum",
        "hypothesis": "两腿角色：A=共跳方向一致度（与池同向共跳占比，方向性系统事件）；B=类别 60 日动量（顺风环境）。假设：共跳方向与池一致而类别动量强（信号高）=系统性上行共跳+顺风，事件后延续；方向不一致（信号低）=逆系统方向的孤立事件，回吐。声明：COJUMP_DIR_AGREE_20 首次价差腿；CATEGORY_MOM_60(T6/W4 条件腿)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U4",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "ULCER_60", "source": "downside_risk"},
        "mechanism": "liquidity_beta_healthy_structure",
        "hypothesis": "两腿角色：A=流动性共性 β（1m Amihud 变化对池均值变化的 20 日回归，Chordia–Roll–Subrahmanyam 2000；Karolyi–Lee–van Dijk 2012，系统性流动性敏感=配置盘特征）；B=60 日溃疡（慢性失血）。假设：共性 β 高而溃疡浅（信号高）=健康结构的系统性流动性敞口，延续；溃疡深（信号低）=流动性敏感是脆弱性。声明：LIQ_COMMON_BETA_20 首次价差腿；ULCER_60(Y1/Z4/K6/T5)第4次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "U5",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"},
        "mechanism": "resilient_low_impact",
        "hypothesis": "两腿角色：A=流动性回复力（1m 冲击后 5 分钟价格回复比例，Kyle–Obizhaeva 2016 意义上的 resiliency 代理）；B=Kyle λ 代理（单位净流冲击）。假设：回复力高而 λ 低（信号高）=低冲击且冲击快速被吸收的干净弹性微结构，延续；λ 高（信号低）=冲击持久不被吸收。声明：RESILIENCY_20 首次价差腿；KYLE_LAMBDA_20(N2/K3)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "U6",
        "operator": "rank_spread",
        "left": {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "SHARE_CHG_20", "source": "fund_flow"},
        "mechanism": "idio_liq_shock_absorbed",
        "hypothesis": "两腿角色：A=特异流动性冲击（Amihud 变化对池回归残差的 20 日 z，个体流动性事件）；B=份额 20 日变化率（一级配置流）。假设：特异冲击高而份额流入（信号高）=个体流动性事件被配置资金吸收（真金白银进场），延续；份额流出（信号低）=特异冲击无承接。声明：IDIO_LIQ_SHOCK_Z_20 首次价差腿；SHARE_CHG_20(X2/X5)第2次。预期正方向。",
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
