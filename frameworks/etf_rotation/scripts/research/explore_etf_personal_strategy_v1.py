#!/usr/bin/env python3
"""One frozen historical exploration of two personal ETF rules; no live authority."""
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

ROOT, ETF = paper.ROOT, paper.ETF
CONFIG = ETF / "configs/etf_personal_strategy_explore_v1.yaml"
OUTPUT = ROOT / "runtime_outputs/etf_rotation_research/personal_strategy_explore_v1"
FROZEN_CONFIG_SHA256 = "1c84a671b9c389a143e87df2bf10c6e3b416abd2121a7ecdf600bca6fa0d81e6"
BENCHMARKS = ("strategy", "B8", "B14")


def validate_config(config: dict) -> None:
    if paper._digest(CONFIG) != FROZEN_CONFIG_SHA256:
        raise ValueError("frozen strategy exploration spec hash changed")
    if (config["population"], config["signal_time"], config["cold_as_of"],
            config["illustrative_cost_bps_per_side"]) != (
                "fixed14_eight_groups", "close_D", "2026-03-24", 10):
        raise ValueError("frozen exploration scope changed")


def benchmark_weights(groups: dict) -> tuple[dict[str, float], dict[str, float]]:
    members = [symbol for spec in groups.values() for symbol in spec["members"]]
    b8 = {symbol: 1 / (len(groups) * len(spec["members"]))
          for spec in groups.values() for symbol in spec["members"]}
    b14 = {symbol: 1 / len(members) for symbol in members}
    return b8, b14


def group_weights(selected: list[str], groups: dict) -> dict[str, float]:
    return {symbol: 1 / (len(selected) * len(groups[group]["members"]))
            for group in selected for symbol in groups[group]["members"]} if selected else {}


def first_sessions(calendar: pd.DatetimeIndex, rule: str) -> list[pd.Timestamp]:
    if rule == "week":
        key = list(zip(calendar.isocalendar().year, calendar.isocalendar().week))
    elif rule == "month":
        key = list(calendar.to_period("M"))
    else:
        raise ValueError(rule)
    return [date for i, date in enumerate(calendar) if i == 0 or key[i] != key[i - 1]]


def schedule_weekly(calendar: pd.DatetimeIndex, score: pd.DataFrame, groups: dict,
                    first_date: pd.Timestamp) -> tuple[list[dict], list[dict]]:
    b8, b14 = benchmark_weights(groups)
    positions = {date: i for i, date in enumerate(calendar)}
    intervals, decisions = [], []
    active_exit_index = -1
    for signal in first_sessions(calendar, "week"):
        i = positions[signal]
        if signal < first_date or i + 2 >= len(calendar):
            continue
        entry = calendar[i + 2]
        if i + 2 < active_exit_index:
            decisions.append({"rule": "A_weekly_weekday_top2", "signal_date": signal,
                              "entry_date": entry, "status": "SKIPPED_ACTIVE_SLEEVE"})
            continue
        selected = paper.rank_basket({"factor": score}, ["factor"], signal, groups)
        if not selected:
            decisions.append({"rule": "A_weekly_weekday_top2", "signal_date": signal,
                              "entry_date": entry, "status": "INCOMPLETE_SCORE_CASH"})
            continue
        exit_index = i + 7
        exit_date = calendar[exit_index] if exit_index < len(calendar) else pd.NaT
        active_exit_index = exit_index
        intervals.append({"rule": "A_weekly_weekday_top2", "signal_date": signal,
                          "entry_date": entry, "exit_date": exit_date,
                          "selected_groups": "|".join(selected),
                          "weights": group_weights(selected, groups), "b8_weights": b8,
                          "b14_weights": b14, "status": "PARTIAL_OPEN" if pd.isna(exit_date) else "SCHEDULED"})
        decisions.append({"rule": "A_weekly_weekday_top2", "signal_date": signal,
                          "entry_date": entry, "status": "RANKED",
                          "selected_groups": "|".join(selected)})
    return intervals, decisions


def schedule_monthly(calendar: pd.DatetimeIndex, adjusted_close: pd.DataFrame,
                     groups: dict, first_date: pd.Timestamp) -> tuple[list[dict], list[dict]]:
    b8, b14 = benchmark_weights(groups)
    positions = {date: i for i, date in enumerate(calendar)}
    ratio = adjusted_close.div(adjusted_close.rolling(60, min_periods=60).mean())
    first = [date for date in first_sessions(calendar, "month")
             if date >= first_date and positions[date] + 2 < len(calendar)]
    intervals, decisions = [], []
    for j, signal in enumerate(first):
        entry = calendar[positions[signal] + 2]
        exit_date = calendar[positions[first[j + 1]] + 2] if j + 1 < len(first) else pd.NaT
        row = ratio.loc[signal]
        if row.isna().any() or not np.isfinite(row.to_numpy()).all():
            eligible, status = [], "INCOMPLETE_60_SESSION_WARMUP_CASH"
        else:
            eligible = [group for group, spec in groups.items() if row[spec["members"]].mean() > 1]
            status = "TREND_ELIGIBLE" if eligible else "NO_ELIGIBLE_GROUP_CASH"
        intervals.append({"rule": "B_monthly_absolute_trend", "signal_date": signal,
                          "entry_date": entry, "exit_date": exit_date,
                          "selected_groups": "|".join(eligible),
                          "weights": group_weights(eligible, groups), "b8_weights": b8,
                          "b14_weights": b14, "status": "PARTIAL_OPEN" if pd.isna(exit_date) else "SCHEDULED"})
        decisions.append({"rule": "B_monthly_absolute_trend", "signal_date": signal,
                          "entry_date": entry, "status": status,
                          "selected_groups": "|".join(eligible)})
    return intervals, decisions


def _rebalance(current: dict[str, float], cash: float, opens: pd.Series,
               target_weights: dict[str, float], cost_rate: float,
               can_trade: dict[str, bool] | None) -> tuple[dict[str, float], float, float, str]:
    """Net orders at the scheduled open; blocked buys stay cash, blocked sells invalidate."""
    symbols = set(current) | set(target_weights)
    prior = {symbol: current.get(symbol, 0.0) * float(opens[symbol]) for symbol in symbols}
    before = cash + sum(prior.values())
    if not np.isfinite(before) or before <= 0:
        raise ValueError("nonpositive account NAV")
    blocked_buy = set()
    if can_trade is not None:
        for symbol in symbols:
            intended = target_weights.get(symbol, 0.0) * before
            if intended < prior[symbol] - 1e-10 and not can_trade[symbol]:
                return current, cash, 0.0, "UNPRICED_EXIT_OR_REBALANCE"
            if intended > prior[symbol] + 1e-10 and not can_trade[symbol]:
                blocked_buy.add(symbol)
    # Solve NAV after exact proportional trading fee; tiny fixed-point contraction.
    after = before
    for _ in range(40):
        desired = {symbol: prior[symbol] if symbol in blocked_buy
                   else target_weights.get(symbol, 0.0) * after for symbol in symbols}
        turnover_value = sum(abs(desired[symbol] - prior[symbol]) for symbol in symbols)
        updated = before - cost_rate * turnover_value
        if abs(updated - after) < 1e-14:
            after = updated
            break
        after = updated
    desired = {symbol: prior[symbol] if symbol in blocked_buy
               else target_weights.get(symbol, 0.0) * after for symbol in symbols}
    turnover_value = sum(abs(desired[symbol] - prior[symbol]) for symbol in symbols)
    new_cash = after - sum(desired.values())
    if new_cash < -1e-9:
        raise ValueError("negative cash after rebalance")
    shares = {symbol: value / float(opens[symbol]) for symbol, value in desired.items() if value > 1e-14}
    return shares, max(0.0, new_cash), turnover_value / before, (
        "MISSED_BUY_CASH" if blocked_buy else "FILLED")


def simulate(intervals: list[dict], portfolio: str, calendar: pd.DatetimeIndex,
             adjusted_open: pd.DataFrame, adjusted_close: pd.DataFrame,
             raw_open: pd.DataFrame, raw_volume: pd.DataFrame,
             first_volume: pd.DataFrame, cost_bps: float,
             fill_aware: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily full-account NAV, with a permanent invalid state after an unfilled sale."""
    entries = {item["entry_date"]: item for item in intervals}
    exits = {item["exit_date"]: item for item in intervals if pd.notna(item["exit_date"])}
    if len(entries) != len(intervals) or len(exits) != sum(pd.notna(item["exit_date"]) for item in intervals):
        raise ValueError("duplicate portfolio event date")
    target_key = {"strategy": "weights", "B8": "b8_weights", "B14": "b14_weights"}[portfolio]
    cash, shares, invalid = 1.0, {}, False
    rows, events = [], []
    for date in calendar:
        exiting = exits.get(date)
        entering = entries.get(date)
        if not invalid and (exiting or entering):
            target = entering[target_key] if entering else {}
            symbols = set(shares) | set(target)
            tradable = ({symbol: paper._can_fill(date, symbol, raw_open, raw_volume, first_volume)
                        for symbol in symbols} if fill_aware else None)
            shares, cash, turnover, status = _rebalance(
                shares, cash, adjusted_open.loc[date], target, cost_bps / 10000, tradable)
            if status == "UNPRICED_EXIT_OR_REBALANCE":
                invalid = True
            events.append({"date": date, "portfolio": portfolio, "cost_bps_per_side": cost_bps,
                           "fill_aware": fill_aware, "event": "EXIT_AND_ENTRY" if exiting and entering
                           else "ENTRY" if entering else "EXIT",
                           "status": status, "one_way_turnover_fraction": turnover,
                           "signal_date": entering["signal_date"] if entering else exiting["signal_date"]})
        nav = (cash + sum(quantity * adjusted_close.at[date, symbol]
                          for symbol, quantity in shares.items())) if not invalid else np.nan
        rows.append({"date": date, "portfolio": portfolio, "cost_bps_per_side": cost_bps,
                     "fill_aware": fill_aware, "nav": nav,
                     "cash": cash if not invalid else np.nan,
                     "has_open_position": bool(shares) if not invalid else None,
                     "status": "INVALID_AFTER_UNPRICED_EXIT" if invalid else
                     "PARTIAL_OPEN_AT_CUTOFF" if date == calendar[-1] and bool(shares) else "VALID"})
    return pd.DataFrame(rows), pd.DataFrame(events)


def summarize_nav(rule: str, daily: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (portfolio, cost, fill), frame in daily.groupby(["portfolio", "cost_bps_per_side", "fill_aware"]):
        frame = frame.sort_values("date")
        one_events = events[(events.portfolio == portfolio) &
                            (events.cost_bps_per_side == cost) &
                            (events.fill_aware == fill)]
        last_valid = frame.nav.dropna()
        invalid = frame.nav.isna().any()
        total_turnover = float(one_events.one_way_turnover_fraction.sum())
        for period, subset in [("FULL_COLD", frame), *[(str(y), frame[frame.date.dt.year.eq(y)])
                                                     for y in (2024, 2025, 2026)]]:
            if subset.empty:
                continue
            start = (1.0 if period == "2024" else
                     float(frame.loc[frame.date.lt(subset.date.min()), "nav"].iloc[-1])
                     if period != "FULL_COLD" else 1.0)
            end = float(subset.nav.iloc[-1]) if pd.notna(subset.nav.iloc[-1]) else np.nan
            path = subset.nav
            high = pd.concat([pd.Series([start]), path], ignore_index=True).cummax()
            drawdown = float((pd.concat([pd.Series([start]), path], ignore_index=True) / high - 1).min()) if path.notna().all() else np.nan
            one_period_events = one_events if period == "FULL_COLD" else one_events[one_events.date.dt.year.eq(int(period))]
            rows.append({"rule": rule, "portfolio": portfolio, "cost_bps_per_side": cost,
                         "fill_aware": fill, "period": period,
                         "period_status": "COLD_PARTIAL_2026" if period == "2026" else
                         "PARTIAL_OPEN_AT_COLD" if period == "FULL_COLD" and subset.iloc[-1].status == "PARTIAL_OPEN_AT_CUTOFF" else
                         "INVALID_AFTER_UNPRICED_EXIT" if invalid and pd.isna(end) else
                         "YEAR_END_MARKED_OPEN" if period in {"2024", "2025"} and bool(subset.iloc[-1].has_open_position) else "COMPLETE",
                         "start_nav": start if pd.notna(start) else None,
                         "end_nav": end if pd.notna(end) else None,
                         "return": end / start - 1 if pd.notna(end) and pd.notna(start) else None,
                         "max_drawdown": drawdown if pd.notna(drawdown) else None,
                         "one_way_turnover_fraction_sum": float(one_period_events.one_way_turnover_fraction.sum()),
                         "n_events": len(one_period_events),
                         "n_missed_buy_events": int(one_period_events.status.eq("MISSED_BUY_CASH").sum()),
                         "n_unpriced_events": int(one_period_events.status.eq("UNPRICED_EXIT_OR_REBALANCE").sum()),
                         "full_turnover_fraction_sum": total_turnover if period == "FULL_COLD" else None})
    return pd.DataFrame(rows)


def _filtered_sha(frame: pd.DataFrame) -> str:
    return sha256(frame.to_csv(index=True, float_format="%.17g", na_rep="NA",
                               date_format="%Y-%m-%dT%H:%M:%S").encode()).hexdigest()


def break_even_costs(schedules: dict, calendar: pd.DatetimeIndex,
                     adjusted_open: pd.DataFrame, adjusted_close: pd.DataFrame,
                     raw_open: pd.DataFrame, raw_volume: pd.DataFrame,
                     first_volume: pd.DataFrame) -> pd.DataFrame:
    """Solve cost sensitivity roots; no rule or threshold is selected from them."""
    rows = []
    for rule, (intervals, _decisions) in schedules.items():
        for benchmark in ("B8", "B14"):
            for fill_aware in (False, True):
                cache = {}

                def terminal(portfolio: str, cost: float) -> float:
                    key = (portfolio, cost)
                    if key not in cache:
                        path, _ = simulate(intervals, portfolio, calendar, adjusted_open,
                                           adjusted_close, raw_open, raw_volume, first_volume,
                                           cost, fill_aware)
                        cache[key] = float(path.nav.iloc[-1])
                    return cache[key]

                for comparison in ("gross_benchmark", "costed_benchmark"):
                    def advantage(cost: float) -> float:
                        return terminal("strategy", cost) - terminal(
                            benchmark, 0.0 if comparison == "gross_benchmark" else cost)

                    at_zero = advantage(0.0)
                    if not np.isfinite(at_zero):
                        value, status = None, "UNPRICED_NAV"
                    elif at_zero <= 0:
                        value, status = None, "NO_POSITIVE_GROSS_HEADROOM"
                    elif advantage(1000.0) >= 0:
                        value, status = None, "ABOVE_1000BP_PER_SIDE_BOUND"
                    else:
                        lo, hi = 0.0, 1000.0
                        for _ in range(38):
                            mid = (lo + hi) / 2
                            if advantage(mid) > 0:
                                lo = mid
                            else:
                                hi = mid
                        value, status = (lo + hi) / 2, "ROOT_WITHIN_BOUND"
                    rows.append({"rule": rule, "benchmark": benchmark,
                                 "fill_aware": fill_aware, "comparison": comparison,
                                 "strategy_gross_minus_benchmark_gross_nav": at_zero if np.isfinite(at_zero) else None,
                                 "break_even_bps_per_side": value, "status": status})
    return pd.DataFrame(rows)


def run(output: Path) -> dict:
    config = yaml.safe_load(CONFIG.read_text())
    validate_config(config)
    if output.exists():
        raise FileExistsError(output)
    cutoff = pd.Timestamp(config["cold_as_of"])
    groups = yaml.safe_load(paper.GROUPS.read_text())["groups"]
    universe = json.loads(paper.UNIVERSE.read_text())["etfs"]
    symbols = [item["ts_code"] for item in universe if item["role"] == "candidate"]
    discovery.validate_groups(groups, symbols)
    panels = paper.load_canonical_daily(paper.DATA_ROOT, paper.UNIVERSE,
                                        as_of=config["cold_as_of"], roles=("candidate",))
    raw_calendar = pd.read_parquet(paper.DATA_ROOT / "1d/510300.SH.parquet",
                                   columns=["trade_date"], filters=[("trade_date", "<=", cutoff)])
    calendar = pd.DatetimeIndex(pd.to_datetime(raw_calendar.trade_date)).sort_values()
    if calendar.max() != cutoff or len(panels["close"].index.difference(calendar)):
        raise ValueError("cold calendar mismatch")
    panels = {key: frame.reindex(calendar) for key, frame in panels.items()}
    score = audit._score("weekday_relative_return_pattern_60", panels, groups).reindex(calendar)[list(groups)]
    saved = audit.read_csv_through(audit._source_score("weekday_relative_return_pattern_60"),
                                   calendar, config["cold_as_of"])[list(groups)]
    common = saved.index.intersection(score.index)
    mismatch = saved.loc[common].isna().ne(score.loc[common].isna()) | (
        (saved.loc[common] - score.loc[common]).abs() > 1e-9 * saved.loc[common].abs().clip(lower=1e-12))
    if mismatch.to_numpy().any():
        raise ValueError("weekday source-score reproducibility failed")
    first_date = pd.Timestamp(config["start_date"])
    schedules = {}
    schedules["A_weekly_weekday_top2"] = schedule_weekly(calendar, score, groups, first_date)
    schedules["B_monthly_absolute_trend"] = schedule_monthly(calendar, panels["close"], groups, first_date)
    raw_open, raw_volume, first_volume = paper._raw_prices_and_opening_volume(symbols, cutoff, calendar)
    study_calendar = calendar[calendar >= first_date]
    all_daily, all_events, decisions, intervals_public = [], [], [], []
    for rule, (intervals, one_decisions) in schedules.items():
        decisions.extend(one_decisions)
        for item in intervals:
            intervals_public.append({key: value for key, value in item.items() if not key.endswith("weights")})
        for portfolio in BENCHMARKS:
            for cost in (0, 10):
                for fill_aware in (False, True):
                    daily, events = simulate(intervals, portfolio, study_calendar,
                                             panels["open"], panels["close"],
                                             raw_open, raw_volume, first_volume,
                                             cost, fill_aware)
                    daily.insert(0, "rule", rule)
                    events.insert(0, "rule", rule)
                    all_daily.append(daily)
                    all_events.append(events)
    daily = pd.concat(all_daily, ignore_index=True)
    events = pd.concat(all_events, ignore_index=True)
    summary = pd.concat([summarize_nav(rule, daily[daily.rule == rule], events[events.rule == rule])
                         for rule in schedules], ignore_index=True)
    break_even = break_even_costs(schedules, study_calendar, panels["open"], panels["close"],
                                  raw_open, raw_volume, first_volume)
    output.mkdir(parents=True, exist_ok=False)
    daily.to_csv(output / "daily_nav.csv", index=False)
    events.to_csv(output / "events.csv", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    break_even.to_csv(output / "break_even.csv", index=False)
    pd.DataFrame(decisions).to_csv(output / "decisions.csv", index=False)
    pd.DataFrame(intervals_public).to_csv(output / "intervals.csv", index=False)
    source_paths = [Path(__file__), CONFIG, Path(audit.__file__), Path(paper.__file__),
                    Path(audit.extra.__file__), Path(audit.monthly.__file__),
                    paper.UNIVERSE, paper.GROUPS,
                    audit._source_score("weekday_relative_return_pattern_60").parent / "PLAN.json",
                    ETF / "src/etf_strategy/canonical_data.py",
                    ETF / "src/etf_strategy/core/etf_group_discovery.py",
                    ETF / "src/etf_strategy/core/etf_group_claude_rounds.py",
                    ETF / "src/etf_strategy/core/etf_rank_utils.py"]
    manifest = {"version": config["version"], "spec_sha256": FROZEN_CONFIG_SHA256,
                "cutoff": config["cold_as_of"], "start": config["start_date"],
                "population": config["population"], "rules": list(schedules),
                "history_status": "DESCRIPTIVE_ADAPTIVE_A_AND_UNTESTED_MECHANISM_B_NO_OOS_CLAIM",
                "input_vintage": config["data_vintage"],
                "label_boundary": "original ETF H5 signed Rank IC and v4 ledgers untouched",
                "timing": "D close decisions, D+2 opens; A D+7 exit, B next monthly D+2 rebalance; cold open positions marked at D close",
                "fill_status": "09:31 positive volume is conservative proxy, not exact daily-open fill evidence",
                "cost_status": "10bp per side illustrative, not personal brokerage cost",
                "benchmark": "B8/B14 on matching event dates, same net-order cost and fill rules",
                "break_even": "exact bisection root of strategy terminal marked NAV minus gross or equally costed benchmark terminal NAV, 0..1000bp per side; diagnostic only",
                "annual_partition": "calendar-year account NAV, cross-year holdings marked at year-end close",
                "source_sha256": {str(path): paper._digest(path) for path in source_paths},
                "filtered_input_sha256": {name: _filtered_sha(frame) for name, frame in {
                    **{f"adjusted_{key}_through_{cutoff.date()}": frame for key, frame in panels.items()},
                    "raw_open": raw_open, "raw_volume": raw_volume,
                    "first_0931_volume": first_volume,
                    "archived_weekday_score": saved}.items()},
                "input_hash_rule": "SHA256 cutoff-filtered in-memory DataFrame CSV with float_format %.17g and NA literal",
                "command": [sys.executable, *sys.argv]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2,
                                                    allow_nan=False) + "\n")
    return {"output": str(output), "intervals": {rule: len(item[0]) for rule, item in schedules.items()},
            "summary_rows": len(summary)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT / "cold_20260324")
    args = parser.parse_args()
    print(json.dumps(run(args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
