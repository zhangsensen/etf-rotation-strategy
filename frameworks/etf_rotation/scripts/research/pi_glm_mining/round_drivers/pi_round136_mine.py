#!/usr/bin/env python3
"""Round 136 driver: stage 23 — cross-stage top-atom pairing scan.
Top-12 atoms by single-atom audit t (<=3/family, kin-deduped), 21 legal
never-paired cross-family pairs under pairing discipline (programmatic
feasibility check passed). Directly tests whether information lives only
in the 1m volume channel."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_136"


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"top_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


ID = "impact_decay_1m"
LB = "largebar_footprint_1m"
SCL = "scaling_memory_1m"
BF = "bar_size_order_flow"
ON = "overnight_structure_1d"
IVP = "intraday_volume_profile_1m"
VT = "volume_time_1m"
AU = "auction_1m"
LBK = "lunch_break_1m"
LS = "liquidity_commonality_1m"
RT = "return_tail_shape"

P = [
    ("CY01", "PV_ELASTICITY_20", ID, "LBAR_CLOCK_STD_20", LB,
     "簇 PV_ELAST：量价弹性 × 体量钟离散——冲击弹性与体量钟不均双确认（t 和 7.12）。"),
    ("CY02", "PV_ELASTICITY_20", ID, "SCL_DFA_RET_20", SCL,
     "簇 PV_ELAST：弹性 × 路径平滑——冲击响应与路径粗糙度互补（7.08）。"),
    ("CY03", "PV_ELASTICITY_20", ID, "VOL_SPIKE_FREQ_20", IVP,
     "簇 PV_ELAST：弹性 × 事件密集（6.76）。"),
    ("CY04", "PV_ELASTICITY_20", ID, "AM_PM_RV_RATIO_20", LBK,
     "簇 PV_ELAST：弹性 × 午间波动比（6.23）。"),
    ("CY05", "LBAR_CLOCK_STD_20", LB, "SCL_DFA_RET_20", SCL,
     "簇 LBAR_CLOCK：体量钟离散 × 路径平滑（6.20）。"),
    ("CY06", "PV_ELASTICITY_20", ID, "WORST_DAY_20", RT,
     "簇 PV_ELAST：弹性 × 无极端损伤（6.18）。"),
    ("CY07", "LBAR_CLOCK_STD_20", LB, "TICK_IMBALANCE_20", BF,
     "簇 LBAR_CLOCK：体量钟离散 × 主买不平衡（6.02）。"),
    ("CY08", "LBAR_CLOCK_STD_20", LB, "VOL_SPIKE_FREQ_20", IVP,
     "簇 LBAR_CLOCK：体量钟离散 × 事件密集（5.88）。"),
    ("CY09", "SCL_DFA_RET_20", SCL, "VOL_SPIKE_FREQ_20", IVP,
     "簇 DFA_RET：路径平滑 × 事件密集（5.84）。"),
    ("CY10", "SCL_DFA_RET_20", SCL, "ON_PREM_20", ON,
     "簇 DFA_RET：路径平滑 × 隔夜溢价（CZ01 同腿，5.84）。"),
    ("CY11", "SCL_DFA_RET_20", SCL, "VT_AUTOCORR_20", VT,
     "簇 DFA_RET：路径平滑 × 体量时间自相关（DA2 同腿，5.68）。"),
    ("CY12", "LBAR_CLOCK_STD_20", LB, "AUC_VARIANCE_RATIO_20", AU,
     "簇 LBAR_CLOCK：体量钟离散 × 波动配置（CM06 同腿，5.42）。"),
    ("CY13", "SCL_DFA_RET_20", SCL, "AUC_VARIANCE_RATIO_20", AU,
     "簇 DFA_RET：路径平滑 × 波动配置（5.38）。"),
    ("CY14", "LBAR_CLOCK_STD_20", LB, "AM_PM_RV_RATIO_20", LBK,
     "簇 LBAR_CLOCK：体量钟离散 × 午间波动比（DA1 同腿，5.35）。"),
    ("CY15", "SCL_DFA_RET_20", SCL, "AM_PM_RV_RATIO_20", LBK,
     "簇 DFA_RET：路径平滑 × 午间波动比（5.31）。"),
    ("CY16", "LBAR_CLOCK_STD_20", LB, "WORST_DAY_20", RT,
     "簇 LBAR_CLOCK：体量钟离散 × 无极端损伤（5.30）。"),
    ("CY17", "SCL_DFA_RET_20", SCL, "WORST_DAY_20", RT,
     "簇 DFA_RET：路径平滑 × 无极端损伤（5.26）。"),
    ("CY18", "LBAR_CLOCK_STD_20", LB, "RESILIENCY_20", LS,
     "簇 LBAR_CLOCK：体量钟离散 × 微结构弹性（5.20）。"),
    ("CY19", "SCL_DFA_RET_20", SCL, "RESILIENCY_20", LS,
     "簇 DFA_RET：路径平滑 × 微结构弹性（5.16）。"),
    ("CY20", "VOL_SPIKE_FREQ_20", IVP, "AUC_VARIANCE_RATIO_20", AU,
     "簇 VOL_SPIKE：事件密集 × 波动配置（5.06）。"),
    ("CY21", "AM_PM_RV_RATIO_20", LBK, "RESILIENCY_20", LS,
     "簇 AM_PM_RV：午间波动比 × 微结构弹性（DA1 同腿，4.31）。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, rsrc, hyp) for cid, left, lsrc, right, rsrc, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage23(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage23_top_atom_cross_pairing"
    plan["pairing_note"] = (
        "第 23 阶段：顶级 12 原子（单原子审计 t 排序，≤3/族，近亲去重）互配扫描；"
        "21 条合法未测跨族对（t 和排序），程序化可行性核查通过；"
        "直接检验'信息是否只在 1m 量通道'"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage23

if __name__ == "__main__":
    base.main()
