#!/usr/bin/env python3
"""Round 034 driver: the final preregisterable fund-leg x low-burn old-atom
pairings. Entering streak: 2 consecutive gate-7 zero rounds (032/033). If this
batch yields zero gate-7 admissions, the contract's exhaustion criterion
(3 consecutive) is met and MECHANISM_EXHAUSTED.json + RETROSPECTIVE.md will be
written in this directory."""
from __future__ import annotations

import json
import sys
import yaml
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_034"

base.CANDIDATES = [
    {
        "id": "Z1",
        "operator": "rank_spread",
        "left": {"name": "SHARE_Z_60", "source": "fund_flow"},
        "right": {"name": "ULCER_60", "source": "downside_risk"},
        "mechanism": "flow_vs_chronic_bleed_60",
        "hypothesis": "两腿角色：A=份额变化 z(一级资金方向)，B=60日溃疡(慢性失血)。假设：份额流入而溃疡浅(信号高)=资金流入健康结构，延续；份额流出而溃疡深(信号低)=双重失血，走弱。声明：SHARE_Z_60 首次价差腿；ULCER_60(Y1 中拒绝)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z2",
        "operator": "rank_spread",
        "left": {"name": "PREMIUM_Z_20", "source": "nav_premium"},
        "right": {"name": "MARKET_LEAD_CORR_60", "source": "cross_etf_lead_lag"},
        "mechanism": "premium_z_vs_market_channel",
        "hypothesis": "折溢价 z 与市场领先耦合之差=溢价的渠道归属：溢价 z 高而市场耦合低(信号高)=非市场渠道的溢价(个体资金定价)，延续；市场渠道主导的溢价随市场回落。声明：PREMIUM_Z_20 首次价差腿；MARKET_LEAD_CORR_60(T4/BB2)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z3",
        "operator": "rank_spread",
        "left": {"name": "SHARE_CHG_5", "source": "fund_flow"},
        "right": {"name": "MARKET_LEAD_BETA_60", "source": "cross_etf_lead_lag"},
        "mechanism": "flow_vs_market_leading_beta",
        "hypothesis": "份额 5 日变化与市场领先贝塔之差=流入的渠道归属：流入强而市场领先贝塔低(信号高)=非市场渠道的个体配置流入，延续；贝塔渠道流入随市场。声明：SHARE_CHG_5 首次价差腿；MARKET_LEAD_BETA_60(W1 中拒绝)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z4",
        "operator": "rank_spread",
        "left": {"name": "PREM_SHARE_ALIGNED_20", "source": "nav_premium"},
        "right": {"name": "ULCER_60", "source": "downside_risk"},
        "mechanism": "arbitrage_alignment_vs_chronic_bleed",
        "hypothesis": "套利对齐与溃疡之差=承接的健康度：套利对齐强而溃疡浅(信号高)=套利承接健康结构，延续；套利对齐伴随深溃疡(信号高区)=慢性失血中的对齐，危险。声明：PREM_SHARE_ALIGNED_20(Y4)第2次；ULCER_60(Y1)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z5",
        "operator": "rank_spread",
        "left": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "right": {"name": "PEER_LEAD_CORR_60", "source": "cross_etf_lead_lag"},
        "mechanism": "primary_vs_peer_channel",
        "hypothesis": "份额-收益相关与组内耦合之差=渠道归属：一级驱动相关高而组内耦合低(信号高)=非组内传导的个体一级驱动，延续；组内耦合主导=组内渠道。声明：SHARE_RET_CORR_20(Y1)第2次；PEER_LEAD_CORR_60(T3)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "Z6",
        "operator": "rank_spread",
        "left": {"name": "PREMIUM_CHG_5", "source": "nav_premium"},
        "right": {"name": "BODY_TO_RANGE", "source": "daily_candle"},
        "mechanism": "premium_repair_vs_body_conviction",
        "hypothesis": "折溢价改善与实体坚决度之差=修复的确认方：溢价改善而实体坚决(信号高)=二级配置确认修复，延续；溢价改善而实体弱(信号高区)=虚拉修复，回吐。声明：PREMIUM_CHG_5(Y2)第2次；BODY_TO_RANGE(Y4/P6)第3次。预期正方向。",
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
