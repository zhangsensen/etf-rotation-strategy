#!/usr/bin/env python3
"""Round 177 driver: stage 41 — session direction-bet mechanism deepening
(session_direction_bet_1m, 4 atoms). Health 4/4 clean (max 0.449).
4 singles + 12 confirmed-leg pairs = 16."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_177"

SB = "session_direction_bet_1m"


def _atom(cid, name, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": SB},
        "right": {"name": name, "source": SB},
        "mechanism": "session_bet", "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": SB},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"s41_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _atom("SE01", "SB_MORN_BET_20", "午前 11:20-11:30 量占比 × 下午收益符号：早段知情流押注下午（HKS 2010 时段动量）。", 1),
    _atom("SE02", "SB_OPEN_BET_20", "开盘首 10 分钟量占比 × 全日收益符号：开盘知情流押注全日。", 1),
    _atom("SE03", "SB_TAIL_BET_20", "尾 10 分钟量占比 × 尾 30 分钟收益符号：尾盘知情流押注收盘（同场信息，无次日泄漏）。", 1),
    _atom("SE04", "SB_LUNCH_WR_MINUS_INT_20", "午后押方向 20 日胜率 − 押注强度：信息优势净额。", 1),
    _pair("SE07", "SB_MORN_BET_20", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m",
     "簇 SB_MORN：午前押下午 × 事件密集。"),
    _pair("SE08", "SB_MORN_BET_20", "RP_PERM_ENT_D3_20", "replication_volume_free_v1",
     "簇 SB_MORN：午前押下午 × 排列熵。"),
    _pair("SE09", "SB_MORN_BET_20", "PD_D1_CHG_20", "price_delay",
     "簇 SB_MORN：午前押下午 × 延迟改善。"),
    _pair("SE10", "SB_OPEN_BET_20", "ON_PREM_20", "overnight_structure_1d",
     "簇 SB_OPEN：开盘押日 × 隔夜溢价。"),
    _pair("SE11", "SB_OPEN_BET_20", "RESILIENCY_20", "liquidity_commonality_1m",
     "簇 SB_OPEN：开盘押日 × 微结构弹性。"),
    _pair("SE12", "SB_OPEN_BET_20", "RCC_BB_SQUEEZE_20", "range_contraction_cycle",
     "簇 SB_OPEN：开盘押日 × squeeze。"),
    _pair("SE13", "SB_TAIL_BET_20", "TICK_IMBALANCE_20", "bar_size_order_flow",
     "簇 SB_TAIL：尾盘押尾盘 × 主买不平衡。"),
    _pair("SE14", "SB_TAIL_BET_20", "VFP_RECOVERY_20", "volume_free_path_v1",
     "簇 SB_TAIL：尾盘押尾盘 × 回撤恢复。"),
    _pair("SE15", "SB_TAIL_BET_20", "PRICE_POSITION_20", "price_location",
     "簇 SB_TAIL：尾盘押尾盘 × 价格位置。"),
    _pair("SE16", "SB_LUNCH_WR_MINUS_INT_20", "SCL_DFA_RET_20", "scaling_memory_1m",
     "簇 SB_WR：押对胜率-强度差 × 路径趋势。"),
    _pair("SE17", "SB_LUNCH_WR_MINUS_INT_20", "ULCER_20", "downside_risk",
     "簇 SB_WR：押对胜率-强度差 × 溃疡低。"),
    _pair("SE18", "SB_LUNCH_WR_MINUS_INT_20", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d",
     "簇 SB_WR：押对胜率-强度差 × 52 周锚。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s41(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage41_session_direction_bet"
    plan["family_note"] = (
        "第 41 阶段 session_direction_bet_1m（MA_LUNCH_DIR_BET 机制加深；"
        "Barclay-Hendershott 2003 / Heston-Korajczyk-Sadka 2010 / Gao-Han-Li-Zhou 2018）。"
        "尾盘押注改为同场信息（尾10分钟量 × 尾30分钟符号）避免 D+1 泄漏。"
        "体检 4/4 清洁（max 0.449 vs MA_LUNCH_DIR_BET）。4 单原子 + 12 配对 = 16。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s41

if __name__ == "__main__":
    base.main()
