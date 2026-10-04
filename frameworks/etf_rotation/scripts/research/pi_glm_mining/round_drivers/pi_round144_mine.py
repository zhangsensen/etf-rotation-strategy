#!/usr/bin/env python3
"""Round 144 driver: stage 26 batch 1 — long_horizon_anchors_1d family.
6 clean atoms (NEAR_HIGH shadowed 0.753 vs CURRENT_DD_120; BREAK_VOL coverage
0.002 - 1d panel volume unavailable - not preregistered) + 10 pairs.
Literature: George-Hwang 2004; Huddart-Lang-Yetman 2009; Li-Yu 2012; Bhootra-Hur 2013.
17:00: each LHA atom's left batch = this round (2 pairs, right legs pairwise
different families); right legs used once."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_144"

LHA = "long_horizon_anchors_1d"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": LHA},
        "right": {"name": name, "source": LHA},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": LHA},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"lha_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


DR = "downside_risk"
BF = "bar_size_order_flow"
SD = "serial_dependence"
IVP = "intraday_volume_profile_1m"
CD = "cost_distribution"
FF = "fund_flow"
RT = "return_tail_shape"
OS = "overnight_structure_1d"
SCL = "scaling_memory_1m"
IVP2 = "intraday_volume_profile_1m"

CANDS = [
    _atom("DA36", "LHA_NEAR_LOW_20", "lha_near_low",
     "收盘价/250 日最低价 20 日均值（George–Hwang 2004 锚定的下沿版；体检 0.633）。方向 +1：远离下锚=趋势健康。", 1),
    _atom("DA37", "LHA_AGE_HIGH_20", "lha_age_high",
     "距 250 日最高价的 20 日新鲜度（1−新高占比）×20（Bhootra–Hur 2013 最近高点距今时间；体检 −0.518）。方向 −1：锚陈旧=动量衰减。", -1),
    _atom("DA38", "LHA_AGE_LOW_20", "lha_age_low",
     "距 250 日最低价的新鲜度（体检 0.405）。方向 −1：低锚新鲜=仍在探底。", -1),
    _atom("DA39", "LHA_POS_DIVERG_20", "lha_pos_diverg",
     "250 日位置 − 60 日位置（长短锚分歧；Li–Yu 2012；体检 0.275）。方向 −1：短锚弱于长锚=回踩风险。", -1),
    _atom("DA40", "LHA_NEWHIGH_20", "lha_newhigh",
     "近 20 日触及 250 日新高的天数占比（体检 0.546）。方向 −1：新高过密=拥挤（George–Hwang 反转侧）。", -1),
    _pair("CY58", "LHA_NEAR_LOW_20", "ULCER_20", DR,
     "簇 NEAR_LOW：远离下锚 × 健康结构。"),
    _pair("CY59", "LHA_NEAR_LOW_20", "TICK_IMBALANCE_20", BF,
     "簇 NEAR_LOW：远离下锚 × 主买不平衡。"),
    _pair("CY60", "LHA_AGE_HIGH_20", "SIGN_ACF1_5", SD,
     "簇 AGE_HIGH：锚新鲜度 × 收益动量。"),
    _pair("CY61", "LHA_AGE_HIGH_20", "OPEN30_VOL_SHARE_20", IVP,
     "簇 AGE_HIGH：锚新鲜度 × 开盘配置（CL09 同腿）。"),
    _pair("CY62", "LHA_AGE_LOW_20", "CHIP_RANGE_90_60", CD,
     "簇 AGE_LOW：低锚新鲜度 × 筹码集中。"),
    _pair("CY63", "LHA_AGE_LOW_20", "SHARE_RET_CORR_20", FF,
     "簇 AGE_LOW：低锚新鲜度 × 一级流解释力。"),
    _pair("CY64", "LHA_POS_DIVERG_20", "WORST_DAY_20", RT,
     "簇 POS_DIVERG：长短锚分歧 × 无极端损伤。"),
    _pair("CY65", "LHA_POS_DIVERG_20", "ON_PREM_20", OS,
     "簇 POS_DIVERG：长短锚分歧 × 隔夜溢价（CZ01 同腿）。"),
    _pair("CY66", "LHA_NEWHIGH_20", "SCL_DFA_RET_20", SCL,
     "簇 NEWHIGH：新高密度 × 路径平滑（CY09 同腿）。"),
    _pair("CY67", "LHA_NEWHIGH_20", "VOL_SPIKE_FREQ_20", IVP2,
     "簇 NEWHIGH：新高密度 × 事件密集（CJ19 同腿）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage26(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage26_long_horizon_anchors"
    plan["family_note"] = (
        "第 26 阶段 long_horizon_anchors_1d 首批：6 干净原子（NEAR_HIGH 影子 0.753 vs CURRENT_DD_120；"
        "BREAK_VOL 覆盖 0.002——1d panels 无可用成交量——未预注册）+ 10 配对；"
        "出处 George-Hwang 2004 / Huddart-Lang-Yetman 2009 / Li-Yu 2012 / Bhootra-Hur 2013"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage26

if __name__ == "__main__":
    base.main()
