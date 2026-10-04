#!/usr/bin/env python3
"""Round 141 driver: stage 25 batch 1 — volume_volatility_leadlag_1m family.
8 clean atoms (health max 0.42 vs price_volume_coupling/volatility_feedback/
activity_response) + 16 pairs. Literature: Karpoff 1987; Clark 1973;
Tauchen-Pitts 1983; Andersen 1996; Lamoureux-Lastrapes 1990.
17:00: each VVL atom's left batch = this round (2 pairs, right legs pairwise
different families); right legs used once."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_141"

VVL = "volume_volatility_leadlag_1m"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": VVL},
        "right": {"name": name, "source": VVL},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": VVL},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"vvl_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


ID = "impact_decay_1m"
LS = "liquidity_commonality_1m"
DR = "downside_risk"
IVP = "intraday_volume_profile_1m"
SD = "serial_dependence"
CD = "cost_distribution"
OS = "overnight_structure_1d"
BF = "bar_size_order_flow"
VT = "volume_time_1m"
RT = "return_tail_shape"
LV = "liquidity_variability"
FF = "fund_flow"
LB = "largebar_footprint_1m"
AU = "auction_1m"
OS2 = "overnight_structure_1d"
BF2 = "bar_size_order_flow"

CANDS = [
    _atom("DA28", "VVL_ABS_VOL1_20", "vvl_abs_vol1",
     "|r_t| 与滞后 1 bar 成交量交叉相关 20 日均值（Karpoff 1987 量价关系；体检 0.36）。方向 −1：量领先波动=不确定性传导。", -1),
    _atom("DA29", "VVL_ABS_VOL5_20", "vvl_abs_vol5",
     "|r_t| 与滞后 5 bar 成交量交叉相关（体检 0.385）。方向 −1 同上。", -1),
    _atom("DA30", "VVL_VOL_ABS1_20", "vvl_vol_abs1",
     "成交量与滞后 |r| 交叉相关（价领先量；体检 0.369）。方向 +1：知情交易先动价。", 1),
    _atom("DA31", "VVL_VOL_ABS5_20", "vvl_vol_abs5",
     "成交量与滞后 5 bar |r| 交叉相关（体检 0.385）。方向 −1。", -1),
    _atom("DA32", "VVL_LEAD_20", "vvl_lead",
     "领先方向差 =（量领先波动）−（波动领先量）（Hasbrouck 1991 符号；体检 0.279）。方向 +1。", 1),
    _atom("DA33", "VVL_MDH_R2_20", "vvl_mdh_r2",
     "日内 |r_t| ~ v_t 回归 R²（MDH 解释度；Clark 1973 / Tauchen-Pitts 1983 / Lamoureux-Lastrapes 1990；体检 0.357）。方向 −1：解释度高=无独立信息。", -1),
    _atom("DA34", "VVL_INCR_R2_20", "vvl_incr_r2",
     "加入 v_{t-1} 的 R² 增量（量的增量解释力；体检 0.119）。方向 +1。", 1),
    _atom("DA35", "VVL_MDH_R2_SHIFT_20", "vvl_mdh_shift",
     "MDH R² 的 20 日变化（体检 0.42，未及影子线）。方向 −1：解释度上升=不确定性上升。", -1),
    _pair("CZ13", "VVL_ABS_VOL1_20", "PV_ELASTICITY_20", ID,
     "簇 ABS_VOL1：量波动传导 × 量价弹性（CA1 同腿）。"),
    _pair("CZ14", "VVL_ABS_VOL1_20", "RESILIENCY_20", LS,
     "簇 ABS_VOL1：量波动传导 × 微结构弹性。"),
    _pair("CZ15", "VVL_ABS_VOL5_20", "ULCER_20", DR,
     "簇 ABS_VOL5：中段传导 × 健康结构。"),
    _pair("CZ16", "VVL_ABS_VOL5_20", "OPEN30_VOL_SHARE_20", IVP,
     "簇 ABS_VOL5：中段传导 × 开盘配置（CL09 同腿）。"),
    _pair("CZ17", "VVL_VOL_ABS1_20", "SIGN_ACF1_5", SD,
     "簇 VOL_ABS1：价领先量 × 收益动量。"),
    _pair("CZ18", "VVL_VOL_ABS1_20", "CHIP_RANGE_90_60", CD,
     "簇 VOL_ABS1：价领先量 × 筹码集中。"),
    _pair("CZ19", "VVL_VOL_ABS5_20", "ON_PREM_20", OS,
     "簇 VOL_ABS5：中段价先 × 隔夜溢价（CZ01 同腿）。"),
    _pair("CZ20", "VVL_VOL_ABS5_20", "TICK_IMBALANCE_20", BF,
     "簇 VOL_ABS5：中段价先 × 主买不平衡。"),
    _pair("CZ21", "VVL_LEAD_20", "VT_BUCKET_GINI_20", VT,
     "簇 LEAD：领先方向 × 体量钟不均（CN08 同腿）。"),
    _pair("CZ22", "VVL_LEAD_20", "WORST_DAY_20", RT,
     "簇 LEAD：领先方向 × 无极端损伤。"),
    _pair("CZ23", "VVL_MDH_R2_20", "LOG_AMOUNT_VOL_20", LV,
     "簇 MDH_R2：MDH 解释度 × 高活跃。"),
    _pair("CZ24", "VVL_MDH_R2_20", "SHARE_RET_CORR_20", FF,
     "簇 MDH_R2：MDH 解释度 × 一级流解释力。"),
    _pair("CZ25", "VVL_INCR_R2_20", "LBAR_CLOCK_STD_20", LB,
     "簇 INCR_R2：增量解释力 × 体量钟离散（BF1 同腿）。"),
    _pair("CZ26", "VVL_INCR_R2_20", "AUC_VARIANCE_RATIO_20", AU,
     "簇 INCR_R2：增量解释力 × 波动配置（CM06 同腿）。"),
    _pair("CZ27", "VVL_MDH_R2_SHIFT_20", "GAP_FILL_RATE_20", OS2,
     "簇 MDH_SHIFT：解释度变化 × 缺口修复率（CN03 同腿）。"),
    _pair("CZ28", "VVL_MDH_R2_SHIFT_20", "CLOSE5_DAY_CONSIST_20", BF2,
     "簇 MDH_SHIFT：解释度变化 × 收盘确认（CK04 同腿）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage25(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage25_volume_volatility_leadlag"
    plan["family_note"] = (
        "第 25 阶段 volume_volatility_leadlag_1m 首批：8 干净原子（体检 max 0.42）+ 16 配对；"
        "出处 Karpoff 1987 / Clark 1973 / Tauchen-Pitts 1983 / Andersen 1996 / Lamoureux-Lastrapes 1990；"
        "每 VVL 左腿的本阶段批=本轮，右腿两两不同族"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage25

if __name__ == "__main__":
    base.main()
