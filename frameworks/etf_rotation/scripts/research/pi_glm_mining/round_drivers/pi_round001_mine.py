#!/usr/bin/env python3
"""Round 001: preregistered low-redundancy cross-sectional ETF factor mining.

Preregisters at most 6 expressions (cross-source atom interactions/spreads built
ONLY from existing family providers), then evaluates them with the frozen
adjudication contract (population, labels, surfaces and gates unchanged).

Sub-commands:
  plan      write PLAN.json (preregistration lock, before any evaluation)
  evaluate  read PLAN.json, run end-to-end evaluation (--mode validate runs one
            candidate and leak checks only; --mode batch evaluates all)
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]  # .../workspace/frameworks/etf_rotation
sys.path.insert(0, str(ROOT / "src"))

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core.etf_factor_grammar import (
    ExpressionSpec,
    build_pit_eligibility,
    cross_sectional_rank,
    materialize_expression,
)
from etf_strategy.core.etf_family_referee import common_sample_spearman
from etf_strategy.core.etf_identity import identity_gate, leave_one_symbol_out
from etf_strategy.core.family_registry import load_builtin_families, resolve_family

CANONICAL_ROOT = Path(str(Path(__file__).resolve().parents[6] / "data/etf_rotation_v1"))
CORAL_PROJECT = Path(str(Path(__file__).resolve().parents[6]))
UNIVERSE_CONFIG = CORAL_PROJECT / "config/etf_rotation_universe_v1.json"
SHELF_DIR = CORAL_PROJECT / "runtime_outputs/etf_ic_factor_shelf_v11_20260919"
LEDGER_MANIFEST = (
    CORAL_PROJECT / "runtime_outputs/etf_family_multisource_v9_20260919/run_manifest.json"
)

AS_OF = "2026-09-17"
DISCOVERY_END = pd.Timestamp("2023-12-31")
AUDIT_START = pd.Timestamp("2024-01-01")
AUDIT_END = pd.Timestamp("2025-04-30")
HORIZONS = [5, 10, 20]
PRIMARY = 5
LAG = 2
MIN_PAIRS = 8
MIN_HISTORY = 120
GATES = {
    "min_discovery_days": 360,
    "min_abs_ic": 0.01,
    "min_abs_seen_audit_ic": 0.01,
    "min_year_direction_count": 2,
    "max_abs_factor_rank_corr": 0.70,
}
EVIDENCE_STATUS = "discovery_candidate_not_certified"

# ---- frozen v9 adjudication contract (read programmatically, never edited) ----
def _v9_manifest() -> dict:
    return json.loads(LEDGER_MANIFEST.read_text())


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


CANDIDATES = [
    {
        "id": "E1",
        "operator": "rank_interaction",
        "left": {"name": "SKIP_RECENT_MOM_60_5", "source": "directional_trend"},
        "right": {"name": "AMOUNT_Z_20", "source": "trading_activity"},
        "mechanism": "volume_conditioned_trend_crowding",
        "hypothesis": "中期趋势(剔除近端反转段)的延续性取决于量能状态：放量伴随的老趋势是拥挤交易、随后均值回归；缩量阴跌是无人接盘的出清。交互项(趋势x成交额活跃度z)捕捉'趋势x拥挤度'联合状态。",
        "expected_sign": -1,
    },
    {
        "id": "E2",
        "operator": "rank_interaction",
        "left": {"name": "PATH_EFFICIENCY_60", "source": "path_efficiency"},
        "right": {"name": "RET_120", "source": "directional_trend"},
        "mechanism": "path_quality_momentum",
        "hypothesis": "RET_120的横截面信息主要被波动率水平吸收；路径效率度量趋势的平滑度(信噪比)。平滑单边下跌代表持续单向配置行为(信息连续到达)，震荡假突破无信息。交互=趋势方向x趋势质量，预期平滑深跌延续(负方向)。",
        "expected_sign": -1,
    },
    {
        "id": "E3",
        "operator": "rank_interaction",
        "left": {"name": "GAP_VOL_RATIO_20", "source": "gap_volatility"},
        "right": {"name": "GAP_SESSION_CORR_20", "source": "gap_response"},
        "mechanism": "overnight_information_resonance",
        "hypothesis": "跳空波动率高=信息在非交易时段集中到达(QDII跨时区/商品夜盘)；跳空-日内相关性=隔夜信息被日内交易延续消化的程度。两者共振时信息传导连贯、短期动量延续；仅有跳空波动而无日内承接为噪声跳空。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "E4",
        "operator": "rank_interaction",
        "left": {"name": "SIGN_ACF1_20", "source": "serial_dependence"},
        "right": {"name": "VOL_ACCEL_5_20", "source": "downside_risk"},
        "mechanism": "volatility_accelerated_overreaction",
        "hypothesis": "符号自相关刻画短期延续/反转状态；波动加速(短窗波动相对长窗上升)标志着分歧扩大与过度反应。波动加速期正自相关(连续同号)更可能是追涨杀跌的过度反应，随后反转。交互预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "E5",
        "operator": "rank_spread",
        "left": {"name": "WORST_DAY_60", "source": "return_tail_shape"},
        "right": {"name": "REALIZED_VOL_20", "source": "downside_risk"},
        "mechanism": "tail_release_repair_net_of_vol",
        "hypothesis": "最差单日(尾部事件已实现释放)后存在修复效应，但该效应必须剥离整体波动水平主效应才是干净的'尾部释放'信息：rank(WORST_DAY_60)-rank(REALIZED_VOL_20)在同等波动水平下比较尾部冲击，降低与波动类shelf因子的冗余。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "E6",
        "operator": "rank_interaction",
        "left": {"name": "MARKET_LEAD_BETA_20", "source": "cross_etf_lead_lag"},
        "right": {"name": "GAP_SESSION_CORR_20", "source": "gap_response"},
        "mechanism": "cross_border_information_chain",
        "hypothesis": "对市场领先beta高=资产接收跨资产信息传导；隔夜信息日内承接(GAP_SESSION_CORR)完整则传导链未断裂。跨境(QDII)资产信息链完整时隔夜信号短期延续。交互预期正方向。",
        "expected_sign": 1,
    },
]


def _config_path(source: str) -> Path:
    return ROOT / "configs" / f"family_{source}_v1.yaml"


def cmd_plan(args: argparse.Namespace) -> None:
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    plan_path = output / "PLAN.json"
    if plan_path.exists():
        raise SystemExit(f"PLAN.json already exists, preregistration is immutable: {plan_path}")
    manifest = _v9_manifest()
    cmd = manifest["command"]
    universe_config = (CORAL_PROJECT / cmd[cmd.index("--universe-config") + 1]).resolve()
    assert universe_config == UNIVERSE_CONFIG, "universe config drifted from v9 contract"
    plan = {
        "round_id": "round_001",
        "miner": "pi/zai/glm-5.3-flash",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration_note": "本文件在任何本轮评估计算之前写入并锁定；evaluate 子命令仅读取本文件。6条表达式均为跨源原子组合/交互，不在v9已枚举的135个atomic表达式中；窗口变体不作为新机制。",
        "as_of": AS_OF,
        "data_root": str(CANONICAL_ROOT),
        "universe_config": str(universe_config),
        "universe_source": "原项目 runtime_outputs/etf_family_multisource_v9_20260919/run_manifest.json 的 command 字段程序化读取",
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
        "gates": GATES,
        "evidence_status": EVIDENCE_STATUS,
        "shelf_reference": {
            "path": str(SHELF_DIR),
            "candidates": len(
                pd.read_csv(SHELF_DIR / "IC_FACTOR_SHELF.csv")
            ),
            "use": "去冗余参照：|rank_corr| < 0.70 对全部16个shelf候选及本轮其他入选候选",
        },
        "candidates": [],
        "config_hashes": {},
    }
    sources = sorted(
        {c["left"]["source"] for c in CANDIDATES} | {c["right"]["source"] for c in CANDIDATES}
    )
    for source in sources:
        cfg = _config_path(source)
        mining = yaml.safe_load(cfg.read_text())
        atoms = {a["name"]: a["family"] for a in mining["atoms"]}
        plan["config_hashes"][str(cfg)] = _hash(cfg)
        for cand in CANDIDATES:
            for side in ("left", "right"):
                slot = cand[side]
                if slot["source"] == source:
                    assert slot["name"] in atoms, f"{slot['name']} missing in {source}"
                    slot["family"] = atoms[slot["name"]]
                    slot["config"] = str(cfg)
    for cand in CANDIDATES:
        assert cand["left"]["family"] != cand["right"]["family"], (
            f"{cand['id']} violates cross_family_only"
        )
        entry = {k: cand[k] for k in ("id", "operator", "mechanism", "hypothesis", "expected_sign")}
        entry["left"] = {k: cand["left"][k] for k in ("name", "source", "family", "config")}
        entry["right"] = {k: cand["right"][k] for k in ("name", "source", "family", "config")}
        entry["novelty"] = "cross-source pair combination; v9 enumerated 135 atomic expressions only"
        plan["candidates"].append(entry)
    assert len({c["mechanism"] for c in plan["candidates"]}) >= 2, "need >=2 independent mechanisms"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))
    print(f"PLAN locked: {plan_path} (candidates={len(plan['candidates'])})")


def _expression_spec(cand: dict) -> ExpressionSpec:
    return ExpressionSpec(
        cand["operator"],
        cand["left"]["name"],
        cand["right"]["name"] if cand["operator"] != "atomic" else None,
        family="+".join(sorted({cand["left"]["family"], cand["right"]["family"]})),
    )


def _raw_forward(open_prices: pd.DataFrame, horizon: int, lag: int) -> pd.DataFrame:
    """Label only. Entry open(D+lag), exit open(D+lag+H). Never used as a feature."""
    entry = open_prices.shift(-lag)
    exit_price = open_prices.shift(-(lag + horizon))
    return (exit_price / entry - 1.0).where((entry > 0.0) & (exit_price > 0.0))


def _load_context() -> tuple[dict[str, pd.DataFrame], pd.DataFrame, list[str], dict[str, pd.DataFrame]]:
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
    panels, eligibility_all: pd.DataFrame, symbols: list[str], plan: dict
) -> dict[str, pd.DataFrame]:
    load_builtin_families()
    needed: dict[str, set[str]] = {}
    for cand in plan["candidates"]:
        for side in ("left", "right"):
            slot = cand[side]
            needed.setdefault(slot["source"], set()).add(slot["name"])
    ranked: dict[str, pd.DataFrame] = {}
    for source, names in sorted(needed.items()):
        cfg = _config_path(source)
        digest = _hash(cfg)
        recorded = {Path(k).name: v for k, v in plan["config_hashes"].items()}
        assert recorded.get(cfg.name) == digest, f"config hash drift for {source}"
        mining = yaml.safe_load(cfg.read_text())
        space = resolve_family(source).builder(panels, eligibility_all, CANONICAL_ROOT, mining)
        missing = sorted(names - set(space))
        assert not missing, f"{source} missing atoms {missing}"
        for name in names:
            ranked[name] = cross_sectional_rank(space[name][symbols], eligibility_all[symbols])
    return ranked


def _shelf_scores(symbols: list[str], index: pd.Index) -> dict[str, pd.DataFrame]:
    long = pd.read_parquet(SHELF_DIR / "selected_factor_scores.parquet")
    out: dict[str, pd.DataFrame] = {}
    for key, group in long.groupby("expression_key"):
        wide = group.pivot(index="signal_date", columns="symbol", values="score")
        out[str(key)] = wide.reindex(index=index, columns=symbols)
    return out


def _stack_corr(a: pd.DataFrame, b: pd.DataFrame, discovery_only: bool = True) -> float:
    va = a.loc[:DISCOVERY_END] if discovery_only else a
    vb = b.loc[:DISCOVERY_END] if discovery_only else b
    pair = pd.DataFrame(
        {
            "a": va.stack(future_stack=True),
            "b": vb.stack(future_stack=True),
        }
    ).dropna()
    if len(pair) < 500 or pair["a"].std() == 0 or pair["b"].std() == 0:
        return float("nan")
    return float(pair["a"].corr(pair["b"], method="spearman"))


def _evaluate_one(
    signal: pd.DataFrame,
    forward: dict[int, pd.DataFrame],
    eligibility: pd.DataFrame,
) -> dict[str, object]:
    row: dict[str, object] = {}
    horizon_ic = {}
    for h in HORIZONS:
        daily_ic, pair_count = common_sample_spearman(signal, forward[h], eligibility, MIN_PAIRS)
        horizon_ic[h] = daily_ic
        discovery = daily_ic.loc[:DISCOVERY_END].dropna()
        row[f"h{h}_discovery_ic"] = float(discovery.mean()) if len(discovery) else np.nan
        row[f"h{h}_discovery_days"] = int(len(discovery))
        row[f"h{h}_median_pairs"] = float(pair_count.loc[:DISCOVERY_END].median())
    primary_ic = horizon_ic[PRIMARY]
    discovery = primary_ic.loc[:DISCOVERY_END].dropna()
    audit = primary_ic.loc[AUDIT_START:AUDIT_END].dropna()
    row["discovery_ic"] = float(discovery.mean())
    row["discovery_days"] = int(len(discovery))
    row["seen_audit_ic"] = float(audit.mean()) if len(audit) else np.nan
    row["seen_audit_days"] = int(len(audit))
    row["all_horizons_same_direction"] = bool(
        all(
            np.isfinite(row[f"h{h}_discovery_ic"])
            and np.sign(row[f"h{h}_discovery_ic"]) == np.sign(row[f"h{PRIMARY}_discovery_ic"])
            for h in HORIZONS
        )
    )
    direction = float(np.sign(row["discovery_ic"]))
    row["direction"] = direction
    years = {}
    matches = 0
    for year in (2021, 2022, 2023):
        values = primary_ic[primary_ic.index.year == year].dropna()
        mean = float(values.mean()) if len(values) else np.nan
        years[f"ic_{year}"] = mean
        if np.isfinite(mean) and np.sign(mean) == direction:
            matches += 1
    row.update(years)
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
    row["identity_gate_pass"] = identity_gate(loso, direction, GATES["min_abs_seen_audit_ic"])
    row["identity_min_discovery_ic_signed"] = float((loso["discovery_ic"] * direction).min())
    row["identity_min_audit_ic_signed"] = float((loso["seen_audit_ic"] * direction).min())
    row["daily_ic"] = primary_ic
    row["signal"] = signal
    return row


def _residual_diagnostic(
    signal: pd.DataFrame,
    shelf: dict[str, pd.DataFrame],
    forward: pd.DataFrame,
    eligibility: pd.DataFrame,
) -> tuple[float, float]:
    """Research-only redundancy diagnostic: regress the candidate on whatever
    shelf factors are jointly observed each day (>=8 names, >=3 regressors).
    Not a gate; NaN-tolerant because shelf coverage is partial on early dates."""
    names = sorted(shelf)
    result = pd.DataFrame(np.nan, index=signal.index, columns=signal.columns)
    for date in signal.index:
        columns = [signal.loc[date].rename("candidate")]
        columns.extend(
            shelf[name].loc[date].rename(name) if date in shelf[name].index
            else pd.Series(np.nan, index=signal.columns, name=name)
            for name in names
        )
        pair = pd.concat(columns, axis=1)
        usable = [c for c in pair.columns[1:] if pair[c].notna().sum() >= 8]
        if len(usable) < 3:
            continue
        pair = pair[["candidate", *usable]].dropna()
        if len(pair) < 8:
            continue
        x = pair[usable].to_numpy(dtype=float)
        x = np.column_stack([np.ones(len(x)), x])
        y = pair["candidate"].to_numpy(dtype=float)
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        result.loc[date, pair.index] = y - x @ beta
    daily_ic, _ = common_sample_spearman(result, forward, eligibility, MIN_PAIRS)
    disc = daily_ic.loc[:DISCOVERY_END].dropna()
    audit = daily_ic.loc[AUDIT_START:AUDIT_END].dropna()
    return (
        float(disc.mean()) if len(disc) else np.nan,
        float(audit.mean()) if len(audit) else np.nan,
    )


def _gate_report(row: dict[str, object]) -> tuple[bool, list[str]]:
    failures = []
    if row["discovery_days"] < GATES["min_discovery_days"]:
        failures.append("discovery_days")
    if not np.isfinite(row["discovery_ic"]) or abs(row["discovery_ic"]) < GATES["min_abs_ic"]:
        failures.append("abs_discovery_ic")
    if not np.isfinite(row["seen_audit_ic"]) or row["seen_audit_ic"] * row["direction"] < GATES["min_abs_seen_audit_ic"]:
        failures.append("signed_seen_audit_ic")
    if not row["all_horizons_same_direction"]:
        failures.append("horizon_direction")
    if row["year_direction_count"] < GATES["min_year_direction_count"]:
        failures.append("year_direction")
    if not row["identity_gate_pass"]:
        failures.append("identity_gate")
    if row.get("max_abs_rank_corr", np.nan) >= GATES["max_abs_factor_rank_corr"] or not np.isfinite(
        row.get("max_abs_rank_corr", np.nan)
    ):
        failures.append("rank_correlation_redundancy")
    return (not failures), failures


def _leak_checks(ranked: dict[str, pd.DataFrame], eligibility_all: pd.DataFrame, plan: dict) -> dict:
    names = sorted(
        {cand[s]["name"] for cand in plan["candidates"] for s in ("left", "right")}
    )
    load_builtin_families()
    # (a) prefix invariance: truncate inputs at discovery end, scores must match.
    trunc_panels = load_canonical_daily(CANONICAL_ROOT, UNIVERSE_CONFIG, as_of=AS_OF)
    trunc_panels = {k: v.loc[:DISCOVERY_END].copy() for k, v in trunc_panels.items()}
    trunc_elig = build_pit_eligibility(trunc_panels, MIN_HISTORY, True)
    # (b) future perturbation: scramble post-discovery data, prefix scores frozen.
    rng = np.random.default_rng(20260919)
    pert_panels = load_canonical_daily(CANONICAL_ROOT, UNIVERSE_CONFIG, as_of=AS_OF)
    mask = pert_panels["close"].index > DISCOVERY_END
    pert_panels = {
        k: v.copy() for k, v in pert_panels.items()
    }
    for frame in pert_panels.values():
        noise = 1.0 + rng.normal(0.0, 0.05, size=frame.shape)
        rows = frame.index.get_indexer(frame.index[mask])
        frame.iloc[rows] = frame.iloc[rows] * noise[rows]
    pert_elig = build_pit_eligibility(pert_panels, MIN_HISTORY, True)
    results = {"atoms_checked": len(names), "prefix_invariance": {}, "future_perturbation": {}}
    for source in sorted({cand[s]["source"] for cand in plan["candidates"] for s in ("left", "right")}):
        mining = yaml.safe_load(_config_path(source).read_text())
        space_trunc = resolve_family(source).builder(trunc_panels, trunc_elig, CANONICAL_ROOT, mining)
        space_pert = resolve_family(source).builder(pert_panels, pert_elig, CANONICAL_ROOT, mining)
        for name in sorted(set(mining_atom["name"] for mining_atom in mining["atoms"]) & set(names)):
            base = ranked[name]
            symbols = base.columns
            trunc = cross_sectional_rank(
                space_trunc[name].reindex(index=base.index, columns=symbols),
                trunc_elig[symbols],
            )
            pert = cross_sectional_rank(
                space_pert[name].reindex(index=base.index, columns=symbols),
                pert_elig[symbols],
            )
            common_idx = base.index.intersection(trunc.index)
            diff = np.nanmax(
                np.abs(base.loc[common_idx].to_numpy() - trunc.loc[common_idx].to_numpy())
            )
            results["prefix_invariance"][f"{source}:{name}"] = float(diff)
            common_idx = base.index[base.index <= DISCOVERY_END]
            diff = np.nanmax(
                np.abs(base.loc[common_idx].to_numpy() - pert.loc[common_idx].to_numpy())
            )
            results["future_perturbation"][f"{source}:{name}"] = float(diff)
    results["prefix_max_abs_diff"] = max(results["prefix_invariance"].values())
    results["perturbation_max_abs_diff"] = max(results["future_perturbation"].values())
    results["pass"] = (
        results["prefix_max_abs_diff"] <= 1e-12 and results["perturbation_max_abs_diff"] <= 1e-12
    )
    return results


def cmd_evaluate(args: argparse.Namespace) -> None:
    output = Path(args.output).resolve()
    plan_path = output / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan_sha = _hash(plan_path)
    only = set(args.only.split(",")) if args.only else None
    candidates = [c for c in plan["candidates"] if only is None or c["id"] in only]
    assert candidates, "no candidates selected"

    panels, eligibility_all, symbols, forward = _load_context()
    ranked = _build_atoms(panels, eligibility_all, symbols, plan)
    eligibility = eligibility_all[symbols]

    rows = []
    for cand in candidates:
        spec = _expression_spec(cand)
        signal = materialize_expression(spec, ranked)
        row = {"candidate_id": cand["id"], "expression": spec.readable,
               "mechanism": cand["mechanism"], "expected_sign": cand["expected_sign"]}
        row.update(_evaluate_one(signal, forward, eligibility))
        rows.append(row)

    shelf = _shelf_scores(symbols, ranked[next(iter(ranked))].index)
    for row in rows:
        corrs = {key: _stack_corr(row["signal"], frame) for key, frame in shelf.items()}
        for other in rows:
            if other is row:
                continue
            corrs[f"round:{other['candidate_id']}"] = _stack_corr(row["signal"], other["signal"])
        finite = {k: v for k, v in corrs.items() if np.isfinite(v)}
        row["rank_corrs"] = corrs
        row["max_abs_rank_corr"] = max((abs(v) for v in finite.values()), default=np.nan)
        row["max_abs_rank_corr_vs"] = max(finite, key=lambda k: abs(finite[k])) if finite else ""
        residual_disc, residual_audit = _residual_diagnostic(row["signal"], shelf, forward[PRIMARY], eligibility)
        row["residual_discovery_ic"] = residual_disc
        row["residual_seen_audit_ic"] = residual_audit

    checks = _leak_checks(ranked, eligibility_all, plan)

    for row in rows:
        passed, failures = _gate_report(row)
        row["gate_pass"] = passed
        row["gate_failures"] = ",".join(failures)
        row["evidence_status"] = EVIDENCE_STATUS if passed else "rejected_this_round"

    if args.mode == "validate":
        for row in rows:
            print(
                f"[validate] {row['candidate_id']} {row['expression']} "
                f"disc_ic={row['discovery_ic']:.4f} days={row['discovery_days']} "
                f"audit_ic={row['seen_audit_ic']:.4f} years={row['year_direction_count']} "
                f"identity={row['identity_gate_pass']} maxcorr={row['max_abs_rank_corr']:.3f}({row['max_abs_rank_corr_vs']}) "
                f"residual_disc={row['residual_discovery_ic']:.4f} pass={row['gate_pass']} fails={row['gate_failures']}"
            )
        print(
            f"[leak] prefix_max_abs_diff={checks['prefix_max_abs_diff']:.3e} "
            f"perturbation_max_abs_diff={checks['perturbation_max_abs_diff']:.3e} pass={checks['pass']}"
        )
        return

    output.mkdir(parents=True, exist_ok=True)
    meta_columns = [
        "candidate_id", "expression", "mechanism", "expected_sign", "direction",
        "discovery_ic", "discovery_days", "seen_audit_ic", "seen_audit_days",
        "h5_discovery_ic", "h10_discovery_ic", "h20_discovery_ic",
        "ic_2021", "ic_2022", "ic_2023", "year_direction_count",
        "all_horizons_same_direction", "identity_gate_pass",
        "identity_min_discovery_ic_signed", "identity_min_audit_ic_signed",
        "max_abs_rank_corr", "max_abs_rank_corr_vs",
        "residual_discovery_ic", "residual_seen_audit_ic",
        "gate_pass", "gate_failures", "evidence_status",
    ]
    metrics = pd.DataFrame(rows)[meta_columns]
    metrics.to_csv(output / "candidate_metrics.csv", index=False)
    corr_dump = {
        row["candidate_id"]: {k: round(v, 6) for k, v in row["rank_corrs"].items() if np.isfinite(v)}
        for row in rows
    }
    (output / "rank_correlations.json").write_text(json.dumps(corr_dump, ensure_ascii=False, indent=2))

    v9 = _v9_manifest()
    cmd = v9["command"]
    status = {
        "round_id": "round_001",
        "as_of": AS_OF,
        "plan_sha256": plan_sha,
        "script_sha256": _hash(SCRIPT),
        "universe_config": str(UNIVERSE_CONFIG),
        "universe_config_sha256": _hash(UNIVERSE_CONFIG),
        "canonical_root": str(CANONICAL_ROOT),
        "contract_source": str(LEDGER_MANIFEST),
        "contract_generation": v9["generation"],
        "surfaces": plan["surfaces"],
        "gates": GATES,
        "evidence_status": EVIDENCE_STATUS,
        "n_preregistered": len(candidates),
        "n_gate_pass": int(sum(bool(r["gate_pass"]) for r in rows)),
        "candidates": [
            {
                "id": r["candidate_id"], "expression": r["expression"],
                "mechanism": r["mechanism"], "discovery_ic": r["discovery_ic"],
                "seen_audit_ic": r["seen_audit_ic"], "gate_pass": bool(r["gate_pass"]),
                "gate_failures": r["gate_failures"],
            }
            for r in rows
        ],
        "leak_checks": {
            "prefix_invariance_max_abs_diff": checks["prefix_max_abs_diff"],
            "future_perturbation_max_abs_diff": checks["perturbation_max_abs_diff"],
            "pass": checks["pass"],
            "scanner": "scan_future_leaks.py run separately; negative shift only in label construction",
        },
        "independent_oos": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": sys.argv,
    }
    (output / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2))

    lines = [
        "# Round 001 挖掘报告（预注册 6 条跨源组合表达式）",
        "",
        f"计划锁定哈希: `{plan_sha[:16]}…`；as_of={AS_OF}；契约复制自 v9 家族裁判（人口/标签/时间面/门槛未改）。",
        f"发现面截至 2023-12-31；2024-01-01~2025-04-30 为已见审计面；2025-04-30 之后未参与。",
        "",
        "| 候选 | 表达式 | 机制 | 发现IC | 有效日 | 已见审计IC | 2021-23同向 | LOSO | 最大|rank corr| | 残差发现IC | 结论 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['candidate_id']} | {row['expression']} | {row['mechanism']} "
            f"| {row['discovery_ic']:+.4f} | {row['discovery_days']} "
            f"| {row['seen_audit_ic']:+.4f} | {row['year_direction_count']}/3 "
            f"| {'通过' if row['identity_gate_pass'] else '未过'} "
            f"| {row['max_abs_rank_corr']:.2f} ({row['max_abs_rank_corr_vs']}) "
            f"| {row['residual_discovery_ic']:+.4f} "
            f"| {'PASS(非认证候选)' if row['gate_pass'] else '拒绝:' + row['gate_failures']} |"
        )
    lines += [
        "",
        f"泄漏检查：前缀不变最大差 {checks['prefix_max_abs_diff']:.2e}；未来扰动最大差 "
        f"{checks['perturbation_max_abs_diff']:.2e}（特征只用D及更早信息，负向 shift 仅出现在标签 open(D+2+H)/open(D+2)）。",
        "",
        "全部通过候选仅为 discovery_candidate_not_certified，不构成正式认证或可交易策略。",
    ]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(f"round_001 batch complete: pass={status['n_gate_pass']}/{len(candidates)} output={output}")


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
