#!/usr/bin/env python3
"""Round 080 atom health (stage 15 step 1): per-atom discovery/audit IC, max
abs shelf + channel-atom rank-corr, shadow flag at |corr|>=0.70, for the new
coskewness_risk family (Harvey-Siddique / Ang-Chen-Xing / Dittmar)."""
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

OUT = eng.WORKSPACE_OUTPUTS / "round_080"
OUT.mkdir(parents=True, exist_ok=True)
NEW_SOURCES = ["coskewness_risk"]
# Directive: health-check vs shelf16 (via eng._shelf_vectors) plus the
# channel atoms named in the controller directive (largebar/bar-size/volume
# profile) and the two families that share second-moment/tail machinery with
# coskewness (market_sensitivity beta/corr, return_tail_shape own skew,
# downside_risk).
EXTRA_REF_SOURCES = [
    "market_sensitivity",
    "return_tail_shape",
    "downside_risk",
    "bar_size_order_flow",
    "largebar_footprint_1m",
    "intraday_volume_profile_1m",
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
    plan_stub = {"_signal_index": dates}
    shelf = dict(eng._shelf_vectors(symbols, plan_stub))
    for ref_source in EXTRA_REF_SOURCES:
        try:
            ref_mining = yaml.safe_load(eng._config_path(ref_source).read_text())
            ref_space = resolve_family(ref_source).builder(
                panels, eligibility_all, eng.CANONICAL_ROOT, ref_mining
            )
        except Exception as exc:  # noqa: BLE001
            print(f"ref source unavailable: {ref_source}: {exc}")
            continue
        for atom_cfg in ref_mining.get("atoms", []):
            ref_name = atom_cfg["name"]
            try:
                ref_ranked = eng.cross_sectional_rank(
                    ref_space[ref_name][symbols], eligibility_all[symbols]
                )
            except Exception:  # noqa: BLE001
                continue
            shelf[f"{ref_source}:{ref_name}"] = eng._stride_vector(ref_ranked)

    rows = []
    spaces = {}
    for source in NEW_SOURCES:
        mining = yaml.safe_load(eng._config_path(source).read_text())
        spaces[source] = resolve_family(source).builder(
            panels, eligibility_all, eng.CANONICAL_ROOT, mining
        )
        for atom_cfg in mining.get("atoms", []):
            name = atom_cfg["name"]
            ranked = eng.cross_sectional_rank(spaces[source][name][symbols], eligibility_all[symbols])
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
                    "source": source,
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
        "round_id": "round_080_build",
        "stage": "stage15_coskewness_risk",
        "as_of": eng.AS_OF,
        "new_sources": NEW_SOURCES,
        "atom_health_rows": len(table),
        "shadow": sorted(table.loc[table["shadow"], "atom"].tolist()),
        "_note": "daily-only family (no 1m path); no physical PIT truncation spot check "
        "needed beyond the standard cmd_evaluate leak gate (validated via --mode validate).",
    }
    (OUT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(table.to_string(index=False))
    print("shadow (>=0.70):", summary["shadow"])
    print("summary written:", OUT / "build_summary.json")


if __name__ == "__main__":
    main()
