"""Read-only repeated-batch diagnostics; never builds or evaluates factors."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "frameworks/etf_rotation/src"))
from etf_strategy.core.etf_mining_referee import newey_west_t_calendar
from etf_strategy.core.etf_rank_utils import stable_rank

GROUPS = ["cn_technology_manufacturing", "hk_technology", "us_large_growth", "innovative_pharma", "gold", "metals_equity", "dividend_low_vol", "electric_power"]
IC_BASELINES = ("efficiency_5", "range_expansion_5", "intraday_return_5")


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, float_precision="round_trip", **kwargs)


def read_metrics(path: Path) -> pd.DataFrame:
    return read_csv(path, parse_dates=["signal_date"]).set_index("signal_date")


def read_scores(path: Path) -> pd.DataFrame:
    return read_csv(path, index_col=0, parse_dates=True)[GROUPS]


def read_labels(path: Path) -> pd.DataFrame:
    return read_csv(path, parse_dates=["signal_date"]).set_index("signal_date")[GROUPS]


def assert_labels_equal(current: pd.DataFrame, reference: pd.DataFrame, dates: pd.DatetimeIndex) -> None:
    """Require the same frozen group labels before any score comparison."""
    left = current.reindex(dates)
    right = reference.reindex(dates)
    assert left.columns.tolist() == GROUPS and right.columns.tolist() == GROUPS
    np.testing.assert_allclose(left.to_numpy(float), right.to_numpy(float), rtol=0.0, atol=1e-12, equal_nan=True)


def valid_calendar(run: Path) -> pd.DatetimeIndex:
    c = read_csv(run / "coverage.csv", parse_dates=["signal_date", "exit_date"])
    out = c.loc[c.in_evaluation_window & c.exit_date.notna() & (c.exit_date <= pd.Timestamp("2026-09-17")), "signal_date"]
    return pd.DatetimeIndex(out).sort_values().unique()


def rank_corr(candidate_score: pd.DataFrame, baseline_score: pd.DataFrame,
              candidate_metric: pd.DataFrame, baseline_metric: pd.DataFrame,
              calendar: pd.DatetimeIndex) -> pd.Series:
    common = candidate_score.index.intersection(baseline_score.index).intersection(calendar)
    valid = candidate_metric["ic"].reindex(common).notna() & baseline_metric["ic"].reindex(common).notna()
    dates = common[valid.to_numpy()]
    return stable_rank(candidate_score.loc[dates]).corrwith(
        stable_rank(baseline_score.loc[dates]), axis=1
    ).dropna()


def paired_ic(candidate_metric: pd.DataFrame, baseline_metric: pd.DataFrame,
              calendar: pd.DatetimeIndex) -> tuple[int, float, float]:
    common = pd.DatetimeIndex(candidate_metric.index.intersection(baseline_metric.index).intersection(calendar))
    valid = candidate_metric["ic"].reindex(common).notna() & baseline_metric["ic"].reindex(common).notna()
    dates = common[valid.to_numpy()]
    delta = candidate_metric["ic"].reindex(dates) - baseline_metric["ic"].reindex(dates)
    aligned = delta.reindex(calendar)
    return int(delta.notna().sum()), float(delta.mean()), float(newey_west_t_calendar(aligned, calendar, 10))


def self_test() -> None:
    """Synthetic no-market test: invalid dates remain calendar gaps, not dropped observations."""
    idx = pd.date_range("2025-01-01", periods=4, freq="D")
    a = pd.DataFrame(np.tile(np.arange(8.0), (4, 1)), index=idx, columns=GROUPS)
    b = a.copy(); b.iloc[1, 0] = np.nan
    m = pd.DataFrame({"ic": [0.1, np.nan, 0.2, 0.3]}, index=idx)
    n = pd.DataFrame({"ic": [0.2, 0.1, 0.2, 0.4]}, index=idx)
    corr = rank_corr(a, b, m, n, idx)
    assert len(corr) == 3 and idx[1] not in corr.index
    global newey_west_t_calendar
    original_hac = newey_west_t_calendar
    captured = {}
    def capture_hac(series, calendar, lag):
        captured["index"] = series.index
        captured["values"] = series.copy()
        captured["lag"] = lag
        return 0.0
    newey_west_t_calendar = capture_hac
    try:
        delta_n, _, _ = paired_ic(m, n, idx)
    finally:
        newey_west_t_calendar = original_hac
    assert delta_n == 3
    assert captured["index"].equals(idx) and pd.isna(captured["values"].iloc[1]) and captured["lag"] == 10
    print("self-test: PASS")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id")
    ap.add_argument("--output")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        with tempfile.TemporaryDirectory(prefix="etf_ic_rounds_test_"):
            self_test()
        if not args.run_id:
            return
    if not args.run_id:
        ap.error("--run-id is required unless --self-test is used alone")
    run_id_path = Path(args.run_id)
    if run_id_path.is_absolute() or run_id_path.name != args.run_id or ".." in run_id_path.parts:
        ap.error("--run-id must be a plain run directory name")
    run = ROOT / "runtime_outputs/etf_rotation_research/runs" / args.run_id
    out = ROOT / args.output if args.output else run / "diagnostics_rounds"
    out.mkdir(parents=True, exist_ok=False)
    calendar = valid_calendar(run)
    current_metrics = read_metrics(run / "daily_metrics.csv")
    current_labels = read_labels(run / "group_labels.csv")
    current_candidates = list(current_metrics.candidate.drop_duplicates())

    runs = ROOT / "runtime_outputs/etf_rotation_research/runs"
    mapping = read_csv(ROOT / "runtime_outputs/etf_rotation_research/rejudgments/frozen80_2025_rejudge_20260922_v3/comparison.csv")[["candidate", "run"]].drop_duplicates()
    baselines: dict[str, tuple[pd.DataFrame, pd.DataFrame, str]] = {}
    for row in mapping.itertuples():
        r = runs / row.run
        baselines[row.candidate] = (read_metrics(r / "daily_metrics.csv").query("candidate == @row.candidate"), read_scores(r / f"scores_{row.candidate}.csv"), row.run)
    breadth = ROOT / "runtime_outputs/etf_rotation_research/group_next8_20260922_v4"
    breadth_metrics = read_metrics(breadth / "daily_metrics.csv")
    for name in ("breadth_5", "breadth_20"):
        baselines[name] = (breadth_metrics.query("candidate == @name"), read_scores(breadth / f"scores_{name}.csv"), "group_next8_20260922_v4")
    batch2 = runs / "group_ic_batch2_20260922"
    batch2_metrics = read_metrics(batch2 / "daily_metrics.csv")
    for name in ("shock_session_response_20", "downshock_recovery_20"):
        baselines[name] = (batch2_metrics.query("candidate == @name"), read_scores(batch2 / f"scores_{name}.csv"), "group_ic_batch2_20260922")
    # Approved future-round atoms are reference inputs when their runs exist;
    # absent rounds are skipped so this script remains usable after each run.
    round_specs = {
        "wick_demand_20": "group_ic_round3_20260922",
        "clv_volume_pressure_20": "group_ic_round4_20260922",
        "lagged_volume_return_corr_20": "group_ic_round5_20260922",
        "reverse_illiquidity_5": "group_ic_reverse_illiquidity_20260922",
        "reverse_minute_late_return_5": "group_ic_reverse_minute_late_20260922",
        "market_residual_downside_20": "group_ic20_batch6_20260922",
        "body_transition_asymmetry_20": "group_ic20_batch6_20260922",
        "realized_vol_term_structure_5_20": "group_ic20_batch6_20260922",
        "amount_signed_imbalance_20": "group_ic20_batch6_20260922",
        "amount_return_asymmetry_20": "group_ic20_batch6_20260922",
        "return_acceleration_5_20": "group_ic20_batch6_20260922",
        "VAR_RATIO_5_60": "group_ic20_outcome_rejudge_v4_20260922",
        "RETURN_AUTOCOV_20": "group_ic20_outcome_rejudge_v4_20260922",
        "DOWN_UP_ACTIVITY_20": "group_ic20_outcome_rejudge_v4_20260922",
        "SHOCK_ACTIVITY_RESPONSE_20": "group_ic20_outcome_rejudge_v4_20260922",
        "RANGE_ACTIVITY_ELASTICITY_20": "group_ic20_outcome_rejudge_v4_20260922",
        "VOL_RESPONSE_ASYMMETRY_20": "group_ic20_outcome_rejudge_v4_20260922",
        "RETURN_CONCENTRATION_20": "group_ic20_outcome_rejudge_v4_20260922",
        "OVERHEAD_TURNOVER_20": "group_ic20_outcome_rejudge_v4_20260922",
        "reverse_realized_vol_term_structure_5_20": "group_ic_reverse_realized_vol_term_structure_20260922",
        "market_residual_skew_20": "group_ic20_batch7_20260922",
        "direction_range_coupling_20": "group_ic20_batch7_20260922",
        "amount_concentration_20": "group_ic20_batch7_20260922",
        "amount_innovation_return_beta_20": "group_ic20_batch7_20260922",
        "market_residual_abs_cluster_20": "group_ic20_batch9_daily_20260922",
        "range_to_return_lead_20": "group_ic20_batch9_daily_20260922",
        "minute_range_persistence_20": "group_ic20_batch9_minute_20260922",
        "minute_signed_flow_persistence_20": "group_ic20_batch9_minute_20260922",
        "minute_range_skew_20": "group_ic20_batch9_minute_20260922",
        "intraday_body_ar1_20": "group_ic20_batch11_20260922",
        "wick_body_coupling_20": "group_ic20_batch11_20260922",
        "close_location_dispersion_20": "group_ic20_batch11_20260922",
        "d2025_range_gap_abs_corr_20": "group_ic20_batch14_stage2_daily_a_20260923",
        "d2025_amount_innovation_abs_change_20": "group_ic20_batch14_stage2_daily_b_20260923",
        "d2025_body_wick_abs_corr_20": "group_ic20_batch14_stage2_daily_b_20260923",
        "d2025_minute_amount_abs_return_concentration_20": "group_ic20_batch15_stage2_minute_20260923",
        "d2025_amount_shock_body_efficiency_20": "group_ic20_batch17_stage2_daily_20260923",
        "d2025_amount_shock_wick_rejection_20": "group_ic20_batch17_stage2_daily_20260923",
        "d2025_body_positive_run_mean_20": "group_ic20_batch19_stage2_daily_a_rejudge_v2_20260923",
        "d2025_clv_extreme_recovery_rate_20": "group_ic20_batch19_stage2_daily_a_rejudge_v2_20260923",
        "d2025_range_shock_body_absorption_20": "group_ic20_batch19_stage2_daily_b_20260923",
        "d2025_range_shock_gap_absorption_20": "group_ic20_batch20_stage2_daily_a_20260923",
        "d2025_range_shock_clv_absorption_20": "group_ic20_batch20_stage2_daily_a_20260923",
        "d2025_range_shock_body_recovery_20": "group_ic20_batch20_stage2_daily_b_20260923",
        "d2025_range_shock_wick_rejection_20": "group_ic20_batch21_stage2_daily_20260923",
        "d2025_clv_extreme_wick_rejection_20": "group_ic20_batch22_stage2_daily_20260923",
    }
    for name, run_name in round_specs.items():
        r = runs / run_name
        if (r / "daily_metrics.csv").exists() and (r / f"scores_{name}.csv").exists():
            rm = read_metrics(r / "daily_metrics.csv")
            baselines[name] = (rm.query("candidate == @name"), read_scores(r / f"scores_{name}.csv"), run_name)

    corr_rows, paired_rows = [], []
    paired_extra = {
        "wick_demand_20": ("close_location_20", "intraday_return_20"),
        "clv_volume_pressure_20": ("close_location_20", "amount_expansion_20", "price_volume_corr_20"),
        "lagged_volume_return_corr_20": ("price_volume_corr_20", "amount_expansion_20"),
        "reverse_illiquidity_5": ("illiquidity_5", "illiquidity_20"),
        "reverse_minute_late_return_5": ("minute_late_return_5",),
    }
    for cname in current_candidates:
        cm = current_metrics.query("candidate == @cname")
        cscore = read_scores(run / f"scores_{cname}.csv")
        for bname, (bm, bscore, brun) in baselines.items():
            if brun == args.run_id and bname == cname:
                continue
            reference_root = breadth if brun == "group_next8_20260922_v4" else runs / brun
            reference_labels = read_labels(reference_root / "group_labels.csv")
            label_dates = cscore.index.intersection(bscore.index).intersection(calendar)
            assert_labels_equal(current_labels, reference_labels, label_dates)
            rc = rank_corr(cscore, bscore, cm, bm, calendar)
            corr_rows.append({"candidate": cname, "baseline": bname, "baseline_run": brun, "n_common_metric_valid": int(len(rc)), "rank_corr_abs_mean": float(rc.abs().mean()) if len(rc) else np.nan, "dedup_fail_abs_mean_ge_0.7": bool(len(rc) and rc.abs().mean() >= .7)})
        paired_names = IC_BASELINES + tuple(paired_extra.get(cname, ()))
        for bname in dict.fromkeys(paired_names):
            if bname not in baselines:
                continue
            bm, _, brun = baselines[bname]
            reference_root = breadth if brun == "group_next8_20260922_v4" else runs / brun
            reference_labels = read_labels(reference_root / "group_labels.csv")
            label_dates = pd.DatetimeIndex(cm.index.intersection(bm.index).intersection(calendar))
            assert_labels_equal(current_labels, reference_labels, label_dates)
            n, mean, hac = paired_ic(cm, bm, calendar)
            paired_rows.append({"candidate": cname, "baseline": bname, "baseline_run": brun, "n_common_metric_valid": n, "paired_ic_diff_mean": mean, "paired_ic_diff_hac_t_calendar_lag10": hac})

    pd.DataFrame(corr_rows).to_csv(out / "rounds_vs_reference_rank_corr.csv", index=False, float_format="%.17g")
    pd.DataFrame(paired_rows).to_csv(out / "rounds_vs_ic3_paired.csv", index=False, float_format="%.17g")
    (out / "REPORT.md").write_text("# ETF repeated-round IC diagnostics\n\nRead-only reference diagnostics for repeated small batches. Inputs use round-trip CSV parsing; only saved scores and original daily_metrics are read. The full current 2025 evaluation calendar is preserved and IC masks are the two original `daily_metrics.ic.notna()` masks. No factor, label, IC, return, or selection recomputation is performed. This is a repetition reference, not certification.\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
