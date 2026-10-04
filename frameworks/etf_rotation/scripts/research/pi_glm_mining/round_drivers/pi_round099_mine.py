#!/usr/bin/env python3
"""Round 099 driver: stage 17 step 3 — pairing batch 3 (24 pairs).
CO09 skeleton extensions (GINI x remaining verticals) + remaining VT-leg
combos. All-new pairs, cross-family only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_099"

VT = "volume_time_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


P = [
    ("CO25", "VT_BUCKET_GINI_20", "RESILIENCY_20", "liquidity_commonality_1m", "gini_resilient",
     "CO09 骨架延伸：到达不均 × 微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp），延续。"),
    ("CO26", "VT_BUCKET_GINI_20", "CATEGORY_VOL_20", "category_state", "gini_calm_category",
     "CO09 骨架延伸：到达不均 × 类别平静（−0.0711/−0.0653/t2.42/+19.0bp），延续。"),
    ("CO27", "VT_BUCKET_GINI_20", "SHARE_RET_CORR_20", "fund_flow", "gini_primary_explain",
     "CO09 骨架延伸：到达不均 × 一级流解释力，延续。"),
    ("CO28", "VT_BUCKET_GINI_20", "VOL_USHAPE_20", "realized_measures_1m", "gini_vol_ushape",
     "CO09 骨架延伸：到达不均 × 体量钟 U 形（−0.0832/−0.0891/t2.12/+33.9bp，r053 入选），延续。"),
    ("CO29", "VT_TAIL_MOM_20", "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "tail_mom_profile",
     "CN21 骨架延伸：尾桶动量 × 轮廓异常（+0.0952/+0.0442/t4.04/+10.1bp），延续。"),
    ("CO30", "VT_TAIL_MOM_20", "SIGN_ACF1_5", "serial_dependence", "tail_mom_acf",
     "CN21 骨架延伸：尾桶动量 × 动量确认（−0.0211/+0.0070/t0.12/+3.9bp），延续。"),
    ("CO31", "VT_TAIL_MOM_20", "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "tail_mom_bigbar",
     "CN21 骨架延伸：尾桶动量 × 大 bar 强度（+0.0832/+0.0548/t2.92/+41.6bp），延续。"),
    ("CO32", "VT_TAIL_MOM_20", "GAP_FILL_FRACTION_60", "gap_repair", "tail_mom_trend",
     "CN21 骨架延伸：尾桶动量 × 趋势持续（−0.0597/−0.0430/t2.59/+9.8bp），延续。"),
    ("CO33", "VT_AUTOCORR_20", "RESILIENCY_20", "liquidity_commonality_1m", "acf_resilient",
     "DA2 骨架延伸：体量趋势自相关 × 微结构弹性，延续。"),
    ("CO34", "VT_SKEW_20", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "skew_close_confirm",
     "体量偏度 × 收盘确认（−0.0233/−0.0313/t−0.30/+27.3bp），延续。"),
    ("CO35", "VT_AUTOCORR_20", "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "acf_dir_skew",
     "DA2 骨架延伸：体量趋势自相关 × 方向偏度（−0.0166/+0.0187/t1.16/+8.7bp），延续。"),
    ("CO36", "VT_AUTOCORR_20", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "acf_events",
     "DA2 骨架延伸：体量趋势自相关 × 事件密集（+0.0804/+0.0595/t2.76/+50.7bp），延续。"),
    ("CO37", "VT_RV_RATIO_20", "RESILIENCY_20", "liquidity_commonality_1m", "rv_resilient",
     "CN10 骨架延伸：体量波动集中 × 微结构弹性，延续。"),
    ("CO38", "VT_RV_RATIO_20", "VOL_USHAPE_20", "realized_measures_1m", "rv_vol_ushape",
     "CN10 骨架延伸：体量波动集中 × U 形（−0.0832/−0.0891/t2.12/+33.9bp），延续。"),
    ("CO39", "VT_RV_RATIO_20", "ULCER_20", "downside_risk", "rv_healthy",
     "CN10 骨架延伸：体量波动集中 × 健康结构（−0.0415/−0.0607/t0.76/+10.7bp），延续。"),
    ("CO40", "VT_RV_RATIO_20", "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "rv_bigbar",
     "CN10 骨架延伸：体量波动集中 × 大 bar 强度（+0.0832/+0.0548/t2.92/+41.6bp），延续。"),
    ("CO41", "VT_BUCKET_COUNT_SHIFT_20", "TICK_IMBALANCE_20", "bar_size_order_flow", "count_trend_buyflow",
     "活跃度趋势 × 买流（−0.0116/+0.0002/t1.01/+4.7bp），延续。"),
    ("CO42", "VT_BUCKET_COUNT_SHIFT_20", "RESILIENCY_20", "liquidity_commonality_1m", "count_trend_resilient",
     "活跃度趋势 × 微结构弹性，延续。"),
    ("CO43", "VT_SKEW_20", "RESILIENCY_20", "liquidity_commonality_1m", "skew_resilient",
     "体量偏度 × 微结构弹性，延续。"),
    ("CO44", "VT_SKEW_20", "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "skew_bigbar",
     "体量偏度 × 大 bar 强度，延续。"),
    ("CO45", "VT_SKEW_20", "CHIP_RANGE_90_60", "cost_distribution", "skew_chip_lock",
     "体量偏度 × 筹码集中，延续。"),
    ("CO46", "VT_SKEW_20", "ULCER_20", "downside_risk", "skew_healthy",
     "体量偏度 × 健康结构，延续。"),
    ("CO47", "VT_SKEW_20", "PRICE_POSITION_20", "price_location", "skew_high_position",
     "体量偏度 × 获利位置（+0.0128/+0.0275/t1.64/+8.5bp），延续。"),
    ("CO48", "VT_TAIL_MOM_20", "PRICE_POSITION_20", "price_location", "tail_mom_high_position",
     "尾桶动量 × 获利位置（CO09 垂直腿），延续。"),
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
    plan["pairing_note"] = "第 17 阶段配对第 3 批：CO09 骨架延伸 + VT 腿剩余垂直组合；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
