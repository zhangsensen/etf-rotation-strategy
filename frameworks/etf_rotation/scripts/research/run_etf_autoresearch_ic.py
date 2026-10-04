#!/usr/bin/env python3
"""Fixed, discovery-only ETF autoresearch evaluator. Do not edit per trial."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
sys.path.insert(0, str(ETF / "src"))
from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as engine
from etf_strategy.core import etf_mining_referee, etf_rank_utils
from etf_strategy import canonical_data

DATA = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
UNIVERSE = ROOT / "config/etf_rotation_universe_v1.json"
GROUPS = ETF / "configs/etf_candidate14_economic_groups_v1.yaml"
CANDIDATE = Path(__file__).with_name("etf_autoresearch_candidate.py")
COLD = pd.Timestamp("2026-03-24")
EVALUATION_START = pd.Timestamp("2025-01-01")
TIME_BUDGET_SECONDS = 300
RESULT_HEADER = "run_id\tcandidate_sha256\tevaluator_sha256\tn\tic\thac_t\tfamily\tstatus\n"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def append_result(output_root: Path, fields: list[str]) -> None:
    path = output_root / "results.tsv"
    if not path.exists():
        path.write_text(RESULT_HEADER)
    with path.open("a") as handle:
        handle.write("\t".join(fields) + "\n")


def load_candidate(path: Path):
    spec = importlib.util.spec_from_file_location("etf_autoresearch_candidate", path)
    if spec is None or spec.loader is None:
        raise ValueError("candidate module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if (not isinstance(module.CANDIDATE_ID, str)
            or not module.CANDIDATE_ID.startswith("autoresearch_")
            or module.DIRECTION not in (-1, 1)
            or not isinstance(module.FAMILY, str)
            or not isinstance(module.DESCRIPTION, str)):
        raise ValueError("candidate metadata invalid")
    return module


def causal_scores(module, panels, cut):
    full = module.score(panels) * module.DIRECTION
    if not isinstance(full, pd.DataFrame) or not full.index.equals(panels["close"].index):
        raise ValueError("candidate score calendar invalid")
    if not full.columns.equals(panels["close"].columns):
        raise ValueError("candidate score population/order invalid")
    if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in full.dtypes):
        raise ValueError("candidate score must be numeric")
    full = full.replace([np.inf, -np.inf], np.nan)
    prefix = module.score({key: panel.loc[:cut].copy() for key, panel in panels.items()}) * module.DIRECTION
    future = {key: panel.copy() for key, panel in panels.items()}
    for panel in future.values():
        panel.loc[panel.index > cut] *= 1.73
    altered = module.score(future) * module.DIRECTION
    pd.testing.assert_frame_equal(full.loc[:cut], prefix, check_exact=False, rtol=1e-10, atol=1e-12)
    pd.testing.assert_frame_equal(full.loc[:cut], altered.loc[:cut], check_exact=False, rtol=1e-10, atol=1e-12)
    # The evaluated 2025+ rows must each be reproducible with data available
    # on that signal date. One pre-evaluation cut cannot catch conditional leaks.
    for signal_date in full.index[full.index >= EVALUATION_START]:
        available = {key: panel.loc[:signal_date].copy() for key, panel in panels.items()}
        current = module.score(available) * module.DIRECTION
        if (not isinstance(current, pd.DataFrame)
                or not current.index.equals(available["close"].index)
                or not current.columns.equals(full.columns)):
            raise ValueError("candidate score shape changes on signal-date prefix")
        pd.testing.assert_series_equal(full.loc[signal_date], current.loc[signal_date],
                                       check_names=False, check_exact=False,
                                       rtol=1e-10, atol=1e-12)
    return full


def _run_with_budget(run_id: str, output_root: Path, candidate_path: Path | None = None,
                     input_profile: str = "daily") -> dict:
    if not run_id.replace("_", "").replace("-", "").isalnum():
        raise ValueError("run-id must be alphanumeric with underscores/hyphens")
    started = time.monotonic()
    out = output_root / run_id
    out.mkdir(parents=True, exist_ok=False)
    candidate_path = candidate_path or CANDIDATE
    candidate_sha = digest(candidate_path)
    module = load_candidate(candidate_path)
    groups = yaml.safe_load(GROUPS.read_text())["groups"]
    calendar_file = DATA / "1d/510300.SH.parquet"
    calendar = pd.DatetimeIndex(pd.to_datetime(pd.read_parquet(calendar_file, columns=["trade_date"]).trade_date)).sort_values()
    calendar = calendar[calendar <= COLD]
    panels = load_canonical_daily(DATA, UNIVERSE, as_of=str(COLD.date()), roles=("candidate",))
    engine.validate_groups(groups, panels["close"].columns)
    input_paths = [calendar_file]
    for symbol in panels["close"].columns:
        input_paths.extend([DATA / "1d" / f"{symbol}.parquet",
                            DATA / "adj_factor" / f"{symbol}.parquet"])
    calendar = calendar[calendar >= panels["close"].index.min()]
    if len(panels["close"].index.difference(calendar)):
        raise ValueError("candidate calendar differs from exchange calendar")
    panels = {key: panel.reindex(calendar) for key, panel in panels.items()}
    feature_panels = {key: panels[key] for key in ("close", "open", "high", "low", "amount", "volume")}
    input_manifest = {"profile": "daily"}
    if input_profile != "daily":
        from etf_autoresearch_inputs import load_inputs
        feature_panels, input_manifest = load_inputs(input_profile, feature_panels, COLD, ROOT)
    score = causal_scores(module, feature_panels, pd.Timestamp("2024-12-31"))
    # Match the formal runner's fixed availability and IC arithmetic.
    known = (panels["close"].notna().rolling(60).sum().eq(60).all(axis=1)
             & panels["volume"].gt(0).all(axis=1) & score.notna().all(axis=1))
    group_score = engine.aggregate(score, groups)
    returns, timing = engine.labels(panels, 2, 5)
    frame, _ = engine.evaluate(group_score, returns, groups, known, timing, 2)
    frame = frame.loc[frame.index >= EVALUATION_START]
    valid = frame.loc[frame.ic.notna()]
    if not ((valid.signal_date < valid.entry_date) & (valid.entry_date < valid.exit_date)).all():
        raise ValueError("signal/label chronology invalid")
    stats = engine.summarize(frame, frame.index, 10)
    yearly = {}
    for year, part in frame.groupby(frame.index.year):
        part = part.copy()
        part.loc[part.exit_date.dt.year.ne(year), "ic"] = np.nan
        yearly[str(year)] = {"n": int(part.ic.count()), "ic": float(part.ic.mean())}
    if time.monotonic() - started > TIME_BUDGET_SECONDS:
        raise TimeoutError("fixed five-minute experiment budget exceeded")
    if digest(candidate_path) != candidate_sha:
        raise ValueError("candidate source changed during evaluation")
    implementation_sha = {str(Path(module.__file__).resolve().relative_to(ROOT)): digest(Path(module.__file__))
                          for module in (engine, etf_mining_referee, etf_rank_utils, canonical_data)}
    result = {
        "status": "SEEN_HISTORY_DISCOVERY_ONLY",
        "candidate": module.CANDIDATE_ID, "family": module.FAMILY,
        "direction": module.DIRECTION, "description": module.DESCRIPTION,
        "n": stats["n"], "ic": stats["ic_mean"],
        "hac_t": stats["ic_hac_t"], "block_t": stats["ic_block_t"],
        "yearly": yearly, "complete_score_days": int(group_score.notna().all(axis=1).sum()),
        "first_signal": str(valid.index.min().date()) if len(valid) else None,
        "last_signal": str(valid.index.max().date()) if len(valid) else None,
        "signal_time": "after China D close", "entry": "D+2 adjusted open",
        "exit": "D+7 adjusted open", "cold_cutoff": str(COLD.date()),
        "candidate_sha256": candidate_sha, "evaluator_sha256": digest(Path(__file__)),
        "input_profile": input_profile, "input_manifest": input_manifest,
        "implementation_sha256": implementation_sha,
        "python_version": sys.version, "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "groups_sha256": digest(GROUPS), "universe_sha256": digest(UNIVERSE),
        "input_sha256": {str(path): digest(path) for path in input_paths},
        "benchmark": "specified by cycle --baseline; this evaluator does not select a baseline",
        "command": [sys.executable, *sys.argv],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "evidence_limit": "adaptive search on seen history; not independent confirmation",
    }
    group_score.loc[group_score.index >= EVALUATION_START].to_csv(
        out / "group_scores.csv", index_label="signal_date")
    frame[["signal_date", "entry_date", "exit_date", "ic"]].to_csv(out / "daily_ic.csv", index=False)
    (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    # Local-only append-only experiment record; the caller decides keep/discard.
    append_result(output_root, [run_id, result["candidate_sha256"], result["evaluator_sha256"],
                                str(result["n"]), f'{result["ic"]:.9f}', f'{result["hac_t"]:.6f}',
                                result["family"], "evaluated"])
    return result


def run(run_id: str, output_root: Path, candidate_path: Path | None = None,
        input_profile: str = "daily") -> dict:
    """Enforce the experiment budget even when candidate.score never returns."""
    if signal.getitimer(signal.ITIMER_REAL)[0] > 0:
        raise RuntimeError("an existing process timer prevents the fixed experiment budget")
    previous_handler = signal.getsignal(signal.SIGALRM)

    def on_timeout(_signum, _frame):
        raise TimeoutError("fixed five-minute experiment budget exceeded")

    signal.signal(signal.SIGALRM, on_timeout)
    signal.setitimer(signal.ITIMER_REAL, TIME_BUDGET_SECONDS)
    try:
        if candidate_path is None and input_profile == "daily":
            return _run_with_budget(run_id, output_root)
        return _run_with_budget(run_id, output_root, candidate_path, input_profile)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-root", type=Path,
                        default=ROOT / "runtime_outputs/etf_autoresearch_ic")
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    try:
        print(json.dumps(run(args.run_id, args.output_root), ensure_ascii=False, indent=2))
    except Exception:
        append_result(args.output_root, [args.run_id, digest(CANDIDATE), digest(Path(__file__)),
                                         "0", "", "", "", "crash"])
        raise
