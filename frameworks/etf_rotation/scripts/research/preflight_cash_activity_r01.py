#!/usr/bin/env python3
"""Label-free draft coverage and old-score comparison for cash activity round 1."""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import StringIO
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
from etf_strategy.core.etf_rank_utils import stable_rank

SOURCE = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
UNIVERSE = ROOT / "config/etf_rotation_universe_v1.json"
GROUPS = ETF / "configs/etf_candidate14_economic_groups_v1.yaml"
INVENTORY = ROOT / "runtime_outputs/etf_rotation_research/ic_inventory_20260925_533_v1/all_factors.csv"
RUNS = ROOT / "runtime_outputs/etf_rotation_research/runs"
PROPOSAL = ETF / "docs/ETF_IC_CAMPAIGN20_PROPOSAL_20260926.md"
CUTOFF = pd.Timestamp("2026-03-24")
START = pd.Timestamp("2023-07-27")
EVALUATION = pd.Timestamp("2025-01-01")
WINDOW = 60


def feature_scores(close: pd.DataFrame, cash_turnover: pd.Series, groups: dict) -> dict[str, pd.DataFrame]:
    """Every beta ends D-1; x_D appears only in the final score multiplier."""
    if not close.index.equals(cash_turnover.index) or close.index.has_duplicates:
        raise ValueError("unaligned cash/ETF calendar")
    if cash_turnover.le(0).any():
        raise ValueError("cash turnover must be positive")
    returns = close.pct_change(fill_method=None)
    shock = np.log(cash_turnover).diff()
    complete = returns.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW)
    complete &= shock.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW).to_numpy()[:, None]

    variance = shock.rolling(WINDOW, min_periods=WINDOW).var(ddof=0).where(lambda x: x.gt(0))
    same_beta = returns.rolling(WINDOW, min_periods=WINDOW).cov(shock, ddof=0).div(variance, axis=0)
    same = same_beta.where(complete).shift(1).mul(shock, axis=0)

    old_shock = shock.shift(1)
    delayed_complete = complete & old_shock.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW).to_numpy()[:, None]
    old_variance = old_shock.rolling(WINDOW, min_periods=WINDOW).var(ddof=0).where(lambda x: x.gt(0))
    delayed_beta = returns.rolling(WINDOW, min_periods=WINDOW).cov(old_shock, ddof=0).div(old_variance, axis=0)
    delayed = delayed_beta.where(delayed_complete).shift(1).mul(shock, axis=0)

    positive = shock.where(shock.gt(0))
    negative = shock.where(shock.lt(0))
    enough = shock.gt(0).rolling(WINDOW, min_periods=WINDOW).sum().ge(10)
    enough &= shock.lt(0).rolling(WINDOW, min_periods=WINDOW).sum().ge(10)
    plus_beta = returns.where(shock.gt(0), axis=0).rolling(WINDOW, min_periods=10).cov(positive, ddof=0)
    plus_beta = plus_beta.div(positive.rolling(WINDOW, min_periods=10).var(ddof=0).where(lambda x: x.gt(0)), axis=0)
    minus_beta = returns.where(shock.lt(0), axis=0).rolling(WINDOW, min_periods=10).cov(negative, ddof=0)
    minus_beta = minus_beta.div(negative.rolling(WINDOW, min_periods=10).var(ddof=0).where(lambda x: x.gt(0)), axis=0)
    plus_beta = plus_beta.where(complete & enough.to_numpy()[:, None]).shift(1)
    minus_beta = minus_beta.where(complete & enough.to_numpy()[:, None]).shift(1)
    signed_beta = plus_beta.where(shock.gt(0), minus_beta.where(shock.lt(0)))
    asymmetric = signed_beta.mul(shock, axis=0)

    atoms = {
        "cash_activity_same_day_response_60": same,
        "cash_activity_delayed_response_60": delayed,
        "cash_activity_sign_asymmetry_60": asymmetric,
    }
    return {name: discovery.aggregate(atom.replace([np.inf, -np.inf], np.nan), groups)[list(groups)]
            for name, atom in atoms.items()}


def read_old_prefix(path: Path, cutoff: pd.Timestamp) -> pd.DataFrame:
    """Stop streaming at cutoff; never parse a saved score after the cold line."""
    with path.open() as handle:
        lines = [handle.readline()]
        for line in handle:
            date = pd.Timestamp(line.split(",", 1)[0])
            if date > cutoff:
                break
            lines.append(line)
    frame = pd.read_csv(StringIO("".join(lines)), index_col=0, parse_dates=True,
                        float_precision="round_trip")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("old score chronology invalid")
    return frame


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    universe = json.loads(UNIVERSE.read_text())
    symbols = [row["ts_code"] for row in universe["etfs"] if row["role"] == "candidate"]
    groups = yaml.safe_load(GROUPS.read_text())["groups"]
    discovery.validate_groups(groups, symbols)
    panels = load_canonical_daily(SOURCE, UNIVERSE, as_of=str(CUTOFF.date()), roles=("candidate",))
    reference = pd.read_parquet(SOURCE / "1d/510300.SH.parquet", columns=["trade_date"],
                                filters=[("trade_date", "<=", CUTOFF)])
    calendar = pd.DatetimeIndex(reference.trade_date).sort_values()
    calendar = calendar[(calendar >= START) & (calendar <= CUTOFF)]
    cash = pd.read_parquet(SOURCE / "1d/511880.SH.parquet",
                           columns=["trade_date", "turnover"],
                           filters=[("trade_date", "<=", CUTOFF)]).set_index("trade_date")["turnover"]
    cash = cash.reindex(calendar)
    close = panels["close"].reindex(calendar)
    scores = feature_scores(close, cash, groups)

    # A changed future, or a strict prefix reload, cannot affect pre-cut scores.
    prefix_cut = pd.Timestamp("2024-12-31")
    prefix = {name: frame.loc[:prefix_cut] for name, frame in
              feature_scores(close.loc[:prefix_cut], cash.loc[:prefix_cut], groups).items()}
    for name, frame in scores.items():
        pd.testing.assert_frame_equal(frame.loc[:prefix_cut], prefix[name],
                                      check_exact=False, rtol=1e-10, atol=1e-12)
    changed_close, changed_cash = close.copy(), cash.copy()
    changed_close.loc[changed_close.index > prefix_cut] *= 1.73
    changed_cash.loc[changed_cash.index > prefix_cut] *= 2.41
    perturbed = feature_scores(changed_close, changed_cash, groups)
    for name, frame in scores.items():
        pd.testing.assert_frame_equal(frame.loc[:prefix_cut], perturbed[name].loc[:prefix_cut],
                                      check_exact=False, rtol=1e-10, atol=1e-12)

    eval_scores = {name: score.loc[EVALUATION:] for name, score in scores.items()}
    coverage = {name: {"complete_eight_group_score_dates": int(score.notna().all(axis=1).sum()),
                       "first_complete": str(score.index[score.notna().all(axis=1)].min().date()),
                       "last_complete": str(score.index[score.notna().all(axis=1)].max().date())}
                for name, score in eval_scores.items()}
    inventory = pd.read_csv(INVENTORY)
    pairs, skipped = [], []
    for row in inventory.to_dict("records"):
        path = RUNS / str(row["source_run"]) / f"scores_{row['candidate']}.csv"
        if not path.exists():
            skipped.append({"candidate": row["candidate"], "reason": "SAVED_SCORE_MISSING"})
            continue
        try:
            old = read_old_prefix(path, CUTOFF)
            if set(old.columns) != set(groups):
                raise ValueError("old score is not eight groups")
            old = old[list(groups)]
            for name, score in eval_scores.items():
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
            skipped.append({"candidate": row["candidate"], "reason": f"{type(exc).__name__}: {str(exc)[:100]}"})
    pair_table = pd.DataFrame(pairs).sort_values(["new_candidate", "mean_abs_daily_rank_corr"],
                                                   ascending=[True, False])
    own_pairs = []
    for i, (left_name, left) in enumerate(eval_scores.items()):
        for right_name, right in list(eval_scores.items())[i + 1:]:
            complete = left.notna().all(axis=1) & right.notna().all(axis=1)
            daily = stable_rank(left.loc[complete]).corrwith(stable_rank(right.loc[complete]), axis=1).dropna()
            own_pairs.append({"left": left_name, "right": right_name, "n": len(daily),
                              "mean_abs_daily_rank_corr": float(daily.abs().mean())})
    output.mkdir(parents=True, exist_ok=False)
    pair_table.to_csv(output / "old_catalog_correlations.csv", index=False)
    pd.DataFrame(own_pairs).to_csv(output / "within_round_correlations.csv", index=False)
    for name, score in eval_scores.items():
        score.to_csv(output / f"scores_{name}.csv", index_label="signal_date")
    nearest = {name: pair_table[pair_table.new_candidate.eq(name)].head(3).to_dict("records")
               for name in eval_scores}
    manifest = {"status": "DRAFT_PRELABEL_NO_H5_LABELS_READ", "as_of": str(CUTOFF.date()),
                "proposal_sha256": sha256(PROPOSAL.read_bytes()).hexdigest(),
                "coverage": coverage, "nearest_old": nearest, "within_round": own_pairs,
                "old_catalog_definitions": len(inventory), "old_comparison_rows": len(pairs),
                "old_score_skips": skipped,
                "prefix_and_future_perturbation": True,
                "command": [sys.executable, *sys.argv]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2,
                                                    allow_nan=False) + "\n")
    return {"output": str(output), "coverage": coverage, "nearest_old": nearest,
            "within_round": own_pairs, "old_comparison_rows": len(pairs),
            "old_score_skips": len(skipped)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
