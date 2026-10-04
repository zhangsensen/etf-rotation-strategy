#!/usr/bin/env python3
"""Round 116 driver: stage 18 step 2 (merged round, 12 candidates).
Part A: atomic gate-7 re-adjudication of 5 remaining lunch_break atoms.
Part B: first lunch x verified-leg pairs (new x new included)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_116"

LB = "lunch_break_1m"


def _atom(cid, name, mech, lit, note, sign=1):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": LB}, "right": {"name": name, "source": LB},
        "mechanism": mech, "hypothesis": f"{note} 文献：{lit}。", "expected_sign": sign,
    }


def _pair(cid, left, lsrc, right, rsrc, mech, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc}, "right": {"name": right, "source": rsrc},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": 1,
    }


base.CANDIDATES = [
    # Part A: atomic re-adjudication (5)
    _atom("AE1", "LUNCH_GAP_20", "lunch_gap_mean",
          "Barclay–Hendershott 2003/2004；Hong–Wang 2000",
          "午间跳空 20 日均值。体检 disc +0.0126/审计 +0.0101/t0.85/审超 −14.9bp。", 1),
    _atom("AE2", "LUNCH_GAP_ABS_20", "lunch_gap_abs",
          "Barclay–Hendershott 2003/2004（跳空幅度）",
          "|午间跳空| 20 日均值。体检 disc −0.0238/审计 −0.0234/t0.70/+5.6bp。", -1),
    _atom("AE3", "LUNCH_REVERT15_20", "lunch_revert15",
          "Hong–Wang 2000 周期闭合",
          "午间跳空 15 分钟回复比例（60 日窗）。体检 disc −0.0079/审计 −0.0203/t0.82/+13.2bp。", -1),
    _atom("AE4", "LUNCH_POST_RUN_20", "lunch_post_run",
          "Barclay–Hendershott 2003（午后抢跑）",
          "午后抢跑量占比（13:00–13:10）。体检 disc +0.0198/审计 +0.0441/t1.22/+8.0bp。", 1),
    _atom("AE5", "AM_PM_RET_CORR_20", "am_pm_ret_corr",
          "时段间动量/反转文献",
          "上午/下午收益 20 日相关。体检 disc −0.0089/审计 −0.0310/t−0.67/−8.6bp。", -1),
    # Part B: lunch x verified pairs (7)
    _pair("AE6", "LUNCH_PRE_RUN_20", LB, "LOG_AMOUNT_VOL_20", "liquidity_variability",
          "prerun_high_activity", "午前抢跑 × 高活跃（+0.0661/+0.0701/t2.23/+36.8bp）：抢跑发生在活跃环境，延续。"),
    _pair("AE7", "LUNCH_PRE_RUN_20", LB, "PV_ELASTICITY_20", "impact_decay_1m",
          "prerun_elasticity", "午前抢跑 × 量价弹性（CA1 入选 −0.1249/−0.0638/t4.00/+52.3bp）：新×新，延续。"),
    _pair("AE8", "AM_PM_RET_CORR_20", LB, "WORST_DAY_20", "return_tail_shape",
          "amcorr_no_damage", "时段相关 × 无极端损伤（+0.0635/+0.0648/t2.18/+16.2bp），延续。"),
    _pair("AE9", "AM_PM_RET_CORR_20", LB, "RESILIENCY_20", "liquidity_commonality_1m",
          "amcorr_resilient", "时段相关 × 微结构弹性（−0.1142/−0.0415/t2.08/+2.2bp），延续。"),
    _pair("AE10", "LUNCH_POST_RUN_20", LB, "AUC_CLOSE_VOLSHARE_20", "auction_1m",
          "post_run_close_auction", "午后抢跑 × 收盘竞价份额（CH6 腿 +0.0075/−0.0540/t0.77/−11.5bp）：新×新，延续。"),
    _pair("AE11", "LUNCH_GAP_ABS_20", LB, "IMP_PERM_SHARE_20", "impact_decay_1m",
          "gap_abs_permanence", "午间跳空幅度 × 冲击永久份额（CA2 入选 −0.1050/−0.0476/t2.67/+22.1bp）：新×新，延续。"),
    _pair("AE12", "LUNCH_REVERT15_20", LB, "GAP_FILL_FRACTION_60", "gap_repair",
          "lunch_revert_trend", "午间回复 × 趋势持续（−0.0597/−0.0430/t2.59/+9.8bp），延续。"),
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage18(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage18_lunch_break"
    plan["pairing_note"] = "合并轮：5 原子重裁 + 7 条 lunch×verified 配对（含 3 条新×新）；同族不配"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage18

if __name__ == "__main__":
    base.main()
