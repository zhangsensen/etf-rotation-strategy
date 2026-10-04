#!/usr/bin/env python3
"""Round 160 driver: stage 32 batch 2 — RCC-as-right x 3 fresh left legs
per atom = 20 pairs (all left legs pairwise distinct; every unordered pair
new vs r159; VSPIKE collider on BB_CHG auto-swapped). After this round
stage-32 pairing enumeration = 0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_160"

RCC = "range_contraction_cycle"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": RCC},
        "mechanism": f"rcc2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


SD = "serial_dependence"
CD = "cost_distribution"
LB = "largebar_footprint_1m"
LS = "liquidity_commonality_1m"
ID = "impact_decay_1m"
FF = "fund_flow"
ID2 = "impact_decay_1m"
SCL = "scaling_memory_1m"
RT = "return_tail_shape"
LV = "liquidity_variability"
OS = "overnight_structure_1d"
OS2 = "overnight_structure_1d"
SCL2 = "scaling_memory_1m"
AU = "auction_1m"
IPD = "intraday_profile_deviation"
PL = "price_location"
IVP = "intraday_volume_profile_1m"
AU2 = "auction_1m"
OS3 = "overnight_structure_1d"
DR = "downside_risk"
AU3 = "auction_1m"

P = [
    ("CZ123", "SIGN_ACF1_5", SD, "RCC_REL_RANGE_20",
     "簇 SIGN_ACF：收益动量 × 区间水平。"),
    ("CZ124", "CHIP_RANGE_90_60", CD, "RCC_REL_RANGE_20",
     "簇 CHIP_RANGE：筹码集中 × 区间水平。"),
    ("CZ125", "LBAR_CLOCK_STD_20", LB, "RCC_REL_RANGE_20",
     "簇 LBAR_CLOCK：体量钟离散 × 区间水平（BF1 同腿反向取向）。"),
    ("CZ126", "RESILIENCY_20", LS, "RCC_NARROW_STREAK_20",
     "簇 RESILIENCY：微结构弹性 × 窄幅连串（CZ110 同腿反向取向）。"),
    ("CZ127", "IMP_PERM_SHARE_20", ID, "RCC_NARROW_STREAK_20",
     "簇 IMP_PERM：冲击永久份额 × 窄幅连串（CY52 同腿骨架）。"),
    ("CZ128", "SHARE_RET_CORR_20", FF, "RCC_NARROW_STREAK_20",
     "簇 SHARE_RET：一级流解释力 × 窄幅连串。"),
    ("CZ129", "PV_ELASTICITY_20", ID2, "RCC_NR7_FREQ_20",
     "簇 PV_ELAST：量价弹性 × NR7 频率（CA1 同腿反向取向）。"),
    ("CZ130", "SCL_DFA_RET_20", SCL, "RCC_NR7_FREQ_20",
     "簇 DFA_RET：路径平滑 × NR7 频率（CY09 同腿反向取向）。"),
    ("CZ131", "WORST_DAY_20", RT, "RCC_NR7_FREQ_20",
     "簇 WORST_DAY：无极端损伤 × NR7 频率。"),
    ("CZ132", "LOG_AMOUNT_VOL_20", LV, "RCC_NR7_AGE_20",
     "簇 LOG_AMOUNT：高活跃 × NR7 距今。"),
    ("CZ133", "ULCER_20", DR, "RCC_NR7_AGE_20",
     "簇 ULCER：健康结构 × NR7 距今（CZ111 同腿反向取向）。"),
    ("CZ134", "GAP_FILL_RATE_20", OS2, "RCC_NR7_AGE_20",
     "簇 GAP_FILL：缺口修复率 × NR7 距今（CN03 同腿反向取向）。"),
    ("CZ135", "SCL_DFA_ABS_20", SCL2, "RCC_BB_SQUEEZE_20",
     "簇 DFA_ABS：|r| 长记忆 × squeeze 深度（CU02 同腿反向取向）。"),
    ("CZ136", "AUC_VARIANCE_RATIO_20", AU, "RCC_BB_SQUEEZE_20",
     "簇 VAR_RATIO：波动配置 × squeeze 深度（CM06 同腿反向取向）。"),
    ("CZ137", "VOL_PROFILE_DISTANCE", IPD, "RCC_BB_SQUEEZE_20",
     "簇 VOL_PROFILE：量轮廓异常 × squeeze 深度。"),
    ("CZ138", "PRICE_POSITION_20", PL, "RCC_BB_CHG_20",
     "簇 PRICE_POSITION：获利位置 × 带宽变化。"),
    ("CZ140", "AUC_CLOSE_VOLSHARE_20", AU2, "RCC_BB_CHG_20",
     "簇 CLOSE_VOLSHARE：收盘竞价份额 × 带宽变化。"),
    ("CZ141", "ON_CONT_20", OS3, "RCC_AR1_20",
     "簇 ON_CONT：隔夜延续度 × 区间持续性。"),
    ("CZ143", "AUC_OPEN_ABSORB_20", AU3, "RCC_AR1_20",
     "簇 OPEN_ABSORB：开盘吸收度 × 区间持续性。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage32(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage32_range_contraction"
    plan["pairing_note"] = (
        "第 32 阶段配对第 2 批：RCC 作右腿 × 3 新左腿/原子 = 20 条"
        "（20 簇各 1 条，全部新无序对）；本批后阶段配对枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage32

if __name__ == "__main__":
    base.main()
