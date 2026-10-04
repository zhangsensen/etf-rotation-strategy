#!/usr/bin/env python3
"""Round 046 driver: stage-8 round 6. Entering streak: 2 consecutive gate-7
zero rounds (r044, r045) — a third triggers contract exhaustion. Six
rank_spread pairs, each with >=1 cojump_1m/liquidity_commonality_1m leg
(all pairs atom-level new, all mechanism names new; W3's admitted vector in
the dedup reference set). Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_046"

base.CANDIDATES = [
    {
        "id": "Z1",
        "operator": "rank_spread",
        "left": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "mechanism": "resilient_profit_structure",
        "hypothesis": "两腿角色：A=流动性回复力（冲击后 5 分钟回复比例，Kyle–Obizhaeva 2016 代理）；B=获利盘比例（成本结构）。假设：回复力高而获利盘高（信号高）=弹性微结构落在盈利资产（冲击被获利盘自然吸收），延续；获利盘低（信号低）=弹性是下跌结构的假象。声明：RESILIENCY_20(U5/V4/X4)第5次；PROFIT_RATIO_60(R1/S4/U1/V5/W2)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z2",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "liq_beta_disciplined_rhythm",
        "hypothesis": "两腿角色：A=流动性共性 β（系统性流动性敏感，CRS 2000/KLvD 2012）；B=日内量分布熵（量的时间均匀度）。假设：共性 β 高而量熵低（信号高）=系统性流动性敏感伴随集中执行节奏（机构配置盘），延续；量熵高（信号低）=敏感被噪声打散。声明：LIQ_COMMON_BETA_20(U4/W1/X2/Y3)第5次；VOL_ENTROPY_20(AA1/AA5/M5/X3/Y2)第5次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Z3",
        "operator": "rank_spread",
        "left": {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "TAIL_Q10_20", "source": "return_tail_shape"},
        "mechanism": "idio_shock_no_tail_damage",
        "hypothesis": "两腿角色：A=特异流动性冲击（Amihud 残差 20 日 z，个体流动性事件）；B=日线左尾深度。假设：特异冲击高而左尾浅（信号高）=个体流动性事件有序发生（无尾部损伤），延续；左尾深（信号低）=冲击已造成结构性损伤。声明：IDIO_LIQ_SHOCK_Z_20(U6/V5/X1/Y2)第5次；TAIL_Q10_20(S2/BB6/X5/M2/R3/Y1)第7次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Z4",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "STREAK_DAYS", "source": "fund_flow"},
        "mechanism": "cojump_primary_streak",
        "hypothesis": "两腿角色：A=与池指数同分钟共跳比例（系统性信息事件）；B=连续净申购天数（一级承接方向）。假设：共跳高且连续净申购（信号高）=系统性事件伴随一级承接（配置资金同步进场），延续；连续赎回（信号低）=事件发生在流出环境。声明：COJUMP_INDEX_SHARE_20(U1/V3/W6/X3)第5次；STREAK_DAYS(T5/N3/K3/T2/S2/X1)第7次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z5",
        "operator": "rank_spread",
        "left": {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "idio_jump_concentrated_chips",
        "hypothesis": "两腿角色：A=特异跳跃份额（Jacod–Todorov 2009，个体信息事件）；B=90% 筹码区间宽度（筹码集中度）。假设：特异跳跃高而筹码区间窄（信号高）=集中筹码中的个体信息事件（控盘资金行为），延续；筹码发散（信号低）=跳跃被分散持有者稀释。声明：IDIO_JUMP_SHARE_20(U2/V2/W4/X5/Y6)第6次；CHIP_RANGE_90_60(C3/T4/V3)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z6",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "aligned_cojump_secondary_origin",
        "hypothesis": "两腿角色：A=共跳方向一致度（方向性系统事件）；B=份额变化-收益相关（一级流解释力）。假设：共跳同向高而一级流不解释价格（信号高）=系统性方向事件来自二级自身（价格发现真实），延续；一级解释力强（信号低）=同向事件是申赎的机械映射。声明：COJUMP_DIR_AGREE_20(U3/V6/W2/Y1/Y5)第6次；SHARE_RET_CORR_20(X6/M1/K4/R5/W3 入选/Y3)第7次。预期负方向。",
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
        "W3(RESILIENCY x SHARE_RET_CORR) 已入选，其向量进入去重参照集"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_cojump

if __name__ == "__main__":
    base.main()
