#!/usr/bin/env python3
"""Round 047 driver: stage-8 round 7 (Z1 admitted in r046, streak = 0).
Six rank_spread pairs, each with >=1 cojump_1m/liquidity_commonality_1m leg;
all pairs atom-level new, all mechanism names new. W3 + Z1 admitted vectors
sit in the dedup reference set (RESILIENCY-leg candidates auto-tested vs Z1).
Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_047"

base.CANDIDATES = [
    {
        "id": "AA1",
        "operator": "rank_spread",
        "left": {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "mechanism": "idio_shock_profit_position",
        "hypothesis": "两腿角色：A=特异流动性冲击（Amihud 残差 20 日 z，个体流动性事件）；B=价格/平均成本−1（获利位置）。假设：特异冲击高而价格高于成本（信号高）=个体事件落在获利定位（有序事件非恐慌），延续；亏损位置（信号低）=事件是失血。声明：IDIO_LIQ_SHOCK_Z_20(U6/V5/X1/Y2/Z3)第6次；PRICE_VS_AVGCOST_20(D1/V3/W4/X2)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AA2",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "TAIL_Q10_20", "source": "return_tail_shape"},
        "mechanism": "common_liquidity_clean_tail",
        "hypothesis": "两腿角色：A=流动性共性 R²（系统性流动性解释力）；B=日线左尾深度。假设：共性 R² 高而左尾浅（信号高）=系统性流动性定价主导且无尾部损伤，延续；左尾深（信号低）=共性定价叠加尾部损伤。声明：LIQ_COMMON_R2_20(V1/W5/X6/Y4)第5次；TAIL_Q10_20(S2/BB6/X5/M2/R3/Y1/Z3)第8次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "AA3",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "resilient_concentrated_chips",
        "hypothesis": "两腿角色：A=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）；B=90% 筹码区间宽度（筹码集中度）。假设：回复力高而筹码区间窄（信号高）=集中筹码下的高弹性（控盘资金提供流动性），延续；筹码发散（信号低）=弹性无主体支持。声明：RESILIENCY_20(U5/V4/X4，注意 Z1 已入选——本对与之不同腿，去重门自动检验)第6次；CHIP_RANGE_90_60(C3/T4/V3/Z5)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AA4",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "SHARE_CHG_20", "source": "fund_flow"},
        "mechanism": "liq_beta_primary_config",
        "hypothesis": "两腿角色：A=流动性共性 β（系统性流动性敏感，CRS 2000/KLvD 2012）；B=份额 20 日变化率（一级配置流）。假设：共性 β 高而份额流入（信号高）=系统性流动性敏感与一级配置同在（配置环境完整），延续；份额流出（信号低）=敏感盘失血。声明：LIQ_COMMON_BETA_20(U4/W1/X2/Y3/Z2)第6次；SHARE_CHG_20(X2/X5/U6)第4次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "AA5",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "cojump_ushape_config_timing",
        "hypothesis": "两腿角色：A=与池指数同分钟共跳比例（系统性信息事件）；B=日内 U 形 RV 占比（开/收盘波动节律）。假设：共跳高而 U 形占比高（信号高）=系统性事件与配置时点重合（开收盘配置盘推动事件），延续；无节律（信号低）=事件时点随机化。声明：COJUMP_INDEX_SHARE_20(U1/V3/W6/X3/Z4)第6次；VOL_USHAPE_20(T2/S4)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AA6",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"},
        "right": {"name": "PRIMARY_SHARE_20", "source": "fund_flow"},
        "mechanism": "aligned_cojump_low_primary_share",
        "hypothesis": "两腿角色：A=共跳方向一致度（方向性系统事件）；B=一级市场量占比（申赎机械流）。假设：共跳同向高而一级占比低（信号高）=系统性方向事件来自二级自身（价格发现真实），延续；一级占比高（信号低）=同向事件是申赎映射。声明：COJUMP_DIR_AGREE_20(U3/V6/W2/Y1/Y5)第7次；PRIMARY_SHARE_20(Y6/X4/M4/K1/R4/V1)第7次。预期负方向。",
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
        "W3(RESILIENCY x SHARE_RET_CORR) 与 Z1(RESILIENCY x PROFIT) 已入选，"
        "其向量进入去重参照集"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_cojump

if __name__ == "__main__":
    base.main()
