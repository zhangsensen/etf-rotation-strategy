#!/usr/bin/env python3
"""Observation-only daily scores and matured H5 IC for the 11 leads outside v4.

The v4 selection contract and its panel are deliberately untouched.  A saved
share-parent interaction cannot acquire new scores by extending its old CSV;
its forward rows are explicitly uncomputable until point-in-time share data
and parent score production have been established.
"""
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

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as discovery
from etf_strategy.core import etf_group_daily_rounds as daily_rounds
from etf_strategy.core import etf_group_claude_rounds as claude_rounds
from etf_strategy.core import etf_group_daily_outcome as daily_outcome
from etf_strategy.core.etf_ic_monthly_factory import load_contract, verify_contract_files
from etf_strategy.core.etf_rank_utils import stable_rank

DATA_ROOT = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
RUNS = ROOT / "runtime_outputs/etf_rotation_research/runs"
GROUPS = ETF / "configs/etf_candidate14_economic_groups_v1.yaml"
UNIVERSE = ROOT / "config/etf_rotation_universe_v1.json"
V4 = ETF / "configs/etf_ic_monthly_factory_v4.yaml"
VERSION = "etf_ic_lead_extra_panel_v1"

# Frozen historical identity, source type and direction; these are not new
# hypotheses.  A change here requires an observer version change.
SOURCES = {
    "market_coskewness_20": ("daily_rounds", "group_ic_batch27_market_coskewness_20260923", 1),
    "beta_asymmetry_60": ("claude_rounds", "group_ic_batchA_market_comovement_20260923", -1),
    "intraday_body_utilization_20": ("daily_rounds", "group_ic_batch29_intraday_body_utilization_20260923", 1),
    "d2025_body_shock_wick_repair_20": ("daily_rounds", "group_ic20_batch22_stage2_daily_20260923", 1),
    "breadth_5": ("group_breadth", "group_next8_20260922_v4", 1),
    "range_flow_20_40_1": ("share_interaction_saved_only", "group_interaction_v1_batch_20260922", 1),
    "d2025_amount_innovation_sign_entropy_20": ("daily_rounds", "group_ic20_batch15_stage2_daily_b_20260923", 1),
    "peer_corr_network_change_60": ("claude_rounds", "group_ic_round3_higher_order_and_network_20260923", -1),
    "intraday_return_5": ("daily", "group_daily_v1_batch_20260922", 1),
    "OVERHEAD_TURNOVER_20": ("daily_outcome", "group_ic20_outcome_rejudge_v4_20260922", -1),
    "weekday_relative_return_pattern_60": ("claude_rounds", "group_ic_round8_horizon_and_seasonality_20260923", 1),
}


def _source_dir(kind: str, run: str) -> Path:
    return (ROOT / "runtime_outputs/etf_rotation_research" / run) if kind == "group_breadth" else RUNS / run


def _definition(candidate: str) -> tuple[dict, str, int]:
    kind, run, direction = SOURCES[candidate]
    plan = json.loads((_source_dir(kind, run) / "PLAN.json").read_text())
    cfg = plan["config"]
    if kind == "group_breadth":
        return cfg, "breadth", 5
    if kind == "share_interaction_saved_only":
        return cfg, "range_flow_20_40", 1
    for name, definition in cfg["mechanisms"].items():
        if kind == "daily_outcome":
            match = name == candidate
            window = 20
        else:
            window = definition.get("window") or next(
                (w for w in cfg["windows"] if f"{name}_{w}" == candidate), None
            )
            match = f"{name}_{window}" == candidate
        if match:
            if definition["direction"] != direction:
                raise ValueError(f"historical direction changed for {candidate}")
            return cfg, name, int(window)
    raise ValueError(f"candidate missing from its frozen source PLAN: {candidate}")


def _breadth_score(close: pd.DataFrame, groups: dict) -> pd.DataFrame:
    ret = close.pct_change(fill_method=None)
    result = {}
    for group, spec in groups.items():
        members = ret[spec["members"]]
        daily = members.gt(0).mean(axis=1).where(members.notna().all(axis=1))
        result[group] = daily.rolling(5, min_periods=5).mean()
    return pd.DataFrame(result, index=close.index)


def _saved_score(candidate: str) -> pd.DataFrame:
    kind, run, _ = SOURCES[candidate]
    path = _source_dir(kind, run) / f"scores_{candidate}.csv"
    return pd.read_csv(path, index_col=0, parse_dates=True, float_precision="round_trip")


def _source_revised(candidate: str) -> bool:
    kind, run, _ = SOURCES[candidate]
    plan = json.loads((_source_dir(kind, run) / "PLAN.json").read_text())
    return any(not Path(path).is_file() or sha256(Path(path).read_bytes()).hexdigest() != digest
               for path, digest in plan.get("input_hashes", {}).items())


def _repro_check(candidate: str, score: pd.DataFrame) -> dict:
    saved = _saved_score(candidate)
    common = saved.index.intersection(score.index)
    common = common[common >= pd.Timestamp("2025-01-01")]
    if len(common) == 0:
        raise ValueError(f"no historical comparison dates for {candidate}")
    if list(saved.columns) != list(score.columns):
        raise ValueError(f"group columns changed for {candidate}")
    a, b = saved.loc[common], score.loc[common]
    mismatch = a.isna().ne(b.isna()) | ((a - b).abs() > 1e-9 * a.abs().clip(lower=1e-12))
    count = int(mismatch.to_numpy().sum())
    revised = _source_revised(candidate)
    if count and not revised:
        raise ValueError(f"unrevised source score mismatch: {candidate}, cells={count}")
    return {"candidate": candidate, "source_run": SOURCES[candidate][1],
            "compared_dates": len(common), "mismatch_cells": count,
            "source_inputs_revised": revised,
            "status": "DATA_REVISED_SINCE_RUN" if count else "MATCH"}


def _matured_ic(score: pd.DataFrame, member_labels: pd.DataFrame,
                groups: dict, base_known: pd.Series,
                label_dates: pd.DataFrame, as_of_date: pd.Timestamp) -> pd.Series:
    """Never expose IC until the entire D+2 to D+7 label has exited."""
    matured = label_dates.exit_date.notna() & label_dates.exit_date.le(as_of_date)
    complete = (score.notna().all(axis=1) & base_known &
                member_labels.notna().all(axis=1) & matured)
    group_labels = discovery.aggregate(member_labels, groups)
    return stable_rank(score).corrwith(group_labels.rank(axis=1, method="average"), axis=1).where(complete)


def build_extra(as_of: str) -> dict:
    """Rebuild eleven frozen score definitions; IC only where H5 exit has matured."""
    as_of_date = pd.Timestamp(as_of).normalize()
    contract, contract_digest = load_contract(V4)
    verify_contract_files(contract, ROOT)
    if (contract["signal_time"], contract["entry_lag"], contract["horizon"]) != ("close_D", 2, 5):
        raise ValueError("v4 time contract changed")
    if set(SOURCES) & set(contract["candidate_catalog"]):
        raise ValueError("extra catalog overlaps v4 selection catalog")
    groups = yaml.safe_load(GROUPS.read_text())["groups"]
    universe = json.loads(UNIVERSE.read_text())
    symbols = [r["ts_code"] for r in universe["etfs"] if r["role"] == "candidate"]
    discovery.validate_groups(groups, symbols)
    panels = load_canonical_daily(DATA_ROOT, UNIVERSE, as_of=str(as_of_date.date()), roles=("candidate",))
    raw_calendar = pd.read_parquet(DATA_ROOT / "1d/510300.SH.parquet", columns=["trade_date"])
    calendar = pd.DatetimeIndex(pd.to_datetime(raw_calendar.trade_date)).sort_values()
    calendar = calendar[calendar <= as_of_date]
    panels = {key: value.reindex(calendar) for key, value in panels.items()}
    member_labels, dates = discovery.labels(panels, lag=2, horizon=5)
    label_dates = dates[["entry_date", "exit_date"]].copy()
    label_dates.index.name = "signal_date"
    dated = label_dates.dropna()
    if not ((dated.index < dated.entry_date) & (dated.entry_date < dated.exit_date)).all():
        raise ValueError("signal < entry < exit timing contract failed")
    base_known = panels["close"].notna().rolling(60).sum().eq(60).all(axis=1) & panels["volume"].gt(0).all(axis=1)

    score_map: dict[str, pd.DataFrame] = {}
    checks = []
    coverage = []
    for candidate, (kind, _run, _direction) in SOURCES.items():
        cfg, name, window = _definition(candidate)
        if kind == "group_breadth":
            score = _breadth_score(panels["close"], groups)
        elif kind == "share_interaction_saved_only":
            # Old parent share scores stop at the archived run.  Forward-fill
            # would turn an unknown D-close disclosure into a false signal.
            saved = _saved_score(candidate)
            score = saved.reindex(calendar)
            last_saved = saved.index.max()
            score.loc[score.index > last_saved] = np.nan
        else:
            selected = {name: cfg["mechanisms"][name]}
            if kind == "daily_rounds":
                atom = daily_rounds.build_atoms(panels, {"windows": [20], "mechanisms": selected})[candidate]
            elif kind == "claude_rounds":
                atom = claude_rounds.build_atoms(panels, {"mechanisms": selected})[candidate]
            elif kind == "daily":
                atom = discovery.build_atoms(panels, {"windows": [window], "mechanisms": selected})[candidate]
            elif kind == "daily_outcome":
                atom = daily_outcome.build_atoms(panels, cfg)[candidate]
            else:
                raise ValueError(f"unsupported historical source: {kind}")
            score = discovery.aggregate(atom, groups)
        score = score.reindex(calendar)[list(groups)]
        score_map[candidate] = score
        checks.append(_repro_check(candidate, score))
        complete = score.notna().all(axis=1) & base_known
        if kind == "share_interaction_saved_only":
            status = "UNCOMPUTABLE_FORWARD_SHARE_PARENT_VINTAGE"
        else:
            status = "COMPUTABLE"
        coverage.append({"candidate": candidate, "status": status,
                         "latest_score_date": str(score.index[complete].max().date()) if complete.any() else None,
                         "as_of_score_complete": bool(complete.loc[as_of_date]) if as_of_date in complete else False})

    daily_ic = pd.DataFrame(index=calendar, columns=list(SOURCES), dtype=float)
    for candidate, score in score_map.items():
        daily_ic[candidate] = _matured_ic(score, member_labels, groups, base_known,
                                          label_dates, as_of_date)
    daily_ic.index.name = "signal_date"
    return {"daily_ic": daily_ic, "label_dates": label_dates, "scores": score_map,
            "coverage": coverage, "reproducibility": checks,
            "version": VERSION, "as_of": str(as_of_date.date()), "v4_contract_sha256": contract_digest,
            "signal_time": "close_D", "entry_lag": 2, "horizon": 5}


def persist_extra(result: dict, output_root: Path) -> Path:
    """Keep one immutable local evidence panel for each data date."""
    output = output_root / result["as_of"]
    if output.exists():
        old = json.loads((output / "manifest.json").read_text())
        if old["version"] != result["version"] or old["v4_contract_sha256"] != result["v4_contract_sha256"]:
            raise ValueError(f"existing extra panel has a different contract: {output}")
        saved_ic = pd.read_csv(output / "daily_ic.csv", index_col=0, parse_dates=True)
        pd.testing.assert_frame_equal(saved_ic, result["daily_ic"], check_exact=False,
                                      check_freq=False, rtol=1e-12, atol=1e-12)
        return output
    output.mkdir(parents=True)
    result["daily_ic"].to_csv(output / "daily_ic.csv")
    result["label_dates"].to_csv(output / "label_dates.csv")
    score_dir = output / "scores"
    score_dir.mkdir()
    for candidate, frame in result["scores"].items():
        frame.to_csv(score_dir / f"{candidate}.csv", index_label="signal_date")
    manifest = {key: value for key, value in result.items() if key not in {"daily_ic", "label_dates", "scores"}}
    manifest["catalog"] = list(SOURCES)
    manifest["source_runs"] = {candidate: run for candidate, (_kind, run, _sign) in SOURCES.items()}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output-root", type=Path, default=ROOT / "runtime_outputs/etf_rotation_research/ic_lead_extra_panels")
    args = parser.parse_args()
    result = build_extra(args.as_of)
    output = persist_extra(result, args.output_root)
    print(json.dumps({"output": str(output), "coverage": result["coverage"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
