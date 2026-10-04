#!/usr/bin/env python3
"""Round 126 driver: stage 19 batch 2 — the remaining legal pairing space.

17:00 rule accounting: each VOV atom consumed its one left-leg batch in r125
(3 pairs each). Remaining legal pairs = VOV-as-right x <=3 distinct left legs
per VOV atom = exactly 18. All left legs pairwise distinct (one batch each).
If this batch zero-passes, next round legal space = 0 -> stage exhaustion.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_126"

VOV = "vol_of_vol_1m"


def _pair(cid, left, lsrc, right, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": VOV},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


LS = "liquidity_commonality_1m"
LV = "liquidity_variability"
BF = "bar_size_order_flow"
IVP = "intraday_volume_profile_1m"
OS = "overnight_structure_1d"
DR = "downside_risk"
ID = "impact_decay_1m"
SD = "serial_dependence"
AU = "auction_1m"
CD = "cost_distribution"
PL = "price_location"
RT = "return_tail_shape"
VT = "volume_time_1m"
FF = "fund_flow"

# cluster id = left leg name (17:00 rule); 18 distinct left legs;
# every unordered (left, VOV) pair is new vs r125 (engine hash enforces commutativity)
P = [
    ("CR01", "RESILIENCY_20", LS, "VOV_HAR_RESID_20",
     "簇 RESILIENCY：高弹性 × 低波动意外——弹性红利只在无意外波动时兑现。"),
    ("CR02", "LOG_AMOUNT_VOL_20", LV, "VOV_HAR_RESID_20",
     "簇 LOG_AMOUNT：高活跃 × 低波动意外——活跃定价效率需要稳定波动体制。"),
    ("CR03", "GAP_FILL_RATE_20", OS, "VOV_HAR_RESID_20",
     "簇 GAP_FILL：高缺口修复 × 低波动意外。"),
    ("CR04", "ULCER_20", DR, "VOV_HAR_RESID_SIGN_20",
     "簇 ULCER：溃疡浅 × 低符号漂移——体制稳定放大健康结构。"),
    ("CR05", "BIGBAR_EDGE_CONC_20", BF, "VOV_HAR_RESID_SIGN_20",
     "簇 BIGBAR_EDGE：大 bar 时点集中 × 低符号漂移。"),
    ("CR06", "TICK_IMBALANCE_20", BF, "VOV_HAR_RESID_SIGN_20",
     "簇 TICK_IMB：主买不平衡 × 低符号漂移。"),
    ("CR07", "SIGN_ACF1_5", SD, "VOV_TERM_RATIO_20_60",
     "簇 SIGN_ACF：动量确认 × 低期限比——动量要求无短期波动升温。"),
    ("CR08", "IMP_PERM_SHARE_20", ID, "VOV_TERM_RATIO_20_60",
     "簇 IMP_PERM：冲击永久份额 × 低期限比。"),
    ("CR09", "PV_ELASTICITY_20", ID, "VOV_TERM_RATIO_20_60",
     "簇 PV_ELAST：弹性 × 低期限比。"),
    ("CR10", "VT_BUCKET_GINI_20", VT, "VOV_LOGRV_STD_20",
     "簇 VT_GINI：桶到达 Gini × 低 vol-of-vol（CN08 同腿反向取向）。"),
    ("CR11", "AUC_VARIANCE_RATIO_20", AU, "VOV_LOGRV_STD_20",
     "簇 VAR_RATIO：波动配置 × 低 vol-of-vol（CM06 同腿反向取向）。"),
    ("CR12", "CLOSE5_DAY_CONSIST_20", BF, "VOV_LOGRV_STD_20",
     "簇 CLOSE5：收盘确认 × 低 vol-of-vol（CK04 同腿反向取向）。"),
    ("CR13", "CHIP_RANGE_90_60", CD, "VOV_RV_CV_20",
     "簇 CHIP_RANGE：筹码集中 × 低 RV 变异系数。"),
    ("CR14", "PRICE_POSITION_20", PL, "VOV_RV_CV_20",
     "簇 PRICE_POSITION：获利位置 × 低 RV 变异系数。"),
    ("CR15", "WORST_DAY_20", RT, "VOV_RV_CV_20",
     "簇 WORST_DAY：无极端损伤 × 低 RV 变异系数。"),
    ("CR16", "VT_SKEW_20", VT, "VOV_RV_AUTOCORR_20",
     "簇 VT_SKEW：体量时间偏度 × 低波动自相关。"),
    ("CR17", "SHARE_RET_CORR_20", FF, "VOV_RV_AUTOCORR_20",
     "簇 SHARE_RET：一级流解释力 × 低波动自相关。"),
    ("CR18", "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "VOV_RV_AUTOCORR_20",
     "簇 LBAR_CLOCK：体量钟离散 × 低波动自相关（BF1 同腿反向取向）。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, f"vovrev_{cid.lower()}", hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage19(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage19_vol_of_vol"
    plan["pairing_note"] = (
        "第 19 阶段配对第 2 批：17:00 口径下 VOV 作右腿 x <=3 左腿的剩余合法空间 = 18 条；"
        "簇 ID = 左腿名，每簇单条；本批后阶段配对空间枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage19

if __name__ == "__main__":
    base.main()
