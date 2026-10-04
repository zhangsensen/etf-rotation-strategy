#!/usr/bin/env python3
"""Round 090 driver: stage 16 step 3 — directed pairing round 4.
CH6 extension: CLOSE_VOLSHARE x other vertical legs; plus open-leg combos.
All-new pairs; no repeats of r087-089."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_090"

base.CANDIDATES = [
    {
        "id": "CJ1",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "close_auction_profile_anomaly",
        "hypothesis": "两腿角色：A=收盘竞价量占比（CH6 腿，+0.0075/−0.0540/t0.77/−11.5bp）；B=量分布距离（轮廓异常，+0.0952/+0.0442/t4.04/+10.1bp）。假设：收盘竞价占比高且量轮廓异常（信号对应方向）=异常活动由收盘时段承接，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CJ2",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "close_auction_buyflow",
        "hypothesis": "两腿角色：A=收盘竞价量占比（CH6 腿）；B=主买不平衡（买流，−0.0116/+0.0002/t1.01/+4.7bp）。假设：收盘竞价占比高且有买流方向（信号对应方向）=收盘竞价由买方结算主导，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CJ3",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "close_auction_resilient",
        "hypothesis": "两腿角色：A=收盘竞价量占比（CH6 腿）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）。假设：收盘竞价占比高且微结构有弹性（信号对应方向）=收盘承接在健康市场完成，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CJ4",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "call_auction_chip_lock",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp）；B=筹码区间宽度（集中度，−0.0574/−0.0620/t0.70/+14.6bp）。假设：竞价配置高而筹码集中（信号对应方向）=集中盘上的开盘信息博弈，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CJ5",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_ABSORB_20", "source": "auction_1m"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "open_absorb_profile_anomaly",
        "hypothesis": "两腿角色：A=开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp）；B=量分布距离（轮廓异常，+0.0952/+0.0442/t4.04/+10.1bp）。假设：开盘信息被吸收且轮廓异常（信号对应方向）=异常活动在开盘消化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CJ6",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_CONSIST_20", "source": "auction_1m"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "close_direction_high_activity",
        "hypothesis": "两腿角色：A=尾 bar 方向与全日方向一致度（−0.0154/+0.0111/t1.12/−23.9bp）；B=对数成交额（CH6 垂直腿，+0.0661/+0.0701/t2.23/+36.8bp）。假设：尾 bar 方向一致且高活跃（信号对应方向）=收盘方向由活跃主体确认，延续。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage16(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage16_auction_pairing"
    plan["pairing_note"] = (
        "第 16 阶段定向配对第 4 轮：CH6 延伸（CLOSE_VOLSHARE × 新垂直腿）+ 开盘腿组合；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage16

if __name__ == "__main__":
    base.main()
