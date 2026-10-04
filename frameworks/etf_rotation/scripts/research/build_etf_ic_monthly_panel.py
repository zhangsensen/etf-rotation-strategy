#!/usr/bin/env python3
"""Build the daily_ic / label_dates / turnover panels the monthly factory
(run_etf_ic_monthly_factory.py freeze/evaluate) reads.

For every candidate in the v3 contract's candidate_catalog, this locates the
historical run that first computed it (PLAN.json's config: source_type,
mechanism definition incl. direction, window), then rebuilds the group score
and daily group Rank IC with the CURRENT engine at the given --as-of, using
the same code path discover_etf_groups.py uses (etf_group_discovery /
etf_group_daily_rounds / etf_group_sources, plus etf_group_discovery.labels
and .evaluate). No new candidate definitions are proposed or registered; this
is a data-production step for the already-frozen v3 catalog.

Reproducibility gate (2026-09-23, layered per master's redefinition): restricted
to signal_date >= 2025-01-01 (the training/evaluation surface).

Layer 1 -- does the rebuild pipeline reproduce the source run's own saved
artifacts: rebuilt group score vs its scores_<candidate>.csv (rtol 1e-9),
rebuilt group label vs its group_labels.csv (atol 1e-12), rebuilt known/
complete mask vs its coverage.csv known_complete (exact, day by day).
If the source run's own PLAN.json input_hashes no longer match today's
data/ files, layer-1 mismatch DATES are reported as DATA_REVISED_SINCE_RUN
and do not fail the gate (the panel keeps the freshly rebuilt value, current
data wins); if hashes are unchanged, any mismatch is a hard failure.

Layer 2 -- IC: the reference is NOT the historical daily_metrics.csv (that
predates both the stable_rank tie-quantization commit and the 2026-09-23
absolute-vs-significant-digit rounding fix). The reference is the source
run's OWN saved scores_<candidate>.csv + group_labels.csv re-ranked with the
CURRENT (fixed) stable_rank. Rebuilt IC must match this reference within
1e-9. The stale daily_metrics.csv IC is still read and reported as an extra
column (diff vs the reference) so the rule-change's effect is visible, but
it is never a gate.

Any layer-1 non-revision mismatch or any layer-2 mismatch is a hard error;
no panel files are written on failure.

Read-only against data/. Writes only under
runtime_outputs/etf_rotation_research/monthly_factory/panels/<as_of>/.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as engine
from etf_strategy.core import etf_group_daily_rounds as daily_rounds_engine
from etf_strategy.core import etf_group_sources as source_engine
from etf_strategy.core.etf_ic_monthly_factory import load_contract, verify_contract_files
from etf_strategy.core.etf_rank_utils import stable_rank

RUNS_DIR = ROOT / "runtime_outputs/etf_rotation_research/runs"
DATA_ROOT = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
GROUPS_PATH = ETF / "configs/etf_candidate14_economic_groups_v1.yaml"
UNIVERSE_PATH = ROOT / "config/etf_rotation_universe_v1.json"
WARMUP = 60  # fixed across every historical run inspected for this catalog

# Candidate -> the run whose PLAN.json first defines it. Derived 2026-09-23
# from runtime_outputs/etf_rotation_research/rejudge_v5_1_halt_diagnostic_20260923/
# summary.csv's `source_run` column, restricted to the 20 v3 catalog ids.
CANDIDATE_SOURCE_RUN = {
    "efficiency_5": "group_daily_v1_batch_20260922",
    "range_expansion_5": "group_daily_v1_batch_20260922",
    "reverse_illiquidity_5": "group_ic_reverse_illiquidity_20260922",
    "reverse_minute_late_return_5": "group_ic_reverse_minute_late_20260922",
    "reverse_realized_vol_term_structure_5_20": "group_ic_reverse_realized_vol_term_structure_20260922",
    "direction_range_coupling_20": "group_ic20_batch7_20260922",
    "market_residual_abs_cluster_20": "group_ic20_batch9_daily_20260922",
    "wick_body_coupling_20": "group_ic20_batch11_20260922",
    "d2025_range_gap_abs_corr_20": "group_ic20_batch14_stage2_daily_a_20260923",
    "d2025_amount_innovation_abs_change_20": "group_ic20_batch14_stage2_daily_b_20260923",
    "d2025_body_wick_abs_corr_20": "group_ic20_batch14_stage2_daily_b_20260923",
    "d2025_minute_amount_abs_return_concentration_20": "group_ic20_batch15_stage2_minute_20260923",
    "d2025_amount_shock_wick_rejection_20": "group_ic20_batch17_stage2_daily_20260923",
    "d2025_clv_extreme_recovery_rate_20": "group_ic20_batch19_stage2_daily_a_rejudge_v2_20260923",
    "d2025_range_shock_body_absorption_20": "group_ic20_batch19_stage2_daily_b_20260923",
    "d2025_range_shock_gap_absorption_20": "group_ic20_batch20_stage2_daily_a_20260923",
    "d2025_range_shock_clv_absorption_20": "group_ic20_batch20_stage2_daily_a_20260923",
    "d2025_range_shock_body_recovery_20": "group_ic20_batch20_stage2_daily_b_20260923",
    "d2025_range_shock_wick_rejection_20": "group_ic20_batch21_stage2_daily_20260923",
    "d2025_clv_extreme_wick_rejection_20": "group_ic20_batch22_stage2_daily_20260923",
}


def _definition(candidate: str) -> tuple[str, str, int, int]:
    """Return (kind, mechanism_name, window, direction) from the source run's PLAN.json."""
    run = CANDIDATE_SOURCE_RUN.get(candidate)
    if run is None:
        raise ValueError(f"no known source run for catalog candidate {candidate!r}")
    plan = json.loads((RUNS_DIR / run / "PLAN.json").read_text())
    cfg = plan["config"]
    kind = cfg.get("source_type", "daily")
    for window in cfg.get("windows", []):
        for mechanism, definition in cfg.get("mechanisms", {}).items():
            if f"{mechanism}_{window}" == candidate:
                return kind, mechanism, window, definition["direction"]
    raise ValueError(f"candidate {candidate!r} not found in {run}'s PLAN.json mechanisms")


def _base_known(panels: dict[str, pd.DataFrame]) -> pd.Series:
    return (
        panels["close"].notna().rolling(WARMUP).sum().eq(WARMUP).all(axis=1)
        & panels["volume"].gt(0).all(axis=1)
    )


def _candidate_known_mask(base_known: pd.Series, atom: pd.DataFrame) -> pd.Series:
    return base_known & atom.notna().all(axis=1)


def _turnover(weights: pd.DataFrame) -> pd.Series:
    """One-way group-weight turnover: 0.5 * sum(|w_t - w_{t-1}|); first row NaN.

    Not previously defined anywhere in the campaign; defined here because the
    monthly factory's evaluate step accepts an optional --turnover panel of
    this same (signal_date, candidate) shape.
    """
    diff = weights.diff().abs().sum(axis=1) * 0.5
    diff.iloc[0] = np.nan
    return diff


def build(as_of: str, contract_path: str) -> dict[str, pd.DataFrame]:
    contract, _digest = load_contract(contract_path)
    verify_contract_files(contract, ROOT)
    catalog = [str(c) for c in contract["candidate_catalog"]]

    groups = yaml.safe_load(GROUPS_PATH.read_text())["groups"]
    universe = json.loads(UNIVERSE_PATH.read_text())
    symbols = [r["ts_code"] for r in universe["etfs"] if r["role"] == "candidate"]

    panels = load_canonical_daily(DATA_ROOT, UNIVERSE_PATH, as_of=as_of, roles=("candidate",))
    calendar_raw = pd.read_parquet(DATA_ROOT / "1d" / "510300.SH.parquet")
    calendar = pd.DatetimeIndex(pd.to_datetime(calendar_raw.trade_date)).sort_values()
    calendar = calendar[calendar <= pd.Timestamp(as_of)]
    if len(panels["close"].index.difference(calendar)):
        raise ValueError("candidate sessions absent from reference calendar")
    panels = {k: p.reindex(calendar) for k, p in panels.items()}

    returns, timing = engine.labels(panels, lag=2, horizon=5)
    base_known = _base_known(panels)

    by_kind: dict[str, list[str]] = {}
    for candidate in catalog:
        kind, *_rest = _definition(candidate)
        by_kind.setdefault(kind, []).append(candidate)

    atoms: dict[str, pd.DataFrame] = {}

    daily_candidates = by_kind.get("daily", [])
    if daily_candidates:
        mechanisms = {}
        windows = set()
        for candidate in daily_candidates:
            _kind, mechanism, window, direction = _definition(candidate)
            mechanisms[mechanism] = {"direction": direction}
            windows.add(window)
        cfg = {"windows": sorted(windows), "mechanisms": mechanisms}
        atoms.update(engine.build_atoms(panels, cfg))

    daily_rounds_candidates = by_kind.get("daily_rounds", [])
    if daily_rounds_candidates:
        mechanisms = {}
        for candidate in daily_rounds_candidates:
            _kind, mechanism, window, direction = _definition(candidate)
            if window != 20:
                raise ValueError("daily_rounds is frozen to window 20")
            mechanisms[mechanism] = {"direction": direction}
        cfg = {"windows": [20], "mechanisms": mechanisms}
        atoms.update(daily_rounds_engine.build_atoms(panels, cfg))

    minute_candidates = by_kind.get("minute", [])
    if minute_candidates:
        mechanisms = {}
        windows = set()
        for candidate in minute_candidates:
            _kind, mechanism, window, direction = _definition(candidate)
            mechanisms[mechanism] = {"direction": direction}
            windows.add(window)
        cfg = {"source_type": "minute", "windows": sorted(windows), "mechanisms": mechanisms}
        minute_panels, _audits, _checks = source_engine.load_source(DATA_ROOT, symbols, calendar, cfg)
        minute_panels["close"] = panels["close"].reindex(calendar)
        minute_atoms = source_engine.build_atoms(minute_panels, cfg)
        for candidate in minute_candidates:
            atoms[candidate] = minute_atoms[candidate]

    unsupported = set(by_kind) - {"daily", "daily_rounds", "minute"}
    if unsupported:
        raise ValueError(f"unsupported source_type in v3 catalog: {sorted(unsupported)}")

    daily_ic = pd.DataFrame(index=calendar, columns=catalog, dtype=float)
    turnover = pd.DataFrame(index=calendar, columns=catalog, dtype=float)
    scores: dict[str, pd.DataFrame] = {}
    known_masks: dict[str, pd.Series] = {}
    for candidate in catalog:
        atom = atoms[candidate]
        known = _candidate_known_mask(base_known, atom)
        score = engine.aggregate(atom, groups)
        frame, weights = engine.evaluate(score, returns, groups, known, timing, k=2)
        daily_ic[candidate] = frame["ic"]
        turnover[candidate] = _turnover(weights)
        scores[candidate] = score
        known_masks[candidate] = known

    group_returns = engine.aggregate(returns, groups)
    label_dates = timing[["entry_date", "exit_date"]].copy()
    label_dates.index.name = "signal_date"
    daily_ic.index.name = "signal_date"
    turnover.index.name = "signal_date"
    return {
        "daily_ic": daily_ic, "label_dates": label_dates, "turnover": turnover,
        "scores": scores, "known": known_masks, "group_returns": group_returns,
        "catalog": catalog, "base_known": base_known,
    }


GATE_START = "2025-01-01"


def _source_run_revised(run: str) -> tuple[bool, list[str]]:
    """Return (any_input_changed, changed_paths) vs the run's own PLAN.json."""
    plan = json.loads((RUNS_DIR / run / "PLAN.json").read_text())
    changed = []
    for path, old_hash in plan.get("input_hashes", {}).items():
        p = Path(path)
        if not p.exists() or sha256(p.read_bytes()).hexdigest() != old_hash:
            changed.append(path)
    return bool(changed), changed


def _read_source_artifacts(run: str, candidate: str) -> dict[str, pd.DataFrame]:
    base = RUNS_DIR / run
    score = pd.read_csv(base / f"scores_{candidate}.csv", index_col=0, parse_dates=True)
    group_labels = pd.read_csv(base / "group_labels.csv", index_col=0, parse_dates=True)
    coverage = pd.read_csv(base / "coverage.csv", parse_dates=["signal_date"]).set_index("signal_date")
    daily_metrics = pd.read_csv(base / "daily_metrics.csv", parse_dates=["signal_date"])
    daily_metrics = daily_metrics.loc[daily_metrics.candidate == candidate].set_index("signal_date")["ic"]
    return {"score": score, "group_labels": group_labels, "coverage": coverage, "stale_ic": daily_metrics}


def _reference_ic(score: pd.DataFrame, group_labels: pd.DataFrame, known: pd.Series) -> pd.Series:
    """IC the CURRENT engine derives from a source run's own frozen artifacts.

    Mirrors etf_group_discovery.evaluate()'s IC formula exactly, but starts
    from the already-aggregated saved group_labels.csv instead of member-
    level returns (all(group_labels notna, axis=1) is equivalent to all(
    member returns notna) since aggregate() nulls a group whenever any of
    its own members is null).
    """
    signal = score.where(known, axis=0)
    complete = known & signal.notna().all(axis=1) & group_labels.notna().all(axis=1)
    ic = stable_rank(signal).corrwith(group_labels.rank(axis=1, method="average"), axis=1)
    return ic.where(complete)


def layer1_check(built: dict, catalog: list[str]) -> pd.DataFrame:
    """Rebuilt score/label/known vs each source run's own saved artifacts,
    signal_date >= GATE_START only. Mismatches on dates where the source
    run's inputs have since changed on disk are reported as
    DATA_REVISED_SINCE_RUN and do not fail the gate.
    """
    rows = []
    for candidate in catalog:
        run = CANDIDATE_SOURCE_RUN[candidate]
        revised, changed_paths = _source_run_revised(run)
        artifacts = _read_source_artifacts(run, candidate)
        score, coverage = artifacts["score"], artifacts["coverage"]
        rebuilt_score = built["scores"][candidate]
        # coverage.csv's known_complete is the date-level base completeness
        # (base_known in discover_etf_groups.py), NOT the per-candidate mask
        # (base_known & atom.notna().all(axis=1)): a candidate's own atom can
        # be legitimately NaN on a date the base panel is otherwise complete
        # (e.g. an insufficient rolling window for one member), and that is
        # not a reproducibility mismatch.
        rebuilt_known = built["base_known"]

        common = score.index.intersection(rebuilt_score.index)
        common = common[common >= pd.Timestamp(GATE_START)]
        score_diff = (score.loc[common] - rebuilt_score.loc[common]).abs()
        score_rel_mismatch = (
            score_diff > (1e-9 * score.loc[common].abs().clip(lower=1e-12))
        ).any(axis=1)

        label_common = artifacts["group_labels"].index.intersection(built["group_returns"].index)
        label_common = label_common[label_common >= pd.Timestamp(GATE_START)]
        label_diff = (
            artifacts["group_labels"].loc[label_common] - built["group_returns"].loc[label_common]
        ).abs()
        label_mismatch = (label_diff > 1e-12).any(axis=1)

        known_common = coverage.index.intersection(rebuilt_known.index)
        known_common = known_common[known_common >= pd.Timestamp(GATE_START)]
        known_mismatch = coverage.loc[known_common, "known_complete"].astype(bool).ne(
            rebuilt_known.loc[known_common]
        )

        mismatch_dates = sorted({
            *score_diff.index[score_rel_mismatch].astype(str),
            *label_diff.index[label_mismatch].astype(str),
            *known_common[known_mismatch].astype(str),
        })
        rows.append({
            "candidate": candidate, "source_run": run,
            "input_data_revised_since_run": revised,
            "n_changed_input_files": len(changed_paths),
            "n_mismatch_dates": len(mismatch_dates),
            "status": (
                "OK" if not mismatch_dates
                else "DATA_REVISED_SINCE_RUN" if revised
                else "LAYER1_FAILED"
            ),
            "mismatch_dates_sample": mismatch_dates[:5],
        })
    return pd.DataFrame(rows)


def layer2_check(built: dict, catalog: list[str], revised: dict[str, bool]) -> pd.DataFrame:
    """Rebuilt daily IC vs the reference IC re-derived from each source run's
    own saved score/label artifacts using the CURRENT stable_rank. Also
    reports (not gates) the stale historical daily_metrics.csv IC for
    context.

    The check is one-directional: wherever the reference (built from the
    source run's OLD frozen artifacts, itself computed at that run's own
    as_of) has a valid IC, the rebuild must reproduce it within tolerance,
    including being non-NaN there. Wherever the reference is NaN, nothing is
    required of the rebuild -- this covers both dates beyond the source
    run's own as_of, and dates whose D+7 exit label had not yet matured
    when the source run computed its own as_of (a later, fresher --as-of
    naturally matures more labels than the source run ever saw). Neither
    case is a reproducibility problem.

    For a candidate layer 1 already flagged DATA_REVISED_SINCE_RUN, the
    reference (built from the source run's OLD frozen inputs) and the
    rebuilt series (built from TODAY's data) are expected to disagree on
    exactly the revised dates -- that disagreement is layer 1's finding, not
    a new layer-2 failure. Revised candidates are gated only on dates where
    both are valid; unrevised candidates additionally require the rebuild to
    be non-NaN wherever the reference is valid.
    """
    rows = []
    for candidate in catalog:
        run = CANDIDATE_SOURCE_RUN[candidate]
        artifacts = _read_source_artifacts(run, candidate)
        coverage = artifacts["coverage"]
        known = coverage["known_complete"].astype(bool)
        reference = _reference_ic(artifacts["score"], artifacts["group_labels"], known)
        rebuilt = built["daily_ic"][candidate]

        common = reference.index.intersection(rebuilt.index)
        common = common[common >= pd.Timestamp(GATE_START)]
        ref_common, rebuilt_common = reference.loc[common], rebuilt.loc[common]
        both_valid = ref_common.notna() & rebuilt_common.notna()
        # One-directional: only "reference valid but rebuild missing" counts.
        nan_pattern_mismatch = int((ref_common.notna() & rebuilt_common.isna()).sum())
        diff = (ref_common - rebuilt_common).abs()
        max_diff = float(diff[both_valid].max()) if both_valid.any() else 0.0

        stale = artifacts["stale_ic"].reindex(common)
        stale_diff = (stale - ref_common).abs()
        stale_valid = stale.notna() & ref_common.notna()
        max_stale_vs_reference_diff = (
            float(stale_diff[stale_valid].max()) if stale_valid.any() else None
        )

        is_revised = revised.get(candidate, False)
        numeric_ok = max_diff <= 1e-9
        candidate_pass = numeric_ok if is_revised else (nan_pattern_mismatch == 0 and numeric_ok)
        rows.append({
            "candidate": candidate, "source_run": run, "n_compared": int(both_valid.sum()),
            "input_data_revised_since_run": is_revised,
            "nan_pattern_mismatch": nan_pattern_mismatch, "max_abs_diff_vs_reference": max_diff,
            "max_abs_diff_stale_daily_metrics_vs_reference": max_stale_vs_reference_diff,
            "pass": candidate_pass,
        })
    return pd.DataFrame(rows)


def run_reproducibility_gate(built: dict, catalog: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    layer1 = layer1_check(built, catalog)
    revised = dict(zip(layer1.candidate, layer1.input_data_revised_since_run))
    layer2 = layer2_check(built, catalog, revised)
    layer1_failed = layer1.loc[layer1.status == "LAYER1_FAILED", "candidate"].tolist()
    layer2_failed = layer2.loc[~layer2["pass"], "candidate"].tolist()
    if layer1_failed or layer2_failed:
        raise ValueError(
            f"reproducibility gate failed. layer1 (non-revision) failures: {layer1_failed}; "
            f"layer2 failures: {layer2_failed}.\nLayer1:\n{layer1.to_string(index=False)}\n"
            f"Layer2:\n{layer2.to_string(index=False)}"
        )
    return layer1, layer2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--contract", default=str(ETF / "configs/etf_ic_monthly_factory_v4.yaml"))
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "runtime_outputs/etf_rotation_research/monthly_factory/panels"),
    )
    parser.add_argument(
        "--skip-reproducibility-check", action="store_true",
        help="only for ad-hoc inspection; the cycle wrapper never sets this",
    )
    args = parser.parse_args()

    contract, _digest = load_contract(args.contract)
    catalog = [str(c) for c in contract["candidate_catalog"]]
    built = build(args.as_of, args.contract)

    if not args.skip_reproducibility_check:
        layer1, layer2 = run_reproducibility_gate(built, catalog)
        print("Layer 1 (artifact reproduction):")
        print(layer1.to_string(index=False))
        print("Layer 2 (IC vs re-derived reference):")
        print(layer2.to_string(index=False))

    out = Path(args.output_root) / args.as_of
    out.mkdir(parents=True, exist_ok=True)
    built["daily_ic"].to_csv(out / "daily_ic.csv")
    built["label_dates"].to_csv(out / "label_dates.csv")
    built["turnover"].to_csv(out / "turnover.csv")
    print(json.dumps({"as_of": args.as_of, "output": str(out), "candidates": len(catalog)}))


if __name__ == "__main__":
    main()
