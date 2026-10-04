#!/usr/bin/env python3
"""Round 094 driver: stage 16 step 3 — directed pairing round 8 (entering
streak 2/3). Final batch of untried auction x verified-atom pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_094"

base.CANDIDATES = [
    {
        "id": "CN1",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "call_auction_resilient",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）。假设：竞价配置高且微结构有弹性（信号对应方向）=开盘配置在有回复力的市场执行，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CN2",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "IMP_PERM_SHARE_20", "source": "impact_decay_1m"},
        "mechanism": "call_auction_permanence",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp）；B=冲击永久份额（CA2 入选：−0.1050/−0.0476/t2.67/+22.1bp）。假设：竞价配置高且冲击永久（信号对应方向）=开盘信息被永久定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CN3",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "mechanism": "call_auction_elasticity",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp）；B=量价弹性（CA1 入选：−0.1249/−0.0638/t4.00/+52.3bp）。假设：竞价配置高且冲击敏感（信号对应方向）=开盘博弈在高弹性市场，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CN4",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_ABSORB_20", "source": "auction_1m"},
        "right": {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"},
        "mechanism": "open_absorb_clock_anomaly",
        "hypothesis": "两腿角色：A=开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp）；B=体量钟离散度（BF1 入选：−0.0883/−0.0259/t3.12/+9.6bp）。假设：开盘被吸收且体量钟异常（信号对应方向）=异常时序在开盘被消化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CN5",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"},
        "mechanism": "close_auction_clock_anomaly",
        "hypothesis": "两腿角色：A=收盘竞价量占比（CH6 腿，+0.0075/−0.0540/t0.77/−11.5bp）；B=体量钟离散度（BF1 入选）。假设：收盘竞价占比高且体量钟异常（信号对应方向）=收盘时段消化时序异常，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CN6",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "mechanism": "close_auction_elasticity",
        "hypothesis": "两腿角色：A=收盘竞价量占比（CH6 腿）；B=量价弹性（CA1 入选）。假设：收盘竞价占比高且冲击敏感（信号对应方向）=收盘结算在高弹性市场完成，延续。",
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
        "第 16 阶段定向配对第 8 轮（计数 2/3）：最后一批未试组合；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage16

if __name__ == "__main__":
    base.main()
