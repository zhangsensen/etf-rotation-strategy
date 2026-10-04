#!/usr/bin/env python3
"""Descriptive, hindsight-catalog ETF H5 paper replay; never an official v4 evaluation."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_saved_etf_ic_history as audit
import run_etf_personal_paper_v1 as paper
from etf_strategy.core import etf_group_discovery as discovery
from etf_strategy.core.etf_mining_referee import newey_west_t_calendar

ROOT = paper.ROOT
ETF = paper.ETF
CONFIG = ETF / "configs/etf_personal_paper_history_v1.yaml"
OUTPUT = ROOT / "runtime_outputs/etf_rotation_research/personal_paper_history_v1"
EXPECTED = {
    "version": "etf_personal_paper_history_v1",
    "purpose": "descriptive_hindsight_catalog_counterfactual_not_pit_strategy",
    "catalog": "frameworks/etf_rotation/configs/etf_ic_lead_watch_v2.yaml",
    "parent_paper": "frameworks/etf_rotation/configs/etf_personal_paper_v1.yaml",
    "historical_ic_source": "runtime_outputs/etf_rotation_research/history_value_20260925_cold_v2",
    "first_signal": "2024-01-01", "last_as_of": "2026-03-24",
    "signal_time": "close_D", "entry_lag": 2, "horizon": 5,
    "factor_policy": "every_basic_ic_lead_separately_no_selection",
    "selected_groups": 2, "daily_sleeve_fraction": 0.2,
    "illustrative_cost_bps_per_side": 10,
    "theoretical_basis": "adjusted_open_no_fill_filter",
    "fill_aware_basis": "adjusted_open_with_0931_positive_volume_proxy",
    "partial_month": "include_all_matured_signals_mark_partial",
    "year_partition": "signal_year_includes_cross_year_exits",
}


def validate_config(config: dict) -> None:
    if config != EXPECTED:
        raise ValueError("historical replay v1 fixed definition changed")


def replay_rows(candidate: str, score: pd.DataFrame, groups: dict,
                dates: pd.DataFrame, adjusted_open: pd.DataFrame,
                raw_open: pd.DataFrame, raw_volume: pd.DataFrame,
                first_volume: pd.DataFrame, as_of: pd.Timestamp,
                sleeve: float = .2, cost_bps: float = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Use the forward paper mapping on every mature date, including partial March."""
    selected = [candidate]
    if dates.empty or dates.exit_date.isna().any() or dates.exit_date.gt(as_of).any():
        raise ValueError("all replayed H5 exits must mature by cold as_of")
    if not ((dates.index < dates.entry_date) & (dates.entry_date < dates.exit_date)).all():
        raise ValueError("signal < entry < exit violated")
    legs, cohorts = [], []
    for signal, time in dates.iterrows():
        entry, exit_ = time.entry_date, time.exit_date
        chosen = paper.rank_basket({candidate: score}, selected, signal, groups)
        returns = adjusted_open.loc[exit_].div(adjusted_open.loc[entry]).sub(1)
        if returns.isna().any() or not np.isfinite(returns).all():
            raise ValueError("incomplete 14-member adjusted-open H5 label")
        b8 = float(np.mean([returns[spec["members"]].mean() for spec in groups.values()]))
        b14 = float(returns.mean())
        theoretical = float(np.mean([returns[groups[g]["members"]].mean() for g in chosen])) if chosen else 0.0
        signal_legs = []
        for group in chosen:
            members = groups[group]["members"]
            weight = sleeve / (2 * len(members))
            for symbol in members:
                status = ("MISSED_ENTRY" if not paper._can_fill(entry, symbol, raw_open, raw_volume, first_volume)
                          else "UNPRICED_EXIT" if not paper._can_fill(exit_, symbol, raw_open, raw_volume, first_volume)
                          else "CLOSED")
                turnover = 0.0 if status == "MISSED_ENTRY" else weight * (1 if status == "UNPRICED_EXIT" else 2)
                gross = weight * float(returns[symbol]) if status == "CLOSED" else 0.0 if status == "MISSED_ENTRY" else None
                cost = turnover * cost_bps / 10000
                signal_legs.append({"candidate": candidate, "signal_date": signal, "entry_date": entry,
                                    "exit_date": exit_, "group": group, "symbol": symbol,
                                    "account_weight": weight, "status": status,
                                    "raw_entry_open": raw_open.at[entry, symbol],
                                    "raw_exit_open": raw_open.at[exit_, symbol],
                                    "first_minute_entry_volume": first_volume.at[entry, symbol],
                                    "first_minute_exit_volume": first_volume.at[exit_, symbol],
                                    "adjusted_open_h5_return": float(returns[symbol]) if status == "CLOSED" else None,
                                    "theoretical_adjusted_open_h5_return": float(returns[symbol]),
                                    "executed_one_way_turnover": turnover,
                                    "gross_account_contribution": gross,
                                    "illustrative_cost_account_contribution": cost,
                                    "illustrative_net_account_contribution": gross - cost if gross is not None else None})
        legs.extend(signal_legs)
        unresolved = sum(row["status"] == "UNPRICED_EXIT" for row in signal_legs)
        gross = sum(row["gross_account_contribution"] for row in signal_legs) if not unresolved else None
        cost = sum(row["illustrative_cost_account_contribution"] for row in signal_legs)
        cohorts.append({"candidate": candidate, "signal_date": signal, "entry_date": entry,
                        "exit_date": exit_, "selected_factors": candidate,
                        "signal_month": str(signal.to_period("M")),
                        "month_status": "PARTIAL_MONTH" if signal.to_period("M") == as_of.to_period("M") else "FULL_MONTH",
                        "selected_groups": "|".join(chosen),
                        "signal_status": "RANKED" if chosen else "INCOMPLETE_SELECTED_SCORE_CASH",
                        "n_closed": sum(row["status"] == "CLOSED" for row in signal_legs),
                        "n_missed_entry": sum(row["status"] == "MISSED_ENTRY" for row in signal_legs),
                        "n_unpriced_exit": unresolved,
                        "executed_one_way_turnover": sum(row["executed_one_way_turnover"] for row in signal_legs),
                        "gross_account_contribution": gross,
                        "illustrative_cost_account_contribution": cost,
                        "illustrative_net_account_contribution": gross - cost if gross is not None else None,
                        "theoretical_gross_account_contribution": sleeve * theoretical,
                        "b8_account_contribution": sleeve * b8,
                        "b14_account_contribution": sleeve * b14})
    return pd.DataFrame(legs), pd.DataFrame(cohorts)


def summarize_period(candidate: str, period: str, cohorts: pd.DataFrame,
                     legs: pd.DataFrame, ic_row: dict | None) -> dict:
    base = {"candidate": candidate, "period": period}
    if cohorts.empty:
        return {**base, "status": "UNCOMPUTABLE_PRE2025_SHARE_SOURCE",
                "n_signal_sleeves": 0, "historical_ic": ic_row.get("ic") if ic_row else None,
                "historical_hac_t": ic_row.get("hac_t") if ic_row else None,
                "historical_ic_n": ic_row.get("n") if ic_row else 0,
                "historical_ic_source": ic_row.get("source") if ic_row else None,
                "historical_ic_window": ic_row.get("window") if ic_row else None}
    fill = paper.summarize(cohorts, legs)
    theoretical = float(cohorts.theoretical_gross_account_contribution.sum())
    b8 = float(cohorts.b8_account_contribution.sum())
    b14 = float(cohorts.b14_account_contribution.sum())
    signal_calendar = pd.DatetimeIndex(cohorts.signal_date)
    theoretical_excess = pd.Series(
        (cohorts.theoretical_gross_account_contribution - cohorts.b8_account_contribution).to_numpy(),
        index=signal_calendar)
    theoretical_t = newey_west_t_calendar(theoretical_excess, signal_calendar, 10)
    if fill["n_unpriced_exit_legs"]:
        priced_net_excess, priced_t = None, None
    else:
        net_excess = pd.Series(
            (cohorts.illustrative_net_account_contribution - cohorts.b8_account_contribution).to_numpy(),
            index=signal_calendar)
        priced_net_excess = float(net_excess.sum())
        priced_t = newey_west_t_calendar(net_excess, signal_calendar, 10)
    return {**base, **fill, "status": "UNPRICED_PERIOD_RESULT" if fill["n_unpriced_exit_legs"] else fill["status"],
            "theoretical_adjusted_open_gross_account_contribution": theoretical,
            "theoretical_minus_b8": theoretical - b8,
            "theoretical_minus_b14": theoretical - b14,
            "theoretical_excess_b8_hac_t_lag10_report_only": float(theoretical_t) if pd.notna(theoretical_t) else None,
            "theoretical_excess_b8_hac_n": len(theoretical_excess),
            "illustrative_10bp_net_minus_b8": priced_net_excess,
            "illustrative_10bp_net_excess_b8_hac_t_lag10_report_only": float(priced_t) if priced_t is not None and pd.notna(priced_t) else None,
            "illustrative_10bp_net_excess_b8_hac_n": len(cohorts) if priced_t is not None else 0,
            "n_ranked_signals": int(cohorts.signal_status.eq("RANKED").sum()),
            "historical_ic": ic_row.get("ic") if ic_row else None,
            "historical_hac_t": ic_row.get("hac_t") if ic_row else None,
            "historical_ic_n": ic_row.get("n") if ic_row else None}


def _filtered_frame_sha(frame: pd.DataFrame) -> str:
    """SHA256 of canonical CSV of a cutoff-filtered in-memory frame."""
    return sha256(frame.to_csv(index=True, float_format="%.17g", na_rep="NA",
                               date_format="%Y-%m-%dT%H:%M:%S").encode()).hexdigest()


def run(as_of: str, output: Path, pilot_first_factor: bool = False) -> dict:
    cutoff = pd.Timestamp(as_of)
    if cutoff > audit.MAX_AS_OF or cutoff != cutoff.normalize():
        raise ValueError("historical replay may not read beyond cold 2026-03-24")
    if output.exists():
        raise FileExistsError(output)
    config = yaml.safe_load(CONFIG.read_text())
    validate_config(config)
    paper_config = yaml.safe_load((ROOT / config["parent_paper"]).read_text())
    contract, _ = paper.load_contract(ROOT / paper_config["parent_contract"])
    paper.validate_paper_config(paper_config, contract)
    catalog = yaml.safe_load((ROOT / config["catalog"]).read_text())["candidate_catalog"]
    if len(catalog) != 16 or len(set(catalog)) != 16:
        raise ValueError("exact sixteen-lead catalog required")
    chosen_catalog = catalog[:1] if pilot_first_factor else catalog
    groups = yaml.safe_load(paper.GROUPS.read_text())["groups"]
    universe = json.loads(paper.UNIVERSE.read_text())["etfs"]
    symbols = [row["ts_code"] for row in universe if row["role"] == "candidate"]
    discovery.validate_groups(groups, symbols)
    panels = paper.load_canonical_daily(paper.DATA_ROOT, paper.UNIVERSE,
                                        as_of=as_of, roles=("candidate",))
    raw_calendar = pd.read_parquet(paper.DATA_ROOT / "1d/510300.SH.parquet",
                                   columns=["trade_date"], filters=[("trade_date", "<=", cutoff)])
    calendar = pd.DatetimeIndex(pd.to_datetime(raw_calendar.trade_date)).sort_values()
    if calendar.max() != cutoff or len(panels["close"].index.difference(calendar)):
        raise ValueError("cold calendar mismatch")
    panels = {key: frame.reindex(calendar) for key, frame in panels.items()}
    known = panels["close"].notna().rolling(60).sum().eq(60).all(axis=1) & panels["volume"].gt(0).all(axis=1)
    member_labels, dates = discovery.labels(panels, lag=2, horizon=5)
    eligible = (known & member_labels.notna().all(axis=1) &
                dates.exit_date.notna() & dates.exit_date.le(cutoff) &
                dates.index.to_series().ge(pd.Timestamp(config["first_signal"])))
    dates = dates.loc[eligible]
    adjusted = panels["open"]
    raw_open, raw_volume, first_volume = paper._raw_prices_and_opening_volume(symbols, cutoff, calendar)
    ic_root = ROOT / config["historical_ic_source"]
    saved_manifest = json.loads((ic_root / "manifest.json").read_text())
    if saved_manifest.get("as_of") != as_of or [row["candidate"] for row in saved_manifest["reproducibility"]] != catalog:
        raise ValueError("historical IC source catalog/cutoff mismatch")
    yearly = pd.read_csv(ic_root / "yearly_ic.csv")
    daily_ic = pd.read_csv(ic_root / "daily_ic.csv", index_col="signal_date", parse_dates=True)
    if set(yearly.candidate) != set(catalog) or list(daily_ic) != catalog:
        raise ValueError("historical IC source candidate mismatch")
    prior_h5_path = ROOT / "runtime_outputs/etf_rotation_research/horizon_profile_20260925_cold_final/horizon_ic.csv"
    prior_h5 = pd.read_csv(prior_h5_path)
    prior_share = prior_h5.loc[prior_h5.candidate.eq("range_flow_20_40_1") &
                                prior_h5.horizon.eq(5) & prior_h5.as_of.eq(as_of)]
    if len(prior_share) != 1:
        raise ValueError("missing cold prior H5 IC for uncomputable share replay")
    prior_share = prior_share.iloc[0]
    all_legs, all_cohorts, summary, repro = [], [], [], []
    for candidate in chosen_catalog:
        score = audit._score(candidate, panels, groups)
        if score is None:
            for period in ("2024", "2025", "2026_COLD", "FULL_COLD"):
                prior = ({"ic": float(prior_share.ic), "hac_t": float(prior_share.hac_t),
                          "n": int(prior_share.n), "source": str(prior_h5_path),
                          "window": "2025-01-01..2026-03-24"} if period == "FULL_COLD" else None)
                summary.append(summarize_period(candidate, period, pd.DataFrame(), pd.DataFrame(), prior))
            repro.append({"candidate": candidate, "status": "UNCOMPUTABLE_PRE2025_SHARE_SOURCE"})
            continue
        score = score.reindex(calendar)[list(groups)]
        saved = audit.read_csv_through(audit._source_score(candidate), calendar, as_of)[list(groups)]
        common = saved.index.intersection(score.index)
        mismatch = saved.loc[common].isna().ne(score.loc[common].isna()) | (
            (saved.loc[common] - score.loc[common]).abs() > 1e-9 * saved.loc[common].abs().clip(lower=1e-12))
        count = int(mismatch.to_numpy().sum())
        if count:
            raise ValueError(f"saved score mismatch: {candidate}: {count} cells")
        repro.append({"candidate": candidate, "status": "MATCH", "compared_dates": len(common),
                      "mismatch_cells": 0, "archived_score_filtered_sha256": _filtered_frame_sha(saved)})
        legs, cohorts = replay_rows(candidate, score, groups, dates, adjusted,
                                    raw_open, raw_volume, first_volume, cutoff)
        all_legs.append(legs)
        all_cohorts.append(cohorts)
        for period, mask in (("2024", cohorts.signal_date.dt.year.eq(2024)),
                             ("2025", cohorts.signal_date.dt.year.eq(2025)),
                             ("2026_COLD", cohorts.signal_date.dt.year.eq(2026)),
                             ("FULL_COLD", pd.Series(True, index=cohorts.index))):
            part = cohorts.loc[mask]
            part_legs = legs.loc[legs.signal_date.isin(part.signal_date)]
            if period == "FULL_COLD":
                values = daily_ic[candidate].reindex(calendar)
                t = newey_west_t_calendar(values, calendar, 10)
                ic_row = {"n": int(values.notna().sum()), "ic": float(values.mean()),
                          "hac_t": float(t) if pd.notna(t) else None}
            else:
                y = period[:4]
                match = yearly.loc[yearly.candidate.eq(candidate) & yearly.period.astype(str).eq(y)]
                if len(match) != 1:
                    raise ValueError(f"missing annual IC reference: {candidate} {y}")
                ic_row = match.iloc[0].to_dict()
            summary.append(summarize_period(candidate, period, part, part_legs, ic_row))
    output.mkdir(parents=True, exist_ok=False)
    pd.concat(all_legs, ignore_index=True).to_csv(output / "legs.csv", index=False)
    pd.concat(all_cohorts, ignore_index=True).to_csv(output / "cohorts.csv", index=False)
    pd.DataFrame(summary).to_csv(output / "summary.csv", index=False)
    inputs = {name: _filtered_frame_sha(frame) for name, frame in {
        **{f"adjusted_{key}_through_{as_of}": value for key, value in panels.items()},
        f"raw_open_through_{as_of}": raw_open,
        f"raw_volume_through_{as_of}": raw_volume,
        f"first_0931_volume_through_{as_of}": first_volume}.items()}
    paths = [CONFIG, ROOT / config["catalog"], ROOT / config["parent_paper"],
             ROOT / paper_config["parent_contract"], paper.UNIVERSE, paper.GROUPS,
             Path(__file__), Path(audit.__file__), Path(paper.__file__),
             Path(audit.monthly.__file__), Path(audit.extra.__file__),
             ETF / "src/etf_strategy/canonical_data.py",
             ETF / "src/etf_strategy/core/etf_group_discovery.py",
             ETF / "src/etf_strategy/core/etf_group_daily_rounds.py",
             ETF / "src/etf_strategy/core/etf_group_claude_rounds.py",
             ETF / "src/etf_strategy/core/etf_group_daily_outcome.py",
             ETF / "src/etf_strategy/core/etf_group_sources.py",
             ETF / "src/etf_strategy/core/etf_mining_referee.py",
             ETF / "src/etf_strategy/core/etf_rank_utils.py",
             ic_root / "manifest.json", ic_root / "yearly_ic.csv", ic_root / "daily_ic.csv",
             prior_h5_path,
             *[audit._source_score(candidate).parent / "PLAN.json" for candidate in catalog]]
    manifest = {"version": config["version"], "as_of": as_of,
                "catalog_status": "HINDSIGHT_SELECTED_16_BASIC_IC_LEADS_NOT_PIT_STRATEGY",
                "pilot_engineering_smoke_only": pilot_first_factor,
                "catalog": chosen_catalog, "full_catalog_size": len(catalog),
                "signal": "close(D)", "paper_h5": "adjusted_open(D+2)->adjusted_open(D+7)",
                "population": "fixed14_eight_groups", "selection": "none; each catalog factor independently Top2",
                "signal_year": "cross-year exits included in replay; IC yearly source purges cross-year exits",
                "month_status": "2026-03 PARTIAL_MONTH; only H5-matured signals through cutoff",
                "theoretical_status": "adjusted-open research-price counterfactual, not fill or actual account PnL",
                "fill_status": "09:31 positive-volume proxy; exact open fill unproved; any unpriced exit nulls period fill-aware return",
                "illustrative_cost": "10bp per side, sensitivity only, not personal account cost",
                "return_unit": "sum of daily 0.2-notional H5 sleeve contributions, not compounded account equity",
                "benchmark": "same signal dates B8/B14 adjusted-open H5, 0.2 daily sleeve",
                "reproducibility": repro, "source_sha256": {str(path): paper._digest(path) for path in paths},
                "input_sha256": inputs,
                "input_hash_rule": "SHA256 cutoff-filtered in-memory DataFrame.to_csv(index=True,float_format='%.17g',na_rep='NA',date_format='%Y-%m-%dT%H:%M:%S'); no post-cutoff data hashed",
                "score_reconstruction": "2024 scores recomputed with today's frozen formulas; archived source-score overlap is mainly 2025 onward, so 2024 is not an archived PIT signal reproduction",
                "eligible_signal_dates": len(dates),
                "command": [sys.executable, *sys.argv]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    return {"output": str(output), "factors": len(chosen_catalog), "signals_per_factor": len(dates),
            "first_signal": str(dates.index.min().date()), "last_signal": str(dates.index.max().date()),
            "uncomputable": sum(row["status"] != "MATCH" for row in repro)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", default="2026-03-24")
    parser.add_argument("--pilot-first-factor", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or OUTPUT / ("pilot_first_factor_cold_20260324" if args.pilot_first_factor
                                    else "all16_cold_20260324")
    print(json.dumps(run(args.as_of, output, args.pilot_first_factor), ensure_ascii=False))


if __name__ == "__main__":
    main()
