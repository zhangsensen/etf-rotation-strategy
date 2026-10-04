#!/usr/bin/env python3
"""Round 131 driver: stage 21 batch 1 — scaling_memory_1m family.
7 clean atoms (SCL_LFPOW_20 shadowed at exactly 0.700 vs VOL_USHAPE_20) + 16 pairs.
Literature: Peng et al. 1994 (DFA); Lo 1991 (modified R/S);
Lo-MacKinlay 1988 (variance ratio); Granger 1966; Ding-Granger-Engle 1993.
17:00 accounting: each SCL atom's left-leg batch = this round (2 pairs,
right legs pairwise different families); right legs used once."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_131"

SCL = "scaling_memory_1m"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": SCL},
        "right": {"name": name, "source": SCL},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": SCL},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"scl_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


LS = "liquidity_commonality_1m"
LV = "liquidity_variability"
DR = "downside_risk"
BF = "bar_size_order_flow"
CD = "cost_distribution"
SD = "serial_dependence"
AU = "auction_1m"
IVP = "intraday_volume_profile_1m"
OS = "overnight_structure_1d"
ON = "overnight_structure_1d"
FF = "fund_flow"
PL = "price_location"
RT = "return_tail_shape"

CANDS = [
    _atom("DA16", "SCL_DFA_ABS_20", "scl_dfa_abs",
     "1m |收益| 的 DFA 标度指数（Peng 1994；Ding-Granger-Engle 1993 绝对收益长记忆；体检 0.17）。方向 −1：高长记忆=波动聚簇延续。", -1),
    _atom("DA17", "SCL_DFA_RET_20", "scl_dfa_ret",
     "1m 收益 DFA 指数 = 价格路径粗糙度（α<0.5 均值回复、>0.5 趋势；体检 0.203）。方向 +1：平滑趋势路径。", 1),
    _atom("DA18", "SCL_VR5_20", "scl_vr5",
     "方差比 VR(5)（Lo–MacKinlay 1988；VR>1 趋势、<1 回复；体检 0.661）。方向 +1。", 1),
    _atom("DA19", "SCL_VR15_20", "scl_vr15",
     "方差比 VR(15)（体检 0.648）。方向 +1。", 1),
    _atom("DA20", "SCL_VR30_20", "scl_vr30",
     "方差比 VR(30)（体检 0.642）。方向 +1。", 1),
    _atom("DA21", "SCL_RS_20", "scl_lo_rs",
     "Lo 修正 R/S 统计量 20 日均值（体检 0.670）。方向 +1：高 R/S=趋势性记忆。", 1),
    _atom("DA22", "SCL_VR5_SHIFT_20", "scl_vr5_shift",
     "VR5 的 20 日变化（趋势度恶化/改善；体检 0.304）。方向 −1：趋势度恶化。", -1),
    _pair("CU01", "SCL_DFA_ABS_20", "RESILIENCY_20", LS,
     "簇 DFA_ABS：|r| 长记忆 × 弹性——波动聚簇在弹性好的标的被吸收。"),
    _pair("CU02", "SCL_DFA_ABS_20", "LOG_AMOUNT_VOL_20", LV,
     "簇 DFA_ABS：|r| 长记忆 × 高活跃。"),
    _pair("CU03", "SCL_DFA_RET_20", "ULCER_20", DR,
     "簇 DFA_RET：路径平滑 × 健康结构。"),
    _pair("CU04", "SCL_DFA_RET_20", "TICK_IMBALANCE_20", BF,
     "簇 DFA_RET：路径平滑 × 主买不平衡。"),
    _pair("CU05", "SCL_VR5_20", "CHIP_RANGE_90_60", CD,
     "簇 VR5：短程趋势 × 筹码集中。"),
    _pair("CU06", "SCL_VR5_20", "SIGN_ACF1_5", SD,
     "簇 VR5：短程趋势 × 收益动量确认。"),
    _pair("CU07", "SCL_VR15_20", "AUC_VARIANCE_RATIO_20", AU,
     "簇 VR15：中程趋势 × 波动配置（CM06 同腿）。"),
    _pair("CU08", "SCL_VR15_20", "OPEN30_VOL_SHARE_20", IVP,
     "簇 VR15：中程趋势 × 开盘配置（CL09 同腿）。"),
    _pair("CU09", "SCL_VR30_20", "GAP_FILL_RATE_20", OS,
     "簇 VR30：长程趋势 × 缺口修复率（CN03 同腿）。"),
    _pair("CU10", "SCL_VR30_20", "CLOSE5_DAY_CONSIST_20", BF,
     "簇 VR30：长程趋势 × 收盘确认（CK04 同腿）。"),
    _pair("CU11", "SCL_RS_20", "ON_PREM_20", ON,
     "簇 RS：趋势记忆 × 隔夜溢价（CZ01 同腿）。"),
    _pair("CU12", "SCL_RS_20", "SHARE_RET_CORR_20", FF,
     "簇 RS：趋势记忆 × 一级流解释力。"),
    _pair("CU13", "SCL_VR5_SHIFT_20", "PRICE_POSITION_20", PL,
     "簇 VR5_SHIFT：趋势度变化 × 获利位置。"),
    _pair("CU14", "SCL_VR5_SHIFT_20", "WORST_DAY_20", RT,
     "簇 VR5_SHIFT：趋势度变化 × 无极端损伤。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage21(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage21_scaling_memory"
    plan["family_note"] = (
        "第 21 阶段 scaling_memory_1m 首批：7 干净原子（SCL_LFPOW_20 影子 0.700 vs VOL_USHAPE_20 剔除）"
        " + 16 配对；出处 Peng 1994 / Lo 1991 / Lo-MacKinlay 1988 / Granger 1966 / DGE 1993；"
        "每 SCL 左腿的本阶段批=本轮，右腿两两不同族"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage21

if __name__ == "__main__":
    base.main()
