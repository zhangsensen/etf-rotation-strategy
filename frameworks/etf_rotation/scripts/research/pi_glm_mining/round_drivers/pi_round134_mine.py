#!/usr/bin/env python3
"""Round 134 driver: stage 22 batch 1 — overnight_structure_1d formalized.
Family extended to 8 atoms; health: ON_SKEW_20 ok (0.279), ON_ID_CORR_20
SHADOW (1.000 vs GAP_SESSION_CORR_20 - identical construction).
Batch: 1 new atomic + 13 pairs. Fresh left-leg batches this stage for the
never-paired existing atoms ID_PREM/ON_ID_DIFF/ON_VAR_SHARE (3 right legs
each, pairwise different families) plus ON_SKEW batch (4 pairs)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_134"

ON = "overnight_structure_1d"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": ON},
        "right": {"name": name, "source": ON},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": ON},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"on2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


LS = "liquidity_commonality_1m"
LB = "largebar_footprint_1m"
BF = "bar_size_order_flow"
PL = "price_location"
DR = "downside_risk"
CD = "cost_distribution"
SD = "serial_dependence"
ID = "impact_decay_1m"
IVP = "intraday_volume_profile_1m"
AU = "auction_1m"
RT = "return_tail_shape"
LV = "liquidity_variability"

CANDS = [
    _atom("DA23", "ON_SKEW_20", "on_skew",
     "隔夜收益 20 日偏度（Berkman–Koch–Tuttle–Zhang 2012 隔夜收益散户注意力；Aboody et al. 2018 情绪代理；体检 0.279 vs ON_PREM）。方向 +1：正偏=情绪驱动的隔夜拉升，后续日内兑现。", 1),
    _pair("CW01", "ON_SKEW_20", "RESILIENCY_20", LS,
     "簇 ON_SKEW：隔夜偏度 × 弹性。"),
    _pair("CW02", "ON_SKEW_20", "LBAR_CLOCK_STD_20", LB,
     "簇 ON_SKEW：隔夜偏度 × 体量钟离散（BF1 同腿）。"),
    _pair("CW03", "ON_SKEW_20", "CLOSE5_DAY_CONSIST_20", BF,
     "簇 ON_SKEW：隔夜偏度 × 收盘确认（CK04 同腿）。"),
    _pair("CW04", "ON_SKEW_20", "PRICE_POSITION_20", PL,
     "簇 ON_SKEW：隔夜偏度 × 获利位置。"),
    _pair("CW05", "ID_PREM_20", "ULCER_20", DR,
     "簇 ID_PREM：日内溢价 × 健康结构（Lou–Polk–Skouras 2019 拉锯分解的日内侧首配）。"),
    _pair("CW06", "ID_PREM_20", "TICK_IMBALANCE_20", BF,
     "簇 ID_PREM：日内溢价 × 主买不平衡。"),
    _pair("CW07", "ID_PREM_20", "CHIP_RANGE_90_60", CD,
     "簇 ID_PREM：日内溢价 × 筹码集中。"),
    _pair("CW08", "ON_ID_DIFF_20", "SIGN_ACF1_5", SD,
     "簇 ON_ID_DIFF：隔夜/日内溢价差 × 收益动量确认。"),
    _pair("CW09", "ON_ID_DIFF_20", "PV_ELASTICITY_20", ID,
     "簇 ON_ID_DIFF：溢价差 × 量价弹性（CA1 同腿）。"),
    _pair("CW10", "ON_ID_DIFF_20", "OPEN30_VOL_SHARE_20", IVP,
     "簇 ON_ID_DIFF：溢价差 × 开盘配置（CL09 同腿）。"),
    _pair("CW11", "ON_VAR_SHARE_20", "AUC_VARIANCE_RATIO_20", AU,
     "簇 ON_VAR_SHARE：隔夜方差份额 × 波动配置（CM06 同腿）。"),
    _pair("CW12", "ON_VAR_SHARE_20", "WORST_DAY_20", RT,
     "簇 ON_VAR_SHARE：隔夜方差份额 × 无极端损伤。"),
    _pair("CW13", "ON_VAR_SHARE_20", "LOG_AMOUNT_VOL_20", LV,
     "簇 ON_VAR_SHARE：隔夜方差份额 × 高活跃。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage22(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage22_overnight_formalized"
    plan["family_note"] = (
        "第 22 阶段 overnight_structure_1d 正式化：家族扩至 8 原子；"
        "体检 ON_SKEW_20 ok（0.279）、ON_ID_CORR_20 影子（1.000 vs GAP_SESSION_CORR_20 同构）；"
        "本批 = 1 新原子 + 13 配对（ID_PREM/ON_ID_DIFF/ON_VAR_SHARE 首次获得左腿批）；"
        "出处 Lou-Polk-Skouras 2019 / Berkman et al. 2012 / Cliff-Cooper-Gulen 2008 / Aboody et al. 2018"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage22

if __name__ == "__main__":
    base.main()
