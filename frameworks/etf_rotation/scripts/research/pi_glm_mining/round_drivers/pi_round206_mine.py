#!/usr/bin/env python3
"""Round 206 driver: stage 58 — replicate Sonnet S60 four entries (master-
defined, new family repl_sonnet_s60, R_ prefix; n_preregistered=4 replication
exemption)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_206"

S60 = "repl_sonnet_s60"
S60G = "repl_sonnet_s60_gapdd"


def _pair(cid, left, lsrc, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": lsrc},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s58_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    {"id": "NCA1", "operator": "atomic",
     "left": {"name": "R_TURNVOL_ENTROPY_SPLIT_20", "source": S60},
     "right": {"name": "R_TURNVOL_ENTROPY_SPLIT_20", "source": S60},
     "mechanism": "s58_nca1",
     "hypothesis": "换手率高日与低日的日内量分布熵之差（高换手日更有序 → 信息驱动）；expected_sign=0 方向由发现期定。Sonnet 目标 disc t 2.45 / aud +15.1。",
     "expected_sign": 0},
    _pair("NCA2", "R_VOLSPIKE_NOISECHG_SPLIT_20", S60, "R_CONTINUOUS_BETA_60", "sonnet_repl_r_beta", 1,
     "噪声上升日量 spike 更少 × 连续日 beta 高。Sonnet 目标 disc t 3.25 / aud +19.3。"),
    _pair("NCA3", "R_TURNVOL_ENTROPY_SPLIT_20", S60, "R_GAP_DD_CONSUMPTION_RATIO_20", S60G, 1,
     "换手分组熵差 × 跳空被回撤吞没比例低（两腿同族 repl_sonnet_s60——主控第 58 阶段指令逐字，不改腿）。Sonnet 目标 disc t 2.85 / aud +27.2。"),
    _pair("NCA4", "R_LIQSHOCK_MFI_SPLIT_20", S60, "R_CONTINUOUS_BETA_60", "sonnet_repl_r_beta", 1,
     "Amihud 冲击日 MFI 更低 × 连续日 beta 高。Sonnet 目标 disc t 2.37 / aud +10.1。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s58(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage58_repl_sonnet_s60"
    plan["family_note"] = (
        "第 58 阶段：复现 Sonnet S60 四条（repl_sonnet_s60 家族，R_ 前缀，n=4 复现例外）。"
        "NCA3 两腿同族系主控指令逐字（不改腿），偏离配对纪律已在 REPORT 披露。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s58

if __name__ == "__main__":
    base.main()
