#!/usr/bin/env python3
"""Round 078 driver: stage 14 step 3 — directed pairing round 4.
Untried largebar x verified-leg combinations; no repeats of r075-077 pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_078"

base.CANDIDATES = [
    {
        "id": "BL1",
        "operator": "rank_spread",
        "left": {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "overnight_absorb_high_activity",
        "hypothesis": "两腿角色：A=大 bar 日次夜隔夜收益（承接，+0.0240/−0.0017/t0.34/−3.0bp）；B=对数成交额（高活跃，+0.0661/+0.0701/t2.23/+36.8bp）。假设：隔夜有承接且活跃水平高（信号高）=机构大额参与（非碎片散户），延续。",
        "expected_sign": 1,
    },
    {
        "id": "BL2",
        "operator": "rank_spread",
        "left": {"name": "LBAR_SILENT_20", "source": "largebar_footprint_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "double_calm_trend",
        "hypothesis": "两腿角色：A=无大 bar 日占比（静默基率，+0.0552/+0.0209/t0.87/+5.6bp）；B=类别波动（环境噪声，−0.0711/−0.0653/t2.42/+19.0bp）。假设：个股静默且类别平静（信号高）=非事件驱动的自然延续环境。",
        "expected_sign": 1,
    },
    {
        "id": "BL3",
        "operator": "rank_spread",
        "left": {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "run_consistency_trend_persist",
        "hypothesis": "两腿角色：A=大 bar 同向游程（大单连续性，−0.0273/−0.0140/t0.27/−1.6bp）；B=缺口修复率（趋势持续，−0.0597/−0.0430/t2.59/+9.8bp）。假设：大单连续成串且趋势持续（信号高）=连续推进型趋势，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BL4",
        "operator": "rank_spread",
        "left": {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "return_carried_dense_events",
        "hypothesis": "两腿角色：A=大 bar 收益承载份额（−0.0164/−0.0111/t0.55/+6.2bp）；B=量 spike 频率（事件密集，+0.0804/+0.0595/t2.76/+50.7bp）。假设：收益由大 bar 承载且事件密集（信号高）=密集事件真实推动价格（非噪声 spike），延续。",
        "expected_sign": 1,
    },
    {
        "id": "BL5",
        "operator": "rank_spread",
        "left": {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "impact_permanence_activity_strength",
        "hypothesis": "两腿角色：A=大 bar 后 15 分钟延续比例（冲击永久性，−0.0949/−0.0356/t2.56/+0.04bp）；B=大 bar 量占比（活动强度，+0.0832/+0.0548/t2.92/+41.6bp）。假设：高强度活动且冲击永久（信号高）=机构持续推进（非临时脉冲），延续。体检 PERM15×BVS 相关 −0.064，影子风险低。",
        "expected_sign": 1,
    },
    {
        "id": "BL6",
        "operator": "rank_spread",
        "left": {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "run_consistency_resilient",
        "hypothesis": "两腿角色：A=大 bar 同向游程（大单连续性，−0.0273/−0.0140/t0.27/−1.6bp）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）。假设：大单连续且微结构有弹性（信号高）=有序推进（非冲击失序），延续。",
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
        "第 14 阶段定向配对第 4 轮：未试组合；REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage14

if __name__ == "__main__":
    base.main()
