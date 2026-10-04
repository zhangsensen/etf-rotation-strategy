#!/usr/bin/env python3
"""Round 030 driver: conditional operators (stage per directive block
23:05). Operators rank_cond / rank_cond_spread implemented in
etf_factor_grammar (ALLOWED_OPERATORS + materialize + readable) and the
engine (_expression_spec passes cond/cond_side; canonical dedup covers them).

Condition legs (C) are cross-sectional state atoms only: category_state /
market_sensitivity (time-series/market-level conditions prohibited, item 11).
Arithmetic note (round_029 proof): half conditioning on a 14-name universe
leaves 7 names < MIN_PAIRS=8, so discovery_days=0 is the expected outcome;
this batch faithfully executes the mandated construction class and documents
the arithmetic under the frozen gates. Bonferroni report line per 补充.
"""
from __future__ import annotations

import json
import sys
import yaml
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_030"

base.CANDIDATES = [
    {
        "id": "M1",
        "operator": "rank_cond",
        "left": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "right": {"name": "CATEGORY_MOM_20", "source": "category_state"},
        "cond": "CATEGORY_MOM_20",
        "cond_side": "top",
        "mechanism": "trend_confirmed_profit_structure",
        "hypothesis": "三腿角色：A=获利结构(成本视角)，B=类别动量(截面环境条件)。假设：类别动量强势(上半区)时，获利结构由顺势资金形成、抛压被板块承接吸收，获利延续。条件方向经济含义：顺势环境放大获利结构的有效性。三腿：A 为筹码新家族原子，B/C 为截面状态条件。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "M2",
        "operator": "rank_cond",
        "left": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "right": {"name": "CATEGORY_VOL_60", "source": "category_state"},
        "cond": "CATEGORY_VOL_60",
        "cond_side": "bottom",
        "mechanism": "calm_regime_pricing",
        "hypothesis": "三腿角色：A=价格/成本(获利定位)，B=类别波动(环境条件)。假设：类别波动平静(下半区)时，价格高于成本=低波环境中的有序配置定价，健康延续；高波环境中的同水平溢价=情绪定价。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "M3",
        "operator": "rank_cond",
        "left": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "right": {"name": "BENCHMARK_RESIDUAL_VOL_20", "source": "market_sensitivity"},
        "cond": "BENCHMARK_RESIDUAL_VOL_20",
        "cond_side": "bottom",
        "mechanism": "clean_structure_low_resid",
        "hypothesis": "三腿角色：A=套牢厚度(历史结构包袱)，B=特质波动(环境条件)。假设：特质波动低(下半区、无自身噪音)时，套牢薄=结构干净且定价安静，延续；特质波动高时的同结构=噪音未清。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "M4",
        "operator": "rank_cond",
        "left": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "CATEGORY_CURRENT_DD_60", "source": "category_state"},
        "cond": "CATEGORY_CURRENT_DD_60",
        "cond_side": "bottom",
        "mechanism": "close_participation_in_healthy_category",
        "hypothesis": "三腿角色：A=尾盘量集中度(收盘定价参与)，B=类别回撤(环境条件)。假设：类别回撤浅(环境健康)时，尾盘参与集中=收盘定价由真实配置驱动，延续；环境受损时的尾盘集中=防御性/拉抬。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "M5",
        "operator": "rank_cond_spread",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "cond": "DOWNSIDE_BETA_20",
        "cond_side": "top",
        "mechanism": "scheduled_exec_under_defensive_demand",
        "hypothesis": "三腿角色：A=大bar边缘集中(定时执行)，B=尾盘量集中(收盘定价)，C=下行贝塔(环境条件)。假设：高下行贝塔(防御需求强)环境中，定时执行相对尾盘定价的优势更可定价（规则执行对冲情绪），延续。声明：A/B 均为多次配对原子（C2/D6/Z1 等），条件化构造与三腿组合全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "M6",
        "operator": "rank_cond",
        "left": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "CATEGORY_BREADTH_MA60", "source": "category_state"},
        "cond": "CATEGORY_BREADTH_MA60",
        "cond_side": "top",
        "mechanism": "uniform_participation_in_broad_rally",
        "hypothesis": "三腿角色：A=量熵(参与均匀度)，B=类别广度(环境条件)。假设：广度高(普涨环境)时，量分布均匀=广泛参与的贝塔配置行情，延续；广度低时的均匀=孤立行情。声明：VOL_ENTROPY_20 已多次配对（C6/D1/E2/E4 中拒绝）；条件化构造与三腿组合全新。预期正方向。",
        "expected_sign": 1,
    },
]

# plan wrapper: inject cond fields + conds config hashes into the locked PLAN
_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_cond(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    src_by_id = {c["id"]: c for c in base.CANDIDATES}
    for cand in plan["candidates"]:
        src = src_by_id.get(cand["id"])
        if src is None:
            continue
        cand["cond"] = src.get("cond")
        cand["cond_side"] = src.get("cond_side")
        cand["driver_extended"] = "cond_operator_v1"
    # condition-leg config hashes (provenance; cond atom may be a 3rd leg)
    for cand in plan["candidates"]:
        cond_name = cand.get("cond")
        if not cond_name:
            continue
        for cfg in sorted((base.ROOT / "configs").glob("family_*_v1.yaml")):
            mining = yaml.safe_load(cfg.read_text())
            if any(a["name"] == cond_name for a in mining.get("atoms", [])):
                key = str(cfg.resolve())
                plan["config_hashes"][key] = base._hash(cfg)
                break
    plan["cond_condition_policy"] = (
        "C 条件腿仅取截面状态（三家族原子或 category_state/market_sensitivity 原子）"
        "的上/下半区；时间序列/市场级条件不做（指令 11）。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_cond

# rank_cond_spread's condition atom C is a third leg: build it via synthetic
# helper entries (same pattern as round_029)
_orig_build = base._build_atoms


def _build_atoms_with_cond(panels, eligibility_all, symbols, plan, data_root=base.CANONICAL_ROOT,
                           sources_filter=None):
    extra = []
    for c in plan["candidates"]:
        cond_name = c.get("cond")
        cond_source = None
        if cond_name and cond_name not in {c["left"]["name"], c["right"]["name"]}:
            for cfg in sorted((base.ROOT / "configs").glob("family_*_v1.yaml")):
                mining = yaml.safe_load(cfg.read_text())
                if any(a["name"] == cond_name for a in mining.get("atoms", [])):
                    cond_source = str(mining.get("factor_source"))
                    break
        if cond_name and cond_source:
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

# leak checks must cover the condition leg as well
_orig_leak = base._leak_checks


def _leak_checks_with_cond(ranked, panels, eligibility_all, symbols, plan, workdir):
    def _source_of(atom_name: str) -> str | None:
        for cfg in sorted((base.ROOT / "configs").glob("family_*_v1.yaml")):
            mining = yaml.safe_load(cfg.read_text())
            if any(a["name"] == atom_name for a in mining.get("atoms", [])):
                return str(mining.get("factor_source"))
        return None

    extra = []
    seen_cond = set()
    for c in plan["candidates"]:
        cond_name = c.get("cond")
        if not cond_name or cond_name in seen_cond:
            continue
        seen_cond.add(cond_name)
        src = _source_of(cond_name)
        if src is None:
            continue
        extra.append(
            {
                "left": {"name": cond_name, "source": src},
                "right": {"name": cond_name, "source": src},
            }
        )
    aug = {**plan, "candidates": list(plan["candidates"]) + extra}
    return _orig_leak(ranked, panels, eligibility_all, symbols, aug, workdir)


base._leak_checks = _leak_checks_with_cond

if __name__ == "__main__":
    base.main()
