#!/usr/bin/env python3
"""Round 129 driver: stage 20 batch 2 — remaining legal pairing space.

17:00 accounting: OFP left-leg batches consumed in r128 (7 atoms, 17 pairs).
Remaining = OFP-as-right x <=3 distinct left legs per atom = exactly 21.
All 21 left legs pairwise distinct (one 1-candidate batch each); every
unordered (left, OFP) pair is new vs r128 (engine hash enforces).
After this round stage-20 pairing enumeration = 0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_129"

OFP = "orderflow_persistence_1m"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": OFP},
        "mechanism": f"ofp2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


DR = "downside_risk"
SD = "serial_dependence"
FF = "fund_flow"
VT = "volume_time_1m"
OS = "overnight_structure_1d"
CD = "cost_distribution"
BF = "bar_size_order_flow"
PL = "price_location"
RT = "return_tail_shape"
LS = "liquidity_commonality_1m"
LB = "largebar_footprint_1m"
ID = "impact_decay_1m"
AU = "auction_1m"
LV = "liquidity_variability"

P = [
    ("CT01", "ULCER_20", DR, "OFP_AC1_20",
     "簇 ULCER：溃疡浅 × 低流持续——健康结构在流稳定时兑现。"),
    ("CT02", "SIGN_ACF1_5", SD, "OFP_AC1_20",
     "簇 SIGN_ACF：收益动量 × 低流持续（双持续互斥检验）。"),
    ("CT03", "SHARE_RET_CORR_20", FF, "OFP_AC1_20",
     "簇 SHARE_RET：一级流解释力 × 低流持续。"),
    ("CT04", "VT_BUCKET_GINI_20", VT, "OFP_AC5_20",
     "簇 VT_GINI：桶到达 Gini × 低中段流记忆（CN08 同腿反向取向）。"),
    ("CT05", "ON_PREM_20", OS, "OFP_AC5_20",
     "簇 ON_PREM：隔夜溢价 × 低中段流记忆（CZ01 同腿反向取向）。"),
    ("CT06", "CHIP_RANGE_90_60", CD, "OFP_AC5_20",
     "簇 CHIP_RANGE：筹码集中 × 低中段流记忆。"),
    ("CT07", "TICK_IMBALANCE_20", BF, "OFP_DECAY_20",
     "簇 TICK_IMB：主买不平衡 × 长流记忆——双确认。"),
    ("CT08", "PRICE_POSITION_20", PL, "OFP_DECAY_20",
     "簇 PRICE_POSITION：获利位置 × 长流记忆。"),
    ("CT09", "WORST_DAY_20", RT, "OFP_DECAY_20",
     "簇 WORST_DAY：无极端损伤 × 长流记忆。"),
    ("CT10", "RESILIENCY_20", LS, "OFP_RUN_MEAN_20",
     "簇 RESILIENCY：微结构弹性 × 低游程延伸（CS01 同腿反向取向）。"),
    ("CT11", "BIGBAR_EDGE_CONC_20", BF, "OFP_RUN_MEAN_20",
     "簇 BIGBAR_EDGE：大 bar 时点集中 × 低游程延伸。"),
    ("CT12", "VT_SKEW_20", VT, "OFP_RUN_MEAN_20",
     "簇 VT_SKEW：体量时间偏度 × 低游程延伸。"),
    ("CT13", "LBAR_CLOCK_STD_20", LB, "OFP_RUN_MAX_20",
     "簇 LBAR_CLOCK：体量钟离散 × 低极端游程（BF1 同腿反向取向）。"),
    ("CT14", "IMP_PERM_SHARE_20", ID, "OFP_RUN_MAX_20",
     "簇 IMP_PERM：冲击永久份额 × 低极端游程。"),
    ("CT15", "AUC_CLOSE_VOLSHARE_20", AU, "OFP_RUN_MAX_20",
     "簇 CLOSE_VOLSHARE：收盘竞价份额 × 低极端游程。"),
    ("CT16", "AUC_VARIANCE_RATIO_20", AU, "OFP_LEAD_20",
     "簇 VAR_RATIO：波动配置 × 高流领先价（CR11 同腿骨架）。"),
    ("CT17", "LOG_AMOUNT_VOL_20", LV, "OFP_LEAD_20",
     "簇 LOG_AMOUNT：高活跃 × 高流领先价。"),
    ("CT18", "PV_ELASTICITY_20", ID, "OFP_LEAD_20",
     "簇 PV_ELAST：量价弹性 × 高流领先价（CA1/CQ31 同腿）。"),
    ("CT19", "CLOSE5_DAY_CONSIST_20", BF, "OFP_SWITCH_20",
     "簇 CLOSE5：收盘确认 × 高方向切换（CK04 同腿反向取向）。"),
    ("CT20", "GAP_FILL_RATE_20", OS, "OFP_SWITCH_20",
     "簇 GAP_FILL：缺口修复率 × 高方向切换。"),
    ("CT21", "VT_RV_RATIO_20", VT, "OFP_SWITCH_20",
     "簇 VT_RV_RATIO：体量波动集中 × 高方向切换。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage20(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage20_orderflow_persistence"
    plan["pairing_note"] = (
        "第 20 阶段配对第 2 批：OFP 作右腿 × 3 新左腿/原子的剩余合法空间 = 21 条；"
        "簇 ID = 左腿名（21 簇各 1 条）；本批后阶段配对枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage20

if __name__ == "__main__":
    base.main()
