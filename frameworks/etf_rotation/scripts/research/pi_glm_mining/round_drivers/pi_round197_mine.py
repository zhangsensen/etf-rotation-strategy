#!/usr/bin/env python3
"""Round 197 driver: stage 55 continuation — VTS atoms as RIGHT legs with 12
validated shelf left legs (canonical-dedup safe vs round_196)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_197"

VTS = "volume_tail_shape_1m"


def _pair(cid, left, lsrc, right, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": lsrc},
            "right": {"name": right, "source": VTS},
            "mechanism": f"s55b_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _pair("VSQ1", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "VTS_HILL_20", -1,
     "排列熵低 × 量尾不重（PA1 左腿）。"),
    _pair("VSQ2", "RP_UW_CHG_20", "replication_volume_free_v1", "VTS_HILL_20", -1,
     "水下改善 × 量尾不重（QA8 左腿）。"),
    _pair("VSQ3", "MA_LUNCH_DIR_BET", "mechanism_atoms_v1", "VTS_HILL_20", 1,
     "午后押对 × 量尾不重。"),
    _pair("VSQ4", "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi", "VTS_LOGCV_20", -1,
     "MFI 极值低 × 量离散低（NI1 模式）。"),
    _pair("VSQ5", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "VTS_LOGCV_20", -1,
     "spike 低 × 量离散低（同通道双写法，检验互补性）。"),
    _pair("VSQ6", "LUNCH_PRE_RUN_20", "lunch_break_1m", "VTS_LOGCV_20", 1,
     "午前抢跑 × 量离散（CK04 同左腿）。"),
    _pair("VSQ7", "LOG_AMOUNT_VOL_20", "liquidity_variability", "VTS_MAXSHARE_20", -1,
     "规模小 × 单 bar 集中（S32P1 同左腿）。"),
    _pair("VSQ8", "ON_PREM_20", "overnight_structure_1d", "VTS_MAXSHARE_20", -1,
     "隔夜溢价 × 单 bar 集中低（CZ01 同左腿）。"),
    _pair("VSQ9", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "VTS_MAXSHARE_20", 1,
     "尾盘一致 × 单 bar 集中。"),
    _pair("VSQ10", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", "VTS_Q95_MED_20", -1,
     "溃疡恶化 × 尖峰度高（DD48 左腿）。"),
    _pair("VSQ11", "R_GAP_DD_CONSUMPTION_20", "sonnet_repl_r2_gapdd", "VTS_Q95_MED_20", 1,
     "跳空被吃 × 尖峰度高（S27B5 左腿）。"),
    _pair("VSQ12", "R_ON_SIGN_STREAK_20", "sonnet_repl_r2_misc", "VTS_Q95_MED_20", -1,
     "隔夜符号连续 × 尖峰度低（HB1 左腿）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s55b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage55_tail_shape_rewrite_b2"
    plan["family_note"] = (
        "第 55 阶段第二批：VTS 原子转右腿 × 12 已验证左腿（每左腿 1 批、右腿 3 用顶格、"
        "canonical 去重 vs round_196 全部为新对）。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s55b

if __name__ == "__main__":
    base.main()
