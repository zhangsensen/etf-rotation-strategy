#!/usr/bin/env python3
"""Round 110 driver: stage 17 extension pairing batch 4 (24 pairs).
CZ01 skeleton extensions (ONPREM/ONCONT/GAPFILL x impact & volume_time
third atoms) + overnight x auction full opening. All-new pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_110"

ON = "overnight_structure_1d"
ID = "impact_decay_1m"
VT = "volume_time_1m"
AU = "auction_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


OP = "ON_PREM_20"
OC = "ON_CONT_20"
G = "GAP_FILL_RATE_20"

P = [
    ("DA01", OP, "IMP_DECAY_SLOPE_20", ID, "onprem_decay_slope",
     "骨架延伸：隔夜溢价 × 衰减斜率（+0.0498/+0.0005/t1.70/+4.1bp），延续。"),
    ("DA02", OC, "IMP_DECAY_SLOPE_20", ID, "oncont_decay_slope",
     "骨架延伸：隔夜延续度 × 衰减斜率，延续。"),
    ("DA03", G, "IMP_DECAY_SLOPE_20", ID, "gapfill_decay_slope",
     "骨架延伸：跳空消化 × 衰减斜率，延续。"),
    ("DA04", OC, "PV_SIGNFLIP_20", ID, "oncont_signflip",
     "骨架延伸：隔夜延续度 × 体制切换频率（+0.0187/+0.0029/t0.72/−20.7bp），延续。"),
    ("DA05", G, "PV_SIGNFLIP_20", ID, "gapfill_signflip",
     "骨架延伸：跳空消化 × 体制切换频率，延续。"),
    ("DA06", OC, "VT_SKEW_20", VT, "oncont_vt_skew",
     "骨架延伸：隔夜延续度 × 体量时间偏度（+0.0158/+0.0026/t1.27/+8.9bp），延续。"),
    ("DA07", OC, "VT_TAIL_MOM_20", VT, "oncont_tail_mom",
     "骨架延伸：隔夜延续度 × 尾桶动量（+0.0034/+0.0067/t−0.49/−4.7bp），延续。"),
    ("DA08", OC, "VT_BUCKET_COUNT_SHIFT_20", VT, "oncont_count_trend",
     "骨架延伸：隔夜延续度 × 活跃度趋势（−0.0488/+0.0781/t0.44/−47.1bp），延续。"),
    ("DA09", G, "VT_SKEW_20", VT, "gapfill_vt_skew",
     "骨架延伸：跳空消化 × 体量时间偏度，延续。"),
    ("DA10", G, "VT_TAIL_MOM_20", VT, "gapfill_tail_mom",
     "骨架延伸：跳空消化 × 尾桶动量，延续。"),
    ("DA11", G, "VT_BUCKET_COUNT_SHIFT_20", VT, "gapfill_count_trend",
     "骨架延伸：跳空消化 × 活跃度趋势，延续。"),
    ("DA12", OP, "VT_SKEW_20", VT, "onprem_vt_skew",
     "骨架延伸：隔夜溢价 × 体量时间偏度，延续。"),
    ("DA13", OP, "VT_TAIL_MOM_20", VT, "onprem_tail_mom",
     "骨架延伸：隔夜溢价 × 尾桶动量，延续。"),
    ("DA14", OP, "VT_BUCKET_COUNT_SHIFT_20", VT, "onprem_count_trend",
     "骨架延伸：隔夜溢价 × 活跃度趋势，延续。"),
    ("DA15", OP, "AUC_OPEN_ABSORB_20", AU, "onprem_open_absorb",
     "跨家族收尾：隔夜溢价 × 开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp），延续。"),
    ("DA16", OP, "AUC_OPEN_VOLSHARE_20", AU, "onprem_open_volshare",
     "跨家族收尾：隔夜溢价 × 集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp），延续。"),
    ("DA17", OP, "AUC_CLOSE_VOLSHARE_20", AU, "onprem_close_volshare",
     "跨家族收尾：隔夜溢价 × 收盘竞价份额（+0.0075/−0.0540/t0.77/−11.5bp），延续。"),
    ("DA18", OP, "AUC_POST_OPEN_REVERT_20", AU, "onprem_post_revert",
     "跨家族收尾：隔夜溢价 × 开盘后回复比例（−0.0324/+0.0215/t0.68/−16.8bp），延续。"),
    ("DA19", OP, "AUC_VARIANCE_RATIO_20", AU, "onprem_var_ratio",
     "跨家族收尾：隔夜溢价 × 开盘/收盘方差比（−0.1123/−0.0926/t1.46/+38.0bp），延续。"),
    ("DA20", OC, "AUC_OPEN_ABSORB_20", AU, "oncont_open_absorb",
     "跨家族收尾：隔夜延续度 × 开盘吸收度，延续。"),
    ("DA21", OC, "AUC_OPEN_VOLSHARE_20", AU, "oncont_open_volshare",
     "跨家族收尾：隔夜延续度 × 集合竞价量占比，延续。"),
    ("DA22", OC, "AUC_CLOSE_VOLSHARE_20", AU, "oncont_close_volshare",
     "跨家族收尾：隔夜延续度 × 收盘竞价份额，延续。"),
    ("DA23", OC, "AUC_POST_OPEN_REVERT_20", AU, "oncont_post_revert",
     "跨家族收尾：隔夜延续度 × 开盘后回复比例，延续。"),
    ("DA24", G, "AUC_OPEN_ABSORB_20", AU, "gapfill_open_absorb",
     "跨家族收尾：跳空消化 × 开盘吸收度，延续。"),
]

base.CANDIDATES = [
    _pair(cid, left, ON, right, rsrc, mech, hyp) for cid, left, right, rsrc, mech, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage17(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage17_overnight_pairing"
    plan["pairing_note"] = "第 17 阶段扩展配对第 4 批：CZ01 骨架延伸 + overnight × auction 全开；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
