#!/usr/bin/env python3
"""Round 113 driver: stage 17 extension pairing batch 7 — programmatic
enumeration of remaining overnight pairs + GINI/RV interaction probes.
Candidates are pre-filtered against all previous canonical hashes; the
first 20 untested are taken. Hypotheses are template-generated per leg
role (mechanism documented per leg in earlier rounds' REPORTs)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_113"

ON = "overnight_structure_1d"
ID = "impact_decay_1m"
LB = "largebar_footprint_1m"
AU = "auction_1m"
IV = "intraday_volume_profile_1m"
VT = "volume_time_1m"
RM = "realized_measures_1m"
FF = "fund_flow"

LEFTS = [
    ("GAP_FILL_RATE_20", ON, "跳空消化"),
    ("ON_PREM_20", ON, "隔夜溢价"),
    ("ON_CONT_20", ON, "隔夜延续度"),
    ("VT_RV_RATIO_20", VT, "体量波动集中"),
    ("VT_BUCKET_GINI_20", VT, "到达不均"),
    ("VT_TAIL_MOM_20", VT, "尾桶动量"),
    ("VT_BUCKET_COUNT_SHIFT_20", VT, "活跃度趋势"),
    ("VT_SKEW_20", VT, "体量偏度"),
    ("VT_AUTOCORR_20", VT, "体量趋势自相关"),
]
RIGHTS = [
    ("SHARE_RET_CORR_20", FF), ("CATEGORY_VOL_20", "category_state"),
    ("HIVOL_RET5_20", ID), ("LOVOL_RET5_20", ID),
    ("VOL_USHAPE_20", RM), ("ULCER_20", "downside_risk"),
    ("AUC_OPEN_ABSORB_20", AU), ("AUC_OPEN_VOLSHARE_20", AU),
    ("AUC_CLOSE_VOLSHARE_20", AU), ("AUC_POST_OPEN_REVERT_20", AU),
    ("AUC_VARIANCE_RATIO_20", AU), ("AUC_DISCOVERY_SHIFT_20", AU),
    ("IMP_DECAY_SLOPE_20", ID), ("PV_SIGNFLIP_20", ID),
    ("IMP_PERM_SHARE_20", ID), ("PV_ELASTICITY_20", ID),
    ("LBAR_CLOCK_STD_20", LB), ("BIGBAR_EDGE_CONC_20", "bar_size_order_flow"),
    ("BIGBAR_DIR_SKEW_20", "bar_size_order_flow"),
    ("CLOSE30_VOL_SHARE_20", IV), ("OPEN30_VOL_SHARE_20", IV),
    ("VOL_SPIKE_FREQ_20", IV), ("VOL_AUTOCORR_20", IV),
    ("VT_AUTOCORR_20", VT), ("VT_RV_RATIO_20", VT),
    ("VT_BUCKET_GINI_20", VT), ("VT_SKEW_20", VT),
    ("VT_TAIL_MOM_20", VT), ("VT_BUCKET_COUNT_SHIFT_20", VT),
]
SAME_FAMILY = {
    "volume_time_1m": {"volume_time_1m"},
    "overnight_structure_1d": {"overnight_structure_1d"},
    "impact_decay_1m": {"impact_decay_1m"},
    "largebar_footprint_1m": {"largebar_footprint_1m"},
}


def _pair(cid, left, lsrc, right, rsrc, op="rank_spread"):
    lname = {"GAP_FILL_RATE_20": "跳空消化", "ON_PREM_20": "隔夜溢价",
             "ON_CONT_20": "隔夜延续度", "VT_RV_RATIO_20": "体量波动集中",
             "VT_BUCKET_GINI_20": "到达不均", "VT_TAIL_MOM_20": "尾桶动量",
             "VT_BUCKET_COUNT_SHIFT_20": "活跃度趋势", "VT_SKEW_20": "体量偏度",
             "VT_AUTOCORR_20": "体量趋势自相关"}[left]
    return {
        "id": cid, "operator": op,
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"{lname}_x_{right}".lower(),
        "hypothesis": (f"{lname} × {right}：两腿各自的单原子门 7 数字见历史档案"
                       "（round_053/073/080/095/106 货架与原子重裁）。"
                       "假设：两腿所测结构互相确认时信号为真，延续。"
                       "文献：Clark 1973；Ane–Geman 2000；Lou–Polk–Skouras 2019；"
                       "Bouchaud–Farmer–Lillo 2009；Easley–O'Hara 2012。"),
        "expected_sign": 1,
    }


def _prev_canonical() -> set:
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
    return prev


def main() -> None:
    load_built = base.load_builtin_families
    prev = _prev_canonical()
    cid_n = 0
    keep = []
    for lname, lsrc, ldesc in LEFTS:
        for rname, rsrc in RIGHTS:
            if SAME_FAMILY.get(lsrc) and rsrc in SAME_FAMILY[lsrc]:
                continue
            cid = f"CT{cid_n + 101:02d}"
            cand = _pair(cid, lname, lsrc, rname, rsrc)
            h = base.canonical_expression(cand)
            if h in prev:
                continue
            cand["hypothesis"] = cand["hypothesis"].replace(
                "× " + rname, "× " + rname)  # keep template
            keep.append(cand)
            cid_n += 1
            if len(keep) >= 20:
                break
        if len(keep) >= 20:
            break
    base.CANDIDATES = keep
    print(f"selected {len(keep)} untested pairs")
    for c in keep:
        print("  ", c["id"], c["left"], "x", c["right"])

    orig_cmd_plan = base.cmd_plan

    def _cmd_plan_with_stage17(args):
        orig_cmd_plan(args)
        plan_path = Path(args.output).resolve() / "PLAN.json"
        plan = json.loads(plan_path.read_text())
        plan["stage"] = "stage17_overnight_pairing"
        plan["pairing_note"] = ("第 17 阶段扩展配对第 7 批：程序化枚举下 20 条未测组合"
                                "（引擎 canonical 预过滤）；假设模板化，机制同前批")
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))

    base.cmd_plan = _cmd_plan_with_stage17
    base.main()


if __name__ == "__main__":
    main()
