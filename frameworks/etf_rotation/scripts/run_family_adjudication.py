#!/usr/bin/env python3
"""Re-adjudicate existing ETF expressions by true information family and IC."""
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
from etf_strategy.core.family_registry import load_builtin_families, resolve_family
from etf_strategy.core.etf_family_catalog import load_family_catalog
from etf_strategy.core.etf_cumulative_ledger import ETFCumulativeLedger, alpha_spending
from etf_strategy.core.etf_data_provenance import hash_config_dependencies, hash_research_inputs
from etf_strategy.core.etf_identity import identity_gate, matched_leave_one_symbol_out, MATCHED_LOSO_COLUMNS
from etf_strategy.core.etf_marginal_ic import residualize_scores_diagnostic
from etf_strategy.core.etf_research_contract import (
    research_surfaces, consumption_contract, population_report, width_diagnostics,
)
from etf_strategy.core.etf_factor_grammar import (
    build_pit_eligibility,
    cross_sectional_rank,
    enumerate_expressions,
    materialize_expression,
    parse_atoms,
)
from etf_strategy.core.etf_family_referee import (
    common_sample_spearman,
    effective_test_count,
    maxstat_block_signflip,
    resolve_permutation_draws,
    timing_exposure_diagnostic,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-data-root", type=Path, required=True)
    parser.add_argument("--universe-config", type=Path, required=True)
    parser.add_argument("--adjudication-config", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    return parser.parse_args()


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _markdown_table(frame: pd.DataFrame) -> str:
    """Render a small report table without an optional tabulate dependency."""
    columns = list(frame.columns)
    rows = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for values in frame.itertuples(index=False, name=None):
        rendered = []
        for value in values:
            if isinstance(value, float):
                rendered.append("" if not np.isfinite(value) else f"{value:.6g}")
            else:
                rendered.append(str(value))
        rows.append("| " + " | ".join(rendered) + " |")
    return "\n".join(rows)


def _raw_forward(open_prices: pd.DataFrame, horizon: int, lag: int) -> pd.DataFrame:
    entry = open_prices.shift(-lag)
    exit_price = open_prices.shift(-(lag + horizon))
    return (exit_price / entry - 1.0).where((entry > 0.0) & (exit_price > 0.0))


def _source_paths(config: dict[str, object], config_path: Path) -> tuple[list[Path], Path]:
    catalog_value = config.get("family_catalog")
    if catalog_value is None or config.get("source_configs"):
        raise ValueError("ETF family adjudication requires family_catalog; source_configs is retired")
    catalog_path = Path(str(catalog_value))
    catalog_path = catalog_path if catalog_path.is_absolute() else (ROOT / catalog_path).resolve()
    return load_family_catalog(catalog_path, ROOT), catalog_path


def main() -> None:
    args = _args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory must be new and empty")
    output.mkdir(parents=True, exist_ok=True)
    config_path = args.adjudication_config.resolve()
    config = yaml.safe_load(config_path.read_text())
    taxonomy_value = Path(str(config["economic_axis_taxonomy"]))
    taxonomy_path = taxonomy_value if taxonomy_value.is_absolute() else (ROOT / taxonomy_value).resolve()
    taxonomy = yaml.safe_load(taxonomy_path.read_text())
    family_axis: dict[str, str] = {}
    for axis, axis_row in taxonomy["axes"].items():
        for family in axis_row["families"]:
            family = str(family)
            if family in family_axis:
                raise ValueError(f"family assigned to multiple economic axes: {family}")
            family_axis[family] = str(axis)
    load_builtin_families()
    ledger = ETFCumulativeLedger(args.ledger.resolve())
    generation = str(config["generation"])
    if ledger.has_generation(generation):
        ledger.close()
        raise ValueError(f"ETF family generation already recorded: {generation}")
    run_kind = config.get('run_kind', 'HYPOTHESIS')
    if run_kind not in {'HYPOTHESIS', 'CORRECTED_RERUN'}:
        raise ValueError('adjudication requires HYPOTHESIS or CORRECTED_RERUN; diagnostics use their own entry point')
    if run_kind == 'CORRECTED_RERUN' and not ledger.has_generation(str(config.get('replay_of', ''))):
        raise ValueError('CORRECTED_RERUN requires replay_of an existing generation')
    generation_number = (
        int(config.get("prior_generations_charged", 0))
        + ledger.prior_generation_count()
        + 1
    )
    generation_alpha = alpha_spending(float(config["gates"]["maxstat_alpha"]), generation_number)
    permutation_draws = resolve_permutation_draws(
        int(config["referee"]["permutation_draws"]),
        generation_alpha,
        multiplicity=len(taxonomy["axes"]),
        max_draws=int(config["referee"].get("max_permutation_draws", 1_000_000)),
    )
    universe_path = args.universe_config.resolve()
    universe = json.loads(universe_path.read_text())
    rows = universe["etfs"]
    rank_roles = set(config["ranking_roles"])
    rank_symbols = [row["ts_code"] for row in rows if row["role"] in rank_roles]
    excluded = [row["ts_code"] for row in rows if row["ts_code"] not in rank_symbols]
    expected_symbols = int(config["expected_ranking_symbols"])
    if len(rank_symbols) != expected_symbols:
        raise ValueError(
            f"ranking contract expected {expected_symbols} symbols, got {len(rank_symbols)}"
        )

    # Exposure is bounded at the adapter, before features or labels are built.
    effective_as_of = min(pd.Timestamp(args.as_of), pd.Timestamp(config['surfaces']['seen_audit_end']))
    all_panels = load_canonical_daily(
        args.canonical_data_root.resolve(), universe_path, as_of=str(effective_as_of.date()),
        allow_future_only_symbols=True,
    )
    all_eligibility = build_pit_eligibility(
        all_panels,
        int(config["min_history_sessions"]),
        bool(config["require_positive_volume"]),
    )
    eligibility = all_eligibility[rank_symbols]
    horizons = [int(value) for value in config["execution"]["horizons"]]
    primary = int(config["execution"]["primary_horizon"])
    if not horizons or len(set(horizons)) != len(horizons) or primary not in horizons:
        raise ValueError('horizons must be unique and include primary_horizon')
    lag = int(config["execution"]["entry_lag_sessions"])
    min_pairs = int(config["min_pairs"])
    calendars, discovery_masks, audit_masks = research_surfaces(
        eligibility.index, horizons, lag, config['surfaces']
    )
    forward = {
        horizon: _raw_forward(all_panels["open"][rank_symbols], horizon, lag).where(eligibility).where(
            discovery_masks[horizon] | audit_masks[horizon], axis=0
        )
        for horizon in horizons
    }
    basket_forward = forward[primary].mean(axis=1, skipna=True)
    discovery_end = pd.Timestamp(config["surfaces"]["discovery_end"])
    audit_start = pd.Timestamp(config["surfaces"]["seen_audit_start"])
    audit_end = pd.Timestamp(config["surfaces"]["seen_audit_end"])

    expression_rows: list[dict[str, object]] = []
    primary_raw: dict[str, pd.Series] = {}
    all_horizon_ic: dict[int, dict[str, pd.Series]] = {h: {} for h in horizons}
    width_rows: list[dict[str, object]] = []
    candidate_signals: dict[str, pd.DataFrame] = {}
    source_hashes: dict[str, str] = {}
    intraday_frequencies: set[str] = set()
    source_paths, catalog_path = _source_paths(config, config_path)
    baseline_scores = {}
    baseline_config_hashes = {}
    for control in config.get('baseline_controls', []):
        baseline_path = (ROOT / control['config']).resolve()
        baseline_config = yaml.safe_load(baseline_path.read_text())
        if baseline_config.get('frequency'):
            intraday_frequencies.add(str(baseline_config['frequency']))
        atom_name = str(control['atom'])
        if atom_name in baseline_scores:
            raise ValueError(f'duplicate baseline atom: {atom_name}')
        provider = resolve_family(str(baseline_config['factor_source']))
        space = provider.builder(all_panels, all_eligibility, args.canonical_data_root.resolve(), baseline_config)
        baseline_scores[atom_name] = space[atom_name].reindex_like(eligibility).where(eligibility)
        baseline_config_hashes[str(baseline_path)] = _hash(baseline_path)
    for source_path in source_paths:
        mining = yaml.safe_load(source_path.read_text())
        if mining.get("frequency"):
            intraday_frequencies.add(str(mining["frequency"]))
        source = str(mining["factor_source"])
        provider = resolve_family(source)
        true_family = provider.information_family
        source_hashes[source] = _hash(source_path)
        factor_space = provider.builder(
            all_panels, all_eligibility, args.canonical_data_root.resolve(), mining
        )
        atoms = parse_atoms(mining["atoms"])
        missing = sorted({atom.name for atom in atoms} - set(factor_space))
        if missing:
            raise ValueError(f"{source} missing atoms: {missing}")
        ranked_atoms = {
            atom.name: cross_sectional_rank(
                factor_space[atom.name].reindex(index=eligibility.index, columns=rank_symbols),
                eligibility,
            )
            for atom in atoms
        }
        expressions = enumerate_expressions(
            atoms, mining["grammar"]["operators"], mining["grammar"]["pair_policy"]
        )
        for expression in expressions:
            key = f"{source}:{expression.expression_id}"
            signal = materialize_expression(expression, ranked_atoms)
            horizon_ic: dict[int, pd.Series] = {}
            row: dict[str, object] = {
                "expression_key": key,
                "expression_id": expression.expression_id,
                "expression": expression.readable,
                "source": source,
                "true_family": true_family,
                "legacy_family": expression.family,
                "operator": expression.operator,
            }
            for horizon in horizons:
                daily_ic, pair_count = common_sample_spearman(
                    signal, forward[horizon], eligibility, min_pairs
                )
                horizon_ic[horizon] = daily_ic
                all_horizon_ic[horizon][key] = daily_ic
                discovery = daily_ic.where(discovery_masks[horizon]).dropna()
                row[f"h{horizon}_discovery_ic"] = float(discovery.mean()) if len(discovery) else np.nan
                row[f"h{horizon}_discovery_days"] = int(len(discovery))
                row[f"h{horizon}_unconditional_median_pairs"] = float(
                    pair_count.loc[:discovery_end].median()
                )
            timing_beta, timing_r2 = timing_exposure_diagnostic(
                horizon_ic[primary], basket_forward, discovery_end
            )
            discovery_primary = horizon_ic[primary].where(discovery_masks[primary]).dropna()
            audit_primary = horizon_ic[primary].where(audit_masks[primary]).dropna()
            common_direction_dates = pd.Series(True, index=eligibility.index)
            for h in horizons:
                common_direction_dates &= discovery_masks[h] & horizon_ic[h].notna()
            direction_means = {h: float(horizon_ic[h].where(common_direction_dates).mean()) for h in horizons}
            row['direction_common_days'] = int(common_direction_dates.sum())
            for h in horizons:
                row[f'h{h}_common_discovery_ic'] = direction_means[h]
            _, primary_pairs = common_sample_spearman(signal, forward[primary], eligibility, min_pairs)
            for diagnostic in width_diagnostics(
                horizon_ic[primary], primary_pairs, eligibility.sum(axis=1),
                {'discovery': discovery_masks[primary], 'seen_audit': audit_masks[primary]},
                min_pairs=min_pairs, ranking_size=len(rank_symbols),
            ):
                width_rows.append({'expression_key': key, **diagnostic})
            row.update(
                {
                    "timing_beta": timing_beta,
                    "timing_r2": timing_r2,
                    "discovery_ic": float(discovery_primary.mean()) if len(discovery_primary) else np.nan,
                    "discovery_days": int(len(discovery_primary)),
                    "seen_audit_ic": float(audit_primary.mean()) if len(audit_primary) else np.nan,
                    "seen_audit_days": int(len(audit_primary)),
                    "all_horizons_same_direction": bool(
                        all(
                            np.isfinite(direction_means[h])
                            and np.sign(direction_means[h]) == np.sign(direction_means[primary])
                            and np.sign(direction_means[primary]) == np.sign(row[f"h{primary}_discovery_ic"])
                            for h in horizons
                        )
                    ),
                }
            )
            primary_direction = np.sign(row[f"h{primary}_discovery_ic"])
            if (
                row["discovery_days"] >= int(config["gates"]["min_discovery_days"])
                and abs(float(row["discovery_ic"])) >= float(config["gates"]["min_abs_ic"])
                and float(row["seen_audit_ic"]) * primary_direction
                >= float(config["gates"]["min_abs_seen_audit_ic"])
                and bool(row["all_horizons_same_direction"])
            ):
                candidate_signals[key] = signal
            expression_rows.append(row)
            primary_raw[key] = horizon_ic[primary]

    summary = pd.DataFrame(expression_rows).set_index("expression_key", drop=False)
    missing_axis = sorted(set(summary["true_family"].astype(str)) - set(family_axis))
    if missing_axis:
        raise ValueError(f"families missing from economic-axis taxonomy: {missing_axis}")
    summary["economic_axis"] = summary["true_family"].map(family_axis)
    descriptive_keys = set(candidate_signals)
    summary["descriptive_gate_pass"] = summary.index.isin(descriptive_keys)
    discovery_matrix = pd.DataFrame(primary_raw).loc[:discovery_end]
    block_t, pooled_maxstat_p = maxstat_block_signflip(
        discovery_matrix,
        block_sessions=int(config["referee"]["block_sessions"]),
        draws=permutation_draws,
        seed=int(config["referee"]["seed"]),
    )
    summary["block_t"] = block_t.reindex(summary.index)
    summary["pooled_maxstat_pvalue"] = pooled_maxstat_p.reindex(summary.index)
    summary["within_family_maxstat_pvalue"] = np.nan
    family_omnibus: dict[str, float] = {}
    for family, group in summary.groupby("true_family", sort=True):
        _, local_p = maxstat_block_signflip(
            discovery_matrix[group.index],
            block_sessions=int(config["referee"]["block_sessions"]),
            draws=permutation_draws,
            seed=int(config["referee"]["seed"])
            + int(hashlib.sha256(family.encode()).hexdigest()[:8], 16),
        )
        summary.loc[group.index, "within_family_maxstat_pvalue"] = local_p.reindex(group.index)
        finite_local = local_p.dropna()
        family_omnibus[family] = (
            float(finite_local.min()) if not finite_local.empty else np.nan
        )
    ordered_families = sorted(
        (family for family, value in family_omnibus.items() if np.isfinite(value)),
        key=family_omnibus.get,
    )
    family_holm = {family: False for family in family_omnibus}
    for rank, family in enumerate(ordered_families):
        threshold = generation_alpha / (len(ordered_families) - rank)
        if family_omnibus[family] > threshold:
            break
        family_holm[family] = True
    summary["family_holm_pass"] = summary["true_family"].map(family_holm).fillna(False)
    summary["within_axis_maxstat_pvalue"] = np.nan
    axis_omnibus: dict[str, float] = {}
    for axis, group in summary.groupby("economic_axis", sort=True):
        _, local_p = maxstat_block_signflip(
            discovery_matrix[group.index],
            block_sessions=int(config["referee"]["block_sessions"]),
            draws=permutation_draws,
            seed=int(config["referee"]["seed"])
            + int(hashlib.sha256(f"axis:{axis}".encode()).hexdigest()[:8], 16),
        )
        summary.loc[group.index, "within_axis_maxstat_pvalue"] = local_p.reindex(group.index)
        finite_local = local_p.dropna()
        axis_omnibus[axis] = float(finite_local.min()) if not finite_local.empty else np.nan
    ordered_axes = sorted(
        (axis for axis, value in axis_omnibus.items() if np.isfinite(value)),
        key=axis_omnibus.get,
    )
    axis_holm = {axis: False for axis in axis_omnibus}
    for rank, axis in enumerate(ordered_axes):
        threshold = generation_alpha / (len(ordered_axes) - rank)
        if axis_omnibus[axis] > threshold:
            break
        axis_holm[axis] = True
    summary["axis_holm_pass"] = summary["economic_axis"].map(axis_holm).fillna(False)
    gates = config["gates"]
    direction = np.sign(summary["discovery_ic"]).replace(0.0, np.nan)
    summary["statistical_gate_pass"] = (
        summary["discovery_days"].ge(int(gates["min_discovery_days"]))
        & summary["discovery_ic"].abs().ge(float(gates["min_abs_ic"]))
        & summary["seen_audit_ic"].mul(direction).ge(float(gates["min_abs_seen_audit_ic"]))
        & summary["all_horizons_same_direction"]
        & summary["pooled_maxstat_pvalue"].lt(generation_alpha)
        & summary["within_axis_maxstat_pvalue"].lt(generation_alpha)
        & summary["axis_holm_pass"]
    )
    summary["identity_gate_pass"] = False
    summary["marginal_gate_pass"] = pd.Series(pd.NA, index=summary.index, dtype="boolean")
    summary["marginal_status"] = "NOT_EVALUATED"
    identity_rows: list[pd.DataFrame] = []
    paired_identity_rows: list[pd.DataFrame] = []
    marginal_rows: list[dict[str, object]] = []
    baseline_rows: list[dict[str, object]] = []
    residual_diagnostics: list[pd.DataFrame] = []
    admitted_scores: dict[str, pd.DataFrame] = {}
    for admitted_path in ledger.admitted_factor_artifacts():
        admitted_long = pd.read_parquet(admitted_path)
        for expression_key, group in admitted_long.groupby("expression_key"):
            admitted_scores[str(expression_key)] = group.pivot(
                index="signal_date", columns="symbol", values="score"
            ).reindex(index=eligibility.index, columns=rank_symbols)
    for key in summary.index[summary["descriptive_gate_pass"]]:
        signal = candidate_signals[key]
        direction_value = float(np.sign(summary.loc[key, "discovery_ic"]))
        loso, paired_loso = matched_leave_one_symbol_out(
            signal, forward[primary], eligibility, min_pairs=min_pairs,
            discovery_mask=discovery_masks[primary], audit_mask=audit_masks[primary],
        )
        for table, destination in [(loso, identity_rows), (paired_loso, paired_identity_rows)]:
            table.insert(0, "expression_key", key)
            destination.append(table)
        summary.loc[key, "identity_gate_pass"] = identity_gate(
            loso, direction_value, float(gates["min_abs_seen_audit_ic"]),
        )
        for kind, references in [('admitted_shelf', admitted_scores), ('economic_baseline', baseline_scores)]:
            residual_signal, diagnostic, status = residualize_scores_diagnostic(
                signal, references,
                candidate_name=str(summary.loc[key, 'expression']) if kind == 'economic_baseline' else key,
                min_pairs=min_pairs,
            )
            diagnostic = diagnostic.copy()
            diagnostic['expression_key'] = key
            diagnostic['reference_kind'] = kind
            residual_diagnostics.append(diagnostic)
            if status == 'EVALUATED':
                # Raw and residual reports use the same signal/label pairs.
                residual_signal = residual_signal.where(eligibility)
                marginal_daily, _ = common_sample_spearman(residual_signal, forward[primary], eligibility, min_pairs)
                raw_common_daily, _ = common_sample_spearman(signal.where(residual_signal.notna()), forward[primary], eligibility, min_pairs)
            else:
                marginal_daily = pd.Series(np.nan, index=eligibility.index)
                raw_common_daily = marginal_daily.copy()
            marginal_discovery = marginal_daily.where(discovery_masks[primary]).dropna()
            marginal_audit = marginal_daily.where(audit_masks[primary]).dropna()
            marginal_mean = float(marginal_discovery.mean())
            marginal_audit_mean = float(marginal_audit.mean())
            marginal_pass = bool(
                status == 'EVALUATED'
                and len(marginal_discovery) >= int(gates['min_discovery_days'])
                and np.isfinite(marginal_mean)
                and abs(marginal_mean) >= float(gates["min_abs_ic"])
                and np.sign(marginal_mean) == direction_value
                and np.isfinite(marginal_audit_mean)
                and marginal_audit_mean * direction_value >= float(gates["min_abs_seen_audit_ic"])
            )
            row = {
                'expression_key': key, 'reference_status': status,
                'references': ','.join(sorted(references)),
                'marginal_discovery_ic': marginal_mean,
                'marginal_seen_audit_ic': marginal_audit_mean,
                'discovery_days': len(marginal_discovery), 'seen_audit_days': len(marginal_audit),
                'raw_common_discovery_ic': float(raw_common_daily.where(discovery_masks[primary]).mean()),
                'raw_common_seen_audit_ic': float(raw_common_daily.where(audit_masks[primary]).mean()),
            }
            if kind == 'admitted_shelf':
                summary.loc[key, 'marginal_status'] = status
                if status != 'NOT_APPLICABLE':
                    summary.loc[key, 'marginal_gate_pass'] = marginal_pass
                marginal_rows.append({**row, 'admitted_factors': row['references'],
                                      'marginal_gate_pass': None if status == 'NOT_APPLICABLE' else marginal_pass})
            else:
                baseline_rows.append({**row, 'report_only': True, 'is_baseline_member': status == 'BASELINE_MEMBER'})
    # N/A does not block the first factor, and is never presented as a passed test.
    incremental_requirement = summary['marginal_status'].eq('NOT_APPLICABLE') | summary['marginal_gate_pass'].fillna(False)
    summary["family_gate_pass"] = (
        summary["statistical_gate_pass"] & summary["identity_gate_pass"] & incremental_requirement
    )

    family_rows = []
    for family, group in summary.groupby("true_family", sort=True):
        ranked = group.sort_values(
            ["family_gate_pass", "within_family_maxstat_pvalue", "discovery_ic"],
            ascending=[False, True, False],
        )
        best = ranked.iloc[0]
        family_matrix = discovery_matrix[group.index]
        family_rows.append(
            {
                "family": family,
                "expressions": int(len(group)),
                "effective_tests": effective_test_count(family_matrix),
                "best_expression_key": best["expression_key"],
                "best_expression": best["expression"],
                "best_source": best["source"],
                "raw_ic": best[f"h{primary}_discovery_ic"],
                "discovery_ic": best["discovery_ic"],
                "timing_r2": best["timing_r2"],
                "within_family_maxstat_pvalue": best["within_family_maxstat_pvalue"],
                "family_omnibus_pvalue": family_omnibus[family],
                "family_holm_pass": family_holm[family],
                "seen_audit_ic": best["seen_audit_ic"],
                "passing_expressions": int(group["family_gate_pass"].sum()),
                "verdict": "PASS" if bool(group["family_gate_pass"].any()) else "DEAD_ON_THIS_DATA",
            }
        )
    family_summary = pd.DataFrame(family_rows)
    axis_rows = []
    for axis, group in summary.groupby("economic_axis", sort=True):
        best = group.sort_values(
            ["family_gate_pass", "within_axis_maxstat_pvalue", "discovery_ic"],
            ascending=[False, True, False],
        ).iloc[0]
        axis_rows.append({
            "economic_axis": axis,
            "families": int(group["true_family"].nunique()),
            "expressions": int(len(group)),
            "effective_tests": effective_test_count(discovery_matrix[group.index]),
            "best_expression_key": best["expression_key"],
            "best_expression": best["expression"],
            "within_axis_maxstat_pvalue": best["within_axis_maxstat_pvalue"],
            "axis_omnibus_pvalue": axis_omnibus[axis],
            "axis_holm_pass": axis_holm[axis],
            "passing_expressions": int(group["family_gate_pass"].sum()),
        })
    axis_summary = pd.DataFrame(axis_rows)

    counts = eligibility.sum(axis=1).rename("eligible_count")
    population = {
        **population_report(eligibility, universe, discovery_masks[primary], audit_masks[primary]),
        "ranking_roles": sorted(rank_roles),
        "ranking_symbols": rank_symbols,
        "excluded_symbols": excluded,
        "discovery_total_dates": int(discovery_masks[primary].sum()),
        "discovery_unconditional_median": float(counts.where(discovery_masks[primary]).median()),
        "date_count_policy": "primary_horizon_mature_surface",
        "discovery_dates_at_min_pairs": int((counts.ge(min_pairs) & discovery_masks[primary]).sum()),
        "first_date_at_min_pairs": str(counts[counts >= min_pairs].index.min().date()),
        "min_pairs": min_pairs,
    }
    counts.to_csv(output / "population_eligible_count.csv", header=True)
    counts.rename_axis('signal_date').to_csv(output / 'wfo_eligibility_counts.csv', header=True)
    summary.to_csv(output / "expression_decomposition.csv", index=False)
    family_summary.to_csv(output / "family_verdict.csv", index=False)
    axis_summary.to_csv(output / "economic_axis_verdict.csv", index=False)
    pd.DataFrame(primary_raw).to_parquet(output / "daily_raw_ic.parquet")
    wfo_rows, date_rows = [], []
    for h in horizons:
        frame = pd.DataFrame(all_horizon_ic[h])
        frame.index.name = 'signal_date'
        frame.columns.name = 'expression_key'
        long = frame.stack(future_stack=True).rename('ic').reset_index()
        long.insert(0, 'horizon', h)
        wfo_rows.append(long)
        dates = calendars[h].rename_axis('signal_date').reset_index()
        dates.insert(0, 'horizon', h)
        date_rows.append(dates)
    pd.concat(wfo_rows, ignore_index=True).to_parquet(output / 'wfo_daily_ic.parquet', index=False)
    pd.concat(date_rows, ignore_index=True).to_parquet(output / 'label_dates.parquet', index=False)
    pd.DataFrame(width_rows).to_csv(output / 'population_width_ic.csv', index=False)
    discovery_matrix.to_parquet(output / "daily_ic_discovery.parquet")
    effective = {
        "pooled": effective_test_count(discovery_matrix),
        **{
            family: effective_test_count(discovery_matrix[group.index])
            for family, group in summary.groupby("true_family")
        },
        "economic_axes": {
            axis: effective_test_count(discovery_matrix[group.index])
            for axis, group in summary.groupby("economic_axis")
        },
    }
    (output / "effective_tests.json").write_text(json.dumps(effective, indent=2))
    (output / "population_contract.json").write_text(json.dumps(population, ensure_ascii=False, indent=2))
    identity_output = (
        pd.concat(identity_rows, ignore_index=True)
        if identity_rows
        else pd.DataFrame(columns=['expression_key', *MATCHED_LOSO_COLUMNS])
    )
    identity_output.to_csv(output / "identity_shared_dates.csv", index=False)
    paired_output = pd.concat(paired_identity_rows, ignore_index=True) if paired_identity_rows else identity_output.iloc[:0]
    paired_output.to_csv(output / 'identity_paired_dates.csv', index=False)
    pd.DataFrame(marginal_rows, columns=[
        'expression_key', 'reference_status', 'admitted_factors', 'marginal_discovery_ic',
        'marginal_seen_audit_ic', 'discovery_days', 'seen_audit_days', 'marginal_gate_pass',
        'raw_common_discovery_ic', 'raw_common_seen_audit_ic',
    ]).to_csv(output / 'marginal_ic.csv', index=False)
    pd.DataFrame(baseline_rows, columns=[
        'expression_key', 'reference_status', 'references', 'marginal_discovery_ic',
        'marginal_seen_audit_ic', 'discovery_days', 'seen_audit_days', 'raw_common_discovery_ic',
        'raw_common_seen_audit_ic', 'report_only', 'is_baseline_member',
    ]).to_csv(output / 'economic_baseline_ic.csv', index=False)
    residual_output = pd.concat(residual_diagnostics, ignore_index=True) if residual_diagnostics else pd.DataFrame(
        columns=['date', 'n_pairs', 'design_rank', 'condition_number', 'status', 'expression_key', 'reference_kind'])
    residual_output.to_csv(output / 'residual_design_diagnostics.csv', index=False)
    admitted_output_rows = []
    for key in summary.index[summary["family_gate_pass"]]:
        stacked = candidate_signals[key].stack(future_stack=True).dropna().rename("score").reset_index()
        stacked.columns = ["signal_date", "symbol", "score"]
        stacked.insert(0, "expression_key", key)
        admitted_output_rows.append(stacked)
    admitted_output = (
        pd.concat(admitted_output_rows, ignore_index=True)
        if admitted_output_rows
        else pd.DataFrame(columns=["expression_key", "signal_date", "symbol", "score"])
    )
    admitted_output.to_parquet(output / "admitted_factor_scores.parquet", index=False)

    passing_families = int(family_summary["verdict"].eq("PASS").sum())
    lines = [
        "# ETF family adjudication",
        "",
        f"表达式：{len(summary)}；目录家族：{len(family_summary)}；冻结经济轴：{len(axis_summary)}；通过家族：{passing_families}。",
        f"排名人口：candidate {len(rank_symbols)}只；发现段无条件中位数{population['discovery_unconditional_median']:.0f}只；",
        f"达到min_pairs={min_pairs}的日期{population['discovery_dates_at_min_pairs']}天。",
        f"本代顺序alpha预算：{generation_alpha:.8f}（累计代次{generation_number}）。",
        "",
        "本轮没有搜索权重、运行策略回测或恢复状态分支。",
        "2024-01-01至2025-04-30仅为已见审计面；任何PASS仍不是独立样本外认证。",
        "",
        _markdown_table(family_summary),
    ]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n")
    artifact_hashes = {
        path.name: _hash(path)
        for path in sorted(output.iterdir())
        if path.is_file() and path.name != "run_manifest.json"
    }
    manifest = {
        "domain": config["domain"],
        "generation": config["generation"],
        "as_of": args.as_of,
        "effective_data_as_of": str(effective_as_of.date()),
        "protocol_version": "etf_engine_contract_v4",
        "run_kind": config.get('run_kind', 'HYPOTHESIS'),
        "replay_of": config.get('replay_of'),
        "label_consumption": consumption_contract(calendars, discovery_masks, audit_masks),
        "exposure_policy": "features_and_labels_capped_at_min_requested_as_of_and_audit_end",
        "direction_policy": "intersection_of_mature_finite_dates_across_all_horizons",
        "identity_policy": "shared_date_gate_plus_paired_date_attribution",
        "empty_shelf_policy": "NOT_APPLICABLE_nonblocking_not_pass_evidence",
        "baseline_controls": config.get('baseline_controls', []),
        "baseline_config_hashes": baseline_config_hashes,
        "baseline_policy": "report_only_post_selection_controls_not_certification",
        "population": population,
        "execution": config["execution"],
        "surfaces": config["surfaces"],
        "gates": config["gates"],
        "referee": config["referee"],
        "expressions": int(len(summary)),
        "families": int(len(family_summary)),
        "economic_axes": int(len(axis_summary)),
        "passing_families": passing_families,
        "cumulative_ledger": str(args.ledger.resolve()),
        "generation_number": generation_number,
        "generation_alpha": generation_alpha,
        "permutation_draws_configured": int(config["referee"]["permutation_draws"]),
        "permutation_draws_resolved": permutation_draws,
        "permutation_resolution_floor": 1.0 / (permutation_draws + 1.0),
        "source_hashes": source_hashes,
        "source_dependency_hashes": hash_config_dependencies(ROOT, source_paths),
        "engine_source_hashes": {
            str(path.relative_to(ROOT)): _hash(path)
            for path in sorted((ROOT / "src/etf_strategy/core").rglob("*.py"))
        },
        "family_catalog_hash": _hash(catalog_path),
        "economic_axis_taxonomy_hash": _hash(taxonomy_path),
        "config_hash": _hash(config_path),
        "universe_hash": _hash(universe_path),
        "runner_hash": _hash(Path(__file__)),
        "canonical_data_hash": _hash(ROOT / "src/etf_strategy/canonical_data.py"),
        "data_inputs": hash_research_inputs(
            args.canonical_data_root.resolve(),
            all_panels["close"].columns,
            intraday_frequencies,
        ),
        "shelf_script_hash": _hash(ROOT / "scripts/build_ic_factor_shelf.py"),
        "artifact_hashes": artifact_hashes,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_status": "seen-history family adjudication; not independent OOS",
        "command": sys.argv,
    }
    manifest_path = output / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    ledger.record(
        generation,
        hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        str(output),
        generation_alpha,
        summary,
        run_kind=config.get('run_kind', 'HYPOTHESIS'),
        replay_of=config.get('replay_of'),
        provenance={key: manifest[key] for key in ['config_hash', 'runner_hash', 'engine_source_hashes', 'data_inputs', 'protocol_version']},
    )
    ledger.close()
    print(f"ETF family adjudication complete: expressions={len(summary)} families={len(family_summary)} pass={manifest['passing_families']}")
    print(f"output={output}")


if __name__ == "__main__":
    main()
