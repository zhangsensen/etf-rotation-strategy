#!/usr/bin/env python3
"""Round 169 driver: stage 36 — volume-free-level atom cross-pairing scan
(pi side, parallel to Sonnet S18). 17-atom pool, 88 legal unpaired
cross-family combos, top-18 by summed single-atom audit t. Pairing
discipline enforced: left batch <=8 rights, rights <=3 uses, pairwise
different families per left batch."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_169"


def _pair(cid, left, lsrc, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": lsrc},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"s36_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _pair("DD00", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "PD_D1_CHG_20", "price_delay",
     "簇 RP：无量水平对，两腿单原子 t 和排序第 1。"),
    _pair("DD01", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "VFP_RECOVERY_20", "volume_free_path_v1",
     "簇 RP：无量水平对，两腿单原子 t 和排序第 2。"),
    _pair("DD02", "PD_D1_CHG_20", "price_delay", "VFP_RECOVERY_20", "volume_free_path_v1",
     "簇 PD：无量水平对，两腿单原子 t 和排序第 3。"),
    _pair("DD03", "PD_D1_CHG_20", "price_delay", "RP_UW_LVL_20", "replication_volume_free_v1",
     "簇 PD：无量水平对，两腿单原子 t 和排序第 4。"),
    _pair("DD04", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "RCC_BB_SQUEEZE_20", "range_contraction_cycle",
     "簇 RP：无量水平对，两腿单原子 t 和排序第 5。"),
    _pair("DD05", "PD_D1_CHG_20", "price_delay", "ON_PREM_20", "overnight_structure_1d",
     "簇 PD：无量水平对，两腿单原子 t 和排序第 6。"),
    _pair("DD06", "AUC_VARIANCE_RATIO_20", "auction_1m", "VFP_RECOVERY_20", "volume_free_path_v1",
     "簇 AUC：无量水平对，两腿单原子 t 和排序第 7。"),
    _pair("DD07", "PD_D1_CHG_20", "price_delay", "RCC_BB_SQUEEZE_20", "range_contraction_cycle",
     "簇 PD：无量水平对，两腿单原子 t 和排序第 8。"),
    _pair("DD08", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d",
     "簇 RP：无量水平对，两腿单原子 t 和排序第 9。"),
    _pair("DD09", "VFP_RECOVERY_20", "volume_free_path_v1", "RP_UW_LVL_20", "replication_volume_free_v1",
     "簇 VFP：无量水平对，两腿单原子 t 和排序第 10。"),
    _pair("DD10", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "SCL_DFA_RET_20", "scaling_memory_1m",
     "簇 RP：无量水平对，两腿单原子 t 和排序第 11。"),
    _pair("DD11", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "RESILIENCY_20", "liquidity_commonality_1m",
     "簇 RP：无量水平对，两腿单原子 t 和排序第 12。"),
    _pair("DD12", "PD_D1_CHG_20", "price_delay", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d",
     "簇 PD：无量水平对，两腿单原子 t 和排序第 13。"),
    _pair("DD13", "AUC_VARIANCE_RATIO_20", "auction_1m", "RP_UW_CHG_20", "replication_volume_free_v1",
     "簇 AUC：无量水平对，两腿单原子 t 和排序第 14。"),
    _pair("DD14", "VFP_RECOVERY_20", "volume_free_path_v1", "RCC_BB_SQUEEZE_20", "range_contraction_cycle",
     "簇 VFP：无量水平对，两腿单原子 t 和排序第 15。"),
    _pair("DD15", "PD_D1_CHG_20", "price_delay", "SCL_DFA_RET_20", "scaling_memory_1m",
     "簇 PD：无量水平对，两腿单原子 t 和排序第 16。"),
    _pair("DD16", "AUC_VARIANCE_RATIO_20", "auction_1m", "LHA_NEAR_LOW_20", "long_horizon_anchors_1d",
     "簇 AUC：无量水平对，两腿单原子 t 和排序第 17。"),
    _pair("DD17", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", "LUNCH_PRE_RUN_20", "lunch_break_1m",
     "簇 RP：无量水平对，两腿单原子 t 和排序第 18。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s36(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage36_volume_free_crosspair"
    plan["family_note"] = (
        "第 36 阶段（与 Sonnet S18 平行）：17 原子无量水平池，88 个合法未配跨族组合，"
        "按两腿单原子审计 t 之和取 top18。左腿批量合规（RP_PERM_ENT 7 / PD_D1_CHG 6 / "
        "AUC 3 / VFP_RECOVERY 2）；右腿用量 VFP_RECOVERY、RCC_BB_SQUEEZE、LHA_NEAR_LOW 顶格 3。"
        "REPORT 单列无量通道结论。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s36

if __name__ == "__main__":
    base.main()
