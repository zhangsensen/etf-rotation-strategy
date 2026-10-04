#!/usr/bin/env python3
"""Round 569 atom health (S14 stage, cross-lane replication): per-atom
discovery/audit IC for the new pi_replication_s14 family, plus the two
directly-reused existing atoms (daily_candle:GAP_MEAN_20 as ON_PREM_20,
bar_size_order_flow:CLOSE5_DAY_CONSIST_20 as-is)."""
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

OUT = eng.WORKSPACE_OUTPUTS / "round_569"
OUT.mkdir(parents=True, exist_ok=True)
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

    sources = {
        "pi_price_delay_1d": ["PD_D1_CHG_20"],
        "pi_auc_variance_ratio_1m": ["AUC_VARIANCE_RATIO_20"],
        "pi_pv_elasticity_1m": ["PV_ELASTICITY_20"],
        "pi_edge_bigbar_volshare_1m": ["EDGE_BIGBAR_VOLSHARE_20"],
        "pi_lunch_prerun_1m": ["LUNCH_PRE_RUN_20"],
        "daily_candle": ["GAP_MEAN_20"],
        "bar_size_order_flow": ["CLOSE5_DAY_CONSIST_20"],
    }
    rows = []
    for source, names in sources.items():
        mining = yaml.safe_load(eng._config_path(source).read_text())
        space = resolve_family(source).builder(panels, eligibility_all, eng.CANONICAL_ROOT, mining)
        for name in names:
            raw = space[name][symbols]
            n_finite = int(np.isfinite(raw.to_numpy(dtype=float)).sum())
            if n_finite == 0:
                rows.append({"source": source, "atom": name, "disc_ic": float("nan"), "disc_days": 0, "audit_ic": float("nan")})
                continue
            ranked = eng.cross_sectional_rank(raw, eligibility_all[symbols])
            disc = _ic_series(ranked.loc[discovery_mask], f5.loc[discovery_mask], eligibility_all[symbols].loc[discovery_mask])
            audit = _ic_series(ranked.loc[audit_mask], f5.loc[audit_mask], eligibility_all[symbols].loc[audit_mask])
            rows.append(
                {
                    "source": source,
                    "atom": name,
                    "disc_ic": float(disc.mean()) if len(disc) else float("nan"),
                    "disc_days": int(len(disc)),
                    "audit_ic": float(audit.mean()) if len(audit) else float("nan"),
                }
            )
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "atom_health.csv", index=False)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
