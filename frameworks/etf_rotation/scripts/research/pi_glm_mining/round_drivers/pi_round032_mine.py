#!/usr/bin/env python3
"""Round 032 driver: completes the stage-5 round over the built fund_flow +
nav_premium families (health-checked in atom_health.csv, zero shadow). Six
rank_spread candidates, each with >=1 fund_flow/nav_premium leg, all pairs
atom-level new, burnt atoms declared. Gate 7 v2.1; leak gates include the
physical PIT truncation/perturbation branch for fund_share/nav."""
from __future__ import annotations

import json
import sys
import yaml
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_032"

base.CANDIDATES = [
    {
        "id": "X1",
        "operator": "rank_spread",
        "left": {"name": "PREMIUM", "source": "nav_premium"},
        "right": {"name": "OVERNIGHT_GAP", "source": "daily_candle"},
        "mechanism": "premium_gap_divergence",
        "hypothesis": "两腿角色：A=折溢价(二级情绪/净值偏离)，B=隔夜跳空(隔夜信息)。假设：溢价高而隔夜跳空弱(信号高)=二级情绪溢价无隔夜信息支撑，回吐；折价而隔夜跳空强(信号低)=折价+隔夜信息，修复。声明：OVERNIGHT_GAP(T1 中拒绝)第2次；PREMIUM 首次价差腿。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "X2",
        "operator": "rank_spread",
        "left": {"name": "SHARE_CHG_20", "source": "fund_flow"},
        "right": {"name": "DOWNSIDE_DEV_20", "source": "downside_risk"},
        "mechanism": "flow_vs_downside_pressure",
        "hypothesis": "两腿角色：A=份额流入(一级配置方向)，B=下行偏差(风险压力)。假设：份额流入而下行偏差低(信号高)=健康吸筹(配置盘无恐慌)，延续；份额流出而下行偏差高(信号低)=双重压力，走弱。声明：SHARE_CHG_20 首次价差腿；DOWNSIDE_DEV_20(Q3)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X3",
        "operator": "rank_spread",
        "left": {"name": "PREMIUM", "source": "nav_premium"},
        "right": {"name": "STREAK_DAYS", "source": "fund_flow"},
        "mechanism": "premium_absorption_streak",
        "hypothesis": "两腿角色：A=折溢价(二级定价偏离)，B=连续申赎天数(一级承接方向)。假设：溢价高且连续净申购(信号高)=一级申购资金在承接二级溢价(套利资金在接)，延续；溢价高而连续净赎回(信号低)=溢价无承接，回吐。新x新组合(两腿均首次价差配对)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X4",
        "operator": "rank_spread",
        "left": {"name": "PRIMARY_SHARE_20", "source": "fund_flow"},
        "right": {"name": "ULCER_60", "source": "downside_risk"},
        "mechanism": "primary_pricing_vs_chronic_bleed",
        "hypothesis": "两腿角色：A=一级市场量占比(定价主渠道)，B=60日溃疡(慢性失血)。假设：一级占比高而溃疡浅(信号高)=一级申赎主导定价且结构健康，延续；溃疡深(信号低)=慢性失血中的申赎，不可信。声明：PRIMARY_SHARE_20(Y6)第2次；ULCER_60(Y1)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X5",
        "operator": "rank_spread",
        "left": {"name": "SHARE_CHG_20", "source": "fund_flow"},
        "right": {"name": "TAIL_Q10_20", "source": "return_tail_shape"},
        "mechanism": "flow_tail_hygiene",
        "hypothesis": "两腿角色：A=份额流入(配置方向)，B=左尾深度(尾部损伤)。假设：份额流入而近期左尾浅(信号高)=配置无尾部破坏干扰，健康延续；份额流出而左尾深(信号低)=流出叠加尾部损伤，走弱。声明：SHARE_CHG_20 第2次；TAIL_Q10_20(S2/BB6)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "X6",
        "operator": "rank_spread",
        "left": {"name": "PREMIUM_Z_20", "source": "nav_premium"},
        "right": {"name": "CATEGORY_CURRENT_DD_60", "source": "category_state"},
        "mechanism": "premium_z_vs_category_health",
        "hypothesis": "两腿角色：A=折溢价 z(定价偏离标准化)，B=类别回撤(环境条件)。假设：溢价 z 高而类别回撤浅(信号高)=健康环境中的温和溢价，延续；类别回撤深而溢价 z 高(信号高区)=弱市透支，回吐。声明：PREMIUM_Z_20 首次价差腿；CATEGORY_CURRENT_DD_60(T6)第2次。注意：本条为 rank_spread(非条件化)，两腿价差本身检验溢价相对环境的偏离。预期正方向。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_fund(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage5_primary_market_data"
    plan["pit_note"] = "fund_share/nav 仅以 usable_from_date <= D 对齐（唯一允许方式）；泄漏门含物理截断/截后扰动副本"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_fund

_orig_build = base._build_atoms


def _build_atoms_with_fund(panels, eligibility_all, symbols, plan, data_root=base.CANONICAL_ROOT,
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


base._build_atoms = _build_atoms_with_fund

_orig_leak = base._leak_checks


def _leak_checks_with_fund(ranked, panels, eligibility_all, symbols, plan, workdir):
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


base._leak_checks = _leak_checks_with_fund

if __name__ == "__main__":
    base.main()
