#!/usr/bin/env python3
"""Round 029 driver: THREE-ATOM CONDITIONAL constructions (stage-3/4 drafts
19-27, activated by two-atom exhaustion archived in round_028).

New operators (driver-level extension; engine gates/dedup/leak untouched):
  cond_spread      : (rank(L) - rank(R)).where(C in <half>)
  cond_double      : rank(L).where(C1 in <half> & C2 in <half>)
  cond_interaction : (rank(L) * rank(R)).where(C in <half>)
Half = cross-sectional rank >= 0.5 (top) / < 0.5 (bottom). NaN rows simply do
not enter ranking (directive 21: discovery_days gate applies unchanged).

Every candidate carries >=1 locally derived three-family atom; C atoms come
from the three families or category_state/market_sensitivity (directive 20).
Gate 7 v2.1; dedup/leak caches active.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_029"

base.CANDIDATES = [
    {
        "id": "H1",
        "operator": "cond_spread",
        "left": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "conds": [
            {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m", "side": "top"}
        ],
        "mechanism": "orderly_flow_priced_at_open_heavy_days",
        "hypothesis": "三腿角色：A=1m主买不平衡(资金方向)，B=量熵(参与形态)，C=早盘量集中度(环境)。假设：开盘集中(隔夜信息开盘定价日)时，全天主买相对参与脉冲的优势更可定价——主买强+参与均匀的价差在开盘集中日延续。三腿全新组合；三腿均为1m新家族原子。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "H2",
        "operator": "cond_spread",
        "left": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "SESSION_MEAN_60", "source": "daily_candle"},
        "conds": [
            {"name": "CATEGORY_MOM_20", "source": "category_state", "side": "bottom"}
        ],
        "mechanism": "close_marking_against_weak_category",
        "hypothesis": "三腿角色：A=尾盘量集中度(收盘定价行为)，B=时段漂移(趋势背景)，C=类别动量(环境)。假设：类别动量弱(板块无共识、个体信息主导环境)时，尾盘集中而时段漂移弱=知情资金逆板块风收盘建仓，随后修复。声明复用：CLOSE30(D6/V2/V3)、SESSION_MEAN_60(U3/W3/D3)均为烧毁原子，本三腿组合全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "H3",
        "operator": "cond_double",
        "left": {"name": "PROFIT_RATIO_60", "source": "cost_distribution"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "conds": [
            {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m", "side": "top"},
            {"name": "CATEGORY_VOL_60", "source": "category_state", "side": "bottom"}
        ],
        "mechanism": "event_driven_healthy_profit",
        "hypothesis": "三腿角色：A=获利结构(成本视角)，B=事件活跃度(条件1)，C=类别波动(环境条件)。假设：获利盘仅在事件活跃放量且类别平静时=事件驱动的健康获利结构(有真实信息博弈)，延续；无事件活跃的获利=拉抬透支。声明：PROFIT_RATIO_60第6次、SPIKE第4次、CATEGORY_VOL_60(N3中拒绝)——三腿组合全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "H4",
        "operator": "cond_double",
        "left": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "conds": [
            {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m", "side": "top"},
            {"name": "CATEGORY_BREADTH_MA60", "source": "category_state", "side": "bottom"}
        ],
        "mechanism": "scheduled_execution_in_differentiated_market",
        "hypothesis": "三腿角色：A=大bar边缘集中(定时执行)，B=早盘集中度(条件1)，C=类别广度(环境条件)。假设：定时执行集中于开盘且类别分化(广度低)=分化行情中的机构规则建仓，延续。声明：OPEN30(F1入选右端，禁变体——此处为条件腿非信号腿)、BREADTH(T2中拒绝)；三腿组合全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "H5",
        "operator": "cond_spread",
        "left": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "DOWNSIDE_BETA_20", "source": "market_sensitivity"},
        "conds": [
            {"name": "CATEGORY_CURRENT_DD_60", "source": "category_state", "side": "bottom"}
        ],
        "mechanism": "uniform_participation_defensive_config",
        "hypothesis": "三腿角色：A=量熵(参与均匀度)，B=下行贝塔(系统性敏感)，C=类别回撤(环境条件)。假设：类别回撤浅(环境健康)时，量熵高(均匀参与)而下行敏感低(信号高)=防御性均匀配置环境，延续。声明：ENTROPY第7次、DOWNSIDE_BETA_20(Q3中拒绝)第2次；三腿组合全新。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "H6",
        "operator": "cond_interaction",
        "left": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "conds": [
            {"name": "CATEGORY_CURRENT_DD_60", "source": "category_state", "side": "bottom"}
        ],
        "mechanism": "clean_structure_uniform_config",
        "hypothesis": "三腿角色：A=套牢厚度(结构包袱)，B=量熵(参与均匀度)，C=类别回撤(环境条件)。假设：类别回撤浅(环境健康)时，套牢薄×量熵高的乘积=干净结构+均匀参与的配置完成形态，强延续。声明：OVERHAND第5次、ENTROPY第8次——条件化新构造下的最后组合。预期正方向。",
        "expected_sign": 1,
    },
]

# ---------------------------------------------------------------- driverside
# conditioning extension (engine gates/dedup/leak/caches untouched)


def _canonical_expression(cand: dict) -> str:
    op = str(cand.get("operator", ""))
    if op.startswith("cond_"):
        legs = "+".join([cand["left"]["name"], cand["right"]["name"]])
        conds = "+".join(f"{c['name']}:{c['side']}" for c in cand.get("conds", []))
        return f"{op}({legs}|{conds})"
    return _orig_canonical(cand)


_orig_canonical = base.canonical_expression
base.canonical_expression = _canonical_expression

_orig_spec = base._expression_spec


class _CondSpec:
    def __init__(self, cand: dict):
        self.cand = cand
        self.operator = cand["operator"]
        l, r = cand["left"]["name"], cand["right"]["name"]
        conds = " & ".join(f"{c['name']}:{c['side']}" for c in cand["conds"])
        forms = {
            "cond_spread": f"cond(rank({l}) - rank({r}) | {conds})",
            "cond_double": f"cond(rank({l}) | {conds})",
            "cond_interaction": f"cond(rank({l}) * rank({r}) | {conds})",
        }
        self.readable = forms[self.operator]
        self.family = "+".join(
            sorted({cand["left"]["source"], cand["right"]["source"]}
                   | {c["source"] for c in cand["conds"]})
        )


def _expression_spec(cand: dict):
    if str(cand.get("operator", "")).startswith("cond_"):
        return _CondSpec(cand)
    return _orig_spec(cand)


base._expression_spec = _expression_spec

_orig_materialize = base.materialize_expression


def _materialize(spec, ranked):  # noqa: ANN001
    cand = getattr(spec, "cand", None)
    if cand is None:
        return _orig_materialize(spec, ranked)

    def mask_of(c: dict) -> pd.DataFrame:
        rk = ranked[c["name"]]
        return rk >= 0.5 if c["side"] == "top" else rk < 0.5

    mask = mask_of(cand["conds"][0])
    for c in cand["conds"][1:]:
        mask = mask & mask_of(c)
    l = ranked[cand["left"]["name"]]
    if spec.operator == "cond_spread":
        base_sig = l - ranked[cand["right"]["name"]]
    elif spec.operator == "cond_interaction":
        base_sig = l * ranked[cand["right"]["name"]]
    else:  # cond_double
        base_sig = l
    return base_sig.where(mask)


base.materialize_expression = _materialize

# cond atoms must be built too: augment plan with synthetic helper entries
_orig_build = base._build_atoms


def _build_atoms_with_conds(panels, eligibility_all, symbols, plan, data_root=base.CANONICAL_ROOT,
                            sources_filter=None):
    extra = []
    for c in plan["candidates"]:
        for cnd in c.get("conds", []):
            extra.append(
                {
                    "left": {"name": cnd["name"], "source": cnd["source"]},
                    "right": {"name": cnd["name"], "source": cnd["source"]},
                }
            )
    aug = {**plan, "candidates": list(plan["candidates"]) + extra}
    return _orig_build(panels, eligibility_all, symbols, aug, data_root=data_root,
                       sources_filter=sources_filter)


base._build_atoms = _build_atoms_with_conds

# cond atoms must pass the leak gates too: augment plan for leak checks as well
_orig_leak = base._leak_checks


def _leak_checks_with_conds(ranked, panels, eligibility_all, symbols, plan, workdir):
    extra = []
    for c in plan["candidates"]:
        for cnd in c.get("conds", []):
            extra.append(
                {
                    "left": {"name": cnd["name"], "source": cnd["source"]},
                    "right": {"name": cnd["name"], "source": cnd["source"]},
                }
            )
    aug = {**plan, "candidates": list(plan["candidates"]) + extra}
    return _orig_leak(ranked, panels, eligibility_all, symbols, aug, workdir)


base._leak_checks = _leak_checks_with_conds

# plan wrapper: after base locks the plan, record conds provenance (additive)
_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_conds(args):
    _orig_cmd_plan(args)
    import hashlib  # noqa: F401

    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    # base 序列化不含 conds 字段：在任何评估开始前补全注册信息（此为注册完成，
    # 之后 PLAN 哈希锁生效、评估读取的即为本文件）。
    src_by_id = {c["id"]: c for c in base.CANDIDATES if "conds" in c}
    for cand in plan["candidates"]:
        src = src_by_id.get(cand["id"])
        if src is not None:
            cand["conds"] = src["conds"]
            cand["driver_extended"] = "cond_operator_v1"
    conds_provenance = {}
    for cand in plan["candidates"]:
        for cnd in cand.get("conds", []):
            src = cnd["source"]
            if src not in conds_provenance:
                cfg = base._config_path(src)
                conds_provenance[str(cfg)] = base._hash(cfg)
    plan["config_hashes"].update(conds_provenance)
    plan["conds_condition_policy"] = (
        "C 条件腿仅取截面状态（三家族原子或 category_state/market_sensitivity 状态原子）"
        "的上/下半区；时间序列状态不做（指令 11/补充）。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_conds

if __name__ == "__main__":
    base.main()
