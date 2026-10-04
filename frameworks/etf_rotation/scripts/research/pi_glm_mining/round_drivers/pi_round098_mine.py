#!/usr/bin/env python3
"""Round 098 driver: stage 17 step 3 — pairing batch 2 (24 pairs).
Skeleton rotations around r097 survivors (CN10/CN13/CN21) plus newxnew
pairs across volume_time/largebar/impact_decay families."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_098"

VT = "volume_time_1m"
LB = "largebar_footprint_1m"
ID = "impact_decay_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


base.CANDIDATES = [
    _pair("CO01", "VT_RV_RATIO_20", VT, "CATEGORY_VOL_20", "category_state", "rv_ratio_calm_category",
          "A=体量波动集中度（CN10 骨架，t1.96/+32.5bp）；B=类别波动。假设：体量波动集中而类别平静=自身结构信号，延续。"),
    _pair("CO02", "VT_RV_RATIO_20", VT, "CHIP_RANGE_90_60", "cost_distribution", "rv_ratio_chip_lock",
          "A=体量波动集中度；B=筹码集中度。假设：体量波动集中 × 集中盘，延续。"),
    _pair("CO03", "VT_RV_RATIO_20", VT, "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "rv_ratio_events",
          "A=体量波动集中度；B=事件密集度。假设：体量波动集中 × 事件密集，延续。"),
    _pair("CO04", "VT_AUTOCORR_20", VT, "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "acf_bigbar_strength",
          "A=体量时间趋势自相关（DA2 入选）；B=大 bar 强度。假设：趋势自相关 × 活动强度，延续。"),
    _pair("CO05", "VT_AUTOCORR_20", VT, "CATEGORY_VOL_20", "category_state", "acf_calm_category",
          "A=体量时间趋势自相关；B=类别波动。假设：趋势自相关 × 类别平静，延续。"),
    _pair("CO06", "VT_AUTOCORR_20", VT, "ULCER_20", "downside_risk", "acf_healthy",
          "A=体量时间趋势自相关；B=溃疡（无慢性失血）。假设：趋势自相关 × 健康结构，延续。"),
    _pair("CO07", "VT_AUTOCORR_20", VT, "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "acf_open_config",
          "A=体量时间趋势自相关；B=开盘配置占比。假设：趋势自相关 × 开盘配置，延续。"),
    _pair("CO08", "VT_AUTOCORR_20", VT, "SHARE_RET_CORR_20", "fund_flow", "acf_primary_explain",
          "A=体量时间趋势自相关；B=份额-收益相关。假设：趋势自相关 × 低一级解释力（信号对应方向），延续。"),
    _pair("CO09", "VT_BUCKET_GINI_20", VT, "PRICE_POSITION_20", "price_location", "gini_high_position",
          "A=到达不均匀度（CN13 骨架 +46.3bp）；B=价格区间位置。假设：到达不均 × 获利位置，延续。"),
    _pair("CO10", "VT_BUCKET_GINI_20", VT, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "gini_close_confirm",
          "A=到达不均；B=收盘确认。假设：到达不均 × 收盘确认，延续。"),
    _pair("CO11", "VT_BUCKET_GINI_20", VT, "SIGN_ACF1_5", "serial_dependence", "gini_acf_confirm",
          "A=到达不均；B=收益自相关。假设：到达不均 × 动量确认，延续。"),
    _pair("CO12", "VT_BUCKET_GINI_20", VT, "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "gini_profile_anomaly",
          "A=到达不均；B=量分布距离。假设：到达不均 × 轮廓异常，延续。"),
    _pair("CO13", "VT_BUCKET_GINI_20", VT, "ULCER_20", "downside_risk", "gini_healthy",
          "A=到达不均；B=溃疡。假设：到达不均 × 健康结构，延续。"),
    _pair("CO14", "VT_BUCKET_GINI_20", VT, "BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "gini_bigbar_strength",
          "A=到达不均；B=大 bar 强度。假设：到达不均 × 活动强度，延续。"),
    _pair("CO15", "VT_TAIL_MOM_20", VT, "TICK_IMBALANCE_20", "bar_size_order_flow", "tail_mom_buyflow",
          "A=尾桶动量（CN21 骨架 +43.9bp）；B=主买不平衡。假设：尾桶动量 × 买流方向，延续。"),
    _pair("CO16", "VT_TAIL_MOM_20", VT, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "tail_mom_close_confirm",
          "A=尾桶动量；B=收盘确认。假设：尾桶动量 × 收盘确认，延续。"),
    _pair("CO17", "VT_TAIL_MOM_20", VT, "CHIP_RANGE_90_60", "cost_distribution", "tail_mom_chip_lock",
          "A=尾桶动量；B=筹码集中度。假设：尾桶动量 × 集中盘，延续。"),
    _pair("CO18", "VT_BUCKET_COUNT_SHIFT_20", VT, "GAP_FILL_FRACTION_60", "gap_repair", "count_trend_gap",
          "A=活跃度趋势（审超 −47bp 反号）；B=缺口修复率。假设：活跃度趋势 × 趋势持续（信号对应方向），延续。"),
    _pair("CO19", "VT_BUCKET_COUNT_SHIFT_20", VT, "PRICE_POSITION_20", "price_location", "count_trend_position",
          "A=活跃度趋势；B=价格区间位置。假设：活跃度趋势 × 获利位置（信号对应方向），延续。"),
    _pair("CO20", "VT_SKEW_20", VT, "LOG_AMOUNT_VOL_20", "liquidity_variability", "skew_high_activity",
          "A=体量时间偏度；B=对数成交额。假设：体量偏度 × 高活跃，延续。"),
    _pair("CO21", "VT_SKEW_20", VT, "GAP_FILL_FRACTION_60", "gap_repair", "skew_trend_persist",
          "A=体量时间偏度；B=缺口修复率。假设：体量偏度 × 趋势持续，延续。"),
    _pair("CO22", "VT_AUTOCORR_20", VT, "PV_ELASTICITY_20", ID, "acf_elasticity",
          "A=体量时间趋势自相关（DA2 入选）；B=量价弹性（CA1 入选）。新×新：体量时间趋势 × 冲击敏感，延续。"),
    _pair("CO23", "VT_AUTOCORR_20", VT, "IMP_PERM_SHARE_20", ID, "acf_permanence",
          "A=体量时间趋势自相关；B=冲击永久份额（CA2 入选）。新×新：趋势自相关 × 冲击永久，延续。"),
    _pair("CO24", "VT_BUCKET_GINI_20", VT, "LBAR_CLOCK_STD_20", LB, "gini_clock_anomaly",
          "A=到达不均（Gini）；B=体量钟离散度（BF1 入选）。新×新：两种到达不均匀度量（Gini vs CV），延续。"),
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage17(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage17_volume_time_pairing"
    plan["pairing_note"] = "第 17 阶段配对第 2 批：CN10/CN13/CN21 骨架轮换 + 跨新家族新×新；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
