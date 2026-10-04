#!/usr/bin/env python3
"""Round 093 driver: stage 16 step 3 — directed pairing round 7.
auction_1m x newly admitted 1m-structure atoms (PV_ELASTICITY_20,
IMP_PERM_SHARE_20, LBAR_CLOCK_STD_20) + remaining close-leg combos.
All-new pairs; no repeats."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_093"

base.CANDIDATES = [
    {
        "id": "CM1",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "mechanism": "variance_center_elasticity",
        "hypothesis": "两腿角色：A=开盘/收盘方差比（−0.1123/−0.0926/t1.46/+38.0bp）；B=量价弹性（CA1 入选：−0.1249/−0.0638/t4.00/+52.3bp）。假设：方差重心前移且冲击敏感（信号对应方向）=开盘博弈在高弹性市场展开，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CM2",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "IMP_PERM_SHARE_20", "source": "impact_decay_1m"},
        "mechanism": "variance_center_permanence",
        "hypothesis": "两腿角色：A=方差重心（同上）；B=冲击永久份额（CA2 入选：−0.1050/−0.0476/t2.67/+22.1bp）。假设：方差重心前移且冲击永久（信号对应方向）=开盘信息被永久定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CM3",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"},
        "mechanism": "call_auction_clock_anomaly",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp）；B=体量钟离散度（BF1 入选：−0.0883/−0.0259/t3.12/+9.6bp）。假设：竞价配置高且体量钟异常（信号对应方向）=时间维异常集中在开盘，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CM4",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_ABSORB_20", "source": "auction_1m"},
        "right": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "mechanism": "open_absorb_elasticity",
        "hypothesis": "两腿角色：A=开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp）；B=量价弹性（CA1 入选）。假设：开盘信息被吸收且市场弹性高（信号对应方向）=吸收在高弹性环境完成，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CM5",
        "operator": "rank_spread",
        "left": {"name": "AUC_POST_OPEN_REVERT_20", "source": "auction_1m"},
        "right": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "mechanism": "post_open_revert_elasticity",
        "hypothesis": "两腿角色：A=开盘后 5 分钟回复比例（−0.0324/+0.0215/t0.68/−16.8bp）；B=量价弹性（CA1 入选）。假设：开盘冲击回复且弹性高（信号对应方向）=回复型开盘（临时冲击主导），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CM6",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_CONSIST_20", "source": "auction_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "close_direction_buyflow",
        "hypothesis": "两腿角色：A=尾 bar 方向一致度（CJ6 腿，−0.0154/+0.0111/t1.12/−23.9bp）；B=主买不平衡（买流，−0.0116/+0.0002/t1.01/+4.7bp）。假设：收盘方向一致且有买流（信号对应方向）=收盘由买方主导收官，延续。",
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
        "第 16 阶段定向配对第 7 轮：auction × 新入账 1m 结构原子；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage16

if __name__ == "__main__":
    base.main()
