#!/usr/bin/env python3
"""Round 079 driver: stage 14 step 3 — directed pairing round 5.
Entering streak 2/3; a zero round triggers stage-14 exhaustion artifacts.
All-new pairs, no repeats of r075-078."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_079"

base.CANDIDATES = [
    {
        "id": "BM1",
        "operator": "rank_spread",
        "left": {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "return_carried_acf_confirm",
        "hypothesis": "两腿角色：A=大 bar 收益承载份额（−0.0164/−0.0111/t0.55/+6.2bp）；B=5 日收益自相关符号（动量确认，−0.0211/+0.0070/t0.12/+3.9bp）。假设：收益由大 bar 承载且短期动量确认（信号高）=承载是趋势性推进，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BM2",
        "operator": "rank_spread",
        "left": {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "run_consistency_chip_lock",
        "hypothesis": "两腿角色：A=大 bar 同向游程（大单连续性，−0.0273/−0.0140/t0.27/−1.6bp）；B=筹码区间宽度（集中度，−0.0574/−0.0620/t0.70/+14.6bp）。假设：大单连续且筹码集中（信号高）=锁定盘上的连续推进，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BM3",
        "operator": "rank_spread",
        "left": {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "activity_heatup_high_activity",
        "hypothesis": "两腿角色：A=大 bar 量占比趋势（活动升温，+0.0426/+0.0206/t0.82/+23.7bp）；B=对数成交额（高活跃，+0.0661/+0.0701/t2.23/+36.8bp）。假设：升温且活跃水平高（信号高）=升温发生在活跃环境（有承接主体），延续。",
        "expected_sign": 1,
    },
    {
        "id": "BM4",
        "operator": "rank_spread",
        "left": {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "return_carried_healthy",
        "hypothesis": "两腿角色：A=大 bar 收益承载份额（−0.0164/−0.0111/t0.55/+6.2bp）；B=溃疡（低慢性失血，−0.0415/−0.0607/t0.76/+10.7bp）。假设：收益由大 bar 承载且无慢性失血（信号高）=健康推进，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BM5",
        "operator": "rank_spread",
        "left": {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "run_consistency_acf_confirm",
        "hypothesis": "两腿角色：A=大 bar 同向游程（−0.0273/−0.0140/t0.27/−1.6bp）；B=收益自相关符号（−0.0211/+0.0070/t0.12/+3.9bp）。假设：日内大单连续且日间动量确认（信号高）=多周期连续性，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BM6",
        "operator": "rank_spread",
        "left": {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "overnight_absorb_day_buyflow",
        "hypothesis": "两腿角色：A=隔夜承接（+0.0240/−0.0017/t0.34/−3.0bp）；B=主买不平衡（日内买流，−0.0116/+0.0002/t1.01/+4.7bp）。假设：隔夜有承接且日内买流强（信号高）=隔夜与日内闭环吸筹，延续。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage14(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage14_largebar_pairing"
    plan["pairing_note"] = (
        "第 14 阶段定向配对第 5 轮（计数 2/3）；REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage14

if __name__ == "__main__":
    base.main()
