#!/usr/bin/env python3
"""Round 083 driver: stage 15 step 3 — directed pairing round 2.
r082 lesson: ELASTICITY/PERM_SHARE x vol-type legs decay in audit and risk
shadows; this round pairs them with flow/location/session legs only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_083"

base.CANDIDATES = [
    {
        "id": "CD1",
        "operator": "rank_spread",
        "left": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "elasticity_buyflow",
        "hypothesis": "两腿角色：A=量价弹性（CA1 入选：−0.1249/−0.0638/t4.00/+52.3bp）；B=主买不平衡（买流方向，−0.0116/+0.0002/t1.01/+4.7bp）。假设：冲击敏感且有买流方向（信号高）=弹性由定向买流驱动（非双向噪声），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CD2",
        "operator": "rank_spread",
        "left": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "elasticity_high_position",
        "hypothesis": "两腿角色：A=量价弹性（CA1 入选）；B=价格区间位置（获利位置，+0.0128/+0.0275/t1.64/+8.5bp）。假设：冲击敏感且价格处于高位（信号高）=高位活跃博弈（强势筹码换手），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CD3",
        "operator": "rank_spread",
        "left": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "right": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "mechanism": "elasticity_close_confirm",
        "hypothesis": "两腿角色：A=量价弹性（CA1 入选）；B=尾 5 分钟与全日方向一致（收盘确认，−0.0233/−0.0313/t−0.30/+27.3bp）。假设：冲击敏感且收盘有确认（信号高）=日内博弈有收官主导方，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CD4",
        "operator": "rank_spread",
        "left": {"name": "IMP_PERM_SHARE_20", "source": "impact_decay_1m"},
        "right": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "mechanism": "impact_permanence_directional_skew",
        "hypothesis": "两腿角色：A=冲击永久份额（CA2 入选：−0.1050/−0.0476/t2.67/+22.1bp）；B=大 bar 方向偏度（定向大单，−0.0166/+0.0187/t1.16/+8.7bp）。假设：冲击永久且大单方向一致（信号高）=定向 metaorder 推进，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CD5",
        "operator": "rank_spread",
        "left": {"name": "IMP_PERM_SHARE_20", "source": "impact_decay_1m"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "impact_permanence_open_config",
        "hypothesis": "两腿角色：A=冲击永久份额（CA2 入选）；B=开盘 30 分钟量占比（开盘配置，−0.1038/−0.0489/t3.30/−10.5bp）。假设：冲击永久且开盘配置占比高（信号高）=开盘时段机构执行（信息消化集中），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CD6",
        "operator": "rank_spread",
        "left": {"name": "IMP_DECAY_SLOPE_20", "source": "impact_decay_1m"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "fast_decay_no_damage",
        "hypothesis": "两腿角色：A=冲击响应衰减斜率（快衰减，+0.0498/+0.0005/t1.70/+4.1bp）；B=最差单日（无极端损伤，+0.0635/+0.0648/t2.18/+16.2bp）。假设：冲击快衰减且无极端损伤（信号高）=市场深度健康（冲击被迅速吸收），延续。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage15(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage15_impact_decay_pairing"
    plan["pairing_note"] = (
        "第 15 阶段定向配对第 2 轮：ELASTICITY/PERM_SHARE × 流向/位置/时段腿 + DECAY × 损伤腿；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage15

if __name__ == "__main__":
    base.main()
