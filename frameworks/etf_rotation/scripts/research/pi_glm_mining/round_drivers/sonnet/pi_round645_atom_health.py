#!/usr/bin/env python3
"""Round 645 atom health (S45, controller-specified 2026-09-21): 5 new
repl_overnight_core_v2 atoms (reproduction of pi's overnight_structure_1d
family with pi's precise code-level definition, R2_ prefix). Small-
sample pilot (3 symbols) ran 3.88s; full 14-symbol run extrapolated
~18s, well under the 10-minute threshold -- ran directly."""
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

OUT = eng.WORKSPACE_OUTPUTS / "round_645"
OUT.mkdir(parents=True, exist_ok=True)
NEW_SOURCES = ["repl_overnight_core_v2a", "repl_overnight_core_v2b"]

REF_CHECK = [
    ("R2_BIGBAR_EDGE_CONC_20", "overnight_intraday_mismatch_v1", "GAP_DD_CONSUMPTION_RATIO_20"),
    ("R2_ON_PREM_20", "overnight_structure_1d", "ON_PREM_20"),
    ("R2_GAP_FILL_RATE_20", "overnight_intraday_mismatch_v1", "ON_TROUGH_RECOVERY_MATCH_20"),
    ("R2_OPEN30_VOL_SHARE_20", "gap_absorption_path_1m", "GAP_REMAIN_10AM_20"),
    ("R2_PRICE_POSITION_20", "overnight_structure_1d", "ON_PREM_20"),
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

    rows = []
    for new_source in NEW_SOURCES:
        mining = yaml.safe_load(eng._config_path(new_source).read_text())
        space = resolve_family(new_source).builder(panels, eligibility_all, eng.CANONICAL_ROOT, mining)
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
    summary = {"round_id": "round_645_build", "stage": "S45_repl_overnight_core_v2", "as_of": eng.AS_OF, "new_sources": NEW_SOURCES}
    (OUT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
