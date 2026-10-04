#!/usr/bin/env python3
"""Round 076 driver: stage 14 step 3 — directed pairing round 2.
Lesson from r075: CLOCK_STD/PERM15 combos were shadows of their own legs.
This round uses full-coverage weak-solo new legs (TREND/RET_CONTRIB/RUN_MAX/
OVERNIGHT) x orthogonal verified legs; no repeats of r075 pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_076"

base.CANDIDATES = [
    {
        "id": "BJ1",
        "operator": "rank_spread",
        "left": {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "activity_heatup_events_dense",
        "hypothesis": "两腿角色：A=大 bar 量占比趋势 MA20−MA60（活动升温，+0.0426/+0.0206/t0.82/审超+23.7bp）；B=量 spike 频率（事件密集，+0.0804/+0.0595/t2.76/+50.7bp）。假设：活动升温且事件密集（信号高）=趋势性参与而非孤立脉冲，延续。体检相关仅 0.29，非同通道。",
        "expected_sign": 1,
    },
    {
        "id": "BJ2",
        "operator": "rank_spread",
        "left": {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "activity_heatup_calm_category",
        "hypothesis": "两腿角色：A=活动升温（+0.0426/+0.0206/t0.82/+23.7bp）；B=类别波动（环境噪声，−0.0711/−0.0653/t2.42/+19.0bp）。假设：活动升温而类别平静（信号高）=自身信息而非环境推动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BJ3",
        "operator": "rank_spread",
        "left": {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"},
        "right": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "mechanism": "return_carried_directional",
        "hypothesis": "两腿角色：A=大 bar 收益承载份额（−0.0164/−0.0111/t0.55/+6.2bp）；B=大 bar 方向偏度（定向大单，−0.0166/+0.0187/t1.16/+8.7bp）。假设：收益由大 bar 承载且大单方向一致（信号高）=机构定向推进，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BJ4",
        "operator": "rank_spread",
        "left": {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "run_consistency_buyflow",
        "hypothesis": "两腿角色：A=大 bar 同向游程（大单连续性，−0.0273/−0.0140/t0.27/−1.6bp）；B=主买不平衡（买流，−0.0116/+0.0002/t1.01/+4.7bp）。假设：大单连续成串且方向偏买（信号高）=程序化扫单，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BJ5",
        "operator": "rank_spread",
        "left": {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "overnight_absorption_chip_conc",
        "hypothesis": "两腿角色：A=大 bar 日次夜隔夜收益（承接，+0.0240/−0.0017/t0.34/−3.0bp）；B=筹码区间宽度（集中度，−0.0574/−0.0620/t0.70/+14.6bp）。假设：隔夜有承接且筹码集中（信号高）=机构囤集，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BJ6",
        "operator": "rank_spread",
        "left": {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "return_carried_open_session",
        "hypothesis": "两腿角色：A=大 bar 收益承载份额（−0.0164/−0.0111/t0.55/+6.2bp）；B=开盘 30 分钟量占比（开盘配置，−0.1038/−0.0489/t3.30/−10.5bp）。假设：收益由大 bar 承载且开盘配置占比高（信号高）=机构节奏在开盘执行，延续。",
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
        "第 14 阶段定向配对第 2 轮：低相关新腿（TREND/RET_CONTRIB/RUN_MAX/OVERNIGHT）× 垂直已验证腿；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage14

if __name__ == "__main__":
    base.main()
