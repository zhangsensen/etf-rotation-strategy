#!/usr/bin/env python3
"""Run one generation of the isolated ETF expression-mining loop."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from etf_strategy.core.data_loader import DataLoader
from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core.etf_factor_grammar import (
    ETF_RESEARCH_DOMAIN,
    active_forward_return,
    build_pit_eligibility,
    cross_sectional_rank,
    enumerate_expressions,
    expression_source_is_etf_only,
    materialize_expression,
    parse_atoms,
)
from etf_strategy.core.etf_factor_referee import (
    block_mean_pvalue,
    gpu_daily_rank_ic,
    holm_rejections,
    rolling_direction_stability,
    summarize_daily_ic,
    top_n_active_return,
)
from etf_strategy.core.ohlcv_factor_mining import build_ohlcv_factor_space
from etf_strategy.core.etf_share_factor_space import (
    apply_share_availability_lag,
    build_share_factor_space,
)
from etf_strategy.core.etf_cross_asset_factor_space import (
    build_cross_asset_factor_space,
    parse_asset_classes,
)
from etf_strategy.core.etf_liquidity_factor_space import build_liquidity_factor_space
from etf_strategy.core.etf_benchmark_factor_space import build_benchmark_factor_space
from etf_strategy.core.etf_serial_dependence_factor_space import (
    build_serial_dependence_factor_space,
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--data-config", type=Path)
    source.add_argument("--canonical-data-root", type=Path)
    parser.add_argument("--universe-config", type=Path)
    parser.add_argument("--as-of")
    parser.add_argument("--mining-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument(
        "--legacy-replay",
        action="store_true",
        help="explicitly replay the retired expression enumerator",
    )
    return parser.parse_args()


def _load_research_panels(args, mining: dict) -> tuple[dict[str, pd.DataFrame], dict, DataLoader | None]:
    """Load either the historical package or the maintained 20-ETF store.

    The canonical path loads every maintained symbol first, then applies the
    predeclared role contract to the ranking population.  Benchmarks and
    observations therefore cannot leak into the cross-sectional label.
    """
    if args.data_config is not None:
        if args.universe_config is not None or args.as_of is not None:
            raise ValueError("--universe-config/--as-of belong to canonical data mode")
        data_path = args.data_config.resolve()
        data_config = yaml.safe_load(data_path.read_text())
        data_cfg = data_config["data"]
        loader = DataLoader(data_dir=data_cfg["data_dir"], cache_dir=data_cfg.get("cache_dir"))
        panels = loader.load_ohlcv(
            etf_codes=data_cfg["symbols"],
            start_date=data_cfg["start_date"],
            end_date=data_cfg["end_date"],
            use_cache=True,
        )
        return panels, {
            "mode": "legacy_config",
            "data_config": str(data_path),
            "data_config_hash": _sha256(data_path),
            "maintained_symbols": len(panels["close"].columns),
            "ranking_symbols": list(panels["close"].columns),
            "ranking_roles": None,
        }, loader

    if args.universe_config is None or args.as_of is None:
        raise ValueError("Canonical mode requires --universe-config and --as-of")
    universe_path = args.universe_config.resolve()
    universe = json.loads(universe_path.read_text())
    rows = universe["etfs"]
    ranking_roles = tuple(mining["population"].get("ranking_roles", ()))
    if not ranking_roles:
        raise ValueError("Canonical mode requires population.ranking_roles")
    known_roles = {row["role"] for row in rows}
    if not set(ranking_roles) <= known_roles:
        raise ValueError("Unknown ranking role in mining config")
    all_panels = load_canonical_daily(
        args.canonical_data_root.resolve(), universe_path, as_of=args.as_of
    )
    ranking_symbols = [row["ts_code"] for row in rows if row["role"] in ranking_roles]
    panels = {name: panel.loc[:, ranking_symbols] for name, panel in all_panels.items()}
    return panels, {
        "mode": "canonical_20",
        "data_root": str(args.canonical_data_root.resolve()),
        "universe_config": str(universe_path),
        "universe_config_hash": _sha256(universe_path),
        "maintained_symbols": len(rows),
        "ranking_symbols": ranking_symbols,
        "ranking_roles": list(ranking_roles),
        "excluded_by_role": [row["ts_code"] for row in rows if row["ts_code"] not in ranking_symbols],
        "as_of": args.as_of,
    }, None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean_abs_daily_rank_corr(
    left: pd.DataFrame,
    right: pd.DataFrame,
    min_pairs: int,
) -> float:
    daily, _ = gpu_daily_rank_ic(left, right, min_pairs)
    return float(daily.abs().mean())


def _median_pairs_on_scored_days(daily_ic: pd.Series, pair_count: pd.Series) -> float:
    """Summarize population size only where the referee actually scored an IC."""
    scored = pair_count.reindex(daily_ic.index).where(daily_ic.notna()).dropna()
    return float(scored.median()) if not scored.empty else np.nan


def _ensure_ledger(path: Path):
    import duckdb

    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(path))
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS etf_factor_generations (
            research_domain VARCHAR NOT NULL,
            grammar_version VARCHAR NOT NULL,
            expression_id VARCHAR NOT NULL,
            expression VARCHAR NOT NULL,
            family VARCHAR NOT NULL,
            operator VARCHAR NOT NULL,
            discovery_mean_ic DOUBLE,
            ordered_audit_mean_ic DOUBLE,
            seen_mean_ic DOUBLE,
            direction INTEGER,
            block_pvalue DOUBLE,
            holm_pass BOOLEAN,
            pre_gate_pass BOOLEAN,
            ordered_audit_pass BOOLEAN,
            final_gate_pass BOOLEAN,
            selected_after_redundancy BOOLEAN,
            run_hash VARCHAR NOT NULL,
            tested_at TIMESTAMP NOT NULL,
            PRIMARY KEY (research_domain, grammar_version, expression_id)
        )
        """
    )
    return connection


def _build_report(
    output: Path,
    manifest: dict,
    summary: pd.DataFrame,
    selected: list[str],
) -> None:
    pre_count = int(summary["pre_gate_pass"].sum())
    holm_count = int(summary["holm_pass"].sum())
    audit_count = int(summary["ordered_audit_pass"].sum())
    final_count = int(summary["final_gate_pass"].sum())
    lines = [
        "# ETF自动表达式挖掘",
        "",
        "## 固定合同",
        "",
        f"- 研究域：`{manifest['research_domain']}`，与个股因子和裁判完全隔离。",
        f"- 人口：维护池{manifest['maintained_symbols']}只，角色约束后的排名池"
        f"{manifest['symbols']}只，再按当日历史长度动态进入；"
        "缺少历史已清盘ETF，因此不能据此完成无幸存偏差认证。",
        f"- 标签：{manifest['label_contract']}。",
        f"- 语法：{manifest['grammar_version']}，共{manifest['generated_expressions']}个表达式。",
        f"- GPU：{manifest['gpu']['device']} / CuPy {manifest['gpu']['cupy_version']}。",
        "",
        "## 漏斗",
        "",
        f"- 发现稳定性门：{pre_count}/{len(summary)}。",
        f"- 全表达式Holm校正：{holm_count}/{len(summary)}。",
        f"- 顺序审计方向及幅度门：{audit_count}/{len(summary)}。",
        f"- 三者同时通过：{final_count}/{len(summary)}。",
        f"- 去冗余最终候选：{len(selected)}。",
        "",
        "## 判定",
        "",
    ]
    if selected:
        lines.append("进入下一阶段的表达式：" + "、".join(f"`{item}`" for item in selected) + "。")
        lines.append("这些仍是已见历史上的发现候选，不是正式认证或实盘许可。")
    else:
        lines.append("本代没有表达式同时通过全部门，输出有效零结果；不得放宽门槛或改权重救援。")
    next_dimension = {
        "ohlcv": "补PIT人口或增加独立的份额流语法",
        "fund_share": "补PIT人口或预注册新的独立价格机制语法",
        "cross_asset": "补PIT人口或预注册新的独立关系语法",
        "liquidity": "补PIT人口或预注册新的独立交易机制语法",
        "benchmark_relative": "补PIT人口或预注册新的独立相对关系语法",
        "serial_dependence": "补PIT人口或预注册新的独立序列机制语法",
    }.get(manifest["factor_source"], "补PIT人口或预注册下一独立信息维度")
    lines.extend(
        [
            "",
            f"当前人口仍缺历史清盘ETF，跨牛熊结论保持未认证。下一步只允许{next_dimension}，",
            "不能把个股因子库、个股事件裁判或个股执行规则接入本研究域。",
            "",
            "## 证据",
            "",
            "`factor_summary.csv`、`daily_ic.parquet`、`expression_registry.json`、",
            "`redundancy_screen.csv`和`run_manifest.json`。完整命令记录于manifest。",
        ]
    )
    (output / "REPORT.md").write_text("\n".join(lines) + "\n")


def main():
    args = parse_args()
    if not args.legacy_replay:
        raise SystemExit(
            "retired candidate generator: use "
            "scripts/research/pi_glm_mining/discover_from_outcomes.py discover; "
            "pass --legacy-replay only to reproduce a historical run"
        )
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty output directory")
    output.mkdir(parents=True, exist_ok=True)

    mining_path = args.mining_config.resolve()
    mining = yaml.safe_load(mining_path.read_text())
    if mining.get("domain") != ETF_RESEARCH_DOMAIN or not expression_source_is_etf_only():
        raise ValueError("Mining config is not in the isolated ETF research domain")
    (output / "resolved_mining_config.yaml").write_text(
        yaml.safe_dump(mining, allow_unicode=True, sort_keys=False)
    )

    import cupy as cp

    if cp.cuda.runtime.getDeviceCount() < 1:
        raise RuntimeError("ETF automated mining requires CUDA")
    ohlcv, data_contract, legacy_loader = _load_research_panels(args, mining)
    population_cfg = mining["population"]
    eligibility = build_pit_eligibility(
        ohlcv,
        min_history_sessions=int(population_cfg["min_history_sessions"]),
        require_positive_volume=bool(population_cfg["require_positive_volume"]),
    )
    factor_source_name = str(mining.get("factor_source", ""))
    availability_lag = int(mining.get("availability_lag_sessions", 0))
    if factor_source_name == "ohlcv":
        if availability_lag != 0:
            raise ValueError("OHLCV grammar v1 expects zero additional availability lag")
        all_factors = build_ohlcv_factor_space(ohlcv)
        factor_source = ROOT / "src/etf_strategy/core/ohlcv_factor_mining.py"
    elif factor_source_name == "fund_share":
        if legacy_loader is None:
            raise ValueError("Canonical ETF store has no point-in-time fund-share contract")
        share_panel = legacy_loader.load_fund_share(
            etf_codes=list(ohlcv["close"].columns),
            trading_dates=ohlcv["close"].index,
        ).reindex(columns=ohlcv["close"].columns)
        all_factors = apply_share_availability_lag(
            build_share_factor_space(share_panel), availability_lag
        )
        factor_source = ROOT / "src/etf_strategy/core/etf_share_factor_space.py"
    elif factor_source_name == "cross_asset":
        if availability_lag != 0:
            raise ValueError("Cross-asset close factors expect zero additional availability lag")
        asset_class_path = Path(str(mining["asset_class_config"]))
        if not asset_class_path.is_absolute():
            asset_class_path = (ROOT / asset_class_path).resolve()
        asset_class_config = yaml.safe_load(asset_class_path.read_text())
        symbol_to_class = parse_asset_classes(
            asset_class_config["classes"], list(ohlcv["close"].columns)
        )
        all_factors = build_cross_asset_factor_space(
            ohlcv["close"], eligibility, symbol_to_class
        )
        factor_source = ROOT / "src/etf_strategy/core/etf_cross_asset_factor_space.py"
    elif factor_source_name == "liquidity":
        if availability_lag != 0:
            raise ValueError("Daily ETF liquidity factors expect zero additional availability lag")
        all_factors = build_liquidity_factor_space(ohlcv)
        factor_source = ROOT / "src/etf_strategy/core/etf_liquidity_factor_space.py"
    elif factor_source_name == "benchmark_relative":
        if availability_lag != 0:
            raise ValueError("Benchmark-relative close factors expect zero availability lag")
        all_factors = build_benchmark_factor_space(
            ohlcv["close"], tuple(mining["benchmark_symbols"])
        )
        factor_source = ROOT / "src/etf_strategy/core/etf_benchmark_factor_space.py"
    elif factor_source_name == "serial_dependence":
        if availability_lag != 0:
            raise ValueError("Serial-dependence close factors expect zero availability lag")
        all_factors = build_serial_dependence_factor_space(ohlcv)
        factor_source = ROOT / "src/etf_strategy/core/etf_serial_dependence_factor_space.py"
    else:
        raise ValueError(f"Unsupported isolated ETF factor source: {factor_source_name!r}")
    atoms = parse_atoms(mining["atoms"])
    missing_atoms = sorted({atom.name for atom in atoms} - set(all_factors))
    if missing_atoms:
        raise ValueError(f"ETF grammar atoms missing implementations: {missing_atoms}")
    ranked_atoms = {
        atom.name: cross_sectional_rank(all_factors[atom.name], eligibility) for atom in atoms
    }
    expressions = enumerate_expressions(
        atoms,
        mining["grammar"]["operators"],
        pair_policy=mining["grammar"]["pair_policy"],
    )
    connection = _ensure_ledger(args.ledger.resolve())
    prior_count = connection.execute(
        """SELECT count(*) FROM etf_factor_generations
           WHERE research_domain = ? AND grammar_version = ?""",
        [ETF_RESEARCH_DOMAIN, mining["grammar_version"]],
    ).fetchone()[0]
    if prior_count:
        connection.close()
        raise ValueError(
            f"ETF grammar version {mining['grammar_version']} already has {prior_count} tested "
            "expressions in the ledger; use a new version for a new hypothesis"
        )

    execution = mining["execution"]
    horizons = [int(value) for value in execution["horizons"]]
    primary_horizon = int(execution["primary_horizon"])
    entry_lag = int(execution["entry_lag_sessions"])
    active_returns = {
        horizon: active_forward_return(ohlcv["open"], eligibility, horizon, entry_lag)
        for horizon in horizons
    }
    active_ranks = {
        horizon: cross_sectional_rank(active_returns[horizon], eligibility)
        for horizon in horizons
    }
    surfaces = mining["surfaces"]
    discovery_end = pd.Timestamp(surfaces["discovery_end"])
    audit_start = pd.Timestamp(surfaces["ordered_audit_start"])
    audit_end = pd.Timestamp(surfaces["ordered_audit_end"])
    seen_start = pd.Timestamp(surfaces["seen_diagnostic_start"])
    gates = mining["gates"]
    min_pairs = int(gates["min_median_pairs"])

    registry = [
        {
            "expression_id": expression.expression_id,
            "expression": expression.readable,
            "operator": expression.operator,
            "left": expression.left,
            "right": expression.right,
            "family": expression.family,
        }
        for expression in expressions
    ]
    (output / "expression_registry.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2)
    )

    rows = []
    daily_rows = []
    primary_signals: dict[str, pd.DataFrame] = {}
    for sequence, expression in enumerate(expressions, start=1):
        raw_signal = materialize_expression(expression, ranked_atoms)
        signal = cross_sectional_rank(raw_signal, eligibility)
        horizon_metrics = {}
        primary_daily = None
        primary_pair_count = None
        for horizon in horizons:
            daily, pair_count = gpu_daily_rank_ic(signal, active_ranks[horizon], min_pairs)
            horizon_metrics[horizon] = summarize_daily_ic(daily.loc[:discovery_end])
            if horizon == primary_horizon:
                primary_daily = daily
                primary_pair_count = pair_count
                for date, ic, pairs in zip(daily.index, daily.to_numpy(), pair_count.to_numpy()):
                    daily_rows.append(
                        {"signal_date": date, "expression_id": expression.expression_id,
                         "horizon": horizon, "ic": ic, "pair_count": pairs}
                    )
        assert primary_daily is not None and primary_pair_count is not None
        discovery = primary_daily.loc[:discovery_end]
        ordered_audit = primary_daily.loc[audit_start:audit_end]
        seen = primary_daily.loc[seen_start:]
        discovery_stats = summarize_daily_ic(discovery)
        direction = 1 if discovery_stats["mean_ic"] >= 0 else -1
        stability, rolling_windows = rolling_direction_stability(discovery, direction)
        yearly = discovery.groupby(discovery.index.year).mean().dropna()
        year_agreement = float((np.sign(yearly) == direction).mean()) if len(yearly) else np.nan
        pvalue, block_count = block_mean_pvalue(discovery)
        horizon_same = all(
            np.sign(horizon_metrics[horizon]["mean_ic"]) == direction for horizon in horizons
        )
        median_pairs = _median_pairs_on_scored_days(
            discovery, primary_pair_count.loc[:discovery_end]
        )
        pre_gate = bool(
            discovery_stats["days"] >= int(gates["min_discovery_days"])
            and median_pairs >= min_pairs
            and abs(float(discovery_stats["mean_ic"])) >= float(gates["min_abs_discovery_ic"])
            and horizon_same
            and np.isfinite(stability)
            and stability >= float(gates["min_rolling_direction_stability"])
            and np.isfinite(year_agreement)
            and year_agreement >= float(gates["min_year_direction_agreement"])
        )
        audit_mean = float(ordered_audit.mean())
        ordered_audit_pass = bool(
            np.isfinite(audit_mean)
            and audit_mean * direction >= float(gates["min_abs_ordered_audit_ic"])
        )
        rows.append(
            {
                "expression_id": expression.expression_id,
                "expression": expression.readable,
                "family": expression.family,
                "operator": expression.operator,
                "direction": direction,
                "discovery_mean_ic": discovery_stats["mean_ic"],
                "discovery_icir_ann": discovery_stats["icir_ann"],
                "discovery_days": discovery_stats["days"],
                "median_pairs": median_pairs,
                "rolling_direction_stability": stability,
                "rolling_windows": rolling_windows,
                "year_direction_agreement": year_agreement,
                "all_horizons_same_direction": horizon_same,
                "block_pvalue": pvalue,
                "block_count": block_count,
                "ordered_audit_mean_ic": audit_mean,
                "seen_mean_ic": float(seen.mean()),
                "pre_gate_pass": pre_gate,
                "ordered_audit_pass": ordered_audit_pass,
                "sequence": sequence,
            }
        )
        if pre_gate and ordered_audit_pass:
            primary_signals[expression.expression_id] = signal

    summary = pd.DataFrame(rows).set_index("expression_id", drop=False)
    summary["holm_pass"] = holm_rejections(
        summary["block_pvalue"], float(gates["holm_alpha"])
    )
    summary["final_gate_pass"] = (
        summary["pre_gate_pass"] & summary["ordered_audit_pass"] & summary["holm_pass"]
    )
    summary["discovery_top2_active_bp"] = np.nan
    summary["audit_top2_active_bp"] = np.nan
    for expression_id in summary.index[summary["final_gate_pass"]]:
        signal = primary_signals[expression_id]
        direction = int(summary.loc[expression_id, "direction"])
        summary.loc[expression_id, "discovery_top2_active_bp"] = 1e4 * top_n_active_return(
            signal.loc[:discovery_end],
            active_returns[primary_horizon].loc[:discovery_end],
            direction,
        )
        summary.loc[expression_id, "audit_top2_active_bp"] = 1e4 * top_n_active_return(
            signal.loc[audit_start:audit_end],
            active_returns[primary_horizon].loc[audit_start:audit_end],
            direction,
        )

    passed = summary.loc[summary["final_gate_pass"]].copy()
    passed["abs_discovery_ic"] = passed["discovery_mean_ic"].abs()
    passed = passed.sort_index().sort_values("abs_discovery_ic", ascending=False, kind="stable")
    selected: list[str] = []
    redundancy_rows = []
    threshold = float(gates["redundancy_max_abs_rank_corr"])
    for expression_id in passed.index:
        blocker = None
        blocker_corr = np.nan
        signal = primary_signals[expression_id].loc[:audit_end]
        for kept in selected:
            corr = _mean_abs_daily_rank_corr(signal, primary_signals[kept].loc[:audit_end], min_pairs)
            if corr >= threshold:
                blocker, blocker_corr = kept, corr
                break
        keep = blocker is None
        if keep:
            selected.append(expression_id)
        redundancy_rows.append(
            {"expression_id": expression_id, "selected": keep, "blocked_by": blocker,
             "mean_abs_daily_rank_corr": blocker_corr}
        )
    summary["selected_after_redundancy"] = summary.index.isin(selected)
    summary = summary.sort_values(
        ["selected_after_redundancy", "final_gate_pass", "discovery_mean_ic"],
        ascending=[False, False, False],
    )

    summary.to_csv(output / "factor_summary.csv", index=False)
    pd.DataFrame(daily_rows).to_parquet(output / "daily_ic.parquet", index=False)
    pd.DataFrame(redundancy_rows).to_csv(output / "redundancy_screen.csv", index=False)
    selected_payload = {
        "research_domain": ETF_RESEARCH_DOMAIN,
        "grammar_version": mining["grammar_version"],
        "selected_expression_ids": selected,
        "selected": summary.loc[selected, ["expression", "family", "direction"]].to_dict(
            orient="index"
        ) if selected else {},
        "strategy_usable": False,
    }
    (output / "selected_expressions.json").write_text(
        json.dumps(selected_payload, ensure_ascii=False, indent=2)
    )

    grammar_source = ROOT / "src/etf_strategy/core/etf_factor_grammar.py"
    run_hash_payload = {
        "data_contract": hashlib.sha256(
            json.dumps(data_contract, sort_keys=True).encode()
        ).hexdigest(),
        "mining_config": _sha256(mining_path),
        "factor_source": _sha256(factor_source),
        "grammar_source": _sha256(grammar_source),
        "runner_source": _sha256(Path(__file__).resolve()),
        "window_end": str(ohlcv["close"].index.max().date()),
    }
    if factor_source_name == "cross_asset":
        run_hash_payload["asset_class_config"] = _sha256(asset_class_path)
    run_hash = hashlib.sha256(
        json.dumps(run_hash_payload, sort_keys=True).encode()
    ).hexdigest()
    device_name = cp.cuda.runtime.getDeviceProperties(0)["name"]
    if isinstance(device_name, bytes):
        device_name = device_name.decode()
    manifest = {
        "research_domain": ETF_RESEARCH_DOMAIN,
        "stock_factor_registry_imported": False,
        "stock_referee_imported": False,
        "grammar_version": mining["grammar_version"],
        "factor_source": factor_source_name,
        "availability_lag_sessions": availability_lag,
        "generated_expressions": len(expressions),
        "symbols": len(ohlcv["close"].columns),
        "maintained_symbols": data_contract["maintained_symbols"],
        "data_contract": data_contract,
        "population_contract": (
            "predeclared current roles followed by point-in-time entry from observed history "
            "and current OHLCV/volume; source pool lacks historical liquidated ETFs"
        ),
        "population_is_survivorship_complete": False,
        "window": [str(ohlcv["close"].index.min().date()), str(ohlcv["close"].index.max().date())],
        "surfaces": surfaces,
        "label_contract": (
            f"available signal on D; enter open D+{entry_lag}; ETF forward return minus "
            f"same-day PIT eligible-pool EW; horizons={horizons}"
        ),
        "multiple_testing": "Holm-Bonferroni over all generated expression block-mean p-values",
        "run_hash": run_hash,
        "source_hashes": run_hash_payload,
        "gpu": {"backend": "cupy", "cupy_version": cp.__version__, "device": device_name},
        "command": sys.argv,
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))

    tested_at = datetime.now(timezone.utc).replace(tzinfo=None)
    records = []
    for row in summary.itertuples(index=False):
        records.append(
            [ETF_RESEARCH_DOMAIN, mining["grammar_version"], row.expression_id, row.expression,
             row.family, row.operator, row.discovery_mean_ic, row.ordered_audit_mean_ic,
             row.seen_mean_ic, int(row.direction), row.block_pvalue, bool(row.holm_pass),
             bool(row.pre_gate_pass), bool(row.ordered_audit_pass), bool(row.final_gate_pass),
             bool(row.selected_after_redundancy), run_hash, tested_at]
        )
    connection.executemany(
        "INSERT INTO etf_factor_generations VALUES " + "(" + ",".join(["?"] * 18) + ")",
        records,
    )
    ledger_rows = connection.execute(
        "SELECT count(*) FROM etf_factor_generations WHERE research_domain = ?",
        [ETF_RESEARCH_DOMAIN],
    ).fetchone()[0]
    connection.close()
    manifest["ledger"] = str(args.ledger.resolve())
    manifest["ledger_etf_rows_after_run"] = int(ledger_rows)
    (output / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    _build_report(output, manifest, summary, selected)

    print(
        f"ETF generation complete: expressions={len(summary)}, "
        f"pre_gate={int(summary.pre_gate_pass.sum())}, holm={int(summary.holm_pass.sum())}, "
        f"audit={int(summary.ordered_audit_pass.sum())}, "
        f"final={int(summary.final_gate_pass.sum())}, selected={len(selected)}"
    )
    if selected:
        print(summary.loc[selected, ["expression", "family", "direction", "discovery_mean_ic",
                                     "ordered_audit_mean_ic", "seen_mean_ic"]].to_string(index=False))
    print(f"Wrote isolated ETF mining generation to {output}")


if __name__ == "__main__":
    main()
