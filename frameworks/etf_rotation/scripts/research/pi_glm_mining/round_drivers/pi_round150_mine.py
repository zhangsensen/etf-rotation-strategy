#!/usr/bin/env python3
"""Round 150 driver: stage 29 batch 1 — price_delay family.
5 clean atoms (PD_D1_1M_20 shadowed 0.712 vs SYNC_BETA_20 - intraday delay IS
sync beta) + 10 pairs. Literature: Hou-Moskowitz 2005; Mech 1993;
Brennan-Jegadeesh-Swaminathan 1993; Boehmer-Wu 2013.
17:00: each PD atom's left batch = this round (2 pairs, right legs pairwise
different families); right legs used once."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_150"

PD = "price_delay"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": PD},
        "right": {"name": name, "source": PD},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": PD},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"pd_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


ID = "impact_decay_1m"
LS = "liquidity_commonality_1m"
DR = "downside_risk"
BF = "bar_size_order_flow"
SD = "serial_dependence"
AU = "auction_1m"
OS = "overnight_structure_1d"
CD = "cost_distribution"
BF2 = "bar_size_order_flow"
ID2 = "impact_decay_1m"

CANDS = [
    _atom("DA47", "PD_D1_D_20", "pd_d1_daily",
     "日频价格延迟 D1（Hou–Moskowitz 2005：篮子滞后信息吸收不足；体检 −0.553 vs INTRADAY_PEER_R2）。方向 −1：高延迟=信息摩擦大。", -1),
    _atom("DA48", "PD_D2_D_20", "pd_d2_daily",
     "延迟 D2 = 滞后系数占比（体检 −0.541）。方向 −1 同上。", -1),
    _atom("DA49", "PD_D1_CHG_20", "pd_d1_chg",
     "1m D1 的 20 日变化（吸收速度恶化；体检 −0.292）。方向 −1。", -1),
    _atom("DA50", "PD_DIFF_20", "pd_diff",
     "日频 D1 − 1m D1（长短期吸收速度分歧；体检 0.229）。方向 −1：分歧大=慢周期摩擦。", -1),
    _atom("DA51", "PD_LAG_SIGN_20", "pd_lag_sign",
     "滞后系数和符号（正反馈 vs 反转；体检 0.40 vs PEER_LEAD_NETWORK）。方向 −1：正号=过度反应后回转。", -1),
    _pair("DA52", "PD_D1_D_20", "PV_ELASTICITY_20", ID,
     "簇 PD_D1：延迟 × 量价弹性（CA1 同腿）。"),
    _pair("DA53", "PD_D1_D_20", "RESILIENCY_20", LS,
     "簇 PD_D1：延迟 × 微结构弹性。"),
    _pair("DA54", "PD_D2_D_20", "ULCER_20", DR,
     "簇 PD_D2：延迟 × 健康结构。"),
    _pair("DA55", "PD_D2_D_20", "TICK_IMBALANCE_20", BF,
     "簇 PD_D2：延迟 × 主买不平衡。"),
    _pair("DA56", "PD_D1_CHG_20", "SIGN_ACF1_5", SD,
     "簇 D1_CHG：吸收恶化 × 收益动量。"),
    _pair("DA57", "PD_D1_CHG_20", "AUC_VARIANCE_RATIO_20", AU,
     "簇 D1_CHG：吸收恶化 × 波动配置（CM06 同腿）。"),
    _pair("DA58", "PD_DIFF_20", "ON_PREM_20", OS,
     "簇 DIFF：吸收分歧 × 隔夜溢价（CZ01 同腿）。"),
    _pair("DA59", "PD_DIFF_20", "CHIP_RANGE_90_60", CD,
     "簇 DIFF：吸收分歧 × 筹码集中。"),
    _pair("DA60", "PD_LAG_SIGN_20", "CLOSE5_DAY_CONSIST_20", BF2,
     "簇 LAG_SIGN：滞后符号 × 收盘确认（CK04 同腿）。"),
    _pair("DA61", "PD_LAG_SIGN_20", "IMP_PERM_SHARE_20", ID2,
     "簇 LAG_SIGN：滞后符号 × 冲击永久份额（CY52 同腿）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage29(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage29_price_delay"
    plan["family_note"] = (
        "第 29 阶段 price_delay 首批：5 干净原子（PD_D1_1M 影子 0.712 vs SYNC_BETA_20——"
        "1m 延迟即同步 beta）+ 10 配对；出处 Hou-Moskowitz 2005 / Mech 1993 / "
        "Brennan-Jegadeesh-Swaminathan 1993 / Boehmer-Wu 2013"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage29

if __name__ == "__main__":
    base.main()
