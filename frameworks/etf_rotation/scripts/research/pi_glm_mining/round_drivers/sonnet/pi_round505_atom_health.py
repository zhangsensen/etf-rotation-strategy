#!/usr/bin/env python3
"""Round 505 atom health (S2 stage step 2): per-atom discovery/audit IC and
shelf/channel rank-corr for the 4 new volatility-residualized upside_tail
atoms (BEST_DAY_20_XVOL, BEST_DAY_60_XVOL, MAX5_MEAN_20_XVOL,
INTRADAY_MAXBAR_RET_20_XVOL). round_504 traced the raw atoms' shadow flags
to REALIZED_VOL_60; this checks the residualized versions are non-shadow
against the full shelf16 plus the same reference families used in
round_504 (return_tail_shape, realized_measures_1m) and downside_risk
itself (the orthogonalization target, sanity check should be ~0)."""
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

OUT = eng.WORKSPACE_OUTPUTS / "round_505"
OUT.mkdir(parents=True, exist_ok=True)
NEW_ATOMS = [
    "BEST_DAY_20_XVOL",
    "BEST_DAY_60_XVOL",
    "MAX5_MEAN_20_XVOL",
    "INTRADAY_MAXBAR_RET_20_XVOL",
]
EXTRA_REF_SOURCES = ["return_tail_shape", "realized_measures_1m", "downside_risk"]
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
    plan_stub = {"_signal_index": dates}
    shelf = dict(eng._shelf_vectors(symbols, plan_stub))
    for ref_source in EXTRA_REF_SOURCES:
        ref_mining = yaml.safe_load(eng._config_path(ref_source).read_text())
        ref_space = resolve_family(ref_source).builder(
            panels, eligibility_all, eng.CANONICAL_ROOT, ref_mining
        )
        for atom_cfg in ref_mining.get("atoms", []):
            ref_name = atom_cfg["name"]
            try:
                ref_ranked = eng.cross_sectional_rank(
                    ref_space[ref_name][symbols], eligibility_all[symbols]
                )
            except Exception:  # noqa: BLE001
                continue
            shelf[f"{ref_source}:{ref_name}"] = eng._stride_vector(ref_ranked)

    mining = yaml.safe_load(eng._config_path("upside_tail").read_text())
    space = resolve_family("upside_tail").builder(panels, eligibility_all, eng.CANONICAL_ROOT, mining)

    rows = []
    for name in NEW_ATOMS:
        ranked = eng.cross_sectional_rank(space[name][symbols], eligibility_all[symbols])
        disc = _ic_series(ranked.loc[discovery_mask], f5.loc[discovery_mask], eligibility_all[symbols].loc[discovery_mask])
        audit = _ic_series(ranked.loc[audit_mask], f5.loc[audit_mask], eligibility_all[symbols].loc[audit_mask])
        strat = eng._stride_vector(ranked)
        best_key, best_corr = "", 0.0
        for key, vec in shelf.items():
            corr = eng._pairwise_pearson(strat, vec)
            if np.isfinite(corr) and abs(corr) > abs(best_corr):
                best_key, best_corr = key, corr
        rows.append(
            {
                "source": "upside_tail",
                "atom": name,
                "disc_ic": float(disc.mean()) if len(disc) else float("nan"),
                "disc_days": int(len(disc)),
                "audit_ic": float(audit.mean()) if len(audit) else float("nan"),
                "max_abs_shelf_corr": abs(best_corr) if best_key else float("nan"),
                "max_corr_vs": best_key,
                "shadow": bool(best_key and abs(best_corr) >= 0.70),
            }
        )
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "atom_health.csv", index=False)
    summary = {
        "round_id": "round_505_build",
        "stage": "S2_upside_tail_xvol",
        "as_of": eng.AS_OF,
        "new_atoms": NEW_ATOMS,
        "shadow": sorted(table.loc[table["shadow"], "atom"].tolist()),
    }
    (OUT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(table.to_string(index=False))
    print("shadow (>=0.70):", summary["shadow"])


if __name__ == "__main__":
    main()
