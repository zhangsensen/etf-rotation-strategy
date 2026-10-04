#!/usr/bin/env python3
"""Freeze or evaluate one month of the versioned ETF IC factor process."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))

from etf_strategy.core.etf_ic_monthly_factory import (
    MonthlyFreeze,
    append_ledger,
    candidate_halt_window_mask,
    evaluate_next_month,
    freeze_month,
    load_contract,
    open_halt_dates,
    verify_contract_files,
)


def frame(path: str) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0, parse_dates=True, float_precision="round_trip")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", default=str(ETF / "configs/etf_ic_monthly_factory_v4.yaml"))
    sub = parser.add_subparsers(dest="action", required=True)
    freeze = sub.add_parser("freeze")
    freeze.add_argument("--daily-ic", required=True)
    freeze.add_argument("--label-dates", required=True)
    freeze.add_argument("--freeze-month", required=True)
    freeze.add_argument("--as-of", required=True)
    freeze.add_argument(
        "--halt-minute", required=True,
        help="513100 1m parquet used only for the report-only halt-window diagnostic",
    )
    freeze.add_argument("--output", required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--freeze", required=True)
    evaluate.add_argument("--daily-ic", required=True)
    evaluate.add_argument("--label-dates", required=True)
    evaluate.add_argument("--turnover")
    evaluate.add_argument("--as-of", required=True)
    evaluate.add_argument("--ledger", default=str(ROOT / "runtime_outputs/etf_rotation_research/monthly_ic_ledger.jsonl"))
    args = parser.parse_args()

    contract, digest = load_contract(args.contract)
    verify_contract_files(contract, ROOT)
    if args.action == "freeze":
        output = Path(args.output)
        if output.exists():
            raise FileExistsError(output)
        output.mkdir(parents=True)
        daily_ic = frame(args.daily_ic)
        minute = pd.read_parquet(args.halt_minute)
        if "ts_code" in minute and not minute["ts_code"].eq("513100.SH").all():
            raise ValueError("halt diagnostic input must contain only 513100.SH")
        halt_mask = candidate_halt_window_mask(
            daily_ic.index,
            [str(candidate) for candidate in contract["candidate_catalog"]],
            open_halt_dates(minute),
        )
        frozen, selection = freeze_month(
            contract, digest, daily_ic, frame(args.label_dates), args.freeze_month,
            halt_window_mask=halt_mask, as_of=args.as_of,
        )
        (output / "freeze.json").write_text(
            json.dumps(asdict(frozen), ensure_ascii=False, indent=2) + "\n")
        selection.to_csv(output / "selection.csv", index=False)
        print(json.dumps(asdict(frozen), ensure_ascii=False))
        return

    raw = json.loads(Path(args.freeze).read_text())
    frozen = MonthlyFreeze(
        **{**raw, "selected_candidates": tuple(raw["selected_candidates"])}
    )
    if frozen.contract_sha256 != digest or frozen.process_version != contract["process_version"]:
        raise ValueError("freeze belongs to a different monthly process version")
    record = evaluate_next_month(
        frozen, frame(args.daily_ic), frame(args.label_dates), as_of=args.as_of,
        turnover=frame(args.turnover) if args.turnover else None,
        hac_lag=int(contract["selection"]["hac_lag"]),
    )
    append_ledger(args.ledger, record)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
