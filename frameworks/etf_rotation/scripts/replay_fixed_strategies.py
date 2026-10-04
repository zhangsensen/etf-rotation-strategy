"""Replay frozen candidates with auditable entry-price protection (local only).

No candidate discovery or parameter search. The reference directory must contain
replay_config.yaml and sealed_two_candidates.parquet from the legacy reproduction.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
os.environ.setdefault("BT_NUM_WORKERS", "2")
os.environ.setdefault("NUMBA_NUM_THREADS", "2")

import pandas as pd
import yaml
import batch_bt_backtest as engine

OUT = None
ACTIVE = "unknown"
ORIGINAL_PROCESS = engine.process_combo
ORIGINAL_RUN = engine.bt.Cerebro.run
ORIGINAL_TARGETS = engine.GenericStrategy._compute_rebalance_targets


def observe_process(row):
    global ACTIVE
    ACTIVE = "composite_1" if "SHARE_CHG_5D" in row["combo"] else "core_4f"
    return ORIGINAL_PROCESS(row)


def observe_targets(self, current_date):
    result = ORIGINAL_TARGETS(self, current_date)
    if result is not None:
        if not hasattr(self, "_replay_targets"):
            self._replay_targets = []
        self._replay_targets.append({
            "signal_date": str(self.datas[0].datetime.date(-1)),
            "decision_date": str(current_date.date()),
            "targets": list(result[0]), "timing": float(result[1]),
        })
    return result


def observe_run(self, *args, **kwargs):
    result = ORIGINAL_RUN(self, *args, **kwargs)
    for strat in result:
        pd.DataFrame(strat.orders).to_csv(OUT / f"{ACTIVE}_orders.csv", index=False)
        pd.DataFrame(strat.trades).to_csv(OUT / f"{ACTIVE}_closed_trades.csv", index=False)
        (OUT / f"{ACTIVE}_stops.json").write_text(json.dumps(strat.stop_events, indent=2))
        (OUT / f"{ACTIVE}_exposure.json").write_text(json.dumps(strat.exposure_events, indent=2))
        (OUT / f"{ACTIVE}_cash_gate.json").write_text(json.dumps(strat.cash_gate_events, indent=2))
        (OUT / f"{ACTIVE}_targets.json").write_text(json.dumps(getattr(strat, "_replay_targets", []), indent=2))
        pd.Series(strat.analyzers.timereturn.get_analysis()).to_csv(OUT / f"{ACTIVE}_daily_returns.csv")
        (OUT / f"{ACTIVE}_end_state.json").write_text(json.dumps({
            "cash": strat.broker.getcash(), "nav": strat.broker.getvalue(),
            "positions": {d._name: {"size": strat.getposition(d).size,
                                     "close": d.close[0]}
                          for d in strat.datas if strat.getposition(d).size},
            "margin_failures": strat.margin_failures,
            "pending_protective_orders": len(strat._stop_orders),
        }, indent=2))
    return result


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stop-loss", type=float, default=.05)
    parser.add_argument("--activate-on", help="First session with protection; default entire replay")
    parser.add_argument("--exposure-control", choices=["legacy", "cap_retained"], default="legacy")
    parser.add_argument("--exposure-start", help="First session with the exposure ceiling enforced")
    parser.add_argument("--cash-gate", choices=["disabled", "dual_worst"], default="disabled")
    parser.add_argument("--cash-start", help="First decision date on which the cash gate may apply")
    args = parser.parse_args()
    OUT = args.output.resolve()
    if OUT.exists() and any(OUT.iterdir()):
        raise ValueError("Use a new empty output directory to preserve previous evidence")
    OUT.mkdir(parents=True, exist_ok=True)
    os.environ["NUMBA_CACHE_DIR"] = str(OUT / "numba_cache")
    reference = args.reference_run.resolve()
    config = yaml.safe_load((reference / "replay_config.yaml").read_text())
    risk = config["backtest"]["risk_control"]
    # Disable via an explicit execution switch; retain the historical frozen
    # 5% threshold so the baseline does not weaken other frozen-parameter checks.
    risk["etf_stop_enabled"] = args.stop_loss != 0
    if args.stop_loss != 0:
        risk["etf_stop_loss"] = args.stop_loss
    risk["etf_stop_execution"] = "next_session_intraday"
    risk["etf_stop_start_date"] = args.activate_on
    engine.load_fixed_stop(config)
    config["backtest"]["exposure_control"] = {"mode": args.exposure_control, "start_date": args.exposure_start}
    config["backtest"]["cash_gate"] = {"mode": args.cash_gate, "start_date": args.cash_start}
    config_path = OUT / "replay_config.yaml"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
    candidates = reference / "sealed_two_candidates.parquet"
    # Snapshot source and hashes, never copy market data or candidate tables for handoff.
    hashes = {}
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in path.parts for p in (".cache", "results", "__pycache__")):
            continue
        rel = path.relative_to(ROOT)
        target = OUT / "source_snapshot" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        hashes[str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "reference_run": str(reference), "reference_input_hashes": str(reference / "input_hashes.json"),
        "candidates": str(candidates), "candidate_sha256": hashlib.sha256(candidates.read_bytes()).hexdigest(),
        "source_sha256": hashes, "stop_loss": args.stop_loss, "activate_on": args.activate_on,
        "exposure_control": args.exposure_control, "exposure_start": args.exposure_start,
        "cash_gate": args.cash_gate, "cash_start": args.cash_start,
        "signal_lag_days": 1, "execution_lag_days_from_factor": 2,
        "stop_contract": "entry VWAP minus loss_pct; resting next-session stop; gap at open; fees extra; no same-session re-entry",
        "python": sys.version,
        "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        "command": sys.argv,
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    engine.ROOT = OUT
    engine.process_combo = observe_process
    engine.bt.Cerebro.run = observe_run
    engine.GenericStrategy._compute_rebalance_targets = observe_targets
    sys.argv = [str(ROOT / "scripts" / "batch_bt_backtest.py"), "--config", str(config_path),
                "--combos", str(candidates), "--delta-rank", "0.10", "--min-hold-days", "9"]
    engine.main()


if __name__ == "__main__":
    main()
