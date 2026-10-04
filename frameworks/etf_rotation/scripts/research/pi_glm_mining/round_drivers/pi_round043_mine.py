#!/usr/bin/env python3
"""Round 043 driver: stage-8 round 3. Entering streak: 2 consecutive gate-7
zero rounds (r041, r042) — a third triggers contract exhaustion. Six
rank_spread pairs, each with >=1 cojump_1m/liquidity_commonality_1m leg
(second/third uses, fresh partners); all pairs atom-level new, all mechanism
names new. Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_043"

base.CANDIDATES = [
    {
        "id": "W1",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "STREAK_DAYS", "source": "fund_flow"},
        "mechanism": "liquidity_beta_primary_streak",
        "hypothesis": "两腿角色：A=流动性共性 β（Amihud 变化对池均值的 20 日回归，CRS 2000/KLvD 2012，系统性流动性敏感）；B=连续净申购天数（一级承接方向）。假设：共性 β 高而连续净申购（信号高）=申赎对系统流动性敏感（配置盘而非噪声盘），延续；连续赎回（信号低）=敏感盘在失血中放大波动。声明：LIQ_COMMON_BETA_20(U4)第2次；STREAK_DAYS(T5/N3/K3/T2/S2)第5次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "W2",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "aligned_cojump_profit_structure",
        "hypothesis": "两腿角色：A=共跳方向一致度（与池同向共跳占比，方向性系统事件）；B=获利盘比例。假设：共跳同向高而获利盘高（信号高）=上行结构中的系统性共跳（全市场信息同向确认），延续；获利盘低（信号低）=共跳是下跌结构中的系统性出逃。声明：COJUMP_DIR_AGREE_20(U3/V6)第3次；PROFIT_RATIO_60(R1/S4/U1/V5)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W3",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "resilient_secondary_independence",
        "hypothesis": "两腿角色：A=流动性回复力（冲击后 5 分钟回复比例，Kyle–Obizhaeva 2016 代理）；B=份额变化-收益相关（一级流解释力）。假设：回复力高而一级流不解释价格（信号高）=弹性来自二级自身的流动性供给（做市/配置盘），延续；一级解释力强（信号低）=回复是申赎回补的假象。声明：RESILIENCY_20(U5/V4)第3次；SHARE_RET_CORR_20(X6/M1/K4/R5)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W4",
        "operator": "rank_spread",
        "left": {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "mechanism": "idio_jump_profit_position",
        "hypothesis": "两腿角色：A=特异跳跃份额（Jacod–Todorov 2009，个体信息事件）；B=价格/平均成本−1（获利位置）。假设：特异跳跃高而价格高于成本（信号高）=个体事件落在获利定位（知情事件在盈利资产上），延续；价格低于成本（信号低）=事件是亏损资产的坏消息。声明：IDIO_JUMP_SHARE_20(U2/V2)第3次；PRICE_VS_AVGCOST_20(D1/V3)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W5",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "CATEGORY_DISPERSION_20", "source": "category_state"},
        "mechanism": "common_liquidity_consensus_category",
        "hypothesis": "两腿角色：A=流动性共性 R²（系统性流动性解释力）；B=类别 20 日分化（个体行情强度）。假设：共性 R² 高而类别分化小（信号高）=系统性流动性定价主导（共识环境），延续；分化大（信号低）=流动性共性被个体行情打破。声明：LIQ_COMMON_R2_20(V1)第2次；CATEGORY_DISPERSION_20(W3/B3 条件腿)第2次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "W6",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "ULCER_60", "source": "downside_risk"},
        "mechanism": "cojump_healthy_bleed_free",
        "hypothesis": "两腿角色：A=与池指数同分钟共跳比例（系统性信息事件）；B=60 日溃疡（慢性失血）。假设：共跳高而溃疡浅（信号高）=健康结构中的系统性事件（事件被正常定价），延续；溃疡深（信号低）=共跳是失血结构的系统性出逃。声明：COJUMP_INDEX_SHARE_20(U1/V3)第3次；ULCER_60(Y1/Z4/K6/T5)第4次。预期正方向。",
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
