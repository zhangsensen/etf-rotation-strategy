#!/usr/bin/env python3
"""Round 212 driver: stage 62 — replicate Sonnet S66 RP_CHANGE_20 x volume
spike + controls. Master lists 5 expressions; 3 of them (RET20 x VOL_SPIKE,
RET20 x MFI, RP_CHANGE x RP_UW) are expression-hash identical to r204 CTC4 /
CTC1 and r203 CGP16 — preregistering them again would collide with the global
dedup. Only the 1 genuinely new expression is preregistered; the other 4
are cited from r203/r204 outputs (master sanctioned citation for #3; engine
dedup blocks re-preregistering hash-identical expressions).
n_preregistered=3 (replication; 4 citations + 2 threshold-free spike-leg variants)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_212"

CGO = "cgo_true_turnover_v2"
SPK = "intraday_volume_profile_1m"
GAPDD = "sonnet_repl_r2_gapdd"


def _pair(cid, left, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": CGO},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s62_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _pair("N62A", "RP_CHANGE_TT_20", "VOL_SPIKE_FREQ_20", SPK, 1,
     "S66 复现：成本基线上移速度 × 量事件低（RP_CHANGE 有 ret20 之外的成本会计增量）。Sonnet 目标 disc +23.4/t2.02 / aud +23.7，H20 aud t 2.84。"),
    _pair("N62B", "RP_CHANGE_TT_20", "VTS_Q95_MED_20", "volume_tail_shape_1m", 1,
     "S66 spike 腿的无阈值改写（第 55 阶段：与 VOL_SPIKE 排序 corr 仅 0.58，定义稳健版）× 成本基线上移。"),
    _pair("N62C", "RET20_CLOSE", "VTS_Q95_MED_20", "volume_tail_shape_1m", -1,
     "N62B 的 ret20 对照（主控对照法）：差值即 RP_CHANGE 的成本会计增量。Sonnet S66 对照 ret20 版发现 t −0.01。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s62(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage62_repl_sonnet_s66"
    plan["family_note"] = (
        "第 62 阶段：复现 Sonnet S66 RP_CHANGE×量 spike 及对照。主控列 5 条，其中 3 条与既有"
        "表达式哈希同物（#2=CTC4、#3=CTC1、#4=CGP16，全局去重挡回）——按主控'#3 直接引用并列'"
        "的口径以引用入对照表；N62E 亦与 r203 CGP 系同哈希被引擎挡回——本轮实预注册 3 条新表达式（N62A 复现 + N62B/C spike 腿无阈值改写及其 ret20 对照，满足引擎 ≥2 独立机制）。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s62

if __name__ == "__main__":
    base.main()
