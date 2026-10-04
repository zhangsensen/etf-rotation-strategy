#!/usr/bin/env python3
"""Round 087 driver: stage 16 step 3 — directed pairing round 1.
auction_1m atoms x verified pool atoms; REPORT lists both legs' gate-7."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_087"

base.CANDIDATES = [
    {
        "id": "CF1",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "variance_center_chip_lock",
        "hypothesis": "两腿角色：A=开盘/收盘方差比（方差重心前移，−0.1123/−0.0926/t1.46/+38.0bp）；B=筹码区间宽度（集中度，−0.0574/−0.0620/t0.70/+14.6bp）。假设：方差重心前移而筹码集中（信号高）=集中盘上的开盘信息消化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CF2",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "variance_center_buyflow",
        "hypothesis": "两腿角色：A=方差重心（同上）；B=主买不平衡（买流方向，−0.0116/+0.0002/t1.01/+4.7bp）。假设：方差重心前移且有买流方向（信号高）=开盘博弈有主导方，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CF3",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"},
        "mechanism": "variance_center_close_confirm",
        "hypothesis": "两腿角色：A=方差重心（同上）；B=收盘确认（−0.0233/−0.0313/t−0.30/+27.3bp）。假设：方差重心前移且收盘有确认（信号高）=信息早盘消化且收盘不翻盘，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CF4",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_ABSORB_20", "source": "auction_1m"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "open_absorb_high_activity",
        "hypothesis": "两腿角色：A=开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp）；B=对数成交额（高活跃，+0.0661/+0.0701/t2.23/+36.8bp）。假设：开盘信息被吸收且活跃水平高（信号高）=高活跃环境的开盘消化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CF5",
        "operator": "rank_spread",
        "left": {"name": "AUC_POST_OPEN_REVERT_20", "source": "auction_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "post_open_revert_resilient",
        "hypothesis": "两腿角色：A=开盘后 5 分钟回复比例（开盘冲击回复，−0.0324/+0.0215/t0.68/−16.8bp）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）。假设：开盘冲击回复且微结构有弹性（信号高）=薄但健康的市场消化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CF6",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "call_auction_trend_persist",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp）；B=缺口修复率（趋势持续，−0.0597/−0.0430/t2.59/+9.8bp）。假设：竞价配置占比高而趋势持续（信号对应方向）=开盘配置服务于趋势，延续。",
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
        "第 16 阶段定向配对第 1 轮：auction_1m 新原子 × 已验证原子；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage16

if __name__ == "__main__":
    base.main()
