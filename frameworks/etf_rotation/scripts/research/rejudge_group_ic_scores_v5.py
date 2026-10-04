#!/usr/bin/env python3
"""IC-only zero-definition rejudge of saved fixed14/eight-group candidate scores.

This command never builds a new hypothesis.  It canonicalises saved score ties,
separates 2025 direction discovery from the 2026 historical segment, and recomputes paired
IC increments for explicit interactions and Batch20 event/response composites.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import shutil
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_confirmation as confirmation
from etf_strategy.core import etf_group_daily_rounds as daily_rounds
from etf_strategy.core import etf_group_discovery as discovery
from etf_strategy.core.etf_mining_referee import (
    block_t_calendar,
    newey_west_t_calendar,
    one_sided_normal_pvalue,
)
from etf_strategy.core.etf_rank_utils import stable_rank
from etf_strategy.core.etf_ic_monthly_factory import (
    candidate_halt_window_mask,
    open_halt_dates,
)


GROUP_COLUMNS = [
    "cn_technology_manufacturing", "hk_technology", "us_large_growth",
    "innovative_pharma", "gold", "metals_equity", "dividend_low_vol",
    "electric_power",
]


def data_quality_status(source_type: str, candidate: str) -> str:
    """Return the reviewed source-quality state; affected history fails closed."""
    if source_type == "share":
        return "DEGRADED_513100_SHARE_STAGNATION"
    if source_type == "nav":
        return "DATA_QUALITY_PENDING_NAV_OUTLIERS"
    if candidate in {
        "minute_amount_abs_return_concentration_20",
        "d2025_minute_amount_abs_return_concentration_20",
    }:
        return "HALT_DIAGNOSTIC_REPORTED"
    return "CLEAN_FOR_CURRENT_REJUDGE"


def read_frame(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0, parse_dates=True, float_precision="round_trip")


def semantic_key(plan: dict, candidate: str) -> str:
    cfg = plan["config"]
    if cfg.get("source_type") == "claude_rounds":
        # Per-mechanism window (no shared top-level windows list).
        mechanism = next(
            (m for m, d in cfg.get("mechanisms", {}).items()
             if candidate == f"{m}_{d.get('window')}"),
            None,
        )
        window = cfg["mechanisms"][mechanism]["window"] if mechanism else None
    else:
        window = next((w for w in cfg["windows"] if candidate.endswith(f"_{w}")), cfg["windows"][0])
        mechanism = candidate.removesuffix(f"_{window}")
    definition = cfg["mechanisms"].get(mechanism, {})
    payload = [cfg.get("source_type", "daily"), candidate, window, definition]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]


def daily_ic(score: pd.DataFrame, labels: pd.DataFrame) -> pd.Series:
    score = score[GROUP_COLUMNS]
    labels = labels[GROUP_COLUMNS].reindex(score.index)
    complete = score.notna().all(axis=1) & labels.notna().all(axis=1)
    return stable_rank(score).corrwith(
        labels.rank(axis=1, method="average"), axis=1
    ).where(complete)


def stats(series: pd.Series, calendar: pd.DatetimeIndex) -> dict:
    x = series.reindex(calendar)
    t = newey_west_t_calendar(x, calendar, 10)
    block, blocks = block_t_calendar(x, calendar, 5)
    return {
        "n": int(x.notna().sum()), "ic_mean": float(x.mean()),
        "ic_hac_t": t, "ic_block_t": block, "ic_blocks": blocks,
        "ic_p_normal_one_sided": one_sided_normal_pvalue(t),
    }


def year_slice(series: pd.Series, timing: pd.DataFrame, year: int) -> pd.Series:
    out = series.loc[series.index.year == year].copy()
    exits = pd.to_datetime(timing.reindex(out.index)["exit_date"])
    return out.where(exits.dt.year.eq(year))


def loso_min(score: pd.DataFrame, labels: pd.DataFrame, valid: pd.Series) -> tuple[float, float]:
    full, confirm = [], []
    for group in GROUP_COLUMNS:
        ic = stable_rank(score.drop(columns=group)).corrwith(
            labels.drop(columns=group).rank(axis=1, method="average"), axis=1
        ).where(valid.notna())
        full.append(float(ic.mean()))
        confirm.append(float(ic.loc[ic.index.year == 2026].mean()))
    return min(full), min(confirm)


def paired_stats(candidate_ic: pd.Series, leg_ic: pd.Series, calendar: pd.DatetimeIndex) -> dict:
    delta = candidate_ic.reindex(calendar) - leg_ic.reindex(calendar)
    return {
        "n": int(delta.notna().sum()),
        "mean": float(delta.mean()),
        "hac_t": newey_west_t_calendar(delta, calendar, 10),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", default=str(ROOT / "runtime_outputs/etf_rotation_research/runs"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--conditional-budget", type=int, default=384)
    parser.add_argument(
        "--halt-minute",
        default=str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1/1m/513100.SH.parquet"),
        help="513100 1m parquet used only for the report-only halt-window diagnostic",
    )
    args = parser.parse_args()
    runs_root, output = Path(args.runs_root), Path(args.output)
    if output.exists():
        raise FileExistsError(output)

    artifacts: dict[str, dict] = {}
    for plan_path in sorted(runs_root.glob("*/PLAN.json")):
        plan = json.loads(plan_path.read_text())
        cfg = plan.get("config", {})
        if cfg.get("groups") != "frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml":
            continue
        run = plan_path.parent
        for score_path in sorted(run.glob("scores_*.csv")):
            candidate = score_path.stem.removeprefix("scores_")
            if candidate not in plan.get("evaluated_ids", []):
                continue
            key = semantic_key(plan, candidate)
            created = plan.get("created_utc", "")
            if key not in artifacts or created > artifacts[key]["created"]:
                artifacts[key] = {
                    "key": key, "candidate": candidate, "run": run,
                    "plan": plan, "score_path": score_path, "created": created,
                }
    if not artifacts:
        raise ValueError("no fixed14/eight-group saved scores found")

    reference = max(
        (artifact["run"] for artifact in artifacts.values()),
        key=lambda run: read_frame(run / "group_labels.csv").index.max(),
    )
    labels = read_frame(reference / "group_labels.csv")[GROUP_COLUMNS]
    coverage = pd.read_csv(reference / "coverage.csv", parse_dates=["signal_date", "entry_date", "exit_date"]).set_index("signal_date")
    timed = coverage.entry_date.notna() & coverage.exit_date.notna()
    if not ((coverage.loc[timed, "entry_date"] > coverage.index[timed]) &
            (coverage.loc[timed, "exit_date"] > coverage.loc[timed, "entry_date"])).all():
        raise ValueError("saved timing contract is not signal < entry < exit")
    calendar = labels.index[(labels.index >= pd.Timestamp("2025-01-01")) &
                            (labels.index <= pd.Timestamp("2026-09-17"))]
    labels = labels.reindex(calendar)
    coverage = coverage.reindex(calendar)
    halt_minute = pd.read_parquet(args.halt_minute)
    if "ts_code" in halt_minute and not halt_minute["ts_code"].eq("513100.SH").all():
        raise ValueError("halt diagnostic input must contain only 513100.SH")
    halted_dates = open_halt_dates(halt_minute)

    raw_context = None
    rows, paired_rows = [], []
    for artifact in artifacts.values():
        candidate, plan, run = artifact["candidate"], artifact["plan"], artifact["run"]
        cfg = plan["config"]
        quality_status = data_quality_status(cfg.get("source_type", "daily"), candidate)
        score = read_frame(artifact["score_path"])[GROUP_COLUMNS].reindex(calendar)
        run_labels = read_frame(run / "group_labels.csv")[GROUP_COLUMNS]
        common_labels = run_labels.index.intersection(calendar)
        run_common = run_labels.reindex(common_labels)
        comparable = run_common.notna().all(axis=1)
        label_artifact_matches = bool(np.allclose(
            run_common.loc[comparable].to_numpy(float),
            labels.reindex(common_labels).loc[comparable].to_numpy(float),
            rtol=0, atol=1e-12, equal_nan=True))
        ic = daily_ic(score, labels)
        halt_mask = candidate_halt_window_mask(
            calendar, [candidate], halted_dates
        )[candidate]
        ic_without_halt_window = ic.where(~halt_mask)
        full = stats(ic, calendar)
        without_halt_window = stats(ic_without_halt_window, calendar)
        y2025 = stats(year_slice(ic, coverage, 2025), calendar[calendar.year == 2025])
        y2026 = stats(year_slice(ic, coverage, 2026), calendar[calendar.year == 2026])
        min_loso, min_loso_2026 = loso_min(score, labels, ic)
        policy = confirmation.evidence_policy(cfg, candidate)
        paired = []

        if cfg.get("source_type") == "interaction":
            window = cfg["windows"][0]
            mechanism = candidate.removesuffix(f"_{window}")
            for side in ("left", "right"):
                parent = cfg["mechanisms"][mechanism][side]
                parent_path = runs_root / parent["parent_run"] / f"scores_{parent['parent_candidate']}.csv"
                leg_score = read_frame(parent_path)[GROUP_COLUMNS].reindex(calendar)
                paired.append((side, daily_ic(leg_score, labels)))
        elif cfg.get("source_type") == "daily_rounds":
            if raw_context is None:
                universe = ROOT / cfg["universe"]
                groups = yaml.safe_load((ROOT / cfg["groups"]).read_text())["groups"]
                panels = load_canonical_daily(
                    Path(cfg["data_root"]), universe, as_of="2026-09-17", roles=("candidate",))
                panels = {key: value.reindex(calendar.union(value.index)).sort_index()
                          for key, value in panels.items()}
                raw_context = panels, groups
            panels, groups = raw_context
            legs = daily_rounds.build_paired_legs(panels, cfg, candidate)
            if legs is not None:
                for side, member_leg in legs.items():
                    leg_score = discovery.aggregate(member_leg, groups).reindex(calendar)
                    paired.append((side, daily_ic(leg_score, labels)))

        judge_calendar = calendar[calendar.year == 2026] if policy == "2025_DIRECTION_2026_HISTORICAL_SEGMENT" else calendar
        paired_pass = True
        if paired:
            for side, leg_ic in paired:
                result = paired_stats(ic, leg_ic, judge_calendar)
                paired_rows.append({"definition_id": artifact["key"], "candidate": candidate,
                                    "side": side, "policy": policy, **result})
                paired_pass &= result["n"] >= (120 if judge_calendar.year.min() == 2026 and judge_calendar.year.max() == 2026 else 360)
                paired_pass &= result["mean"] > 0 and result["hac_t"] >= 2.0
        years_positive = y2025["ic_mean"] > 0 and y2026["ic_mean"] > 0
        historical_pass = (
            full["n"] >= 360 and full["ic_mean"] >= .01 and full["ic_hac_t"] >= 2
            and full["ic_block_t"] >= 2 and years_positive and min_loso > 0
        )
        confirmation_pass = (
            y2026["n"] >= 120 and y2026["ic_mean"] >= .01 and y2026["ic_hac_t"] >= 2
            and y2026["ic_block_t"] >= 2 and min_loso_2026 > 0
        )
        if policy == "PRIOR_DIRECTION_FULL_WINDOW":
            evidence_pass = historical_pass
            judge_p = full["ic_p_normal_one_sided"]
        elif policy == "2025_DIRECTION_2026_HISTORICAL_SEGMENT":
            evidence_pass = confirmation_pass
            judge_p = y2026["ic_p_normal_one_sided"]
        else:
            evidence_pass = False
            judge_p = y2026["ic_p_normal_one_sided"]
        evidence_pass = bool(
            evidence_pass and label_artifact_matches
            and quality_status in {
                "CLEAN_FOR_CURRENT_REJUDGE", "HALT_DIAGNOSTIC_REPORTED"
            }
        )
        rows.append({
            "definition_id": artifact["key"], "candidate": candidate,
            "source_run": run.name, "evidence_policy": policy,
            "source_label_artifact_matches": label_artifact_matches,
            "data_quality_status": quality_status,
            **{f"full_{k}": v for k, v in full.items()},
            "halt_window_excluded_n": int((halt_mask & ic.notna()).sum()),
            **{f"without_halt_window_{k}": v for k, v in without_halt_window.items()},
            "halt_window_diagnostic_only": True,
            **{f"y2025_{k}": v for k, v in y2025.items()},
            **{f"y2026_{k}": v for k, v in y2026.items()},
            "full_min_loso_ic": min_loso, "y2026_min_loso_ic": min_loso_2026,
            "historical_metrics_pass": historical_pass,
            "historical_2026_metrics_pass": confirmation_pass,
            "paired_required": bool(paired), "paired_increment_pass": bool(paired_pass),
            "factor_evidence_pass": evidence_pass,
            "conditional_budget_pass": bool(evidence_pass and judge_p <= .05 / args.conditional_budget),
        })

    output.mkdir(parents=True)
    summary = pd.DataFrame(rows).sort_values(["full_ic_hac_t", "candidate"], ascending=[False, True])
    summary.to_csv(output / "summary.csv", index=False)
    pd.DataFrame(paired_rows).to_csv(output / "paired_increment.csv", index=False)
    ic_names = summary.loc[summary.factor_evidence_pass, "candidate"].tolist()
    budget_names = summary.loc[summary.conditional_budget_pass, "candidate"].tolist()
    summary_wording = f"{len(ic_names)} basic historical IC leads; {len(budget_names)} conditional-budget leads; certified factors 0"
    verdict = {
        "status": "HISTORICAL_ZERO_BUDGET_IC_ONLY_REJUDGE_V6",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "definitions_rejudged": len(summary),
        "conditionally_registered_definitions": args.conditional_budget,
        "registration_minus_saved_semantic_count": args.conditional_budget - len(summary),
        "count_note": "Registration counts implementation versions and external8; this difference is not a missing-score count. See IC inventory registrations.csv.",
        "conditional_budget": args.conditional_budget,
        "primary_evidence_field": "ic_candidates",
        "ic_candidates": ic_names,
        "factor_evidence_candidates": ic_names,
        "conditional_budget_candidates": budget_names,
        "certified_factors": 0,
        "summary_wording": summary_wording,
        "paired_increment_policy": "REPORT_ONLY_NOT_AN_IC_GATE",
        "cost_gate": "NOT_APPLIED_FACTOR_STAGE",
        "new_definitions_registered": 0,
        "data_quality_counts": summary["data_quality_status"].value_counts().to_dict(),
    }
    source_dir = output / "source"
    source_dir.mkdir()
    source_files = [Path(__file__), Path(daily_rounds.__file__), Path(discovery.__file__),
                    Path(confirmation.__file__), ETF / "src/etf_strategy/core/etf_rank_utils.py",
                    ETF / "src/etf_strategy/core/etf_mining_referee.py",
                    ETF / "src/etf_strategy/core/etf_ic_monthly_factory.py"]
    source_files.extend(Path(module.__file__) for module in daily_rounds.LUNA_MODULES)
    for source_file in source_files:
        shutil.copyfile(source_file, source_dir / source_file.name)
    verdict["command"] = [sys.executable, *sys.argv]
    verdict["source_hashes"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    (output / "verdict.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n")
    (output / "REPORT.md").write_text(
        "# ETF IC repair rejudge\n\n"
        f"{summary_wording}.\n\n"
        f"Rejudged {len(summary)} frozen semantic definitions with saved scores; "
        f"conditional registration budget {args.conditional_budget} counts implementation versions and external8 separately. "
        "Scores were normalized to 12 significant digits before average-tie ranking. "
        "Prior directions use the full seen-history window; directions chosen on 2025 use only the 2026 historical segment. Neither is independent confirmation. "
        "Paired increments are reported separately and never gate basic IC leads. Costs are not a factor gate. "
        "For every candidate, the IC/HAC t after removing signal dates whose trailing candidate window contains a 513100 opening-halt day is reported as a diagnostic only and never used as a gate.\n\n"
        f"Historical factor-evidence rows after source-quality isolation: {int(summary.factor_evidence_pass.sum())}; "
        f"conditional-budget rows: {int(summary.conditional_budget_pass.sum())}. "
        f"Source-quality states: {summary['data_quality_status'].value_counts().to_dict()}.\n"
    )
    print(json.dumps(verdict, ensure_ascii=False))


if __name__ == "__main__":
    main()
