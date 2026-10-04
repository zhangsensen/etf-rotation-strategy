#!/usr/bin/env python3
"""Round 174 driver: stage 38 ("only this round") — replicate Sonnet
mechanism atoms S27B5/S29Q1/S29P10/UE3/HB1 with R_-prefixed per-definition
implementations (sonnet_repl_r2_gapdd/mfi/misc)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_174"

G = "sonnet_repl_r2_gapdd"
MF = "sonnet_repl_r2_mfi"
MS = "sonnet_repl_r2_misc"
RP = "replication_volume_free_v1"
LV = "liquidity_variability"


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"repl_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _pair("R_B5", "R_GAP_DD_CONSUMPTION_20", G, "R_MFI_EXTREME_FRAC_20", MF,
     "S27B5 复现：跳空被吃 × MFI 极端（Sonnet +58.3bp/t3.89）。"),
    _pair("R_Q1", "RP_UW_CHG_20", RP, "R_MFI_EXTREME_UW_SKEW_20", MF,
     "S29Q1 复现：水下改善 × MFI 极端水下偏斜（Sonnet +58.0bp/t3.44）。"),
    _pair("R_P10", "R_REL_UW_CATEGORY_20", MS, "LOG_AMOUNT_VOL_20", LV,
     "S29P10 复现：类内相对水下 × 成交额水平（Sonnet +66.8bp/t2.84；LOG_AMOUNT_VOL 复用现存）。"),
    _pair("R_UE3", "R_YZ_ON_SHARE_20", MS, "RP_UW_CHG_20", RP,
     "UE3 复现：YZ 隔夜方差占比 × 水下改善（Sonnet +53.3bp/t3.08）。"),
    _pair("R_HB1", "R_ON_SIGN_STREAK_20", MS, "RP_UW_CHG_20", RP,
     "HB1 复现：隔夜符号连续 × 水下改善（Sonnet +56.5bp/t2.98）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s38(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage38_sonnet_mechanism_repl"
    plan["family_note"] = (
        "第 38 阶段（只此一轮）：sonnet_repl_r2（R_ 前缀三 source：gapdd/mfi/misc）5 原子按定义实现；"
        "RP_UW_CHG_20 与 LOG_AMOUNT_VOL_20 按指令复用现存。5 条 = 主控处方（复现纪律覆盖批量下限）。"
        "小样本试算 2 只 4s。复现完即写 MECHANISM_EXHAUSTED。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s38

if __name__ == "__main__":
    base.main()
