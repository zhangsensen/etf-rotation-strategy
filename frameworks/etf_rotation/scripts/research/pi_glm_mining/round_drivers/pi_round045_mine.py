#!/usr/bin/env python3
"""Round 045 driver: stage-8 round 5 (entering streak: 1 zero round, r044).
Six rank_spread pairs, each with >=1 cojump_1m/liquidity_commonality_1m leg
(third/fourth uses, fresh partners); all pairs atom-level new, all mechanism
names new. W3's admitted vector remains in the dedup reference set. Gate 7
v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_045"

base.CANDIDATES = [
    {
        "id": "Y1",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"},
        "right": {"name": "TAIL_Q10_20", "source": "return_tail_shape"},
        "mechanism": "aligned_cojump_clean_tail",
        "hypothesis": "两腿角色：A=共跳方向一致度（与池同向共跳占比，方向性系统事件）；B=日线左尾深度。假设：共跳同向高而左尾浅（信号高）=系统性方向事件且无尾部损伤，事件后延续；左尾深（信号低）=同向事件是下行共跳。声明：COJUMP_DIR_AGREE_20(U3/V6/W2)第4次；TAIL_Q10_20(S2/BB6/X5/M2/R3)第6次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Y2",
        "operator": "rank_spread",
        "left": {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "idio_shock_disciplined_rhythm",
        "hypothesis": "两腿角色：A=特异流动性冲击（Amihud 残差 20 日 z，个体流动性事件）；B=日内量分布熵（量的时间均匀度）。假设：特异冲击高而量熵低（信号高）=集中执行节奏中的个体流动性事件（机构执行痕迹），延续；量熵高（信号低）=事件是散户噪声。声明：IDIO_LIQ_SHOCK_Z_20(U6/V5/X1)第4次；VOL_ENTROPY_20(AA1/AA5/M5/X3)第4次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Y3",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "liq_beta_secondary_sensitivity",
        "hypothesis": "两腿角色：A=流动性共性 β（系统性流动性敏感，CRS 2000/KLvD 2012）；B=份额变化-收益相关（一级流解释力）。假设：共性 β 高而一级流不解释价格（信号高）=系统性流动性敏感来自真实配置盘（非申赎映射），延续；一级解释力强（信号低）=敏感是申赎机械产物。声明：LIQ_COMMON_BETA_20(U4/W1/X2)第4次；SHARE_RET_CORR_20(X6/M1/K4/R5/W3 入选)第6次——去重门自动检验与 W3 向量的相关。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Y4",
        "operator": "rank_spread",
        "left": {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"},
        "right": {"name": "STREAK_DAYS", "source": "fund_flow"},
        "mechanism": "common_liquidity_primary_streak",
        "hypothesis": "两腿角色：A=流动性共性 R²（系统性流动性解释力）；B=连续净申购天数（一级承接方向）。假设：共性 R² 高而连续净申购（信号高）=系统性流动性定价+一级承接同在（配置环境完整），延续；连续赎回（信号低）=共性定价叠加失血。声明：LIQ_COMMON_R2_20(V1/W5/X6)第4次；STREAK_DAYS(T5/N3/K3/T2/S2/X1)第6次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "Y5",
        "operator": "rank_spread",
        "left": {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"},
        "right": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "mechanism": "aligned_cojump_profitable",
        "hypothesis": "两腿角色：A=共跳方向一致度（方向性系统事件）；B=价格/平均成本−1（获利位置）。假设：共跳同向高而价格高于成本（信号高）=系统性同向事件落在获利定位（多头确认），延续；价格低于成本（信号低）=同向事件在亏损结构中（出逃确认）。声明：COJUMP_DIR_AGREE_20(U3/V6/W2/Y1)第5次；PRICE_VS_AVGCOST_20(D1/V3/W4/X2)第5次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Y6",
        "operator": "rank_spread",
        "left": {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"},
        "right": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "mechanism": "idio_jump_clean_overhead",
        "hypothesis": "两腿角色：A=特异跳跃份额（Jacod–Todorov 2009，个体信息事件）；B=上方套牢厚度（结构包袱）。假设：特异跳跃高而套牢薄（信号高）=个体信息事件无结构包袱（上方无封顶），事件后延续；套牢厚（信号低）=事件被历史套牢压制。声明：IDIO_JUMP_SHARE_20(U2/V2/W4/X5)第5次；OVERHAND_THICKNESS_60(D2/D3/E1/AA1/AA2/N6/R2)第8次。预期正方向。",
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
