#!/usr/bin/env python3
"""Round 162 driver: stage 33 — cross-line replication of Sonnet two-window
significant pairs (6 replications) + 6 confirmed-leg pairs for the 2 clean
new atoms (SR_BEST_DAY_XVOL, SR_MAX5_MEAN; CONT_BETA/NOISE_VAR/MFI_EXTREME
shadowed vs pi atoms but replicated as mandated).
Literature: Bali-Cakici-Whitelaw 2011; Bollerslev-Li-Todorov 2016;
Bandi-Russell 2008; Quong-Soudack 1989."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_162"

SR = "sonnet_repl_v1"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": SR},
        "right": {"name": name, "source": SR},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"repl_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


ID = "impact_decay_1m"
LS = "liquidity_commonality_1m"
OS = "overnight_structure_1d"
DR = "downside_risk"
BF = "bar_size_order_flow"
CD = "cost_distribution"
IVP = "intraday_volume_profile_1m"
SD = "serial_dependence"
MS = "microstructure_1m"
RM = "realized_measures_1m"

CANDS = [
    # === 6 replication pairs (Sonnet verified, reproduced as-is) ===
    _pair("VA3R", "SR_BEST_DAY_XVOL_60", SR, "VOL_SPIKE_FREQ_20", IVP,
     "VA3 复现：MAX(60)/vol × 事件密集（Sonnet +34.3bp/t2.24）。"),
    _pair("KR1R", "SR_CONT_BETA_60", SR, "SIGN_ACF1_5", SD,
     "KR1 复现：连续 beta × 收益动量（Sonnet RET_ACF1_5≈pi SIGN_ACF1_5 最近似；+43.1bp/t2.12）。"),
    _pair("KU2R", "SR_CONT_BETA_60", SR, "ROLL_SPREAD_20", MS,
     "KU2 复现：连续 beta × Roll 价差（Sonnet +31.3bp/t2.15）。"),
    # KQ4 不可复现：cross_family_only 拒绝同族对（SR_CONT_BETA × SR_MAX5 同族）
    _pair("CZ151", "SR_CONT_BETA_60", SR, "VOL_SPIKE_FREQ_20", IVP,
     "簇 CONT_BETA：连续 beta × 事件密集（替代 KQ4 的同族约束绕行尝试）。"),
    _pair("MH3R", "SR_NOISE_VAR_20", SR, "ROLL_SPREAD_20", MS,
     "MH3 复现：噪声方差 × Roll 价差（Sonnet +39.5bp/t2.48）。"),
    _pair("NI1R", "SR_MFI_EXTREME_20", SR, "VOL_USHAPE_20", RM,
     "NI1 复现：MFI 极端占比 × U 型量（Sonnet +43.6bp/t2.12）。"),
    # === 6 confirmed-leg pairs for the 2 clean atoms ===
    _pair("CZ145", "SR_BEST_DAY_XVOL_60", SR, "PV_ELASTICITY_20", ID,
     "簇 BEST_DAY：MAX/vol × 量价弹性（CA1 同腿）。"),
    _pair("CZ146", "SR_BEST_DAY_XVOL_60", SR, "RESILIENCY_20", LS,
     "簇 BEST_DAY：MAX/vol × 微结构弹性。"),
    _pair("CZ147", "SR_BEST_DAY_XVOL_60", SR, "ON_PREM_20", OS,
     "簇 BEST_DAY：MAX/vol × 隔夜溢价（CZ01 同腿）。"),
    _pair("CZ148", "SR_MAX5_MEAN_20", SR, "ULCER_20", DR,
     "簇 MAX5：MAX5 × 健康结构。"),
    _pair("CZ149", "SR_MAX5_MEAN_20", SR, "TICK_IMBALANCE_20", BF,
     "簇 MAX5：MAX5 × 主买不平衡。"),
    _pair("CZ150", "SR_MAX5_MEAN_20", SR, "CHIP_RANGE_90_60", CD,
     "簇 MAX5：MAX5 × 筹码集中。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage33(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage33_sonnet_replication"
    plan["family_note"] = (
        "第 33 阶段 sonnet_repl_v1：独立实现 5 原子（BEST_DAY_XVOL/CONT_BETA/MAX5/NOISE_VAR/MFI_EXTREME）；"
        "体检 2 干净（BEST_DAY 0.683、MAX5 0.662）+ 3 影子（CONT_BETA 0.864 vs SYNC_BETA、"
        "NOISE_VAR 0.829 vs ROLL_SPREAD、MFI 0.764 vs JV_RV_SHARE）——影子对按复现指令原样预注册；"
        "6 复现对 + 6 确认腿对 = 12；KQ4 为同族对（复现例外）；全部复现完即穷尽"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage33

if __name__ == "__main__":
    base.main()
