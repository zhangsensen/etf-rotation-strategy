#!/usr/bin/env python3
"""Round 148 driver: stage 27 batch 2 — RPF-as-right x 3 fresh left legs
per atom = 18 pairs (all left legs pairwise distinct; every unordered pair
new vs r147). After this round stage-27 pairing enumeration = 0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_148"

RPF = "replication_volume_free_v1"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": RPF},
        "mechanism": f"rpf2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


DR = "downside_risk"
BF = "bar_size_order_flow"
OS = "overnight_structure_1d"
LS = "liquidity_commonality_1m"
LV = "liquidity_variability"
RT = "return_tail_shape"
SD = "serial_dependence"
IVP = "intraday_volume_profile_1m"
ID = "impact_decay_1m"
CD = "cost_distribution"
FF = "fund_flow"
SCL = "scaling_memory_1m"
AU = "auction_1m"
VT = "volume_time_1m"
OS2 = "overnight_structure_1d"
BF2 = "bar_size_order_flow"
IVP2 = "intraday_volume_profile_1m"
AU2 = "auction_1m"
IPD = "intraday_profile_deviation"
PL = "price_location"
LB = "largebar_footprint_1m"

P = [
    ("CY68", "ULCER_20", DR, "RP_PERM_ENT_D3_20",
     "簇 ULCER：健康结构 × 低排列熵（DA41 同腿反向取向）。"),
    ("CY69", "TICK_IMBALANCE_20", BF, "RP_PERM_ENT_D3_20",
     "簇 TICK_IMB：主买不平衡 × 低排列熵。"),
    ("CY70", "ON_PREM_20", OS, "RP_PERM_ENT_D3_20",
     "簇 ON_PREM：隔夜溢价 × 低排列熵（CZ01 同腿反向取向）。"),
    ("CY71", "RESILIENCY_20", LS, "RP_PERM_ENT_D4_20",
     "簇 RESILIENCY：微结构弹性 × 低排列熵(d4)。"),
    ("CY72", "LOG_AMOUNT_VOL_20", LV, "RP_PERM_ENT_D4_20",
     "簇 LOG_AMOUNT：高活跃 × 低排列熵(d4)。"),
    ("CY73", "AUC_CLOSE_VOLSHARE_20", AU, "RP_PERM_ENT_D4_20",
     "簇 CLOSE_VOLSHARE：收盘竞价份额 × 低排列熵(d4)。"),
    ("CY74", "PRICE_POSITION_20", PL, "RP_PERM_ENT_D3_60",
     "簇 PRICE_POSITION：20 日位置 × 慢速排列熵。"),
    ("CY75", "ON_CONT_20", OS2, "RP_PERM_ENT_D3_60",
     "簇 ON_CONT：隔夜延续度 × 慢速排列熵。"),
    ("CY76", "PV_ELASTICITY_20", ID, "RP_PERM_ENT_D3_60",
     "簇 PV_ELAST：量价弹性 × 慢速排列熵（CA1 同腿反向取向）。"),
    ("CY77", "CHIP_RANGE_90_60", CD, "RP_UW_CHG_20",
     "簇 CHIP_RANGE：筹码集中 × 水下变化（DA44 同腿反向取向）。"),
    ("CY78", "SHARE_RET_CORR_20", FF, "RP_UW_CHG_20",
     "簇 SHARE_RET：一级流解释力 × 水下变化。"),
    ("CY79", "SCL_DFA_RET_20", SCL, "RP_UW_CHG_20",
     "簇 DFA_RET：路径平滑 × 水下变化（CY09 同腿）。"),
    ("CY80", "IMP_PERM_SHARE_20", ID, "RP_UW_LVL_20",
     "簇 IMP_PERM：冲击永久份额 × 低水下水平（CY52 同腿骨架）。"),
    ("CY81", "AUC_VARIANCE_RATIO_20", AU, "RP_UW_LVL_20",
     "簇 VAR_RATIO：波动配置 × 低水下水平（CM06 同腿反向取向）。"),
    ("CY82", "VT_BUCKET_GINI_20", VT, "RP_UW_LVL_20",
     "簇 VT_GINI：桶到达 Gini × 低水下水平（CN08 同腿反向取向）。"),
    ("CY83", "VOL_PROFILE_DISTANCE", IPD, "RP_UW_CHG_60",
     "簇 VOL_PROFILE：量轮廓异常 × 水下变化60。"),
    ("CY84", "AUC_OPEN_ABSORB_20", AU2, "RP_UW_CHG_60",
     "簇 OPEN_ABSORB：开盘吸收度 × 水下变化60。"),
    ("CY85", "CLOSE5_DAY_CONSIST_20", BF2, "RP_UW_CHG_60",
     "簇 CLOSE5：收盘确认 × 水下变化60（CK04 同腿反向取向）。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage27(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage27_volume_free_replication"
    plan["pairing_note"] = (
        "第 27 阶段配对第 2 批：RPF 作右腿 × 3 新左腿/原子 = 18 条"
        "（18 簇各 1 条，全部新无序对）；本批后阶段配对枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage27

if __name__ == "__main__":
    base.main()
