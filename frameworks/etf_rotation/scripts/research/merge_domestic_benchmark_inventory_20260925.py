#!/usr/bin/env python3
"""Append the two frozen cold-window results to the prior local full summary."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from etf_strategy.core import etf_group_run_rules as rules
from build_ic_inventory import semantic_id

BASE = ROOT / "runtime_outputs/etf_rotation_research/us_index_merged_531"
NEW = ROOT / "runtime_outputs/etf_rotation_research/runs/group_ic_cn_benchmark_aux_20260925"
PREFLIGHT = ROOT / "runtime_outputs/etf_rotation_research/preflight_domestic_benchmark_20260925"
CONFIG_SHA256 = "54a8bcd0534cc1263ae9e6d1875ec2ee8d6d58c806882e737b18d07af199b926"


def append_rows(old: pd.DataFrame, current: pd.DataFrame, annual: pd.DataFrame,
                config: dict, run: Path) -> pd.DataFrame:
    if len(current) != 2 or set(current.candidate) != set(rules.candidate_ids(config)):
        raise ValueError("frozen two-candidate result missing")
    if old.definition_id.duplicated().any():
        raise ValueError("prior summary has duplicate semantic IDs")
    additions = []
    for row in current.to_dict("records"):
        name = row["candidate"]
        years = annual[annual.candidate.eq(name)].set_index("year")
        if set(years.index) != {2025, 2026}:
            raise ValueError(f"annual evidence missing: {name}")
        mapped = {"definition_id": semantic_id(config, name), "candidate": name,
                  "source_run": run.name, "evidence_policy": "PRIOR_DIRECTION_FULL_WINDOW",
                  "source_label_artifact_matches": True,
                  "data_quality_status": "CLEAN_FOR_CURRENT_REJUDGE",
                  "full_n": row["n"], "full_ic_mean": row["ic_mean"],
                  "full_ic_hac_t": row["ic_hac_t"], "full_ic_block_t": row["ic_block_t"],
                  "full_ic_blocks": row["ic_blocks"],
                  "full_ic_p_normal_one_sided": row["ic_p_normal_one_sided"],
                  "full_min_loso_ic": row["min_leave_group_ic"],
                  "y2026_min_loso_ic": row["historical_2026_min_leave_group_ic"],
                  "historical_metrics_pass": bool(row["historical_ic_supported"]),
                  "historical_2026_metrics_pass": bool(row["historical_2026_metrics_pass"]),
                  "paired_required": False, "paired_increment_pass": True,
                  "factor_evidence_pass": bool(row["factor_evidence_supported"]),
                  "conditional_budget_pass": bool(row["ic_budget_supported"]),
                  "import_source_summary": str(run / "summary.csv")}
        for year in (2025, 2026):
            for field in ("n", "ic_mean", "ic_hac_t", "ic_block_t", "ic_blocks",
                          "ic_p_normal_one_sided"):
                mapped[f"y{year}_{field}"] = years.loc[year, field]
        additions.append(mapped)
    new = pd.DataFrame(additions)
    if set(new.definition_id) & set(old.definition_id):
        raise ValueError("new definitions already in prior summary")
    return pd.concat([old, new], ignore_index=True).reindex(columns=list(old.columns))


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    old = pd.read_csv(BASE / "summary.csv")
    current = pd.read_csv(NEW / "summary.csv")
    annual = pd.read_csv(NEW / "yearly.csv")
    plan = json.loads((NEW / "PLAN.json").read_text())
    check = json.loads((NEW / "independent_check.json").read_text())
    preflight = json.loads((PREFLIGHT / "manifest.json").read_text())
    cfg = plan["config"]
    config_path = ROOT / "frameworks/etf_rotation/configs/group_ic_cn_benchmark_aux_20260925.yaml"
    if sha256(config_path.read_bytes()).hexdigest() != CONFIG_SHA256:
        raise ValueError("frozen config changed")
    if (plan["cumulative_registered_definitions"] != 533 or
            len(check["results"]) != 2 or check["group_label_mismatch_dates"] or
            set(preflight["redundant_names"]) != set(rules.candidate_ids(cfg)) or
            any(item["ic_row_presence_mismatch"] or
                item["max_daily_ic_abs_diff"] > 1e-12 or
                not item["timing_order_on_valid_ic_dates"] for item in check["results"])):
        raise ValueError("independent timing, IC or redundant-status check incomplete")
    merged = append_rows(old, current, annual, cfg, NEW)
    output.mkdir(parents=True, exist_ok=False)
    merged.to_csv(output / "summary.csv", index=False)
    verdict = {"conditionally_registered_definitions": 533,
               "prior_complete_summary_rows": len(old),
               "new_domestic_benchmark_results": 2,
               "new_ids": rules.candidate_ids(cfg),
               "prelabel_redundant_names": preflight["redundant_names"],
               "independent_daily_ic_recomputation_matches": True,
               "independent_group_labels_match": True}
    (output / "verdict.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n")
    sources = [BASE / "summary.csv", NEW / "summary.csv", NEW / "yearly.csv",
               NEW / "PLAN.json", NEW / "independent_check.json",
               PREFLIGHT / "manifest.json", config_path, Path(__file__)]
    manifest = {"status": "LOCAL_INVENTORY_MERGE_NO_NEW_H5_EVALUATION",
                "prior_rows": len(old), "added_rows": 2, "total_rows": len(merged),
                "source_sha256": {str(path): sha256(path.read_bytes()).hexdigest() for path in sources},
                "command": [sys.executable, *sys.argv]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return {"output": str(output), "rows": len(merged), "registered": 533}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
