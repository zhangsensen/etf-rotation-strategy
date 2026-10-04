#!/usr/bin/env python3
"""Round 203 driver: stage 57b — true-PIT-turnover CGO (cgo_true_turnover_v2),
6 atoms + 18 pairs (rights prefer GAP_DD/PERM/UW_CHG per master)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_203"

CT = "cgo_true_turnover_v2"


def _atom(cid, name, sign, hyp):
    return {"id": cid, "operator": "atomic",
            "left": {"name": name, "source": CT},
            "right": {"name": name, "source": CT},
            "mechanism": f"s57b_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


def _pair(cid, left, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": CT},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s57b_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _atom("CGA", "CGO_TT_60", 1,
     "真 PIT 换手 CGO（60 日参考价）：高未实现盈利 → 处置效应延迟兑现（Grinblatt–Han 2005）。"),
    _atom("CGB", "CGO_TT_250", 1,
     "真 PIT 换手 CGO（250 日参考价）。"),
    _atom("CGC", "GAIN_OVERHANG_TT_60", 1,
     "存活权重中成本 ≤ 现价的占比（60 日窗）：盈利盘主导=上方抛压已消化。"),
    _atom("CGD", "LOSS_OVERHANG_TT_60", -1,
     "存活权重中成本 > 现价的占比（60 日窗）：套牢盘重=反弹阻力。"),
    _atom("CGE", "UW_SHARE_TT_250", -1,
     "250 日窗被套体量占比：长视界水下权重。"),
    _atom("CGF", "RP_CHANGE_TT_20", 1,
     "参考价 20 日变化：成本基线上移速度=新资金入场强度。"),

    _pair("CGP1", "CGO_TT_60", "R_GAP_DD_CONSUMPTION_20", "sonnet_repl_r2_gapdd", -1,
     "CGO × 跳空被吃低（S27B5 右腿重测于正确左腿下）。"),
    _pair("CGP2", "CGO_TT_60", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", -1,
     "CGO × 排列熵低（PA1 右腿重测）。"),
    _pair("CGP3", "CGO_TT_60", "RP_UW_CHG_20", "replication_volume_free_v1", 1,
     "CGO × 水下改善（QA8 右腿重测）。"),
    _pair("CGP4", "CGO_TT_250", "RP_UW_CHG_20", "replication_volume_free_v1", 1,
     "250 日 CGO × 水下改善。"),
    _pair("CGP5", "CGO_TT_250", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", 1,
     "250 日 CGO × 量事件（BB1 右腿）。"),
    _pair("CGP6", "CGO_TT_250", "LOG_AMOUNT_VOL_20", "liquidity_variability", -1,
     "250 日 CGO × 规模小（S32P1 模式）。"),
    _pair("CGP7", "GAIN_OVERHANG_TT_60", "R_GAP_DD_CONSUMPTION_20", "sonnet_repl_r2_gapdd", 1,
     "盈利盘占比 × 跳空被吃低。"),
    _pair("CGP8", "GAIN_OVERHANG_TT_60", "ON_PREM_20", "overnight_structure_1d", 1,
     "盈利盘占比 × 隔夜溢价。"),
    _pair("CGP9", "GAIN_OVERHANG_TT_60", "MA_LUNCH_DIR_BET", "mechanism_atoms_v1", 1,
     "盈利盘占比 × 午后押对。"),
    _pair("CGP10", "LOSS_OVERHANG_TT_60", "RP_UW_CHG_20", "replication_volume_free_v1", -1,
     "套牢盘 × 水下改善。"),
    _pair("CGP11", "LOSS_OVERHANG_TT_60", "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi", -1,
     "套牢盘 × MFI 极值低。"),
    _pair("CGP12", "LOSS_OVERHANG_TT_60", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", -1,
     "套牢盘 × 尾盘一致度低（CK04 右腿）。"),
    _pair("CGP13", "UW_SHARE_TT_250", "R_GAP_DD_CONSUMPTION_20", "sonnet_repl_r2_gapdd", -1,
     "250 日被套 × 跳空被吃低。"),
    _pair("CGP14", "UW_SHARE_TT_250", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", -1,
     "250 日被套 × 排列熵低。"),
    _pair("CGP15", "UW_SHARE_TT_250", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", -1,
     "250 日被套 × 量事件低。"),
    _pair("CGP16", "RP_CHANGE_TT_20", "RP_UW_CHG_20", "replication_volume_free_v1", 1,
     "成本基线上移 × 水下改善。"),
    _pair("CGP17", "RP_CHANGE_TT_20", "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi", -1,
     "成本基线上移 × MFI 极值低。"),
    _pair("CGP18", "RP_CHANGE_TT_20", "LOG_AMOUNT_VOL_20", "liquidity_variability", -1,
     "成本基线上移 × 规模小。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s57b2(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage57b_cgo_true_turnover"
    plan["family_note"] = (
        "第 57b 阶段（E30 修正）：换手率改用 PIT 基金份额（fund_share usable_from_date），"
        "6 原子 + 18 配对。第 57 阶段全部 CD 原子与入选标 DEGENERATE_RET1_SHADOW 不入表。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s57b2

if __name__ == "__main__":
    base.main()
