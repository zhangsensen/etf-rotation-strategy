#!/usr/bin/env python3
"""Round 105 driver: stage 17 step 3 — pairing batch 9 (20 pairs).
Full enumeration of remaining volume_time x auction pairs + 3 interaction
probes on the CT11 skeleton (rank_interaction is a distinct, untested
construction class for these pairs)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_105"

VT = "volume_time_1m"
AU = "auction_1m"
ID = "impact_decay_1m"
LB = "largebar_footprint_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp, op="rank_spread"):
    return {
        "id": cid, "operator": op,
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


P = [
        ('CU01', 'VT_SKEW_20', 'AUC_DISCOVERY_SHIFT_20', AU, 'skew_discovery_shift2', 'SKEW 收尾：体量偏度 × 发现重心（CK4 腿），延续。'),
        ('CU02', 'VT_RV_RATIO_20', 'AUC_OPEN_VOLSHARE_20', AU, 'rv_open_volshare2', 'RV 收尾：体量波动集中 × 集合竞价量占比，延续。'),
        ('CU03', 'VT_RV_RATIO_20', 'AUC_CLOSE_VOLSHARE_20', AU, 'rv_close_volshare2', 'RV 收尾：体量波动集中 × 收盘竞价份额，延续。'),
        ('CU04', 'VT_RV_RATIO_20', 'AUC_POST_OPEN_REVERT_20', AU, 'rv_post_revert', 'RV 收尾：体量波动集中 × 开盘后回复比例，延续。'),
        ('CU05', 'VT_BUCKET_GINI_20', 'AUC_POST_OPEN_REVERT_20', 'auction_1m', 'gini_post_revert', 'GINI 收尾：到达不均 × 开盘后回复比例，延续。'),
        ('CU06', 'VT_BUCKET_GINI_20', 'AUC_OPEN_VOLSHARE_20', 'auction_1m', 'gini_open_volshare', 'GINI 收尾：到达不均 × 集合竞价量占比，延续。'),
        ('CU07', 'VT_BUCKET_GINI_20', 'LOVOL_RET5_20', 'impact_decay_1m', 'gini_lovol', 'GINI 收尾：到达不均 × 低量日响应，延续。'),
        ('CU08', 'VT_SKEW_20', 'LOVOL_RET5_20', 'impact_decay_1m', 'skew_lovol', 'SKEW 收尾：体量偏度 × 低量日响应，延续。'),
        ('CU09', 'VT_SKEW_20', 'BIGBAR_EDGE_CONC_20', 'bar_size_order_flow', 'skew_edge_conc2', 'SKEW 收尾：体量偏度 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。'),
        ('CU10', 'VT_TAIL_MOM_20', 'LOVOL_RET5_20', 'impact_decay_1m', 'tail_mom_lovol', 'TAIL 收尾：尾桶动量 × 低量日响应，延续。'),
        ('CU11', 'VT_BUCKET_COUNT_SHIFT_20', 'IMP_DECAY_SLOPE_20', 'impact_decay_1m', 'count_decay_slope', 'COUNT 收尾：活跃度趋势 × 衰减斜率（+0.0498/+0.0005/t1.70/+4.1bp），延续。'),
        ('CU12', 'VT_BUCKET_COUNT_SHIFT_20', 'PV_SIGNFLIP_20', 'impact_decay_1m', 'count_signflip', 'COUNT 收尾：活跃度趋势 × 体制切换频率，延续。'),
        ('CU13', 'VT_BUCKET_COUNT_SHIFT_20', 'AUC_POST_OPEN_REVERT_20', 'auction_1m', 'count_post_revert', 'COUNT 收尾：活跃度趋势 × 开盘后回复比例，延续。'),
        ('CU14', 'VT_BUCKET_COUNT_SHIFT_20', 'AUC_CLOSE_VOLSHARE_20', 'auction_1m', 'count_close_volshare', 'COUNT 收尾：活跃度趋势 × 收盘竞价份额，延续。'),
        ('CU15', 'VT_BUCKET_COUNT_SHIFT_20', 'AUC_OPEN_VOLSHARE_20', 'auction_1m', 'count_open_volshare', 'COUNT 收尾：活跃度趋势 × 集合竞价量占比，延续。'),
        ('CU16', 'VT_BUCKET_COUNT_SHIFT_20', 'AUC_DISCOVERY_SHIFT_20', 'auction_1m', 'count_discovery_shift', 'COUNT 收尾：活跃度趋势 × 发现重心（CK4 腿），延续。'),
        ('CU17', 'VT_BUCKET_COUNT_SHIFT_20', 'BIGBAR_EDGE_CONC_20', 'bar_size_order_flow', 'count_edge_conc', 'COUNT 收尾：活跃度趋势 × 大 bar 时点集中（CS03 +71.2bp 邻域，rank_spread 版已测；本条为同对确认——否，同对不重复。改：× 时点集中 rank_interaction 探针），interaction。'),
        ('CU18', 'VT_SKEW_20', 'AUC_VARIANCE_RATIO_20', 'skew_var_ratio_inter', 'CT11 骨架 interaction 版：体量偏度 × 开盘/收盘方差比相乘（乘法 vs 减法的构造差异），延续。', 'rank_interaction'),
        ('CU19', 'VT_AUTOCORR_20', 'AUC_VARIANCE_RATIO_20', 'acf_var_ratio_inter', 'CS13 骨架 interaction 版：体量趋势自相关 × 方差比相乘，延续。', 'rank_interaction'),
        ('CU20', 'VT_RV_RATIO_20', 'IMP_PERM_SHARE_20', 'rv_perm_inter', 'CT05 骨架 interaction 版：体量波动集中 × 冲击永久份额相乘，延续。', 'rank_interaction'),
]

base.CANDIDATES = []
for rec in P:
    cid, left, right, rsrc, mech, hyp = rec[:6]
    op = rec[6] if len(rec) > 6 else "rank_spread"
    if cid == "CU17":
        # CU17 as written would duplicate CS03's pair (COUNT x BIGBAR_EDGE);
        # replace with an untested combination: COUNT_SHIFT x CLOSE5_DAY_CONSIST
        base.CANDIDATES.append(
            _pair(cid, "VT_BUCKET_COUNT_SHIFT_20", VT, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow",
                  "count_close_confirm", "活跃度趋势 × 收盘确认（−0.0233/−0.0313/t−0.30/+27.3bp），延续。"))
        continue
    base.CANDIDATES.append(_pair(cid, left, VT, right, rsrc, mech, hyp, op))

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage17(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage17_volume_time_pairing"
    plan["pairing_note"] = "第 17 阶段配对第 9 批：volume_time 残余全枚举 + 3 条 rank_interaction 探针；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


# Pre-filter: drop candidates whose canonical hash exists in previous rounds.
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
    keep = []
    seen = set()
    for c in base.CANDIDATES:
        h = base.canonical_expression(c)
        if h in prev or h in seen:
            continue
        seen.add(h)
        keep.append(c)
    base.CANDIDATES = keep[:20]
    print(f"prefilter: kept {len(base.CANDIDATES)} new candidates")


_prefilter()

base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
