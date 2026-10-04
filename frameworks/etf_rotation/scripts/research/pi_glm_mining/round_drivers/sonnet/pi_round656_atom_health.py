#!/usr/bin/env python3
"""Round 656 atom health (S54, main controller directive 2026-09-21): 2
new atoms added to the existing category_relative_geometry family --
REL_ULCER_CATEGORY_CHG_20, REL_RECOVERY_TIME_CATEGORY_CHG_20. Small-
sample pilot (3 symbols) ran 35.0s; full 14-symbol run extrapolated
~2.7 min, well under the 10-minute threshold -- ran directly.

Per directive: report REL_UNDERWATER_CATEGORY_CHG_20's corr vs
UNDERWATER_FRAC_CHG_20 and REL_UNDERWATER_CATEGORY_20 for reference
(that atom itself is NOT re-registered this round -- it was already
single-atom gate-7 re-adjudicated in round_631 as S32A1, rejected for
rank_correlation_redundancy vs prior:round_545:QA8, corr 0.83)."""
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

OUT = eng.WORKSPACE_OUTPUTS / "round_656"
OUT.mkdir(parents=True, exist_ok=True)
NEW_SOURCE = "category_relative_geometry"
NEW_ATOMS = ("REL_ULCER_CATEGORY_CHG_20", "REL_RECOVERY_TIME_CATEGORY_CHG_20")

REF_CHECK = {
    "REL_ULCER_CATEGORY_CHG_20": [
        ("intraday_pain_recovery_1m", "ULCER_INDEX_CHG_20"),
        ("category_relative_geometry", "REL_UNDERWATER_CATEGORY_CHG_20"),
    ],
    "REL_RECOVERY_TIME_CATEGORY_CHG_20": [
        ("category_relative_geometry", "REL_RECOVERY_TIME_CATEGORY_20"),
        ("intraday_pain_recovery_1m", "RECOVERY_TIME_FRAC_20"),
    ],
}
# also report the disclosure check requested for REL_UNDERWATER_CATEGORY_CHG_20
# itself (already-tested atom, not re-registered, corr reported for context)
DISCLOSURE_CHECK = [
    ("mechanism_atoms_v2", "REL_UNDERWATER_CATEGORY_20"),
]
REF_SOURCES = sorted({s for checks in REF_CHECK.values() for s, _ in checks} | {"intraday_drawdown_1m"})
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

    mining = yaml.safe_load(eng._config_path(NEW_SOURCE).read_text())
    space = resolve_family(NEW_SOURCE).builder(panels, eligibility_all, eng.CANONICAL_ROOT, mining)

    ref_ranked = {}
    for src in REF_SOURCES:
        try:
            if src == NEW_SOURCE:
                ref_space = space
                ref_mining = mining
            else:
                ref_mining = yaml.safe_load(eng._config_path(src).read_text())
                ref_space = resolve_family(src).builder(panels, eligibility_all, eng.CANONICAL_ROOT, ref_mining)
        except Exception as exc:  # noqa: BLE001
            print(f"skip reference family {src}: {exc}")
            continue
        for atom_cfg in ref_mining.get("atoms", []):
            name = atom_cfg["name"]
            try:
                ranked = eng.cross_sectional_rank(ref_space[name][symbols], eligibility_all[symbols])
            except Exception:  # noqa: BLE001
                continue
            ref_ranked[f"{src}:{name}"] = eng._stride_vector(ranked)

    # also fetch mechanism_atoms_v2:REL_UNDERWATER_CATEGORY_20 and QA8's
    # UNDERWATER_FRAC_CHG_20 for the disclosure check
    disclosure_ranked = {}
    for src, name in DISCLOSURE_CHECK + [("intraday_drawdown_1m", "UNDERWATER_FRAC_CHG_20")]:
        key = f"{src}:{name}"
        if key in ref_ranked:
            disclosure_ranked[key] = ref_ranked[key]
            continue
        try:
            d_mining = yaml.safe_load(eng._config_path(src).read_text())
            d_space = resolve_family(src).builder(panels, eligibility_all, eng.CANONICAL_ROOT, d_mining)
            ranked = eng.cross_sectional_rank(d_space[name][symbols], eligibility_all[symbols])
            disclosure_ranked[key] = eng._stride_vector(ranked)
        except Exception as exc:  # noqa: BLE001
            print(f"skip disclosure ref {key}: {exc}")

    rel_uw_chg_strat = None
    if "REL_UNDERWATER_CATEGORY_CHG_20" in mining.get("atoms", [{}])[0].get("name", "") or True:
        try:
            ranked = eng.cross_sectional_rank(
                space["REL_UNDERWATER_CATEGORY_CHG_20"][symbols], eligibility_all[symbols]
            )
            rel_uw_chg_strat = eng._stride_vector(ranked)
        except Exception as exc:  # noqa: BLE001
            print(f"skip REL_UNDERWATER_CATEGORY_CHG_20 disclosure: {exc}")

    rows = []
    for name in NEW_ATOMS:
        raw = space[name][symbols]
        n_finite = int(np.isfinite(raw.to_numpy(dtype=float)).sum())
        if n_finite == 0:
            rows.append({"atom": name, "disc_ic": float("nan"), "disc_days": 0,
                         "audit_ic": float("nan"), "n_finite": 0})
            continue
        ranked = eng.cross_sectional_rank(raw, eligibility_all[symbols])
        disc = _ic_series(ranked.loc[discovery_mask], f5.loc[discovery_mask], eligibility_all[symbols].loc[discovery_mask])
        audit = _ic_series(ranked.loc[audit_mask], f5.loc[audit_mask], eligibility_all[symbols].loc[audit_mask])
        strat = eng._stride_vector(ranked)

        corrs = {}
        for src, ref_name in REF_CHECK[name]:
            key = f"{src}:{ref_name}"
            if key in ref_ranked:
                corrs[key] = eng._pairwise_pearson(strat, ref_ranked[key])

        rows.append(
            {
                "atom": name,
                "disc_ic": float(disc.mean()) if len(disc) else float("nan"),
                "disc_days": int(len(disc)),
                "audit_ic": float(audit.mean()) if len(audit) else float("nan"),
                "n_finite": n_finite,
                **{f"corr_vs_{k}": v for k, v in corrs.items()},
            }
        )
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "atom_health.csv", index=False)

    disclosure_rows = []
    if rel_uw_chg_strat is not None:
        for key, ref_vec in disclosure_ranked.items():
            disclosure_rows.append({
                "atom": "REL_UNDERWATER_CATEGORY_CHG_20 (already tested S32A1, not re-registered)",
                "ref": key,
                "corr": eng._pairwise_pearson(rel_uw_chg_strat, ref_vec),
            })
    disclosure_table = pd.DataFrame(disclosure_rows)
    disclosure_table.to_csv(OUT / "disclosure_check.csv", index=False)

    summary = {"round_id": "round_656_build", "stage": "S54_category_relative_geometry_chg", "as_of": eng.AS_OF, "new_source": NEW_SOURCE}
    (OUT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(table.to_string(index=False))
    print("\n-- disclosure check (REL_UNDERWATER_CATEGORY_CHG_20, not re-registered) --")
    print(disclosure_table.to_string(index=False))


if __name__ == "__main__":
    main()
