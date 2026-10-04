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
      gate). Direction is the preregistered expected_sign; the discovery sign
      is reported but never used to choose the tested tail.

Sub-commands:
  plan      write PLAN.json (preregistration lock, before any evaluation)
  evaluate  read PLAN.json; --mode validate runs one candidate end-to-end
            (including hard leak gates); --mode batch evaluates all.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
from etf_strategy.core.etf_family_referee import common_sample_spearman
from etf_strategy.core.etf_identity import identity_gate, matched_leave_one_symbol_out
from etf_strategy.core.etf_mining_campaign import (
    verify_plan_seal,
    write_plan_seal,
    write_plan_with_budget,
)
from etf_strategy.core.etf_mining_referee import (
    block_t,
    block_t_calendar,
    campaign_bonferroni_pass,
    newey_west_t,
    newey_west_t_calendar,
    paired_increment_stats,
    purge_by_exit,
    topk_series,
)
from etf_strategy.core.family_registry import load_builtin_families, resolve_family

CANONICAL_ROOT = Path(str(Path(__file__).resolve().parents[6] / "data/etf_rotation_v1"))
CORAL_PROJECT = Path(str(Path(__file__).resolve().parents[6]))
UNIVERSE_CONFIG = CORAL_PROJECT / "config/etf_rotation_universe_v1.json"
SHELF_DIR = CORAL_PROJECT / "runtime_outputs/etf_ic_factor_shelf_v11_20260919"
LEDGER_MANIFEST = (
    CORAL_PROJECT / "runtime_outputs/etf_family_multisource_v9_20260919/run_manifest.json"
)
WORKSPACE_OUTPUTS = ROOT.parents[1] / "outputs"  # workspace/outputs
CAMPAIGN_OUTPUT_ROOTS = (
    CORAL_PROJECT / "runtime_outputs/etf_pi_glm_mining_20260919/workspace/outputs",
    CORAL_PROJECT / "runtime_outputs/etf_sonnet_mining_20260920/workspace/outputs",
)
CAMPAIGN_LOCK = CORAL_PROJECT / "runtime_outputs/etf_mining_campaign_v4.lock"

ROUND_ID = "round_002"
AS_OF = "2026-09-17"
DISCOVERY_END = pd.Timestamp("2023-12-31")
# fix A (2026-09-21): the discovery window opens on the first session with >= MIN_PAIRS eligible names
# (data-derived in _load_context; 2021-08-09 on the current panel). Sessions before it never enter
# discovery statistics, and the year-direction gate only counts years with >= 120 valid IC days.
DISCOVERY_START = pd.Timestamp("2000-01-01")  # overwritten by _load_context
YEAR_GATE_MIN_DAYS = 120
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
    "identity_min_discovery_ic": 0.01,   # 2026-09-21: discovery side also needs the magnitude floor
    "min_year_direction_count": 2,
    "max_abs_factor_rank_corr": 0.70,
    "topk_k": 3,
    "topk_min_t_block5_disc": 2.0,
    "topk_min_excess_audit_bp": 5.0,
    "topk_min_t_audit": 2.0,
    "campaign_alpha": 0.05,
    "campaign_hypothesis_budget": 6000,
    "leg_increment_min_t_disc": 2.0,
    "leg_increment_min_t_audit": 1.5,
    "leg_increment_min_audit_bp": 0.0,
    "pair_base_shadow_max_corr": 0.60,
}
# Referee fixes 2026-09-21 (USER-approved, order I -> C -> D -> B):
#   I  top-K weights: names strictly above the K-th value get weight 1, names tied at the boundary share the
#      remainder equally (weights sum to K) -> no dependence on universe column order.
#   C  block length = max(PRIMARY, H) for every horizon (non-overlapping blocks); HAC (Newey-West, lag H-1) t
#      reported alongside.
#   D  direction = preregistered expected_sign; a fixed 6,000-hypothesis campaign budget controls discovery tests.
#   B  audit leg: block/HAC t >= topk_min_t_audit AND excess >= topk_min_excess_audit_bp.
REFEREE_VERSION = "v4.3_20260921"  # semantics changed vs v4 (purged year gate, calendar blocks, D-known selection); v4/v4.1 admissions are not same-version references
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


_SOURCE_TREE_HASH: dict[str, str] = {}


def _python_tree_hash(refresh: bool = False) -> str:
    if refresh:
        _SOURCE_TREE_HASH.pop("value", None)   # P0 (Codex): end-of-run verification must re-hash the tree
    if "value" in _SOURCE_TREE_HASH:
        return _SOURCE_TREE_HASH["value"]
    digest = hashlib.sha256()
    source_root = ROOT / "src/etf_strategy"
    for path in sorted(source_root.rglob("*.py")):
        digest.update(str(path.relative_to(source_root)).encode())
        digest.update(path.read_bytes())
    _SOURCE_TREE_HASH["value"] = digest.hexdigest()
    return _SOURCE_TREE_HASH["value"]


def _write_plan_with_campaign_budget(plan_path: Path, plan: dict) -> int:
    """Reserve campaign tests and write PLAN while holding one cross-lane lock."""
    return write_plan_with_budget(
        plan_path,
        plan,
        output_roots=CAMPAIGN_OUTPUT_ROOTS,
        lock_path=CAMPAIGN_LOCK,
        budget=int(GATES["campaign_hypothesis_budget"]),
    )


CACHE_DIR = ROOT.parents[1] / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
# item 5 (2026-09-21): caches written during a run stay ".pending" until the run contract is
# re-verified at the end; a failed run leaves no cache and no STATUS.
_PENDING_CACHE: list[tuple[Path, Path]] = []


def _pending_path(final: Path) -> Path:
    return final.with_name(final.name + f".pending.{os.getpid()}")


def _finalize_pending_caches() -> int:
    n = 0
    for tmp, final in _PENDING_CACHE:
        if tmp.exists():
            os.replace(tmp, final); n += 1
    _PENDING_CACHE.clear()
    return n


def _discard_pending_caches() -> int:
    n = 0
    for tmp, _final in _PENDING_CACHE:
        if tmp.exists():
            tmp.unlink(); n += 1
    _PENDING_CACHE.clear()
    return n


def _locked_input_fingerprint(plan: dict) -> str:
    input_hashes = plan.get("input_hashes")
    if not isinstance(input_hashes, dict) or not input_hashes:
        raise ValueError("PLAN is missing locked input content hashes")
    payload = json.dumps(input_hashes, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _atom_cache_path(data_fp: str, cfg_hash: str, name: str, sym_key: str) -> Path:
    key = hashlib.sha256(
        f"{data_fp}|{cfg_hash}|{_python_tree_hash()}|{name}|{AS_OF}|{sym_key}|rank_v2".encode()
    ).hexdigest()
    cp = CACHE_DIR / "atoms" / f"{key}.parquet"
    cp.parent.mkdir(parents=True, exist_ok=True)
    return cp


def _leak_cache_path(data_fp: str, cfg_hash: str, name: str, sym_key: str) -> Path:
    key = hashlib.sha256(
        f"{data_fp}|{cfg_hash}|{_python_tree_hash()}|{name}|{AS_OF}|{sym_key}|leak_v3".encode()
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


def _campaign_plan_paths() -> list[Path]:
    paths: list[Path] = []
    for root in CAMPAIGN_OUTPUT_ROOTS:
        paths.extend(
            path for path in root.glob("round_*/PLAN.json")
            if re.fullmatch(r"round_\d+", path.parent.name)
        )
    return sorted(paths)


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
    for plan_path in _campaign_plan_paths():
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
    stop_path = WORKSPACE_OUTPUTS.parents[1] / "STOP"
    if stop_path.exists():
        raise SystemExit(f"mining lane is frozen by {stop_path}; use a forward-only protocol")
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
        assert cand["operator"] in {
            "atomic", "rank_mean", "rank_spread", "rank_interaction",
        }, f"{cand['id']} uses an operator unsupported by the current ETF grammar"
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
        # "1d"/"adj_factor" are symlinked below as shared context; they must never be
        # collected as frequencies or the writer below would write THROUGH the symlink
        # into CANONICAL_ROOT (E23, 2026-09-20: 14 raw 1d files truncated to 2023-12-29).
        if mining.get("frequency") and str(mining["frequency"]) not in ("1d", "adj_factor"):
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
        if cand["operator"] == "atomic":
            continue  # single-atom readjudication: left==right by construction
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
            "C5": "契约冻结；检验方向只取预登记 expected_sign；发现期符号只报告",
        },
        "as_of": AS_OF,
        "data_root": str(CANONICAL_ROOT),
        "universe_config": str(universe_config),
        "universe_source": "原项目 run_manifest.json 的 command 字段程序化读取",
        "population_limit": {
            "selected_with_current_knowledge": True,
            "survivorship_controlled": False,
            "external_validity": False,
        },
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
            "referee_v4": "top-3 excess; fixed expected_sign; fractional tie weights; "
            "discovery campaign Bonferroni plus block/HAC t; audit mean>=5bp plus "
            "block/HAC t>=2; paired leg increment; base-shadow controls",
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
        "engine_hashes": {
            "base_script": _hash(SCRIPT),
            "driver": _hash(Path(sys.argv[0]).resolve()),
            "python_tree": _python_tree_hash(),
        },
        "expression_hashes": {c["id"]: expression_hash(c) for c in CANDIDATES},
        "expression_canonical": {c["id"]: canonical_expression(c) for c in CANDIDATES},
        "evidence_status": EVIDENCE_STATUS,
        "shelf_reference": {
            "path": str(SHELF_DIR),
            "candidates": len(pd.read_csv(SHELF_DIR / "IC_FACTOR_SHELF.csv")),
            "scores_sha256": _hash(SHELF_DIR / "selected_factor_scores.parquet"),
            "catalog_sha256": _hash(SHELF_DIR / "IC_FACTOR_SHELF.csv"),
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
    campaign_used = _write_plan_with_campaign_budget(plan_path, plan)
    print(
        f"PLAN locked: {plan_path} (candidates={len(plan['candidates'])}, "
        f"campaign_used={campaign_used}/{GATES['campaign_hypothesis_budget']})"
    )


def _expression_spec(cand: dict) -> ExpressionSpec:
    return ExpressionSpec(
        cand["operator"],
        cand["left"]["name"],
        cand["right"]["name"] if cand["operator"] != "atomic" else None,
        family="+".join(sorted({cand["left"]["family"], cand["right"]["family"]})),
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
    global DISCOVERY_START
    enough = eligibility.sum(axis=1) >= MIN_PAIRS
    DISCOVERY_START = pd.Timestamp(enough[enough].index.min()) if enough.any() else DISCOVERY_START
    forward = {
        h: _raw_forward(panels["open"][symbols], h, LAG).where(eligibility) for h in HORIZONS
    }
    return panels, eligibility, symbols, forward


def _build_atoms(
    panels, eligibility_all: pd.DataFrame, symbols: list[str], plan: dict,
    data_root: Path = CANONICAL_ROOT, sources_filter: set[str] | None = None,
    use_cache: bool = True,
) -> dict[str, pd.DataFrame]:
    load_builtin_families()
    needed: dict[str, set[str]] = {}
    for cand in plan["candidates"]:
        for side in ("left", "right"):
            slot = cand[side]
            needed.setdefault(slot["source"], set()).add(slot["name"])
    ranked: dict[str, pd.DataFrame] = {}
    sym_key = "|".join(symbols)
    data_fp = _locked_input_fingerprint(plan)
    for source, names in sorted(needed.items()):
        if sources_filter is not None and source not in sources_filter:
            continue
        cfg = _config_path(source)
        cfg_hash = _hash(cfg)
        mining = yaml.safe_load(cfg.read_text())
        remaining = []
        for name in sorted(names):
            cp = _atom_cache_path(data_fp, cfg_hash, name, sym_key)
            if use_cache and cp.exists():
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
            if use_cache:
                final = _atom_cache_path(data_fp, cfg_hash, name, sym_key)
                tmp = _pending_path(final)
                ranked[name].to_parquet(tmp)
                _PENDING_CACHE.append((tmp, final))
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


def _temp_subdir_root(subdir_sources, symbols, mode, workdir):
    """Physical PIT copies of declared data subdirs (e.g. fund_share/nav):
    trunc -> keep only usable_from_date <= DISCOVERY_END rows;
    perturb -> noise on numeric values of rows with usable_from_date > cutoff."""
    subdirs = set()
    for s in subdir_sources:
        mining = yaml.safe_load(_config_path(s).read_text())
        subdirs.update(mining.get("data_subdirs", []))
    root = workdir / f"subdirs_{mode}"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    rng = np.random.default_rng(20260919)
    date_like = {"usable_from_date", "trade_date", "nav_date", "ann_date", "datetime"}
    str_like = {"ts_code", "source", "downloaded_at"}
    for sub in sorted(subdirs):
        out_dir = root / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        _assert_scratch_dir(out_dir)
        for path in sorted((CANONICAL_ROOT / sub).glob("*.parquet")):
            frame = pd.read_parquet(path)
            u = pd.to_datetime(frame["usable_from_date"])
            if mode == "trunc":
                frame = frame.loc[u <= DISCOVERY_END].copy()
            else:
                mask_rows = (u > DISCOVERY_END).to_numpy()
                numeric = [
                    c
                    for c in frame.columns
                    if c not in date_like | str_like
                    and pd.api.types.is_numeric_dtype(frame[c])
                ]
                frame = frame.copy()
                if mask_rows.any() and numeric:
                    arr = frame[numeric].astype(float).to_numpy(copy=True)
                    noise = 1.0 + rng.normal(0.0, 0.05, size=(int(mask_rows.sum()), len(numeric)))
                    arr[mask_rows] = arr[mask_rows] * noise
                    frame[numeric] = arr
            frame.to_parquet(out_dir / path.name)
    return root


def _assert_scratch_dir(out_dir: Path) -> None:
    """Leak-gate copies are written to scratch only. Refuse any target that is a symlink
    or resolves inside CANONICAL_ROOT (E23: a 1d symlink + a 1d-frequency family let the
    truncated copies overwrite the canonical raw 1d files)."""
    if out_dir.is_symlink():
        raise RuntimeError(f"leak-gate refuses to write through symlink: {out_dir}")
    r = out_dir.resolve()
    c = Path(CANONICAL_ROOT).resolve()
    if r == c or c in r.parents:
        raise RuntimeError(f"leak-gate refuses to write inside CANONICAL_ROOT: {r}")


def _temp_intraday_root(
    sources: list[str], symbols: list[str], mode: str, workdir: Path
) -> tuple[Path, set[str]]:
    """Build a local temp data root with PHYSICALLY truncated (mode=trunc) or
    post-cutoff-perturbed (mode=perturb) copies of the intraday files used by
    the plan. Original data root is never modified."""
    frequencies: set[str] = set()
    benchmark_symbols: set[str] = set()
    for source in sources:
        mining = yaml.safe_load(_config_path(source).read_text())
        # "1d" is symlinked below as shared (non-truncated) context: daily
        # atoms read the as_of-frozen canonical panels, so physical 1d
        # truncation copies would break the canonical loader without adding
        # leak protection (1d-family builders have no data_root path deps).
        if mining.get("frequency") and str(mining["frequency"]) not in ("1d", "adj_factor"):
            frequencies.add(str(mining["frequency"]))
        # reference-leg symbols (e.g. 510300.SH/510500.SH for benchmark_leadlag
        # families) must exist in the temp root or the family's builder would
        # see an empty benchmark and produce all-NaN atoms -> false leak alarm
        benchmark_symbols.update(str(b) for b in mining.get("benchmark_symbols", []))
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
        _assert_scratch_dir(out_dir)
        for symbol in sorted(set(symbols) | benchmark_symbols):
            path = CANONICAL_ROOT / frequency / f"{symbol}.parquet"
            if not path.exists():
                continue
            frame = pd.read_parquet(path)
            # daily files carry trade_date; intraday files carry datetime
            date_col = (
                "datetime" if "datetime" in frame.columns
                else ("trade_date" if "trade_date" in frame.columns else "date")
            )
            dates = pd.to_datetime(frame[date_col]).dt.normalize()
            if mode == "trunc":
                frame = frame.loc[dates <= DISCOVERY_END].copy()
            elif mode == "perturb":
                mask_rows = (dates > DISCOVERY_END).to_numpy()
                numeric = [
                    c
                    for c in frame.columns
                    if c != date_col and pd.api.types.is_numeric_dtype(frame[c])
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


_orig_build = _build_atoms


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
    data_fp = _locked_input_fingerprint(plan)

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
        trunc_atoms = _build_atoms(trunc_panels, trunc_elig, symbols, plan, use_cache=False)
        rng = np.random.default_rng(20260919)
        pert_panels = {k: v.copy() for k, v in panels.items()}
        for frame in pert_panels.values():
            rows = frame.index > DISCOVERY_END
            frame.loc[rows] = frame.loc[rows] * (
                1.0 + rng.normal(0.0, 0.05, size=(int(rows.sum()), frame.shape[1]))
            )
        pert_elig = build_pit_eligibility(pert_panels, MIN_HISTORY, True)
        pert_atoms = _build_atoms(pert_panels, pert_elig, symbols, plan, use_cache=False)

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
                use_cache=False,
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
                use_cache=False,
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

    # (e)+(f) primary-market data (fund_share/nav): physical PIT copies.
    subdir_sources = [
        s
        for s in sources
        if yaml.safe_load(_config_path(s).read_text()).get("data_subdirs")
    ]
    results["subdir_sources"] = subdir_sources
    if subdir_sources:
        sub_to_compute = [n for n in to_compute if atom_source[n] in subdir_sources]
        results["subdir_cache"] = {
            "computed": len(sub_to_compute),
            "cached": len(to_compute) - len(sub_to_compute),
        }
        results["prefix_invariance_subdir"] = {}
        results["future_perturbation_subdir"] = {}
        if sub_to_compute:
            sub_plan = {
                **plan,
                "candidates": [
                    c
                    for c in plan["candidates"]
                    if c["left"]["source"] in subdir_sources
                    or c["right"]["source"] in subdir_sources
                ],
            }
            trunc_root = _temp_subdir_root(subdir_sources, symbols, "trunc", workdir)
            trunc_s_atoms = _orig_build(
                panels, eligibility_all, symbols, sub_plan, data_root=trunc_root, use_cache=False
            )
            pert_root = _temp_subdir_root(subdir_sources, symbols, "perturb", workdir)
            pert_s_atoms = _orig_build(
                panels, eligibility_all, symbols, sub_plan, data_root=pert_root, use_cache=False
            )
            for name in sub_to_compute:
                if name not in trunc_s_atoms:
                    continue
                record(
                    "prefix_subdir",
                    results["prefix_invariance_subdir"],  # type: ignore[arg-type]
                    name,
                    _masked_max_abs_diff(ranked[name], trunc_s_atoms[name], prefix_index),
                )
                record(
                    "perturb_subdir",
                    results["future_perturbation_subdir"],  # type: ignore[arg-type]
                    name,
                    _masked_max_abs_diff(ranked[name], pert_s_atoms[name], prefix_index),
                )
            shutil.rmtree(trunc_root, ignore_errors=True)
            shutil.rmtree(pert_root, ignore_errors=True)

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
            ("prefix_invariance_subdir", "prefix_subdir"),
            ("future_perturbation_subdir", "perturb_subdir"),
        ):
            value = results.get(bucket, {}).get(name)
            if isinstance(value, float):
                record_out[key] = value
        cp = _leak_cache_path(data_fp, _hash(_config_path(source)), name, sym_key)
        cp.parent.mkdir(parents=True, exist_ok=True)
        tmp = _pending_path(cp)                     # P1 (Codex): leak cache is two-phase too
        tmp.write_text(json.dumps(record_out))
        _PENDING_CACHE.append((tmp, cp))

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
    """V4 referee: fixed direction, tie-neutral portfolios, HAC and campaign gate."""
    k = GATES["topk_k"]
    series = topk_series(
        signal, forward5, eligibility, direction=direction, k=k,
        min_names=max(MIN_PAIRS, k + 1),
    )
    cal = forward5.index
    disc_ex_cal = purge_by_exit(series.excess.loc[DISCOVERY_START:DISCOVERY_END], cal, DISCOVERY_END, LAG + PRIMARY)
    aud_ex_cal = purge_by_exit(series.excess.loc[AUDIT_START:AUDIT_END], cal, AUDIT_END, LAG + PRIMARY)
    disc_ex = disc_ex_cal.dropna()
    aud_ex = aud_ex_cal.dropna()
    disc_p = purge_by_exit(series.precision.loc[DISCOVERY_START:DISCOVERY_END], cal, DISCOVERY_END, LAG + PRIMARY).dropna()
    aud_p = purge_by_exit(series.precision.loc[AUDIT_START:AUDIT_END], cal, AUDIT_END, LAG + PRIMARY).dropna()
    t_block, _ = block_t_calendar(disc_ex_cal, cal, PRIMARY)
    t_block_aud, _ = block_t_calendar(aud_ex_cal, cal, PRIMARY)
    t_hac_disc = newey_west_t_calendar(disc_ex_cal, cal, PRIMARY - 1)   # lag in trading sessions
    t_hac_aud = newey_west_t_calendar(aud_ex_cal, cal, PRIMARY - 1)
    campaign_pass, p_one = campaign_bonferroni_pass(
        t_hac_disc,
        alpha=GATES["campaign_alpha"],
        hypothesis_budget=GATES["campaign_hypothesis_budget"],
    )
    base_disc = float((k / series.eligible_count.loc[disc_ex.index]).mean()) if len(disc_ex) else float("nan")
    base_aud = float((k / series.eligible_count.loc[aud_ex.index]).mean()) if len(aud_ex) else float("nan")
    row: dict[str, object] = {
        "topk_excess_disc_bp": float(disc_ex.mean() * 1e4) if len(disc_ex) else float("nan"),
        "topk_t_block5_disc": t_block,
        "topk_excess_audit_bp": float(aud_ex.mean() * 1e4) if len(aud_ex) else float("nan"),
        "topk_t_block_audit": t_block_aud,
        "topk_t_hac_disc": t_hac_disc,
        "topk_t_hac_audit": t_hac_aud,
        "discovery_p_one_sided": p_one,
        "campaign_budget": GATES["campaign_hypothesis_budget"],
        "campaign_pass": campaign_pass,
        "referee_version": REFEREE_VERSION,
        "topk_p_at_3_disc": float(disc_p.mean()) if len(disc_p) else float("nan"),
        "topk_p_at_3_audit": float(aud_p.mean()) if len(aud_p) else float("nan"),
        "topk_p_baseline_disc": base_disc,
        "topk_p_baseline_audit": base_aud,
        "_topk_excess_series": series.excess,
        "topk_dropped_label_days": series.dropped_label_days,
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
        and campaign_pass
        and t_block >= GATES["topk_min_t_block5_disc"]
        and row["topk_excess_audit_bp"] >= GATES["topk_min_excess_audit_bp"]
        and np.isfinite(t_block_aud) and t_block_aud >= GATES["topk_min_t_audit"]
        and np.isfinite(t_hac_disc) and t_hac_disc >= GATES["topk_min_t_block5_disc"]     # fix C: HAC must agree
        and np.isfinite(t_hac_aud) and t_hac_aud >= GATES["topk_min_t_audit"]
        and row["topk_p_at_3_disc"] > base_disc
        and row["topk_p_at_3_audit"] > base_aud
    )
    return row


def _evaluate_one(
    signal: pd.DataFrame,
    forward: dict[int, pd.DataFrame],
    eligibility: pd.DataFrame,
    preregistered_direction: float | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {}
    for h in HORIZONS:
        daily_ic, pair_count = common_sample_spearman(signal, forward[h], eligibility, MIN_PAIRS)
        discovery = purge_by_exit(daily_ic.loc[DISCOVERY_START:DISCOVERY_END], forward[h].index, DISCOVERY_END, LAG + h).dropna()
        row[f"h{h}_discovery_ic"] = float(discovery.mean()) if len(discovery) else np.nan
        row[f"h{h}_discovery_days"] = int(len(discovery))
        row[f"h{h}_median_pairs"] = float(pair_count.loc[DISCOVERY_START:DISCOVERY_END].median())
        if h == PRIMARY:
            primary_ic = daily_ic
    discovery = purge_by_exit(primary_ic.loc[DISCOVERY_START:DISCOVERY_END], forward[PRIMARY].index, DISCOVERY_END, LAG + PRIMARY).dropna()
    audit = purge_by_exit(primary_ic.loc[AUDIT_START:AUDIT_END], forward[PRIMARY].index, AUDIT_END, LAG + PRIMARY).dropna()
    row["discovery_ic"] = float(discovery.mean())
    row["discovery_days"] = int(len(discovery))
    row["seen_audit_ic"] = float(audit.mean()) if len(audit) else np.nan
    row["seen_audit_days"] = int(len(audit))
    primary_value = row[f"h{PRIMARY}_discovery_ic"]
    row["all_horizons_same_direction"] = bool(
        all(
            np.isfinite(row[f"h{h}_discovery_ic"])
            and np.sign(row[f"h{h}_discovery_ic"]) == float(preregistered_direction)
            for h in HORIZONS
        )
    )
    row["discovery_direction"] = float(np.sign(row["discovery_ic"]))
    # fix D: the tested direction is the preregistered hypothesis, never fitted on discovery data
    if preregistered_direction not in (-1.0, 1.0):
        raise ValueError("candidate direction must be preregistered as +1 or -1")
    direction = float(preregistered_direction)
    row["direction"] = direction
    matches = 0
    eligible_years = 0
    for year in (2021, 2022, 2023):
        values = discovery[discovery.index.year == year].dropna()   # P0 (Codex): purged series, same as discovery_ic
        mean = float(values.mean()) if len(values) else np.nan
        row[f"ic_{year}"] = mean
        row[f"ic_{year}_days"] = int(len(values))
        if len(values) >= YEAR_GATE_MIN_DAYS:      # fix A: partial years (2021 = 5 months) do not vote
            eligible_years += 1
            if np.isfinite(mean) and np.sign(mean) == direction:
                matches += 1
    row["year_direction_count"] = matches
    row["year_direction_eligible"] = eligible_years
    row["discovery_start"] = str(DISCOVERY_START.date())
    cal = forward[PRIMARY].index
    disc_keep = purge_by_exit(pd.Series(True, index=cal).loc[DISCOVERY_START:DISCOVERY_END], cal, DISCOVERY_END, LAG + PRIMARY).index
    aud_keep = purge_by_exit(pd.Series(True, index=cal).loc[AUDIT_START:AUDIT_END], cal, AUDIT_END, LAG + PRIMARY).index
    loso, _loso_baseline = matched_leave_one_symbol_out(
        signal,
        forward[PRIMARY],
        eligibility,
        min_pairs=MIN_PAIRS,
        discovery_mask=pd.Series(cal.isin(disc_keep), index=cal),
        audit_mask=pd.Series(cal.isin(aud_keep), index=cal),
    )
    row["identity_gate_pass"] = identity_gate(loso, direction, GATES["identity_min_abs_ic"], GATES["identity_min_discovery_ic"])
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
    if not np.isfinite(row["discovery_ic"]) or row["discovery_ic"] * row["direction"] < GATES["min_abs_ic"]:
        failures.append("signed_discovery_ic")   # fix D: signed in the preregistered direction
    if not row.get("campaign_pass", False):
        failures.append("campaign_bonferroni")
    if not row.get("leg_increment_pass", True):
        failures.append("leg_increment")         # fix E
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
    return signal.loc[DISCOVERY_START:DISCOVERY_END].iloc[::RANK_CORR_STRIDE].stack(future_stack=True)


def _pairwise_pearson(a: pd.Series, b: pd.Series) -> float:
    """Pearson correlation of cross-sectional rank vectors, min_periods=500.
    NaN (insufficient overlapping pairs) means FAIL CLOSED upstream."""
    frame = pd.DataFrame({"a": a, "b": b})
    value = frame.corr(min_periods=RANK_CORR_MIN_PERIODS)
    result = float(value.loc["a", "b"])
    return result if np.isfinite(result) else float("nan")


def _previously_admitted(current_output: Path) -> list[dict]:
    """Load gate-passing candidates together with their immutable plans."""
    admitted = []
    # Controller void list (E30, 2026-09-21): admissions the controller voided on audit stay
    # gate_pass=True in their immutable STATUS but must not act as dedup references, or a
    # voided one-day-return shadow would block every later candidate correlated with it.
    for output_root in CAMPAIGN_OUTPUT_ROOTS:
        lane = output_root.parents[1].name
        void_path = output_root.parents[1] / "CONTROLLER_VOID.json"
        voided: set[str] = set()
        if void_path.exists():
            for rid, entry in json.loads(void_path.read_text()).items():
                voided.update(f"{rid}:{cid}" for cid in entry.get("ids", []))
        status_paths = sorted(
            path for path in output_root.glob("round_*/STATUS.json")
            if re.fullmatch(r"round_\d+", path.parent.name)
        )
        for status_path in status_paths:
            if status_path.parent.resolve() == current_output.resolve():
                continue
            status = json.loads(status_path.read_text())
            if not status.get("candidates") or status.get("referee_version") != REFEREE_VERSION:
                continue
            plan_path = status_path.with_name("PLAN.json")
            if not plan_path.exists() or status.get("plan_sha256") != _hash(plan_path):
                raise ValueError(f"v4 admitted plan missing or changed: {status_path.parent}")
            candidates = {
                str(candidate["id"]): candidate
                for candidate in json.loads(plan_path.read_text())["candidates"]
            }
            vector_path = status_path.with_name("admitted_rank_vectors.parquet")
            if not vector_path.exists() or status.get("admitted_rank_vectors_sha256") != _hash(vector_path):
                raise ValueError(f"v4 admitted vectors missing or changed: {status_path.parent}")
            for cand in status.get("candidates", []):
                if not cand.get("gate_pass"):
                    continue
                candidate_id = str(cand["id"])
                if f"{status['round_id']}:{candidate_id}" in voided:
                    continue
                if candidate_id not in candidates:
                    raise ValueError(f"admitted candidate absent from plan: {status['round_id']}:{candidate_id}")
                admitted.append({
                    "lane": lane,
                    "round": status["round_id"],
                    "id": candidate_id,
                    "plan_sha256": status["plan_sha256"],
                    "vector_path": vector_path,
                })
    return admitted


def _prior_admitted_vectors(
    current_output: Path,
) -> tuple[dict[str, pd.Series], list[dict[str, object]]]:
    """Load frozen v4 ranks; never rebuild prior signals with current code."""
    vectors: dict[str, pd.Series] = {}
    summary: list[dict[str, object]] = []
    for prior in _previously_admitted(current_output):
        stored = pd.read_parquet(prior["vector_path"])
        required = {"candidate_id", "signal_date", "symbol", "rank_value"}
        if not required <= set(stored.columns):
            raise ValueError(f"prior admitted vector schema mismatch: {prior['vector_path']}")
        stored = stored.loc[stored["candidate_id"].astype(str) == prior["id"]].copy()
        stored["signal_date"] = pd.to_datetime(stored["signal_date"])
        stored["symbol"] = stored["symbol"].astype(str)
        if stored.duplicated(["signal_date", "symbol"]).any():
            raise ValueError(f"duplicate prior admitted rank keys: {prior['vector_path']}")
        vector = pd.Series(
            stored["rank_value"].to_numpy(dtype=float),
            index=pd.MultiIndex.from_frame(stored[["signal_date", "symbol"]]),
        )
        key = f"prior:{prior['lane']}:{prior['round']}:{prior['id']}"
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
    current_output: Path,
) -> list[dict[str, object]]:
    """Deterministic gate-then-dedup, fixed plan order. Failures never enter
    the comparison set. Missing must-compare correlations fail closed."""
    reference: dict[str, pd.Series] = dict(shelf_vectors)
    prior_vectors, prior_summary = _prior_admitted_vectors(current_output)
    reference.update(prior_vectors)
    # Base-return references (E30 rule, 2026-09-21): a candidate whose cross-sectional ranks
    # track the trailing 1-day or 20-day return at |corr| >= 0.70 is a return shadow, not a
    # factor. Both use close <= D only (no lookahead); same stride/rank rule as the shelf.
    close = panels["close"][symbols].where(eligibility_all[symbols])
    # fix F (2026-09-21): price-position and basket-beta references join the base set.
    high, low = panels["high"][symbols].where(eligibility_all[symbols]), panels["low"][symbols].where(eligibility_all[symbols])
    pos20 = (close - low.rolling(20, min_periods=10).min()) / (high.rolling(20, min_periods=10).max() - low.rolling(20, min_periods=10).min())
    pos250 = (close - low.rolling(250, min_periods=120).min()) / (high.rolling(250, min_periods=120).max() - low.rolling(250, min_periods=120).min())
    r1 = close / close.shift(1) - 1.0
    mkt = r1.mean(axis=1)
    cov = r1.rolling(60, min_periods=40).cov(mkt)
    beta60 = cov.div(mkt.rolling(60, min_periods=40).var(), axis=0)
    base_refs = (("base:RET1", r1), ("base:RET20", close / close.shift(20) - 1.0),
                 ("base:PRICE_POS_20", pos20), ("base:PRICE_POS_250", pos250), ("base:BETA_60", beta60))
    for name, ret in base_refs:
        ranked_ret = ret.rank(axis=1, pct=True).reindex(index=plan["_signal_index"], columns=symbols)
        vec = _stride_vector(ranked_ret)
        if len(vec.dropna()) >= RANK_CORR_MIN_PERIODS:
            reference[name] = vec
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
        base_corrs = {key: value for key, value in corrs.items() if key.startswith("base:")}
        pair_operator = row.get("operator") in ("rank_spread", "rank_interaction", "rank_ratio", "rank_product")
        if pair_operator and base_corrs and max(abs(value) for value in base_corrs.values()) >= GATES["pair_base_shadow_max_corr"]:
            row["gate_pass"] = False
            row["gate_failures"] = "pair_base_shadow"
            continue
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
    # Preserve the Python implementation that materialized signals and gates.
    # Hash-only provenance cannot replay a round after family/core code changes.
    source = ROOT / "src/etf_strategy"
    frozen_source = snap / "source/etf_strategy"
    if not frozen_source.exists():
        shutil.copytree(
            source,
            frozen_source,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    for path in sorted(frozen_source.rglob("*.py")):
        hashes[f"source:{path.relative_to(frozen_source)}"] = _hash(path)
    return hashes


def _log_attempt(output: Path, entry: dict) -> None:
    with (output / "attempts.jsonl").open("a") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cmd_evaluate(args: argparse.Namespace) -> None:
    output = Path(args.output).resolve()
    started = datetime.now(timezone.utc).isoformat()
    plan_path = output / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    if not verify_plan_seal(plan_path):
        raise ValueError("PLAN seal missing or changed after preregistration")
    # Codex round-2 P1: bind every family implementation to this process BEFORE the source tree is
    # hashed, so a modify-then-restore of a family file between the two hashes cannot be executed
    # unnoticed (the imported bytes are the hashed bytes, or the start hash already mismatches).
    load_builtin_families()
    _verify_plan_contract(plan)
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
        dropped = _discard_pending_caches()
        _log_attempt(
            output,
            {"event": "evaluate_error", "mode": args.mode, "at_utc": datetime.now(timezone.utc).isoformat(),
             "error": f"{type(error).__name__}: {error}", "pending_caches_discarded": dropped},
        )
        raise


def _verify_run_end(plan_path: Path, plan_sha: str, plan: dict) -> None:
    """P1 (Codex): the PLAN file on disk, its seal and the whole run contract are re-verified at the END
    of the run with fresh hashes; any change during the run aborts before caches/STATUS are published."""
    if not verify_plan_seal(plan_path):
        raise ValueError("PLAN seal invalid at end of run (PLAN changed during evaluation)")
    if _hash(plan_path) != plan_sha:
        raise ValueError("PLAN.json hash changed during evaluation")
    _verify_plan_contract(plan, refresh=True)


def _verify_plan_contract(plan: dict, refresh: bool = False) -> None:
    expected_engine = plan.get("engine_hashes")
    if not expected_engine:
        raise ValueError("PLAN predates v4 engine hashes; use historical rejudge, not evaluate")
    actual_engine = {
        "base_script": _hash(SCRIPT),
        "driver": _hash(Path(sys.argv[0]).resolve()),
        "python_tree": _python_tree_hash(refresh=refresh),
    }
    if actual_engine != expected_engine:
        raise ValueError("engine source changed after PLAN lock")
    for path, expected in plan.get("config_hashes", {}).items():
        if not Path(path).exists() or _hash(Path(path)) != expected:
            raise ValueError(f"config changed after PLAN lock: {path}")
    symbols = [
        row["ts_code"]
        for row in json.loads(UNIVERSE_CONFIG.read_text())["etfs"]
        if row["role"] == "candidate"
    ]
    frequencies = set()
    sources = {
        candidate[side]["source"]
        for candidate in plan["candidates"]
        for side in ("left", "right")
    }
    for source in sources:
        config = yaml.safe_load(_config_path(source).read_text())
        frequency = str(config.get("frequency", ""))
        if frequency and frequency not in ("1d", "adj_factor"):
            frequencies.add(frequency)
    if hash_research_inputs(CANONICAL_ROOT, symbols, frequencies) != plan.get("input_hashes"):
        raise ValueError("research inputs changed after PLAN lock")
    shelf = plan.get("shelf_reference", {})
    if (
        shelf.get("scores_sha256") != _hash(SHELF_DIR / "selected_factor_scores.parquet")
        or shelf.get("catalog_sha256") != _hash(SHELF_DIR / "IC_FACTOR_SHELF.csv")
    ):
        raise ValueError("shelf reference changed after PLAN lock")


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
            "operator": cand.get("operator", ""),
            "expression": spec.readable,
            "mechanism": cand["mechanism"],
            "expected_sign": cand["expected_sign"],
        }
        row.update(_evaluate_one(signal, forward, eligibility, float(cand["expected_sign"])))
        # Fix E: test the paired candidate-minus-leg return series on both surfaces.
        # Each standalone leg receives its better discovery direction, which is conservative for the pair.
        row["leg_increment_pass"] = True
        if str(cand.get("operator", "")) in ("rank_spread", "rank_interaction", "rank_ratio", "rank_product"):
            leg_passes = []
            for side in ("left", "right"):
                leg = cand.get(side) or {}
                name = leg.get("name") if isinstance(leg, dict) else None
                if name not in ranked:
                    leg_passes.append(False)
                    continue
                leg_rows = {d: _topk_referee(ranked[name], forward[PRIMARY], eligibility, d) for d in (1.0, -1.0)}
                best_d = max(
                    leg_rows,
                    key=lambda d: np.nan_to_num(leg_rows[d]["topk_t_hac_disc"], nan=-np.inf),
                )
                stats = paired_increment_stats(
                    row["_topk_excess_series"], leg_rows[best_d]["_topk_excess_series"],
                    discovery_end=DISCOVERY_END, audit_start=AUDIT_START,
                    audit_end=AUDIT_END, horizon=PRIMARY,
                    calendar=forward[PRIMARY].index, lag=LAG, discovery_start=DISCOVERY_START,
                )
                row[f"leg_{side}_direction"] = best_d
                for key, value in stats.items():
                    row[f"leg_{side}_{key}"] = value
                leg_passes.append(bool(
                    np.isfinite(stats["discovery_t_hac"])
                    and stats["discovery_t_hac"] >= GATES["leg_increment_min_t_disc"]
                    and np.isfinite(stats["audit_t_hac"])
                    and stats["audit_t_hac"] >= GATES["leg_increment_min_t_audit"]
                    and stats["audit_bp"] > GATES["leg_increment_min_audit_bp"]
                ))
            row["leg_increment_pass"] = len(leg_passes) == 2 and all(leg_passes)
        for side in ("left", "right"):
            for key in ("direction", "discovery_bp", "discovery_t_hac", "audit_bp", "audit_t_hac"):
                row.setdefault(f"leg_{side}_{key}", np.nan)
        row["expected_sign_match"] = bool(
            np.isfinite(row["discovery_direction"]) and row["discovery_direction"] == float(cand["expected_sign"])
        )
        rows.append(row)
    checks = _leak_checks(ranked, panels, eligibility_all, symbols, plan, output)
    prior_reference_summary: list[dict[str, object]] = []
    if not checks["pass"]:
        # C2: fail closed -- no candidate may pass while any leak check fails.
        for row in rows:
            row["intrinsic_gate_pass"] = False
            row["intrinsic_failures"] = "leak_checks_fail_closed"
            row["gate_pass"] = False
            row["gate_failures"] = "leak_checks_fail_closed"
    else:
        shelf_vectors = _shelf_vectors(symbols, plan)
        for row in rows:
            passed, failures = _intrinsic_gate_report(row)
            row["intrinsic_gate_pass"] = passed
            row["intrinsic_failures"] = ",".join(failures)
        prior_reference_summary = _dedup_pass(
            rows, shelf_vectors, plan, panels, eligibility_all, symbols, output
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
             "leak_pass": checks["pass"],
             "pending_caches_discarded": _discard_pending_caches()},   # validate never publishes caches
        )
        return

    output.mkdir(parents=True, exist_ok=True)
    meta_columns = [
        "candidate_id", "operator", "expression", "mechanism", "expected_sign", "direction",
        "expected_sign_match",
        "discovery_ic", "discovery_days", "seen_audit_ic", "seen_audit_days",
        "h5_discovery_ic", "h10_discovery_ic", "h20_discovery_ic",
        "ic_2021", "ic_2022", "ic_2023", "year_direction_count",
        "all_horizons_same_direction", "identity_gate_pass",
        "identity_min_discovery_ic_signed", "identity_min_audit_ic_signed",
        "max_abs_rank_corr", "max_abs_rank_corr_vs",
        "topk_excess_disc_bp", "topk_t_block5_disc", "topk_t_hac_disc",
        "topk_excess_audit_bp", "topk_t_block_audit", "topk_t_hac_audit",
        "discovery_p_one_sided", "campaign_budget", "campaign_pass", "referee_version",
        "topk_p_at_3_disc", "topk_p_at_3_audit", "topk_gate_pass",
        "leg_increment_pass",
        "leg_left_direction", "leg_left_discovery_bp", "leg_left_discovery_t_hac",
        "leg_left_audit_bp", "leg_left_audit_t_hac",
        "leg_right_direction", "leg_right_discovery_bp", "leg_right_discovery_t_hac",
        "leg_right_audit_bp", "leg_right_audit_t_hac",
        "gate_pass", "gate_failures", "evidence_status",
    ]
    for row in rows:
        row["evidence_status"] = EVIDENCE_STATUS if row["gate_pass"] else "rejected_this_round"
    metrics = pd.DataFrame(rows)[meta_columns]
    metrics.to_csv(output / "candidate_metrics.csv", index=False)
    vector_frames = []
    for row in rows:
        if not row["gate_pass"]:
            continue
        frame = _stride_vector(row["signal"]).rename("rank_value").reset_index()
        frame.columns = ["signal_date", "symbol", "rank_value"]
        frame.insert(0, "candidate_id", row["candidate_id"])
        vector_frames.append(frame)
    admitted_vectors = (
        pd.concat(vector_frames, ignore_index=True)
        if vector_frames
        else pd.DataFrame(columns=["candidate_id", "signal_date", "symbol", "rank_value"])
    )
    vector_path = output / "admitted_rank_vectors.parquet"
    admitted_vectors.to_parquet(vector_path, index=False)
    corr_dump = {
        row["candidate_id"]: {k: round(v, 6) for k, v in row.get("rank_corrs", {}).items()}
        for row in rows
    }
    (output / "rank_correlations.json").write_text(
        json.dumps(corr_dump, ensure_ascii=False, indent=2)
    )

    snapshot_hashes = _snapshot(output, plan)
    # provenance fix (2026-09-21): family Python code was not hashed, so rounds 018-034 became
    # non-reproducible after families/*.py were edited. Record every family module's sha256.
    families_dir = ROOT / "src/etf_strategy/core/families"
    for fam_py in sorted(families_dir.glob("*.py")):
        snapshot_hashes[f"family_py:{fam_py.name}"] = _hash(fam_py)
    snapshot_hashes["referee_version"] = REFEREE_VERSION
    manifest = json.loads(LEDGER_MANIFEST.read_text())
    admitted = [r for r in rows if r["gate_pass"]]
    status = {
        "round_id": ROUND_ID,
        "referee_version": REFEREE_VERSION,
        "as_of": AS_OF,
        "discovery_start": str(DISCOVERY_START.date()),
        "discovery_end": str(DISCOVERY_END.date()),
        "plan_sha256": plan_sha,
        "script_sha256": _hash(SCRIPT),
        "script_snapshot": str(output / "snapshots" / SCRIPT.name),
        "universe_config": str(UNIVERSE_CONFIG),
        "universe_config_sha256": _hash(UNIVERSE_CONFIG),
        "canonical_root": str(CANONICAL_ROOT),
        "input_file_hashes": plan["input_hashes"],
        "config_hashes": plan["config_hashes"],
        "snapshot_hashes": snapshot_hashes,
        "admitted_rank_vectors_sha256": _hash(vector_path),
        "contract_source": str(LEDGER_MANIFEST),
        "contract_generation": manifest["generation"],
        "surfaces": plan["surfaces"],
        "gates": {
            **GATES,
            "referee_v4": "top-3 excess; fixed expected_sign; fractional tie weights; "
            "discovery campaign Bonferroni plus block/HAC t; audit mean>=5bp plus "
            "block/HAC t>=2; paired leg increment; base-shadow controls",
        },
        "dedup_rule": plan["dedup_rule"],
        "prior_admitted_references": prior_reference_summary,
        "evidence_status": EVIDENCE_STATUS,
        "certified_factor": False,
        "promotion_allowed": False,
        "population_survivorship_controlled": False,
        "external_validity": False,
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
                "topk_t_hac_disc": r["topk_t_hac_disc"],
                "topk_excess_audit_bp": r["topk_excess_audit_bp"],
                "topk_t_block_audit": r.get("topk_t_block_audit"),        # Codex round-3 P1: was missing -> verifier could not compare it
                "topk_t_hac_audit": r["topk_t_hac_audit"],
                "topk_dropped_label_days": r.get("topk_dropped_label_days"),
                "identity_gate_pass": bool(r.get("identity_gate_pass", False)),
                "year_direction_count": r.get("year_direction_count"),
                "year_direction_eligible": r.get("year_direction_eligible"),
                "campaign_pass": bool(r["campaign_pass"]),
                "leg_increment_pass": bool(r["leg_increment_pass"]),
                "referee_version": REFEREE_VERSION,
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
            "subdir_sources": checks.get("subdir_sources", []),
            "prefix_invariance_subdir_max_abs_diff": _bucket_max(
                checks.get("prefix_invariance_subdir", {})
            ),
            "future_perturbation_subdir_max_abs_diff": _bucket_max(
                checks.get("future_perturbation_subdir", {})
            ),
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
            "scanner": None,
            "scanner_note": (
                "No standalone scan artifact is claimed; executable prefix-invariance "
                "and future-perturbation results above are the hard leak evidence."
            ),
            "hard_gate": True,
        },
        "correction_reference": None,
        "prior_round_plan_sha256": plan["prior_round_plan_sha256"],
        "expression_hashes": plan["expression_hashes"],
        "notes": {
            "direction_rule": "检验方向只取预登记 expected_sign；发现期符号只报告，不参与选向",
            "combination_vs_mechanisms": "8个表达式共享部分原子，组合数不等于已证实的独立机制数",
            "independent_oos": "2024-01-01起为已见审计面；无任何独立OOS；不自行交易或认证",
        },
        "campaign_bonferroni": {
            "alpha": GATES["campaign_alpha"],
            "fixed_hypothesis_budget": GATES["campaign_hypothesis_budget"],
            "hard_gate": True,
        },
        "independent_oos": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": sys.argv,
    }
    # item 5: inputs, configs, engine and shelf must be unchanged at the END of the run too;
    # only then do pending caches become visible and STATUS gets written.
    _verify_run_end(output / "PLAN.json", plan_sha, plan)
    status["run_contract_reverified_at_utc"] = datetime.now(timezone.utc).isoformat()
    status["caches_finalized"] = _finalize_pending_caches()
    status["exit_purge"] = {"lag": LAG, "rule": "signal kept only if open(D+lag+H) is on/before the window end"}
    (output / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2))

    prior_names = ", ".join(
        str(item["reference_key"]) for item in prior_reference_summary
    ) or "无"
    lines = [
        f"# {ROUND_ID} 挖掘报告（预注册 {len(candidates)} 条跨家族交互表达式）",
        "",
        f"计划锁定哈希: `{plan_sha[:16]}…`；as_of={AS_OF}；契约复制自 v9 家族裁判（人口/标签/时间面/门槛未改）。",
        "发现面截至 2023-12-31；2024-01-01~2025-04-30 为已见审计面；2025-04-30 之后未参与。",
        "检验符号只取预登记 expected_sign；发现期符号只报告，不参与选向。",
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
        "原始数据根未改动。负向 shift 仅出现在标签 open(D+2+H)/open(D+2)-1 的构造中，标签从不作为特征。"
        "本轮不声称另有静态扫描文件；以上可执行检查就是泄漏硬门证据。",
        "",
        "历史 round_001 的欠定残差诊断不进入本轮门或报告；历史产物原样保留。",
        "",
        "8个表达式共享部分原子，组合数不等于已证实的独立机制数。全部通过候选仅为 "
        "discovery_candidate_not_certified，不构成正式认证或可交易策略。",
        "",
        f"多重检验硬门：固定预算 N={GATES['campaign_hypothesis_budget']}，alpha={GATES['campaign_alpha']}，使用发现期 HAC t 的单边 p 值。",
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
        write_plan_seal(Path(args.output).resolve() / "PLAN.json")
    else:
        cmd_evaluate(args)


if __name__ == "__main__":
    main()
