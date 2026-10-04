#!/usr/bin/env python3
"""Forward-only paper H5 sleeves from the already-frozen ETF monthly v4 choice.

This script never selects factors, edits the v4 contract/ledgers, or places an
order.  Its 10 bp/side result is an illustrative sensitivity, not account P&L.
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
sys.path.insert(0, str(Path(__file__).resolve().parent))

from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as discovery
from etf_strategy.core.etf_ic_monthly_factory import load_contract, verify_contract_files
from etf_strategy.core.etf_rank_utils import stable_rank
import build_etf_ic_monthly_panel as panel_builder

CONFIG = ETF / "configs/etf_personal_paper_v1.yaml"
FREEZES = ROOT / "runtime_outputs/etf_rotation_research/monthly_factory/freezes"
OUTPUT = ROOT / "runtime_outputs/etf_rotation_research/personal_paper_v1"
DATA_ROOT = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
UNIVERSE = ROOT / "config/etf_rotation_universe_v1.json"
GROUPS = ETF / "configs/etf_candidate14_economic_groups_v1.yaml"


def _digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode()).hexdigest()


def validate_paper_config(config: dict, contract: dict) -> None:
    fixed = {
        "version": "etf_personal_paper_v1", "purpose": "forward_only_observation_not_trade_authority",
        "first_freeze_month": "2026-09",
        "first_evaluation_month": "2026-10", "signal_time": "close_D",
        "entry_lag": 2, "horizon": 5, "selected_groups": 2,
        "group_rank": "mean_of_selected_factors_stable_eight_group_ranks",
        "group_tie_break": "group_id_ascending", "member_weight": "equal_within_fixed_group",
        "daily_sleeve_fraction": 0.2, "zero_selection": "cash",
        "opening_fill_proxy": "first_09_31_minute_volume_positive_and_daily_open_valid",
        "missed_entry": "leave_member_allocation_in_cash",
        "missed_exit": "unpriced_no_monthly_return",
        "price_basis": "adjusted_open_total_return_proxy_raw_open_for_fill_audit",
        "illustrative_cost_bps_per_side": 10,
        "cost_interpretation": "fixed_sensitivity_only_not_personal_brokerage_cost",
        "benchmark": ["B8_equal_groups", "B14_equal_members"],
        "result_interpretation": "realized_h5_sleeve_pnl_over_fixed_reference_capital_not_compounded_account_equity",
    }
    bad = [key for key, value in fixed.items() if config.get(key) != value]
    if bad:
        raise ValueError(f"paper v1 fixed definition changed: {bad}")
    if config["parent_contract"] != "frameworks/etf_rotation/configs/etf_ic_monthly_factory_v4.yaml":
        raise ValueError("paper must read frozen v4 contract")
    if (contract["signal_time"], contract["entry_lag"], contract["horizon"]) != ("close_D", 2, 5):
        raise ValueError("v4 time contract changed")
    if contract["max_selected"] != 2:
        raise ValueError("v4 selection count changed")


def validate_freeze(frozen: dict, contract: dict, contract_digest: str) -> str:
    if frozen.get("process_version") != contract["process_version"] or frozen.get("contract_sha256") != contract_digest:
        raise ValueError("freeze belongs to another v4 contract")
    period = pd.Period(frozen["freeze_month"], freq="M")
    if period < pd.Period("2026-09", freq="M") or frozen.get("evaluation_month") != str(period + 1):
        raise ValueError("freeze/evaluation month relationship changed")
    if frozen.get("train_end") != str(period.end_time.normalize().date()):
        raise ValueError("freeze training end changed")
    selected = list(frozen["selected_candidates"])
    if len(selected) > 2 or len(selected) != len(set(selected)) or not set(selected) <= set(contract["candidate_catalog"]):
        raise ValueError("freeze selected candidates invalid")
    if frozen.get("candidate_catalog_sha256") != _canonical_digest(contract["candidate_catalog"]):
        raise ValueError("freeze catalog hash mismatch")
    return frozen["evaluation_month"]


def rank_basket(score_map: dict[str, pd.DataFrame], selected: list[str],
                signal_date: pd.Timestamp, groups: dict) -> list[str]:
    """Average selected frozen-direction ranks, then take fixed top two groups."""
    if not selected:
        return []
    ranks = []
    for name in selected:
        if name not in score_map:
            raise ValueError(f"selected factor score missing: {name}")
        frame = score_map[name]
        if signal_date not in frame.index or list(frame.columns) != list(groups):
            raise ValueError(f"selected factor has no fixed-eight score at {signal_date}: {name}")
        row = frame.loc[[signal_date]]
        if row.isna().any().any():
            return []  # no ranking without all eight fixed groups
        ranks.append(stable_rank(row).iloc[0])
    average = pd.concat(ranks, axis=1).mean(axis=1)
    return sorted(groups, key=lambda group: (-average[group], group))[:2]


def opening_volume(minute: pd.DataFrame) -> pd.Series:
    """First regular minute is 09:31 in this store; proxy, not fill proof."""
    if not {"datetime", "volume"} <= set(minute):
        raise ValueError("minute source missing opening volume fields")
    times = pd.to_datetime(minute["datetime"])
    first = minute.loc[times.dt.hour.eq(9) & times.dt.minute.eq(31), ["volume"]].copy()
    first.index = times.loc[first.index].dt.normalize().to_numpy()
    if (first.index.has_duplicates or first.volume.isna().any() or
            not np.isfinite(first.volume.to_numpy(dtype=float)).all() or first.volume.lt(0).any()):
        raise ValueError("invalid first-minute opening volume")
    return first.volume.astype(float)


def _can_fill(date: pd.Timestamp, symbol: str, raw_open: pd.DataFrame,
              raw_volume: pd.DataFrame, first_volume: pd.DataFrame) -> bool:
    if date not in raw_open.index or date not in first_volume.index:
        return False
    price = raw_open.at[date, symbol]
    volume = raw_volume.at[date, symbol]
    minute = first_volume.at[date, symbol]
    return bool(np.isfinite(price) and price > 0 and np.isfinite(volume) and volume > 0
                and np.isfinite(minute) and minute > 0)


def paper_rows(frozen: dict, score_map: dict[str, pd.DataFrame], groups: dict,
               label_dates: pd.DataFrame, adjusted_open: pd.DataFrame,
               raw_open: pd.DataFrame, raw_volume: pd.DataFrame,
               first_volume: pd.DataFrame, as_of: pd.Timestamp,
               sleeve: float = 0.2, cost_bps: float = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fixed-notional H5 sleeves; unresolved exits make monthly P&L unavailable."""
    month = pd.Period(frozen["evaluation_month"], freq="M")
    dates = label_dates.index[label_dates.index.to_period("M") == month]
    if not len(dates) or as_of <= month.end_time.normalize():
        raise ValueError("evaluation month has not fully closed")
    timing = label_dates.loc[dates]
    if timing.exit_date.isna().any() or timing.exit_date.gt(as_of).any():
        raise ValueError("evaluation month H5 labels have not all matured")
    if not ((timing.index < timing.entry_date) & (timing.entry_date < timing.exit_date)).all():
        raise ValueError("signal < D+2 entry < D+7 exit violated")
    selected = list(frozen["selected_candidates"])
    legs, cohorts = [], []
    for signal_date, entry_exit in timing.iterrows():
        entry, exit_ = entry_exit.entry_date, entry_exit.exit_date
        chosen = rank_basket(score_map, selected, signal_date, groups)
        signal_status = ("NO_SELECTED_FACTORS_CASH" if not selected else
                         "INCOMPLETE_SELECTED_SCORE_CASH" if not chosen else "RANKED")
        member_returns = adjusted_open.loc[exit_].div(adjusted_open.loc[entry]).sub(1)
        if member_returns.isna().any() or not np.isfinite(member_returns).all():
            raise ValueError("B8/B14 research price missing on a matured H5 label")
        group_returns = pd.Series({g: member_returns[spec["members"]].mean() for g, spec in groups.items()})
        b8 = float(group_returns.mean())
        b14 = float(member_returns.mean())
        for group in chosen:
            members = groups[group]["members"]
            weight = sleeve / (2 * len(members))
            for symbol in members:
                status = "CLOSED"
                if not _can_fill(entry, symbol, raw_open, raw_volume, first_volume):
                    status = "MISSED_ENTRY"
                elif not _can_fill(exit_, symbol, raw_open, raw_volume, first_volume):
                    status = "UNPRICED_EXIT"
                one_way_turnover = 0.0 if status == "MISSED_ENTRY" else weight * (1 if status == "UNPRICED_EXIT" else 2)
                gross = (weight * float(member_returns[symbol]) if status == "CLOSED"
                         else 0.0 if status == "MISSED_ENTRY" else None)
                cost = one_way_turnover * cost_bps / 10000
                legs.append({"signal_date": signal_date, "entry_date": entry, "exit_date": exit_,
                             "group": group, "symbol": symbol, "account_weight": weight,
                             "status": status, "raw_entry_open": raw_open.at[entry, symbol],
                             "raw_exit_open": raw_open.at[exit_, symbol],
                             "first_minute_entry_volume": first_volume.at[entry, symbol] if entry in first_volume.index else None,
                             "first_minute_exit_volume": first_volume.at[exit_, symbol] if exit_ in first_volume.index else None,
                             "adjusted_open_h5_return": float(member_returns[symbol]) if status == "CLOSED" else None,
                             "executed_one_way_turnover": one_way_turnover,
                             "gross_account_contribution": gross,
                             "illustrative_cost_account_contribution": cost,
                             "illustrative_net_account_contribution": gross - cost if gross is not None else None})
        current = [row for row in legs if row["signal_date"] == signal_date]
        unresolved = sum(row["status"] == "UNPRICED_EXIT" for row in current)
        gross = sum(row["gross_account_contribution"] for row in current) if not unresolved else None
        cost = sum(row["illustrative_cost_account_contribution"] for row in current)
        turnover = sum(row["executed_one_way_turnover"] for row in current)
        cohorts.append({"signal_date": signal_date, "entry_date": entry, "exit_date": exit_,
                        "selected_factors": "|".join(selected), "selected_groups": "|".join(chosen),
                        "signal_status": signal_status,
                        "n_closed": sum(row["status"] == "CLOSED" for row in current),
                        "n_missed_entry": sum(row["status"] == "MISSED_ENTRY" for row in current),
                        "n_unpriced_exit": unresolved,
                        "executed_one_way_turnover": turnover,
                        "gross_account_contribution": gross,
                        "illustrative_cost_account_contribution": cost,
                        "illustrative_net_account_contribution": gross - cost if gross is not None else None,
                        "b8_account_contribution": sleeve * b8,
                        "b14_account_contribution": sleeve * b14})
    return pd.DataFrame(legs), pd.DataFrame(cohorts)


def summarize(cohorts: pd.DataFrame, legs: pd.DataFrame) -> dict:
    unresolved = int(cohorts.n_unpriced_exit.sum())
    gross = None if unresolved else float(cohorts.gross_account_contribution.sum())
    turnover = float(cohorts.executed_one_way_turnover.sum())
    cost = float(cohorts.illustrative_cost_account_contribution.sum())
    b8 = float(cohorts.b8_account_contribution.sum())
    b14 = float(cohorts.b14_account_contribution.sum())
    return {"n_signal_sleeves": len(cohorts), "n_closed_legs": int((legs.status == "CLOSED").sum()) if len(legs) else 0,
            "n_missed_entry_legs": int(cohorts.n_missed_entry.sum()), "n_unpriced_exit_legs": unresolved,
            "executed_one_way_turnover_account": turnover,
            "gross_account_pnl_contribution": gross,
            "illustrative_10bp_net_account_pnl_contribution": gross - cost if gross is not None else None,
            "b8_gross_account_pnl_contribution": b8, "b14_gross_account_pnl_contribution": b14,
            "gross_minus_b8": gross - b8 if gross is not None else None,
            "gross_minus_b14": gross - b14 if gross is not None else None,
            "break_even_cost_bps_per_side_vs_b8": (10000 * (gross - b8) / turnover
                                                    if gross is not None and turnover else None),
            "break_even_cost_bps_per_side_vs_b14": (10000 * (gross - b14) / turnover
                                                     if gross is not None and turnover else None),
            "status": "UNPRICED_MONTHLY_RESULT" if unresolved else "PAPER_H5_SLEEVES_CLOSED"}


def _raw_prices_and_opening_volume(symbols: list[str], as_of: pd.Timestamp,
                                   calendar: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    opens, volumes, firsts = {}, {}, {}
    for symbol in symbols:
        daily = pd.read_parquet(DATA_ROOT / "1d" / f"{symbol}.parquet",
                                columns=["trade_date", "open", "volume"],
                                filters=[("trade_date", "<=", as_of)])
        daily.trade_date = pd.to_datetime(daily.trade_date)
        daily = daily.set_index("trade_date")
        if daily.index.has_duplicates:
            raise ValueError(f"duplicate daily trading date: {symbol}")
        opens[symbol] = daily.open.reindex(calendar)
        volumes[symbol] = daily.volume.reindex(calendar)
        minute = pd.read_parquet(DATA_ROOT / "1m" / f"{symbol}.parquet",
                                 columns=["datetime", "volume"],
                                 filters=[("datetime", "<=", as_of + pd.Timedelta(days=1))])
        firsts[symbol] = opening_volume(minute).reindex(calendar)
    return pd.DataFrame(opens, index=calendar), pd.DataFrame(volumes, index=calendar), pd.DataFrame(firsts, index=calendar)


def input_hashes(symbols: list[str]) -> dict[str, str]:
    """Bind local paper evidence to exact ETF, adjustment, and fill-proxy bytes."""
    files = [DATA_ROOT / "1d/510300.SH.parquet"]
    for symbol in symbols:
        files.extend(DATA_ROOT / sub / f"{symbol}.parquet" for sub in ("1d", "adj_factor", "1m"))
    return {str(path): _digest(path) for path in sorted(set(files))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--freeze-root", type=Path, default=FREEZES)
    parser.add_argument("--output-root", type=Path, default=OUTPUT)
    args = parser.parse_args()
    paper_config = yaml.safe_load(args.config.read_text())
    parent_path = ROOT / paper_config["parent_contract"]
    contract, contract_digest = load_contract(parent_path)
    verify_contract_files(contract, ROOT)
    validate_paper_config(paper_config, contract)
    freeze_paths = sorted(args.freeze_root.glob("*/freeze.json"))
    if not freeze_paths:
        print("NOOP: no frozen v4 month exists")
        return
    calendar_raw = pd.read_parquet(DATA_ROOT / "1d/510300.SH.parquet", columns=["trade_date"])
    as_of = pd.to_datetime(calendar_raw.trade_date).max().normalize()
    pending = []
    for freeze_path in freeze_paths:
        frozen = json.loads(freeze_path.read_text())
        month = validate_freeze(frozen, contract, contract_digest)
        if as_of <= pd.Period(month, freq="M").end_time.normalize():
            continue
        output = args.output_root / f"{frozen['freeze_month']}_{month}"
        if not output.exists():
            pending.append((freeze_path, frozen, output))
    if not pending:
        print("NOOP: no closed, unprocessed evaluation month")
        return
    built = panel_builder.build(str(as_of.date()), str(parent_path))
    panel_builder.run_reproducibility_gate(built, list(contract["candidate_catalog"]))
    universe = json.loads(UNIVERSE.read_text())
    groups = yaml.safe_load(GROUPS.read_text())["groups"]
    symbols = [row["ts_code"] for row in universe["etfs"] if row["role"] == "candidate"]
    discovery.validate_groups(groups, symbols)
    adjusted = load_canonical_daily(DATA_ROOT, UNIVERSE, as_of=str(as_of.date()), roles=("candidate",))
    calendar = built["label_dates"].index
    adjusted_open = adjusted["open"].reindex(calendar)
    raw_open, raw_volume, first_volume = _raw_prices_and_opening_volume(symbols, as_of, calendar)
    inputs_sha256 = input_hashes(symbols)
    sources_sha256 = {str(path): _digest(path) for path in (
        Path(__file__), Path(panel_builder.__file__),
        ETF / "src/etf_strategy/canonical_data.py",
        ETF / "src/etf_strategy/core/etf_group_discovery.py",
        ETF / "src/etf_strategy/core/etf_group_daily_rounds.py",
        ETF / "src/etf_strategy/core/etf_group_sources.py",
        ETF / "src/etf_strategy/core/etf_rank_utils.py",
    )}
    for freeze_path, frozen, output in pending:
        month = frozen["evaluation_month"]
        dates = built["label_dates"].index[built["label_dates"].index.to_period("M") == pd.Period(month)]
        if not len(dates) or built["label_dates"].loc[dates, "exit_date"].isna().any() or \
                built["label_dates"].loc[dates, "exit_date"].gt(as_of).any():
            print(f"NOOP: {month} H5 labels have not fully matured")
            continue
        legs, cohorts = paper_rows(frozen, built["scores"], groups, built["label_dates"],
                                   adjusted_open, raw_open, raw_volume, first_volume, as_of)
        summary = summarize(cohorts, legs)
        output.mkdir(parents=True, exist_ok=False)
        legs.to_csv(output / "legs.csv", index=False)
        cohorts.to_csv(output / "cohorts.csv", index=False)
        manifest = {"version": paper_config["version"], "freeze_month": frozen["freeze_month"],
                    "evaluation_month": month, "as_of": str(as_of.date()), "summary": summary,
                    "selected_factors": frozen["selected_candidates"], "paper_config_sha256": _digest(args.config),
                    "v4_contract_file_sha256": _digest(parent_path), "v4_contract_sha256": contract_digest,
                    "freeze_sha256": _digest(freeze_path), "source_sha256": sources_sha256,
                    "input_sha256": inputs_sha256,
                    "population_file_sha256": _digest(UNIVERSE), "groups_sha256": _digest(GROUPS),
                    "score_source": "v4 panel builder rebuilt under reproducibility gate",
                    "fill_proxy": "09:31 first-minute positive volume; exact daily open fill not proved",
                    "return_status": "H5 paper sleeve contributions, not compounded account equity or actual net return",
                    "benchmark": "same-day fixed B8/B14 adjusted open(D+2)->open(D+7)",
                    "command": [sys.executable, *sys.argv]}
        (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"output": str(output), "summary": summary}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
