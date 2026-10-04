#!/usr/bin/env python3
"""Round 156 driver: stage 31 batch 1 — volume_free_path_v1 + RP_* fresh batches.
Health verdict (the finding): LZ 0.929 / SampEn 0.969 vs RP_PERM_ENT_D4 and
Ulcer_1m 0.726 vs DAILY_RANGE_PCT — new constructions yield only 2 independent
facets (ULCER_SHIFT, RECOVERY). Batch = 2 atomic + 16 pairs (programmatic
hash/cap-checked; colliders auto-replaced).
Literature: Lempel-Ziv 1976; Kaspar-Schuster 1987; Richman-Moorman 2000;
Martin-McCann 1989; Magdon-Ismail-Atiya 2004."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_156"

RPF = "replication_volume_free_v1"
VFP = "volume_free_path_v1"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": VFP},
        "right": {"name": name, "source": VFP},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"vfp_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _atom("DA67", "VFP_ULCER_SHIFT_20", "vfp_ulcer_shift",
     "1m 日内溃疡指数的 20 日变化（Martin–McCann 1989 的 1m 路径版；体检 0.333 独立切面）。方向 −1：回撤恶化。", -1),
    _atom("DA68", "VFP_RECOVERY_20", "vfp_recovery",
     "最大回撤恢复时间占比（Magdon-Ismail–Atiya 2004；体检 0.412 独立切面）。方向 −1：恢复久=弱。", -1),
    _pair("CZ93", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", "PRICE_POSITION_20", "price_location",
     "簇 VFP_ULCER_SHIFT_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ94", "VFP_ULCER_SHIFT_20", "volume_free_path_v1", "GAP_FILL_RATE_20", "overnight_structure_1d",
     "簇 VFP_ULCER_SHIFT_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ95", "VFP_RECOVERY_20", "volume_free_path_v1", "RESILIENCY_20", "liquidity_commonality_1m",
     "簇 VFP_RECOVERY_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ96", "VFP_RECOVERY_20", "volume_free_path_v1", "ON_PREM_20", "overnight_structure_1d",
     "簇 VFP_RECOVERY_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ97", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "PRICE_POSITION_20", "price_location",
     "簇 RP_PERM_ENT_D3_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ98", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "GAP_FILL_RATE_20", "overnight_structure_1d",
     "簇 RP_PERM_ENT_D3_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ99", "RP_PERM_ENT_D4_20", "replication_volume_free_v1", "ON_PREM_20", "overnight_structure_1d",
     "簇 RP_PERM_ENT_D4_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ100", "RP_PERM_ENT_D4_20", "replication_volume_free_v1", "WORST_DAY_20", "return_tail_shape",
     "簇 RP_PERM_ENT_D4_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ101", "RP_PERM_ENT_D3_60", "replication_volume_free_v1", "AUC_VARIANCE_RATIO_20", "auction_1m",
     "簇 RP_PERM_ENT_D3_60：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ103", "RP_UW_CHG_20", "replication_volume_free_v1", "GAP_FILL_RATE_20", "overnight_structure_1d",
     "簇 RP_UW_CHG_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ104", "RP_UW_CHG_20", "replication_volume_free_v1", "RESILIENCY_20", "liquidity_commonality_1m",
     "簇 RP_UW_CHG_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ105", "RP_UW_LVL_20", "replication_volume_free_v1", "PRICE_POSITION_20", "price_location",
     "簇 RP_UW_LVL_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ106", "RP_UW_LVL_20", "replication_volume_free_v1", "ON_PREM_20", "overnight_structure_1d",
     "簇 RP_UW_LVL_20：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ107", "RP_UW_CHG_60", "replication_volume_free_v1", "PRICE_POSITION_20", "price_location",
     "簇 RP_UW_CHG_60：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ108", "RP_UW_CHG_60", "replication_volume_free_v1", "VT_BUCKET_GINI_20", "volume_time_1m",
     "簇 RP_UW_CHG_60：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
    _pair("CZ102", "RP_PERM_ENT_D3_60", "replication_volume_free_v1", "TICK_IMBALANCE_20", "bar_size_order_flow",
     "簇 RP_PERM_ENT_D3_60：无成交量通道反向取向（左腿新批/右腿帽内核算）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage31(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage31_volume_free_path"
    plan["family_note"] = (
        "第 31 阶段 volume_free_path_v1 首批：通道结论=新构造独立切面仅 2 个"
        "（LZ 0.929/SAMPEN 0.969 与 RP_PERM_ENT_D4 同信息影子、ULCER_1M 0.726 影子）；"
        "2 新原子 + 16 条 RP_*/VFP 反向与新批配对（程序化哈希/帽位核查）；"
        "出处 Lempel-Ziv 1976 / Kaspar-Schuster 1987 / Richman-Moorman 2000 / "
        "Martin-McCann 1989 / Magdon-Ismail-Atiya 2004"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage31

if __name__ == "__main__":
    base.main()
