#!/usr/bin/env python3
"""Round 135 driver: stage 22 batch 2 — remaining left-leg batches.
r134 consumed ON_SKEW/ID_PREM/ON_ID_DIFF/ON_VAR_SHARE left batches.
This round: fresh batches for ON_PREM, GAP_FILL_RATE, ON_CONT (8 pairs each,
right legs pairwise different families) + ON_SKEW as right x 3 new left legs.
All unordered pairs new vs history (hash guard enforces)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_135"

ON = "overnight_structure_1d"


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"on3_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


DR = "downside_risk"
BF = "bar_size_order_flow"
CD = "cost_distribution"
SD = "serial_dependence"
ID = "impact_decay_1m"
VT = "volume_time_1m"
AU = "auction_1m"
RT = "return_tail_shape"
LS = "liquidity_commonality_1m"
LV = "liquidity_variability"
IPD = "intraday_profile_deviation"
LB = "largebar_footprint_1m"
FF = "fund_flow"
SCL = "scaling_memory_1m"
PL = "price_location"

OPS = [
    ("ULCER_20", DR, "健康结构：隔夜溢价在无损伤标的延续（Lou–Polk–Skouras 2019）。"),
    ("TICK_IMBALANCE_20", BF, "主买不平衡：方向性流确认隔夜溢价。"),
    ("CHIP_RANGE_90_60", CD, "筹码集中：隔夜溢价在筹码稳定时更强。"),
    ("SIGN_ACF1_5", SD, "收益动量：隔夜溢价的动量确认。"),
    ("PV_ELASTICITY_20", ID, "量价弹性：低弹性放大隔夜溢价。"),
    ("VT_BUCKET_GINI_20", VT, "桶到达 Gini：交易不均时的隔夜溢价（CN08 同腿）。"),
    ("AUC_VARIANCE_RATIO_20", AU, "波动配置：开收方差比 × 隔夜溢价（CM06 同腿）。"),
    ("WORST_DAY_20", RT, "无极端损伤：隔夜溢价免于尾部拖累。"),
]
GFFS = [
    ("RESILIENCY_20", LS, "微结构弹性：缺口修复在弹性标的更可信。"),
    ("LOG_AMOUNT_VOL_20", LV, "高活跃：修复信号的信息效率。"),
    ("IMP_PERM_SHARE_20", ID, "冲击永久份额：修复的持久成分。"),
    ("CLOSE5_DAY_CONSIST_20", BF, "收盘确认：修复方向的日内确认（CK04 同腿）。"),
    ("VOL_PROFILE_DISTANCE", IPD, "量轮廓异常：修复在轮廓正常时更实。"),
    ("LBAR_CLOCK_STD_20", LB, "体量钟离散 × 缺口修复（BF1 同腿）。"),
    ("SHARE_RET_CORR_20", FF, "一级流解释力 × 缺口修复。"),
    ("SCL_DFA_RET_20", SCL, "路径平滑度 × 缺口修复（DA17 同腿）。"),
]
ONCS = [
    ("ULCER_20", DR, "健康结构 × 隔夜延续度（CZ01 骨架）。"),
    ("TICK_IMBALANCE_20", BF, "主买不平衡 × 隔夜延续度。"),
    ("CHIP_RANGE_90_60", CD, "筹码集中 × 隔夜延续度。"),
    ("SIGN_ACF1_5", SD, "收益动量 × 隔夜延续度。"),
    ("PV_ELASTICITY_20", ID, "量价弹性 × 隔夜延续度。"),
    ("VT_BUCKET_GINI_20", VT, "桶到达 Gini × 隔夜延续度。"),
    ("AUC_VARIANCE_RATIO_20", AU, "波动配置 × 隔夜延续度。"),
    ("PRICE_POSITION_20", PL, "获利位置 × 隔夜延续度。"),
]
SKS = [
    ("WORST_DAY_20", RT, "无极端损伤 × 高隔夜偏度（CW01 簇姊妹取向）。"),
    ("AUC_CLOSE_VOLSHARE_20", AU, "收盘竞价份额 × 高隔夜偏度。"),
    ("SCL_DFA_RET_20", SCL, "路径平滑度 × 高隔夜偏度。"),
]

C = []
i = 0
for left, rights, lsrc in [("ON_PREM_20", OPS, ON),
                           ("GAP_FILL_RATE_20", GFFS, ON),
                           ("ON_CONT_20", ONCS, ON)]:
    for right, rsrc, hyp in rights:
        i += 1
        C.append(_pair(f"CX{i:02d}", left, lsrc, right, rsrc, hyp))
for right, rsrc, hyp in SKS:
    i += 1
    C.append(_pair(f"CX{i:02d}", right, rsrc, "ON_SKEW_20", ON, hyp))

base.CANDIDATES = C

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage22(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage22_overnight_formalized"
    plan["pairing_note"] = (
        "第 22 阶段配对第 2 批：ON_PREM/GAP_FILL_RATE/ON_CONT 左腿批各 8 条"
        "（右腿两两不同族）+ ON_SKEW 作右腿 ×3 = 27 条；簇 ID = 左腿名"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage22

if __name__ == "__main__":
    base.main()
