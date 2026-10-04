#!/usr/bin/env python3
"""Round 208 driver: stage 59 — split-conditioned mechanism atoms (pi-side
parallel to Sonnet S64). 8 single atoms + 8 directed pairs = 16 candidates."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_208"

SCA = "split_conditioned_atoms_pi"
BETA = "sonnet_repl_r_beta"
GAPDD = "sonnet_repl_r2_gapdd"
ULC = "volume_free_path_v1"


def _atomic(name, hyp):
    return {"id": f"SCA_{name.split('_')[1]}_{name.split('_')[2]}_A" if False else name + "_A",
            "operator": "atomic",
            "left": {"name": name, "source": SCA},
            "right": {"name": name, "source": SCA},
            "mechanism": f"s59_{name.lower()}_a",
            "hypothesis": hyp, "expected_sign": 0}


def _pair(cid, left, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": SCA},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s59_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _atomic("SCA_DD_BY_AMT", "最大回撤在高/低成交额日的 20 日组差——机构扫单痕迹（Magdon-Ismail 2004）。"),
    _atomic("SCA_DD_BY_AMH", "最大回撤在 Amihud 冲击高/低日的组差——冲击日回撤几何。"),
    _atomic("SCA_PE_BY_AMT", "排列熵（Bandt-Pompe d=3）在高/低成交额日的组差——有序度状态。"),
    _atomic("SCA_PE_BY_GAP", "排列熵在隔夜跳空正/负日的组差——跳空后的路径有序度。"),
    _atomic("SCA_LPR_BY_AMT", "午后首 10 分钟量占比（CJ16 日值）在高/低成交额日的组差。"),
    _atomic("SCA_ULC_BY_AMH", "溃疡指数（Martin-McCann）在 Amihud 冲击高/低日的组差。"),
    _atomic("SCA_ON_BY_VR", "隔夜收益在 5m 噪声 VR 升/降日的组差——噪声状态下的隔夜行为。"),
    _atomic("SCA_UWF_BY_GAP", "水下时间占比在隔夜跳空正/负日的组差——QA8 几何的跳空条件化。"),

    _pair("SCP1", "SCA_DD_BY_AMT", "R_GAP_DD_CONSUMPTION_20", GAPDD, 1,
     "成交额条件化回撤 × 跳空被吃低——回撤几何双切面。"),
    _pair("SCP2", "SCA_DD_BY_AMH", "VFP_ULCER_SHIFT_20", ULC, 1,
     "冲击日回撤 × 溃疡变化——DD48 簇的条件化切面。"),
    _pair("SCP3", "SCA_PE_BY_AMT", "R_CONTINUOUS_BETA_60", BETA, -1,
     "成交额条件化排列熵（低=有序→正，PA1 先验 −1）× 连续日 beta。"),
    _pair("SCP4", "SCA_PE_BY_GAP", "R_CONTINUOUS_BETA_60", BETA, -1,
     "跳空条件化排列熵（−1 先验）× 连续日 beta。"),
    _pair("SCP5", "SCA_LPR_BY_AMT", "R_GAP_DD_CONSUMPTION_20", GAPDD, 1,
     "成交额条件化午后抢跑 × 跳空被吃低。"),
    _pair("SCP6", "SCA_ULC_BY_AMH", "VFP_ULCER_SHIFT_20", ULC, 1,
     "冲击日溃疡 × 溃疡变化。"),
    _pair("SCP7", "SCA_ON_BY_VR", "R_CONTINUOUS_BETA_60", BETA, 1,
     "噪声状态隔夜收益 × 连续日 beta。"),
    _pair("SCP8", "SCA_UWF_BY_GAP", "VFP_ULCER_SHIFT_20", ULC, 1,
     "跳空条件化水下占比 × 溃疡变化。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s59(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage59_split_conditioned_atoms_pi"
    plan["family_note"] = (
        "第 59 阶段：split 条件化机制原子（与 Sonnet S64 平行独立实现）。8 统计量×条件原子 + "
        "8 定向配对（右腿 BETA/GAP_DD/ULCER 各 ≤3 配对纪律）；组内 ≥3 日（58b 教训）；"
        "条件全部 20 日中位二分（shift(1) PIT 安全）。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s59

if __name__ == "__main__":
    base.main()
