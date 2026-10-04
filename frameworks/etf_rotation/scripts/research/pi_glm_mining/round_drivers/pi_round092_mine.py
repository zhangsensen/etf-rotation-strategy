#!/usr/bin/env python3
"""Round 092 driver: stage 16 step 3 — directed pairing round 6.
CK4 extension (DISCOVERY_SHIFT x flow/resilience) + remaining open/close
leg combinations. All-new pairs; no repeats of r087-091."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_092"

base.CANDIDATES = [
    {
        "id": "CL1",
        "operator": "rank_spread",
        "left": {"name": "AUC_DISCOVERY_SHIFT_20", "source": "auction_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "discovery_center_buyflow",
        "hypothesis": "两腿角色：A=价格发现重心（CK4 腿，−0.0086/+0.0262/t0.54/−0.7bp）；B=主买不平衡（买流，−0.0116/+0.0002/t1.01/+4.7bp）。假设：发现重心位置与买流方向（信号对应方向）=重心由真实买盘推动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CL2",
        "operator": "rank_spread",
        "left": {"name": "AUC_DISCOVERY_SHIFT_20", "source": "auction_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "discovery_center_resilient",
        "hypothesis": "两腿角色：A=发现重心（CK4 腿）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）。假设：发现重心与弹性（信号对应方向）=重心在有回复力的环境中形成，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CL3",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "call_auction_bigbar_strength",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp）；B=大 bar 量占比（活动强度，+0.0832/+0.0548/t2.92/+41.6bp）。假设：竞价配置与大 bar 强度并存（信号对应方向）=开盘配置伴随全日强活动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CL4",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "mechanism": "call_auction_close_confirm",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22）；B=收盘确认（−0.0233/−0.0313/t−0.30/+27.3bp）。假设：竞价配置高且收盘有确认（信号对应方向）=首尾呼应的机构节奏，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CL5",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_ABSORB_20", "source": "auction_1m"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "open_absorb_acf_confirm",
        "hypothesis": "两腿角色：A=开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp）；B=5 日收益自相关（动量确认，−0.0211/+0.0070/t0.12/+3.9bp）。假设：开盘信息被吸收且日间动量确认（信号对应方向）=吸收配合跨日延续，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CL6",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "close_auction_chip_lock",
        "hypothesis": "两腿角色：A=收盘竞价量占比（CH6 腿，+0.0075/−0.0540/t0.77/−11.5bp）；B=筹码区间宽度（集中度，−0.0574/−0.0620/t0.70/+14.6bp）。假设：收盘竞价占比高而筹码集中（信号对应方向）=集中盘上的收盘结算，延续。",
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
        "第 16 阶段定向配对第 6 轮：CK4 骨架延伸 + 开/收盘腿剩余组合；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage16

if __name__ == "__main__":
    base.main()
