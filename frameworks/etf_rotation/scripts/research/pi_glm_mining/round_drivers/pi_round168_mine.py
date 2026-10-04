#!/usr/bin/env python3
"""Round 168 driver: stage 35b — replicate Sonnet KR1/KU2/KQ4 with atoms
built strictly per directive definitions (new family file, R_ prefix,
two sources: sonnet_repl_r_beta / sonnet_repl_r_tail so beta-vs-tail pairs
are cross-family). Prescribed batch: 3 replication pairs + 1 single."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_168"

RB = "sonnet_repl_r_beta"
RT = "sonnet_repl_r_tail"


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": RB},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"repl_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


def _atom(cid, name, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": RB},
        "right": {"name": name, "source": RB},
        "mechanism": "repl_cont_beta", "hypothesis": hyp, "expected_sign": sign,
    }


CANDS = [
    _pair("R_KR1", "R_CONTINUOUS_BETA_60", "R_RET_ACF1_5", RT,
     "KR1 复现：连续 beta × 日收益 5 日窗 1 阶自相关（Sonnet +43.1bp/t2.12）。"),
    _pair("R_KU2", "R_CONTINUOUS_BETA_60", "R_KYLE_LAMBDA_20", RT,
     "KU2 复现：连续 beta × Kyle lambda（Sonnet +31.3bp/t2.15）。"),
    _pair("R_KQ4", "R_CONTINUOUS_BETA_60", "R_MAX5_MEAN_20", RT,
     "KQ4 复现：连续 beta × MAX5（Sonnet +44.2bp/t2.29）。"),
    _atom("R_CB60", "R_CONTINUOUS_BETA_60",
          "CONTINUOUS_BETA_60 单原子复现（Sonnet +13.6bp/t0.43）。", 1),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s35b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage35b_sonnet_kr_ku_kq"
    plan["family_note"] = (
        "第 35b 阶段（只此一轮，主控 03:01 指令）：按原定义新建 sonnet_repl_r（R_ 前缀，双 source："
        "sonnet_repl_r_beta=连续 beta、sonnet_repl_r_tail=ACF1_5/KYLE_LAMBDA/MAX5），beta×尾部为跨族。"
        "小样本试算 2 只 6s，全量 ~30s。4 条 = 主控处方（复现纪律覆盖批量下限）。"
        "复现完即写 MECHANISM_EXHAUSTED。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s35b

if __name__ == "__main__":
    base.main()
