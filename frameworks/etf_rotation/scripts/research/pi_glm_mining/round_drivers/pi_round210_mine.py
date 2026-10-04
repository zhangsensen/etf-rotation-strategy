#!/usr/bin/env python3
"""Round 210 driver: stage 61 — replicate Sonnet S64 three strongest
split-conditioned entries (new family repl_sonnet_s64_split; n=4 replication
exemption)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_210"

S64 = "repl_sonnet_s64_split"
UW = "replication_volume_free_v1"
BETA = "sonnet_repl_r_beta"
GAPDD = "sonnet_repl_r2_gapdd"


def _pair(cid, left, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": S64},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s61_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _pair("NS64A", "R_PERMENT_TURNOVER_SPLIT_20", "RP_UW_CHG_20", UW, -1,
     "5m 排列熵×成交额 split − 水下占比变化（熵低→正，PA1 先验 −1）。Sonnet 目标 disc t 2.97 / aud +49.7 (t2.45)。"),
    _pair("NS64B", "R_PERMENT_TURNOVER_SPLIT_20", "R_CONTINUOUS_BETA_60", BETA, -1,
     "5m 排列熵 split − 连续日 beta。Sonnet 目标 disc t 4.15 / aud +35.4。"),
    _pair("NS64C", "R_LUNCHPR_ONGAP_SPLIT_20", "R_GAP_DD_CONSUMPTION_20", GAPDD, 1,
     "午间前段量×跳空符号 split − 跳空被吃低。Sonnet 目标 disc t 3.68 / aud +26.4。"),
    _pair("NS64D", "R_ULCER_NOISERATIO_SPLIT_20", "RP_PERM_ENT_D3_20", UW, 1,
     "ULCER×噪声VR方向 split − 排列熵。Sonnet 目标 disc t 3.98 / aud +21.4。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s61(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage61_repl_sonnet_s64_split"
    plan["family_note"] = (
        "第 61 阶段：复现 Sonnet S64 三条最强 split 入选（repl_sonnet_s64_split，n=4 复现例外）。"
        "split = 20 日窗内条件成立/不成立两组均值差，组内 ≥3 日（58b 教训）；"
        "歧义处理：R_LUNCHPR 的 X 按字面取 pi 现有 LUNCH_PRE_RUN 日值（午前 11:20–11:30 量占比，"
        "主控文写'CJ16 所用'但 CJ16 实为 LUNCH_POST_RUN——已在 REPORT 标注）。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s61

if __name__ == "__main__":
    base.main()
