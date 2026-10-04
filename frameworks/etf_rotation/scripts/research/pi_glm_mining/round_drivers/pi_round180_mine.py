#!/usr/bin/env python3
"""Round 180 driver: stage 43 ("only this round") — final Sonnet pair
replications S32P1/WA1/XC5/MH3/S47D3 with R_-prefixed per-definition atoms
(sonnet_repl_r3, five sources for cross-family compliance)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_180"

UW = "sonnet_repl_r3_uw"
XC = "sonnet_repl_r3_xc"
TL = "sonnet_repl_r3_tail"
MH = "sonnet_repl_r3_mh"
SP = "sonnet_repl_r3_split"
LV = "liquidity_variability"
MF = "sonnet_repl_r2_mfi"
MS = "microstructure_1m"


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"repl_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _pair("R_S32P1", "R_REL_UW_CATEGORY_CHG_20", UW, "LOG_AMOUNT_VOL_20", LV,
     "S32P1 复现：类内相对水下变化 × 成交额（Sonnet +58.6bp/t3.10；LOG_AMOUNT_VOL 复用现存）。"),
    _pair("R_WA1", "R_VT_UNDERWATER_FRAC_20", UW, "R_MFI_EXTREME_FRAC_20", MF,
     "WA1 复现：量钟水下占比 × MFI 极端（Sonnet +45.3bp/t2.15；MFI 复用 r168 R_ 实现）。"),
    _pair("R_XC5", "R_VT_BUCKET_COUNT_SHIFT_20", XC, "R_BEST_DAY_20", TL,
     "XC5 复现：桶数变化 × 20 日最大日收益（Sonnet +45.4bp/t2.27）。"),
    _pair("R_MH3", "R_NOISE_VAR_20", MH, "ROLL_SPREAD_20", MS,
     "MH3 复现（原定义 R_ 实现）：噪声方差 × Roll 价差（Sonnet +39.5bp/t2.48；ROLL_SPREAD 为定义本身 legs）。"),
    _pair("R_S47D3", "R_ON_SHARE_PMCONSIST_SPLIT_20", SP, "R_MFI_EXTREME_FRAC_20", MF,
     "S47D3 复现：YZ 隔夜占比分半 × 午后一致率差 − MFI 极端（Sonnet +36.6bp/t2.31）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s43(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage43_sonnet_final_repl"
    plan["family_note"] = (
        "第 43 阶段（只此一轮）：sonnet_repl_r3 五 source（uw/xc/tail/mh/split）按定义实现 6 原子；"
        "R_MFI_EXTREME_FRAC_20 复用 r168 sonnet_repl_r2_mfi（同一定义 R_ 实现）；"
        "LOG_AMOUNT_VOL_20/ROLL_SPREAD_20 复用 pi 现存（定义本身/主控注明）。5 条 = 主控处方。"
        "复现完 pi 对 Sonnet 全部两窗口显著候选均有独立实现。试算 3s/2 只。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s43

if __name__ == "__main__":
    base.main()
