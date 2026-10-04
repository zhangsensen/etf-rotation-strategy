#!/usr/bin/env python3
"""Round 153 driver: stage 30 batch 1 — liquidity_momentum family.
5 clean atoms (health max 0.589 vs AMOUNT_RATIO_20_60, no shadows) + 10 pairs.
Literature: Amihud 2002; Bali-Peng-Shen-Tang 2014; Acharya-Pedersen 2005;
Chordia-Roll-Subrahmanyam 2001.
17:00: each LM atom's left batch = this round (2 pairs, right legs pairwise
different families); right legs used once."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_153"

LM = "liquidity_momentum"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": LM},
        "right": {"name": name, "source": LM},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": LM},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"lm_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


ID = "impact_decay_1m"
LS = "liquidity_commonality_1m"
DR = "downside_risk"
BF = "bar_size_order_flow"
SD = "serial_dependence"
AU = "auction_1m"
OS = "overnight_structure_1d"
CD = "cost_distribution"
RT = "return_tail_shape"
FF = "fund_flow"

CANDS = [
    _atom("DA62", "LM_AMIHUD_RATIO_20_60", "lm_amihud_ratio",
     "Amihud 20/60 日之比（流动性动量，Amihud 2002 预期非流动性；体检 0.578）。方向 +1：非流动性上升=补偿溢价。", 1),
    _atom("DA63", "LM_AMIHUD_LOGCHG_20", "lm_amihud_logchg",
     "log-Amihud 20 日变化（流动性冲击水平；Bali et al. 2014；体检 0.589）。方向 +1。", 1),
    _atom("DA64", "LM_UNEXP_AMIHUD_20", "lm_unexp_amihud",
     "Amihud AR(1) 残差 20 日均值=非预期非流动性（Amihud 2002 未预期部分；体检 0.413）。方向 −1：意外冲击=短期定价混乱。", -1),
    _atom("DA65", "LM_ROLL_CHG_20", "lm_roll_chg",
     "Roll 价差代理 20 日变化（Chordia–Roll–Subrahmanyam 2001；体检 0.193）。方向 −1：价差走阔。", -1),
    _atom("DA66", "LM_LIQ_RET_CORR_20", "lm_liq_ret_corr",
     "流动性变化与收益的 20 日相关（流动性冲击的价格反应；Acharya–Pedersen 2005；体检 0.446）。方向 −1。", -1),
    _pair("CZ68", "LM_AMIHUD_RATIO_20_60", "PV_ELASTICITY_20", ID,
     "簇 AMIHUD_RATIO：非流动性动量 × 量价弹性（CA1 同腿）。"),
    _pair("CZ69", "LM_AMIHUD_RATIO_20_60", "RESILIENCY_20", LS,
     "簇 AMIHUD_RATIO：非流动性动量 × 微结构弹性。"),
    _pair("CZ70", "LM_AMIHUD_LOGCHG_20", "ULCER_20", DR,
     "簇 AMIHUD_LOGCHG：流动性冲击 × 健康结构。"),
    _pair("CZ71", "LM_AMIHUD_LOGCHG_20", "TICK_IMBALANCE_20", BF,
     "簇 AMIHUD_LOGCHG：流动性冲击 × 主买不平衡。"),
    _pair("CZ72", "LM_UNEXP_AMIHUD_20", "SIGN_ACF1_5", SD,
     "簇 UNEXP_AMIHUD：意外非流动性 × 收益动量。"),
    _pair("CZ73", "LM_UNEXP_AMIHUD_20", "AUC_VARIANCE_RATIO_20", AU,
     "簇 UNEXP_AMIHUD：意外非流动性 × 波动配置（CM06 同腿）。"),
    _pair("CZ74", "LM_ROLL_CHG_20", "ON_PREM_20", OS,
     "簇 ROLL_CHG：价差变化 × 隔夜溢价（CZ01 同腿）。"),
    _pair("CZ75", "LM_ROLL_CHG_20", "CHIP_RANGE_90_60", CD,
     "簇 ROLL_CHG：价差变化 × 筹码集中。"),
    _pair("CZ76", "LM_LIQ_RET_CORR_20", "WORST_DAY_20", RT,
     "簇 LIQ_RET：流动性冲击反应 × 无极端损伤。"),
    _pair("CZ77", "LM_LIQ_RET_CORR_20", "SHARE_RET_CORR_20", FF,
     "簇 LIQ_RET：流动性冲击反应 × 一级流解释力。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage30(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage30_liquidity_momentum"
    plan["family_note"] = (
        "第 30 阶段 liquidity_momentum 首批：5 干净原子（体检 max 0.589，无影子）+ 10 配对；"
        "出处 Amihud 2002 / Bali et al. 2014 / Acharya-Pedersen 2005 / Chordia et al. 2001"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage30

if __name__ == "__main__":
    base.main()
