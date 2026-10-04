#!/usr/bin/env python3
"""Round 111 driver: stage 17 extension pairing batch 5 (17 pairs).
Full enumeration of remaining overnight x {impact/volume_time/auction}
combinations. All-new pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_111"

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
    ("CX19", OP, "PV_SIGNFLIP_20", ID, "onprem_signflip",
     "骨架收尾：隔夜溢价 × 体制切换频率（+0.0187/+0.0029/t0.72/−20.7bp），延续。"),
    ("CX20", OP, "HIVOL_RET5_20", ID, "onprem_hivol",
     "骨架收尾：隔夜溢价 × 高量溢价（覆盖 212 日，组合覆盖预计不足）。"),
    ("CX21", OP, "LOVOL_RET5_20", ID, "onprem_lovol",
     "骨架收尾：隔夜溢价 × 低量日响应，延续。"),
    ("CX22", OP, "AUC_DISCOVERY_SHIFT_20", AU, "onprem_discovery_shift",
     "骨架收尾：隔夜溢价 × 发现重心（CK4 腿），延续。"),
    ("CX23", OC, "HIVOL_RET5_20", ID, "oncont_hivol",
     "骨架收尾：隔夜延续度 × 高量溢价，延续。"),
    ("CX24", OC, "LOVOL_RET5_20", ID, "oncont_lovol",
     "骨架收尾：隔夜延续度 × 低量日响应，延续。"),
    ("CX25", OC, "AUC_VARIANCE_RATIO_20", AU, "oncont_var_ratio",
     "骨架收尾：隔夜延续度 × 开盘/收盘方差比（−0.1123/−0.0926/t1.46/+38.0bp），延续。"),
    ("CX26", OC, "AUC_DISCOVERY_SHIFT_20", AU, "oncont_discovery_shift",
     "骨架收尾：隔夜延续度 × 发现重心，延续。"),
    ("CX27", G, "IMP_PERM_SHARE_20", ID, "gapfill_permanence",
     "骨架收尾：跳空消化 × 冲击永久份额（CA2 入选 −0.1050/−0.0476/t2.67/+22.1bp），延续。"),
    ("CX28", G, "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "gapfill_clock_anomaly",
     "骨架收尾：跳空消化 × 体量钟离散（BF1 入选 −0.0883/−0.0259/t3.12/+9.6bp），延续。"),
    ("CX29", G, "VT_BUCKET_GINI_20", VT, "gapfill_vt_gini",
     "骨架收尾：跳空消化 × 桶到达 Gini（CO09 腿 −0.0398/−0.0649/t1.61/+24.5bp），延续。"),
    ("CX30", G, "SHARE_RET_CORR_20", "fund_flow", "gapfill_primary",
     "骨架收尾：跳空消化 × 一级流解释力，延续。"),
    ("CX31", G, "HIVOL_RET5_20", ID, "gapfill_hivol",
     "骨架收尾：跳空消化 × 高量溢价，延续。"),
    ("CX32", G, "LOVOL_RET5_20", ID, "gapfill_lovol",
     "骨架收尾：跳空消化 × 低量日响应，延续。"),
    ("CX33", G, "VOL_USHAPE_20", "realized_measures_1m", "gapfill_vol_ushape",
     "骨架收尾：跳空消化 × 体量钟 U 形（−0.0832/−0.0891/t2.12/+33.9bp），延续。"),
    ("CX34", G, "ULCER_20", "downside_risk", "gapfill_healthy",
     "骨架收尾：跳空消化 × 溃疡浅（−0.0415/−0.0607/t0.76/+10.7bp），延续。"),
    ("CX35", G, "AUC_DISCOVERY_SHIFT_20", AU, "gapfill_discovery_shift",
     "骨架收尾：跳空消化 × 发现重心（CK4 腿），延续。"),
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
    plan["pairing_note"] = "第 17 阶段扩展配对第 5 批：overnight 残余全枚举（17 条）；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
