#!/usr/bin/env python3
"""Round 625 atom health (S29, controller-specified 2026-09-21): 6 new
mechanism atoms in mechanism_atoms_v2, checked against the source
pairings' legs they are inspired by (MFI_EXTREME_FRAC_20, UNDERWATER_*,
YZ_OVERNIGHT_SHARE_20, LUNCH_POST_RUN_20, BEST_DAY_20, VT_BUCKET_COUNT_20)
for corr -- expected meaningfully different since these are new
self-contained constructs, not rebuilds of the same atoms."""
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

OUT = eng.WORKSPACE_OUTPUTS / "round_625"
OUT.mkdir(parents=True, exist_ok=True)
NEW_SOURCE = "mechanism_atoms_v2"

REF_CHECK = [
    ("MFI_EXTREME_UNDERWATER_SKEW_20", "accumulation_distribution_1m", "MFI_EXTREME_FRAC_20"),
    ("MFI_EXTREME_FWD5_RET_20", "accumulation_distribution_1m", "MFI_EXTREME_FRAC_20"),
    ("ON_UNDERWATER_SPLIT_20", "intraday_drawdown_1m", "UNDERWATER_FRAC_20"),
    ("REL_UNDERWATER_CATEGORY_20", "intraday_drawdown_1m", "UNDERWATER_FRAC_20"),
    ("PM_FRONTRUN_RET_CONSIST_20", "lunch_break_1m", "LUNCH_POST_RUN_20"),
    ("BESTDAY_BUCKET_COUNT_RATIO_20", "volume_time_1m", "VT_BUCKET_COUNT_20"),
]
REF_SOURCES = sorted({s for _, s, _ in REF_CHECK})
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
    for ref_source in REF_SOURCES:
        try:
            ref_mining = yaml.safe_load(eng._config_path(ref_source).read_text())
            ref_space = resolve_family(ref_source).builder(panels, eligibility_all, eng.CANONICAL_ROOT, ref_mining)
        except Exception as exc:  # noqa: BLE001
            print(f"skip reference family {ref_source}: {exc}")
            continue
        for atom_cfg in ref_mining.get("atoms", []):
            name = atom_cfg["name"]
            try:
                ranked = eng.cross_sectional_rank(ref_space[name][symbols], eligibility_all[symbols])
            except Exception:  # noqa: BLE001
                continue
            ref_ranked[f"{ref_source}:{name}"] = eng._stride_vector(ranked)

    ref_lookup = {new: f"{src}:{old}" for new, src, old in REF_CHECK}

    mining = yaml.safe_load(eng._config_path(NEW_SOURCE).read_text())
    space = resolve_family(NEW_SOURCE).builder(panels, eligibility_all, eng.CANONICAL_ROOT, mining)

    rows = []
    for atom_cfg in mining.get("atoms", []):
        name = atom_cfg["name"]
        raw = space[name][symbols]
        n_finite = int(np.isfinite(raw.to_numpy(dtype=float)).sum())
        if n_finite == 0:
            rows.append({"atom": name, "disc_ic": float("nan"), "disc_days": 0,
                         "audit_ic": float("nan"), "n_finite": 0, "corr_vs_ref": float("nan"),
                         "ref_key": ref_lookup.get(name, "")})
            continue
        ranked = eng.cross_sectional_rank(raw, eligibility_all[symbols])
        disc = _ic_series(ranked.loc[discovery_mask], f5.loc[discovery_mask], eligibility_all[symbols].loc[discovery_mask])
        audit = _ic_series(ranked.loc[audit_mask], f5.loc[audit_mask], eligibility_all[symbols].loc[audit_mask])
        strat = eng._stride_vector(ranked)

        ref_key = ref_lookup.get(name, "")
        corr_vs_ref = float("nan")
        if ref_key in ref_ranked:
            corr_vs_ref = eng._pairwise_pearson(strat, ref_ranked[ref_key])

        rows.append(
            {
                "atom": name,
                "disc_ic": float(disc.mean()) if len(disc) else float("nan"),
                "disc_days": int(len(disc)),
                "audit_ic": float(audit.mean()) if len(audit) else float("nan"),
                "n_finite": n_finite,
                "corr_vs_ref": corr_vs_ref,
                "ref_key": ref_key,
            }
        )
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "atom_health.csv", index=False)
    summary = {"round_id": "round_625_build", "stage": "S29_mechanism_atoms_v2", "as_of": eng.AS_OF, "new_source": NEW_SOURCE}
    (OUT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
