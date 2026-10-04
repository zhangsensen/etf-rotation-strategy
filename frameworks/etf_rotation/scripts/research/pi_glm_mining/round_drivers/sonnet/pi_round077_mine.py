#!/usr/bin/env python3
"""Round 077 driver: stage 14 step 3 — directed pairing round 3.
BJ5 (OVERNIGHT x CHIP_RANGE) extension: keep the absorption leg, vary the
vertical leg; plus silence/amtsplit falsification probes. All-new pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_077"

base.CANDIDATES = [
    {
        "id": "BK1",
        "operator": "rank_spread",
        "left": {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"},
        "right": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "mechanism": "overnight_absorb_close_confirm",
        "hypothesis": "两腿角色：A=大 bar 日次夜隔夜收益（承接，BJ5 腿，+0.0240/−0.0017/t0.34/−3.0bp）；B=尾 5 分钟与全日方向一致（收盘确认，−0.0233/−0.0313/t−0.30/+27.3bp）。假设：隔夜有承接且收盘方向一致（信号高）=隔夜与日内同源机构（非散户隔夜），延续。",
        "expected_sign": 1,
    },
    {
        "id": "BK2",
        "operator": "rank_spread",
        "left": {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "overnight_absorb_resilient",
        "hypothesis": "两腿角色：A=隔夜承接（BJ5 腿）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp，W3/Z1/AI1/AL3/AN2/AN6 配角腿）。假设：隔夜承接且冲击后快速回复（信号高）=健康承接（非被动接盘），延续。",
        "expected_sign": 1,
    },
    {
        "id": "BK3",
        "operator": "rank_spread",
        "left": {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "overnight_absorb_high_position",
        "hypothesis": "两腿角色：A=隔夜承接（BJ5 腿）；B=价格 20 日区间位置（+0.0128/+0.0275/t1.64/+8.5bp）。假设：隔夜承接而价格处于高位（信号高）=高位强势吸筹（非低位自救），延续。",
        "expected_sign": 1,
    },
    {
        "id": "BK4",
        "operator": "rank_spread",
        "left": {"name": "LBAR_SILENT_20", "source": "largebar_footprint_1m"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "silence_gap_trend",
        "hypothesis": "两腿角色：A=无大 bar 日占比（静默基率，+0.0552/+0.0209/t0.87/+5.6bp；Kyle–Obizhaeva 平静期）；B=缺口修复率（趋势持续，−0.0597/−0.0430/t2.59/+9.8bp）。假设：平静而趋势持续（信号高）=非炒作型延续（趋势不依赖脉冲）。证伪点：SILENT 有效日 290<360，组合覆盖可能不足。",
        "expected_sign": 1,
    },
    {
        "id": "BK5",
        "operator": "rank_spread",
        "left": {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "activity_heatup_resilient",
        "hypothesis": "两腿角色：A=大 bar 量占比趋势（活动升温，+0.0426/+0.0206/t0.82/+23.7bp）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）。假设：活动升温且微结构有弹性（信号高）=健康参与（非失血升温），延续。",
        "expected_sign": 1,
    },
    {
        "id": "BK6",
        "operator": "rank_spread",
        "left": {"name": "LBAR_AMTSPLIT_20", "source": "largebar_footprint_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "high_price_sweep_calm_category",
        "hypothesis": "两腿角色：A=大额不大量 bar 占比（高价位扫货，−0.0506/−0.0113/t−0.14/+9.6bp）；B=类别波动（环境噪声，−0.0711/−0.0653/t2.42/+19.0bp）。假设：高价位扫货而类别平静（信号高）=自身吸筹（非环境推动），延续。证伪点：AMTSPLIT 有效日 312<360。",
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
        "第 14 阶段定向配对第 3 轮：BJ5 承接机制延伸（OVERNIGHT × 三个新垂直腿）+ 静默/扫货腿证伪探针；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage14

if __name__ == "__main__":
    base.main()
