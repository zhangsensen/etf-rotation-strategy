#!/usr/bin/env python3
"""Round 612 atom health (S26 corrected, controller-specified 2026-09-20
23:35): per-atom discovery/audit IC AND rank corr vs the pre-existing
shelf atoms of the same underlying concept (VOL_SPIKE_FREQ_20,
BIGBAR_VOL_SHARE_20, BIGBAR_DIR_SKEW_20, VOL_AUTOCORR_20,
LOG_AMOUNT_VOL_20, ULCER_20, GAP_FILL_FRACTION_60). Controller's
explicit check: corr should be close to but NOT exactly 1.000 -- a
value of exactly 1.000 would indicate the implementation was copied
rather than independently rewritten."""
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

OUT = eng.WORKSPACE_OUTPUTS / "round_612"
OUT.mkdir(parents=True, exist_ok=True)
NEW_SOURCES = ["repl_volume_core_v1"]

# (new atom, old shelf source, old atom name)
PAIR_CHECK = [
    ("R_VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", "VOL_SPIKE_FREQ_20"),
    ("R_BIGBAR_VOL_SHARE_20", "bar_size_order_flow", "BIGBAR_VOL_SHARE_20"),
    ("R_BIGBAR_DIR_SKEW_20", "bar_size_order_flow", "BIGBAR_DIR_SKEW_20"),
    ("R_VOL_AUTOCORR_20", "intraday_volume_profile_1m", "VOL_AUTOCORR_20"),
    ("R_LOG_AMOUNT_VOL_20", "liquidity_variability", "LOG_AMOUNT_VOL_20"),
    ("R_ULCER_20", "ohlcv", "ULCER_20"),
    ("R_GAP_FILL_FRACTION_60", "gap_repair", "GAP_FILL_FRACTION_60"),
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

    # build old-atom rank vectors for the pairwise corr check
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

    mining = yaml.safe_load(eng._config_path("repl_volume_core_v1").read_text())
    space = resolve_family("repl_volume_core_v1").builder(
        panels, eligibility_all, eng.CANONICAL_ROOT, mining
    )

    old_lookup = {new: f"{src}:{old}" for new, src, old in PAIR_CHECK}

    rows = []
    for atom_cfg in mining.get("atoms", []):
        name = atom_cfg["name"]
        raw = space[name][symbols]
        n_finite = int(np.isfinite(raw.to_numpy(dtype=float)).sum())
        if n_finite == 0:
            rows.append({"source": "repl_volume_core_v1", "atom": name, "disc_ic": float("nan"),
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
                "source": "repl_volume_core_v1",
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
        "round_id": "round_612_build",
        "stage": "S26_repl_volume_core_v1_corrected",
        "as_of": eng.AS_OF,
        "new_sources": NEW_SOURCES,
        "copied_suspect": table.loc[table.get("copied_suspect", False) == True, "atom"].tolist() if "copied_suspect" in table else [],
    }
    (OUT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(table.to_string(index=False))
    print("copied_suspect (corr==1.000):", summary["copied_suspect"])


if __name__ == "__main__":
    main()
