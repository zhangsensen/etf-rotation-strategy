#!/usr/bin/env python3
"""Round 618 atom health (S28, controller-specified 2026-09-20): sanity
check on the 2 new atoms (S28_PRICE_POSITION_20, S28_VOV_HAR_RESID_20)
before plan-lock. The other 4 legs used by S28's 6 reproduction pairs
(LUNCH_GAP_20/LUNCH_POST_RUN_20, R_ULCER_20/R_LOG_AMOUNT_VOL_20,
VT_BUCKET_GINI_20, PD_D1_CHG_20, PV_ELASTICITY_20) were already
atom-health-checked and gate-7-tested in their originating rounds
(round_5xx S22/S24/S26R/S14); not re-checked here."""
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

OUT = eng.WORKSPACE_OUTPUTS / "round_618"
OUT.mkdir(parents=True, exist_ok=True)
NEW_SOURCE = "pi_repl_s28"
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

    rows = []
    for atom_cfg in mining.get("atoms", []):
        name = atom_cfg["name"]
        raw = space[name][symbols]
        n_finite = int(np.isfinite(raw.to_numpy(dtype=float)).sum())
        if n_finite == 0:
            rows.append({"source": NEW_SOURCE, "atom": name, "disc_ic": float("nan"),
                         "disc_days": 0, "audit_ic": float("nan"), "n_finite": 0})
            continue
        ranked = eng.cross_sectional_rank(raw, eligibility_all[symbols])
        disc = _ic_series(ranked.loc[discovery_mask], f5.loc[discovery_mask], eligibility_all[symbols].loc[discovery_mask])
        audit = _ic_series(ranked.loc[audit_mask], f5.loc[audit_mask], eligibility_all[symbols].loc[audit_mask])
        rows.append(
            {
                "source": NEW_SOURCE,
                "atom": name,
                "disc_ic": float(disc.mean()) if len(disc) else float("nan"),
                "disc_days": int(len(disc)),
                "audit_ic": float(audit.mean()) if len(audit) else float("nan"),
                "n_finite": n_finite,
            }
        )
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "atom_health.csv", index=False)
    summary = {"round_id": "round_618_build", "stage": "S28_pi_repl_third_batch", "as_of": eng.AS_OF, "new_sources": [NEW_SOURCE]}
    (OUT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
