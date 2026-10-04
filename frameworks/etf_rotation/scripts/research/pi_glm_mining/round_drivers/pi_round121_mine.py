#!/usr/bin/env python3
"""Round 121 driver: stage 18 step 3 — lunch pairing batch 5 (24 pairs).
CM06 skeleton (GAP x vol-structure) extensions + remaining verticals."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_121"

LB = "lunch_break_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


PR = "LUNCH_PRE_RUN_20"
PO = "LUNCH_POST_RUN_20"
GA = "LUNCH_GAP_ABS_20"
RC = "AM_PM_RET_CORR_20"
LG = "LUNCH_GAP_20"
LR = "LUNCH_REVERT15_20"
ID = "impact_decay_1m"

P = [
    ("CN01", LG, "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "lunchgap_dirskew",
     "CM06 骨架：午间跳空 × 方向偏度（−0.0166/+0.0187/t1.16/+8.7bp），延续。"),
    ("CN02", LG, "PV_ELASTICITY_20", ID, "lunchgap_elastic",
     "骨架延伸：午间跳空 × 量价弹性（−0.1249/−0.0638/t4.00/+52.3bp），延续。"),
    ("CN03", LG, "GAP_FILL_RATE_20", "overnight_structure_1d", "lunchgap_gapfill",
     "骨架延伸：午间跳空 × 缺口修复率（GAP_FILL_RATE_20 与 GFF 同通道），延续。"),
    ("CN04", LG, "RESILIENCY_20", "liquidity_commonality_1m", "lunchgap_resilient",
     "骨架延伸：午间跳空 × 微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp），延续。"),
    ("CN05", LG, "WORST_DAY_20", "return_tail_shape", "lunchgap_worstday",
     "骨架延伸：午间跳空 × 无极端损伤（+0.0635/+0.0648/t2.18/+16.2bp），延续。"),
    ("CN06", LG, "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "lunchgap_events",
     "骨架延伸：午间跳空 × 事件密集（+0.0804/+0.0595/t2.76/+50.7bp），延续。"),
    ("CN07", LG, "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "lunchgap_bigbar",
     "骨架延伸：午间跳空 × 大 bar 强度（+0.0832/+0.0548/t2.92/+41.6bp），延续。"),
    ("CN08", LG, "VT_BUCKET_GINI_20", "volume_time_1m", "lunchgap_gini",
     "骨架延伸：午间跳空 × 桶到达 Gini（−0.0398/−0.0649/t1.61/+24.5bp），延续。"),
    ("CN09", LR, "RESILIENCY_20", "liquidity_commonality_1m", "lunchrevert_resilient",
     "REVERT 残余：午间回复 × 微结构弹性，延续。"),
    ("CN10", LR, "WORST_DAY_20", "return_tail_shape", "lunchrevert_worstday",
     "REVERT 残余：午间回复 × 无极端损伤，延续。"),
    ("CN11", LR, "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "lunchrevert_events",
     "REVERT 残余：午间回复 × 事件密集，延续。"),
    ("CN12", LR, "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "lunchrevert_bigbar",
     "REVERT 残余：午间回复 × 大 bar 强度，延续。"),
    ("CN13", LR, "PV_ELASTICITY_20", ID, "lunchrevert_elastic",
     "REVERT 残余：午间回复 × 量价弹性，延续。"),
    ("CN14", LR, "VT_BUCKET_GINI_20", "volume_time_1m", "lunchrevert_gini",
     "REVERT 残余：午间回复 × 桶到达 Gini，延续。"),
    ("CN15", GA, "PV_ELASTICITY_20", ID, "gapabs_elastic",
     "GA 残余：跳空幅度 × 量价弹性，延续。"),
    ("CN16", GA, "VT_SKEW_20", "volume_time_1m", "gapabs_vtskew",
     "GA 残余：跳空幅度 × 体量时间偏度，延续。"),
    ("CN17", GA, "VT_BUCKET_GINI_20", "volume_time_1m", "gapabs_gini",
     "GA 残余：跳空幅度 × 桶到达 Gini，延续。"),
    ("CN18", GA, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "gapabs_close5",
     "GA 残余：跳空幅度 × 收盘确认，延续。"),
    ("CN19", GA, "AUC_POST_OPEN_REVERT_20", "auction_1m", "gapabs_openrevert",
     "GA 残余：跳空幅度 × 开盘冲击回复，延续。"),
    ("CN20", RC, "IMP_PERM_SHARE_20", ID, "amcorr_perm",
     "RC 残余：时段相关 × 冲击永久份额，延续。"),
    ("CN21", RC, "AUC_VARIANCE_RATIO_20", "auction_1m", "amcorr_varratio",
     "RC 残余：时段相关 × 开收方差比（CM06 同腿），延续。"),
    ("CN22", RC, "VT_SKEW_20", "volume_time_1m", "amcorr_vtskew",
     "RC 残余：时段相关 × 体量时间偏度，延续。"),
    ("CN23", PR, "IMP_PERM_SHARE_20", ID, "prerun_perm",
     "PR 残余：午前抢跑 × 冲击永久份额，延续。"),
    ("CN24", PO, "IMP_PERM_SHARE_20", ID, "postrun_perm",
     "PO 残余：午后抢跑 × 冲击永久份额，延续。"),
]

base.CANDIDATES = [
    _pair(cid, left, LB, right, rsrc, mech, hyp) for cid, left, right, rsrc, mech, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage18(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage18_lunch_pairing"
    plan["pairing_note"] = "第 18 阶段配对第 5 批：CM06 骨架延伸 + 各 lunch 腿残余垂直；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage18

if __name__ == "__main__":
    base.main()
