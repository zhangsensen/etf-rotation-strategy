#!/usr/bin/env python3
"""Round 033 driver: conditional stage round 2 (streak = 1 zero round:
round_030). Six NEW rank_cond combos on tie-rich category_state condition
atoms (feasible valid days proven: round_030 M1 177 days / M6 404 days).
Round_029's arithmetic infeasibility applies only to continuous condition
atoms (bottom-half = 7 names < 8) — avoided here by using tie-rich category
conditions. All combos new; condition directions preregistered."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_033"

base.CANDIDATES = [
    {
        "id": "B1",
        "operator": "rank_cond",
        "left": {"name": "SHARE_Z_60", "source": "fund_flow"},
        "right": {"name": "CATEGORY_CURRENT_DD_20", "source": "category_state"},
        "cond": "CATEGORY_CURRENT_DD_20",
        "cond_side": "top",
        "mechanism": "flow_inflow_in_healthy_category",
        "hypothesis": "条件(CATEGORY_CURRENT_DD_20 上半区=类别回撤浅、结构健康)：健康环境中份额 z 高(申购流入)=真实配置流入，延续。声明：SHARE_Z_60 首次条件化；CATEGORY_CURRENT_DD_20 首次作条件腿。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "B2",
        "operator": "rank_cond",
        "left": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "right": {"name": "CATEGORY_BREADTH_MA20", "source": "category_state"},
        "cond": "CATEGORY_BREADTH_MA20",
        "cond_side": "top",
        "mechanism": "breadth_confirmed_profit_structure",
        "hypothesis": "条件(CATEGORY_BREADTH_MA20 上半区=普涨环境)：广度高时获利盘高=顺势获利结构(贝塔获利)，延续。声明：PROFIT_RATIO_60 第2次条件化(C4-030 用 CATEGORY_MOM_20)；本条件腿全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "B3",
        "operator": "rank_cond",
        "left": {"name": "PREMIUM", "source": "nav_premium"},
        "right": {"name": "CATEGORY_DISPERSION_20", "source": "category_state"},
        "cond": "CATEGORY_DISPERSION_20",
        "cond_side": "bottom",
        "mechanism": "premium_in_consensus_regime",
        "hypothesis": "条件(CATEGORY_DISPERSION_20 下半区=板块一致环境)：一致环境中折溢价高=普涨的情绪溢价，随环境回归。声明：PREMIUM 首次条件化；CATEGORY_DISPERSION_20 首次作条件腿。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "B4",
        "operator": "rank_cond",
        "left": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "right": {"name": "CATEGORY_DISPERSION_20", "source": "category_state"},
        "cond": "CATEGORY_DISPERSION_20",
        "cond_side": "top",
        "mechanism": "idiosyncratic_profit_in_dispersion",
        "hypothesis": "条件(CATEGORY_DISPERSION_20 上半区=分化行情)：分化环境中价格高于成本(获利定位)=个体信息驱动的获利，延续。声明：PRICE_VS_AVGCOST_20 第2次条件化(M2-030 用 CATEGORY_VOL_60)；本条件腿全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "B5",
        "operator": "rank_cond",
        "left": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "right": {"name": "CATEGORY_BREADTH_MA20", "source": "category_state"},
        "cond": "CATEGORY_BREADTH_MA20",
        "cond_side": "top",
        "mechanism": "primary_flow_confirmed_by_breadth",
        "hypothesis": "条件(CATEGORY_BREADTH_MA20 上半区=普涨环境)：广度高时份额-收益相关高(信号高)=一级申购与价格互相确认(真实配置)，延续。声明：SHARE_RET_CORR_20 首次条件化；CATEGORY_BREADTH_MA20 第2次(不同窗口方向假设)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "B6",
        "operator": "rank_cond",
        "left": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "right": {"name": "CATEGORY_CURRENT_DD_20", "source": "category_state"},
        "cond": "CATEGORY_CURRENT_DD_20",
        "cond_side": "top",
        "mechanism": "overhang_relief_in_healthy_category",
        "hypothesis": "条件(CATEGORY_CURRENT_DD_20 上半区=类别健康)：套牢厚(信号高区)在健康环境中=历史套牢被持续买盘消化，解放行情延续。声明：OVERHAND_THICKNESS_60 第2次条件化(AA2-026 价差腿)；本条件腿全新。预期正方向。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_cond(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    src_by_id = {c["id"]: c for c in base.CANDIDATES}
    for cand in plan["candidates"]:
        src = src_by_id.get(cand["id"])
        if src is not None:
            cand["cond"] = src.get("cond")
            cand["cond_side"] = src.get("cond_side")
    for cand in plan["candidates"]:
        cond_name = cand.get("cond")
        if not cond_name:
            continue
        for cfg in sorted((base.ROOT / "configs").glob("family_*_v1.yaml")):
            mining = yaml.safe_load(cfg.read_text())
            if any(a["name"] == cond_name for a in mining.get("atoms", [])):
                plan["config_hashes"][str(cfg.resolve())] = base._hash(cfg)
                break
    plan["cond_condition_policy"] = (
        "条件腿仅取截面状态（category_state，tie-rich 保证有效日）；时间序列/市场级条件不做（指令 11）。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_cond

_orig_build = base._build_atoms


def _build_atoms_with_cond(panels, eligibility_all, symbols, plan, data_root=base.CANONICAL_ROOT,
                           sources_filter=None):
    extra = []
    seen = set()
    for c in plan["candidates"]:
        cond_name = c.get("cond")
        if not cond_name or cond_name in seen:
            continue
        seen.add(cond_name)
        cond_source = None
        for cfg in sorted((base.ROOT / "configs").glob("family_*_v1.yaml")):
            mining = yaml.safe_load(cfg.read_text())
            if any(a["name"] == cond_name for a in mining.get("atoms", [])):
                cond_source = str(mining.get("factor_source"))
                break
        if cond_source:
            extra.append(
                {
                    "left": {"name": cond_name, "source": cond_source},
                    "right": {"name": cond_name, "source": cond_source},
                }
            )
    aug = {**plan, "candidates": list(plan["candidates"]) + extra}
    return _orig_build(panels, eligibility_all, symbols, aug, data_root=data_root,
                       sources_filter=sources_filter)


base._build_atoms = _build_atoms_with_cond

_orig_leak = base._leak_checks


def _leak_checks_with_cond(ranked, panels, eligibility_all, symbols, plan, workdir):
    extra = []
    seen = set()
    for c in plan["candidates"]:
        cond_name = c.get("cond")
        if not cond_name or cond_name in seen:
            continue
        seen.add(cond_name)
        cond_source = None
        for cfg in sorted((base.ROOT / "configs").glob("family_*_v1.yaml")):
            mining = yaml.safe_load(cfg.read_text())
            if any(a["name"] == cond_name for a in mining.get("atoms", [])):
                cond_source = str(mining.get("factor_source"))
                break
        if cond_source:
            extra.append(
                {
                    "left": {"name": cond_name, "source": cond_source},
                    "right": {"name": cond_name, "source": cond_source},
                }
            )
    aug = {**plan, "candidates": list(plan["candidates"]) + extra}
    return _orig_leak(ranked, panels, eligibility_all, symbols, aug, workdir)


base._leak_checks = _leak_checks_with_cond

if __name__ == "__main__":
    base.main()
