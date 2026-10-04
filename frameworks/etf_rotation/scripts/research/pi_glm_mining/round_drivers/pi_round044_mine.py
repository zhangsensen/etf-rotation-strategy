#!/usr/bin/env python3
"""Round 044 driver: stage-8 round 4 (W3 admitted in r043, streak = 0).
Six rank_spread pairs, each with >=1 cojump_1m/liquidity_commonality_1m leg
(second/third uses, fresh partners); all pairs atom-level new, all mechanism
names new. W3 (RESILIENCY_20 x SHARE_RET_CORR_20) is now an admitted
reference vector — the dedup gate tests every new candidate against it.
Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_044"

base.CANDIDATES = [
    {
        "id": "X1",
        "operator": "rank_spread",
        "left": {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "STREAK_DAYS", "source": "fund_flow"},
        "mechanism": "idio_liq_shock_absorbed_by_streak",
        "hypothesis": "两腿角色：A=特异流动性冲击（Amihud 变化对池回归残差的 20 日 z，个体流动性事件）；B=连续净申购天数（一级承接方向）。假设：特异冲击高而连续净申购（信号高）=个体流动性事件被一级持续承接，事件后延续；连续赎回（信号低）=冲击无承接放大失血。声明：IDIO_LIQ_SHOCK_Z_20(U6/V5)第3次；STREAK_DAYS(T5/N3/K3/T2/S2)第5次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "X2",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "mechanism": "liq_beta_profitable_position",
        "hypothesis": "两腿角色：A=流动性共性 β（系统性流动性敏感，CRS 2000/KLvD 2012）；B=价格/平均成本−1（获利位置）。假设：共性 β 高而价格高于成本（信号高）=系统流动性敏感落在获利定位（配置盘在盈利资产上），延续；亏损位置（信号低）=敏感是脆弱性。声明：LIQ_COMMON_BETA_20(U4/W1)第3次；PRICE_VS_AVGCOST_20(D1/V3/W4)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X3",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "cojump_disciplined_rhythm",
        "hypothesis": "两腿角色：A=与池指数同分钟共跳比例（系统性信息事件）；B=日内量分布熵（量的时间均匀度）。假设：共跳高而量熵低（信号高）=系统性事件落在集中执行节奏中（机构化执行），事件后延续；量熵高（信号低）=共跳被散户噪声打散。声明：COJUMP_INDEX_SHARE_20(U1/V3/W6)第4次；VOL_ENTROPY_20(AA1/AA5/M5)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X4",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "CATEGORY_DISPERSION_20", "source": "category_state"},
        "mechanism": "resilient_consensus_category",
        "hypothesis": "两腿角色：A=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）；B=类别 20 日分化（个体行情强度）。假设：回复力高而类别分化小（信号高）=共识环境中的弹性微结构（无个体行情扰动），延续；分化大（信号低）=弹性被个体行情打破。声明：RESILIENCY_20(U5/V4，注意 W3 已入选——本对与之不同腿，去重门自动检验)第4次；CATEGORY_DISPERSION_20(W3/B3 条件腿+W5)第3次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "X5",
        "operator": "rank_spread",
        "left": {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "idio_jump_profit_structure",
        "hypothesis": "两腿角色：A=特异跳跃份额（Jacod–Todorov 2009，个体信息事件）；B=获利盘比例（成本结构）。假设：特异跳跃高而获利盘高（信号高）=获利结构中的个体信息事件（知情资金在盈利资产上定向进场），延续；获利盘低（信号低）=个体跳跃是坏消息。声明：IDIO_JUMP_SHARE_20(U2/V2/W4)第4次；PROFIT_RATIO_60(R1/S4/U1/V5/W2)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X6",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "common_liquidity_secondary_pricing",
        "hypothesis": "两腿角色：A=流动性共性 R²（系统性流动性解释力）；B=份额变化-收益相关（一级流解释力）。假设：共性 R² 高而一级流不解释价格（信号高）=定价由系统性流动性主导而非申赎映射（价格发现真实），延续；一级解释力强（信号低）=价格是申赎的机械产物。声明：LIQ_COMMON_R2_20(V1/W5)第3次；SHARE_RET_CORR_20(X6/M1/K4/R5，注意 W3 已入选——本对与之不同腿，去重门自动检验)第6次。预期正方向。",
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
        "W3(RESILIENCY x SHARE_RET_CORR) 已入选，其向量进入去重参照集"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_cojump

if __name__ == "__main__":
    base.main()
