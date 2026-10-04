#!/usr/bin/env python3
"""Round 109 driver: stage 17 extension pairing batch 3 (24 pairs).
Remaining overnight verticals + cross-family (impact/volume_time) pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_109"

ON = "overnight_structure_1d"
ID = "impact_decay_1m"
VT = "volume_time_1m"


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
    ("CZ01", OP, "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "onprem_edge_conc",
     "骨架收尾：隔夜溢价 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。"),
    ("CZ02", OP, "CLOSE30_VOL_SHARE_20", "intraday_volume_profile_1m", "onprem_close30",
     "骨架收尾：隔夜溢价 × 尾 30 分钟量占比，延续。"),
    ("CZ03", OP, "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "onprem_dir_skew",
     "骨架收尾：隔夜溢价 × 方向偏度（−0.0166/+0.0187/t1.16/+8.7bp），延续。"),
    ("CZ04", OP, "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "onprem_events",
     "骨架收尾：隔夜溢价 × 事件密集（+0.0804/+0.0595/t2.76/+50.7bp），延续。"),
    ("CZ05", OP, "VOL_AUTOCORR_20", "intraday_volume_profile_1m", "onprem_vol_acf",
     "骨架收尾：隔夜溢价 × 量自相关（−0.0571/−0.0218/t0.92/−3.8bp），延续。"),
    ("CZ06", OP, "SHARE_RET_CORR_20", "fund_flow", "onprem_primary",
     "骨架收尾：隔夜溢价 × 一级流解释力，延续。"),
    ("CZ07", OC, "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "oncont_edge_conc",
     "骨架收尾：隔夜延续度 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。"),
    ("CZ08", OC, "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "oncont_dir_skew",
     "骨架收尾：隔夜延续度 × 方向偏度（−0.0166/+0.0187/t1.16/+8.7bp），延续。"),
    ("CZ09", OC, "CLOSE30_VOL_SHARE_20", "intraday_volume_profile_1m", "oncont_close30",
     "骨架收尾：隔夜延续度 × 尾 30 分钟量占比，延续。"),
    ("CZ10", OC, "VOL_AUTOCORR_20", "intraday_volume_profile_1m", "oncont_vol_acf",
     "骨架收尾：隔夜延续度 × 量自相关（−0.0571/−0.0218/t0.92/−3.8bp），延续。"),
    ("CZ11", OC, "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "oncont_open30",
     "骨架收尾：隔夜延续度 × 开盘配置（−0.1038/−0.0489/t3.30/−10.5bp），延续。"),
    ("CZ12", OC, "IMP_PERM_SHARE_20", "impact_decay_1m", "oncont_permanence",
     "跨新家族：隔夜延续度 × 冲击永久份额（CA2 入选 −0.1050/−0.0476/t2.67/+22.1bp），延续。"),
    ("CZ13", G, "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "gapfill_edge_conc",
     "骨架收尾：跳空消化 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。"),
    ("CZ14", G, "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "gapfill_dir_skew",
     "骨架收尾：跳空消化 × 方向偏度（−0.0166/+0.0187/t1.16/+8.7bp），延续。"),
    ("CZ15", G, "CLOSE30_VOL_SHARE_20", "intraday_volume_profile_1m", "gapfill_close30",
     "骨架收尾：跳空消化 × 尾 30 分钟量占比，延续。"),
    ("CZ16", G, "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "gapfill_events",
     "骨架收尾：跳空消化 × 事件密集（+0.0804/+0.0595/t2.76/+50.7bp），延续。"),
    ("CZ17", G, "VOL_AUTOCORR_20", "intraday_volume_profile_1m", "gapfill_vol_acf",
     "骨架收尾：跳空消化 × 量自相关（−0.0571/−0.0218/t0.92/−3.8bp），延续。"),
    ("CZ18", G, "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "gapfill_open30",
     "骨架收尾：跳空消化 × 开盘配置（−0.1038/−0.0489/t3.30/−10.5bp），延续。"),
    ("CZ19", OP, "IMP_PERM_SHARE_20", "impact_decay_1m", "onprem_permanence",
     "跨新家族：隔夜溢价 × 冲击永久份额（CA2 入选 −0.1050/−0.0476/t2.67/+22.1bp），延续。"),
    ("CZ20", OP, "VT_RV_RATIO_20", "volume_time_1m", "onprem_vt_rv_ratio",
     "跨新家族：隔夜溢价 × 体量时间 RV 集中度（−0.1182/−0.0415/t2.80/+21.2bp），延续。"),
    ("CZ21", OC, "VT_RV_RATIO_20", "volume_time_1m", "oncont_vt_rv_ratio",
     "跨新家族：隔夜延续度 × 体量时间 RV 集中度，延续。"),
    ("CZ22", G, "VT_AUTOCORR_20", "volume_time_1m", "gapfill_vt_autocorr",
     "跨新家族：跳空消化 × 体量时间趋势自相关（DA2 入选 −0.0822/−0.0363/t2.32/+17.9bp），延续。"),
    ("CZ23", OP, "VT_BUCKET_GINI_20", "volume_time_1m", "onprem_vt_gini",
     "跨新家族：隔夜溢价 × 桶到达 Gini（CO09 腿 −0.0398/−0.0649/t1.61/+24.5bp），延续。"),
    ("CZ24", G, "VT_RV_RATIO_20", "volume_time_1m", "gapfill_vt_rv_ratio",
     "跨新家族：跳空消化 × 体量时间 RV 集中度，延续。"),
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
    plan["pairing_note"] = "第 17 阶段扩展配对第 3 批：overnight 三骨架剩余垂直腿 + 跨新家族；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
