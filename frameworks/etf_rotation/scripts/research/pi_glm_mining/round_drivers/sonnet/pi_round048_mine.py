#!/usr/bin/env python3
"""Round 048 driver: stage-8 round 8 (entering streak: 1 zero round, r047).
Six rank_spread pairs, each with >=1 cojump_1m/liquidity_commonality_1m leg;
all pairs atom-level new, all mechanism names new; W3+Z1 admitted vectors in
the dedup reference set. Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_048"

base.CANDIDATES = [
    {
        "id": "AB1",
        "operator": "rank_spread",
        "left": {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "SHARE_Z_60", "source": "fund_flow"},
        "mechanism": "idio_jump_primary_inflow",
        "hypothesis": "两腿角色：A=特异跳跃份额（Jacod–Todorov 2009，个体信息事件）；B=份额变化 z(60)（一级配置流强度）。假设：特异跳跃高而份额 z 高（信号高）=个体信息事件伴随配置流入（知情与配置同向），延续；份额流出（信号低）=跳跃无承接。声明：IDIO_JUMP_SHARE_20(U2/V2/W4/X5/Y6/Z5)第7次；SHARE_Z_60(S1)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AB2",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "aligned_cojump_calm_category",
        "hypothesis": "两腿角色：A=共跳方向一致度（方向性系统事件）；B=类别 20 日波动（环境噪声）。假设：共跳同向高而类别平静（信号高）=系统性方向事件非类别噪声（池级信息确认），延续；类别高波动（信号低）=事件被环境噪声淹没。声明：COJUMP_DIR_AGREE_20(U3/V6/W2/Y1/Y5/AA6)第8次；CATEGORY_VOL_20(T4/Y3/N4/U2)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AB3",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "CATEGORY_MOM_60", "source": "category_state"},
        "mechanism": "resilient_tailwind_category",
        "hypothesis": "两腿角色：A=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）；B=类别 60 日动量（顺风环境）。假设：回复力高而类别动量强（信号高）=顺风环境中的弹性微结构（冲击逆风小），延续；逆风（信号低）=弹性被环境消耗。声明：RESILIENCY_20(U5/V4/X4，W3 已入选——本对与之不同腿)第7次；CATEGORY_MOM_60(T6/W4 条件腿)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AB4",
        "operator": "rank_spread",
        "left": {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "idio_shock_concentrated_orderly",
        "hypothesis": "两腿角色：A=特异流动性冲击（Amihud 残差 20 日 z，个体流动性事件）；B=90% 筹码区间宽度（筹码集中度）。假设：特异冲击高而筹码区间窄（信号高）=集中筹码中的个体事件（控盘有序），延续；筹码发散（信号低）=事件被分散持有者放大。声明：IDIO_LIQ_SHOCK_Z_20(U6/V5/X1/Y2/Z3)第7次；CHIP_RANGE_90_60(C3/T4/V3/Z5/AA3)第6次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "AB5",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "liq_beta_profit_assets",
        "hypothesis": "两腿角色：A=流动性共性 β（系统性流动性敏感，CRS 2000/KLvD 2012）；B=获利盘比例。假设：共性 β 高而获利盘高（信号高）=系统流动性敏感落在盈利资产（配置盘在盈利端提供流动性），延续；获利盘低（信号低）=敏感是脆弱性。声明：LIQ_COMMON_BETA_20(U4/W1/X2/Y3/Z2/AA4)第7次；PROFIT_RATIO_60(R1/S4/U1/V5/W2/X5/Z1 入选)第8次——去重门自动检验与 Z1 向量的相关。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AB6",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "PREMIUM_Z_20", "source": "nav_premium"},
        "mechanism": "cojump_no_sentiment",
        "hypothesis": "两腿角色：A=与池指数同分钟共跳比例（系统性信息事件）；B=折溢价 20 日 z（情绪透支）。假设：共跳高而溢价 z 低（信号高）=系统性事件无情绪透支（信息定价干净），延续；溢价 z 高（信号低）=事件叠加情绪透支。声明：COJUMP_INDEX_SHARE_20(U1/V3/W6/X3/Z4/AA5)第7次；PREMIUM_Z_20(N5/K2/T6/V4)第5次。预期负方向。",
        "expected_sign": -1,
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
