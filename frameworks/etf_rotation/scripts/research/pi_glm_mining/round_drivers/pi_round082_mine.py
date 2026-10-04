#!/usr/bin/env python3
"""Round 082 driver: stage 15 step 3 — directed pairing round 1.
impact_decay_1m new atoms (CA1 PV_ELASTICITY_20 / CA2 IMP_PERM_SHARE_20
admitted) x verified pool atoms. REPORT lists both legs' gate-7 numbers."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_082"

base.CANDIDATES = [
    {
        "id": "CC1",
        "operator": "rank_spread",
        "left": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "elasticity_chip_lock",
        "hypothesis": "两腿角色：A=量价弹性（冲击敏感度，CA1 门 7 入选：−0.1249/−0.0638/t4.00/+52.3bp）；B=筹码区间宽度（集中度，−0.0574/−0.0620/t0.70/+14.6bp）。假设：冲击敏感而筹码集中（信号高）=集中盘上的高弹性（BJ5 骨架延伸），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CC2",
        "operator": "rank_spread",
        "left": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "elasticity_resilient",
        "hypothesis": "两腿角色：A=量价弹性（CA1 入选）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）。假设：冲击敏感且冲击后快回复（信号高）=深度浅但有效的健康薄市场，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CC3",
        "operator": "rank_spread",
        "left": {"name": "IMP_PERM_SHARE_20", "source": "impact_decay_1m"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "impact_permanence_trend_persist",
        "hypothesis": "两腿角色：A=冲击永久份额（CA2 入选：−0.1050/−0.0476/t2.67/+22.1bp）；B=缺口修复率（趋势持续，−0.0597/−0.0430/t2.59/+9.8bp）。假设：冲击永久且趋势持续（信号高）=冲击被趋势吸收，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CC4",
        "operator": "rank_spread",
        "left": {"name": "IMP_PERM_SHARE_20", "source": "impact_decay_1m"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "impact_permanence_no_damage",
        "hypothesis": "两腿角色：A=冲击永久份额（CA2 入选）；B=最差单日（无极端损伤，+0.0635/+0.0648/t2.18/+16.2bp）。假设：冲击永久而无极端损伤（信号高）=有序承接下的永久冲击，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CC5",
        "operator": "rank_spread",
        "left": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "elasticity_acf_confirm",
        "hypothesis": "两腿角色：A=量价弹性（CA1 入选）；B=5 日收益自相关（动量确认，−0.0211/+0.0070/t0.12/+3.9bp）。假设：冲击敏感而日间动量确认（信号高）=弹性是趋势性参与（非噪声），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CC6",
        "operator": "rank_spread",
        "left": {"name": "IMP_DECAY_SLOPE_20", "source": "impact_decay_1m"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "decay_profile_anomaly",
        "hypothesis": "两腿角色：A=冲击响应衰减斜率（+0.0498/+0.0005/t1.70/+4.1bp）；B=量分布距离（轮廓异常，+0.0952/+0.0442/t4.04/+10.1bp）。假设：冲击快衰减且活动轮廓异常（信号高）=异常活动被市场快速消化（流动性好），延续。",
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
        "第 15 阶段定向配对第 1 轮：impact_decay_1m 新原子 × 已验证原子；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage15

if __name__ == "__main__":
    base.main()
