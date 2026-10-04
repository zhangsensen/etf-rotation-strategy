#!/usr/bin/env python3
"""Round 089 driver: stage 16 step 3 — directed pairing round 3 (entering
streak 2/3). Remaining auction x verified legs; zero round triggers
stage-16 exhaustion artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_089"

base.CANDIDATES = [
    {
        "id": "CH1",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "variance_center_resilient",
        "hypothesis": "两腿角色：A=开盘/收盘方差比（−0.1123/−0.0926/t1.46/+38.0bp）；B=微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp）。假设：方差重心前移且微结构有弹性（信号高）=开盘博弈发生在有回复力的市场，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CH2",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "variance_center_acf_confirm",
        "hypothesis": "两腿角色：A=方差重心（同上）；B=5 日收益自相关（动量确认，−0.0211/+0.0070/t0.12/+3.9bp）。假设：方差重心前移且日间动量确认（信号高）=开盘信息跨日延续，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CH3",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "variance_center_calm_category",
        "hypothesis": "两腿角色：A=方差重心（同上）；B=类别波动（环境噪声，−0.0711/−0.0653/t2.42/+19.0bp）。假设：方差重心前移而类别平静（信号高）=自身信息（非环境），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CH4",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_ABSORB_20", "source": "auction_1m"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "open_absorb_trend_persist",
        "hypothesis": "两腿角色：A=开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp）；B=缺口修复率（趋势持续，−0.0597/−0.0430/t2.59/+9.8bp）。假设：开盘信息被吸收且趋势持续（信号高）=吸收服务于趋势，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CH5",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_ABSORB_20", "source": "auction_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "open_absorb_calm_category",
        "hypothesis": "两腿角色：A=开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp）；B=类别波动（−0.0711/−0.0653/t2.42/+19.0bp）。假设：开盘被吸收而类别平静（信号高）=个股层面信息消化（非环境推动），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CH6",
        "operator": "rank_spread",
        "left": {"name": "AUC_CLOSE_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "close_auction_high_activity",
        "hypothesis": "两腿角色：A=收盘竞价量占比（+0.0075/−0.0540/t0.77/−11.5bp）；B=对数成交额（高活跃，+0.0661/+0.0701/t2.23/+36.8bp）。假设：收盘竞价占比高且活跃水平高（信号对应方向）=收盘时段机构结算活跃，延续。",
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
        "第 16 阶段定向配对第 3 轮（计数 2/3）：VAR_RATIO 剩余垂直腿 + 吸收/竞价尾腿；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage16

if __name__ == "__main__":
    base.main()
