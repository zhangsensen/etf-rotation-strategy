#!/usr/bin/env python3
"""Phase 2 of PREREG_LONGHISTORY_DISCOVERY_20260924.md: discovery-window
(proxy panel, 2015-01-05..2024-12-31) Spearman IC + Newey-West HAC t for
every CATALOG.csv candidate, selection (|HAC t| >= 3.0), post-selection
dedup (>=0.7 daily rank corr among SELECTED candidates only, keep larger
|t|), K<=10, SELECTED.json + sha256.

Label: close(D+1)/close(D) style forward return, specifically close(D+6)/
close(D+1) - 1 (prereg §1, the close-price analogue of the real line's
open(D+2)->open(D+7)). Built via close.shift(-1)/close.shift(-6) on the
SAME 2015-01-05..2024-12-31-truncated panel Phase 1 already uses -- a
label is allowed to look ahead of its own signal date by construction,
but never past the panel's own 2024-12-31 truncation (a date within 6
trading days of the panel's end naturally gets a NaN label via pandas'
own out-of-range shift, which is the "purge" the prereg asks for -- no
2025+ data is ever read to compute it).

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

import discover_longhistory_catalog_20260924 as phase1  # noqa: E402
from etf_strategy.core.etf_mining_referee import newey_west_t  # noqa: E402

OUT = phase1.OUT
HAC_LAG = 10
SELECT_T = 3.0
DEDUP_THRESHOLD = 0.7
K_MAX = 10


def build_label(close: pd.DataFrame) -> pd.DataFrame:
    """close(D+6)/close(D+1) - 1, per column. NaN for any D within 6
    trading days of the panel's own end (purge -- never reads past
    2024-12-31 since `close` itself never contains later rows)."""
    return close.shift(-6) / close.shift(-1) - 1.0


def daily_spearman_ic(atom: pd.DataFrame, label: pd.DataFrame) -> pd.Series:
    """Signed daily cross-sectional Spearman rank IC (all 8 columns must
    be valid in both atom and label that day, matching this campaign's
    established all-groups-valid convention)."""
    common_idx = atom.index.intersection(label.index)
    a = atom.loc[common_idx]
    b = label.loc[common_idx]
    valid = a.notna().all(axis=1) & b.notna().all(axis=1)
    a, b = a.loc[valid], b.loc[valid]
    ra = a.rank(axis=1)
    rb = b.rank(axis=1)
    ra_c = ra.sub(ra.mean(axis=1), axis=0)
    rb_c = rb.sub(rb.mean(axis=1), axis=0)
    numerator = (ra_c * rb_c).sum(axis=1)
    denominator = ((ra_c.pow(2)).sum(axis=1) * (rb_c.pow(2)).sum(axis=1)).pow(0.5)
    return numerator.div(denominator.where(denominator > 0))


def mean_abs_daily_rank_corr(a: pd.DataFrame, b: pd.DataFrame) -> float | None:
    common_idx = a.index.intersection(b.index)
    ra = a.loc[common_idx].rank(axis=1)
    rb = b.loc[common_idx].rank(axis=1)
    ra_c = ra.sub(ra.mean(axis=1), axis=0)
    rb_c = rb.sub(rb.mean(axis=1), axis=0)
    numerator = (ra_c * rb_c).sum(axis=1)
    denominator = ((ra_c.pow(2)).sum(axis=1) * (rb_c.pow(2)).sum(axis=1)).pow(0.5)
    corr = numerator.div(denominator.where(denominator > 0))
    valid = corr.dropna()
    return float(valid.abs().mean()) if len(valid) else None


def main():
    catalog = pd.read_csv(phase1.CATALOG_PATH)
    close = phase1.load_proxy_close()
    atoms = phase1.build_all_atoms(close, catalog)
    label = build_label(close)
    print(f"label built on the SAME {close.index.min().date()}..{close.index.max().date()} panel "
          f"(purge: last 6 rows get NaN label automatically)", flush=True)

    results = []
    ic_series_by_name = {}
    for name, atom in atoms.items():
        ic = daily_spearman_ic(atom, label)
        ic_series_by_name[name] = ic
        n = int(ic.notna().sum())
        ic_mean = float(ic.mean()) if n else float("nan")
        t = newey_west_t(ic, HAC_LAG) if n else float("nan")
        direction = int(np.sign(ic_mean)) if ic_mean == ic_mean and ic_mean != 0 else 0
        yearly = ic.groupby(ic.index.year).mean().round(4).to_dict()
        results.append({
            "name": name, "n": n, "ic_mean": round(ic_mean, 4) if ic_mean == ic_mean else None,
            "hac_t": round(t, 3) if t == t else None, "direction": direction,
            "yearly_ic": {int(k): v for k, v in yearly.items()},
        })
        print(f"{name}: n={n} ic_mean={ic_mean:.4f} hac_t={t:.2f} direction={direction}", flush=True)

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUT / "discovery_ic_all_candidates.csv", index=False)

    passing = results_df[results_df.hac_t.abs() >= SELECT_T].copy()
    passing = passing.sort_values("hac_t", key=lambda s: s.abs(), ascending=False)
    print(f"\n{len(passing)} candidates pass |HAC t| >= {SELECT_T}: {list(passing.name)}", flush=True)

    # Post-selection dedup: among PASSING candidates only, using their
    # SIGNED (direction-applied) atoms -- pairwise >=0.7, drop the one
    # with the smaller |t| (keep the larger), symmetric evaluation.
    signed_atoms = {row["name"]: atoms[row["name"]] * row["direction"] for _, row in passing.iterrows()}
    kept = list(passing.name)
    dropped_for_dedup = []
    changed = True
    while changed:
        changed = False
        for i, a_name in enumerate(kept):
            for b_name in kept[i + 1:]:
                corr = mean_abs_daily_rank_corr(signed_atoms[a_name], signed_atoms[b_name])
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
        "prereg": "frameworks/etf_rotation/docs/PREREG_LONGHISTORY_DISCOVERY_20260924.md",
        "catalog_sha256": hashlib.sha256(phase1.CATALOG_PATH.read_bytes()).hexdigest(),
        "discovery_panel": f"{close.index.min().date()}..{close.index.max().date()}",
        "select_threshold_abs_hac_t": SELECT_T,
        "dedup_threshold": DEDUP_THRESHOLD,
        "k_max": K_MAX,
        "n_catalog": len(catalog),
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
    }
    (OUT / "SELECTED.json").write_text(json.dumps(selected, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(selected, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
