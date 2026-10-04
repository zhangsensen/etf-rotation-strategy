#!/usr/bin/env python3
"""Round 101 driver: stage 17 step 3 — pairing batch 5 (20 pairs).
CP19/CP20 skeleton rotation into the third impact atom (DECAY_SLOPE,
SIGNFLIP) plus HIVOL/LOVOL coverage probes. All-new pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_101"

VT = "volume_time_1m"
ID = "impact_decay_1m"
LB = "largebar_footprint_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


P = [
    ("CQ01", "VT_SKEW_20", "IMP_DECAY_SLOPE_20", ID, "skew_decay_slope",
     "CP19/20 骨架延伸：体量偏度 × 冲击衰减斜率（+0.0498/+0.0005/t1.70/+4.1bp），延续。"),
    ("CQ02", "VT_SKEW_20", "PV_SIGNFLIP_20", ID, "skew_signflip",
     "骨架延伸：体量偏度 × 量价体制切换频率（+0.0187/+0.0029/t0.72/−20.7bp），延续。"),
    ("CQ03", "VT_AUTOCORR_20", "IMP_DECAY_SLOPE_20", ID, "acf_decay_slope",
     "CO35/36 骨架延伸：体量趋势自相关 × 衰减斜率，延续。"),
    ("CQ04", "VT_AUTOCORR_20", "PV_SIGNFLIP_20", ID, "acf_signflip",
     "骨架延伸：体量趋势自相关 × 体制切换频率，延续。"),
    ("CQ05", "VT_BUCKET_GINI_20", "IMP_DECAY_SLOPE_20", ID, "gini_decay_slope",
     "CO09 骨架延伸：到达不均 × 衰减斜率，延续。"),
    ("CQ06", "VT_BUCKET_GINI_20", "PV_SIGNFLIP_20", ID, "gini_signflip",
     "骨架延伸：到达不均 × 体制切换频率，延续。"),
    ("CQ07", "VT_TAIL_MOM_20", "IMP_DECAY_SLOPE_20", ID, "tail_mom_decay",
     "CN21 骨架延伸：尾桶动量 × 衰减斜率，延续。"),
    ("CQ08", "VT_RV_RATIO_20", "IMP_DECAY_SLOPE_20", ID, "rv_decay_slope",
     "CN10 骨架延伸：体量波动集中 × 衰减斜率，延续。"),
    ("CQ09", "VT_RV_RATIO_20", "PV_SIGNFLIP_20", ID, "rv_signflip",
     "CN10 骨架延伸：体量波动集中 × 体制切换频率，延续。"),
    ("CQ10", "VT_BUCKET_COUNT_SHIFT_20", "PV_ELASTICITY_20", ID, "count_trend_elasticity",
     "CK4 骨架延伸：活跃度趋势 × 量价弹性（CA1 入选），延续。"),
    ("CQ11", "VT_BUCKET_COUNT_SHIFT_20", "IMP_PERM_SHARE_20", ID, "count_trend_permanence",
     "骨架延伸：活跃度趋势 × 冲击永久份额（CA2 入选），延续。"),
    ("CQ12", "VT_BUCKET_COUNT_SHIFT_20", "LBAR_CLOCK_STD_20", LB, "count_trend_clock",
     "骨架延伸：活跃度趋势 × 体量钟离散（BF1 入选），延续。"),
    ("CQ13", "VT_BUCKET_COUNT_SHIFT_20", "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "count_trend_bigbar",
     "骨架延伸：活跃度趋势 × 大 bar 强度（+0.0832/+0.0548/t2.92/+41.6bp），延续。"),
    ("CQ14", "VT_SKEW_20", "VOL_USHAPE_20", "realized_measures_1m", "skew_vol_ushape",
     "骨架延伸：体量偏度 × 体量钟 U 形（−0.0832/−0.0891/t2.12/+33.9bp），延续。"),
    ("CQ15", "VT_AUTOCORR_20", "HIVOL_RET5_20", ID, "acf_hivol_premium",
     "覆盖探边：体量趋势自相关 × 高量溢价（覆盖 212 日，组合覆盖预计不足）。"),
    ("CQ16", "VT_AUTOCORR_20", "LOVOL_RET5_20", ID, "acf_lovol_response",
     "覆盖探边：体量趋势自相关 × 低量日响应（覆盖 51 日，预计 discovery_days 门淘汰）。"),
    ("CQ17", "VT_RV_RATIO_20", "HIVOL_RET5_20", ID, "rv_hivol_premium",
     "覆盖探边：体量波动集中 × 高量溢价。"),
    ("CQ18", "VT_BUCKET_GINI_20", "HIVOL_RET5_20", ID, "gini_hivol_premium",
     "覆盖探边：到达不均 × 高量溢价。"),
    ("CQ19", "VT_TAIL_MOM_20", "HIVOL_RET5_20", ID, "tail_mom_hivol",
     "覆盖探边：尾桶动量 × 高量溢价。"),
    ("CQ20", "VT_SKEW_20", "HIVOL_RET5_20", ID, "skew_hivol",
     "覆盖探边：体量偏度 × 高量溢价。"),
]

base.CANDIDATES = [
    _pair(cid, left, VT, right, (rsrc if rsrc else ID), mech, hyp)
    for cid, left, right, rsrc, mech, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage17(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage17_volume_time_pairing"
    plan["pairing_note"] = "第 17 阶段配对第 5 批：CP19/20 骨架旋转入 impact 第三腿 + HIVOL/LOVOL 覆盖探边；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
