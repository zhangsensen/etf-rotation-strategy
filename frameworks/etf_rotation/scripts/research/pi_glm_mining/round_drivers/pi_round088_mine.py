#!/usr/bin/env python3
"""Round 088 driver: stage 16 step 3 — directed pairing round 2. Untried
auction x verified combinations; no repeats of r087 pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_088"

base.CANDIDATES = [
    {
        "id": "CG1",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "variance_center_high_activity",
        "hypothesis": "两腿角色：A=开盘/收盘方差比（−0.1123/−0.0926/t1.46/+38.0bp）；B=对数成交额（高活跃，+0.0661/+0.0701/t2.23/+36.8bp）。假设：方差重心前移且活跃水平高（信号高）=高活跃环境的开盘信息博弈，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CG2",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "variance_center_profile_anomaly",
        "hypothesis": "两腿角色：A=方差重心（同上）；B=量分布距离（轮廓异常，+0.0952/+0.0442/t4.04/+10.1bp）。假设：方差重心前移且量轮廓异常（信号高）=异常活动集中在开盘（信息早消化），延续。",
        "expected_sign": 1,
    },
    {
        "id": "CG3",
        "operator": "rank_spread",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "variance_center_no_damage",
        "hypothesis": "两腿角色：A=方差重心（同上）；B=最差单日（无极端损伤，+0.0635/+0.0648/t2.18/+16.2bp）。假设：方差重心前移而无极端损伤（信号高）=开盘博弈非恐慌型，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CG4",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_ABSORB_20", "source": "auction_1m"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "open_absorb_buyflow",
        "hypothesis": "两腿角色：A=开盘吸收度（−0.0295/−0.0518/t0.93/+11.7bp）；B=主买不平衡（买流，−0.0116/+0.0002/t1.01/+4.7bp）。假设：开盘信息被吸收且有买流方向（信号高）=吸收由真实买盘完成，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CG5",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "call_auction_profile_anomaly",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22/−8.6bp）；B=量分布距离（+0.0952/+0.0442/t4.04/+10.1bp）。假设：竞价配置占比高且量轮廓异常（信号高）=异常活动由开盘配置主导，延续。",
        "expected_sign": 1,
    },
    {
        "id": "CG6",
        "operator": "rank_spread",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "SIGN_ACF1_5", "source": "serial_dependence"},
        "mechanism": "call_auction_acf_confirm",
        "hypothesis": "两腿角色：A=集合竞价量占比（−0.0329/−0.0035/t2.22）；B=收益自相关（动量确认，−0.0211/+0.0070/t0.12/+3.9bp）。假设：竞价配置高且日间动量确认（信号对应方向）=开盘信息跨日延续，延续。",
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
        "第 16 阶段定向配对第 2 轮：未试 auction × verified 组合；"
        "REPORT 并列两腿单原子门 7 数字（只报告）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage16

if __name__ == "__main__":
    base.main()
