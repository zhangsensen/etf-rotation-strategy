#!/usr/bin/env python3
"""Idempotent daily driver for the versioned ETF IC monthly factory.

Every invocation, in order:
  (a) rebuilds today's daily_ic/label_dates/turnover panel at the actual
      latest available data date (never a hand-supplied or backdated date)
      and runs the panel builder's reproducibility gate;
  (b) if the previous calendar month has closed, the contract's freeze
      conditions are met, and that month is not yet frozen, freezes it;
  (c) for every already-frozen month whose evaluation-month labels have all
      matured and whose (process_version, contract_sha256, freeze_month,
      evaluation_month) key is not yet in the ledger, evaluates it and
      appends the ledger.

If neither (b) nor (c) does anything, prints a NOOP reason per skipped
action and exits 0. No new candidate definitions are proposed here; this is
a data-production and forward-evaluation driver only.

Read-only against data/. Writes only under
runtime_outputs/etf_rotation_research/monthly_factory/{panels,freezes}/ and
appends to runtime_outputs/etf_rotation_research/monthly_ic_ledger.jsonl.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from etf_strategy.core.etf_ic_monthly_factory import (
    MonthlyFreeze,
    append_ledger,
    candidate_halt_window_mask,
    evaluate_next_month,
    freeze_month,
    load_contract,
    open_halt_dates,
    read_version,
    verify_contract_files,
)

import build_etf_ic_monthly_panel as panel_builder

DATA_ROOT = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
CONTRACT_PATH = ETF / "configs/etf_ic_monthly_factory_v4.yaml"
PANELS_ROOT = ROOT / "runtime_outputs/etf_rotation_research/monthly_factory/panels"
FREEZES_ROOT = ROOT / "runtime_outputs/etf_rotation_research/monthly_factory/freezes"
LEDGER_PATH = ROOT / "runtime_outputs/etf_rotation_research/monthly_ic_ledger.jsonl"
HALT_MINUTE_PATH = DATA_ROOT / "1m/513100.SH.parquet"


def determine_as_of() -> pd.Timestamp:
    """The actual latest available trading date in the canonical calendar.

    Never accepts a manually supplied or earlier date: this function is the
    only source of --as-of for every step in the cycle.
    """
    calendar_raw = pd.read_parquet(DATA_ROOT / "1d/510300.SH.parquet")
    return pd.to_datetime(calendar_raw.trade_date).max().normalize()


def build_and_gate_panel(as_of: pd.Timestamp, contract_path: Path) -> dict:
    built = panel_builder.build(str(as_of.date()), str(contract_path))
    contract, _digest = load_contract(str(contract_path))
    catalog = [str(c) for c in contract["candidate_catalog"]]
    panel_builder.run_reproducibility_gate(built, catalog)
    out = PANELS_ROOT / str(as_of.date())
    out.mkdir(parents=True, exist_ok=True)
    built["daily_ic"].to_csv(out / "daily_ic.csv")
    built["label_dates"].to_csv(out / "label_dates.csv")
    built["turnover"].to_csv(out / "turnover.csv")
    return {"daily_ic": built["daily_ic"], "label_dates": built["label_dates"],
            "turnover": built["turnover"], "panel_dir": out}


def _already_frozen_months(freezes_root: Path) -> set[str]:
    if not freezes_root.exists():
        return set()
    return {p.name for p in freezes_root.iterdir() if p.is_dir() and (p / "freeze.json").exists()}


def find_freeze_candidate(contract: dict, as_of: pd.Timestamp) -> tuple[str | None, str]:
    """Return (freeze_month or None, reason). Scans forward from
    first_freeze_month for the first CLOSED month not yet frozen, so a
    dormant wrapper catches up one month per invocation rather than skipping
    straight to the most recent one.
    """
    if not contract.get("freeze_requires_month_closed"):
        raise ValueError("v4 contract must require freeze_requires_month_closed")
    first = pd.Period(str(contract["first_freeze_month"]), freq="M")
    frozen = _already_frozen_months(FREEZES_ROOT)
    month = first
    while month.end_time.normalize() <= as_of:
        if str(month) not in frozen:
            return str(month), f"month {month} is closed and unfrozen"
        month += 1
    return None, "no closed month is pending a freeze"


def do_freeze(
    contract: dict, digest: str, freeze_month_str: str,
    daily_ic: pd.DataFrame, label_dates: pd.DataFrame, as_of: pd.Timestamp,
) -> dict:
    minute = pd.read_parquet(HALT_MINUTE_PATH)
    if "ts_code" in minute and not minute["ts_code"].eq("513100.SH").all():
        raise ValueError("halt diagnostic input must contain only 513100.SH")
    halt_mask = candidate_halt_window_mask(
        daily_ic.index, [str(c) for c in contract["candidate_catalog"]],
        open_halt_dates(minute),
    )
    frozen, selection = freeze_month(
        contract, digest, daily_ic, label_dates, freeze_month_str,
        halt_window_mask=halt_mask, as_of=str(as_of.date()),
    )
    output = FREEZES_ROOT / freeze_month_str
    output.mkdir(parents=True)  # must not already exist; caller already checked
    (output / "freeze.json").write_text(json.dumps(asdict(frozen), ensure_ascii=False, indent=2) + "\n")
    selection.to_csv(output / "selection.csv", index=False)
    return asdict(frozen)


def find_evaluate_candidates(
    contract: dict, digest: str, label_dates: pd.DataFrame, as_of: pd.Timestamp,
) -> list[tuple[MonthlyFreeze, Path]]:
    ready = []
    ledger_rows = read_version(LEDGER_PATH, contract["process_version"], digest)
    ledger_keys = {
        (r["process_version"], r["contract_sha256"], r["freeze_month"], r["evaluation_month"])
        for r in ledger_rows
    }
    for month_dir in sorted(_already_frozen_months(FREEZES_ROOT)):
        freeze_path = FREEZES_ROOT / month_dir / "freeze.json"
        raw = json.loads(freeze_path.read_text())
        if raw["contract_sha256"] != digest or raw["process_version"] != contract["process_version"]:
            continue  # belongs to a different process version; not this contract's concern
        frozen = MonthlyFreeze(**{**raw, "selected_candidates": tuple(raw["selected_candidates"])})
        key = (frozen.process_version, frozen.contract_sha256, frozen.freeze_month, frozen.evaluation_month)
        if key in ledger_keys:
            continue
        month = pd.Period(frozen.evaluation_month, freq="M")
        eval_dates = label_dates.index[
            (label_dates.index >= month.start_time) & (label_dates.index <= month.end_time)
        ]
        if len(eval_dates) == 0:
            continue  # evaluation month has no signal dates yet at all
        if as_of.normalize() < month.end_time.normalize():
            continue  # never settle a partial calendar month
        exits = pd.to_datetime(label_dates.loc[eval_dates, "exit_date"])
        matured = exits.notna().all() and exits.max() <= as_of.normalize()
        if matured:
            ready.append((frozen, freeze_path.parent))
    return ready


def do_evaluate(
    frozen: MonthlyFreeze, daily_ic: pd.DataFrame, label_dates: pd.DataFrame,
    turnover: pd.DataFrame, as_of: pd.Timestamp, hac_lag: int,
) -> dict:
    record = evaluate_next_month(
        frozen, daily_ic, label_dates, as_of=str(as_of.date()),
        turnover=turnover, hac_lag=hac_lag,
    )
    append_ledger(LEDGER_PATH, record)
    return record


def main() -> None:
    contract, digest = load_contract(str(CONTRACT_PATH))
    verify_contract_files(contract, ROOT)
    as_of = determine_as_of()

    panels = build_and_gate_panel(as_of, CONTRACT_PATH)
    print(json.dumps({"step": "build_panel", "as_of": str(as_of.date()), "output": str(panels["panel_dir"])}))

    noop_reasons = []

    freeze_target, freeze_reason = find_freeze_candidate(contract, as_of)
    if freeze_target is None:
        noop_reasons.append(f"freeze: NOOP ({freeze_reason})")
    else:
        result = do_freeze(contract, digest, freeze_target, panels["daily_ic"], panels["label_dates"], as_of)
        print(json.dumps({"step": "freeze", "result": result}))

    evaluate_candidates = find_evaluate_candidates(contract, digest, panels["label_dates"], as_of)
    if not evaluate_candidates:
        noop_reasons.append("evaluate: NOOP (no frozen month has fully matured, unevaluated labels)")
    else:
        for frozen, _freeze_dir in evaluate_candidates:
            record = do_evaluate(
                frozen, panels["daily_ic"], panels["label_dates"], panels["turnover"],
                as_of, hac_lag=int(contract["selection"]["hac_lag"]),
            )
            print(json.dumps({"step": "evaluate", "result": record}))

    if noop_reasons:
        print(json.dumps({"step": "noop_summary", "reasons": noop_reasons}))


if __name__ == "__main__":
    main()
