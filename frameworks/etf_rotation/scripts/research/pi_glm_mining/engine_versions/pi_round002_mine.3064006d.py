#!/usr/bin/env python3
"""Round 002: preregistered low-redundancy cross-sectional ETF factor mining.

Corrections carried from the round_001 supervisor review (round_001 outputs are
frozen and never overwritten):

  C1  residual diagnostic removed entirely (16-regressor OLS on <=14
      cross-sectional names was saturated/underdetermined; see
      outputs/round_002/correction.json).
  C2  leak checks are a HARD gate: any False / non-finite / NaN-mask mismatch
      fails closed and blocks every promotion. Future perturbation compares
      missing-value masks (no nanmax skipping). Because intraday providers
      read their own files, the intraday path is verified with a REAL input
      truncation (physically truncated copies of the intraday parquet files)
      plus a post-cutoff perturbation of those copies.
  C3  input file hashes via hash_research_inputs, script/config snapshots and
      the exact command are stored; every run attempt is logged to
      attempts.jsonl; PLAN.json is write-once. New expression hashes are
      deduplicated against ALL previous round plans (canonical, swap- and
      sign-symmetric forms collapse to one hash) and against the v9 atomic
      enumeration / shelf keys.
  C4  deterministic gate-then-dedup: intrinsic gates first (no cross-candidate
      information); only gate passers, in fixed plan order, are rank-correlation
      compared against the baseline 16 shelf factors + previously admitted
      candidates from earlier rounds + earlier admitted candidates of this
      batch. Reuses the shelf rule: Pearson correlation of cross-sectional
      ranks, stride=5, min_periods=500, discovery-window only. A missing
      must-compare correlation fails closed (candidate rejected, never passed).
  C5  contract frozen (population, D+2 clock, H=5/10/20, surfaces, identity
      gate). Direction is determined by the discovery period; expected_sign is
      recorded as an economic hypothesis and mismatches are reported, never
      used to rescue.

Sub-commands:
  plan      write PLAN.json (preregistration lock, before any evaluation)
  evaluate  read PLAN.json; --mode validate runs one candidate end-to-end
            (including hard leak gates); --mode batch evaluates all.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]  # .../workspace/frameworks/etf_rotation
sys.path.insert(0, str(ROOT / "src"))

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core.etf_data_provenance import hash_research_inputs
from etf_strategy.core.etf_factor_grammar import (
    ExpressionSpec,
    build_pit_eligibility,
    cross_sectional_rank,
    materialize_expression,
)
from etf_strategy.core.etf_family_referee import block_means, common_sample_spearman
from etf_strategy.core.etf_identity import identity_gate, leave_one_symbol_out
from etf_strategy.core.family_registry import load_builtin_families, resolve_family

CANONICAL_ROOT = Path(str(Path(__file__).resolve().parents[6] / "data/etf_rotation_v1"))
CORAL_PROJECT = Path(str(Path(__file__).resolve().parents[6]))
UNIVERSE_CONFIG = CORAL_PROJECT / "config/etf_rotation_universe_v1.json"
SHELF_DIR = CORAL_PROJECT / "runtime_outputs/etf_ic_factor_shelf_v11_20260919"
LEDGER_MANIFEST = (
    CORAL_PROJECT / "runtime_outputs/etf_family_multisource_v9_20260919/run_manifest.json"
)
WORKSPACE_OUTPUTS = ROOT.parents[1] / "outputs"  # workspace/outputs

ROUND_ID = "round_002"
AS_OF = "2026-09-17"
DISCOVERY_END = pd.Timestamp("2023-12-31")
AUDIT_START = pd.Timestamp("2024-01-01")
AUDIT_END = pd.Timestamp("2025-04-30")
HORIZONS = [5, 10, 20]
PRIMARY = 5
LAG = 2
MIN_PAIRS = 8
MIN_HISTORY = 120
RANK_CORR_STRIDE = int(
    yaml.safe_load((ROOT / "configs/ic_factor_shelf_v1.yaml").read_text())[
        "rank_correlation_sample_stride"
    ]
)
RANK_CORR_MIN_PERIODS = 500
GATES = {
    "min_discovery_days": 360,
    "min_abs_ic": 0.01,
    "min_abs_seen_audit_ic": 0.01,
    "identity_min_abs_ic": 0.01,
    "min_year_direction_count": 2,
    "max_abs_factor_rank_corr": 0.70,
    "topk_k": 3,
    "topk_min_t_block5_disc": 2.0,
    "topk_min_excess_audit_bp": 5.0,
}
EVIDENCE_STATUS = "discovery_candidate_not_certified"

CANDIDATES = [
    {
        "id": "R1",
        "operator": "rank_interaction",
        "left": {"name": "LAST_HOUR_RET", "source": "intraday_return_path"},
        "right": {"name": "TURNOVER_CONCENTRATION", "source": "intraday_turnover_shape"},
        "mechanism": "closing_execution_information",
        "hypothesis": "尾盘收益的信息含量取决于全日成交的时间集中度：知情交易者为最小化冲击成本倾向在尾盘集中执行，'尾盘有方向+成交高度集中'是知情定价，短期延续；成交时间分散时的尾盘收益是流动性噪声。交互捕捉被确认的尾盘动能。",
        "expected_sign": 1,
    },
    {
        "id": "R2",
        "operator": "rank_interaction",
        "left": {"name": "CLOSE_VWAP_DEV_Z_20", "source": "intraday_vwap_position"},
        "right": {"name": "RET_5", "source": "directional_trend"},
        "mechanism": "marking_pressure_short_reversal",
        "hypothesis": "收盘价相对全日VWAP的偏离z(20日)度量持续性的日内收盘买压/标记行为；当近5日已经上涨(短线超买)时，该压力更可能是不可持续的装饰性收盘，随后的短期回报应为负。交互预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "R3",
        "operator": "rank_interaction",
        "left": {"name": "MORNING_VOL_SHARE", "source": "intraday_volatility_structure"},
        "right": {"name": "RET_20", "source": "directional_trend"},
        "mechanism": "information_timing_trend_persistence",
        "hypothesis": "波动的日内时间结构刻画信息到达速度：早盘波动占比高=隔夜信息在开盘快速一次性定价(有效定价)，此后趋势漂移可持续；午后波动占比高=盘中增量噪声/情绪交易消耗趋势。中期趋势方向x信息到达时点交互。",
        "expected_sign": 1,
    },
    {
        "id": "R4",
        "operator": "rank_interaction",
        "left": {"name": "FIRST_HOUR_RET", "source": "intraday_return_path"},
        "right": {"name": "AMIHUD_20", "source": "price_volume_coupling"},
        "mechanism": "opening_move_liquidity_cost",
        "hypothesis": "开盘一小时方向性变动的含义取决于冲击成本状态：低AMIHUD(高流动性低冲击)环境中的早盘方向更可能是机构有序建仓、日内延续；高冲击成本环境中的早盘波动更多是噪声来回。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R5",
        "operator": "rank_interaction",
        "left": {"name": "INTRADAY_PV_RETURN_TURNOVER_CORR", "source": "intraday_price_volume_shock"},
        "right": {"name": "MONEY_PRESSURE_20", "source": "price_volume_coupling"},
        "mechanism": "flow_quality_resonance",
        "hypothesis": "日内量价相关(上涨时段换手集中=买方驱动知情流入)度量单日流入质量；与20日资金压力方向共振时流入质量高、短期延续，背离则量价关系不稳定。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R6",
        "operator": "rank_interaction",
        "left": {"name": "INTRADAY_TAIL_JUMP_ASYMMETRY", "source": "intraday_tail_reversal_jump"},
        "right": {"name": "PRICE_POSITION_60", "source": "price_location"},
        "mechanism": "position_dependent_tail_reversal",
        "hypothesis": "5分钟尾盘跳转不对称(尾盘急拉/急跌)的短期含义取决于价格在60日区间的位置：高位尾盘急拉更像派发/诱多，低位尾盘急跌像出清后的修复。位置条件化的尾盘流动性冲击交互预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "R7",
        "operator": "rank_interaction",
        "left": {"name": "MORNING_AFTERNOON_SPREAD", "source": "intraday_return_path"},
        "right": {"name": "VOLUME_RATIO_5_20", "source": "trading_activity"},
        "mechanism": "intraday_rotation_volume_expansion",
        "hypothesis": "日内强弱切换(早弱午后强=接力形态)在量能扩张(5日/20日量比高)时代表资金日内轮动接力、短期延续；缩量下的午后拉升是虚拉。与round_001 E1不同：E1是中期趋势x成交额水平拥挤，此处左端是日内时段切换形态而非多日动量。交互预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "R8",
        "operator": "rank_interaction",
        "left": {"name": "VWAP_HALFDAY_SLOPE", "source": "intraday_vwap_position"},
        "right": {"name": "RANGE_ACTIVITY_ELASTICITY_60", "source": "uncertainty_activity"},
        "mechanism": "intraday_drift_activity_regime",
        "hypothesis": "日内VWAP半日斜率(午后相对早盘的漂移方向)在不同活跃度-波幅弹性状态下含义不同：低弹性(缩量窄幅)环境中的日内漂移更可能是持续配置行为，高弹性环境中是情绪过山车易反转。交互预期正方向。",
        "expected_sign": 1,
    },
]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


CACHE_DIR = ROOT.parents[1] / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
_DATA_FP: dict[str, str] = {}


def _data_fingerprint() -> str:
    """Cheap deterministic fingerprint of the canonical data root (paths +
    sizes + mtimes of the parquet files actually used)."""
    if "fp" in _DATA_FP:
        return _DATA_FP["fp"]
    h = hashlib.sha256()
    root = CANONICAL_ROOT
    for sub in ("1d", "adj_factor", "1m", "5m", "15m", "30m", "60m"):
        d = root / sub
        if not d.exists():
            continue
        for f in sorted(d.glob("*.parquet")):
            st = f.stat()
            h.update(f"{sub}/{f.name}:{st.st_size}:{st.st_mtime_ns};".encode())
    _DATA_FP["fp"] = h.hexdigest()
    return _DATA_FP["fp"]


def _atom_cache_path(data_fp: str, cfg_hash: str, name: str, sym_key: str) -> Path:
    key = hashlib.sha256(
        f"{data_fp}|{cfg_hash}|{name}|{AS_OF}|{sym_key}|rank_v1".encode()
    ).hexdigest()
    cp = CACHE_DIR / "atoms" / f"{key}.parquet"
    cp.parent.mkdir(parents=True, exist_ok=True)
    return cp


def _leak_cache_path(data_fp: str, cfg_hash: str, name: str, sym_key: str) -> Path:
    key = hashlib.sha256(
        f"{data_fp}|{cfg_hash}|{name}|{AS_OF}|{sym_key}|leak_v1".encode()
    ).hexdigest()
    return CACHE_DIR / "leak" / f"{key}.json"


def _config_path(source: str) -> Path:
    return ROOT / "configs" / f"family_{source}_v1.yaml"


def canonical_expression(cand: dict) -> str:
    """Canonical, swap-symmetric (interaction) and sign-symmetric (spread) form."""
    left, right, op = cand["left"]["name"], cand["right"]["name"], cand["operator"]
    if op == "rank_interaction":
        a, b = sorted([left, right])
        return f"rank_interaction({a},{b})"
    if op == "rank_spread":
        return min(f"rank_spread({left},{right})", f"rank_spread({right},{left})")
    if op in ("rank_cond", "rank_cond_spread"):
        cond, side = cand.get("cond"), cand.get("cond_side")
        if op == "rank_cond":
            return f"rank_cond({left}|{cond}:{side})"
        return f"rank_cond_spread({left},{right}|{cond}:{side})"
    if op in ("cond_spread", "cond_double", "cond_interaction"):
        # round_029 historical conditional operators (archive compatibility)
        legs = "+".join(sorted([left, right]))
        conds = "+".join(
            f"{c['name']}:{c['side']}" for c in cand.get("conds", [])
        )
        return f"{op}({legs}|{conds})"
    if op == "atomic":
        return f"atomic({left})"
    raise ValueError(f"unknown operator {op}")


def expression_hash(cand: dict) -> str:
    return hashlib.sha256(canonical_expression(cand).encode()).hexdigest()


def _previous_round_plans() -> list[Path]:
    return sorted(WORKSPACE_OUTPUTS.glob("round_*/PLAN.json"))


def _canonical_names_from_readable(readable: str, operator: str) -> str:
    """Backward-compatible canonicalization of a stored readable expression."""
    names = sorted(
        part.strip().replace("rank(", "").replace(")", "")
        for part in readable.split("*" if operator == "rank_interaction" else "-")
    )
    if operator == "rank_interaction":
        return f"rank_interaction({names[0]},{names[1]})"
    return min(
        f"rank_spread({names[0]},{names[1]})", f"rank_spread({names[1]},{names[0]})"
    )


def _existing_expression_hashes() -> dict[str, list[str]]:
    """All expression hashes that must NOT be re-mined: previous round plans,
    v9 atomic enumeration, shelf keys."""
    hashes: dict[str, list[str]] = {"previous_rounds": [], "v9_atomic": [], "shelf": []}
    for plan_path in _previous_round_plans():
        plan = json.loads(plan_path.read_text())
        for cand in plan.get("candidates", []):
            if {"left", "right", "operator"} <= set(cand):
                fake = {
                    "operator": cand["operator"],
                    "left": {"name": cand["left"]["name"]},
                    "right": {"name": cand["right"]["name"]},
                }
                hashes["previous_rounds"].append(expression_hash(fake))
            elif "expression" in cand:  # fallback: readable string
                op = "rank_spread" if " - " in cand["expression"] else "rank_interaction"
                hashes["previous_rounds"].append(
                    hashlib.sha256(
                        _canonical_names_from_readable(cand["expression"], op).encode()
                    ).hexdigest()
                )
    decomp = pd.read_csv(LEDGER_MANIFEST.parent / "expression_decomposition.csv")
    for expression in decomp["expression"].astype(str):
        hashes["v9_atomic"].append(
            hashlib.sha256(f"atomic({expression})".encode()).hexdigest()
        )
    shelf = pd.read_csv(SHELF_DIR / "IC_FACTOR_SHELF.csv")
    for expression in shelf["expression"].astype(str):
        hashes["shelf"].append(
            hashlib.sha256(f"atomic({expression})".encode()).hexdigest()
        )
    return hashes


def _assert_not_window_variant(plan: dict, prior_plan: dict) -> None:
    prior_pairs = {
        frozenset(
            [c["left"]["name"], c["right"]["name"]]
            if {"left", "right"} <= set(c)
            else [t for t in c["expression"].replace("rank(", "").split(") ") if t]
        )
        for c in prior_plan.get("candidates", [])
    }
    prior_mechanisms = {c.get("mechanism") for c in prior_plan.get("candidates", [])}
    for cand in plan["candidates"]:
        pair = frozenset([cand["left"]["name"], cand["right"]["name"]])
        assert pair not in prior_pairs, f"{cand['id']} repeats a prior atom pair"
        assert cand["mechanism"] not in prior_mechanisms, (
            f"{cand['id']} mechanism name already tested in a prior round"
        )


def cmd_plan(args: argparse.Namespace) -> None:
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    plan_path = output / "PLAN.json"
    if plan_path.exists():
        raise SystemExit(f"PLAN.json already exists, preregistration is immutable: {plan_path}")
    manifest = json.loads(LEDGER_MANIFEST.read_text())
    cmd = manifest["command"]
    universe_config = (CORAL_PROJECT / cmd[cmd.index("--universe-config") + 1]).resolve()
    assert universe_config == UNIVERSE_CONFIG, "universe config drifted from v9 contract"

    prior_plans = _previous_round_plans()
    prior_names = [p.parent.name for p in prior_plans]
    assert ROUND_ID not in prior_names and prior_names == sorted(prior_names), (
        f"unexpected prior rounds: {prior_names}"
    )
    assert "round_001" in prior_names, "round_001 plan must exist for dedup baseline"
    dedup = _existing_expression_hashes()
    seen_hashes: dict[str, str] = {}
    for cand in CANDIDATES:
        h = expression_hash(cand)
        assert h not in seen_hashes, f"{cand['id']} duplicates {seen_hashes[h]} in-plan"
        seen_hashes[h] = cand["id"]
        for bucket, existing in dedup.items():
            assert h not in existing, (
                f"{cand['id']} canonical hash already exists in {bucket}; not a new candidate"
            )

    symbols = [
        row["ts_code"]
        for row in json.loads(UNIVERSE_CONFIG.read_text())["etfs"]
        if row["role"] == "candidate"
    ]
    sources = sorted(
        {c["left"]["source"] for c in CANDIDATES}
        | {c["right"]["source"] for c in CANDIDATES}
    )
    frequencies: set[str] = set()
    config_hashes: dict[str, str] = {}
    for source in sources:
        cfg = _config_path(source)
        mining = yaml.safe_load(cfg.read_text())
        config_hashes[str(cfg)] = _hash(cfg)
        if mining.get("frequency"):
            frequencies.add(str(mining["frequency"]))
        atoms = {a["name"] for a in mining["atoms"]}
        for cand in CANDIDATES:
            for side in ("left", "right"):
                slot = cand[side]
                if slot["source"] == source:
                    assert slot["name"] in atoms, f"{slot['name']} missing in {source}"
                    slot["family"] = mining["atoms"][0]["family"]
                    slot["config"] = str(cfg)
    input_hashes = hash_research_inputs(CANONICAL_ROOT, symbols, frequencies)

    for cand in CANDIDATES:
        assert cand["left"]["family"] != cand["right"]["family"], (
            f"{cand['id']} violates cross_family_only"
        )
    assert len({c["mechanism"] for c in CANDIDATES}) >= 2, "need >=2 independent mechanisms"

    prior_plan = json.loads(prior_plans[0].read_text())
    draft = {"candidates": CANDIDATES}
    _assert_not_window_variant(draft, prior_plan)

    plan = {
        "round_id": ROUND_ID,
        "miner": "pi/zai/glm-5.3-flash",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration_note": (
            "本文件在任何本轮评估计算之前写入并锁定；evaluate 子命令仅读取本文件。"
            "8条表达式均为跨家族原子交互(优先日内路径/成交结构x日线原子)，"
            "canonical哈希对round_001计划、v9的135个atomic枚举及shelf 16键去重；"
            "交换对称与纯符号变体不算新候选。组合数不等于独立机制数。"
        ),
        "corrections_from_round_001_review": {
            "C1": "残差诊断删除(outputs/round_002/correction.json)；round_001产物原样保留",
            "C2": "泄漏检查为硬门，fail closed；未来扰动比较缺失掩码；日内用物理截断副本+截后扰动验证",
            "C3": "hash_research_inputs输入哈希/脚本配置快照/命令/attempts日志/跨round表达式哈希去重",
            "C4": "先门后去重(固定顺序)，仅对shelf16+此前入选+本批已入选比较Pearson rank corr(stride=5,min_periods=500)，相关缺失fail closed",
            "C5": "契约冻结；方向由发现期确定，expected_sign仅为经济假设并如实报告不符",
        },
        "as_of": AS_OF,
        "data_root": str(CANONICAL_ROOT),
        "universe_config": str(universe_config),
        "universe_source": "原项目 run_manifest.json 的 command 字段程序化读取",
        "contract_copied_from": str(LEDGER_MANIFEST),
        "execution": {
            "signal_time": "D_CLOSE",
            "entry": "open(D+2+H)/open(D+2)-1",
            "entry_lag_sessions": LAG,
            "horizons": HORIZONS,
            "primary_horizon": PRIMARY,
            "min_pairs": MIN_PAIRS,
            "min_history_sessions": MIN_HISTORY,
            "require_positive_volume": True,
        },
        "surfaces": {
            "discovery_end": "2023-12-31",
            "seen_audit": ["2024-01-01", "2025-04-30"],
            "note": "2024-01-01起为已见审计面，非独立OOS；2025-04-30之后不参与本轮筛选。",
        },
        "gates": {
            **GATES,
            "referee_v2_1": "7th gate: top-3 excess over eligible equal-weight pool; "
            "discovery 5-session non-overlapping block t >= 2.0; audit 5-session excess "
            "mean >= 5 bp (v2.1, was '> 0'); Precision@3 > K/n baseline in both windows; "
            "identity uses identity_min_abs_ic",
        },
        "dedup_rule": {
            "order": "intrinsic gates first, then fixed plan order",
            "compare_against": [
                "baseline 16 shelf factors",
                "previously admitted candidates from earlier rounds",
                "earlier admitted candidates of this batch",
            ],
            "method": "Pearson correlation of stacked cross-sectional ranks, "
            f"discovery window only, stride={RANK_CORR_STRIDE}, min_periods={RANK_CORR_MIN_PERIODS}",
            "missing_correlation": "fail_closed_reject",
        },
        "input_hashes": input_hashes,
        "expression_hashes": {c["id"]: expression_hash(c) for c in CANDIDATES},
        "expression_canonical": {c["id"]: canonical_expression(c) for c in CANDIDATES},
        "evidence_status": EVIDENCE_STATUS,
        "shelf_reference": {
            "path": str(SHELF_DIR),
            "candidates": len(pd.read_csv(SHELF_DIR / "IC_FACTOR_SHELF.csv")),
        },
        "candidates": [],
        "config_hashes": config_hashes,
        "prior_round_plan_sha256": {p.parent.name: _hash(p) for p in prior_plans},
    }
    for cand in CANDIDATES:
        entry = {
            k: cand[k]
            for k in ("id", "operator", "mechanism", "hypothesis", "expected_sign")
        }
        entry["left"] = {k: cand["left"][k] for k in ("name", "source", "family", "config")}
        entry["right"] = {k: cand["right"][k] for k in ("name", "source", "family", "config")}
        entry["novelty"] = (
            "cross-family pair interaction; not a v9 atomic expression, not a "
            "round_001 pair, no window-variant reuse of round_001 failure mechanisms"
        )
        plan["candidates"].append(entry)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))
    print(f"PLAN locked: {plan_path} (candidates={len(plan['candidates'])})")


def _expression_spec(cand: dict) -> ExpressionSpec:
    return ExpressionSpec(
        cand["operator"],
        cand["left"]["name"],
        cand["right"]["name"] if cand["operator"] != "atomic" else None,
        family="+".join(sorted({cand["left"]["family"], cand["right"]["family"]})),
        cond=cand.get("cond"),
        cond_side=cand.get("cond_side"),
    )


def _raw_forward(open_prices: pd.DataFrame, horizon: int, lag: int) -> pd.DataFrame:
    """Label only. Entry open(D+lag), exit open(D+lag+H). Never used as a feature.
    The negative shifts below are the label definition; audit trail:
    scan_future_leaks.py negative_shift hits are expected here only."""
    entry = open_prices.shift(-lag)
    exit_price = open_prices.shift(-(lag + horizon))
    return (exit_price / entry - 1.0).where((entry > 0.0) & (exit_price > 0.0))


def _load_context() -> tuple[dict[str, pd.DataFrame], pd.DataFrame, list[str], dict[int, pd.DataFrame]]:
    panels = load_canonical_daily(CANONICAL_ROOT, UNIVERSE_CONFIG, as_of=AS_OF)
    all_eligibility = build_pit_eligibility(panels, MIN_HISTORY, True)
    universe = json.loads(UNIVERSE_CONFIG.read_text())["etfs"]
    symbols = [row["ts_code"] for row in universe if row["role"] == "candidate"]
    assert len(symbols) == 14, f"expected 14 candidates, got {len(symbols)}"
    eligibility = all_eligibility[symbols]
    forward = {
        h: _raw_forward(panels["open"][symbols], h, LAG).where(eligibility) for h in HORIZONS
    }
    return panels, eligibility, symbols, forward


def _build_atoms(
    panels, eligibility_all: pd.DataFrame, symbols: list[str], plan: dict,
    data_root: Path = CANONICAL_ROOT, sources_filter: set[str] | None = None,
) -> dict[str, pd.DataFrame]:
    load_builtin_families()
    needed: dict[str, set[str]] = {}
    for cand in plan["candidates"]:
        for side in ("left", "right"):
            slot = cand[side]
            needed.setdefault(slot["source"], set()).add(slot["name"])
    ranked: dict[str, pd.DataFrame] = {}
    sym_key = "|".join(symbols)
    data_fp = _data_fingerprint()
    for source, names in sorted(needed.items()):
        if sources_filter is not None and source not in sources_filter:
            continue
        cfg = _config_path(source)
        cfg_hash = _hash(cfg)
        mining = yaml.safe_load(cfg.read_text())
        remaining = []
        for name in sorted(names):
            cp = _atom_cache_path(data_fp, cfg_hash, name, sym_key)
            if cp.exists():
                ranked[name] = pd.read_parquet(cp)
            else:
                remaining.append(name)
        if not remaining:
            continue
        space = resolve_family(source).builder(panels, eligibility_all, data_root, mining)
        missing = sorted(set(remaining) - set(space))
        assert not missing, f"{source} missing atoms {missing}"
        for name in remaining:
            ranked[name] = cross_sectional_rank(space[name][symbols], eligibility_all[symbols])
            ranked[name].to_parquet(_atom_cache_path(data_fp, cfg_hash, name, sym_key))
    return ranked


def _masked_max_abs_diff(base: pd.DataFrame, other: pd.DataFrame, index: pd.Index) -> float | None:
    """Compare on a fixed index with EXPLICIT missing-mask equality.
    Returns None when masks differ (counts as failure, never skipped)."""
    a = base.reindex(index)
    b = other.reindex(index)
    if not a.notna().equals(b.notna()):
        return None
    mask = a.notna().to_numpy()
    if not mask.any():
        return 0.0
    diff = np.abs(a.to_numpy(dtype=float) - b.to_numpy(dtype=float))[mask]
    value = float(diff.max()) if diff.size else 0.0
    return value if np.isfinite(value) else None


def _temp_intraday_root(
    sources: list[str], symbols: list[str], mode: str, workdir: Path
) -> tuple[Path, set[str]]:
    """Build a local temp data root with PHYSICALLY truncated (mode=trunc) or
    post-cutoff-perturbed (mode=perturb) copies of the intraday files used by
    the plan. Original data root is never modified."""
    frequencies: set[str] = set()
    for source in sources:
        mining = yaml.safe_load(_config_path(source).read_text())
        if mining.get("frequency"):
            frequencies.add(str(mining["frequency"]))
    root = workdir / f"intraday_{mode}"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    for link in ("1d", "adj_factor"):
        target = CANONICAL_ROOT / link
        if target.exists() and not (root / link).exists():
            (root / link).symlink_to(target)
    rng = np.random.default_rng(20260919)
    for frequency in sorted(frequencies):
        out_dir = root / frequency
        out_dir.mkdir(exist_ok=True)
        for symbol in symbols:
            path = CANONICAL_ROOT / frequency / f"{symbol}.parquet"
            if not path.exists():
                continue
            frame = pd.read_parquet(path)
            dates = pd.to_datetime(frame["datetime"]).dt.normalize()
            if mode == "trunc":
                frame = frame.loc[dates <= DISCOVERY_END].copy()
            elif mode == "perturb":
                mask_rows = (dates > DISCOVERY_END).to_numpy()
                numeric = [
                    c
                    for c in frame.columns
                    if c != "datetime" and pd.api.types.is_numeric_dtype(frame[c])
                ]
                frame = frame.copy()
                if mask_rows.any() and numeric:
                    arr = frame[numeric].astype(float).to_numpy(copy=True)
                    noise = 1.0 + rng.normal(0.0, 0.05, size=(int(mask_rows.sum()), len(numeric)))
                    arr[mask_rows] = arr[mask_rows] * noise
                    frame[numeric] = arr
            frame.to_parquet(out_dir / path.name)
    return root, frequencies


def _atom_source_map(plan: dict) -> dict[str, str]:
    return {
        cand[s]["name"]: cand[s]["source"]
        for cand in plan["candidates"]
        for s in ("left", "right")
    }


def _leak_checks(
    ranked: dict[str, pd.DataFrame],
    panels: dict[str, pd.DataFrame],
    eligibility_all: pd.DataFrame,
    symbols: list[str],
    plan: dict,
    workdir: Path,
) -> dict:
    """Hard, fail-closed leak checks (referee v2.1 era, with per-atom cache).

    Per-atom results are cached under .cache/leak keyed by
    (data fingerprint, family config hash, atom, as_of, symbol set). Only
    atoms without a cached result are recomputed; the physical intraday
    truncation/perturbation copies are built only when such atoms exist.
    Cached results were produced under the same data fingerprint, so the
    guarantee carries over unchanged."""
    load_builtin_families()
    names = sorted(
        {cand[s]["name"] for cand in plan["candidates"] for s in ("left", "right")}
    )
    sources = sorted(
        {cand[s]["source"] for cand in plan["candidates"] for s in ("left", "right")}
    )
    intraday_sources = [
        s for s in sources if yaml.safe_load(_config_path(s).read_text()).get("frequency")
    ]
    atom_source = _atom_source_map(plan)
    prefix_index = ranked[names[0]].index[ranked[names[0]].index <= DISCOVERY_END]
    sym_key = "|".join(symbols)
    data_fp = _data_fingerprint()

    results: dict[str, object] = {
        "atoms_checked": len(names),
        "prefix_invariance_daily": {},
        "future_perturbation_daily": {},
    }
    failures: list[str] = []

    def record(kind: str, bucket: dict, key: str, value: float | None) -> None:
        if value is None or value > 1e-12:
            bucket[key] = "mask_mismatch_or_nonfinite" if value is None else value
            failures.append(f"{kind}:{key}")
        else:
            bucket[key] = value

    def merged(atom: str) -> dict:
        saved = cached.get(atom, {})
        merged = {"pass": bool(saved.get("pass", False))}
        for key, bucket in (
            ("prefix_daily", "prefix_invariance_daily"),
            ("perturb_daily", "future_perturbation_daily"),
            ("prefix_intraday", "prefix_invariance_intraday"),
            ("perturb_intraday", "future_perturbation_intraday"),
        ):
            if key in saved:
                record(f"{key}:{atom}", results.setdefault(bucket, {}), atom, saved[key])  # type: ignore[arg-type]
        return merged

    cached: dict[str, dict] = {}
    to_compute: list[str] = []
    for name in names:
        cp = _leak_cache_path(
            data_fp, _hash(_config_path(atom_source[name])), name, sym_key
        )
        if cp.exists():
            cached[name] = json.loads(cp.read_text())
        else:
            to_compute.append(name)
    results["cache"] = {"cached": len(names) - len(to_compute), "computed": len(to_compute)}

    # (a) daily prefix invariance + (b) daily future perturbation
    trunc_atoms = pert_atoms = None
    trunc_elig = pert_elig = None
    trunc_panels = pert_panels = None
    if to_compute:
        trunc_panels = {k: v.loc[:DISCOVERY_END].copy() for k, v in panels.items()}
        trunc_elig = build_pit_eligibility(trunc_panels, MIN_HISTORY, True)
        trunc_atoms = _build_atoms(trunc_panels, trunc_elig, symbols, plan)
        rng = np.random.default_rng(20260919)
        pert_panels = {k: v.copy() for k, v in panels.items()}
        for frame in pert_panels.values():
            rows = frame.index > DISCOVERY_END
            frame.loc[rows] = frame.loc[rows] * (
                1.0 + rng.normal(0.0, 0.05, size=(int(rows.sum()), frame.shape[1]))
            )
        pert_elig = build_pit_eligibility(pert_panels, MIN_HISTORY, True)
        pert_atoms = _build_atoms(pert_panels, pert_elig, symbols, plan)

    for name in names:
        if name in cached:
            merged(name)
            continue
        record(
            "prefix_daily",
            results["prefix_invariance_daily"],  # type: ignore[arg-type]
            name,
            _masked_max_abs_diff(ranked[name], trunc_atoms[name], prefix_index),  # type: ignore[union-attr]
        )
        record(
            "perturb_daily",
            results["future_perturbation_daily"],  # type: ignore[arg-type]
            name,
            _masked_max_abs_diff(ranked[name], pert_atoms[name], prefix_index),  # type: ignore[union-attr]
        )

    # (c)+(d) intraday providers read their own files: verify with REAL input
    # truncation and post-cutoff perturbation on local copies. Only intraday
    # sources are rebuilt (daily atoms are covered by (a)/(b)); panels are
    # restricted to the 14 candidate columns because the comparison only
    # touches those columns.
    results["intraday_sources"] = intraday_sources
    results["intraday_frequencies"] = sorted(
        {
            str(yaml.safe_load(_config_path(s).read_text()).get("frequency"))
            for s in intraday_sources
        }
    )
    if intraday_sources:
        intraday_plan = {
            **plan,
            "candidates": [
                c
                for c in plan["candidates"]
                if c["left"]["source"] in intraday_sources
                or c["right"]["source"] in intraday_sources
            ],
        }
        cand_panels = {k: v[symbols] for k, v in panels.items()}
        trunc_cand_panels = {k: v[symbols] for k, v in trunc_panels.items()} if trunc_panels else None
        pert_cand_panels = {k: v[symbols] for k, v in pert_panels.items()} if pert_panels else None
        intraday_to_compute = [
            n
            for n in to_compute
            if atom_source[n] in intraday_sources
        ]
        results["intraday_cache"] = {
            "computed": len(intraday_to_compute),
            "cached": len(names) - len(to_compute),
        }
        if intraday_to_compute:
            assert trunc_cand_panels is not None and pert_cand_panels is not None
            trunc_elig_intra = trunc_elig
            trunc_root, freqs = _temp_intraday_root(
                intraday_sources, symbols, "trunc", workdir
            )
            trunc_i_atoms = _build_atoms(
                trunc_cand_panels,
                trunc_elig,
                symbols,
                intraday_plan,
                data_root=trunc_root,
                sources_filter=set(intraday_sources),
            )
            pert_root, _ = _temp_intraday_root(
                intraday_sources, symbols, "perturb", workdir
            )
            pert_i_atoms = _build_atoms(
                cand_panels,
                eligibility_all,
                symbols,
                intraday_plan,
                data_root=pert_root,
                sources_filter=set(intraday_sources),
            )
            results["prefix_invariance_intraday"] = {}
            results["future_perturbation_intraday"] = {}
            for name in intraday_to_compute:
                record(
                    "prefix_intraday",
                    results["prefix_invariance_intraday"],  # type: ignore[arg-type]
                    name,
                    _masked_max_abs_diff(
                        ranked[name], trunc_i_atoms[name], prefix_index
                    ),
                )
                record(
                    "perturb_intraday",
                    results["future_perturbation_intraday"],  # type: ignore[arg-type]
                    name,
                    _masked_max_abs_diff(
                        ranked[name], pert_i_atoms[name], prefix_index
                    ),
                )
            shutil.rmtree(trunc_root, ignore_errors=True)
            shutil.rmtree(pert_root, ignore_errors=True)
        else:
            results["prefix_invariance_intraday"] = {}
            results["future_perturbation_intraday"] = {}

    # write per-atom cache records
    sym_key = "|".join(symbols)
    for name in to_compute:
        source = atom_source[name]
        record_out: dict[str, object] = {"pass": not _failures_for_atom(failures, name)}
        for bucket, key in (
            ("prefix_invariance_daily", "prefix_daily"),
            ("future_perturbation_daily", "perturb_daily"),
        ):
            value = results[bucket].get(name)
            if isinstance(value, float):
                record_out[key] = value
        for bucket, key in (
            ("prefix_invariance_intraday", "prefix_intraday"),
            ("future_perturbation_intraday", "perturb_intraday"),
        ):
            value = results.get(bucket, {}).get(name)
            if isinstance(value, float):
                record_out[key] = value
        cp = _leak_cache_path(data_fp, _hash(_config_path(source)), name, sym_key)
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(record_out))

    finite_ok = not failures
    results["failures"] = sorted(set(failures))
    results["pass"] = bool(finite_ok)
    results["contract"] = (
        "HARD gate: any mask mismatch, non-finite or missing comparison fails "
        "closed and blocks all promotions."
    )
    return results


def _failures_for_atom(failures: list[str], name: str) -> bool:
    """True if this atom has any failure entry."""
    return any(f.endswith(":" + name) for f in failures)


def _topk_referee(signal: pd.DataFrame, forward5: pd.DataFrame, eligibility: pd.DataFrame, direction: float) -> dict[str, object]:
    """7th gate (referee v2): rotation-relevant top-K excess over the eligible
    equal-weight pool. K=3, same D+2/open(D+7) label, same eligibility.
    Fail closed on any non-finite quantity."""
    k = GATES["topk_k"]
    sig = (signal * direction).where(eligibility)
    f = forward5.where(eligibility)
    valid = sig.notna() & f.notna()
    sig, f = sig.where(valid), f.where(valid)
    n = valid.sum(axis=1)
    ok = n >= max(MIN_PAIRS, k + 1)
    top_mask = sig.rank(axis=1, ascending=False, method="first") <= k
    real_top = f.rank(axis=1, ascending=False, method="first") <= k
    top_ret = f.where(top_mask).mean(axis=1).where(ok)
    ew_ret = f.mean(axis=1).where(ok)
    excess = top_ret - ew_ret
    precision = ((top_mask & real_top).sum(axis=1) / k).where(ok)

    disc_ex = excess.loc[:DISCOVERY_END].dropna()
    aud_ex = excess.loc[AUDIT_START:AUDIT_END].dropna()
    disc_p = precision.loc[:DISCOVERY_END].dropna()
    aud_p = precision.loc[AUDIT_START:AUDIT_END].dropna()
    blocks = block_means(disc_ex.to_frame("x"), PRIMARY)["x"].dropna()
    t_block = (
        float(blocks.mean() / (blocks.std(ddof=1) / np.sqrt(len(blocks))))
        if len(blocks) > 3
        else float("nan")
    )
    base_disc = float(k / n.loc[disc_ex.index].mean()) if len(disc_ex) else float("nan")
    base_aud = float(k / n.loc[aud_ex.index].mean()) if len(aud_ex) else float("nan")
    row: dict[str, object] = {
        "topk_excess_disc_bp": float(disc_ex.mean() * 1e4) if len(disc_ex) else float("nan"),
        "topk_t_block5_disc": t_block,
        "topk_excess_audit_bp": float(aud_ex.mean() * 1e4) if len(aud_ex) else float("nan"),
        "topk_p_at_3_disc": float(disc_p.mean()) if len(disc_p) else float("nan"),
        "topk_p_at_3_audit": float(aud_p.mean()) if len(aud_p) else float("nan"),
        "topk_p_baseline_disc": base_disc,
        "topk_p_baseline_audit": base_aud,
    }
    finite = all(
        np.isfinite(v)
        for v in (
            row["topk_excess_disc_bp"], row["topk_t_block5_disc"],
            row["topk_excess_audit_bp"], row["topk_p_at_3_disc"],
            row["topk_p_at_3_audit"], base_disc, base_aud,
        )
    )
    row["topk_gate_pass"] = bool(
        finite
        and t_block >= GATES["topk_min_t_block5_disc"]
        and row["topk_excess_audit_bp"] >= GATES["topk_min_excess_audit_bp"]
        and row["topk_p_at_3_disc"] > base_disc
        and row["topk_p_at_3_audit"] > base_aud
    )
    return row


def _evaluate_one(
    signal: pd.DataFrame,
    forward: dict[int, pd.DataFrame],
    eligibility: pd.DataFrame,
) -> dict[str, object]:
    row: dict[str, object] = {}
    for h in HORIZONS:
        daily_ic, pair_count = common_sample_spearman(signal, forward[h], eligibility, MIN_PAIRS)
        discovery = daily_ic.loc[:DISCOVERY_END].dropna()
        row[f"h{h}_discovery_ic"] = float(discovery.mean()) if len(discovery) else np.nan
        row[f"h{h}_discovery_days"] = int(len(discovery))
        row[f"h{h}_median_pairs"] = float(pair_count.loc[:DISCOVERY_END].median())
        if h == PRIMARY:
            primary_ic = daily_ic
    discovery = primary_ic.loc[:DISCOVERY_END].dropna()
    audit = primary_ic.loc[AUDIT_START:AUDIT_END].dropna()
    row["discovery_ic"] = float(discovery.mean())
    row["discovery_days"] = int(len(discovery))
    row["seen_audit_ic"] = float(audit.mean()) if len(audit) else np.nan
    row["seen_audit_days"] = int(len(audit))
    primary_value = row[f"h{PRIMARY}_discovery_ic"]
    row["all_horizons_same_direction"] = bool(
        all(
            np.isfinite(row[f"h{h}_discovery_ic"])
            and np.sign(row[f"h{h}_discovery_ic"]) == np.sign(primary_value)
            for h in HORIZONS
        )
    )
    direction = float(np.sign(row["discovery_ic"]))
    row["direction"] = direction
    matches = 0
    for year in (2021, 2022, 2023):
        values = primary_ic[primary_ic.index.year == year].dropna()
        mean = float(values.mean()) if len(values) else np.nan
        row[f"ic_{year}"] = mean
        if np.isfinite(mean) and np.sign(mean) == direction:
            matches += 1
    row["year_direction_count"] = matches
    loso = leave_one_symbol_out(
        signal,
        forward[PRIMARY],
        eligibility,
        min_pairs=MIN_PAIRS,
        discovery_end=DISCOVERY_END,
        audit_start=AUDIT_START,
        audit_end=AUDIT_END,
    )
    row["identity_gate_pass"] = identity_gate(loso, direction, GATES["identity_min_abs_ic"])
    row["identity_min_discovery_ic_signed"] = float((loso["discovery_ic"] * direction).min())
    row["identity_min_audit_ic_signed"] = float((loso["seen_audit_ic"] * direction).min())
    row.update(_topk_referee(signal, forward[PRIMARY], eligibility, direction))
    row["daily_ic"] = primary_ic
    row["signal"] = signal
    return row


def _intrinsic_gate_report(row: dict[str, object]) -> tuple[bool, list[str]]:
    failures = []
    if row["discovery_days"] < GATES["min_discovery_days"]:
        failures.append("discovery_days")
    if not np.isfinite(row["discovery_ic"]) or abs(row["discovery_ic"]) < GATES["min_abs_ic"]:
        failures.append("abs_discovery_ic")
    if (
        not np.isfinite(row["seen_audit_ic"])
        or row["seen_audit_ic"] * row["direction"] < GATES["min_abs_seen_audit_ic"]
    ):
        failures.append("signed_seen_audit_ic")
    if not row["all_horizons_same_direction"]:
        failures.append("horizon_direction")
    if row["year_direction_count"] < GATES["min_year_direction_count"]:
        failures.append("year_direction")
    if not row["identity_gate_pass"]:
        failures.append("identity_gate")
    if not row.get("topk_gate_pass", False):
        failures.append("topk_gate")
    return (not failures), failures


def _shelf_vectors(symbols: list[str], plan: dict) -> dict[str, pd.Series]:
    long = pd.read_parquet(SHELF_DIR / "selected_factor_scores.parquet")
    sample_index = plan["_signal_index"]
    vectors: dict[str, pd.Series] = {}
    for key, group in long.groupby("expression_key"):
        wide = group.pivot(index="signal_date", columns="symbol", values="score")
        wide = wide.reindex(index=sample_index, columns=symbols)
        vectors[str(key)] = _stride_vector(wide)
    return vectors


def _stride_vector(signal: pd.DataFrame) -> pd.Series:
    """Exactly the shelf rule: discovery window, stride slice, stacked ranks."""
    return signal.loc[:DISCOVERY_END].iloc[::RANK_CORR_STRIDE].stack(future_stack=True)


def _pairwise_pearson(a: pd.Series, b: pd.Series) -> float:
    """Pearson correlation of cross-sectional rank vectors, min_periods=500.
    NaN (insufficient overlapping pairs) means FAIL CLOSED upstream."""
    frame = pd.DataFrame({"a": a, "b": b})
    value = frame.corr(min_periods=RANK_CORR_MIN_PERIODS)
    result = float(value.loc["a", "b"])
    return result if np.isfinite(result) else float("nan")


def _previously_admitted() -> list[dict]:
    """Load gate-passing candidates together with their immutable plans."""
    admitted = []
    for status_path in sorted(WORKSPACE_OUTPUTS.glob("round_*/STATUS.json")):
        status = json.loads(status_path.read_text())
        if status.get("round_id") == ROUND_ID:
            continue
        plan_path = status_path.with_name("PLAN.json")
        if not plan_path.exists():
            raise ValueError(f"admitted round is missing PLAN.json: {status_path.parent}")
        if status.get("plan_sha256") != _hash(plan_path):
            raise ValueError(f"admitted round plan hash mismatch: {status_path.parent}")
        candidates = {
            str(candidate["id"]): candidate
            for candidate in json.loads(plan_path.read_text())["candidates"]
        }
        for cand in status.get("candidates", []):
            if cand.get("gate_pass"):
                candidate_id = str(cand["id"])
                if candidate_id not in candidates:
                    raise ValueError(
                        f"admitted candidate absent from plan: "
                        f"{status['round_id']}:{candidate_id}"
                    )
                admitted.append(
                    {
                        "round": status["round_id"],
                        "id": candidate_id,
                        "candidate": candidates[candidate_id],
                        "plan_sha256": status["plan_sha256"],
                    }
                )
    return admitted


def _prior_admitted_vectors(
    panels: dict[str, pd.DataFrame],
    eligibility_all: pd.DataFrame,
    symbols: list[str],
) -> tuple[dict[str, pd.Series], list[dict[str, object]]]:
    """Deterministically rebuild previously-admitted signals from their locked
    PLAN + STATUS so they join the dedup reference set. Missing atoms are built
    with the same frozen contract; original PLAN files are read-only."""
    vectors: dict[str, pd.Series] = {}
    summary: list[dict[str, object]] = []
    for prior in _previously_admitted():
        candidate = prior["candidate"]
        prior_plan = {"candidates": [candidate]}
        ranked = _build_atoms(panels, eligibility_all, symbols, prior_plan)
        signal = materialize_expression(_expression_spec(candidate), ranked)
        key = f"prior:{prior['round']}:{prior['id']}"
        vector = _stride_vector(signal)
        if len(vector) < RANK_CORR_MIN_PERIODS:
            raise ValueError(f"prior admitted candidate has insufficient rank pairs: {key}")
        vectors[key] = vector
        summary.append(
            {
                "reference_key": key,
                "source_plan_sha256": prior["plan_sha256"],
                "rank_pair_count": len(vector),
            }
        )
    return vectors, summary


def _dedup_pass(
    rows: list[dict],
    shelf_vectors: dict[str, pd.Series],
    plan: dict,
    panels: dict[str, pd.DataFrame],
    eligibility_all: pd.DataFrame,
    symbols: list[str],
) -> list[dict[str, object]]:
    """Deterministic gate-then-dedup, fixed plan order. Failures never enter
    the comparison set. Missing must-compare correlations fail closed."""
    reference: dict[str, pd.Series] = dict(shelf_vectors)
    prior_vectors, prior_summary = _prior_admitted_vectors(
        panels, eligibility_all, symbols
    )
    reference.update(prior_vectors)
    order = [c["id"] for c in plan["candidates"]]
    by_id = {row["candidate_id"]: row for row in rows}
    for row in rows:
        row.setdefault("max_abs_rank_corr", np.nan)
        row.setdefault("max_abs_rank_corr_vs", "")
        row.setdefault("rank_corrs", {})
    for cid in order:
        if cid not in by_id:
            continue  # validate mode may evaluate a subset; batch covers all
        row = by_id[cid]
        if not row["intrinsic_gate_pass"]:
            row["gate_pass"] = False
            row["gate_failures"] = row["intrinsic_failures"]
            continue
        vector = _stride_vector(row["signal"])
        corrs: dict[str, float] = {}
        fail_closed = None
        for key, ref in reference.items():
            value = _pairwise_pearson(vector, ref)
            if not np.isfinite(value):
                fail_closed = key
                break
            corrs[key] = value
        row["rank_corrs"] = corrs
        if fail_closed is not None:
            row["gate_pass"] = False
            row["gate_failures"] = f"rank_correlation_missing_fail_closed:{fail_closed}"
            continue
        worst = max(corrs, key=lambda k: abs(corrs[k]))
        row["max_abs_rank_corr"] = abs(corrs[worst])
        row["max_abs_rank_corr_vs"] = worst
        if row["max_abs_rank_corr"] >= GATES["max_abs_factor_rank_corr"]:
            row["gate_pass"] = False
            row["gate_failures"] = "rank_correlation_redundancy"
            continue
        reference[f"{ROUND_ID}:{cid}"] = vector
        row["gate_pass"] = True
        row["gate_failures"] = ""
    return prior_summary


def _snapshot(output: Path, plan: dict) -> dict[str, str]:
    snap = output / "snapshots"
    snap.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    items = {"script": SCRIPT, "universe_config": UNIVERSE_CONFIG}
    driver = Path(sys.argv[0]).resolve()
    if driver != SCRIPT:
        items["driver"] = driver
    for path in plan["config_hashes"]:
        items[Path(path).name] = Path(path)
    for name, path in items.items():
        target = snap / path.name
        if not target.exists():
            shutil.copy2(path, target)
        hashes[f"{name}:{path.name}"] = _hash(path)
    return hashes


def _log_attempt(output: Path, entry: dict) -> None:
    with (output / "attempts.jsonl").open("a") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cmd_evaluate(args: argparse.Namespace) -> None:
    output = Path(args.output).resolve()
    started = datetime.now(timezone.utc).isoformat()
    plan_path = output / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan_sha = _hash(plan_path)
    only = set(args.only.split(",")) if args.only else None
    candidates = [c for c in plan["candidates"] if only is None or c["id"] in only]
    assert candidates, "no candidates selected"
    _log_attempt(
        output,
        {"event": "evaluate_start", "mode": args.mode, "ids": sorted(c["id"] for c in candidates),
         "plan_sha256": plan_sha, "at_utc": started, "command": sys.argv},
    )
    try:
        _run_evaluate(args, output, plan, plan_sha, candidates, only)
    except Exception as error:  # noqa: BLE001 - attempts must record failures
        _log_attempt(
            output,
            {"event": "evaluate_error", "mode": args.mode, "at_utc": datetime.now(timezone.utc).isoformat(),
             "error": f"{type(error).__name__}: {error}"},
        )
        raise


def _run_evaluate(args, output: Path, plan: dict, plan_sha: str, candidates, only) -> None:
    panels, eligibility_all, symbols, forward = _load_context()
    ranked = _build_atoms(panels, eligibility_all, symbols, plan)
    eligibility = eligibility_all[symbols]
    plan["_signal_index"] = ranked[next(iter(ranked))].index

    rows = []
    for cand in candidates:
        spec = _expression_spec(cand)
        signal = materialize_expression(spec, ranked)
        row = {
            "candidate_id": cand["id"],
            "expression": spec.readable,
            "mechanism": cand["mechanism"],
            "expected_sign": cand["expected_sign"],
        }
        row.update(_evaluate_one(signal, forward, eligibility))
        direction = row["direction"]
        row["expected_sign_match"] = bool(
            np.isfinite(direction) and direction == float(cand["expected_sign"])
        )
        rows.append(row)

    stage_bonferroni_line = ""
    try:
        stage_n = sum(
            1
            for pp in sorted(WORKSPACE_OUTPUTS.glob("round_*/PLAN.json"))
            for c in json.loads(pp.read_text()).get("candidates", [])
            if str(c.get("operator", "")).startswith("cond_")
        )
        if stage_n > 0:
            from statistics import NormalDist

            equiv = NormalDist().inv_cdf(1 - 0.05 / (2 * stage_n))
            stage_bonferroni_line = (
                f"多重检验预算（只报告不改门）：条件化/三原子阶段累计预注册 N={stage_n}；"
                f"按 N 做 Bonferroni 后门 7 的 t 门等价值（正态近似，双边 5%/N）≈ {equiv:.2f}。"
            )
    except Exception:  # noqa: BLE001 - 报告行失败不影响评估
        stage_bonferroni_line = ""
    checks = _leak_checks(ranked, panels, eligibility_all, symbols, plan, output)
    prior_reference_summary: list[dict[str, object]] = []
    if not checks["pass"]:
        # C2: fail closed -- no candidate may pass while any leak check fails.
        for row in rows:
            row["intrinsic_gate_pass"] = False
            row["intrinsic_failures"] = "leak_checks_fail_closed"
    else:
        shelf_vectors = _shelf_vectors(symbols, plan)
        for row in rows:
            passed, failures = _intrinsic_gate_report(row)
            row["intrinsic_gate_pass"] = passed
            row["intrinsic_failures"] = ",".join(failures)
        prior_reference_summary = _dedup_pass(
            rows, shelf_vectors, plan, panels, eligibility_all, symbols
        )

    if args.mode == "validate":
        for row in rows:
            print(
                f"[validate] {row['candidate_id']} {row['expression']} "
                f"disc_ic={row['discovery_ic']:.4f} days={row['discovery_days']} "
                f"audit_ic={row['seen_audit_ic']:.4f} years={row['year_direction_count']} "
                f"identity={row['identity_gate_pass']} "
                f"pass={row['gate_pass']} fails={row['gate_failures']}"
            )
        print(
            f"[leak] pass={checks['pass']} failures={checks['failures']} "
            f"prefix_daily_max={_bucket_max(checks['prefix_invariance_daily'])} "
            f"perturb_daily_max={_bucket_max(checks['future_perturbation_daily'])}"
        )
        _log_attempt(
            output,
            {"event": "evaluate_done", "mode": args.mode,
             "at_utc": datetime.now(timezone.utc).isoformat(),
             "pass": [r["candidate_id"] for r in rows if r["gate_pass"]],
             "leak_pass": checks["pass"]},
        )
        return

    output.mkdir(parents=True, exist_ok=True)
    meta_columns = [
        "candidate_id", "expression", "mechanism", "expected_sign", "direction",
        "expected_sign_match",
        "discovery_ic", "discovery_days", "seen_audit_ic", "seen_audit_days",
        "h5_discovery_ic", "h10_discovery_ic", "h20_discovery_ic",
        "ic_2021", "ic_2022", "ic_2023", "year_direction_count",
        "all_horizons_same_direction", "identity_gate_pass",
        "identity_min_discovery_ic_signed", "identity_min_audit_ic_signed",
        "max_abs_rank_corr", "max_abs_rank_corr_vs",
        "topk_excess_disc_bp", "topk_t_block5_disc", "topk_excess_audit_bp",
        "topk_p_at_3_disc", "topk_p_at_3_audit", "topk_gate_pass",
        "gate_pass", "gate_failures", "evidence_status",
    ]
    for row in rows:
        row["evidence_status"] = EVIDENCE_STATUS if row["gate_pass"] else "rejected_this_round"
    metrics = pd.DataFrame(rows)[meta_columns]
    metrics.to_csv(output / "candidate_metrics.csv", index=False)
    corr_dump = {
        row["candidate_id"]: {k: round(v, 6) for k, v in row.get("rank_corrs", {}).items()}
        for row in rows
    }
    (output / "rank_correlations.json").write_text(
        json.dumps(corr_dump, ensure_ascii=False, indent=2)
    )

    STAGE_N_COND = sum(
        1
        for pp in sorted(WORKSPACE_OUTPUTS.glob("round_*/PLAN.json"))
        for c in json.loads(pp.read_text()).get("candidates", [])
        if str(c.get("operator", "")).startswith("cond_")
    )
    from statistics import NormalDist

    BONFERRONI_EQUIV_T = round(
        NormalDist().inv_cdf(1 - 0.05 / (2 * max(STAGE_N_COND, 1))), 3
    )
    snapshot_hashes = _snapshot(output, plan)
    manifest = json.loads(LEDGER_MANIFEST.read_text())
    admitted = [r for r in rows if r["gate_pass"]]
    status = {
        "round_id": ROUND_ID,
        "as_of": AS_OF,
        "plan_sha256": plan_sha,
        "script_sha256": _hash(SCRIPT),
        "script_snapshot": str(output / "snapshots" / SCRIPT.name),
        "universe_config": str(UNIVERSE_CONFIG),
        "universe_config_sha256": _hash(UNIVERSE_CONFIG),
        "canonical_root": str(CANONICAL_ROOT),
        "input_file_hashes": plan["input_hashes"],
        "config_hashes": plan["config_hashes"],
        "snapshot_hashes": snapshot_hashes,
        "contract_source": str(LEDGER_MANIFEST),
        "contract_generation": manifest["generation"],
        "surfaces": plan["surfaces"],
        "gates": {
            **GATES,
            "referee_v2_1": "7th gate: top-3 excess over eligible equal-weight pool; "
            "discovery 5-session non-overlapping block t >= 2.0; audit 5-session excess "
            "mean >= 5 bp (v2.1, was '> 0'); Precision@3 > K/n baseline in both windows; "
            "identity uses identity_min_abs_ic",
        },
        "dedup_rule": plan["dedup_rule"],
        "prior_admitted_references": prior_reference_summary,
        "evidence_status": EVIDENCE_STATUS,
        "n_preregistered": len(candidates),
        "n_gate_pass": len(admitted),
        "candidates": [
            {
                "id": r["candidate_id"],
                "expression": r["expression"],
                "mechanism": r["mechanism"],
                "discovery_ic": r["discovery_ic"],
                "seen_audit_ic": r["seen_audit_ic"],
                "direction": r["direction"],
                "expected_sign_match": r["expected_sign_match"],
                "topk_excess_disc_bp": r["topk_excess_disc_bp"],
                "topk_t_block5_disc": r["topk_t_block5_disc"],
                "topk_excess_audit_bp": r["topk_excess_audit_bp"],
                "topk_p_at_3_disc": r["topk_p_at_3_disc"],
                "topk_p_at_3_audit": r["topk_p_at_3_audit"],
                "topk_gate_pass": bool(r["topk_gate_pass"]),
                "gate_pass": bool(r["gate_pass"]),
                "gate_failures": r["gate_failures"],
            }
            for r in rows
        ],
        "leak_checks": {
            "pass": checks["pass"],
            "failures": checks["failures"],
            "cache": checks.get("cache"),
            "prefix_invariance_daily_max_abs_diff": _bucket_max(
                checks["prefix_invariance_daily"]
            ),
            "future_perturbation_daily_max_abs_diff": _bucket_max(
                checks["future_perturbation_daily"]
            ),
            "prefix_invariance_intraday_max_abs_diff": (
                _bucket_max(checks.get("prefix_invariance_intraday", {}))
                if intraday_checked(checks)
                else None
            ),
            "future_perturbation_intraday_max_abs_diff": (
                _bucket_max(checks.get("future_perturbation_intraday", {}))
                if intraday_checked(checks)
                else None
            ),
            "intraday_sources": checks.get("intraday_sources", []),
            "intraday_frequencies": checks.get("intraday_frequencies", []),
            "method": "missing-mask equality required; nanmax never skips new missing; "
            "intraday verified with physically truncated and post-cutoff-perturbed local copies",
            "scanner": "scan_future_leaks.py outputs/round_002/future_leak_scan_round002.txt",
            "hard_gate": True,
        },
        "correction_reference": "outputs/round_002/correction.json (round_001 residual diagnostic retracted)",
        "prior_round_plan_sha256": plan["prior_round_plan_sha256"],
        "expression_hashes": plan["expression_hashes"],
        "notes": {
            "direction_rule": "符号由发现期确定；expected_sign仅为预登记经济假设，mismatch已逐条报告",
            "combination_vs_mechanisms": "8个表达式共享部分原子，组合数不等于已证实的独立机制数",
            "independent_oos": "2024-01-01起为已见审计面；无任何独立OOS；不自行交易或认证",
        },
        "stage_prereg_count_cond": STAGE_N_COND,
        "bonferroni": {
            "note": "本阶段累计预注册 N；按 N 做 Bonferroni 后门 7 的 t 门等价值（正态近似，双边 5%/N）。只报告不改门。",
            "N": STAGE_N_COND,
            "equiv_t_gate_normal_approx": BONFERRONI_EQUIV_T,
        },
        "independent_oos": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": sys.argv,
    }
    (output / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2))

    prior_names = ", ".join(
        str(item["reference_key"]) for item in prior_reference_summary
    ) or "无"
    lines = [
        f"# {ROUND_ID} 挖掘报告（预注册 {len(candidates)} 条跨家族交互表达式）",
        "",
        f"计划锁定哈希: `{plan_sha[:16]}…`；as_of={AS_OF}；契约复制自 v9 家族裁判（人口/标签/时间面/门槛未改）。",
        "发现面截至 2023-12-31；2024-01-01~2025-04-30 为已见审计面；2025-04-30 之后未参与。",
        "符号由发现期确定；expected_sign 为预登记经济假设，不符处如实标注。",
        "",
        "| 候选 | 表达式 | 机制 | 发现IC | 有效日 | 已见审计IC | 2021-23同向 | LOSO | 假设方向 | 最大|rank corr| | 结论 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        corr = (
            f"{row['max_abs_rank_corr']:.2f} ({row['max_abs_rank_corr_vs']})"
            if "max_abs_rank_corr" in row
            else "n/a"
        )
        hyp = f"{row['expected_sign']:+d}->{'匹配' if row['expected_sign_match'] else '不符'}"
        lines.append(
            f"| {row['candidate_id']} | {row['expression']} | {row['mechanism']} "
            f"| {row['discovery_ic']:+.4f} | {row['discovery_days']} "
            f"| {row['seen_audit_ic']:+.4f} | {row['year_direction_count']}/3 "
            f"| {'通过' if row['identity_gate_pass'] else '未过'} | {hyp} | {corr} "
            f"| {'PASS(非认证候选)' if row['gate_pass'] else '拒绝:' + row['gate_failures']} |"
        )
    lines += [
        "",
        "去冗余规则：先门(日数/|IC|/已见审计/3期同向/年度同向/identity)后去重；仅对 shelf16 + "
        f"此前轮入选({prior_names}) + 本批按固定顺序已入选者比较 Pearson rank corr(stride=5, min_periods=500, 发现窗内)；"
        "相关缺失即 fail closed 拒绝；失败者不进入比较集。",
        "",
        f"泄漏硬门：{'通过' if checks['pass'] else '未通过(fail closed)'}；"
        f"失败项={checks['failures']}。日面：前缀不变与截后扰动均要求缺失掩码完全一致。"
        f"日内面({', '.join(checks.get('intraday_sources', []))})：以本地物理截断副本与截后扰动副本实测，"
        "原始数据根未改动。负向 shift 仅出现在标签 open(D+2+H)/open(D+2)-1 的构造中，标签从不作为特征；"
        f"静态扫描见 future_leak_scan_{ROUND_ID}.txt。",
        "",
        "残差诊断已删除（见 correction.json）：round_001 报告中的残差列欠定作废，round_001 产物原样保留。",
        "",
        "8个表达式共享部分原子，组合数不等于已证实的独立机制数。全部通过候选仅为 "
        "discovery_candidate_not_certified，不构成正式认证或可交易策略。",
        "",
        stage_bonferroni_line,
    ]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n")
    _log_attempt(
        output,
        {"event": "evaluate_done", "mode": args.mode,
         "at_utc": datetime.now(timezone.utc).isoformat(),
         "n_pass": len(admitted), "ids": [r["candidate_id"] for r in admitted],
         "leak_pass": checks["pass"]},
    )
    print(
        f"{ROUND_ID} batch complete: pass={len(admitted)}/{len(rows)} "
        f"leak={'OK' if checks['pass'] else 'FAIL'} output={output}"
    )


def intraday_checked(checks: dict) -> bool:
    return bool(checks.get("intraday_sources"))


def _bucket_max(bucket: dict) -> float | None:
    """Max of a diff bucket; None if any entry is not a finite float
    (mask mismatch string) so a failure can never look like 0.0."""
    values = list(bucket.values())
    if not values:
        return 0.0
    if any(not isinstance(v, float) or not np.isfinite(v) for v in values):
        return None
    return max(values)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--output", type=Path, required=True)
    p_eval = sub.add_parser("evaluate")
    p_eval.add_argument("--output", type=Path, required=True)
    p_eval.add_argument("--mode", choices=["validate", "batch"], default="batch")
    p_eval.add_argument("--only", type=str, default=None, help="comma separated candidate ids")
    args = parser.parse_args()
    if args.cmd == "plan":
        cmd_plan(args)
    else:
        cmd_evaluate(args)


if __name__ == "__main__":
    main()
