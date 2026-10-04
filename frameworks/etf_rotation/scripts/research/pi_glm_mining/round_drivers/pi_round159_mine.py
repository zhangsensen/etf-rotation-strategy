#!/usr/bin/env python3
"""Round 159 driver: stage 32 batch 1 — range_contraction_cycle family.
7 clean atoms (RCC_EXPAND_DIR_20 coverage 0.0 - not preregistered; max health
0.558 vs VOV_HAR_RESID_20, no shadows) + 14 pairs.
Literature: Crabel 1990; Bollinger 2001; Parkinson 1980; Taylor 1986;
Engle-Gallo 2006.
17:00: each RCC atom's left batch = this round (2 pairs, right legs pairwise
different families); right legs used once."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_159"

RCC = "range_contraction_cycle"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": RCC},
        "right": {"name": name, "source": RCC},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": RCC},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"rcc_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


ID = "impact_decay_1m"
LS = "liquidity_commonality_1m"
DR = "downside_risk"
BF = "bar_size_order_flow"
SD = "serial_dependence"
AU = "auction_1m"
CD = "cost_distribution"
OS = "overnight_structure_1d"
FF = "fund_flow"
LB = "largebar_footprint_1m"
IVP = "intraday_volume_profile_1m"
OS2 = "overnight_structure_1d"
BF2 = "bar_size_order_flow"
OS3 = "overnight_structure_1d"
RT = "return_tail_shape"

CANDS = [
    _atom("DA69", "RCC_REL_RANGE_20", "rcc_rel_range",
     "真实区间/20 日均区间 20 日均值（区间相对水平；Parkinson 1980 区间波动；体检 0.558）。方向 −1：高相对区间=高波动状态。", -1),
    _atom("DA70", "RCC_NARROW_STREAK_20", "rcc_narrow_streak",
     "连续窄幅日计数 20 日均值（Crabel 1990 窄幅日；体检 0.324）。方向 −1：窄幅连串后通常伴随扩张方向脉冲。", -1),
    _atom("DA71", "RCC_NR7_FREQ_20", "rcc_nr7_freq",
     "NR7 标志 20 日频率（Crabel 1990 NR7；体检 0.243）。方向 −1 同上。", -1),
    _atom("DA72", "RCC_NR7_AGE_20", "rcc_nr7_age",
     "距最近 NR7 天数（锚新鲜度；体检 0.274）。方向 −1：NR7 已久=动能耗散。", -1),
    _atom("DA73", "RCC_BB_SQUEEZE_20", "rcc_bb_squeeze",
     "Bollinger 带宽 120 日百分位（squeeze 深度；Bollinger 2001；体检 0.396）。方向 −1：深度 squeeze 后方向脉冲。", -1),
    _atom("DA74", "RCC_BB_CHG_20", "rcc_bb_chg",
     "带宽 20 日变化率（体检 0.398）。方向 −1：带宽骤增=波动冲击。", -1),
    _atom("DA75", "RCC_AR1_20", "rcc_ar1",
     "区间序列 1 阶自相关（Taylor 1986 区间持续性；体检 0.556 vs RANGE_ACF1）。方向 −1：高自相关=波动聚簇。", -1),
    _pair("CZ109", "RCC_REL_RANGE_20", "PV_ELASTICITY_20", ID,
     "簇 REL_RANGE：区间水平 × 量价弹性（CA1 同腿）。"),
    _pair("CZ110", "RCC_REL_RANGE_20", "RESILIENCY_20", LS,
     "簇 REL_RANGE：区间水平 × 微结构弹性。"),
    _pair("CZ111", "RCC_NARROW_STREAK_20", "ULCER_20", DR,
     "簇 NARROW_STREAK：窄幅连串 × 健康结构。"),
    _pair("CZ112", "RCC_NARROW_STREAK_20", "TICK_IMBALANCE_20", BF,
     "簇 NARROW_STREAK：窄幅连串 × 主买不平衡。"),
    _pair("CZ113", "RCC_NR7_FREQ_20", "SIGN_ACF1_5", SD,
     "簇 NR7_FREQ：NR7 频率 × 收益动量。"),
    _pair("CZ114", "RCC_NR7_FREQ_20", "AUC_VARIANCE_RATIO_20", AU,
     "簇 NR7_FREQ：NR7 频率 × 波动配置（CM06 同腿）。"),
    _pair("CZ115", "RCC_NR7_AGE_20", "CHIP_RANGE_90_60", CD,
     "簇 NR7_AGE：NR7 距今 × 筹码集中。"),
    _pair("CZ116", "RCC_NR7_AGE_20", "ON_PREM_20", OS,
     "簇 NR7_AGE：NR7 距今 × 隔夜溢价（CZ01 同腿）。"),
    _pair("CZ117", "RCC_BB_SQUEEZE_20", "SHARE_RET_CORR_20", FF,
     "簇 BB_SQUEEZE：squeeze 深度 × 一级流解释力。"),
    _pair("CZ118", "RCC_BB_SQUEEZE_20", "LBAR_CLOCK_STD_20", LB,
     "簇 BB_SQUEEZE：squeeze 深度 × 体量钟离散（BF1 同腿）。"),
    _pair("CZ119", "RCC_BB_CHG_20", "WORST_DAY_20", RT,
     "簇 BB_CHG：带宽变化 × 无极端损伤。"),
    _pair("CZ120", "RCC_BB_CHG_20", "VOL_SPIKE_FREQ_20", IVP,
     "簇 BB_CHG：带宽变化 × 事件密集（CJ19 同腿）。"),
    _pair("CZ121", "RCC_AR1_20", "CLOSE5_DAY_CONSIST_20", BF2,
     "簇 AR1：区间持续性 × 收盘确认（CK04 同腿）。"),
    _pair("CZ122", "RCC_AR1_20", "GAP_FILL_RATE_20", OS3,
     "簇 AR1：区间持续性 × 缺口修复率（CN03 同腿）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage32(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage32_range_contraction"
    plan["family_note"] = (
        "第 32 阶段 range_contraction_cycle 首批：7 干净原子（RCC_EXPAND_DIR_20 覆盖 0.0 "
        "未预注册；max 体检 0.558 无影子）+ 14 配对；"
        "出处 Crabel 1990 / Bollinger 2001 / Parkinson 1980 / Taylor 1986 / Engle-Gallo 2006"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage32

if __name__ == "__main__":
    base.main()
