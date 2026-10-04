#!/usr/bin/env python3
"""Round 128 driver: stage 20 batch 1 — orderflow_persistence_1m family.
7 clean atoms (health max 0.644 vs TICK_IMBALANCE/SIGN_ACF1/VPIN) + 17 pairs.
Literature: Lillo-Farmer 2004; Hasbrouck 1991; Bouchaud et al. 2004; Wald-Wolfowitz 1940.
17:00 accounting: each OFP atom's left-leg batch = this round (2-3 pairs,
right legs pairwise different families); no right leg used twice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_128"

OFP = "orderflow_persistence_1m"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": OFP},
        "right": {"name": name, "source": OFP},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": OFP},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"ofp_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


LS = "liquidity_commonality_1m"
LV = "liquidity_variability"
OS = "overnight_structure_1d"
ID = "impact_decay_1m"
DR = "downside_risk"
CD = "cost_distribution"
VT = "volume_time_1m"
AU = "auction_1m"
BF = "bar_size_order_flow"
RT = "return_tail_shape"
ON = "overnight_structure_1d"
FF = "fund_flow"
PL = "price_location"
LB = "largebar_footprint_1m"

CANDS = [
    _atom("DA9", "OFP_AC1_20", "ofp_ac1",
     "签名成交量 1 阶自相关 20 日均值（Lillo–Farmer 2004 订单流长记忆；体检 0.229 vs VPIN）。预注册方向：高持续流 → 反转（-1）。", -1),
    _atom("DA10", "OFP_AC5_20", "ofp_ac5",
     "签名成交量 5 阶自相关 20 日均值（长记忆中段；体检 0.102）。方向 -1 同上。", -1),
    _atom("DA11", "OFP_DECAY_20", "ofp_decay",
     "自相关衰减指数：log|acf(k)| 对 log(k) 斜率（k=1..10），越平=记忆越长（体检 0.0）。方向 +1：慢衰减=知情流延续。", 1),
    _atom("DA12", "OFP_RUN_MEAN_20", "ofp_run_mean",
     "同号 1m 收益游程平均长度（Wald–Wolfowitz 游程结构；体检 0.179 vs TICK_IMB）。方向 -1：长游程=过度延伸。", -1),
    _atom("DA13", "OFP_RUN_MAX_20", "ofp_run_max",
     "最长游程/期望上限比（体检 0.192）。方向 -1 同上。", -1),
    _atom("DA14", "OFP_LEAD_20", "ofp_lead",
     "流跟价 vs 价跟流交叉相关之差（Hasbrouck 1991 冲击响应符号；体检 0.082）。方向 +1：流领先价=知情交易。", 1),
    _atom("DA15", "OFP_SWITCH_20", "ofp_switch",
     "日内买卖方向切换频率（体检 0.644 vs VPIN，未及影子线）。方向 +1：双向流动性=定价健康。", 1),
    _pair("CS01", "OFP_AC1_20", "RESILIENCY_20", LS,
     "簇 OFP_AC1：流持续 × 弹性——反转压力被微结构弹性吸收。"),
    _pair("CS02", "OFP_AC1_20", "LOG_AMOUNT_VOL_20", LV,
     "簇 OFP_AC1：流持续 × 高活跃。"),
    _pair("CS03", "OFP_AC1_20", "GAP_FILL_RATE_20", OS,
     "簇 OFP_AC1：流持续 × 缺口修复。"),
    _pair("CS04", "OFP_AC5_20", "PV_ELASTICITY_20", ID,
     "簇 OFP_AC5：中段流记忆 × 量价弹性（CA1 同腿）。"),
    _pair("CS05", "OFP_AC5_20", "ULCER_20", DR,
     "簇 OFP_AC5：中段流记忆 × 健康结构。"),
    _pair("CS06", "OFP_DECAY_20", "VT_BUCKET_GINI_20", VT,
     "簇 OFP_DECAY：长记忆 × 体量钟不均（CN08 同腿）。"),
    _pair("CS07", "OFP_DECAY_20", "IMP_PERM_SHARE_20", ID,
     "簇 OFP_DECAY：长记忆 × 冲击永久份额——持续流的永久冲击。"),
    _pair("CS08", "OFP_DECAY_20", "OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m",
     "簇 OFP_DECAY：长记忆 × 开盘配置（CL09 同腿）。"),
    _pair("CS09", "OFP_RUN_MEAN_20", "AUC_VARIANCE_RATIO_20", AU,
     "簇 OFP_RUN_MEAN：游程长度 × 波动配置（CM06 同腿）。"),
    _pair("CS10", "OFP_RUN_MEAN_20", "CLOSE5_DAY_CONSIST_20", BF,
     "簇 OFP_RUN_MEAN：游程长度 × 收盘确认（CK04 同腿）。"),
    _pair("CS11", "OFP_RUN_MAX_20", "ON_PREM_20", ON,
     "簇 OFP_RUN_MAX：极端游程 × 隔夜溢价（CZ01 同腿）。"),
    _pair("CS12", "OFP_RUN_MAX_20", "BIGBAR_EDGE_CONC_20", BF,
     "簇 OFP_RUN_MAX：极端游程 × 大 bar 时点集中。"),
    _pair("CS13", "OFP_LEAD_20", "TICK_IMBALANCE_20", BF,
     "簇 OFP_LEAD：流领先价 × 主买不平衡——知情流双确认。"),
    _pair("CS14", "OFP_LEAD_20", "PRICE_POSITION_20", PL,
     "簇 OFP_LEAD：流领先价 × 获利位置。"),
    _pair("CS15", "OFP_LEAD_20", "LBAR_CLOCK_STD_20", LB,
     "簇 OFP_LEAD：流领先价 × 体量钟离散（BF1 同腿）。"),
    _pair("CS16", "OFP_SWITCH_20", "VT_SKEW_20", VT,
     "簇 OFP_SWITCH：方向切换 × 体量时间偏度。"),
    _pair("CS17", "OFP_SWITCH_20", "CHIP_RANGE_90_60", CD,
     "簇 OFP_SWITCH：方向切换 × 筹码集中。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage20(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage20_orderflow_persistence"
    plan["family_note"] = (
        "第 20 阶段 orderflow_persistence_1m 首批：7 干净原子（体检 max 0.644，无影子）+ 17 配对；"
        "出处 Lillo-Farmer 2004 / Hasbrouck 1991 / Bouchaud et al. 2004 / Wald-Wolfowitz 1940；"
        "每 OFP 左腿的本阶段批=本轮，右腿两两不同族"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage20

if __name__ == "__main__":
    base.main()
