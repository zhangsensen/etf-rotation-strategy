#!/usr/bin/env python3
"""Round 204 driver: stage 57b continuation — per master addendum:
(a) ret20 controls for each CGO left leg; (b) TT atoms as RIGHT legs with
validated shelf lefts. 20 candidates."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_204"

CT = "cgo_true_turnover_v2"


def _pair(cid, left, lsrc, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": lsrc},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s57c_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    # —— 对照组（RET20 动量代理，逐右腿与 CGO 版并列）——
    _pair("CTC1", "RET20_CLOSE", CT, "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi", -1,
     "对照（CGP17）：ret20 动量 × MFI 极值低——与 RP_CHANGE_TT 版并列测成本会计增量。"),
    _pair("CTC2", "RET20_CLOSE", CT, "RP_UW_CHG_20", "replication_volume_free_v1", 1,
     "对照（CGP3/4/16）：ret20 × 水下改善。"),
    _pair("CTC3", "RET20_CLOSE", CT, "R_GAP_DD_CONSUMPTION_20", "sonnet_repl_r2_gapdd", -1,
     "对照（CGP1/7/13）：ret20 × 跳空被吃低。"),
    _pair("CTC4", "RET20_CLOSE", CT, "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", -1,
     "对照（CGP5/15）：ret20 × 量事件低。"),
    _pair("CTC5", "RET20_CLOSE", CT, "LOG_AMOUNT_VOL_20", "liquidity_variability", -1,
     "对照（CGP6/18）：ret20 × 规模小。"),
    _pair("CTC6", "RET20_CLOSE", CT, "ON_PREM_20", "overnight_structure_1d", 1,
     "对照（CGP8）：ret20 × 隔夜溢价。"),

    # —— TT 原子转右腿 × 已验证左腿 ——
    _pair("CTP1", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "CGO_TT_60", CT, -1,
     "量事件低 × CGO 高（BB1 右腿换位）。"),
    _pair("CTP2", "MA_LUNCH_DIR_BET", "mechanism_atoms_v1", "CGO_TT_60", CT, 1,
     "午后押对 × CGO 高。"),
    _pair("CTP3", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", "CGO_TT_250", CT, -1,
     "尾盘一致低 × 250 日 CGO（CK04 右腿换位）。"),
    _pair("CTP4", "ON_PREM_20", "overnight_structure_1d", "CGO_TT_250", CT, -1,
     "隔夜溢价低 × 250 日 CGO（CZ01 左腿）。"),
    _pair("CTP5", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "LOSS_OVERHANG_TT_60", CT, -1,
     "排列熵低 × 套牢盘轻（PA1 左腿）。"),
    _pair("CTP6", "LOG_AMOUNT_VOL_20", "liquidity_variability", "LOSS_OVERHANG_TT_60", CT, -1,
     "规模小 × 套牢盘轻（S32P1 同左腿）。"),
    _pair("CTP7", "LUNCH_POST_RUN_20", "lunch_break_1m", "CGO_TT_60", CT, -1,
     "午后抢跑 × CGO（CJ16 左腿）。"),
    _pair("CTP8", "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi", "CGO_TT_250", CT, -1,
     "MFI 极值低 × 250 日 CGO。"),
    _pair("CTP9", "LUNCH_PRE_RUN_20", "lunch_break_1m", "LOSS_OVERHANG_TT_60", CT, -1,
     "午前抢跑 × 套牢盘轻（CK04 左腿）。"),
    _pair("CTP10", "GAP_FILL_RATE_20", "overnight_structure_1d", "UW_SHARE_TT_250", CT, -1,
     "跳空回补 × 250 日被套低。"),
    _pair("CTP11", "R_GAP_DD_CONSUMPTION_20", "sonnet_repl_r2_gapdd", "RP_CHANGE_TT_20", CT, 1,
     "跳空被吃 × 成本基线上移（S27B5 左腿）。"),
    _pair("CTP12", "RESILIENCY_20", "liquidity_commonality_1m", "RP_CHANGE_TT_20", CT, -1,
     "微结构弹性低 × 成本基线上移。"),
    _pair("CTP13", "R_ON_SIGN_STREAK_20", "sonnet_repl_r2_misc", "UW_SHARE_TT_250", CT, -1,
     "隔夜符号连续 × 250 日被套低（HB1 左腿）。"),
    _pair("CTP14", "PRICE_POSITION_20", "price_location", "UW_SHARE_TT_250", CT, -1,
     "价格位置低 × 250 日被套低。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s57c(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage57b_cgo_true_turnover_b2"
    plan["family_note"] = (
        "第 57b 阶段第二批：6 条 ret20 对照对（主控补遗指令）+ 14 条 TT 原子转右腿。"
        "CGP17 及后续 CGO 配对标注动量代理（corr ret20 见 atom_health.csv）。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s57c

if __name__ == "__main__":
    base.main()
