#!/usr/bin/env python3
"""Round 119 driver: stage 18 step 3 — lunch pairing batch 3 (24 pairs).
CK04/06/13/20/23 skeleton extensions + remaining lunch verticals.
All-new pairs, cross-family only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_119"

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

P = [
    ("CL01", PR, "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "prerun_events",
     "CK04 骨架延伸：午前抢跑 × 事件密集（+0.0804/+0.0595/t2.76/+50.7bp），延续。"),
    ("CL02", PR, "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "prerun_edge_conc",
     "骨架延伸：午前抢跑 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。"),
    ("CL03", PR, "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "prerun_dir_skew",
     "骨架延伸：午前抢跑 × 方向偏度（−0.0166/+0.0187/t1.16/+8.7bp），延续。"),
    ("CL04", PR, "SHARE_RET_CORR_20", "fund_flow", "prerun_primary",
     "骨架延伸：午前抢跑 × 一级流解释力，延续。"),
    ("CL05", PR, "LBAR_CLOCK_STD_20", "largebar_footprint_1m", "prerun_clock",
     "骨架延伸：午前抢跑 × 体量钟离散（BF1 入选 −0.0883/−0.0259/t3.12/+9.6bp），延续。"),
    ("CL06", PR, "VT_RV_RATIO_20", "volume_time_1m", "prerun_vt_rv",
     "骨架延伸：午前抢跑 × 体量波动集中（−0.1182/−0.0415/t2.80/+21.2bp），延续。"),
    ("CL07", PO, "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "postrun_edge_conc",
     "CK06 骨架延伸：午后抢跑 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。"),
    ("CL08", PO, "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "postrun_dir_skew",
     "骨架延伸：午后抢跑 × 方向偏度（−0.0166/+0.0187/t1.16/+8.7bp），延续。"),
    ("CL09", PO, "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "postrun_open30",
     "骨架延伸：午后抢跑 × 开盘配置（−0.1038/−0.0489/t3.30/−10.5bp），延续。"),
    ("CL10", PO, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "postrun_close_confirm",
     "骨架延伸：午后抢跑 × 收盘确认（−0.0233/−0.0313/t−0.30/+27.3bp），延续。"),
    ("CL11", PO, "VT_RV_RATIO_20", "volume_time_1m", "postrun_vt_rv",
     "骨架延伸：午后抢跑 × 体量波动集中（−0.1182/−0.0415/t2.80/+21.2bp），延续。"),
    ("CL12", PO, "VT_BUCKET_GINI_20", "volume_time_1m", "postrun_vt_gini",
     "骨架延伸：午后抢跑 × 桶到达 Gini（−0.0398/−0.0649/t1.61/+24.5bp），延续。"),
    ("CL13", PO, "VT_SKEW_20", "volume_time_1m", "postrun_vt_skew",
     "骨架延伸：午后抢跑 × 体量时间偏度（+0.0158/+0.0026/t1.27/+8.9bp），延续。"),
    ("CL14", PO, "VT_TAIL_MOM_20", "volume_time_1m", "postrun_vt_tail",
     "骨架延伸：午后抢跑 × 尾桶动量（+0.0034/+0.0067/t−0.49/−4.7bp），延续。"),
    ("CL15", PO, "VT_BUCKET_COUNT_SHIFT_20", "volume_time_1m", "postrun_vt_count",
     "骨架延伸：午后抢跑 × 活跃度趋势（−0.0488/+0.0781/t0.44/−47.1bp），延续。"),
    ("CL16", GA, "ULCER_20", "downside_risk", "gapabs_healthy",
     "CK13 骨架延伸：跳空幅度 × 溃疡浅（−0.0415/−0.0607/t0.76/+10.7bp），延续。"),
    ("CL17", GA, "CHIP_RANGE_90_60", "cost_distribution", "gapabs_chip",
     "骨架延伸：跳空幅度 × 筹码集中（−0.0574/−0.0620/t0.70/+14.6bp），延续。"),
    ("CL18", GA, "PRICE_POSITION_20", "price_location", "gapabs_position",
     "骨架延伸：跳空幅度 × 获利位置（+0.0128/+0.0275/t1.64/+8.5bp），延续。"),
    ("CL19", GA, "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "gapabs_bigbar",
     "骨架延伸：跳空幅度 × 大 bar 强度（+0.0832/+0.0548/t2.92/+41.6bp），延续。"),
    ("CL20", GA, "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "gapabs_edge_conc",
     "骨架延伸：跳空幅度 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。"),
    ("CL21", GA, "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "gapabs_dir_skew",
     "骨架延伸：跳空幅度 × 方向偏度（−0.0166/+0.0187/t1.16/+8.7bp），延续。"),
    ("CL22", RC, "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "amcorr_edge_conc",
     "RET_CORR 收尾：时段相关 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。"),
    ("CL23", RC, "SIGN_ACF1_5", "serial_dependence", "amcorr_acf",
     "RET_CORR 收尾：时段相关 × 动量确认（−0.0211/+0.0070/t0.12/+3.9bp），延续。"),
    ("CL24", RC, "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "amcorr_profile",
     "RET_CORR 收尾：时段相关 × 量轮廓异常（+0.0952/+0.0442/t4.04/+10.1bp），延续。"),
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
    plan["pairing_note"] = "第 18 阶段配对第 3 批：CK 骨架延伸 + lunch 残余垂直腿；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage18

if __name__ == "__main__":
    base.main()
