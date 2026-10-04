#!/usr/bin/env python3
"""H20 step 2 of PREREG_LONGHISTORY_DISCOVERY_20260924.md §7: discovery-
window (proxy panel, 2015-01-05..2024-12-31) Spearman IC + Newey-West HAC
t (lag=30) for every CATALOG_H20.csv candidate (60, the frozen H5 57 +
beta_asymmetry_60/market_residual_abs_cluster_20/market_coskewness_20),
label close(D+1)->close(D+21) (purge for the boundary, same mechanism as
H5's own build_label just with a 21-day horizon instead of 6). Selection
(|HAC t| >= 3.0), post-selection dedup (>=0.7, keep larger |t|), K<=10,
SELECTED_H20.json + sha256.

No real ETF 2025+ label is read anywhere in this script.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "frameworks/etf_rotation/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import discover_longhistory_catalog_h20_20260924 as h20_catalog  # noqa: E402
import discover_longhistory_ic_20260924 as phase2  # noqa: E402
from etf_strategy.core.etf_mining_referee import newey_west_t  # noqa: E402

OUT = h20_catalog.OUT
HAC_LAG_H20 = 30
HORIZON_H20 = 21
SELECT_T = 3.0
DEDUP_THRESHOLD = 0.7
K_MAX = 10


def build_label_h20(close: pd.DataFrame) -> pd.DataFrame:
    """close(D+21)/close(D+1) - 1, per column. NaN (purge) for any D
    within 21 trading days of the panel's own 2024-12-31 end -- same
    out-of-range-shift mechanism as H5's build_label, just HORIZON_H20
    instead of 6."""
    return close.shift(-HORIZON_H20) / close.shift(-1) - 1.0


def main():
    catalog_h20 = pd.read_csv(h20_catalog.CATALOG_H20_PATH)
    close = h20_catalog.phase1.load_proxy_close()
    atoms = h20_catalog.build_all_atoms_h20(close, catalog_h20)
    label = build_label_h20(close)
    print(f"H20 label built on {close.index.min().date()}..{close.index.max().date()} "
          f"(purge: last {HORIZON_H20} rows get NaN label)", flush=True)

    results = []
    for name, atom in atoms.items():
        ic = phase2.daily_spearman_ic(atom, label)
        n = int(ic.notna().sum())
        ic_mean = float(ic.mean()) if n else float("nan")
        t = newey_west_t(ic, HAC_LAG_H20) if n else float("nan")
        direction = int(np.sign(ic_mean)) if ic_mean == ic_mean and ic_mean != 0 else 0
        yearly = ic.groupby(ic.index.year).mean().round(4).to_dict()
        results.append({
            "name": name, "n": n, "ic_mean": round(ic_mean, 4) if ic_mean == ic_mean else None,
            "hac_t": round(t, 3) if t == t else None, "direction": direction,
            "yearly_ic": {int(k): v for k, v in yearly.items()},
        })
        print(f"{name}: n={n} ic_mean={ic_mean:.4f} hac_t={t:.2f} direction={direction}", flush=True)

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUT / "discovery_ic_all_candidates_H20.csv", index=False)

    passing = results_df[results_df.hac_t.abs() >= SELECT_T].copy()
    passing = passing.sort_values("hac_t", key=lambda s: s.abs(), ascending=False)
    print(f"\n{len(passing)} candidates pass |HAC t| >= {SELECT_T}: {list(passing.name)}", flush=True)

    signed_atoms = {row["name"]: atoms[row["name"]] * row["direction"] for _, row in passing.iterrows()}
    kept = list(passing.name)
    dropped_for_dedup = []
    changed = True
    while changed:
        changed = False
        for i, a_name in enumerate(kept):
            for b_name in kept[i + 1:]:
                corr = phase2.mean_abs_daily_rank_corr(signed_atoms[a_name], signed_atoms[b_name])
                if corr is not None and corr >= DEDUP_THRESHOLD:
                    a_t = float(passing.loc[passing.name == a_name, "hac_t"].abs().iloc[0])
                    b_t = float(passing.loc[passing.name == b_name, "hac_t"].abs().iloc[0])
                    drop = b_name if a_t >= b_t else a_name
                    kept.remove(drop)
                    dropped_for_dedup.append({"dropped": drop, "kept_instead": a_name if drop == b_name else b_name,
                                               "mean_abs_daily_rank_corr": round(corr, 4)})
                    changed = True
                    break
            if changed:
                break

    final = passing[passing.name.isin(kept)].sort_values("hac_t", key=lambda s: s.abs(), ascending=False)
    final = final.head(K_MAX)
    print(f"\nafter dedup, K<={K_MAX}: {len(final)} selected: {list(final.name)}", flush=True)

    selected = {
        "prereg": "frameworks/etf_rotation/docs/PREREG_LONGHISTORY_DISCOVERY_20260924.md §7",
        "catalog_h20_sha256": hashlib.sha256(h20_catalog.CATALOG_H20_PATH.read_bytes()).hexdigest(),
        "discovery_panel": f"{close.index.min().date()}..{close.index.max().date()}",
        "horizon": HORIZON_H20, "hac_lag": HAC_LAG_H20,
        "select_threshold_abs_hac_t": SELECT_T,
        "dedup_threshold": DEDUP_THRESHOLD,
        "k_max": K_MAX,
        "n_catalog": len(catalog_h20),
        "n_passing_before_dedup": len(passing),
        "n_dropped_for_dedup": len(dropped_for_dedup),
        "dedup_drops": dropped_for_dedup,
        "selected": [
            {
                "name": row["name"], "direction": int(row["direction"]),
                "ic_mean": row["ic_mean"], "hac_t": row["hac_t"], "n": int(row["n"]),
                "yearly_ic": row["yearly_ic"],
            }
            for _, row in final.iterrows()
        ],
        "labels_read": "discovery_proxy_only_2015_2024_never_real_etf_2025plus",
        "judgment_note": "real ETF 2025-01-01..cold line has only ~14 non-overlapping H20 windows "
                          "-- per prereg, selected entries go straight to forward monthly cumulative-IC "
                          "registration, not a pass/fail gate.",
    }
    (OUT / "SELECTED_H20.json").write_text(json.dumps(selected, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(selected, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
