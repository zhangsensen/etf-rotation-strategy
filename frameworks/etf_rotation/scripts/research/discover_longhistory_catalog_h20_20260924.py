#!/usr/bin/env python3
"""H20 addendum to PREREG_LONGHISTORY_DISCOVERY_20260924.md §7, step 1
(no labels read): CATALOG_H20.csv = the frozen H5 CATALOG.csv's 57
candidates (UNCHANGED, not recomputed here) + 3 portable close-only
entries from the library's 16 HAS_IC list (runtime_outputs/etf_rotation_
research/ic_inventory_20260923_claude_10rounds/has_ic.csv):
  - beta_asymmetry_60 (claude_rounds) -- this campaign's first-ever
    HAS_IC. Disclosed gap: Phase 1's automated close-only scan regex only
    matched `elif name ==` branches in build_atoms's dispatch chain and
    missed the very FIRST branch (`if name == "beta_asymmetry":`), so
    this generic, non-hardcoded-structure candidate was wrongly absent
    from the original 57-row H5 CATALOG.csv. The frozen H5 CATALOG.csv/
    SELECTED.json (0/57 passed |HAC t|>=3.0) are NOT retroactively
    modified or rerun -- that result stands as reported. This candidate
    is included fresh here, before any H20 label is read, so there is no
    contamination for the H20 exercise specifically.
  - market_residual_abs_cluster_20, market_coskewness_20 (daily_rounds)
    -- master's own two expected candidates for this task, verified
    close-only (both take only `close`, no hardcoded ticker/group
    structure -- `_market_residuals`/the coskewness loop both use
    generic leave-one-out/leave-none equal-weight means over whatever
    columns are passed).

`breadth_5` (also in has_ic.csv) was checked and could not be traced to
a close-only-only implementation within this task's time budget (its
"daily" engine's own build_atoms has no "breadth" mechanism key at all in
the archived run's PLAN.json; the actual computation appears to live
outside build_atoms' per-member dispatch) -- excluded rather than guessed,
disclosed explicitly rather than silently dropped.

Runs structural diagnostics + no-label dedup precheck for the FULL 60
(reusing the same functions as Phase 1's driver; the original 57's own
diagnostics are recomputed here too for a single consistent combined
report, not because anything about them changed).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "frameworks/etf_rotation/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import discover_longhistory_catalog_20260924 as phase1  # noqa: E402
from etf_strategy.core import etf_group_claude_rounds as claude_rounds  # noqa: E402
from etf_strategy.core import etf_group_daily_rounds as daily_rounds  # noqa: E402

OUT = phase1.OUT
CATALOG_H20_PATH = OUT / "CATALOG_H20.csv"

# The 3 new H20 additions, dispatched separately from Phase 1's _A_BUILD_FNS
# (the daily_rounds ones take ONLY `close`, no window parameter -- their
# window is a module-level WINDOW=20 constant baked into the formula, not
# parametrized, unlike every claude_rounds candidate).
_NEW_BUILD_FNS = {
    "beta_asymmetry_60": lambda close: claude_rounds._build_beta_asymmetry(close, 60),
    "market_residual_abs_cluster_20": lambda close: daily_rounds._build_market_residual_abs_cluster(close),
    "market_coskewness_20": lambda close: daily_rounds._build_market_coskewness(close),
}


def build_all_atoms_h20(close: pd.DataFrame, catalog_h20: pd.DataFrame) -> dict[str, pd.DataFrame]:
    atoms = {}
    original = catalog_h20[catalog_h20.name.isin(pd.read_csv(phase1.CATALOG_PATH).name)]
    atoms.update(phase1.build_all_atoms(close, original))
    for name, fn in _NEW_BUILD_FNS.items():
        atoms[name] = fn(close)
    return atoms


def main():
    catalog_h20 = pd.read_csv(CATALOG_H20_PATH)
    close = phase1.load_proxy_close()
    atoms = build_all_atoms_h20(close, catalog_h20)
    print(f"H20 catalog: {len(atoms)} candidates ({len(catalog_h20) - len(_NEW_BUILD_FNS)} from frozen H5 "
          f"CATALOG.csv unchanged + {len(_NEW_BUILD_FNS)} new library-HAS_IC additions), "
          f"panel {close.index.min().date()}..{close.index.max().date()}, no labels read", flush=True)

    struct = phase1.structural_diagnostics(atoms)
    struct.to_csv(OUT / "structural_diagnostics_H20.csv", index=False)

    dedup = phase1.dedup_precheck(atoms)
    dedup.to_csv(OUT / "dedup_precheck_H20.csv", index=False)

    flagged = dedup[dedup.mean_abs_daily_rank_corr >= 0.7]
    structurally_invalid = sorted(struct[struct.status == "STRUCTURALLY_INVALID"].candidate.unique())
    new_candidate_status = {
        name: ("STRUCTURALLY_INVALID" if name in structurally_invalid else "OK")
        for name in _NEW_BUILD_FNS
    }
    new_candidate_dedup_max = (
        dedup[dedup.candidate.isin(_NEW_BUILD_FNS)]
        .groupby("candidate").mean_abs_daily_rank_corr.max().round(4).to_dict()
    )

    summary = {
        "discovery_panel": f"{close.index.min().date()}..{close.index.max().date()}",
        "n_catalog_candidates": len(atoms),
        "n_new_h20_additions": len(_NEW_BUILD_FNS),
        "new_additions": list(_NEW_BUILD_FNS),
        "excluded_but_checked": ["breadth_5 (could not confirm close-only implementation in time budget)"],
        "labels_read": False,
        "structurally_invalid_candidates": structurally_invalid,
        "new_candidate_structural_status": new_candidate_status,
        "new_candidate_dedup_max": new_candidate_dedup_max,
        "flagged_pairs_ge_0_7": len(flagged) // 2,
    }
    (OUT / "summary_H20_catalog.json").write_text(
        __import__("json").dumps(summary, indent=2, ensure_ascii=False, default=str) + "\n"
    )
    print(__import__("json").dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
