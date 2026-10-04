#!/usr/bin/env python3
"""Round 196 driver: stage 55 — threshold-free volume tail-shape rewrites of
the VOL_SPIKE leg (volume_tail_shape_1m), incl. the 3 mandated BB1/CO36/Z2
replacements, plus one batch per VTS atom as left leg."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_196"

VTS = "volume_tail_shape_1m"


def _atom(cid, name, sign, hyp):
    return {"id": cid, "operator": "atomic",
            "left": {"name": name, "source": VTS},
            "right": {"name": name, "source": VTS},
            "mechanism": f"s55_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


def _pair(cid, left, lsrc, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": lsrc},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s55_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _atom("VTA", "VTS_Q95_MED_20", 1,
     "量分布 95 分位/中位数：无阈值尖峰度（Clark 1973；Gabaix et al. 2003 幂律尾）。"),
    _atom("VTB", "VTS_HILL_20", 1,
     "Hill 尾指数（上 10% 样本）：尾部重尾程度（Gopikrishnan et al. 2000）。"),
    _atom("VTC", "VTS_LOGCV_20", 1,
     "log 量离散度 std/mean：日内量活动不均匀度。"),
    _atom("VTD", "VTS_MAXSHARE_20", 1,
     "单 bar 量集中度：最大 1m 量占全日比例。"),

    # —— 强制三条：BB1/CO36/Z2 的 spike 腿替换 ——
    _pair("VTR1", "VTS_Q95_MED_20", VTS, "ULCER_20", "downside_risk", 1,
     "BB1 改写：rank(Q95/med) − rank(ULCER)，原 BB1=rank(VOL_SPIKE)−rank(ULCER)+1（aud +36.3/2.46）。"),
    _pair("VTR2", "VT_AUTOCORR_20", "volume_time_1m", "VTS_Q95_MED_20", VTS, -1,
     "CO36 改写：原 CO36=rank(AC)−rank(VOL_SPIKE) dir −1（aud +47.7/3.14），spike 腿换 Q95/med，同向。"),
    _pair("VTR3", "BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "VTS_LOGCV_20", VTS, 1,
     "Z2 改写：原 Z2=rank(DIR_SKEW)−rank(VOL_AUTOCORR) +1（aud +49.2/3.02），量簇集腿换 log 离散度。"),

    # —— VTS 原子左腿批（每原子一批、右腿异族）——
    _pair("VTP1", "VTS_Q95_MED_20", VTS, "RP_UW_CHG_20", "replication_volume_free_v1", -1,
     "尖峰度 × 水下改善（QA8 右腿）。"),
    _pair("VTP2", "VTS_Q95_MED_20", VTS, "RP_PERM_ENT_D3_20", "replication_volume_free_v1", -1,
     "尖峰度 × 排列熵低（PA1 右腿）。"),
    _pair("VTP3", "VTS_Q95_MED_20", VTS, "MA_LUNCH_DIR_BET", "mechanism_atoms_v1", 1,
     "尖峰度 × 午后押对。"),
    _pair("VTP4", "VTS_Q95_MED_20", VTS, "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi", -1,
     "尖峰度 × MFI 极值低。"),
    _pair("VTP5", "VTS_HILL_20", VTS, "LOG_AMOUNT_VOL_20", "liquidity_variability", -1,
     "重尾 × 规模小（S32P1 模式）。"),
    _pair("VTP6", "VTS_HILL_20", VTS, "ON_PREM_20", "overnight_structure_1d", 1,
     "重尾 × 隔夜溢价。"),
    _pair("VTP7", "VTS_HILL_20", VTS, "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", 1,
     "重尾 × 尾盘一致度。"),
    _pair("VTP8", "VTS_LOGCV_20", VTS, "LUNCH_POST_RUN_20", "lunch_break_1m", -1,
     "量离散 × 午后抢跑（CJ16 左腿）。"),
    _pair("VTP9", "VTS_LOGCV_20", VTS, "RESILIENCY_20", "liquidity_commonality_1m", -1,
     "量离散 × 微结构弹性低。"),
    _pair("VTP10", "VTS_LOGCV_20", VTS, "VT_TAIL_MOM_20", "volume_time_1m", 1,
     "量离散 × 尾桶动量。"),
    _pair("VTP11", "VTS_MAXSHARE_20", VTS, "R_GAP_DD_CONSUMPTION_20", "sonnet_repl_r2_gapdd", -1,
     "单 bar 集中 × 跳空被吃（S27B5 左腿）。"),
    _pair("VTP12", "VTS_MAXSHARE_20", VTS, "R_ON_SIGN_STREAK_20", "sonnet_repl_r2_misc", 1,
     "单 bar 集中 × 隔夜符号连续（HB1 右腿）。"),
    _pair("VTP13", "VTS_MAXSHARE_20", VTS, "GAP_FILL_RATE_20", "overnight_structure_1d", -1,
     "单 bar 集中 × 跳空回补低。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s55(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage55_tail_shape_rewrite"
    plan["family_note"] = (
        "第 55 阶段：量 spike 信息的无阈值改写（volume_tail_shape_1m，4 原子）+ "
        "3 条强制 BB1/CO36/Z2 spike 腿替换 + 13 条左腿批配对。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s55

if __name__ == "__main__":
    base.main()
