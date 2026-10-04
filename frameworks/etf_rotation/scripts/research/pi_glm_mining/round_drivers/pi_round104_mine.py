#!/usr/bin/env python3
"""Round 104 driver: stage 17 step 3 — pairing batch 8 (entering streak 2/3).
Final untried volume_time pairs incl. auction cross-family closure."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_104"

VT = "volume_time_1m"
AU = "auction_1m"
ID = "impact_decay_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


P = [
    ("CT01", "VT_AUTOCORR_20", "AUC_OPEN_VOLSHARE_20", "acf_open_volshare",
     "DA2 骨架：体量趋势自相关 × 集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp），延续。"),
    ("CT02", "VT_AUTOCORR_20", "AUC_OPEN_ABSORB_20", "acf_open_absorb",
     "DA2 骨架：体量趋势自相关 × 开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp），延续。"),
    ("CT03", "VT_AUTOCORR_20", "AUC_CLOSE_VOLSHARE_20", "acf_close_volshare",
     "DA2 骨架：体量趋势自相关 × 收盘竞价份额（CH6 腿，+0.0075/−0.0540/t0.77/−11.5bp），延续。"),
    ("CT04", "VT_AUTOCORR_20", "AUC_DISCOVERY_SHIFT_20", "acf_discovery_shift",
     "DA2 骨架：体量趋势自相关 × 发现重心（CK4 腿），延续。"),
    ("CT05", "VT_RV_RATIO_20", "IMP_PERM_SHARE_20", ID, "rv_permanence",
     "CN10 骨架：体量波动集中 × 冲击永久份额（CA2 入选），延续。"),
    ("CT06", "VT_BUCKET_GINI_20", "AUC_OPEN_ABSORB_20", "gini_open_absorb",
     "GINI 收尾：到达不均 × 开盘吸收度，延续。"),
    ("CT07", "VT_BUCKET_GINI_20", "AUC_VARIANCE_RATIO_20", "gini_var_ratio",
     "GINI 收尾：到达不均 × 开盘/收盘方差比（−0.1123/−0.0926/t1.46/+38.0bp），延续。"),
    ("CT08", "VT_SKEW_20", "AUC_OPEN_ABSORB_20", "skew_open_absorb",
     "SKEW 收尾：体量偏度 × 开盘吸收度，延续。"),
    ("CT09", "VT_SKEW_20", "AUC_DISCOVERY_SHIFT_20", "skew_discovery_shift",
     "SKEW 收尾：体量偏度 × 发现重心，延续。"),
    ("CT10", "VT_SKEW_20", "AUC_POST_OPEN_REVERT_20", "skew_post_revert",
     "SKEW 收尾：体量偏度 × 开盘后回复比例，延续。"),
    ("CT11", "VT_SKEW_20", "AUC_VARIANCE_RATIO_20", "skew_var_ratio",
     "SKEW 收尾：体量偏度 × 开盘/收盘方差比，延续。"),
    ("CT12", "VT_TAIL_MOM_20", "AUC_DISCOVERY_SHIFT_20", "tail_mom_discovery_shift",
     "TAIL 收尾：尾桶动量 × 发现重心，延续。"),
    ("CT13", "VT_TAIL_MOM_20", "AUC_OPEN_ABSORB_20", "tail_mom_open_absorb",
     "TAIL 收尾：尾桶动量 × 开盘吸收度，延续。"),
    ("CT14", "VT_TAIL_MOM_20", "AUC_OPEN_VOLSHARE_20", "tail_mom_open_volshare",
     "TAIL 收尾：尾桶动量 × 集合竞价量占比，延续。"),
    ("CT15", "VT_TAIL_MOM_20", "AUC_VARIANCE_RATIO_20", "tail_mom_var_ratio",
     "TAIL 收尾：尾桶动量 × 开盘/收盘方差比，延续。"),
    ("CT16", "VT_BUCKET_COUNT_SHIFT_20", "AUC_VARIANCE_RATIO_20", "count_var_ratio",
     "COUNT 收尾：活跃度趋势 × 开盘/收盘方差比，延续。"),
    ("CT17", "VT_BUCKET_COUNT_SHIFT_20", "AUC_OPEN_ABSORB_20", "count_open_absorb",
     "COUNT 收尾：活跃度趋势 × 开盘吸收度，延续。"),
    ("CT18", "VT_SKEW_20", "AUC_CLOSE_VOLSHARE_20", "skew_close_volshare",
     "SKEW 收尾：体量偏度 × 收盘竞价份额，延续。"),
    ("CT19", "VT_TAIL_MOM_20", "AUC_CLOSE_VOLSHARE_20", "tail_mom_close_volshare",
     "TAIL 收尾：尾桶动量 × 收盘竞价份额，延续。"),
    ("CT20", "VT_RV_RATIO_20", "AUC_VARIANCE_RATIO_20", "rv_var_ratio",
     "RV 收尾：体量波动集中 × 开盘/收盘方差比，延续。"),
]

base.CANDIDATES = [
    _pair(cid, left, VT, right, (rsrc if rsrc else AU), mech, hyp) for cid, left, right, rsrc, mech, hyp in (r if len(r) == 6 else (*r[:3], AU, *r[3:]) for r in P)
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage17(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage17_volume_time_pairing"
    plan["pairing_note"] = "第 17 阶段配对第 8 批（计数 2/3）：volume_time × auction 收尾 + 残余未测；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
