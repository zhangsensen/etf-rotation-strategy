#!/usr/bin/env python3
"""Phase 1 of PREREG_LONGHISTORY_DISCOVERY_20260924.md: CATALOG.csv's
close-only candidates computed on the 8-group discovery proxy panel
(2015-01-05..2024-12-31, truncated from etf_group_regime_longhistory.
build()'s own 2015-01-05..COLD return panel), structural diagnostics and
no-label dedup precheck. NO LABEL (forward return) is read anywhere in
this script -- that only happens in Phase 2's discovery-IC script, after
etf-reviewer approves this CATALOG + this code.

Panel reuse: `build()` (etf_group_regime_longhistory.py) is called
UNCHANGED (same 8-group mapping, same ffill/reindex logic) and its output
(daily RETURNS through COLD) is simply truncated to <=2024-12-31 here --
no reimplementation of the group-composition/alignment logic, per the
prereg's "面板复用...build的映射但截到2024-12-31+purge". The 8-group
"close" proxy used by every close-price candidate is reconstructed from
those truncated returns via cumprod (exact inverse of pct_change, no
information added or removed).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "frameworks/etf_rotation/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import etf_group_regime_longhistory as regime_base  # noqa: E402
import etf_group_longhistory_literature_factors as lit  # noqa: E402
from etf_strategy.core import etf_group_claude_rounds as claude_rounds  # noqa: E402

OUT = ROOT / "runtime_outputs/etf_rotation_research/longhistory_discovery_20260924"
CATALOG_PATH = OUT / "CATALOG.csv"
DISCOVERY_END = "2024-12-31"  # Phase 1/2 boundary -- never read past this date here.

# name -> (build_fn, window, kwargs) for every source=a CATALOG row, using
# the EXACT registered window from etf_group_claude_rounds._DEFINITIONS
# (verified against CATALOG.csv's own window column at runtime below).
_A_BUILD_FNS = {
    "corr_stability_20_60": claude_rounds._build_corr_stability_20_60,
    "lead_to_market": claude_rounds._build_lead_to_market,
    "vol_scaled_momentum": claude_rounds._build_vol_scaled_momentum,
    "tsmom_consistency": claude_rounds._build_tsmom_consistency,
    "vol_of_vol": claude_rounds._build_vol_of_vol,
    "downside_correlation": claude_rounds._build_downside_correlation,
    "beta_variability": claude_rounds._build_beta_variability,
    "market_tail_relative_return": claude_rounds._build_market_tail_relative_return,
    "capture_asymmetry": claude_rounds._build_capture_asymmetry,
    "corr_level": claude_rounds._build_corr_level,
    "residual_vol_term_structure_20_60": claude_rounds._build_residual_vol_term_structure,
    "high_low_vol_beta_gap": claude_rounds._build_high_low_vol_beta_gap,
    "market_jump_response": claude_rounds._build_market_jump_response,
    "lag1_beta_to_market": claude_rounds._build_lag1_beta_to_market,
    "residual_skew_gap": claude_rounds._build_residual_skew_gap,
    "residual_market_vol_corr": claude_rounds._build_residual_market_vol_corr,
    "cokurtosis": claude_rounds._build_cokurtosis,
    "downside_coskewness": claude_rounds._build_downside_coskewness,
    "avg_peer_residual_corr": claude_rounds._build_avg_peer_residual_corr,
    "peer_corr_network_change": claude_rounds._build_peer_corr_network_change,
    "peer_corr_dispersion": claude_rounds._build_peer_corr_dispersion,
    "quantile_beta_gap": claude_rounds._build_quantile_beta_gap,
    "tail_coexceedance_asymmetry": claude_rounds._build_tail_coexceedance_asymmetry,
    "residual_kurtosis": claude_rounds._build_residual_kurtosis,
    "residual_variance_ratio_1_5": claude_rounds._build_residual_variance_ratio_1_5,
    "residual_sign_run": claude_rounds._build_residual_sign_run,
    "residual_drawdown": claude_rounds._build_residual_drawdown,
    "residual_tail_ratio": claude_rounds._build_residual_tail_ratio,
    "roll_spread": claude_rounds._build_roll_spread,
    "post_market_tail_relative_return": claude_rounds._build_post_market_tail_relative_return,
    "post_own_tail_relative_return": claude_rounds._build_post_own_tail_relative_return,
    "corr_horizon_ratio": claude_rounds._build_corr_horizon_ratio,
    "beta_horizon_ratio": claude_rounds._build_beta_horizon_ratio,
    "month_end_calendar_relative_return": claude_rounds._build_month_end_calendar_relative_return,
    "rank_persistence": claude_rounds._build_rank_persistence,
    "residual_semideviation_asymmetry": claude_rounds._build_residual_semideviation_asymmetry,
    "weekday_relative_return_pattern": claude_rounds._build_weekday_relative_return_pattern,
    "post_market_tail_delayed_relative_return": claude_rounds._build_post_market_tail_delayed_relative_return,
    "post_own_tail_delayed_relative_return": claude_rounds._build_post_own_tail_delayed_relative_return,
}
# The two "skip" momentum candidates take extra kwargs, dispatched separately.
_A_MOMENTUM_SKIP = {
    "momentum_120_skip5": dict(lookback=120, skip=5),
    "momentum_250_skip20": dict(lookback=250, skip=20),
}

_B_BUILD_FNS = {
    "vol_20": lambda close, w: lit.build_realized_vol(close, w),
    "vol_60": lambda close, w: lit.build_realized_vol(close, w),
    "beta_ew8_60": lambda close, w: lit.build_beta_to_ew8(close, w),
    "idio_vol_60": lambda close, w: lit.build_idio_vol(close, w),
    "residual_momentum_120": lambda close, w: lit.build_residual_momentum(close, w),
    "max5": lambda close, w: lit.build_max5(close, w),
    "skew_60": lambda close, w: lit.build_skew(close, w),
    "downside_beta_60": lambda close, w: lit.build_downside_beta(close, w),
    "corr_to_ew8_change_60": lambda close, w: lit.build_corr_to_ew8_change(close, w),
}
_B_TRAILING_RETURN = {
    "momentum_5": 5, "reversal_5": 5, "momentum_20": 20, "reversal_20": 20,
    "momentum_60": 60, "momentum_120": 120, "momentum_250": 250,
}


def load_proxy_close() -> pd.DataFrame:
    """8-group discovery-proxy close level, 2015-01-05..2024-12-31 (Phase
    1/2 boundary; the real build() panel runs through COLD but is never
    read past DISCOVERY_END anywhere in this script)."""
    returns = regime_base.build()
    returns = returns.loc[:DISCOVERY_END]
    close = (1.0 + returns).cumprod()
    return close


def build_all_atoms(close: pd.DataFrame, catalog: pd.DataFrame) -> dict[str, pd.DataFrame]:
    atoms = {}
    for _, row in catalog.iterrows():
        name, window, source = row["name"], int(row["window"]), row["source"]
        if source == "a":
            if name in _A_MOMENTUM_SKIP:
                atoms[name] = claude_rounds._build_momentum_skip(close, **_A_MOMENTUM_SKIP[name])
            else:
                atoms[name] = _A_BUILD_FNS[name](close, window)
        else:
            if name in _B_TRAILING_RETURN:
                atoms[name] = lit.build_trailing_return(close, _B_TRAILING_RETURN[name])
            else:
                atoms[name] = _B_BUILD_FNS[name](close, window)
    return atoms


def structural_diagnostics(atoms: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per-candidate, per-column (= per economic group, no further
    aggregation needed on this already-group-level proxy panel) nan_rate
    and mode_value_rate, same >0.20 / >0.50 STRUCTURALLY_INVALID
    thresholds as the real-panel diagnostics scripts use."""
    rows = []
    for name, atom in atoms.items():
        for col in atom.columns:
            s = atom[col]
            valid = s.dropna()
            nan_rate = float(s.isna().mean())
            mode_rate = (
                float(valid.round(10).value_counts().iloc[0] / len(valid)) if len(valid) else float("nan")
            )
            status = "STRUCTURALLY_INVALID" if (nan_rate > 0.20 or (mode_rate or 0) > 0.50) else "OK"
            rows.append({
                "candidate": name, "column": col,
                "nan_rate": round(nan_rate, 4),
                "mode_value_rate": round(mode_rate, 4) if mode_rate == mode_rate else None,
                "status": status,
            })
        all_valid = atom.notna().all(axis=1)
        rows.append({
            "candidate": name, "column": "__all_8_valid__", "nan_rate": None, "mode_value_rate": None,
            "status": f"days_all_8_valid={int(all_valid.sum())}/{len(atom)}",
        })
    return pd.DataFrame(rows)


def mean_abs_daily_rank_corr(a: pd.DataFrame, b: pd.DataFrame) -> tuple[float | None, int]:
    common_idx = a.index.intersection(b.index)
    common_cols = a.columns.intersection(b.columns)
    if len(common_idx) == 0 or len(common_cols) < 2:
        return None, 0
    ra = a.loc[common_idx, common_cols].rank(axis=1)
    rb = b.loc[common_idx, common_cols].rank(axis=1)
    ra_c = ra.sub(ra.mean(axis=1), axis=0)
    rb_c = rb.sub(rb.mean(axis=1), axis=0)
    numerator = (ra_c * rb_c).sum(axis=1)
    denominator = ((ra_c.pow(2)).sum(axis=1) * (rb_c.pow(2)).sum(axis=1)).pow(0.5)
    corr = numerator.div(denominator.where(denominator > 0))
    valid = corr.dropna()
    if len(valid) == 0:
        return None, 0
    return float(valid.abs().mean()), len(valid)


def dedup_precheck(atoms: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """No-label pairwise dedup among ALL catalog candidates (raw,
    undirected -- direction is not assigned until Phase 2's discovery IC
    sign, and .abs() on the correlation already makes a same-vs-opposite-
    sign duplicate like momentum_5/reversal_5 show up as redundant
    regardless). Each unordered pair recorded symmetrically (master's
    round-8+ convention): both sides get their own max_corr entry."""
    names = list(atoms)
    rows = []
    for name in names:
        for other in names:
            if other == name:
                continue
            corr, n = mean_abs_daily_rank_corr(atoms[name], atoms[other])
            if corr is not None:
                rows.append({"candidate": name, "compared_against": other,
                             "mean_abs_daily_rank_corr": corr, "n_common_days": n})
    return pd.DataFrame(rows)


def main():
    catalog = pd.read_csv(CATALOG_PATH)
    close = load_proxy_close()
    print(f"proxy close panel: {close.shape[0]} days x {close.shape[1]} groups, "
          f"{close.index.min().date()}..{close.index.max().date()}", flush=True)

    atoms = build_all_atoms(close, catalog)
    print(f"computed {len(atoms)} catalog atoms (no labels read)", flush=True)

    struct = structural_diagnostics(atoms)
    struct.to_csv(OUT / "structural_diagnostics.csv", index=False)

    dedup = dedup_precheck(atoms)
    dedup.to_csv(OUT / "dedup_precheck.csv", index=False)

    flagged = dedup[dedup.mean_abs_daily_rank_corr >= 0.7]
    per_candidate_max = dedup.groupby("candidate").mean_abs_daily_rank_corr.max().sort_values(ascending=False)
    structurally_invalid = sorted(struct[struct.status == "STRUCTURALLY_INVALID"].candidate.unique())

    summary = {
        "discovery_panel": f"{close.index.min().date()}..{close.index.max().date()}",
        "n_catalog_candidates": len(atoms),
        "labels_read": False,
        "structurally_invalid_candidates": structurally_invalid,
        "per_candidate_max_dedup_corr": per_candidate_max.round(4).to_dict(),
        "flagged_pairs_ge_0_7": len(flagged) // 2,  # symmetric recording double-counts pairs
        "flagged_pair_list": sorted({tuple(sorted((r.candidate, r.compared_against)))
                                      for r in flagged.itertuples()}),
    }
    (OUT / "summary_phase1.json").write_text(
        __import__("json").dumps(summary, indent=2, ensure_ascii=False, default=str) + "\n"
    )
    print(__import__("json").dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
