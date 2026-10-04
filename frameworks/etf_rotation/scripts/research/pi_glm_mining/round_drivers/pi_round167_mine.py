#!/usr/bin/env python3
"""Round 167 driver: stage 35 — second Sonnet replication batch ("only this
round").
Health: SR2_UW_Z_60 clean (max 0.477); SR2_CAT_DISP_20 SHADOW 0.992 vs
existing CATEGORY_DISPERSION_20 (category_state) -> per directive reuse the
existing atom for FC3 and do NOT preregister the shadow twin.
Batch: 2 replications + 10 confirmed-leg pairs with SR2_UW_Z_60 (5 as left
+3 as right within the <=3 cap; total 12 = floor)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_167"

S2 = "sonnet_repl_v2"


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"s35_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


OS = "overnight_structure_1d"
RM = "realized_measures_1m"
DR = "downside_risk"
VF = "volume_free_path_v1"
PL = "price_location"
ID = "impact_decay_1m"
BF = "bar_size_order_flow"
LC = "liquidity_commonality_1m"
SM = "scaling_memory_1m"
RP = "replication_volume_free_v1"
CS = "category_state"

CANDS = [
    # === 2 replication pairs (Sonnet verified, as-is) ===
    _pair("DC01", "SR2_UW_Z_60", S2, "CATEGORY_DISPERSION_20", CS,
     "FC3 复现：水下 z 高 × 类内离散高（Sonnet +37.6bp/t2.31）；CATEGORY_DISPERSION_20 复用 pi 现存原子（新算同义原子与之 corr 0.992 影子，按指令注明复用）。"),
    _pair("DC02", "SR2_UW_Z_60", S2, "RP_PERM_ENT_D3_20", RP,
     "FC8 复现：水下 z 高 × 排列熵低（Sonnet +33.0bp/t2.17）。"),
    # === SR2_UW_Z_60 as left (one batch, 8 rights pairwise diff families) ===
    _pair("DC03", "SR2_UW_Z_60", S2, "ON_PREM_20", OS,
     "簇 UW_Z：水下 z × 隔夜溢价。"),
    _pair("DC04", "SR2_UW_Z_60", S2, "VOL_USHAPE_20", RM,
     "簇 UW_Z：水下 z × 量 U 型弱。"),
    _pair("DC05", "SR2_UW_Z_60", S2, "ULCER_20", DR,
     "簇 UW_Z：水下 z × 溃疡低。"),
    _pair("DC06", "SR2_UW_Z_60", S2, "VFP_RECOVERY_20", VF,
     "簇 UW_Z：水下 z × 回撤恢复快。"),
    _pair("DC07", "SR2_UW_Z_60", S2, "PRICE_POSITION_20", PL,
     "簇 UW_Z：水下 z × 价格位置高。"),
    _pair("DC08", "SR2_UW_Z_60", S2, "TICK_IMBALANCE_20", BF,
     "簇 UW_Z：水下 z × 主买不平衡。"),
    _pair("DC09", "SR2_UW_Z_60", S2, "SCL_DFA_RET_20", SM,
     "簇 UW_Z：水下 z × 路径趋势度。"),
    _pair("DC10", "SR2_UW_Z_60", S2, "RESILIENCY_20", LC,
     "簇 UW_Z：水下 z × 微结构弹性。"),
    # === SR2_UW_Z_60 as right (2 of 3 slots) ===
    _pair("DC11", "PV_ELASTICITY_20", ID, "SR2_UW_Z_60", S2,
     "簇 PV_ELASTICITY：量价弹性 × 水下 z（CA1 同腿）。"),
    _pair("DC12", "PD_D1_CHG_20", "price_delay", "SR2_UW_Z_60", S2,
     "簇 PD_D1_CHG：延迟改善 × 水下 z（DA57 同腿）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s35(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage35_sonnet_replication_2"
    plan["family_note"] = (
        "第 35 阶段 sonnet_repl_v2（只此一轮）：SR2_UW_Z_60 体检清洁（max 0.477）；"
        "SR2_CAT_DISP_20 与现存 CATEGORY_DISPERSION_20（category_state）corr 0.992 影子——"
        "按指令 FC3 复用现存原子并注明，影子孪生不预注册。2 复现 + 10 确认腿对（UW_Z 左批 8 权利"
        "两两不同族 + 右腿 2/3 槽）= 12。复现完即穷尽。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s35

if __name__ == "__main__":
    base.main()
