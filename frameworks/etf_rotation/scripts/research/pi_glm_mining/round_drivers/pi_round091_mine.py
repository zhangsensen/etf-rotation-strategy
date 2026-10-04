#!/usr/bin/env python3
"""Round 091 driver: stage 16 step 3 — directed pairing round 5.
CH6/CJ6 mechanism extensions and remaining open-leg combos. All-new pairs;
no repeats of r087-090."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_091"

base.CANDIDATES = [
    {
        "id": "CK1",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "close_auction_no_damage",
        "hypothesis": "两腿角色：A=收盘竞价量占比（CH6 腿，+0.0075/−0.0540/t0.77/−11.5bp）；B=最差单日（无极端损伤，+0.0635/+0.0648/t2.18/+16.2bp）。假设：收盘竞价占比高而无极端损伤（信号对应方向）=收盘承接非恐慌型，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CK2",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_CONSIST_20", "source": "auction_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "close_direction_resilient",
        "hypothesis": "两腿角色：A=尾 bar 方向一致度（CJ6 腿，−0.0154/+0.0111/t1.12/−23.9bp）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）。假设：收盘方向一致且微结构有弹性（信号对应方向）=收盘主导方在有回复力的市场收官，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CK3",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_CONSIST_20", "source": "auction_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "close_direction_chip_lock",
        "hypothesis": "两腿角色：A=尾 bar 方向一致度（CJ6 腿）；B=筹码区间宽度（集中度，−0.0574/−0.0620/t0.70/+14.6bp）。假设：收盘方向一致且筹码集中（信号对应方向）=集中盘上的方向收官，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CK4",
        "operator": "rank_spread",
        "left": {"name": "AUC_DISCOVERY_SHIFT_20", "source": "auction_1m"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "discovery_center_high_activity",
        "hypothesis": "两腿角色：A=价格发现重心（首尾量占比差，−0.0086/+0.0262/t0.54/−0.7bp）；B=对数成交额（高活跃，CH6 垂直腿，+0.0661/+0.0701/t2.23/+36.8bp）。假设：发现重心位置 × 高活跃环境（CH6 同族骨架），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CK5",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "call_auction_no_damage",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp）；B=最差单日（无极端损伤，+0.0635/+0.0648/t2.18/+16.2bp）。假设：竞价配置高而无极端损伤（信号对应方向）=开盘配置非恐慌驱动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CK6",
        "operator": "rank_spread",
        "left": {"name": "AUC_POST_OPEN_REVERT_20", "source": "auction_1m"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "post_open_revert_acf",
        "hypothesis": "两腿角色：A=开盘后 5 分钟回复比例（−0.0324/+0.0215/t0.68/−16.8bp）；B=收益自相关（动量确认，−0.0211/+0.0070/t0.12/+3.9bp）。假设：开盘冲击回复与日间动量确认（信号对应方向）=回复型开盘配合趋势日，延续。",
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
        "第 16 阶段定向配对第 5 轮：CH6/CJ6 骨架延伸 + 开盘腿收尾；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage16

if __name__ == "__main__":
    base.main()
