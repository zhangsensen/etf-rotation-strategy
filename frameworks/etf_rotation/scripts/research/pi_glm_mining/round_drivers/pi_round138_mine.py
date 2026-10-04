#!/usr/bin/env python3
"""Round 138 driver: stage 24 batch 1 — relative_tick_1m family.
4 clean atoms (RT_REL_TICK 0.824 vs ROLL_SPREAD, RT_ZEROBAR 0.842 vs AMIHUD
shadowed - discretization IS the known friction channel) + 12 pairs.
Literature: Harris 1991; Angel 1997; O'Hara-Saar-Zhu 2019; Chung-Chuwonganant 2004.
17:00: each clean atom's left batch = this round (3 pairs, right legs
pairwise different families); right legs used once."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_138"

RTF = "relative_tick_1m"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": RTF},
        "right": {"name": name, "source": RTF},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": RTF},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"rt_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CD = "cost_distribution"
ID = "impact_decay_1m"
RT = "return_tail_shape"
SD = "serial_dependence"
FF = "fund_flow"
VT = "volume_time_1m"
LV = "liquidity_variability"
OS = "overnight_structure_1d"
IVP = "intraday_volume_profile_1m"
SCL = "scaling_memory_1m"
LB = "largebar_footprint_1m"
BF = "bar_size_order_flow"

CANDS = [
    _atom("DA24", "RT_ONETICK_20", "rt_onetick",
     "1m 收益恰为 ±1 tick 的比例 20 日均值（O'Hara–Saar–Zhu 2019 相对 tick 约束；体检 0.269）。方向 −1：高度量子化=流动性差。", -1),
    _atom("DA25", "RT_CLUSTER5_20", "rt_cluster5",
     "收盘价落整 5 tick 价位比例 − 20%（Harris 1991 价格聚集；体检 0.201）。方向 −1：过度聚集=陈旧报价。", -1),
    _atom("DA26", "RT_ZERO_SHIFT_20", "rt_zero_shift",
     "零区间比例 20 日变化（离散化约束恶化；体检 −0.399）。方向 −1：恶化。", -1),
    _atom("DA27", "RT_ENTROPY_20", "rt_entropy",
     "1m 收益离散化熵（取值多样性/bar 数；体检 0.424）。方向 +1：熵高=价格发现充分。", 1),
    _pair("CZ01", "RT_ONETICK_20", "CHIP_RANGE_90_60", CD,
     "簇 ONETICK：量子化 × 筹码集中。"),
    _pair("CZ02", "RT_ONETICK_20", "PV_ELASTICITY_20", ID,
     "簇 ONETICK：量子化 × 量价弹性（CA1 同腿）。"),
    _pair("CZ03", "RT_ONETICK_20", "WORST_DAY_20", RT,
     "簇 ONETICK：量子化 × 无极端损伤。"),
    _pair("CZ04", "RT_CLUSTER5_20", "SIGN_ACF1_5", SD,
     "簇 CLUSTER5：价格聚集 × 收益动量。"),
    _pair("CZ05", "RT_CLUSTER5_20", "SHARE_RET_CORR_20", FF,
     "簇 CLUSTER5：价格聚集 × 一级流解释力。"),
    _pair("CZ06", "RT_CLUSTER5_20", "VT_BUCKET_GINI_20", VT,
     "簇 CLUSTER5：价格聚集 × 体量钟不均（CN08 同腿）。"),
    _pair("CZ07", "RT_ZERO_SHIFT_20", "LOG_AMOUNT_VOL_20", LV,
     "簇 ZERO_SHIFT：离散化恶化 × 高活跃。"),
    _pair("CZ08", "RT_ZERO_SHIFT_20", "ON_PREM_20", OS,
     "簇 ZERO_SHIFT：离散化恶化 × 隔夜溢价（CZ01 同腿）。"),
    _pair("CZ09", "RT_ZERO_SHIFT_20", "VOL_SPIKE_FREQ_20", IVP,
     "簇 ZERO_SHIFT：离散化恶化 × 事件密集（CJ19 同腿）。"),
    _pair("CZ10", "RT_ENTROPY_20", "SCL_DFA_RET_20", SCL,
     "簇 ENTROPY：收益熵 × 路径平滑（CY09 同腿）。"),
    _pair("CZ11", "RT_ENTROPY_20", "LBAR_CLOCK_STD_20", LB,
     "簇 ENTROPY：收益熵 × 体量钟离散（BF1 同腿）。"),
    _pair("CZ12", "RT_ENTROPY_20", "CLOSE5_DAY_CONSIST_20", BF,
     "簇 ENTROPY：收益熵 × 收盘确认（CK04 同腿）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage24(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage24_relative_tick"
    plan["family_note"] = (
        "第 24 阶段 relative_tick_1m 首批：4 干净原子（REL_TICK 0.824 vs ROLL_SPREAD、"
        "ZEROBAR 0.842 vs AMIHUD 影子剔除——离散化≈已知摩擦通道）+ 12 配对；"
        "出处 Harris 1991 / Angel 1997 / O'Hara-Saar-Zhu 2019 / Chung-Chuwonganant 2004"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage24

if __name__ == "__main__":
    base.main()
