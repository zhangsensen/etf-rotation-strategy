#!/usr/bin/env python3
"""Round 147 driver: stage 27 batch 1 — replication_volume_free_v1 family.
Independent pi-workspace implementation of two volume-free Sonnet-verified
atoms + literature-defined variants (6 atoms, health max 0.399, no shadows)
+ 12 pairs. 17:00: each RPF atom's left batch = this round (2 pairs, right
legs pairwise different families); right legs used once."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_147"

RPF = "replication_volume_free_v1"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": RPF},
        "right": {"name": name, "source": RPF},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": RPF},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"rpf_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


ID = "impact_decay_1m"
AU = "auction_1m"
SD = "serial_dependence"
CD = "cost_distribution"
DR = "downside_risk"
IVP = "intraday_volume_profile_1m"
RT = "return_tail_shape"
ID2 = "impact_decay_1m"
LS = "liquidity_commonality_1m"
FF = "fund_flow"
LB = "largebar_footprint_1m"
OS = "overnight_structure_1d"

CANDS = [
    _atom("DA41", "RP_PERM_ENT_D3_20", "rpf_perm_d3",
     "1m 收益 Bandt–Pompe 归一化排列熵 d=3，20 日均值（Bandt–Pompe 2002；Sonnet 复现，预登记 −1：熵低=路径结构确定）。体检 0.286。", -1),
    _atom("DA42", "RP_PERM_ENT_D4_20", "rpf_perm_d4",
     "同上嵌入维 d=4 变体（更细序数结构；体检 0.306）。方向 −1。", -1),
    _atom("DA43", "RP_PERM_ENT_D3_60", "rpf_perm_d3_60",
     "d=3 排列熵 60 日窗变体（慢速体制版；体检 0.276）。方向 −1。", -1),
    _atom("DA44", "RP_UW_CHG_20", "rpf_uw_chg",
     "日内水下时间占比的 20 日均值 − 前 20 日均值（Sonnet 复现 UNDERWATER_FRAC_CHG_20，预登记按 Sonnet 方向）。体检 0.306。", 1),
    _atom("DA45", "RP_UW_LVL_20", "rpf_uw_lvl",
     "水下时间占比 20 日水平（Grossman–Zhou 式回撤时间会计；体检 0.399）。方向 −1：水下久=弱。", -1),
    _atom("DA46", "RP_UW_CHG_60", "rpf_uw_chg60",
     "水下占比 60 日窗变化变体（体检 0.266）。方向 1（与 DA44 同向）。", 1),
    _pair("CZ41", "RP_PERM_ENT_D3_20", "PV_ELASTICITY_20", ID,
     "簇 PERM_D3：路径熵 × 量价弹性（CA1 同腿）。"),
    _pair("CZ42", "RP_PERM_ENT_D3_20", "AUC_VARIANCE_RATIO_20", AU,
     "簇 PERM_D3：路径熵 × 波动配置（CM06 同腿）。"),
    _pair("CZ43", "RP_PERM_ENT_D4_20", "SIGN_ACF1_5", SD,
     "簇 PERM_D4：路径熵(d4) × 收益动量。"),
    _pair("CZ44", "RP_PERM_ENT_D4_20", "CHIP_RANGE_90_60", CD,
     "簇 PERM_D4：路径熵(d4) × 筹码集中。"),
    _pair("CZ45", "RP_PERM_ENT_D3_60", "ULCER_20", DR,
     "簇 PERM_D3_60：慢熵 × 健康结构。"),
    _pair("CZ46", "RP_PERM_ENT_D3_60", "OPEN30_VOL_SHARE_20", IVP,
     "簇 PERM_D3_60：慢熵 × 开盘配置（CL09 同腿）。"),
    _pair("CZ47", "RP_UW_CHG_20", "WORST_DAY_20", RT,
     "簇 UW_CHG：水下变化 × 无极端损伤。"),
    _pair("CZ48", "RP_UW_CHG_20", "IMP_PERM_SHARE_20", ID,
     "簇 UW_CHG：水下变化 × 冲击永久份额。"),
    _pair("CZ49", "RP_UW_LVL_20", "RESILIENCY_20", LS,
     "簇 UW_LVL：水下水平 × 微结构弹性（CS01 同腿）。"),
    _pair("CZ50", "RP_UW_LVL_20", "SHARE_RET_CORR_20", FF,
     "簇 UW_LVL：水下水平 × 一级流解释力。"),
    _pair("CZ51", "RP_UW_CHG_60", "LBAR_CLOCK_STD_20", LB,
     "簇 UW_CHG60：水下变化(60) × 体量钟离散（BF1 同腿）。"),
    _pair("CZ52", "RP_UW_CHG_60", "GAP_FILL_RATE_20", OS,
     "簇 UW_CHG60：水下变化(60) × 缺口修复率（CN03 同腿）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage27(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage27_volume_free_replication"
    plan["family_note"] = (
        "第 27 阶段 replication_volume_free_v1 首批：独立实现两条 Sonnet 已验证无成交量原子"
        "（排列熵 d3 + 水下占比变化）及 4 个文献变体（d4/60 日/水平），体检 6/6 干净（max 0.399）"
        " + 12 配对；出处 Bandt-Pompe 2002 / Chekhlov-Uryasev-Zabarankin 2005；未读 Sonnet 代码"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage27

if __name__ == "__main__":
    base.main()
