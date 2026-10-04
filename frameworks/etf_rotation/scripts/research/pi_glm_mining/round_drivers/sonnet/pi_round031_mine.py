#!/usr/bin/env python3
"""Round 031 driver: conditional stage, round 2 (streak entering = 1 zero
round: round_030). Six NEW rank_cond / rank_cond_spread combos: category
conditions are tie-rich, so valid discovery days are feasible (round_030 M1:
177 days, M6: 404 days proved the class viable for category conditions).
Reused atoms / construction-class changes declared per hypothesis."""
from __future__ import annotations

import json
import sys
import yaml
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_031"

base.CANDIDATES = [
    {
        "id": "W1",
        "operator": "rank_cond",
        "left": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "right": {"name": "CATEGORY_DISPERSION_60", "source": "category_state"},
        "cond": "CATEGORY_DISPERSION_60",
        "cond_side": "top",
        "mechanism": "informed_buy_in_differentiated_regime",
        "hypothesis": "条件(CATEGORY_DISPERSION_60 上半区)：类别分化大=个体行情主导环境。假设：分化环境中1m主买不平衡由个体信息驱动(非板块贝塔)，知情买入延续。声明：TICK_IMBALANCE_20 为 F1 入选左端，此处换条件化构造类并换条件腿，非窗口变体。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W2",
        "operator": "rank_cond",
        "left": {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"},
        "right": {"name": "CATEGORY_CURRENT_DD_60", "source": "category_state"},
        "cond": "CATEGORY_CURRENT_DD_60",
        "cond_side": "bottom",
        "mechanism": "clean_profit_in_healthy_category",
        "hypothesis": "条件(CATEGORY_CURRENT_DD_60 下半区)：类别回撤浅=结构健康环境。假设：环境健康时价格高于成本(获利定位)由真实配置形成、无恐慌干扰，延续。声明：PRICE_VS_AVGCOST_20 第2次条件化(D1/U1 为价差腿)；CATEGORY_CURRENT_DD_60 第2次(T6 中拒绝)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W3",
        "operator": "rank_cond",
        "left": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "cond": "CATEGORY_VOL_20",
        "cond_side": "bottom",
        "mechanism": "clean_structure_in_calm_regime",
        "hypothesis": "条件(CATEGORY_VOL_20 下半区)：类别波动平静=无噪音环境。假设：平静环境中套牢薄(历史包袱轻)的品种定价干净、趋势健康，延续。声明：OVERHAND_THICKNESS_60 第4次配对(D2/D3/E1/AA2)；条件化构造与条件腿全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W4",
        "operator": "rank_cond",
        "left": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "CATEGORY_MOM_60", "source": "category_state"},
        "cond": "CATEGORY_MOM_60",
        "cond_side": "top",
        "mechanism": "tail_participation_in_category_uptrend",
        "hypothesis": "条件(CATEGORY_MOM_60 上半区)：类别动量强=顺风环境。假设：顺风环境中尾盘参与集中=收盘定价由真实配置驱动(顺势收尾)，延续。声明：CLOSE30_VOL_SHARE_20 第3次条件化(D6/V2/V3 为价差腿)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W5",
        "operator": "rank_cond_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "COST_CENTER_SHIFT_20", "source": "cost_distribution"},
        "cond": "CATEGORY_DISPERSION_60",
        "cond_side": "top",
        "mechanism": "absorbed_pulse_vs_cost_chase",
        "hypothesis": "三腿角色：A=事件脉冲频率(信息事件)，B=成本重心位移(筹码追高)，C=类别分化(环境条件)。假设：分化环境(个体行情多)中，事件脉冲被市场深度吸收而成本未快速上移(信号高)=承接充分、信息未透支，延续；成本追高型脉冲=透支回归。声明：VOL_SPIKE_FREQ_20 第2次条件化(BB1 入选左端，禁变体)、COST_CENTER_SHIFT_20 第4次(D5/D6/E5 中拒绝)；本三腿组合全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "W6",
        "operator": "rank_cond",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "CATEGORY_MOM_5", "source": "category_state"},
        "cond": "CATEGORY_MOM_5",
        "cond_side": "top",
        "mechanism": "scheduled_execution_in_short_momentum",
        "hypothesis": "条件(CATEGORY_MOM_5 上半区)：类别短动量强=顺风短环境。假设：顺风短环境中大bar定时执行(开盘/收盘规则单)=顺势规则执行，延续。声明：BIGBAR_EDGE_CONC_20 第4次配对(C2/F5/Z1/AA3)；CATEGORY_MOM_5 首次作条件腿。预期正方向。",
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
        "C 条件腿仅取截面状态（三家族原子或 category_state/market_sensitivity 状态原子）"
        "的上/下半区；时间序列/市场级条件不做（指令 11）。"
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
