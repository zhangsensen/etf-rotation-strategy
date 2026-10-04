#!/usr/bin/env python3
"""Round 193 driver: stage 53 — second-tier H=20 slow signals (CZ68/CP21/
CS11/DB1) -> one mechanism atom each (mechanism_atoms_v3), then pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_193"

MV3 = "mechanism_atoms_v3"


def _atom(cid, name, sign, hyp):
    return {"id": cid, "operator": "atomic",
            "left": {"name": name, "source": MV3},
            "right": {"name": name, "source": MV3},
            "mechanism": f"s53_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


def _pair(cid, left, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": MV3},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s53_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _atom("M3A", "M3_ELAST_LIQSPLIT_20", 1,
     "CZ68 机制原子：流动性改善日（Amihud 20d 改善）的量价弹性 − 恶化日弹性（来源 CZ68=LM_AMIHUD_RATIO×PV_ELASTICITY，H20 4.63）。Amihud 2002。"),
    _atom("M3B", "M3_TAIL_ALIGN_20", 1,
     "CP21 机制原子：尾 20% 量桶动量方向与全日方向一致天数占比 20 日均值（来源 CP21=VT_TAIL_MOM×PV_ELASTICITY，H20 4.43）。Easley–López de Prado–O'Hara 2012。"),
    _atom("M3C", "M3_TAILMOM_USHAPE_SPLIT_20", 1,
     "CS11 机制原子：高 U 形日尾桶动量 − 低 U 形日（20d 滚动中位数分半，来源 CS11=VT_TAIL_MOM×VOL_USHAPE，H20 3.98）。"),
    _atom("M3D", "M3_AC_GINI_SPLIT_20", -1,
     "DB1 机制原子：高到达 Gini 日量钟 AC1 − 低 Gini 日（来源 DB1=VT_BUCKET_GINI 单原子，H20 3.88）。Easley–O'Hara 2012。"),

    _pair("M3P1", "M3_ELAST_LIQSPLIT_20", "RP_UW_CHG_20", "replication_volume_free_v1", 1,
     "弹性改善切面 × 水下改善（QA8 同右腿）。"),
    _pair("M3P2", "M3_ELAST_LIQSPLIT_20", "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi", -1,
     "弹性改善 × MFI 极值低（S27B5 模式）。"),
    _pair("M3P3", "M3_ELAST_LIQSPLIT_20", "ON_PREM_20", "overnight_structure_1d", 1,
     "弹性改善 × 隔夜溢价（Lou–Polk–Skouras 2019）。"),
    _pair("M3P4", "M3_ELAST_LIQSPLIT_20", "PRICE_POSITION_20", "price_location", 1,
     "弹性改善 × 20 日价格位置。"),

    _pair("M3P5", "M3_TAIL_ALIGN_20", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", -1,
     "尾桶对齐 × 量 spike 低（CO36 模式）。"),
    _pair("M3P6", "M3_TAIL_ALIGN_20", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", -1,
     "尾桶对齐 × 排列熵低（PA1 同右腿）。"),
    _pair("M3P7", "M3_TAIL_ALIGN_20", "GAP_FILL_RATE_20", "overnight_structure_1d", 1,
     "尾桶对齐 × 跳空回补。"),
    _pair("M3P8", "M3_TAIL_ALIGN_20", "RESILIENCY_20", "liquidity_commonality_1m", 1,
     "尾桶对齐 × 微结构弹性。"),

    _pair("M3P9", "M3_TAILMOM_USHAPE_SPLIT_20", "LOG_AMOUNT_VOL_20", "liquidity_variability", -1,
     "高 U 形尾桶动量 × 规模小（S32P1 模式）。"),
    _pair("M3P10", "M3_TAILMOM_USHAPE_SPLIT_20", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", 1,
     "高 U 形尾桶动量 × 溃疡改善（DD48 同右腿）。"),
    _pair("M3P11", "M3_TAILMOM_USHAPE_SPLIT_20", "MA_GAP_DD_EAT", "mechanism_atoms_v1", 1,
     "高 U 形尾桶动量 × 跳空未被吃。"),

    _pair("M3P12", "M3_AC_GINI_SPLIT_20", "R_ON_SIGN_STREAK_20", "sonnet_repl_r2_misc", 1,
     "高 Gini AC1 × 隔夜符号连续（HB1 同右腿）。"),
    _pair("M3P13", "M3_AC_GINI_SPLIT_20", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", -1,
     "高 Gini AC1 × 尾盘一致度低（DB1 方向）。"),
    _pair("M3P14", "M3_AC_GINI_SPLIT_20", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", -1,
     "高 Gini AC1 × 量 spike 低。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s53(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage53_tier2_mechanisms"
    plan["family_note"] = (
        "第 53 阶段：H=20 慢信号第 2 梯队（CZ68/CP21/CS11/DB1）各抽 1 个机制原子"
        "（mechanism_atoms_v3，4 原子）+ 定向配对 14 条。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s53

if __name__ == "__main__":
    base.main()
