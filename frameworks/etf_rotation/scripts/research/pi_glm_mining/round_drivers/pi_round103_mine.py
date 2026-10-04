#!/usr/bin/env python3
"""Round 100 driver: stage 17 step 3 — pairing batch 7 (20 pairs).
COUNT_SHIFT skeleton closure + volume_time x auction cross-family pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_103"

VT = "volume_time_1m"
AU = "auction_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


P = [
    ("CS01", "VT_BUCKET_COUNT_SHIFT_20", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "count_vspike",
     "COUNT 骨架收尾：活跃度趋势 × 事件密集（+0.0804/+0.0595/t2.76/+50.7bp），延续。"),
    ("CS02", "VT_BUCKET_COUNT_SHIFT_20", "WORST_DAY_20", "return_tail_shape", "count_worst_day",
     "COUNT 骨架收尾：活跃度趋势 × 无极端损伤（+0.0635/+0.0648/t2.18/+16.2bp），延续。"),
    ("CS03", "VT_BUCKET_COUNT_SHIFT_20", "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "count_edge_conc",
     "COUNT 骨架收尾：活跃度趋势 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。"),
    ("CS04", "VT_BUCKET_COUNT_SHIFT_20", "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "count_dir_skew",
     "COUNT 骨架收尾：活跃度趋势 × 方向偏度（−0.0166/+0.0187/t1.16/+8.7bp），延续。"),
    ("CS05", "VT_AUTOCORR_20", "WORST_DAY_20", "return_tail_shape", "acf_worst_day",
     "DA2 骨架收尾：体量趋势自相关 × 无极端损伤（+0.0635/+0.0648/t2.18/+16.2bp），延续。"),
    ("CS06", "VT_BUCKET_GINI_20", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "gini_vspike",
     "GINI 收尾：到达不均 × 事件密集，延续。"),
    ("CS07", "VT_BUCKET_GINI_20", "WORST_DAY_20", "return_tail_shape", "gini_worst_day",
     "GINI 收尾：到达不均 × 无极端损伤，延续。"),
    ("CS08", "VT_BUCKET_GINI_20", "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "gini_dir_skew",
     "GINI 收尾：到达不均 × 方向偏度，延续。"),
    ("CS09", "VT_SKEW_20", "WORST_DAY_20", "return_tail_shape", "skew_worst_day",
     "SKEW 收尾：体量偏度 × 无极端损伤，延续。"),
    ("CS10", "VT_TAIL_MOM_20", "WORST_DAY_20", "return_tail_shape", "tail_mom_worst_day",
     "TAIL 收尾：尾桶动量 × 无极端损伤，延续。"),
    ("CS11", "VT_TAIL_MOM_20", "VOL_USHAPE_20", "realized_measures_1m", "tail_mom_ushape",
     "TAIL 收尾：尾桶动量 × 体量钟 U 形（−0.0832/−0.0891/t2.12/+33.9bp），延续。"),
    ("CS12", "VT_RV_RATIO_20", "WORST_DAY_20", "return_tail_shape", "rv_worst_day",
     "RV 收尾：体量波动集中 × 无极端损伤，延续。"),
    ("CS13", "VT_AUTOCORR_20", "AUC_VARIANCE_RATIO_20", AU, "acf_var_ratio",
     "跨家族新×新：体量趋势自相关 × 开盘/收盘方差比（−0.1123/−0.0926/t1.46/+38.0bp），延续。"),
    ("CS14", "VT_RV_RATIO_20", "AUC_OPEN_ABSORB_20", AU, "rv_open_absorb",
     "跨家族新×新：体量波动集中 × 开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp），延续。"),
    ("CS15", "VT_BUCKET_GINI_20", "AUC_CLOSE_VOLSHARE_20", AU, "gini_close_volshare",
     "跨家族新×新：到达不均 × 收盘竞价份额（CH6 腿），延续。"),
    ("CS16", "VT_SKEW_20", "AUC_OPEN_VOLSHARE_20", AU, "skew_open_volshare",
     "跨家族新×新：体量偏度 × 集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp），延续。"),
    ("CS17", "VT_TAIL_MOM_20", "AUC_POST_OPEN_REVERT_20", AU, "tail_mom_post_revert",
     "跨家族新×新：尾桶动量 × 开盘后回复比例（−0.0324/+0.0215/t0.68/−16.8bp），延续。"),
    ("CS18", "VT_RV_RATIO_20", "AUC_DISCOVERY_SHIFT_20", AU, "rv_discovery_shift",
     "跨家族新×新：体量波动集中 × 发现重心（CK4 腿），延续。"),
    ("CS19", "VT_BUCKET_GINI_20", "AUC_DISCOVERY_SHIFT_20", AU, "gini_discovery_shift",
     "跨家族新×新：到达不均 × 发现重心，延续。"),
    ("CS20", "VT_AUTOCORR_20", "AUC_POST_OPEN_REVERT_20", AU, "acf_post_revert",
     "跨家族新×新：体量趋势自相关 × 开盘后回复，延续。"),
]

base.CANDIDATES = [
    _pair(cid, left, VT, right, rsrc, mech, hyp) for cid, left, right, rsrc, mech, hyp in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage17(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage17_volume_time_pairing"
    plan["pairing_note"] = "第 17 阶段配对第 7 批：COUNT 骨架收尾 + volume_time × auction 跨家族；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
