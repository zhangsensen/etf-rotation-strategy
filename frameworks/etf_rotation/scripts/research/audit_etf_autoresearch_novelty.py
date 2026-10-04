#!/usr/bin/env python3
"""Read-only, prelabel score overlap against an existing ETF IC inventory."""
from __future__ import annotations

import argparse
from io import StringIO
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "frameworks/etf_rotation/src"))
from etf_strategy.core.etf_rank_utils import stable_rank

CUTOFF = pd.Timestamp("2026-03-24")


def require_latest_inventory(inventory: Path, runs_root: Path) -> None:
    pointer = runs_root.parent / "IC_INVENTORY_LATEST.json"
    if not pointer.is_file():
        raise ValueError("latest formal inventory pointer is missing")
    latest = json.loads(pointer.read_text())
    snapshot = Path(latest["snapshot"])
    if not inventory.is_file() or inventory.resolve() != (snapshot / "all_factors.csv").resolve():
        raise ValueError("inventory is stale relative to the formal ledger")
    registered = [json.loads(path.read_text()).get("cumulative_registered_definitions")
                  for path in runs_root.glob("*/PLAN.json")]
    registered = [count for count in registered if type(count) is int]
    if not registered or max(registered) != latest.get("registered_budget_count"):
        raise ValueError("inventory count trails or differs from the persistent PLAN ledger")


def read_prefix(path: Path) -> pd.DataFrame:
    """Never load saved score rows after the cold cutoff."""
    with path.open() as handle:
        lines = [handle.readline()]
        for line in handle:
            if pd.Timestamp(line.split(",", 1)[0].strip('"')) > CUTOFF:
                break
            lines.append(line)
    result = pd.read_csv(StringIO("".join(lines)), index_col=0,
                         parse_dates=True, float_precision="round_trip")
    if result.index.has_duplicates or not result.index.is_monotonic_increasing:
        raise ValueError("saved score chronology invalid")
    return result


def audit(run_dir: Path, inventory: Path, runs_root: Path) -> dict:
    new = read_prefix(run_dir / "group_scores.csv")
    catalog = pd.read_csv(inventory)
    records, skipped, not_comparable = [], [], []

    def compare_score(path: Path, candidate: str, family: str, source: str) -> None:
        old = read_prefix(path)
        if set(old.columns) != set(new.columns):
            skipped.append({"candidate": candidate, "source": source, "reason": "GROUPS_DIFFER"})
            return
        old = old[new.columns]
        dates = new.index.intersection(old.index)
        left, right = new.loc[dates], old.loc[dates]
        valid = left.notna().all(axis=1) & right.notna().all(axis=1)
        if valid.sum() < 40:
            not_comparable.append({"candidate": candidate, "source": source,
                                   "common_complete_days": int(valid.sum())})
            return
        daily = stable_rank(left.loc[valid]).corrwith(
            stable_rank(right.loc[valid]), axis=1).dropna()
        if len(daily) < 40:
            not_comparable.append({"candidate": candidate, "source": source,
                                   "common_rankable_days": len(daily)})
            return
        records.append({"candidate": candidate, "family": family, "source": source,
                        "n": len(daily), "mean_abs_daily_rank_corr": float(daily.abs().mean()),
                        "mean_signed_daily_rank_corr": float(daily.mean())})

    for row in catalog.to_dict("records"):
        path = runs_root / str(row["source_run"]) / f"scores_{row['candidate']}.csv"
        if not path.is_file():
            skipped.append({"candidate": row["candidate"], "source": "formal_inventory",
                            "reason": "SCORE_FILE_MISSING"})
            continue
        try:
            compare_score(path, row["candidate"], row["family"], "formal_inventory")
        except (ValueError, IndexError, KeyError):
            skipped.append({"candidate": row["candidate"], "source": "formal_inventory",
                            "reason": "SCORE_READ_FAILED"})
    for path in run_dir.parent.glob("*/group_scores.csv"):
        if path.parent == run_dir:
            continue
        result_path = path.parent / "result.json"
        if not result_path.is_file():
            continue
        prior = json.loads(result_path.read_text())
        try:
            compare_score(path, prior["candidate"], prior["family"], "local_trial")
        except (ValueError, IndexError, KeyError):
            skipped.append({"candidate": prior.get("candidate", path.parent.name),
                            "source": "local_trial", "reason": "SCORE_READ_FAILED"})
    records.sort(key=lambda row: (-row["mean_abs_daily_rank_corr"], row["candidate"]))
    result = {"inventory": str(inventory), "indexed": len(catalog), "compared": len(records),
              "skipped": skipped, "not_comparable": not_comparable,
              "nearest": records[:10],
              "scope": "score overlap only; no IC labels read", "cold_cutoff": str(CUTOFF.date())}
    (run_dir / "novelty.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.run_dir, args.inventory, args.runs_root), ensure_ascii=False))
