#!/usr/bin/env python3
"""Round 213 driver: stage 63 — replicate Sonnet S67 sole entry (vol-spike x
max-DD split) + S68 window sensitivity (w20/40/60) + single-leg decomposition.
The w20 window-check candidate is hash-identical to r210 NS64A (cited, not
re-preregistered). n_preregistered=5 (replication exemption)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_213"

S64 = "repl_sonnet_s64_split"
PE = "replication_volume_free_v1"
UW = "replication_volume_free_v1"


def _pair(cid, left, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": S64},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s63_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _pair("NS67A", "R_VOLSPIKE_MAXDD_SPLIT_20", "RP_PERM_ENT_D3_20", PE, 1,
     "S67 复现：量 spike 在大回撤日 vs 小回撤日的组差 × 排列熵。Sonnet 目标 disc t 2.67 / aud +22.5 (t1.37)。"),
    _pair("NS68W40", "R_PERMENT_TURNOVER_SPLIT_40", "RP_UW_CHG_20", UW, 1,
     "S68 窗口敏感性 w40（Sonnet 审计 t 1.04）：PERMENT×成交额 split 窗 40 − UW_CHG。"),
    _pair("NS68W60", "R_PERMENT_TURNOVER_SPLIT_60", "RP_UW_CHG_20", UW, 1,
     "S68 窗口敏感性 w60（Sonnet 审计 t 1.12）：窗 60 − UW_CHG。"),
    _pair("NS68HI", "R_PERMENT_TURNOVER_HI_20", "RP_UW_CHG_20", UW, 1,
     "S68 单腿分解（高成交额侧）：split = HI − LO，S68 报两侧 t 全负、差为正——验证增量来自差而非单侧。"),
    _pair("NS68LO", "R_PERMENT_TURNOVER_LO_20", "RP_UW_CHG_20", UW, 1,
     "S68 单腿分解（低成交额侧）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s63(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage63_repl_sonnet_s67_s68"
    plan["family_note"] = (
        "第 63 阶段：复现 Sonnet S67 唯一入选（R_VOLSPIKE_MAXDD_SPLIT_20 新原子）+ S68 窗口敏感性"
        "（w20 引用 r210 NS64A——表达式同哈希；w40/w60 新预注册）+ 单腿分解（HI/LO 各配 UW_CHG）。"
        "n=5 复现例外 + 1 引用。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s63

if __name__ == "__main__":
    base.main()
