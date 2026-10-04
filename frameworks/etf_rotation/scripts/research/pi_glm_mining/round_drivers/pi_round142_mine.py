#!/usr/bin/env python3
"""Round 142 driver: stage 25 batch 2 — VVL-as-right x 3 fresh left legs
per atom = 24 pairs (all left legs pairwise distinct; every unordered pair
new vs r141; hash guard enforces). Zero here makes streak 2/3."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_142"

VVL = "volume_volatility_leadlag_1m"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": VVL},
        "mechanism": f"vvl2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


DR = "downside_risk"
SD = "serial_dependence"
PL = "price_location"
LS = "liquidity_commonality_1m"
CD = "cost_distribution"
FF = "fund_flow"
ID = "impact_decay_1m"
BF = "bar_size_order_flow"
OS = "overnight_structure_1d"
RT = "return_tail_shape"
IVP = "intraday_volume_profile_1m"
LV = "liquidity_variability"
LB = "largebar_footprint_1m"
BF2 = "bar_size_order_flow"
VT = "volume_time_1m"
AU = "auction_1m"
OS2 = "overnight_structure_1d"
SCL = "scaling_memory_1m"
SCL2 = "scaling_memory_1m"
PL2 = "price_location"

P = [
    ("CY34", "ULCER_20", DR, "VVL_ABS_VOL1_20",
     "簇 ULCER：健康结构 × 低量波动传导（DA28 同腿反向取向）。"),
    ("CY35", "SIGN_ACF1_5", SD, "VVL_ABS_VOL1_20",
     "簇 SIGN_ACF：收益动量 × 低量波动传导。"),
    ("CY36", "PRICE_POSITION_20", PL, "VVL_ABS_VOL1_20",
     "簇 PRICE_POSITION：获利位置 × 低量波动传导。"),
    ("CY37", "RESILIENCY_20", LS, "VVL_ABS_VOL5_20",
     "簇 RESILIENCY：微结构弹性 × 低中段传导。"),
    ("CY38", "CHIP_RANGE_90_60", CD, "VVL_ABS_VOL5_20",
     "簇 CHIP_RANGE：筹码集中 × 低中段传导。"),
    ("CY39", "SHARE_RET_CORR_20", FF, "VVL_ABS_VOL5_20",
     "簇 SHARE_RET：一级流解释力 × 低中段传导。"),
    ("CY40", "PV_ELASTICITY_20", ID, "VVL_VOL_ABS1_20",
     "簇 PV_ELAST：量价弹性 × 低价先量（CA1 同腿反向取向）。"),
    ("CY41", "TICK_IMBALANCE_20", BF, "VVL_VOL_ABS1_20",
     "簇 TICK_IMB：主买不平衡 × 低价先量。"),
    ("CY42", "GAP_FILL_RATE_20", OS, "VVL_VOL_ABS1_20",
     "簇 GAP_FILL：缺口修复率 × 低价先量（CN03 同腿反向取向）。"),
    ("CY43", "WORST_DAY_20", RT, "VVL_VOL_ABS5_20",
     "簇 WORST_DAY：无极端损伤 × 低中段价先。"),
    ("CY44", "OPEN30_VOL_SHARE_20", IVP, "VVL_VOL_ABS5_20",
     "簇 OPEN30：开盘配置 × 低中段价先（CL09 同腿反向取向）。"),
    ("CY45", "LOG_AMOUNT_VOL_20", LV, "VVL_VOL_ABS5_20",
     "簇 LOG_AMOUNT：高活跃 × 低中段价先。"),
    ("CY46", "LBAR_CLOCK_STD_20", LB, "VVL_LEAD_20",
     "簇 LBAR_CLOCK：体量钟离散 × 高领先方向（BF1 同腿反向取向）。"),
    ("CY47", "CLOSE5_DAY_CONSIST_20", BF2, "VVL_LEAD_20",
     "簇 CLOSE5：收盘确认 × 高领先方向（CK04 同腿反向取向）。"),
    ("CY48", "VT_SKEW_20", VT, "VVL_LEAD_20",
     "簇 VT_SKEW：体量时间偏度 × 高领先方向。"),
    ("CY49", "AUC_VARIANCE_RATIO_20", AU, "VVL_MDH_R2_20",
     "簇 VAR_RATIO：波动配置 × 低 MDH 解释度（CM06 同腿反向取向）。"),
    ("CY50", "ON_PREM_20", OS, "VVL_MDH_R2_20",
     "簇 ON_PREM：隔夜溢价 × 低 MDH 解释度（CZ01 同腿反向取向）。"),
    ("CY51", "SCL_DFA_RET_20", SCL, "VVL_MDH_R2_20",
     "簇 DFA_RET：路径平滑 × 低 MDH 解释度（CY09 同腿反向取向）。"),
    ("CY52", "IMP_PERM_SHARE_20", ID, "VVL_INCR_R2_20",
     "簇 IMP_PERM：冲击永久份额 × 高增量解释力。"),
    ("CY53", "VOL_SPIKE_FREQ_20", IVP, "VVL_INCR_R2_20",
     "簇 VOL_SPIKE：事件密集 × 高增量解释力（CJ19 同腿反向取向）。"),
    ("CY54", "AUC_CLOSE_VOLSHARE_20", AU, "VVL_INCR_R2_20",
     "簇 CLOSE_VOLSHARE：收盘竞价份额 × 高增量解释力。"),
    ("CY55", "BIGBAR_EDGE_CONC_20", BF2, "VVL_MDH_R2_SHIFT_20",
     "簇 BIGBAR_EDGE：大 bar 时点集中 × 低解释度恶化。"),
    ("CY56", "SCL_DFA_ABS_20", SCL2, "VVL_MDH_R2_SHIFT_20",
     "簇 DFA_ABS：|r| 长记忆 × 低解释度恶化（CU02 同腿反向取向）。"),
    ("CY57", "PRICE_POSITION_20", PL2, "VVL_MDH_R2_SHIFT_20",
     "簇 PP2：获利位置 × 低解释度恶化。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage25(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage25_volume_volatility_leadlag"
    plan["pairing_note"] = (
        "第 25 阶段配对第 2 批：VVL 作右腿 × 3 新左腿/原子 = 24 条"
        "（24 簇各 1 条，全部新无序对）；本批后阶段配对枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage25

if __name__ == "__main__":
    base.main()
