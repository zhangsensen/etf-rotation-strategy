#!/usr/bin/env python3
"""Round 053 driver: stage 10 = single-atom readjudication of the WHOLE
catalog under gate 7 (top-3 vs 14-EW). Not a new search: every atom was
previously adjudicated only under the v9 cross-sectional IC referee. One
`atomic` candidate per non-shadow catalog atom; seven gates + dedup as
usual; direction determined by the discovery window; expected_sign = 0
(no prior direction — readjudication). Known shadow atoms excluded."""
from __future__ import annotations

import json
import sys
import yaml
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_053"

SHADOW_ATOMS = {
    "SYNC_BETA_20",       # r050 health: |corr| 0.760 vs downside_risk
    "PEER_RELSTR_Z_20",   # r050 health: |corr| 0.718 vs SESSION_MEAN_20
}


def _catalog_candidates() -> list[dict]:
    seen: set[str] = set()
    candidates: list[dict] = []
    for cfg_path in sorted((base.ROOT / "configs").glob("family_*_v1.yaml")):
        mining = yaml.safe_load(cfg_path.read_text())
        source = str(mining.get("factor_source"))
        for atom in mining.get("atoms", []):
            name = str(atom["name"])
            if name in seen or name in SHADOW_ATOMS:
                continue
            seen.add(name)
            candidates.append(
                {
                    "id": name,
                    "operator": "atomic",
                    "left": {"name": name, "source": source},
                    "right": {"name": name, "source": source},
                    "mechanism": f"readjudication__{name}",
                    "hypothesis": (
                        "货架重裁（阶段 10）：该原子此前仅在 v9 截面 IC 裁判下作 atomic 裁决，"
                        "本条在门 7（top-3 对 14-EW，v2.1）下用同一现行尺子重评；"
                        "expected_sign=0（无先验方向，方向由发现期确定）。"
                    ),
                    "expected_sign": 0,
                }
            )
    return candidates


base.CANDIDATES = _catalog_candidates()

# Stage-10 exemption: the plan-level hash assert refuses atomic expressions
# that exist in the v9 enumeration — but re-evaluating them under gate 7 is
# EXACTLY this stage's purpose (unified ruler, not a new-discovery claim).
# Evaluation-time dedup (shelf16 + prior admitted vectors incl. W3/Z1) stays
# fully active for any atom that passes the six intrinsic gates.
def _existing_expression_hashes_readjudication() -> dict[str, list[str]]:
    return {"previous_rounds": [], "v9_atomic": [], "shelf": []}


base._existing_expression_hashes = _existing_expression_hashes_readjudication

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_readjudication(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage10_atomic_readjudication"
    plan["readjudication"] = {
        "scope": "全部目录原子（非 shadow）各一条 atomic 候选",
        "excluded_shadow": sorted(SHADOW_ATOMS),
        "note": "口径统一重裁，非新搜索；旧原子泄漏门历史引用，新增原子按缓存计算",
    }
    plan["pit_note"] = (
        "atomic 原子全部沿用既有家族构建（PIT 不变）；泄漏门按缓存命中/新增计算"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_readjudication

if __name__ == "__main__":
    base.main()
