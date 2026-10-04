#!/usr/bin/env python3
"""Round 100 driver: stage 17 step 3 — pairing batch 4 (24 pairs).
CO35/36/43/44 skeleton extensions + remaining cross-new-family pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_100"

VT = "volume_time_1m"
LB = "largebar_footprint_1m"
ID = "impact_decay_1m"
AU = "auction_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


P = [
    ("CP01", "VT_AUTOCORR_20", "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "acf_edge_conc",
     "CO36 骨架延伸：体量趋势自相关 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。"),
    ("CP02", "VT_AUTOCORR_20", "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "acf_profile",
     "骨架延伸：体量趋势自相关 × 量轮廓异常（+0.0952/+0.0442/t4.04/+10.1bp），延续。"),
    ("CP03", "VT_AUTOCORR_20", "LBAR_CLOCK_STD_20", LB, "acf_clock_anomaly",
     "新×新：体量趋势自相关 × 体量钟离散（BF1 入选），延续。"),
    ("CP04", "VT_SKEW_20", "SHARE_RET_CORR_20", "fund_flow", "skew_primary",
     "CO43/44 骨架延伸：体量偏度 × 一级流解释力，延续。"),
    ("CP05", "VT_SKEW_20", "CATEGORY_VOL_20", "category_state", "skew_calm_category",
     "骨架延伸：体量偏度 × 类别平静（−0.0711/−0.0653/t2.42/+19.0bp），延续。"),
    ("CP06", "VT_SKEW_20", "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "skew_open_config",
     "骨架延伸：体量偏度 × 开盘配置（−0.1038/−0.0489/t3.30/−10.5bp），延续。"),
    ("CP07", "VT_TAIL_MOM_20", "LBAR_CLOCK_STD_20", LB, "tail_mom_clock",
     "CN21 骨架延伸：尾桶动量 × 体量钟离散，延续。"),
    ("CP08", "VT_TAIL_MOM_20", "CATEGORY_VOL_20", "category_state", "tail_mom_calm",
     "CN21 骨架延伸：尾桶动量 × 类别平静，延续。"),
    ("CP09", "VT_TAIL_MOM_20", "SHARE_RET_CORR_20", "fund_flow", "tail_mom_primary",
     "CN21 骨架延伸：尾桶动量 × 一级流解释力，延续。"),
    ("CP10", "VT_BUCKET_GINI_20", "IMP_PERM_SHARE_20", ID, "gini_permanence",
     "新×新：到达不均 × 冲击永久份额（CA2 入选），延续。"),
    ("CP11", "VT_BUCKET_GINI_20", "PV_ELASTICITY_20", ID, "gini_elasticity",
     "新×新：到达不均 × 量价弹性（CA1 入选），延续。"),
    ("CP12", "VT_RV_RATIO_20", "GAP_FILL_FRACTION_60", "gap_repair", "rv_ratio_trend",
     "CN10 骨架延伸：体量波动集中 × 趋势持续，延续。"),
    ("CP13", "VT_RV_RATIO_20", "LOG_AMOUNT_VOL_20", "liquidity_variability", "rv_ratio_activity",
     "CN10 骨架延伸：体量波动集中 × 高活跃，延续。"),
    ("CP14", "VT_RV_RATIO_20", "LBAR_CLOCK_STD_20", LB, "rv_ratio_clock",
     "新×新：体量波动集中 × 体量钟离散，延续。"),
    ("CP15", "VT_BUCKET_COUNT_SHIFT_20", "CATEGORY_VOL_20", "category_state", "count_trend_calm",
     "活跃度趋势 × 类别平静，延续。"),
    ("CP16", "VT_BUCKET_COUNT_SHIFT_20", "ULCER_20", "downside_risk", "count_trend_healthy",
     "活跃度趋势 × 健康结构，延续。"),
    ("CP17", "VT_AUTOCORR_20", "VOL_USHAPE_20", "realized_measures_1m", "acf_vol_ushape",
     "骨架延伸：体量趋势自相关 × 体量钟 U 形（−0.0832/−0.0891/t2.12/+33.9bp），延续。"),
    ("CP18", "VT_SKEW_20", "LBAR_CLOCK_STD_20", LB, "skew_clock",
     "骨架延伸：体量偏度 × 体量钟离散，延续。"),
    ("CP19", "VT_SKEW_20", "IMP_PERM_SHARE_20", ID, "skew_permanence",
     "新×新：体量偏度 × 冲击永久份额，延续。"),
    ("CP20", "VT_SKEW_20", "PV_ELASTICITY_20", ID, "skew_elasticity",
     "新×新：体量偏度 × 量价弹性，延续。"),
    ("CP21", "VT_TAIL_MOM_20", "PV_ELASTICITY_20", ID, "tail_mom_elasticity",
     "新×新：尾桶动量 × 量价弹性，延续。"),
    ("CP22", "VT_TAIL_MOM_20", "IMP_PERM_SHARE_20", ID, "tail_mom_permanence",
     "新×新：尾桶动量 × 冲击永久份额，延续。"),
    ("CP23", "VT_BUCKET_GINI_20", "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "gini_edge_conc",
     "CO14 骨架延伸：到达不均 × 大 bar 时点集中（−0.0971/−0.0459/t2.55/+30.7bp），延续。"),
    ("CP24", "VT_RV_RATIO_20", "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "rv_edge_conc",
     "CN10 骨架延伸：体量波动集中 × 大 bar 时点集中，延续。"),
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
    plan["pairing_note"] = "第 17 阶段配对第 4 批：CO35/36/43/44 骨架延伸 + 跨新家族收尾；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
