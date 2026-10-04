#!/usr/bin/env python3
"""Round 201 driver: stage 57 continuation — cost_distribution atoms as RIGHT
legs with 12 validated shelf left legs (canonical-dedup safe vs round_200)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_201"

CD = "cost_distribution_1m"


def _pair(cid, left, lsrc, right, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": lsrc},
            "right": {"name": right, "source": CD},
            "mechanism": f"s57b_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _pair("CDQ1", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "CGO_20", -1,
     "排列熵低 × 成本悬垂高（PA1 左腿）。"),
    _pair("CDQ2", "PRICE_POSITION_20", "price_location", "CGO_60", -1,
     "价格位置低 × 成本悬垂（52 周锚×成本会计）。"),
    _pair("CDQ3", "MA_LUNCH_DIR_BET", "mechanism_atoms_v1", "UW_VOL_SHARE_60", -1,
     "午后押对 × 被套体量低。"),
    _pair("CDQ4", "VT_AUTOCORR_20", "volume_time_1m", "CGO_60", -1,
     "量钟自相关低 × 成本悬垂（CO36 左腿）。"),
    _pair("CDQ5", "LOG_AMOUNT_VOL_20", "liquidity_variability", "UW_VOL_SHARE_60", -1,
     "规模小 × 被套体量低（S32P1 同左腿）。"),
    _pair("CDQ6", "R_GAP_DD_CONSUMPTION_20", "sonnet_repl_r2_gapdd", "CGO_20", 1,
     "跳空被吃 × 成本悬垂（S27B5 左腿）。"),
    _pair("CDQ7", "ON_PREM_20", "overnight_structure_1d", "CGO_60", -1,
     "隔夜溢价 × 成本悬垂（CZ01 左腿）。"),
    _pair("CDQ8", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "CGO_20", 1,
     "尾盘一致 × 成本悬垂（CK04 右腿）。"),
    _pair("CDQ9", "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi", "UW_VOL_SHARE_60", -1,
     "MFI 极值低 × 被套体量低（NI1 模式）。"),
    _pair("CDQ10", "R_ON_SIGN_STREAK_20", "sonnet_repl_r2_misc", "COST_CONC_60", 1,
     "隔夜符号连续 × 成本集中（HB1 左腿）。"),
    _pair("CDQ11", "LUNCH_PRE_RUN_20", "lunch_break_1m", "MODE_DIST_60", -1,
     "午前抢跑 × 下方成本密集（CK04 左腿）。"),
    _pair("CDQ12", "RP_UW_CHG_20", "replication_volume_free_v1", "COST_CONC_60", 1,
     "水下改善 × 成本集中（QA8 左腿；r200 CONC×RP_PERM 非互换）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s57b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage57_cost_distribution_1m_b2"
    plan["family_note"] = (
        "第 57 阶段第二批：cost_distribution 原子转右腿 × 12 已验证左腿（每左腿 1 批、"
        "右腿 3 用顶格、canonical 去重 vs round_200 全部为新对）。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s57b

if __name__ == "__main__":
    base.main()
