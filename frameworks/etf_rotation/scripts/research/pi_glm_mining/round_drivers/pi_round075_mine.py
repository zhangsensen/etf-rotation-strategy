#!/usr/bin/env python3
"""Round 075 driver: stage 14 step 3 — directed pairing round 1.
New largebar_footprint_1m atoms x verified pool atoms; <=6 pairs; REPORT
must list both legs' single-atom gate-7 numbers (report-only)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_075"

base.CANDIDATES = [
    {
        "id": "BH1",
        "operator": "rank_spread",
        "left": {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "clock_anomaly_activity_confirm",
        "hypothesis": "两腿角色：A=成交量钟到时离散度（体量钟异常，BF1 门 7 入选：−0.0883/−0.0259/t=3.12/+9.6bp）；B=大 bar 量占比（活动强度，+0.0832/+0.0548/t=2.92/+41.6bp）。假设：体量钟异常而活动强度高（信号高）=异常体量时序伴随真实大单活动（机构在场），延续。两腿体检相关仅 −0.087，非同通道复制。",
        "expected_sign": 1,
    },
    {
        "id": "BH2",
        "operator": "rank_spread",
        "left": {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "clock_anomaly_profile_anomaly",
        "hypothesis": "两腿角色：A=体量钟离散（时间维异常，BF1 入选）；B=量分布距离（形状维异常，+0.0952/+0.0442/t=4.04/+10.1bp）。假设：时间与形状两维同时异常（信号高）=全面活动异常（非单一噪声源），延续。",
        "expected_sign": 1,
    },
    {
        "id": "BH3",
        "operator": "rank_spread",
        "left": {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "impact_permanence_trend_persist",
        "hypothesis": "两腿角色：A=大 bar 后 15 分钟延续比例（冲击永久性，−0.0949/−0.0356/t=2.56/+0.04bp，差 5bp 线）；B=缺口修复率（趋势持续，−0.0597/−0.0430/t=2.59/+9.8bp）。假设：冲击永久（信号对应方向）而趋势持续（信号对应方向）=冲击被趋势吸收而非回复，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BH4",
        "operator": "rank_spread",
        "left": {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "activity_trend_gap_persist",
        "hypothesis": "两腿角色：A=大 bar 量占比趋势 MA20−MA60（活动升温，+0.0426/+0.0206/t=0.82/审超+23.7bp 诱人但 t 弱）；B=缺口修复率（趋势持续，−0.0597/−0.0430/t=2.59/+9.8bp）。假设：活动升温而趋势持续（信号高）=升温是趋势性参与而非孤立脉冲，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BH5",
        "operator": "rank_spread",
        "left": {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "impact_permanence_no_damage",
        "hypothesis": "两腿角色：A=冲击永久性（−0.0949/−0.0356/t=2.56）；B=最差单日（无极端损伤，+0.0635/+0.0648/t=2.18/+16.2bp）。假设：冲击永久而无极端损伤（信号高）=机构持续参与且结构健康，延续。",
        "expected_sign": 1,
    },
    {
        "id": "BH6",
        "operator": "rank_spread",
        "left": {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "clock_anomaly_healthy_structure",
        "hypothesis": "两腿角色：A=体量钟离散（BF1 入选）；B=溃疡（低慢性失血，−0.0415/−0.0607/t=0.76/+10.7bp）。假设：体量钟异常而溃疡浅（信号高）=异常活动发生在健康结构中（非失血异常），延续。",
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
        "第 14 阶段定向配对第 1 轮：largebar_footprint_1m 新原子 × 已验证原子；"
        "REPORT 并列两腿单原子门 7 数字（只报告）；去重含对两腿 |rank corr|>=0.7 影子拒绝"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage14

if __name__ == "__main__":
    base.main()
