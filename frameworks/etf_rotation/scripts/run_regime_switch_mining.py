#!/usr/bin/env python3
"""Run the first isolated ETF market-regime state mining generation."""
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

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core.etf_market_state_space import (
    build_market_state_space,
    parse_state_atoms,
    past_zscore,
)
from etf_strategy.core.etf_regime_label import (
    basket_spec_from_universe,
    build_regime_labels,
    label_contract,
)
from etf_strategy.core.etf_regime_referee import (
    directional_block_gate,
    generation_family_holm,
    directional_signature,
    hierarchical_family_holm,
    negative_effect_pvalue,
    non_overlapping,
    robust_block_pvalue,
)
from etf_strategy.core.etf_regime_grammar import enumerate_regime_expressions, materialize_regime_expression


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-data-root", type=Path, required=True)
    parser.add_argument("--universe-config", type=Path, required=True)
    parser.add_argument("--mining-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    return parser.parse_args()


def _ledger(path: Path):
    import duckdb

    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS etf_regime_attempts (
            generation VARCHAR NOT NULL,
            grammar_version VARCHAR NOT NULL,
            expression_id VARCHAR NOT NULL,
            expression VARCHAR NOT NULL,
            family VARCHAR NOT NULL,
            pvalue DOUBLE,
            direction INTEGER,
            final_pass BOOLEAN,
            run_hash VARCHAR NOT NULL,
            tested_at TIMESTAMP NOT NULL,
            PRIMARY KEY (generation, grammar_version, expression_id)
        )
        """
    )
    return con


def _block_summary(signal, labels, horizon, block):
    frame = labels[int(horizon)].set_index("signal_date")
    pair = pd.concat([signal.rename("signal"), frame["basket_spread"].rename("label")], axis=1).dropna()
    pair = pair.loc[pd.Timestamp(block[0]) : pd.Timestamp(block[1])]
    pair = pair.iloc[:: int(horizon)]
    # State skill is the covariance between the signed state and the basket
    # spread.  The state itself is frozen before outcomes are read; this score
    # does not rank ETFs or use a cross-sectional benchmark.
    series = (pair["signal"] * pair["label"]).rename("predictive_score")
    sampled = series.dropna()
    pvalue, block_count, median_effect = robust_block_pvalue(sampled)
    return float(sampled.mean()) if not sampled.empty else np.nan, pvalue, block_count, median_effect, len(sampled)


def _neutral_summary(signal, labels, horizon, block, direction, alpha):
    """Evaluate only statistically significant signed harm in a neutral block."""
    frame = labels[int(horizon)].set_index("signal_date")
    pair = pd.concat(
        [signal.rename("signal"), frame["basket_spread"].rename("label")], axis=1
    ).dropna()
    pair = pair.loc[pd.Timestamp(block[0]) : pd.Timestamp(block[1])]
    pair = pair.iloc[:: int(horizon)]
    signed = (pair["signal"] * pair["label"] * int(direction)).dropna()
    pvalue, block_count, median_effect = negative_effect_pvalue(signed)
    mean = float(signed.mean()) if not signed.empty else np.nan
    return mean, pvalue, block_count, median_effect, len(signed), bool(
        np.isfinite(mean) and mean < 0.0 and np.isfinite(pvalue) and pvalue < float(alpha)
    )


def main() -> None:
    args = _args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("use a new empty output directory")
    output.mkdir(parents=True, exist_ok=True)
    config_path = args.mining_config.resolve()
    config = yaml.safe_load(config_path.read_text())
    if config.get("domain") != "etf_rotation_regime":
        raise ValueError("regime config must declare etf_rotation_regime")
    universe_path = args.universe_config.resolve()
    panels = load_canonical_daily(args.canonical_data_root.resolve(), universe_path, as_of=args.as_of)
    basket = basket_spec_from_universe(
        universe_path,
        defensive_symbols=tuple(config["basket"]["defensive_symbols"]),
        min_attack_members=int(config["basket"]["min_attack_members"]),
        min_defensive_members=int(config["basket"]["min_defensive_members"]),
    )
    horizons = tuple(int(v) for v in config["execution"]["horizons"])
    entry_lag = int(config["execution"]["entry_lag_sessions"])
    labels = build_regime_labels(panels["open"], basket, horizons=horizons, entry_lag=entry_lag)
    rows = json.loads(universe_path.read_text())["etfs"]
    candidates = [r["ts_code"] for r in rows if r.get("role") == "candidate" and r["ts_code"] not in basket.defensive_symbols]
    state_raw = build_market_state_space(
        panels["close"], candidate_symbols=candidates,
        benchmark_symbols=tuple(config["state_inputs"]["benchmark_symbols"]),
        defensive_symbols=basket.defensive_symbols,
        min_attack_members=basket.min_attack_members,
        min_defensive_members=basket.min_defensive_members,
    )
    atom_specs = parse_state_atoms(config["atoms"])
    missing = sorted({a.name for a in atom_specs} - set(state_raw))
    if missing:
        raise ValueError(f"missing state atoms: {missing}")
    normalization_window = int(config["state_inputs"]["normalization_window"])
    normalization_min_observations = int(
        config["state_inputs"].get("normalization_min_observations", normalization_window)
    )
    states = {
        a.name: past_zscore(
            state_raw[a.name],
            normalization_window,
            normalization_min_observations,
        )
        for a in atom_specs
    }
    expressions = enumerate_regime_expressions(atom_specs, config["grammar"]["operators"], config["grammar"]["pair_policy"])
    prior = _ledger(args.ledger.resolve())
    generation = str(config["generation"])
    grammar = str(config["grammar_version"])
    if prior.execute(
        "SELECT count(*) FROM etf_regime_attempts WHERE generation = ? OR grammar_version = ?",
        [generation, grammar],
    ).fetchone()[0]:
        prior.close()
        raise ValueError("generation or grammar version already exists in regime ledger")
    prior_attempts = prior.execute(
        "SELECT family, pvalue FROM etf_regime_attempts"
    ).fetchdf()
    blocks = {str(k): (str(v["start"]), str(v["end"])) for k, v in config["referee"]["blocks"].items()}
    horizon = int(config["execution"]["primary_horizon"])
    directional_blocks = tuple(str(value) for value in config["referee"]["directional_blocks"])
    neutral_blocks = tuple(str(value) for value in config["referee"]["neutral_blocks"])
    diagnostic_blocks = tuple(str(value) for value in config["referee"]["diagnostic_blocks"])
    neutral_alpha = float(config["referee"]["neutral_harm_alpha"])
    referee_mode = str(config["referee"].get("mode", "six_cell_sign_v1"))
    # 2020 and 2021 remain available as diagnostics; neither can affect gates.
    signal_rows = []
    for h, frame in labels.items():
        frame.to_csv(output / f"labels_h{h}.csv", index=False)
    pd.DataFrame({"signal_date": panels["close"].index, **{name: series for name, series in state_raw.items()}}).to_parquet(output / "state_atoms.parquet", index=False)
    registry = []
    for e in expressions:
        registry.append({"expression_id": e.expression_id, "expression": e.readable, "operator": e.operator, "left": e.left, "right": e.right, "family": e.family})
    (output / "expression_registry.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2))

    attempt_rows = []
    for sequence, expr in enumerate(expressions, 1):
        signal = materialize_regime_expression(expr, states)
        block_means = {}
        horizon_block_means = {}
        diagnostics = {}
        for name, block in blocks.items():
            means = []
            for test_horizon in horizons:
                mean, pvalue, count, median, samples = _block_summary(
                    signal, labels, test_horizon, block
                )
                horizon_block_means[f"{name}_h{test_horizon}_mean"] = mean
                diagnostics[f"{name}_h{test_horizon}_pvalue"] = pvalue
                diagnostics[f"{name}_h{test_horizon}_block_count"] = count
                diagnostics[f"{name}_h{test_horizon}_samples"] = samples
                diagnostics[f"{name}_h{test_horizon}_median_effect"] = median
                means.append(mean)
            block_means[name] = (
                float(np.nanmean(means)) if np.isfinite(means).any() else np.nan
            )
        usable = labels[horizon].set_index("signal_date")["basket_spread"].reindex(signal.index)
        usable = (signal * usable).dropna()
        sampled_all = non_overlapping(usable, horizon)
        pvalue, block_count, median_effect = robust_block_pvalue(sampled_all)
        directional_inputs = {
            key.removesuffix("_mean"): value
            for key, value in horizon_block_means.items()
        }
        direction, directional_gate, directional_signed = directional_signature(
            directional_inputs,
            directional_blocks=directional_blocks,
            horizons=horizons,
            min_signed_effect=float(config["referee"]["min_signed_block_mean"]),
        )
        neutral_harm = False
        neutral_cells = {}
        for neutral_block in neutral_blocks:
            for test_horizon in horizons:
                (
                    neutral_mean,
                    neutral_pvalue,
                    neutral_count,
                    neutral_median,
                    neutral_samples,
                    neutral_failed,
                ) = _neutral_summary(
                    signal,
                    labels,
                    test_horizon,
                    blocks[neutral_block],
                    direction,
                    neutral_alpha,
                )
                key = f"{neutral_block}_h{test_horizon}"
                neutral_cells[key] = neutral_mean
                diagnostics[f"{key}_signed_mean"] = neutral_mean
                diagnostics[f"{key}_negative_pvalue"] = neutral_pvalue
                diagnostics[f"{key}_block_count"] = neutral_count
                diagnostics[f"{key}_samples"] = neutral_samples
                diagnostics[f"{key}_median_effect"] = neutral_median
                diagnostics[f"{key}_significant_negative"] = neutral_failed
                neutral_harm = neutral_harm or neutral_failed
        neutral_harm_pass = not neutral_harm
        min_edge = float(config["referee"]["min_signed_block_mean"])
        if referee_mode == "block_ttest_v2":
            direction, directional_gate, v2_cells = directional_block_gate(
                signal,
                labels[horizon].set_index("signal_date")["basket_spread"],
                horizon=horizon,
                directional_blocks={b: blocks[b] for b in directional_blocks},
                block_alpha=float(config["referee"]["directional_block_alpha"]),
            )
            diagnostics.update({f"v2_{k}": v for k, v in v2_cells.items()})
        hard_pass = bool(directional_gate and neutral_harm_pass)
        row = {
            "sequence": sequence,
            "expression_id": expr.expression_id,
            "expression": expr.readable,
            "family": expr.family,
            "operator": expr.operator,
            "direction": direction,
            "pvalue": pvalue,
            "block_count": block_count,
            "median_effect": median_effect,
            "directional_gate_pass": directional_gate,
            "neutral_harm_pass": neutral_harm_pass,
            "hard_block_pass": hard_pass,
            "final_pass": False,
            **{f"{k}_mean": v for k, v in block_means.items()},
            **horizon_block_means,
            **{f"directional_signed_{k}": v for k, v in directional_signed.items()},
            **diagnostics,
        }
        attempt_rows.append(row)
    summary = pd.DataFrame(attempt_rows).set_index("expression_id", drop=False)
    if referee_mode == "block_ttest_v2":
        summary["family_holm_pass"], family_summary = generation_family_holm(
            summary["pvalue"], summary["family"], float(config["referee"]["holm_alpha"])
        )
    else:
        summary["family_holm_pass"], family_summary = hierarchical_family_holm(
            summary["pvalue"],
            summary["family"],
            float(config["referee"]["holm_alpha"]),
            prior_attempts,
        )
    summary["final_pass"] = summary["hard_block_pass"] & summary["family_holm_pass"]
    summary.to_csv(output / "regime_factor_summary.csv", index=False)
    family_summary.to_csv(output / "family_multiple_testing.csv", index=False)

    # Preserve a deterministic ATTACK-family readout even when no expression
    # survives the full referee.  This is discovery evidence, not strategy
    # permission; final status remains controlled by the gates above.
    attack_mask = summary["family"].astype(str).str.contains("attack_", regex=False)
    attack_summary = summary.loc[attack_mask].copy()
    if attack_summary.empty:
        strongest_attack = None
        attack_performance_rows = []
    else:
        attack_summary["_final_rank"] = attack_summary["final_pass"].astype(int)
        attack_summary["_hard_rank"] = attack_summary["hard_block_pass"].astype(int)
        strongest_attack = attack_summary.sort_values(
            ["_final_rank", "_hard_rank", "pvalue", "sequence"],
            ascending=[False, False, True, True],
        ).iloc[0]
        attack_performance_rows = []
        for block_name in blocks:
            for test_horizon in horizons:
                raw_mean = strongest_attack.get(
                    f"{block_name}_h{test_horizon}_mean", np.nan
                )
                attack_performance_rows.append(
                    {
                        "expression_id": strongest_attack["expression_id"],
                        "expression": strongest_attack["expression"],
                        "family": strongest_attack["family"],
                        "direction": int(strongest_attack["direction"]),
                        "horizon": int(test_horizon),
                        "block": block_name,
                        "raw_mean": raw_mean,
                        "signed_mean": raw_mean * int(strongest_attack["direction"]),
                    }
                )
    pd.DataFrame(attack_performance_rows).to_csv(
        output / "attack_family_block_performance.csv", index=False
    )

    performance_rows = []
    for h, frame in labels.items():
        for block, (start, end) in blocks.items():
            subset = frame.loc[(frame.signal_date >= pd.Timestamp(start)) & (frame.signal_date <= pd.Timestamp(end))]
            for col in ("attack_return", "defensive_return", "basket_spread"):
                valid = subset[col].dropna()
                sampled = valid.iloc[:: int(h)]
                performance_rows.append({"horizon": h, "block": block, "metric": col, "mean": float(valid.mean()) if not valid.empty else np.nan, "median": float(valid.median()) if not valid.empty else np.nan, "non_overlap_compound": float((1.0 + sampled).prod() - 1.0) if not sampled.empty else np.nan, "observations": int(valid.size), "non_overlap_observations": int(sampled.size)})
    pd.DataFrame(performance_rows).to_csv(output / "block_performance.csv", index=False)
    diagnostic_rows = []
    diagnostic_block = (str(config["referee"]["diagnostic_2021_start"]), str(config["referee"]["diagnostic_2021_end"]))
    for h, frame in labels.items():
        subset = frame.loc[(frame.signal_date >= pd.Timestamp(diagnostic_block[0])) & (frame.signal_date <= pd.Timestamp(diagnostic_block[1]))]
        for col in ("attack_return", "defensive_return", "basket_spread"):
            valid = subset[col].dropna()
            sampled = valid.iloc[:: int(h)]
            diagnostic_rows.append({"horizon": h, "metric": col, "mean": float(valid.mean()) if not valid.empty else np.nan, "median": float(valid.median()) if not valid.empty else np.nan, "non_overlap_compound": float((1.0 + sampled).prod() - 1.0) if not sampled.empty else np.nan, "observations": int(valid.size), "non_overlap_observations": int(sampled.size)})
    pd.DataFrame(diagnostic_rows).to_csv(output / "diagnostic_2021_performance.csv", index=False)
    # Preserve the strongest hard-gate candidates even for a valid zero result;
    # an empty "best" file would hide the mechanism that was actually tested.
    best = summary.sort_values(["hard_block_pass", "pvalue"], ascending=[False, True]).head(20)
    best.insert(0, "selection_status", np.where(best["final_pass"], "final_pass", "diagnostic_only"))
    best.to_csv(output / "best_signals.csv", index=False)

    run_hash_payload = {"config": _sha(config_path), "universe": _sha(universe_path), "runner": _sha(Path(__file__).resolve()), "label": _sha(ROOT / "src/etf_strategy/core/etf_regime_label.py"), "state": _sha(ROOT / "src/etf_strategy/core/etf_market_state_space.py"), "referee": _sha(ROOT / "src/etf_strategy/core/etf_regime_referee.py"), "as_of": args.as_of}
    run_hash = hashlib.sha256(json.dumps(run_hash_payload, sort_keys=True).encode()).hexdigest()
    tested_at = datetime.now(timezone.utc).replace(tzinfo=None)
    records = [(generation, grammar, row.expression_id, row.expression, row.family, row.pvalue, int(row.direction), bool(row.final_pass), run_hash, tested_at) for row in summary.itertuples()]
    prior.executemany("INSERT INTO etf_regime_attempts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", records)
    ledger_count = prior.execute("SELECT count(*) FROM etf_regime_attempts").fetchone()[0]
    prior.close()
    try:
        import cupy as cp
        gpu = {"available": cp.cuda.runtime.getDeviceCount() > 0, "cupy_version": cp.__version__}
    except Exception as exc:
        gpu = {"available": False, "reason": type(exc).__name__}
    manifest = {
        "research_domain": "etf_rotation_regime",
        "generation": generation,
        "grammar_version": grammar,
        "generated_expressions": len(expressions),
        "attempt_manifest": "expression_registry.json + regime_factor_summary.csv + family_multiple_testing.csv",
        "basket": label_contract(basket, horizons, entry_lag),
        "window": [str(panels["close"].index.min().date()), str(panels["close"].index.max().date())],
        "referee_blocks": blocks,
        "referee_contract": {
            "directional_blocks": list(directional_blocks),
            "directional_cells": [f"{block}_h{h}" for block in directional_blocks for h in horizons],
            "directional_rule": "freeze sign from the six directional cells, then require every signed cell > min_signed_block_mean",
            "neutral_blocks": list(neutral_blocks),
            "neutral_harm_rule": "fail only when signed block effect mean < 0 and one-sided t-test on non-overlapping block means has p < neutral_harm_alpha",
            "neutral_harm_alpha": neutral_alpha,
            "diagnostic_blocks": list(diagnostic_blocks),
            "diagnostic_2021_excluded_from_gates": True,
        },
        "diagnostic_2021": {"start": str(config["referee"]["diagnostic_2021_start"]), "end": str(config["referee"]["diagnostic_2021_end"]), "excluded_from_gates": True},
        "state_contract": "D and earlier only; benchmark ETFs are state inputs and never label members or ranked population",
        "multiple_testing": "Simes family p-values; Holm across all current/prior families; Holm within passed families over all current/prior regime attempts",
        "ledger": str(args.ledger.resolve()),
        "ledger_rows_before_run": int(len(prior_attempts)),
        "ledger_rows_after_run": int(ledger_count),
        "gpu": gpu,
        "run_hash": run_hash,
        "source_hashes": run_hash_payload,
        "command": sys.argv,
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    attack_best_text = "none"
    if strongest_attack is not None:
        attack_best_text = (
            f"{strongest_attack['expression']} [{strongest_attack['family']}] "
            f"final={bool(strongest_attack['final_pass'])}, "
            f"direction={int(strongest_attack['direction'])}"
        )
    lines = [
        f"# ETF regime switch {generation}",
        "",
        f"表达式：{len(summary)}；directional gate：{int(summary.directional_gate_pass.sum())}；",
        f"neutral harm pass：{int(summary.neutral_harm_pass.sum())}；neutral harm fail：{int((~summary.neutral_harm_pass).sum())}；",
        f"家族门：{int(summary.family_holm_pass.sum())}；",
        f"最终晋级：{int(summary.final_pass.sum())}。",
        "",
        "标签从 close(D) 后的 open(D+2) 执行，未来 H 个开盘收益为进攻固定篮子减防守固定篮子。",
        "方向只由2022与2025–26的6个块×周期格冻结，并要求签名后全部为正；2023–24只在签名后效应显著为负（单侧t检验、alpha=0.05）时判定neutral harm。2020与2021仅作诊断。",
        "",
        f"最强ATTACK表达式：{attack_best_text}。四块篮子表现见 `block_performance.csv`；该表达式四块×5/10/20表现见 `attack_family_block_performance.csv`。",
        "最强硬门候选见 `best_signals.csv`（即使最终晋级为零也保留）；每次尝试见 `expression_registry.json`、`regime_factor_summary.csv`；完整时间、篮子和裁判合同见 `run_manifest.json`。",
        "",
        "旧横截面 rank IC 结果只保留为第二层历史诊断，不能进入本代状态切换晋级。",
    ]
    (output / "CAMPAIGN_REPORT.md").write_text("\n".join(lines) + "\n")
    print(f"ETF regime generation complete: expressions={len(summary)} family_holm={int(summary.family_holm_pass.sum())} hard_blocks={int(summary.hard_block_pass.sum())} final={int(summary.final_pass.sum())}")
    print(f"output={output}")


if __name__ == "__main__":
    main()
