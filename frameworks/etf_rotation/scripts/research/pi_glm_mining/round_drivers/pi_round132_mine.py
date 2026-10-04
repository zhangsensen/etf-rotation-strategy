#!/usr/bin/env python3
"""Round 132 driver: stage 21 batch 2 — remaining legal pairing space.

17:00 accounting: SCL left-leg batches consumed in r131 (7 atoms, 16 pairs).
Remaining = SCL-as-right x <=3 distinct left legs per atom = exactly 21
(LFPOW shadowed, ineligible). All 21 left legs pairwise distinct; every
unordered (left, SCL) pair is new vs r131. r131 recorded VR-family direction
prior (disc ~ -0.08 at preregistered +1): reversed orientation (+1 on X - SCL)
embeds the mean-reversion direction as a new falsifiable preregistration.
After this round stage-21 pairing enumeration = 0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_132"

SCL = "scaling_memory_1m"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": SCL},
        "mechanism": f"scl2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


DR = "downside_risk"
BF = "bar_size_order_flow"
OS = "overnight_structure_1d"
CD = "cost_distribution"
SD = "serial_dependence"
FF = "fund_flow"
LS = "liquidity_commonality_1m"
PL = "price_location"
RT = "return_tail_shape"
LV = "liquidity_variability"
AU = "auction_1m"
ID = "impact_decay_1m"
IVP = "intraday_volume_profile_1m"
VT = "volume_time_1m"
LB = "largebar_footprint_1m"

P = [
    ("CV01", "ULCER_20", DR, "SCL_DFA_ABS_20",
     "簇 ULCER：健康结构 × 低 |r| 长记忆（CU02 同腿反向取向）。"),
    ("CV02", "TICK_IMBALANCE_20", BF, "SCL_DFA_ABS_20",
     "簇 TICK_IMB：主买不平衡 × 低 |r| 长记忆。"),
    ("CV03", "GAP_FILL_RATE_20", OS, "SCL_DFA_ABS_20",
     "簇 GAP_FILL：缺口修复率 × 低 |r| 长记忆（CN03 同腿反向取向）。"),
    ("CV04", "CHIP_RANGE_90_60", CD, "SCL_DFA_RET_20",
     "簇 CHIP_RANGE：筹码集中 × 低路径粗糙度（DFA_RET 原子 t3.08 同腿）。"),
    ("CV05", "SIGN_ACF1_5", SD, "SCL_DFA_RET_20",
     "簇 SIGN_ACF：收益动量 × 低路径粗糙度。"),
    ("CV06", "SHARE_RET_CORR_20", FF, "SCL_DFA_RET_20",
     "簇 SHARE_RET：一级流解释力 × 低路径粗糙度。"),
    ("CV07", "RESILIENCY_20", LS, "SCL_VR5_20",
     "簇 RESILIENCY：微结构弹性 × 低 VR5（VR 反号先验：回复型佳）。"),
    ("CV08", "PRICE_POSITION_20", PL, "SCL_VR5_20",
     "簇 PRICE_POSITION：获利位置 × 低 VR5。"),
    ("CV09", "WORST_DAY_20", RT, "SCL_VR5_20",
     "簇 WORST_DAY：无极端损伤 × 低 VR5。"),
    ("CV10", "LOG_AMOUNT_VOL_20", LV, "SCL_VR15_20",
     "簇 LOG_AMOUNT：高活跃 × 低 VR15（CU02 同簇姊妹腿）。"),
    ("CV11", "CLOSE5_DAY_CONSIST_20", BF, "SCL_VR15_20",
     "簇 CLOSE5：收盘确认 × 低 VR15（CK04 同腿反向取向）。"),
    ("CV12", "ON_PREM_20", OS, "SCL_VR15_20",
     "簇 ON_PREM：隔夜溢价 × 低 VR15（CZ01 同腿反向取向）。"),
    ("CV13", "IMP_PERM_SHARE_20", ID, "SCL_VR30_20",
     "簇 IMP_PERM：冲击永久份额 × 低 VR30。"),
    ("CV14", "OPEN30_VOL_SHARE_20", IVP, "SCL_VR30_20",
     "簇 OPEN30：开盘配置 × 低 VR30（CL09 同腿反向取向）。"),
    ("CV15", "BIGBAR_EDGE_CONC_20", BF, "SCL_VR30_20",
     "簇 BIGBAR_EDGE：大 bar 时点集中 × 低 VR30。"),
    ("CV16", "AUC_VARIANCE_RATIO_20", AU, "SCL_RS_20",
     "簇 VAR_RATIO：波动配置 × 低 R/S（CM06/CR11 同腿骨架）。"),
    ("CV17", "PV_ELASTICITY_20", ID, "SCL_RS_20",
     "簇 PV_ELAST：量价弹性 × 低 R/S（CA1 同腿）。"),
    ("CV18", "VT_BUCKET_GINI_20", VT, "SCL_RS_20",
     "簇 VT_GINI：桶到达 Gini × 低 R/S（CN08 同腿反向取向）。"),
    ("CV19", "LBAR_CLOCK_STD_20", LB, "SCL_VR5_SHIFT_20",
     "簇 LBAR_CLOCK：体量钟离散 × 低 VR5 恶化（BF1 同腿反向取向）。"),
    ("CV20", "VOL_SPIKE_FREQ_20", IVP, "SCL_VR5_SHIFT_20",
     "簇 VOL_SPIKE：事件密集 × 低 VR5 恶化（CJ19 同腿反向取向）。"),
    ("CV21", "AUC_CLOSE_VOLSHARE_20", AU, "SCL_VR5_SHIFT_20",
     "簇 CLOSE_VOLSHARE：收盘竞价份额 × 低 VR5 恶化。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage21(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage21_scaling_memory"
    plan["pairing_note"] = (
        "第 21 阶段配对第 2 批：SCL 作右腿 × 3 新左腿/原子 = 21 条（LFPOW 影子不合格）；"
        "簇 ID = 左腿名（21 簇各 1 条）；VR 反向取向按 r131 方向先验预注册；"
        "本批后阶段配对枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage21

if __name__ == "__main__":
    base.main()
