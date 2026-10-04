#!/usr/bin/env python3
"""Round 084 driver: stage 15 step 3 — directed pairing round 3 (entering
streak 2/3). Uses non-dominant new legs (DECAY_SLOPE/SIGNFLIP/ELAST_SHIFT)
to avoid the shadow trap that consumed r082/083 strong-leg pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_084"

base.CANDIDATES = [
    {
        "id": "CE1",
        "operator": "rank_spread",
        "left": {"name": "IMP_DECAY_SLOPE_20", "source": "impact_decay_1m"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "fast_decay_acf_confirm",
        "hypothesis": "两腿角色：A=冲击响应衰减斜率（快衰减，+0.0498/+0.0005/t1.70/+4.1bp）；B=5 日收益自相关（动量确认，−0.0211/+0.0070/t0.12/+3.9bp）。假设：日内冲击快衰减且日间动量确认（信号高）=多周期健康延续，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CE2",
        "operator": "rank_spread",
        "left": {"name": "IMP_DECAY_SLOPE_20", "source": "impact_decay_1m"},
        "right": {"name": "PRICE_POSITION_20", "source": "price_location"},
        "mechanism": "fast_decay_high_position",
        "hypothesis": "两腿角色：A=快衰减（+0.0498/+0.0005/t1.70/+4.1bp）；B=价格区间位置（+0.0128/+0.0275/t1.64/+8.5bp）。假设：冲击快衰减且价格处于高位（信号高）=高位高深度（承接充裕），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CE3",
        "operator": "rank_spread",
        "left": {"name": "PV_SIGNFLIP_20", "source": "impact_decay_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "regime_switch_resilient",
        "hypothesis": "两腿角色：A=日内量价相关符号翻转频率（体制切换，+0.0187/+0.0029/t0.72/−20.7bp）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）。假设：量价体制频繁切换且微结构有弹性（信号高）=高频博弈在弹性环境中被消化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CE4",
        "operator": "rank_spread",
        "left": {"name": "PV_SIGNFLIP_20", "source": "impact_decay_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "regime_switch_calm_category",
        "hypothesis": "两腿角色：A=体制切换频率（+0.0187/+0.0029/t0.72）；B=类别波动（−0.0711/−0.0653/t2.42/+19.0bp）。假设：个股量价体制切换而类别平静（信号高）=自身博弈（非环境），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CE5",
        "operator": "rank_spread",
        "left": {"name": "PV_ELAST_SHIFT_20", "source": "impact_decay_1m"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "elasticity_migration_activity",
        "hypothesis": "两腿角色：A=量价弹性 20 日迁移（−0.0734/+0.0297/t1.62/审超−48.1bp 反号）；B=大 bar 量占比（+0.0832/+0.0548/t2.92/+41.6bp）。假设：弹性正迁移（信号对应方向）而活动强度高（信号对应方向）=活跃且有主体的换手结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CE6",
        "operator": "rank_spread",
        "left": {"name": "PV_ELAST_SHIFT_20", "source": "impact_decay_1m"},
        "right": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "mechanism": "elasticity_migration_close_confirm",
        "hypothesis": "两腿角色：A=弹性迁移（−0.0734/+0.0297/t1.62）；B=收盘确认（−0.0233/−0.0313/t−0.30/+27.3bp）。假设：弹性迁移伴随收盘方向确认（信号对应方向）=迁移由主导方推动（非漂移），延续。",
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
        "第 15 阶段定向配对第 3 轮（计数 2/3）：非主导新腿（DECAY_SLOPE/SIGNFLIP/ELAST_SHIFT）避免影子吞噬；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage15

if __name__ == "__main__":
    base.main()
