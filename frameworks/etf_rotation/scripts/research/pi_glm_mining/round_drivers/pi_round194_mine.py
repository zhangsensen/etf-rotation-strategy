#!/usr/bin/env python3
"""Round 194 driver: stage 53 continuation — M3 atoms as RIGHT legs with 12
validated shelf left legs (canonical-dedup safe vs round_193)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_194"

MV3 = "mechanism_atoms_v3"


def _pair(cid, left, lsrc, right, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": lsrc},
            "right": {"name": right, "source": MV3},
            "mechanism": f"s53b_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _pair("M3Q1", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "M3_ELAST_LIQSPLIT_20", -1,
     "排列熵低 × 弹性改善（PA1 左腿；r193 ELAST×RP_UW 非互换）。"),
    _pair("M3Q2", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "M3_ELAST_LIQSPLIT_20", -1,
     "量 spike 低 × 弹性改善（CO36 模式）。"),
    _pair("M3Q3", "MA_LUNCH_DIR_BET", "mechanism_atoms_v1", "M3_ELAST_LIQSPLIT_20", 1,
     "午后押对 × 弹性改善。"),
    _pair("M3Q4", "VT_AUTOCORR_20", "volume_time_1m", "M3_TAIL_ALIGN_20", -1,
     "量钟自相关低 × 尾桶对齐（CO36 同左腿）。"),
    _pair("M3Q5", "RP_UW_CHG_20", "replication_volume_free_v1", "M3_TAIL_ALIGN_20", 1,
     "水下改善 × 尾桶对齐（QA8 同左腿）。"),
    _pair("M3Q6", "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi", "M3_TAIL_ALIGN_20", -1,
     "MFI 极值低 × 尾桶对齐（NI1 模式）。"),
    _pair("M3Q7", "LUNCH_POST_RUN_20", "lunch_break_1m", "M3_TAILMOM_USHAPE_SPLIT_20", 1,
     "午后抢跑 × 高 U 形尾桶动量（CJ16 同左腿）。"),
    _pair("M3Q8", "LUNCH_PRE_RUN_20", "lunch_break_1m", "M3_TAILMOM_USHAPE_SPLIT_20", 1,
     "午前抢跑 × 高 U 形尾桶动量（CK04 同左腿）。"),
    _pair("M3Q9", "R_GAP_DD_CONSUMPTION_20", "sonnet_repl_r2_gapdd", "M3_TAILMOM_USHAPE_SPLIT_20", 1,
     "跳空被吃 × 高 U 形尾桶动量（S27B5 左腿）。"),
    _pair("M3Q10", "ON_PREM_20", "overnight_structure_1d", "M3_AC_GINI_SPLIT_20", -1,
     "隔夜溢价 × 高 Gini AC1（CZ01 同左腿）。"),
    _pair("M3Q11", "GAP_FILL_RATE_20", "overnight_structure_1d", "M3_AC_GINI_SPLIT_20", 1,
     "跳空回补 × 高 Gini AC1。"),
    _pair("M3Q12", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", "M3_AC_GINI_SPLIT_20", -1,
     "溃疡恶化 × 高 Gini AC1（DD48 左腿）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s53b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage53_tier2_mechanisms_b2"
    plan["family_note"] = (
        "第 53 阶段第二批：M3 原子转右腿 × 12 已验证左腿（每左腿 1 批、右腿 3 用顶格、"
        "canonical 去重 vs round_193 全部为新对）。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s53b

if __name__ == "__main__":
    base.main()
