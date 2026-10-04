#!/usr/bin/env python3
"""Round 181 driver: stage 44 — mechanism atoms from the H=20 slow-signal
list head (goal: survive the current H=5 gates). Health: EDGE 0.587 ok,
splits ok (low coverage), PREUP_PERM_ENT SHADOW 0.964 vs RP_PERM_ENT_D3_20
-> dropped per contract. 3 singles + 9 pairs = 12 (floor)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_181"

MA = "mechanism_atoms_v2"


def _atom(cid, name, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": MA},
        "right": {"name": name, "source": MA},
        "mechanism": "mech_atom_v2", "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": MA},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"s44_{{cid.lower()}}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _atom("TE01", "MA2_EDGE_TIME_BIAS_20",
     "大 bar（额>日中位×5）成交量首尾 30 分钟占比 − 中段：时点偏置直接写法（BIGBAR_EDGE_CONC 机制化；Bouchaud metaorder）。", 1),
    _atom("TE02", "MA2_CHIP_BIGBAR_SPLIT_20",
     "筹码区间宽日 vs 窄日的大 bar 量占比之差（C3 机制化；时间序列分半）。", -1),
    _atom("TE03", "MA2_BB_RES_SPLIT_20",
     "高/低微结构弹性日的大 bar 量占比之差（AI1 机制化；时间序列分半）。", 1),
    _pair("TE04", "MA2_EDGE_TIME_BIAS_20", "PD_D1_CHG_20", "price_delay",
     "簇 EDGE_BIAS：时点偏置 × 延迟改善。"),
    _pair("TE05", "MA2_EDGE_TIME_BIAS_20", "SCL_DFA_RET_20", "scaling_memory_1m",
     "簇 EDGE_BIAS：时点偏置 × 路径趋势。"),
    _pair("TE06", "MA2_EDGE_TIME_BIAS_20", "ON_PREM_20", "overnight_structure_1d",
     "簇 EDGE_BIAS：时点偏置 × 隔夜溢价。"),
    _pair("TE07", "MA2_CHIP_BIGBAR_SPLIT_20", "AUC_VARIANCE_RATIO_20", "auction_1m",
     "簇 CHIP_SPLIT：筹码分裂 × 开盘方差比。"),
    _pair("TE08", "MA2_CHIP_BIGBAR_SPLIT_20", "PRICE_POSITION_20", "price_location",
     "簇 CHIP_SPLIT：筹码分裂 × 价格位置。"),
    _pair("TE09", "MA2_CHIP_BIGBAR_SPLIT_20", "VFP_RECOVERY_20", "volume_free_path_v1",
     "簇 CHIP_SPLIT：筹码分裂 × 回撤恢复。"),
    _pair("TE10", "MA2_BB_RES_SPLIT_20", "GAP_FILL_RATE_20", "overnight_structure_1d",
     "簇 BB_RES：弹性分裂 × 跳空回补。"),
    _pair("TE11", "MA2_BB_RES_SPLIT_20", "TICK_IMBALANCE_20", "bar_size_order_flow",
     "簇 BB_RES：弹性分裂 × 主买不平衡。"),
    _pair("TE12", "MA2_BB_RES_SPLIT_20", "CHIP_RANGE_90_60", "cost_distribution",
     "簇 BB_RES：弹性分裂 × 筹码区间。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s44(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage44_h20_mechanism_atoms"
    plan["family_note"] = (
        "第 44 阶段 mechanism_atoms_v2（H20 慢信号头部机制化，目标：现行 H5 门站住）。"
        "体检：EDGE 0.587 ok、splits 0.18/0.23 ok；MA2_PREUP_PERM_ENT 影子 0.964 vs "
        "RP_PERM_ENT_D3_20（同信号）——按纪律剔除不预注册。3 单原子 + 9 配对 = 12。"
        "MA2_CHG/BB_RES 分裂型覆盖率 0.14–0.17，门 1 风险已知。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s44

if __name__ == "__main__":
    base.main()
