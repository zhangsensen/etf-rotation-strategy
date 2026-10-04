#!/usr/bin/env python3
"""No-H5-label VIX source, timing, coverage and full old-score redundancy check."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as discovery
from etf_strategy.core import etf_group_us_vix as vix_mod
from etf_strategy.core.etf_rank_utils import stable_rank
from preflight_sox_specific_r01 import old_score_prefix

CONFIG = ETF / "configs/group_ic_campaign20_r02_vix_risk_20260926.yaml"
DATA = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
INVENTORY = ROOT / "runtime_outputs/etf_rotation_research/ic_inventory_20260926_536_r01/all_factors.csv"
RUNS = ROOT / "runtime_outputs/etf_rotation_research/runs"


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    cfg = yaml.safe_load(CONFIG.read_text())
    if (cfg["status"] != "PROPOSED_NOT_APPROVED_NO_H5_LABELS_READ" or
            cfg["prior_registered"] != 536 or cfg["new_definitions"] != 3 or
            cfg["as_of"] != "2026-03-24" or cfg["windows"] != [60] or
            set(cfg["mechanisms"]) != {name.removesuffix("_60") for name in vix_mod.MECHANISMS}):
        raise ValueError("R2 prelabel scope changed")
    cutoff = pd.Timestamp(cfg["as_of"])
    universe_path = ROOT / cfg["universe"]
    universe = json.loads(universe_path.read_text())
    symbols = [row["ts_code"] for row in universe["etfs"] if row["role"] == "candidate"]
    groups = yaml.safe_load((ROOT / cfg["groups"]).read_text())["groups"]
    discovery.validate_groups(groups, symbols)
    if set(symbols) != vix_mod.CANDIDATES:
        raise ValueError("candidate population changed")
    source_path = ROOT / cfg["vix_file"]
    vix = vix_mod.read_vix(source_path, cfg["vix_sha256"], cutoff)
    calendar_frame = pd.read_parquet(DATA / "1d/510300.SH.parquet", columns=["trade_date"],
                                     filters=[("trade_date", "<=", cutoff)])
    calendar = pd.DatetimeIndex(calendar_frame.trade_date).sort_values()
    calendar = calendar[(calendar >= pd.Timestamp(cfg["start"])) & (calendar <= cutoff)]
    shock = vix_mod.align_vix_shock(vix, calendar)
    panels = load_canonical_daily(DATA, universe_path, as_of=cfg["as_of"], roles=("candidate",))
    close = panels["close"].reindex(calendar)
    atoms = vix_mod.score_atoms(close, shock)

    prefix_cut = pd.Timestamp("2024-12-31")
    prefix_calendar = calendar[calendar <= prefix_cut]
    prefix_shock = vix_mod.align_vix_shock(vix.loc[:prefix_cut], prefix_calendar)
    pd.testing.assert_series_equal(shock.loc[:prefix_cut], prefix_shock)
    prefix_panels = load_canonical_daily(DATA, universe_path, as_of=str(prefix_cut.date()),
                                         roles=("candidate",))
    prefix_close = prefix_panels["close"].reindex(prefix_calendar)
    pd.testing.assert_frame_equal(close.loc[:prefix_cut].pct_change(fill_method=None),
                                  prefix_close.pct_change(fill_method=None),
                                  rtol=1e-10, atol=1e-12)
    prefix_atoms = vix_mod.score_atoms(prefix_close, prefix_shock)
    perturbed_close, perturbed_shock = close.copy(), shock.copy()
    perturbed_close.loc[perturbed_close.index > prefix_cut] *= 1.73
    perturbed_shock.loc[perturbed_shock.index > prefix_cut] *= 2.41
    perturbed_atoms = vix_mod.score_atoms(perturbed_close, perturbed_shock)
    for name, atom in atoms.items():
        pd.testing.assert_frame_equal(atom.loc[:prefix_cut], prefix_atoms[name],
                                      rtol=1e-10, atol=1e-12)
        pd.testing.assert_frame_equal(atom.loc[:prefix_cut], perturbed_atoms[name].loc[:prefix_cut],
                                      rtol=1e-10, atol=1e-12)

    evaluation = pd.Timestamp(cfg["evaluation_start"])
    scores = {name: discovery.aggregate(atom, groups).loc[evaluation:, list(groups)]
              for name, atom in atoms.items()}
    coverage = {}
    for name, score in scores.items():
        complete = score.notna().all(axis=1)
        dates = score.index[complete]
        coverage[name] = {"complete_eight_group_score_dates": len(dates),
                          "first_complete": str(dates.min().date()) if len(dates) else None,
                          "last_complete": str(dates.max().date()) if len(dates) else None}
    if any(row["complete_eight_group_score_dates"] == 0 for row in coverage.values()):
        raise ValueError("structural zero-rankable definition")

    inventory = pd.read_csv(INVENTORY)
    pairs, skipped = [], []
    for row in inventory.to_dict("records"):
        path = RUNS / str(row["source_run"]) / f"scores_{row['candidate']}.csv"
        if not path.exists():
            skipped.append({"candidate": row["candidate"], "reason": "SAVED_SCORE_MISSING"})
            continue
        try:
            old = old_score_prefix(path, cutoff)
            if set(old.columns) != set(groups):
                raise ValueError("old score not eight-group")
            old = old[list(groups)]
            for name, score in scores.items():
                dates = score.index.intersection(old.index)
                left, right = score.loc[dates], old.loc[dates]
                usable = left.notna().all(axis=1) & right.notna().all(axis=1)
                if not usable.any():
                    continue
                daily = stable_rank(left.loc[usable]).corrwith(stable_rank(right.loc[usable]), axis=1).dropna()
                if len(daily):
                    pairs.append({"new_candidate": name, "old_candidate": row["candidate"],
                                  "old_family": row["family"], "n": len(daily),
                                  "mean_abs_daily_rank_corr": float(daily.abs().mean()),
                                  "mean_signed_daily_rank_corr": float(daily.mean())})
        except (KeyError, ValueError, IndexError) as exc:
            skipped.append({"candidate": row["candidate"],
                            "reason": f"{type(exc).__name__}: {str(exc)[:100]}"})
    table = pd.DataFrame(pairs).sort_values(["new_candidate", "mean_abs_daily_rank_corr"],
                                            ascending=[True, False])
    within = []
    names = list(scores)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            complete = scores[a].notna().all(axis=1) & scores[b].notna().all(axis=1)
            daily = stable_rank(scores[a].loc[complete]).corrwith(
                stable_rank(scores[b].loc[complete]), axis=1).dropna()
            within.append({"left": a, "right": b, "n": len(daily),
                           "mean_abs_daily_rank_corr": float(daily.abs().mean())})
    nearest = {name: table[table.new_candidate.eq(name)].head(3).to_dict("records")
               for name in scores}
    output.mkdir(parents=True, exist_ok=False)
    table.to_csv(output / "old_catalog_correlations.csv", index=False)
    pd.DataFrame(within).to_csv(output / "within_round_correlations.csv", index=False)
    for name, score in scores.items():
        score.to_csv(output / f"scores_{name}.csv", index_label="signal_date")
    valid = vix.dropna().index
    known = pd.merge_asof(pd.DataFrame({"china_date": calendar}),
                          pd.DataFrame({"us_date": valid}), left_on="china_date", right_on="us_date",
                          direction="backward", allow_exact_matches=False)
    ages = (known.china_date - known.us_date).dt.days
    source_files = [source_path, CONFIG, Path(vix_mod.__file__), Path(__file__), INVENTORY,
                    universe_path, ROOT / cfg["groups"]]
    manifest = {"status": "PROPOSED_PRELABEL_NO_H5_LABELS_READ",
                "config_sha256": sha256(CONFIG.read_bytes()).hexdigest(),
                "as_of": cfg["as_of"], "coverage": coverage,
                "foreign_age_max_calendar_days": int(ages.max()),
                "nearest_old": nearest, "within_round": within,
                "old_catalog_definitions": len(inventory), "old_comparison_rows": len(pairs),
                "old_score_skips": skipped,
                "canonical_prefix_returns_and_future_perturbation": True,
                "filtered_input_sha256": {
                    "candidate_adjusted_close": sha256(close.to_csv(float_format="%.17g").encode()).hexdigest(),
                    "aligned_vix_shock": sha256(shock.to_csv(float_format="%.17g").encode()).hexdigest()},
                "source_sha256": {str(path): sha256(path.read_bytes()).hexdigest() for path in source_files},
                "command": [sys.executable, *sys.argv]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False,
                                                    indent=2, allow_nan=False) + "\n")
    return {"output": str(output), "config_sha256": manifest["config_sha256"],
            "coverage": coverage, "nearest_old": nearest, "within_round": within,
            "old_comparison_rows": len(pairs), "old_score_skips": len(skipped)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
