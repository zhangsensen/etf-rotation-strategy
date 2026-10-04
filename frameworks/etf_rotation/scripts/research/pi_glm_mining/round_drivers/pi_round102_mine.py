#!/usr/bin/env python3
"""Round 100 driver: stage 17 step 3 — pairing batch 6 (20 pairs).
CLOSE30/session-share and COUNT_SHIFT skeleton closures; remaining untried
volume_time x verified pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_102"

VT = "volume_time_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


P = [
    ("CR01", "VT_RV_RATIO_20", "CLOSE30_VOL_SHARE_20", "intraday_volume_profile_1m", "rv_close30",
     "体量波动集中 × 尾 30 分钟量占比（CJ6 邻域），延续。"),
    ("CR02", "VT_RV_RATIO_20", "SHARE_RET_CORR_20", "fund_flow", "rv_primary",
     "体量波动集中 × 一级流解释力，延续。"),
    ("CR03", "VT_RV_RATIO_20", "PV_ELASTICITY_20", "impact_decay_1m", "rv_elasticity",
     "新×新证伪：体量波动集中 × 量价弹性（CA1；影子风险已知，实测判定）。"),
    ("CR04", "VT_AUTOCORR_20", "CLOSE30_VOL_SHARE_20", "intraday_volume_profile_1m", "acf_close30",
     "DA2 骨架 × 尾 30 分钟量占比，延续。"),
    ("CR05", "VT_BUCKET_GINI_20", "CLOSE30_VOL_SHARE_20", "intraday_volume_profile_1m", "gini_close30",
     "到达不均 × 尾 30 分钟量占比，延续。"),
    ("CR06", "VT_SKEW_20", "CLOSE30_VOL_SHARE_20", "intraday_volume_profile_1m", "skew_close30",
     "体量偏度 × 尾 30 分钟量占比，延续。"),
    ("CR07", "VT_TAIL_MOM_20", "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "tail_mom_edge_conc",
     "尾桶动量 × 大 bar 时点集中，延续。"),
    ("CR08", "VT_BUCKET_COUNT_SHIFT_20", "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "count_open30",
     "活跃度趋势 × 开盘配置，延续。"),
    ("CR09", "VT_BUCKET_COUNT_SHIFT_20", "CLOSE30_VOL_SHARE_20", "intraday_volume_profile_1m", "count_close30",
     "活跃度趋势 × 尾 30 分钟量占比，延续。"),
    ("CR10", "VT_BUCKET_COUNT_SHIFT_20", "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "count_profile",
     "活跃度趋势 × 量轮廓异常，延续。"),
    ("CR11", "VT_BUCKET_COUNT_SHIFT_20", "SHARE_RET_CORR_20", "fund_flow", "count_primary",
     "活跃度趋势 × 一级流解释力，延续。"),
    ("CR12", "VT_TAIL_MOM_20", "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "tail_mom_open30",
     "尾桶动量 × 开盘配置，延续。"),
    ("CR13", "VT_SKEW_20", "BIGBAR_EDGE_CONC_20", "bar_size_order_flow", "skew_edge_conc",
     "体量偏度 × 大 bar 时点集中，延续。"),
    ("CR14", "VT_BUCKET_GINI_20", "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "gini_open30",
     "到达不均 × 开盘配置，延续。"),
    ("CR15", "VT_BUCKET_COUNT_SHIFT_20", "CHIP_RANGE_90_60", "cost_distribution", "count_chip",
     "活跃度趋势 × 筹码集中，延续。"),
    ("CR16", "VT_TAIL_MOM_20", "ULCER_20", "downside_risk", "tail_mom_healthy",
     "尾桶动量 × 健康结构，延续。"),
    ("CR17", "VT_TAIL_MOM_20", "CLOSE30_VOL_SHARE_20", "intraday_volume_profile_1m", "tail_mom_close30",
     "尾桶动量 × 尾 30 分钟量占比，延续。"),
    ("CR18", "VT_BUCKET_COUNT_SHIFT_20", "HIVOL_RET5_20", "impact_decay_1m", "count_hivol",
     "活跃度趋势 × 高量溢价，延续。"),
    ("CR19", "VT_BUCKET_COUNT_SHIFT_20", "LOVOL_RET5_20", "impact_decay_1m", "count_lovol",
     "活跃度趋势 × 低量日响应，延续。"),
    ("CR20", "VT_BUCKET_COUNT_SHIFT_20", "VOL_USHAPE_20", "realized_measures_1m", "count_ushape",
     "活跃度趋势 × 体量钟 U 形，延续。"),
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
    plan["pairing_note"] = "第 17 阶段配对第 6 批：CLOSE30 骨架 + COUNT_SHIFT 收尾；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
