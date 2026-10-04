#!/usr/bin/env python3
"""Round 652 atom health (S50, main controller directive 2026-09-21): 2
new repl_pi37_core_v1 atoms (reproduction of pi lane's stage-37
mechanism atoms). Small-sample pilot (3 symbols) ran 4.8s; full
14-symbol run extrapolated ~22.5s, ran directly.

Per directive: report R_LUNCH_DIR_BET_20's correlation against this
line's own S30 PM_POSTRUN_DAY_CONSIST_20 (mechanism_atoms_v3) for
transparency -- the directive forbids substituting one for the other,
this is purely a disclosure check."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as eng  # noqa: E402
from etf_strategy.core.family_registry import load_builtin_families, resolve_family  # noqa: E402

OUT = eng.WORKSPACE_OUTPUTS / "round_652"
OUT.mkdir(parents=True, exist_ok=True)
NEW_SOURCE = "repl_pi37_core_v1"

REF_SOURCES = [
    ("mechanism_atoms_v3", "PM_POSTRUN_DAY_CONSIST_20"),
    ("intraday_pain_recovery_1m", "ULCER_INDEX_CHG_20"),
    ("intraday_drawdown_1m", "UNDERWATER_FRAC_CHG_20"),
    ("pi_lunch_prerun_1m", "LUNCH_PRE_RUN_20"),
]
DISCOVERY_END = eng.DISCOVERY_END
AUDIT_START, AUDIT_END = eng.AUDIT_START, eng.AUDIT_END


def _ic_series(signal: pd.DataFrame, forward: pd.DataFrame, eligibility: pd.DataFrame) -> pd.Series:
    sig = signal.where(eligibility)
    ics = {}
    for date, row in sig.iterrows():
        if date not in forward.index:
            continue
        f = forward.loc[date]
        mask = row.notna() & f.notna()
        if mask.sum() < eng.MIN_PAIRS:
            continue
        ics[date] = row[mask].rank().corr(f[mask].rank())
    return pd.Series(ics).dropna()


def main() -> None:
    load_builtin_families()
    panels, eligibility_all, symbols, forward = eng._load_context()
    dates = panels["close"].index
    discovery_mask = dates <= DISCOVERY_END
    audit_mask = (dates >= AUDIT_START) & (dates <= AUDIT_END)
    f5 = forward[5]

    ref_ranked = {}
    for ref_source, ref_name in REF_SOURCES:
        try:
            ref_mining = yaml.safe_load(eng._config_path(ref_source).read_text())
            ref_space = resolve_family(ref_source).builder(panels, eligibility_all, eng.CANONICAL_ROOT, ref_mining)
            ranked = eng.cross_sectional_rank(ref_space[ref_name][symbols], eligibility_all[symbols])
            ref_ranked[f"{ref_source}:{ref_name}"] = eng._stride_vector(ranked)
        except Exception as exc:  # noqa: BLE001
            print(f"skip reference {ref_source}:{ref_name}: {exc}")

    mining = yaml.safe_load(eng._config_path(NEW_SOURCE).read_text())
    space = resolve_family(NEW_SOURCE).builder(panels, eligibility_all, eng.CANONICAL_ROOT, mining)

    rows = []
    for atom_cfg in mining.get("atoms", []):
        name = atom_cfg["name"]
        raw = space[name][symbols]
        n_finite = int(np.isfinite(raw.to_numpy(dtype=float)).sum())
        if n_finite == 0:
            rows.append({"atom": name, "disc_ic": float("nan"), "disc_days": 0,
                         "audit_ic": float("nan"), "n_finite": 0, "max_corr_vs_ref": float("nan"), "max_corr_ref_key": ""})
            continue
        ranked = eng.cross_sectional_rank(raw, eligibility_all[symbols])
        disc = _ic_series(ranked.loc[discovery_mask], f5.loc[discovery_mask], eligibility_all[symbols].loc[discovery_mask])
        audit = _ic_series(ranked.loc[audit_mask], f5.loc[audit_mask], eligibility_all[symbols].loc[audit_mask])
        strat = eng._stride_vector(ranked)

        best_corr, best_key = float("nan"), ""
        for ref_key, ref_vec in ref_ranked.items():
            c = eng._pairwise_pearson(strat, ref_vec)
            if np.isfinite(c) and (not np.isfinite(best_corr) or abs(c) > abs(best_corr)):
                best_corr, best_key = c, ref_key

        # explicit disclosure corr vs PM_POSTRUN_DAY_CONSIST_20 for R_LUNCH_DIR_BET_20
        pm_corr = float("nan")
        if "mechanism_atoms_v3:PM_POSTRUN_DAY_CONSIST_20" in ref_ranked:
            pm_corr = eng._pairwise_pearson(strat, ref_ranked["mechanism_atoms_v3:PM_POSTRUN_DAY_CONSIST_20"])

        rows.append(
            {
                "atom": name,
                "disc_ic": float(disc.mean()) if len(disc) else float("nan"),
                "disc_days": int(len(disc)),
                "audit_ic": float(audit.mean()) if len(audit) else float("nan"),
                "n_finite": n_finite,
                "max_corr_vs_ref": best_corr,
                "max_corr_ref_key": best_key,
                "corr_vs_PM_POSTRUN_DAY_CONSIST_20": pm_corr,
            }
        )
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "atom_health.csv", index=False)
    summary = {"round_id": "round_652_build", "stage": "S50_repl_pi37_core_v1", "as_of": eng.AS_OF, "new_source": NEW_SOURCE}
    (OUT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
