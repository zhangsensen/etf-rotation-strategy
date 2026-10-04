#!/usr/bin/env python3
"""Round 139 driver: stage 24 batch 2 — remaining legal pairing space.
r138 consumed the 4 clean atoms' left batches. Remaining = RT-as-right x
<=3 distinct left legs per atom = exactly 12 (= floor). All unordered pairs
new vs r138. After this round stage-24 pairing enumeration = 0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_139"

RTF = "relative_tick_1m"


def _pair(cid, left, lsrc, right, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": RTF},
        "mechanism": f"rt2_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


DR = "downside_risk"
SD = "serial_dependence"
IVP = "intraday_volume_profile_1m"
LS = "liquidity_commonality_1m"
PL = "price_location"
OS = "overnight_structure_1d"
ID = "impact_decay_1m"
BF = "bar_size_order_flow"
VT = "volume_time_1m"
FF = "fund_flow"
RT2 = "return_tail_shape"
OS2 = "overnight_structure_1d"

P = [
    ("CY22", "ULCER_20", DR, "RT_ONETICK_20",
     "簇 ULCER：健康结构 × 低量子化（DA24 同腿反向取向）。"),
    ("CY23", "SIGN_ACF1_5", SD, "RT_ONETICK_20",
     "簇 SIGN_ACF：收益动量 × 低量子化。"),
    ("CY24", "OPEN30_VOL_SHARE_20", IVP, "RT_ONETICK_20",
     "簇 OPEN30：开盘配置 × 低量子化（CL09 同腿反向取向）。"),
    ("CY25", "RESILIENCY_20", LS, "RT_CLUSTER5_20",
     "簇 RESILIENCY：微结构弹性 × 低价格聚集。"),
    ("CY26", "PRICE_POSITION_20", PL, "RT_CLUSTER5_20",
     "簇 PRICE_POSITION：获利位置 × 低价格聚集。"),
    ("CY27", "ON_PREM_20", OS, "RT_CLUSTER5_20",
     "簇 ON_PREM：隔夜溢价 × 低价格聚集（CZ01 同腿反向取向）。"),
    ("CY28", "PV_ELASTICITY_20", ID, "RT_ZERO_SHIFT_20",
     "簇 PV_ELAST：量价弹性 × 低离散化恶化（CA1 同腿）。"),
    ("CY29", "TICK_IMBALANCE_20", BF, "RT_ZERO_SHIFT_20",
     "簇 TICK_IMB：主买不平衡 × 低离散化恶化。"),
    ("CY30", "VT_BUCKET_GINI_20", VT, "RT_ZERO_SHIFT_20",
     "簇 VT_GINI：桶到达 Gini × 低离散化恶化（CN08 同腿反向取向）。"),
    ("CY31", "SHARE_RET_CORR_20", FF, "RT_ENTROPY_20",
     "簇 SHARE_RET：一级流解释力 × 高收益熵。"),
    ("CY32", "WORST_DAY_20", RT2, "RT_ENTROPY_20",
     "簇 WORST_DAY：无极端损伤 × 高收益熵。"),
    ("CY33", "GAP_FILL_RATE_20", OS2, "RT_ENTROPY_20",
     "簇 GAP_FILL：缺口修复率 × 高收益熵（CN03 同腿反向取向）。"),
]

base.CANDIDATES = [
    _pair(cid, left, lsrc, right, hyp) for cid, left, lsrc, right, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage24(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage24_relative_tick"
    plan["pairing_note"] = (
        "第 24 阶段配对第 2 批：RT 作右腿 × 3 新左腿/原子 = 12 条（恰达下限）；"
        "簇 ID = 左腿名；本批后阶段配对枚举为零"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage24

if __name__ == "__main__":
    base.main()
