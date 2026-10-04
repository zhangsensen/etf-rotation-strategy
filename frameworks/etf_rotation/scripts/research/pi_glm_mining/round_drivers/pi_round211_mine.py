#!/usr/bin/env python3
"""Round 211 driver: stage 61b — second S64 replication with master-verified
exact construction (rolling-X daily values, same-window median split, groups
>=1, LUNCHPR window 40). n=4 replication exemption."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_211"

S64 = "repl_sonnet_s64_split_r2"
UW = "replication_volume_free_v1"
BETA = "sonnet_repl_r_beta"
GAPDD = "sonnet_repl_r2_gapdd"


def _pair(cid, left, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": S64},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s61b_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _pair("NR2A", "R2_PERMENT_TURNOVER_SPLIT_20", "RP_UW_CHG_20", UW, -1,
     "精确构造：X=1m PE 的 20 日滚动日值，同窗成交额中位分组（≥1 日）。Sonnet 目标 disc t 2.97 / aud +49.7 (t2.45)。"),
    _pair("NR2B", "R2_PERMENT_TURNOVER_SPLIT_20", "R_CONTINUOUS_BETA_60", BETA, -1,
     "同左腿 − 连续日 beta。Sonnet 目标 disc t 4.15 / aud +35.4。"),
    _pair("NR2C", "R2_LUNCHPR_ONGAP_SPLIT", "R_GAP_DD_CONSUMPTION_20", GAPDD, 1,
     "X=LUNCH_POST_RUN 滚动日值，跳空符号分组（窗 40）。Sonnet 目标 disc t 3.68 / aud +26.4。"),
    _pair("NR2D", "R2_ULCER_NOISERATIO_SPLIT", "RP_PERM_ENT_D3_20", UW, 1,
     "X=ULCER 滚动日值，5m 噪声 VR 20 日变化符号分组。Sonnet 目标 disc t 3.98 / aud +21.4。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s61b(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage61b_repl_sonnet_s64_split_r2"
    plan["family_note"] = (
        "第 61b 阶段：S64 复现第二次——主控核对出两线做的不是同一原子（左腿 corr 仅 0.03）。"
        "精确构造：X=滚动原子日值（20 日均值 mp12）、同窗自身中位数分组（含当日）、组内 ≥1 日、"
        "LUNCHPR 窗 40。体检报 R2 与第 61 阶段 R_ 版及 ret1/ret20 的 corr。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s61b

if __name__ == "__main__":
    base.main()
