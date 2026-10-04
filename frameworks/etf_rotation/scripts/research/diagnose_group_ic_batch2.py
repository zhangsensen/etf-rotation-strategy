"""Read-only, metric-aligned diagnostics for the approved batch-2 run."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "frameworks/etf_rotation/src"))
from etf_strategy.core.etf_mining_referee import newey_west_t_calendar

GROUPS = ["cn_technology_manufacturing", "hk_technology", "us_large_growth", "innovative_pharma", "gold", "metals_equity", "dividend_low_vol", "electric_power"]
def read_csv(path, **kwargs): return pd.read_csv(path, float_precision="round_trip", **kwargs)
def metric(path): return read_csv(path, parse_dates=["signal_date"]).set_index("signal_date")
def scores(path): return read_csv(path, index_col=0, parse_dates=True)[GROUPS]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run-id", default="group_ic_batch2_20260922"); args = ap.parse_args()
    run = ROOT / "runtime_outputs/etf_rotation_research/runs" / args.run_id
    out = run / "diagnostics_v2"; out.mkdir(parents=True, exist_ok=False)
    old_map = read_csv(ROOT / "runtime_outputs/etf_rotation_research/rejudgments/frozen80_2025_rejudge_20260922_v3/comparison.csv")[["candidate", "run"]].drop_duplicates()
    runs = ROOT / "runtime_outputs/etf_rotation_research/runs"
    new_metrics = metric(run / "daily_metrics.csv")
    breadth_root = ROOT / "runtime_outputs/etf_rotation_research/group_next8_20260922_v4"
    breadth_metrics = metric(breadth_root / "daily_metrics.csv")
    coverage = read_csv(run / "coverage.csv", parse_dates=["signal_date", "exit_date"])
    calendar = pd.DatetimeIndex(coverage.loc[coverage.in_evaluation_window & coverage.exit_date.notna() & (coverage.exit_date <= pd.Timestamp("2026-09-17")), "signal_date"]).sort_values().unique()
    assert len(calendar) == 409 and calendar.is_monotonic_increasing
    entries = [(r.candidate, r.run, metric(runs / r.run / "daily_metrics.csv").query("candidate == @r.candidate"), runs / r.run / f"scores_{r.candidate}.csv") for r in old_map.itertuples()]
    assert len(entries) == 80 and all(p.exists() for _, _, _, p in entries)
    breadth_entries = [(n, "group_next8_20260922_v4", breadth_metrics[breadth_metrics.candidate.eq(n)], breadth_root / f"scores_{n}.csv") for n in ("breadth_5", "breadth_20")]
    candidate_scores = {n: scores(run / f"scores_{n}.csv") for n in ("shock_session_response_20", "downshock_recovery_20")}
    rows = []
    for cname, cs in candidate_scores.items():
        cm = new_metrics[new_metrics.candidate.eq(cname)]
        for bname, brun, bm, spath in entries + breadth_entries:
            bs = scores(spath); common = cs.index.intersection(bs.index).intersection(calendar)
            valid = cm["ic"].reindex(common).notna() & bm["ic"].reindex(common).notna(); dates = common[valid.to_numpy()]
            corr = cs.loc[dates].rank(axis=1).corrwith(bs.loc[dates].rank(axis=1), axis=1).dropna()
            rows.append({"candidate": cname, "baseline": bname, "baseline_run": brun, "n_common_metric_valid": int(len(dates)), "rank_corr_mean": float(corr.mean()) if len(corr) else np.nan, "rank_corr_abs_mean": float(corr.abs().mean()) if len(corr) else np.nan, "dedup_fail_abs_mean_ge_0.7": bool(len(corr) and corr.abs().mean() >= .7)})
    pd.DataFrame(rows).sort_values(["candidate", "rank_corr_abs_mean"], ascending=[True, False]).to_csv(out / "batch2_vs_existing82_rank_corr.csv", index=False, float_format="%.17g")
    paired = {"shock_session_response_20": ["gap_20", "intraday_return_20", "efficiency_5", "range_expansion_5", "intraday_return_5"], "downshock_recovery_20": ["reversal_20", "downside_20", "volatility_20", "efficiency_5", "range_expansion_5", "intraday_return_5"]}
    old_by_name = {name: (brun, bm) for name, brun, bm, _ in entries}; paired_rows = []
    for cname, baselines in paired.items():
        a = new_metrics[new_metrics.candidate.eq(cname)]
        for bname in baselines:
            brun, b = old_by_name[bname]; common = pd.DatetimeIndex(a.index.intersection(b.index).intersection(calendar)); valid = a["ic"].reindex(common).notna() & b["ic"].reindex(common).notna(); common = common[valid.to_numpy()]
            for field in ("ic", "excess8"):
                delta = a[field].reindex(common) - b[field].reindex(common); aligned = delta.reindex(calendar)
                paired_rows.append({"candidate": cname, "baseline": bname, "baseline_run": brun, "metric": field, "n_common_metric_valid": int(delta.notna().sum()), "mean": float(delta.mean()), "hac_t_calendar_lag10": float(newey_west_t_calendar(aligned, calendar, 10))})
    pd.DataFrame(paired_rows).to_csv(out / "batch2_vs_pre_registered_baselines_paired.csv", index=False, float_format="%.17g")
    (out / "REPORT.md").write_text("# Batch 2 diagnostics v2\n\nMetric-aligned, read-only diagnostics. Inputs use `float_precision=round_trip`; the full 2025 evaluation calendar is retained and paired deltas are reindexed before calendar HAC. No IC, excess return, or selection weights are recomputed.\n\nRank correlations use exact frozen-v3 candidate-to-run mapping plus next8 breadth_5/breadth_20, masked by both original daily_metrics `ic.notna()` fields. Paired files contain only pre-registered baseline sets.\n")
    print(f"wrote {out}")
if __name__ == "__main__": main()
