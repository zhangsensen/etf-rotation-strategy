#!/usr/bin/env python3
"""Round 114 driver: stage 17 extension closing batch — the last 14 untested
overnight-extension pairs (full enumeration after r097-r113). Per master
directive: remaining pairs merged into one >=12 round. If zero passes,
streak reaches 3 -> stage exhaustion per contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_114"

ON = "overnight_structure_1d"
ID = "impact_decay_1m"
VT = "volume_time_1m"
AU = "auction_1m"
RM = "realized_measures_1m"
FF = "fund_flow"


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
    ("CVA1", OP, "VOL_USHAPE_20", RM, "onprem_vol_ushape",
     "ONPREM 20-pool 收尾：隔夜溢价 × 体量钟 U 形（−0.0832/−0.0891/t2.12/+33.9bp），延续。"),
    ("CVA2", OP, "SHARE_RET_CORR_20", FF, "onprem_primary",
     "ONPREM 20-pool 收尾：隔夜溢价 × 一级流解释力，延续。"),
    ("CVA3", OC, "VOL_USHAPE_20", RM, "oncont_vol_ushape",
     "ONCONT 20-pool 收尾：隔夜延续度 × 体量钟 U 形，延续。"),
    ("CVA4", OC, "SHARE_RET_CORR_20", FF, "oncont_primary",
     "ONCONT 20-pool 收尾：隔夜延续度 × 一级流解释力，延续。"),
    ("CVA5", G, "VT_BUCKET_GINI_20", VT, "gapfill_vt_gini",
     "GAPFILL×VT 收尾：跳空消化 × 桶到达 Gini（CO09 腿 −0.0398/−0.0649/t1.61/+24.5bp），延续。"),
    ("CVA6", G, "VT_SKEW_20", VT, "gapfill_vt_skew",
     "GAPFILL×VT 收尾：跳空消化 × 体量时间偏度，延续。"),
    ("CVA7", G, "VT_TAIL_MOM_20", VT, "gapfill_vt_tail_mom",
     "GAPFILL×VT 收尾：跳空消化 × 尾桶动量，延续。"),
    ("CVA8", G, "VT_BUCKET_COUNT_SHIFT_20", VT, "gapfill_vt_count_trend",
     "GAPFILL×VT 收尾：跳空消化 × 活跃度趋势（审超 −47.1bp 反号腿），延续。"),
    ("CVA9", G, "AUC_OPEN_VOLSHARE_20", AU, "gapfill_open_volshare",
     "GAPFILL×auction 收尾：跳空消化 × 集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp），延续。"),
    ("CVA10", G, "AUC_CLOSE_VOLSHARE_20", AU, "gapfill_close_volshare",
     "GAPFILL×auction 收尾：跳空消化 × 收盘竞价份额（+0.0075/−0.0540/t0.77/−11.5bp），延续。"),
    ("CVA11", G, "AUC_POST_OPEN_REVERT_20", AU, "gapfill_post_revert",
     "GAPFILL×auction 收尾：跳空消化 × 开盘后回复比例（−0.0324/+0.0215/t0.68/−16.8bp），延续。"),
    ("CVA12", G, "AUC_VARIANCE_RATIO_20", AU, "gapfill_var_ratio",
     "GAPFILL×auction 收尾：跳空消化 × 开盘/收盘方差比（−0.1123/−0.0926/t1.46/+38.0bp），延续。"),
    ("CVA13", OC, "HIVOL_RET5_20", ID, "oncont_hivol",
     "ONCONT×impact 收尾：隔夜延续度 × 高量溢价（覆盖 212 日探边）。"),
    ("CVA14", OC, "LOVOL_RET5_20", ID, "oncont_lovol",
     "ONCONT×impact 收尾：隔夜延续度 × 低量日响应（覆盖 51 日探边）。"),
]

base.CANDIDATES = [
    _pair(rec[0], rec[1], ON, rec[2], rec[3], rec[4], rec[5]) for rec in P
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage17(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage17_overnight_pairing"
    plan["pairing_note"] = ("第 17 阶段扩展收尾批：最后 14 条合法未测配对（≥12 达标，"
                            "程序化枚举确认此后配对空间用尽）；同族不配")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


# Pre-filter against all previous canonical hashes (keep up to 20 untested).
def _prefilter():
    prev = set()
    for pf in sorted(Path("outputs").glob("round_*/PLAN.json")):
        if pf.parent.name == base.ROUND_ID:
            continue
        try:
            plan = json.loads(pf.read_text())
        except Exception:
            continue
        for c in plan.get("candidates", []):
            try:
                prev.add(base.canonical_expression(c))
            except Exception:
                continue
    keep, seen = [], set()
    for c in base.CANDIDATES:
        h = base.canonical_expression(c)
        if h in prev or h in seen:
            print("  drop duplicate:", c["id"], c["left"]["name"], "x", c["right"]["name"])
            continue
        seen.add(h)
        keep.append(c)
    base.CANDIDATES = keep[:20]
    print(f"prefilter: kept {len(base.CANDIDATES)} untested candidates")


_prefilter()

base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
