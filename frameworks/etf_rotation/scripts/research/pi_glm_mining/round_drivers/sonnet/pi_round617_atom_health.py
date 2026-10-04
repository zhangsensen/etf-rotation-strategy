#!/usr/bin/env python3
"""Round 617 atom health (S26R2, controller-specified 2026-09-20):
per-atom discovery/audit IC and rank corr vs S26R's R_ atoms and the
original shelf atoms (expect >0.95 but not exactly 1.000 -- these
share more structural similarity with pi's precise definitions than
S26R's paraphrased ones did)."""
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

OUT = eng.WORKSPACE_OUTPUTS / "round_617"
OUT.mkdir(parents=True, exist_ok=True)
NEW_SOURCES = ["repl_volume_core_v2a", "repl_volume_core_v2b"]

PAIR_CHECK = [
    ("R2_VOL_SPIKE_FREQ_20", "repl_volume_core_a", "R_VOL_SPIKE_FREQ_20"),
    ("R2_BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "BIGBAR_DIR_SKEW_20"),
    ("R2_BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "BIGBAR_VOL_SHARE_20"),
    ("R2_VOL_AUTOCORR_20", "repl_volume_core_b", "R_VOL_AUTOCORR_20"),
]
REF_SOURCES = sorted({s for _, s, _ in PAIR_CHECK})
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

    old_ranked = {}
    for ref_source in REF_SOURCES:
        try:
            ref_mining = yaml.safe_load(eng._config_path(ref_source).read_text())
            ref_space = resolve_family(ref_source).builder(
                panels, eligibility_all, eng.CANONICAL_ROOT, ref_mining
            )
        except Exception as exc:  # noqa: BLE001
            print(f"skip reference family {ref_source}: {exc}")
            continue
        for atom_cfg in ref_mining.get("atoms", []):
            name = atom_cfg["name"]
            try:
                ranked = eng.cross_sectional_rank(ref_space[name][symbols], eligibility_all[symbols])
            except Exception:  # noqa: BLE001
                continue
            old_ranked[f"{ref_source}:{name}"] = eng._stride_vector(ranked)

    old_lookup = {new: f"{src}:{old}" for new, src, old in PAIR_CHECK}

    rows = []
    for source in NEW_SOURCES:
        mining = yaml.safe_load(eng._config_path(source).read_text())
        space = resolve_family(source).builder(panels, eligibility_all, eng.CANONICAL_ROOT, mining)
        for atom_cfg in mining.get("atoms", []):
            name = atom_cfg["name"]
            raw = space[name][symbols]
            n_finite = int(np.isfinite(raw.to_numpy(dtype=float)).sum())
            if n_finite == 0:
                rows.append({"source": source, "atom": name, "disc_ic": float("nan"),
                             "disc_days": 0, "audit_ic": float("nan"), "corr_vs_old": float("nan"),
                             "old_key": old_lookup.get(name, "")})
                continue
            ranked = eng.cross_sectional_rank(raw, eligibility_all[symbols])
            disc = _ic_series(ranked.loc[discovery_mask], f5.loc[discovery_mask], eligibility_all[symbols].loc[discovery_mask])
            audit = _ic_series(ranked.loc[audit_mask], f5.loc[audit_mask], eligibility_all[symbols].loc[audit_mask])
            strat = eng._stride_vector(ranked)

            old_key = old_lookup.get(name, "")
            corr_vs_old = float("nan")
            if old_key in old_ranked:
                corr_vs_old = eng._pairwise_pearson(strat, old_ranked[old_key])

            rows.append(
                {
                    "source": source,
                    "atom": name,
                    "disc_ic": float(disc.mean()) if len(disc) else float("nan"),
                    "disc_days": int(len(disc)),
                    "audit_ic": float(audit.mean()) if len(audit) else float("nan"),
                    "corr_vs_old": corr_vs_old,
                    "old_key": old_key,
                    "copied_suspect": bool(np.isfinite(corr_vs_old) and abs(abs(corr_vs_old) - 1.0) < 1e-6),
                }
            )
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "atom_health.csv", index=False)
    summary = {
        "round_id": "round_617_build",
        "stage": "S26R2_repl_volume_core_v2",
        "as_of": eng.AS_OF,
        "new_sources": NEW_SOURCES,
        "copied_suspect": table.loc[table.get("copied_suspect", False) == True, "atom"].tolist() if "copied_suspect" in table else [],
    }
    (OUT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(table.to_string(index=False))
    print("copied_suspect (corr==1.000):", summary["copied_suspect"])


if __name__ == "__main__":
    main()
