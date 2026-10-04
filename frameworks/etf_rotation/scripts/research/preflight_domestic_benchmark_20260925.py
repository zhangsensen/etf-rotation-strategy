#!/usr/bin/env python3
"""Cold-cutoff, no-label coverage and old-score comparison for two frozen factors."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as discovery
from etf_strategy.core import etf_group_domestic_benchmark as domestic
from etf_strategy.core.etf_rank_utils import stable_rank
import audit_saved_etf_ic_history as audit

CONFIG = ETF / "configs/group_ic_cn_benchmark_aux_20260925.yaml"
CONFIG_SHA256 = "54a8bcd0534cc1263ae9e6d1875ec2ee8d6d58c806882e737b18d07af199b926"
DATA_ROOT = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
INVENTORY = ROOT / "runtime_outputs/etf_rotation_research/ic_inventory_20260925_531_v1/all_factors.csv"
RUNS = ROOT / "runtime_outputs/etf_rotation_research/runs"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _filtered_sha(frame: pd.DataFrame) -> str:
    return sha256(frame.to_csv(index=True, float_format="%.17g", na_rep="NA",
                               date_format="%Y-%m-%dT%H:%M:%S").encode()).hexdigest()


def _saved_score(path: Path, cutoff: pd.Timestamp, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """Read at most pre-cutoff rows of a saved score, never later score rows."""
    with path.open() as handle:
        header = handle.readline().rstrip("\n").split(",")
        first = handle.readline().split(",", 1)[0]
    if len(header) != 9 or first == "":
        raise ValueError(f"unexpected saved score layout: {path}")
    count = int(((calendar >= pd.Timestamp(first)) & (calendar <= cutoff)).sum())
    frame = pd.read_csv(path, nrows=count, index_col=0, parse_dates=True,
                        float_precision="round_trip")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing or frame.index.max() > cutoff:
        raise ValueError(f"saved score crosses cold cutoff: {path}")
    return frame


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    if _sha(CONFIG) != CONFIG_SHA256:
        raise ValueError("frozen candidate spec changed")
    cfg = yaml.safe_load(CONFIG.read_text())
    cutoff = pd.Timestamp(cfg["as_of"])
    if cutoff != pd.Timestamp("2026-03-24"):
        raise ValueError("preflight cold cutoff changed")
    universe = ROOT / cfg["universe"]
    groups_path = ROOT / cfg["groups"]
    groups = yaml.safe_load(groups_path.read_text())["groups"]
    symbols = [row["ts_code"] for row in json.loads(universe.read_text())["etfs"]
               if row["role"] == "candidate"]
    discovery.validate_groups(groups, symbols)
    panels = load_canonical_daily(DATA_ROOT, universe, as_of=cfg["as_of"], roles=("candidate",))
    benchmark = load_canonical_daily(DATA_ROOT, universe, as_of=cfg["as_of"], roles=("benchmark",))
    raw_calendar = pd.read_parquet(DATA_ROOT / "1d/510300.SH.parquet", columns=["trade_date"],
                                   filters=[("trade_date", "<=", cutoff)])
    calendar = pd.DatetimeIndex(pd.to_datetime(raw_calendar.trade_date)).sort_values()
    calendar = calendar[(calendar >= pd.Timestamp(cfg["start"])) & (calendar <= cutoff)]
    in_scope = panels["close"].index[panels["close"].index >= pd.Timestamp(cfg["start"])]
    if calendar.max() != cutoff or len(in_scope.difference(calendar)):
        raise ValueError("preflight calendar mismatch")
    feature = {"close": panels["close"].reindex(calendar),
               "benchmark_close": benchmark["close"][cfg["auxiliary_symbols"]].reindex(calendar)}
    atoms = domestic.build_atoms(feature, cfg)
    checks = {cut: domestic.leakage_checks(feature, cfg, cut)
              for cut in ("2024-12-31", "2025-12-31")}
    prefix_candidate = load_canonical_daily(DATA_ROOT, universe, as_of="2024-12-31", roles=("candidate",))
    prefix_benchmark = load_canonical_daily(DATA_ROOT, universe, as_of="2024-12-31", roles=("benchmark",))
    prefix_calendar = calendar[calendar <= pd.Timestamp("2024-12-31")]
    prefix_feature = {"close": prefix_candidate["close"].reindex(prefix_calendar),
                      "benchmark_close": prefix_benchmark["close"][cfg["auxiliary_symbols"]].reindex(prefix_calendar)}
    prefix_atoms = domestic.build_atoms(prefix_feature, cfg)
    for name in atoms:
        pd.testing.assert_frame_equal(atoms[name].loc[prefix_calendar], prefix_atoms[name],
                                      check_exact=False, rtol=1e-7, atol=1e-10)
    known = (feature["close"].notna().rolling(60).sum().eq(60).all(axis=1) &
             panels["volume"].reindex(calendar).gt(0).all(axis=1))
    evaluation = calendar[calendar >= pd.Timestamp(cfg["evaluation_start"])]
    scores = {name: discovery.aggregate(atom, groups).reindex(evaluation)[list(groups)]
              for name, atom in atoms.items()}
    coverage = {name: {"rankable_eight_group_days": int((score.notna().all(axis=1) & known.reindex(evaluation)).sum()),
                       "first_score": str(score.dropna().index.min().date()) if score.notna().all(axis=1).any() else None,
                       "last_score": str(score.dropna().index.max().date()) if score.notna().all(axis=1).any() else None}
                for name, score in scores.items()}
    if any(item["rankable_eight_group_days"] == 0 for item in coverage.values()):
        raise ValueError("zero rankable-date structural failure; do not formally evaluate")
    inventory = pd.read_csv(INVENTORY)
    pairs, skipped, read_hashes = [], [], {}
    for row in inventory.to_dict("records"):
        path = RUNS / str(row["source_run"]) / f"scores_{row['candidate']}.csv"
        if not path.exists():
            skipped.append({"candidate": row["candidate"], "reason": "SAVED_SCORE_MISSING"})
            continue
        try:
            old = _saved_score(path, cutoff, calendar)
            if set(old.columns) != set(groups):
                raise ValueError("non-eight-group saved score")
            old = old.reindex(columns=list(groups))
            read_hashes[str(path)] = _filtered_sha(old)
            for name, score in scores.items():
                dates = score.index.intersection(old.index)
                left, right = score.reindex(dates), old.reindex(dates)
                complete = left.notna().all(axis=1) & right.notna().all(axis=1)
                complete &= known.reindex(dates).fillna(False)
                if not complete.any():
                    continue
                correlation = stable_rank(left.loc[complete]).corrwith(
                    stable_rank(right.loc[complete]), axis=1).dropna()
                if not len(correlation):
                    continue
                pairs.append({"new_candidate": name, "old_candidate": row["candidate"],
                              "old_family": row["family"], "old_source_run": row["source_run"],
                              "n": len(correlation), "mean_abs_daily_rank_corr": float(correlation.abs().mean()),
                              "mean_signed_daily_rank_corr": float(correlation.mean()),
                              "redundant_at_0p7": bool(correlation.abs().mean() >= .7)})
        except (ValueError, IndexError, KeyError) as exc:
            skipped.append({"candidate": row["candidate"], "reason": type(exc).__name__ + ":" + str(exc)[:100]})
    pair_table = pd.DataFrame(pairs).sort_values(["new_candidate", "mean_abs_daily_rank_corr"],
                                                    ascending=[True, False])
    nearest = {name: pair_table[pair_table.new_candidate.eq(name)].head(1).to_dict("records")
               for name in scores}
    output.mkdir(parents=True, exist_ok=False)
    pair_table.to_csv(output / "old_catalog_correlations.csv", index=False)
    for name, score in scores.items():
        score.to_csv(output / f"scores_{name}.csv", index_label="signal_date")
    manifest = {"status": "PRELABEL_NO_H5_LABELS_READ", "config_sha256": CONFIG_SHA256,
                "as_of": cfg["as_of"], "population": "fixed14_eight_groups",
                "coverage": coverage, "leakage_checks": checks,
                "canonical_reload_prefix": True, "old_catalog_definitions": len(inventory),
                "old_catalog_comparison_rows": len(pairs), "skipped_old_scores": skipped,
                "nearest": nearest,
                "redundant_names": sorted(pair_table.loc[pair_table.redundant_at_0p7, "new_candidate"].unique()),
                "source_sha256": {str(path): _sha(path) for path in
                                  (Path(__file__), CONFIG, Path(domestic.__file__),
                                   ETF / "src/etf_strategy/canonical_data.py", universe,
                                   groups_path, INVENTORY)},
                "filtered_input_sha256": {**{name: _filtered_sha(frame) for name, frame in feature.items()},
                                          "old_scores": sha256(json.dumps(read_hashes, sort_keys=True).encode()).hexdigest()},
                "command": [sys.executable, *sys.argv]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2,
                                                    allow_nan=False) + "\n")
    return {"output": str(output), "coverage": coverage, "nearest": nearest,
            "redundant_names": manifest["redundant_names"], "old_scores_compared": len(pairs),
            "old_scores_skipped": len(skipped)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
