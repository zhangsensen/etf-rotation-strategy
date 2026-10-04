#!/usr/bin/env python3
"""Round 097 driver: stage 17 step 3 — first pairing batch (22 pairs).
volume_time_1m legs (VT_AUTOCORR admitted; VT_RV_RATIO/GINI/COUNT_SHIFT/
SKEW/TAIL_MOM) x verified pool legs. All-new pairs, cross-family only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_097"

VT = "volume_time_1m"


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


_leg_notes = {
    "VT_AUTOCORR_20": "体量时间收益自相关（DA2 入选：−0.0822/−0.0363/t2.32/+17.9bp）",
    "VT_RV_RATIO_20": "体量时间 RV 集中度（−0.1182/−0.0415/t2.80/+21.2bp；原子态被影子墙拒，作腿重试）",
    "VT_BUCKET_GINI_20": "桶到达 Gini（−0.0398/−0.0649/t1.61/+24.5bp）",
    "VT_BUCKET_COUNT_SHIFT_20": "活跃度趋势 MA20−MA60（−0.0488/+0.0781/t0.44/审超−47.1bp 反号）",
    "VT_SKEW_20": "体量时间收益偏度（+0.0158/+0.0026/t1.27/+8.9bp）",
    "VT_TAIL_MOM_20": "最近 20% 体量桶动量（+0.0034/+0.0067/t−0.49/−4.7bp）",
}

base.CANDIDATES = [
    _pair("CN01", "VT_AUTOCORR_20", VT, "LOG_AMOUNT_VOL_20", "liquidity_variability", "vt_acf_high_activity",
          "A=VT_AUTOCORR（体量时间趋势自相关）；B=对数成交额（高活跃）。假设：体量时间趋势自相关 × 高活跃=活跃环境的趋势连续，延续。"),
    _pair("CN02", "VT_AUTOCORR_20", VT, "GAP_FILL_FRACTION_60", "gap_repair", "vt_acf_trend_persist",
          "A=VT_AUTOCORR；B=缺口修复率（趋势持续）。假设：体量时间趋势自相关 × 趋势持续，延续。"),
    _pair("CN03", "VT_AUTOCORR_20", VT, "TICK_IMBALANCE_20", "bar_size_order_flow", "vt_acf_buyflow",
          "A=VT_AUTOCORR；B=主买不平衡。假设：体量时间趋势自相关 × 买流方向，延续。"),
    _pair("CN04", "VT_AUTOCORR_20", VT, "CHIP_RANGE_90_60", "cost_distribution", "vt_acf_chip_lock",
          "A=VT_AUTOCORR；B=筹码集中度。假设：体量时间趋势自相关 × 集中盘，延续。"),
    _pair("CN05", "VT_AUTOCORR_20", VT, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "vt_acf_close_confirm",
          "A=VT_AUTOCORR；B=收盘确认。假设：体量时间趋势自相关 × 收盘确认，延续。"),
    _pair("CN06", "VT_AUTOCORR_20", VT, "PRICE_POSITION_20", "price_location", "vt_acf_high_position",
          "A=VT_AUTOCORR；B=价格区间位置。假设：体量时间趋势自相关 × 获利位置，延续。"),
    _pair("CN07", "VT_RV_RATIO_20", VT, "TICK_IMBALANCE_20", "bar_size_order_flow", "vt_rv_buyflow",
          "A=VT_RV_RATIO（体量时间波动集中度）；B=主买不平衡。假设：体量波动集中 × 买流方向，延续。"),
    _pair("CN08", "VT_RV_RATIO_20", VT, "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "vt_rv_dir_skew",
          "A=VT_RV_RATIO；B=大 bar 方向偏度。假设：体量波动集中 × 定向大单，延续。"),
    _pair("CN09", "VT_RV_RATIO_20", VT, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "vt_rv_close_confirm",
          "A=VT_RV_RATIO；B=收盘确认。假设：体量波动集中 × 收盘确认，延续。"),
    _pair("CN10", "VT_RV_RATIO_20", VT, "PRICE_POSITION_20", "price_location", "vt_rv_high_position",
          "A=VT_RV_RATIO；B=价格区间位置。假设：体量波动集中 × 获利位置，延续。"),
    _pair("CN11", "VT_RV_RATIO_20", VT, "SIGN_ACF1_5", "serial_dependence", "vt_rv_acf_confirm",
          "A=VT_RV_RATIO；B=收益自相关确认。假设：体量波动集中 × 动量确认，延续。"),
    _pair("CN12", "VT_RV_RATIO_20", VT, "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m", "vt_rv_open_config",
          "A=VT_RV_RATIO；B=开盘配置占比。假设：体量波动集中 × 开盘配置，延续。"),
    _pair("CN13", "VT_BUCKET_GINI_20", VT, "LOG_AMOUNT_VOL_20", "liquidity_variability", "gini_high_activity",
          "A=VT_BUCKET_GINI（到达不均匀度，审计 +24.5bp 强）；B=对数成交额。假设：到达不均 × 高活跃，延续。"),
    _pair("CN14", "VT_BUCKET_GINI_20", VT, "GAP_FILL_FRACTION_60", "gap_repair", "gini_trend_persist",
          "A=VT_BUCKET_GINI；B=缺口修复率（趋势持续）。假设：到达不均 × 趋势持续，延续。"),
    _pair("CN15", "VT_BUCKET_GINI_20", VT, "TICK_IMBALANCE_20", "bar_size_order_flow", "gini_buyflow",
          "A=VT_BUCKET_GINI；B=主买不平衡。假设：到达不均 × 买流方向，延续。"),
    _pair("CN16", "VT_BUCKET_GINI_20", VT, "CHIP_RANGE_90_60", "cost_distribution", "gini_chip_lock",
          "A=VT_BUCKET_GINI；B=筹码集中度。假设：到达不均 × 集中盘，延续。"),
    _pair("CN17", "VT_BUCKET_COUNT_SHIFT_20", VT, "SIGN_ACF1_5", "serial_dependence", "count_trend_acf",
          "A=活跃度趋势 MA20−MA60（审超 −47bp 反号）；B=收益自相关。假设：活跃度降温且动量确认（信号对应方向）=冷环境的延续，延续。"),
    _pair("CN18", "VT_BUCKET_COUNT_SHIFT_20", VT, "LOG_AMOUNT_VOL_20", "liquidity_variability", "count_trend_activity",
          "A=活跃度趋势；B=对数成交额。假设：活跃度趋势 × 当前活跃水平（信号对应方向），延续。"),
    _pair("CN19", "VT_SKEW_20", VT, "VOL_PROFILE_DISTANCE", "intraday_profile_deviation", "vt_skew_profile_anomaly",
          "A=体量时间偏度；B=量分布距离。假设：体量偏度 × 轮廓异常，延续。"),
    _pair("CN20", "VT_SKEW_20", VT, "TICK_IMBALANCE_20", "bar_size_order_flow", "vt_skew_buyflow",
          "A=体量时间偏度；B=主买不平衡。假设：体量偏度 × 买流方向，延续。"),
    _pair("CN21", "VT_TAIL_MOM_20", VT, "LOG_AMOUNT_VOL_20", "liquidity_variability", "tail_mom_high_activity",
          "A=最近 20% 体量桶动量；B=对数成交额。假设：尾桶动量 × 高活跃，延续。"),
    _pair("CN22", "VT_TAIL_MOM_20", VT, "RESILIENCY_20", "liquidity_commonality_1m", "tail_mom_resilient",
          "A=最近 20% 体量桶动量；B=微结构弹性。假设：尾桶动量 × 弹性微结构，延续。"),
]

# enrich hypotheses with leg notes
for c in base.CANDIDATES:
    a_note = _leg_notes.get(c["left"]["name"], "")
    c["hypothesis"] = c["hypothesis"] + f" 腿注：A {a_note}。文献：Clark 1973 / Ane–Geman 2000 / Easley–O'Hara 2012。"

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage17(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage17_volume_time_pairing"
    plan["pairing_note"] = "第 17 阶段首批配对：volume_time_1m 新腿 × 已验证腿；同族不配；REPORT 并列两腿单原子门 7 数字（只报告）"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage17

if __name__ == "__main__":
    base.main()
