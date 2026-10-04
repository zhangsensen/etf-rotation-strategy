#!/usr/bin/env python3
"""Round 207 driver: stage 58b — redo stage-58 replication after coverage fix.
Same four candidates, atoms rebuilt per 58b spec (amount-median split, group
min 3 days, Amihud without fund_share), names versioned _V2 (global expression
dedup, _TT precedent from 57->57b). n_preregistered=4 replication exemption."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_207"

S60 = "repl_sonnet_s60"
S60G = "repl_sonnet_s60_gapdd"


def _pair(cid, left, lsrc, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": lsrc},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s58b_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    {"id": "NCA1B", "operator": "atomic",
     "left": {"name": "R_TURNVOL_ENTROPY_SPLIT_20_V2", "source": S60},
     "right": {"name": "R_TURNVOL_ENTROPY_SPLIT_20_V2", "source": S60},
     "mechanism": "s58b_nca1b",
     "hypothesis": "58b 修复重实现：成交额分组（当日 vs 前 20 日中位）的日内量熵差，组内 ≥3 日。Sonnet 目标 disc t 2.45 / aud +15.1。",
     "expected_sign": 0},
    _pair("NCA2B", "R_VOLSPIKE_NOISECHG_SPLIT_20_V2", S60, "R_CONTINUOUS_BETA_60", "sonnet_repl_r_beta", 1,
     "同 58 原定义（VR5 噪声 20 日变化符号分组，组内 ≥3 日）。Sonnet 目标 disc t 3.25 / aud +19.3。"),
    _pair("NCA3B", "R_TURNVOL_ENTROPY_SPLIT_20_V2", S60, "R_GAP_DD_CONSUMPTION_RATIO_20_V2", S60G, 1,
     "同 58 主控逐字配对（family 拆分满足引擎 cross_family_only）。Sonnet 目标 disc t 2.85 / aud +27.2（r206 审计已复现 +26.3）。"),
    _pair("NCA4B", "R_LIQSHOCK_MFI_SPLIT_20_V2", S60, "R_CONTINUOUS_BETA_60", "sonnet_repl_r_beta", 1,
     "Amihud 改 1d 直算（去 fund_share 依赖，覆盖 191→2379 发现日）。Sonnet 目标 disc t 2.37 / aud +10.1。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s58b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage58b_repl_sonnet_s60_v2"
    plan["family_note"] = (
        "第 58b 阶段：58 阶段复现因原子覆盖不足失效（0–331 vs Sonnet 544–579 有效日），"
        "按 58b 指令修复（成交额中位分组、组内 ≥3 日、Amihud 去 fund_share、缺 1m 日置 NaN）；"
        "原子名加 _V2 后缀满足全局表达式去重（57→57b _TT 先例）。发现窗覆盖 1272–2392 日 ≥540。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s58b

if __name__ == "__main__":
    base.main()
