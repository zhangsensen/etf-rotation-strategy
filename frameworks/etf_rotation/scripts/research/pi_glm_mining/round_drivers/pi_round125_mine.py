#!/usr/bin/env python3
"""Round 125 driver: stage 19 batch 1 — vol_of_vol_1m family.
6 clean atoms (2 shadowed: VOV_RQ_20 0.705, VOV_RQ_RV2_20 0.824) + 18 pairs.
Literature: Baltussen-Van Bekkum-Van der Grient 2018; Corsi 2009 HAR;
Barndorff-Nielsen-Shephard 2002; Bollerslev-Paton-Quaedvlieg 2016."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_125"

VOV = "vol_of_vol_1m"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": VOV},
        "right": {"name": name, "source": VOV},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": VOV},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"vov_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _atom("DA3", "VOV_LOGRV_STD_20", "vov_logrv_std",
     "体量的体量：日 log-RV 20 日标准差（Baltussen–Van Bekkum–Van der Grient 2018 vol-of-vol 风险溢价；体检 max|corr| 0.625 vs RKURT_20）。高低 vol-of-vol 的截面风险补偿差。", -1),
    _atom("DA4", "VOV_RV_CV_20", "vov_rv_cv",
     "RV 变异系数 20 日（同一 vol-of-vol 构造的尺度无关版；体检 0.602 ok）。", -1),
    _atom("DA5", "VOV_HAR_RESID_20", "vov_har_surprise",
     "HAR-RV 滚动拟合残差 20 日均值 = 波动意外（Corsi 2009 HAR；体检 0.165 ok）。持续超预期波动 = 信息流强度。", 1),
    _atom("DA6", "VOV_HAR_RESID_SIGN_20", "vov_har_sign",
     "HAR 残差符号一致度 20 日（|mean(sign)|；体检 0.081 ok）。方向性波动体制 vs 双向震荡。", -1),
    _atom("DA7", "VOV_TERM_RATIO_20_60", "vov_term_structure",
     "RV 20 日/60 日期限比（波动期限结构；体检 0.194 ok）。短期波动升温。", -1),
    _atom("DA8", "VOV_RV_AUTOCORR_20", "vov_rv_persistence",
     "日 RV 一阶自相关 20 日 = 波动持续性（Corsi HAR 的 H 假设；体检 0.213 ok）。", -1),
    _pair("CQ25", "VOV_LOGRV_STD_20", "LOG_AMOUNT_VOL_20", "liquidity_variability",
     "vov × 活跃：vol-of-vol × 高活跃（LOG_AMOUNT_VOL_20 多组合入选腿）。高风险补偿要求在流动性好的标的可被定价。"),
    _pair("CQ26", "VOV_LOGRV_STD_20", "RESILIENCY_20", "liquidity_commonality_1m",
     "vov × 弹性：vol-of-vol × 微结构弹性。高 vov 但弹性好 = 波动被吸收。"),
    _pair("CQ27", "VOV_LOGRV_STD_20", "TICK_IMBALANCE_20", "bar_size_order_flow",
     "vov × 方向性流：vol-of-vol × 主买不平衡。方向明确的高 vov 延续。"),
    _pair("CQ28", "VOV_RV_CV_20", "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m",
     "vov × 开盘配置：RV 变异系数 × 开盘配置（CL09 同腿）。波动不确定在时段结构固定时更可预测。"),
    _pair("CQ29", "VOV_RV_CV_20", "GAP_FILL_RATE_20", "overnight_structure_1d",
     "vov × 缺口修复：RV 变异系数 × 缺口修复率（CN03 同腿）。"),
    _pair("CQ30", "VOV_RV_CV_20", "ULCER_20", "downside_risk",
     "vov × 健康：RV 变异系数 × 溃疡浅。"),
    _pair("CQ31", "VOV_HAR_RESID_20", "PV_ELASTICITY_20", "impact_decay_1m",
     "波动意外 × 弹性：超预期波动在低弹性标的的冲击更持久（CA1 同腿）。"),
    _pair("CQ32", "VOV_HAR_RESID_20", "SIGN_ACF1_5", "serial_dependence",
     "波动意外 × 动量：正波动意外的方向确认。"),
    _pair("CQ33", "VOV_HAR_RESID_20", "IMP_PERM_SHARE_20", "impact_decay_1m",
     "波动意外 × 冲击永久份额：意外波动的永久成分。"),
    _pair("CQ34", "VOV_HAR_RESID_SIGN_20", "VT_BUCKET_GINI_20", "volume_time_1m",
     "符号一致 × 体量钟：方向性波动体制 × 交易到达不均（CN08 同腿）。"),
    _pair("CQ35", "VOV_HAR_RESID_SIGN_20", "AUC_VARIANCE_RATIO_20", "auction_1m",
     "符号一致 × 波动配置：方向性体制 × 开/收盘方差失衡（CM06 同腿）。"),
    _pair("CQ36", "VOV_HAR_RESID_SIGN_20", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow",
     "符号一致 × 收盘确认：体制一致性的日内确认（CK04 同腿）。"),
    _pair("CQ37", "VOV_TERM_RATIO_20_60", "CHIP_RANGE_90_60", "cost_distribution",
     "期限结构 × 筹码：波动升温 × 筹码集中。"),
    _pair("CQ38", "VOV_TERM_RATIO_20_60", "PRICE_POSITION_20", "price_location",
     "期限结构 × 位置：波动升温在高位 vs 低位的不对称。"),
    _pair("CQ39", "VOV_TERM_RATIO_20_60", "WORST_DAY_20", "return_tail_shape",
     "期限结构 × 尾部：波动升温 × 无极端损伤。"),
    _pair("CQ40", "VOV_RV_AUTOCORR_20", "BIGBAR_VOL_SHARE_20", "bar_size_order_flow",
     "波动持续性 × 大 bar：持续体制的机构参与。"),
    _pair("CQ41", "VOV_RV_AUTOCORR_20", "ON_PREM_20", "overnight_structure_1d",
     "波动持续性 × 隔夜溢价：体制化波动的隔夜定价（CZ01 同腿）。"),
    _pair("CQ42", "VOV_RV_AUTOCORR_20", "LOG_AMOUNT_VOL_20", "liquidity_variability",
     "波动持续性 × 活跃：持续波动在活跃标的信息效率更高。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage19(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage19_vol_of_vol"
    plan["family_note"] = (
        "第 19 阶段 vol_of_vol_1m 首批：6 干净原子（VOV_RQ_20 corr 0.705、VOV_RQ_RV2_20 corr 0.824 影子剔除）"
        " + 18 定向配对；出处 Baltussen 2018 / Corsi 2009 / BNS 2002 / BPQ 2016"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage19

if __name__ == "__main__":
    base.main()
