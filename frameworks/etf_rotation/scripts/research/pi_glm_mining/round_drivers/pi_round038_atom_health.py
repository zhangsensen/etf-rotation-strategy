#!/usr/bin/env python3
"""Round 035 atom health (stage 6): per-atom discovery/audit IC, max abs
shelf rank-corr (stride rule), shadow flag at |corr|>=0.70, plus a physical
PIT spot check (fund + 1m truncation) for the new-family atoms."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as eng  # noqa: E402
from etf_strategy.core.family_registry import load_builtin_families, resolve_family  # noqa: E402

OUT = eng.WORKSPACE_OUTPUTS / "round_038"
OUT.mkdir(parents=True, exist_ok=True)
NEW_SOURCES = ["realized_measures_1m", "intraday_periodicity"]
# directive: health-check vs the 5m families and daily_candle same-name atoms
EXTRA_REF_SOURCES = ["intraday_return_distribution", "intraday_tail_reversal_jump", "daily_candle"]
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


def _pit_truncated_root(workdir: Path) -> Path:
    root = workdir / "pit_trunc"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for sub in ("fund_share", "nav"):
        out_dir = root / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted((eng.CANONICAL_ROOT / sub).glob("*.parquet")):
            frame = pd.read_parquet(path)
            u = pd.to_datetime(frame["usable_from_date"])
            frame.loc[u <= eng.DISCOVERY_END].to_parquet(out_dir / path.name)
    # 1m: physical truncation of bars after the cutoff (micro atoms read these)
    out_1m = root / "1m"
    out_1m.mkdir(parents=True, exist_ok=True)
    cutoff = eng.DISCOVERY_END + pd.Timedelta(days=1)
    for path in sorted((eng.CANONICAL_ROOT / "1m").glob("*.parquet")):
        frame = pd.read_parquet(path)
        frame.loc[pd.to_datetime(frame["datetime"]) < cutoff].to_parquet(out_1m / path.name)
    return root


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

    # physical PIT spot check: rebuild new-family atoms from a truncated root
    trunc_root = _pit_truncated_root(OUT)
    spot_rows = []
    for source in NEW_SOURCES:
        mining = yaml.safe_load(eng._config_path(source).read_text())
        space_trunc = resolve_family(source).builder(
            panels, eligibility_all, trunc_root, mining
        )
        for atom_cfg in mining.get("atoms", []):
            name = atom_cfg["name"]
            base = eng.cross_sectional_rank(spaces[source][name][symbols], eligibility_all[symbols])
            trunc = eng.cross_sectional_rank(space_trunc[name][symbols], eligibility_all[symbols])
            common = base.index[base.index <= DISCOVERY_END]
            diff = (
                base.loc[common].to_numpy(float) - trunc.loc[common].to_numpy(float)
            )
            finite = np.isfinite(base.loc[common].to_numpy(float))
            max_diff = float(np.nanmax(np.abs(diff)[finite])) if finite.any() else 0.0
            spot_rows.append(
                {
                    "source": source,
                    "atom": name,
                    "prefix_max_abs_diff": max_diff,
                    "pass": bool(max_diff == 0.0),
                }
            )
    spot = pd.DataFrame(spot_rows)
    spot.to_csv(OUT / "pit_leak_spot_check.csv", index=False)

    summary = {
        "round_id": "round_038_build",
        "stage": "stage7_realized_measures_periodicity",
        "as_of": eng.AS_OF,
        "new_sources": NEW_SOURCES,
        "atom_health_rows": len(table),
        "shadow": sorted(table.loc[table["shadow"], "atom"].tolist()),
        "pit_prefix_all_zero": bool(spot["pass"].all()),
        "_pit_note": "已实现测度原子只用 <=D 的 1m bar；LM 跳跃 sigma 只用前一日 bar；1m 截断副本物理重建后前缀逐值一致",
    }
    (OUT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(table.to_string(index=False))
    print("shadow (>=0.70):", summary["shadow"])
    print("PIT leak spot check: all pass =", summary["pit_prefix_all_zero"], f"({len(spot)} atoms)")
    print("summary written:", OUT / "build_summary.json")


if __name__ == "__main__":
    main()
