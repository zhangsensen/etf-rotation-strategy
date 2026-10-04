#!/usr/bin/env python3
"""Append all three frozen USDCNH round-7 results to the prior local full inventory input."""
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

BASE = ROOT / "runtime_outputs/etf_rotation_research/ext_crude_merged_551"
NEW = ROOT / "runtime_outputs/etf_rotation_research/runs/group_ic_campaign20_r07_ext_cnh_20260926"
PRE = ROOT / "runtime_outputs/etf_rotation_research/preflight_ext_cnh_r07_draft_20260926"
CONFIG = ETF / "configs/group_ic_campaign20_r07_ext_cnh_20260926.yaml"
CONFIG_SHA = "decc9653c9814460f10fb79c9c4184a74b63465492b4b05accd56773c0eeae59"


def append_rows(old: pd.DataFrame, current: pd.DataFrame, annual: pd.DataFrame,
                cfg: dict) -> pd.DataFrame:
    ids = rules.candidate_ids(cfg)
    if len(current) != 3 or set(current.candidate) != set(ids):
        raise ValueError("frozen three-candidate result missing")
    if old.definition_id.duplicated().any():
        raise ValueError("prior summary contains duplicate semantic IDs")
    additions = []
    for row in current.to_dict("records"):
        name = row["candidate"]
        years = annual[annual.candidate.eq(name)].set_index("year")
        if set(years.index) != {2025, 2026}:
            raise ValueError(f"annual evidence missing: {name}")
        mapped = {"definition_id": semantic_id(cfg, name), "candidate": name,
                  "source_run": NEW.name, "evidence_policy": "PRIOR_DIRECTION_FULL_WINDOW",
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
                  "import_source_summary": str(NEW / "summary.csv")}
        for year in (2025, 2026):
            for field in ("n", "ic_mean", "ic_hac_t", "ic_block_t", "ic_blocks",
                          "ic_p_normal_one_sided"):
                mapped[f"y{year}_{field}"] = years.loc[year, field]
        additions.append(mapped)
    new = pd.DataFrame(additions)
    if set(new.definition_id) & set(old.definition_id):
        raise ValueError("new USDCNH definitions already in prior summary")
    return pd.concat([old, new], ignore_index=True).reindex(columns=list(old.columns))


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    if sha256(CONFIG.read_bytes()).hexdigest() != CONFIG_SHA:
        raise ValueError("approved config changed")
    old = pd.read_csv(BASE / "summary.csv")
    current = pd.read_csv(NEW / "summary.csv")
    annual = pd.read_csv(NEW / "yearly.csv")
    plan = json.loads((NEW / "PLAN.json").read_text())
    check = json.loads((NEW / "independent_check.json").read_text())
    preflight = json.loads((PRE / "manifest.json").read_text())
    cfg = plan["config"]
    n_by_candidate = current.set_index("candidate")["n"].to_dict()
    if (plan["cumulative_registered_definitions"] != 554 or
            check["status"] != "INDEPENDENT_RECOMPUTATION_MATCHES" or
            set(check["results"]) != set(rules.candidate_ids(cfg)) or
            check["group_label_max_abs_diff"] > 1e-12 or
            any(item["n"] != int(n_by_candidate[name]) or item["max_daily_ic_abs_diff"] > 1e-12 or
                not item["timing_order_on_valid_ic_dates"]
                for name, item in check["results"].items()) or
            preflight["config_sha256"] != CONFIG_SHA):
        raise ValueError("formal budget/prelabel/independent check incomplete")
    merged = append_rows(old, current, annual, cfg)
    output.mkdir(parents=True, exist_ok=False)
    merged.to_csv(output / "summary.csv", index=False)
    verdict = {"conditionally_registered_definitions": 554,
               "prior_complete_summary_rows": len(old), "new_ext_cnh_results": 3,
               "new_ids": rules.candidate_ids(cfg),
               "independent_daily_ic_recomputation_matches": True,
               "independent_group_labels_match": True,
               "prelabel_nearest_old": preflight["nearest_old"]}
    (output / "verdict.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n")
    sources = [BASE / "summary.csv", NEW / "summary.csv", NEW / "yearly.csv",
               NEW / "PLAN.json", NEW / "independent_check.json",
               PRE / "manifest.json", CONFIG, Path(__file__)]
    manifest = {"status": "LOCAL_INVENTORY_MERGE_NO_NEW_H5_EVALUATION",
                "prior_rows": len(old), "added_rows": 3, "total_rows": len(merged),
                "source_sha256": {str(path): sha256(path.read_bytes()).hexdigest() for path in sources},
                "command": [sys.executable, *sys.argv]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return {"output": str(output), "rows": len(merged), "registered": 554}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
