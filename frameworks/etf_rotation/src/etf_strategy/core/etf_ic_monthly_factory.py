"""Versioned monthly forward evaluator for the fixed ETF group-factor process.

The unit under evaluation is the frozen selection process.  A month-end freeze
may use only labels whose exits are already known at that cutoff.  The selected
factor set is then evaluated on next month's signal dates after every label has
matured.  Costs are outside factor acceptance; turnover is retained as a field.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import yaml

from .etf_mining_referee import newey_west_t_calendar


@dataclass(frozen=True)
class MonthlyFreeze:
    process_version: str
    contract_sha256: str
    freeze_month: str
    train_end: str
    evaluation_month: str
    selected_candidates: tuple[str, ...]
    candidate_catalog_sha256: str


def candidate_lookback(candidate: str) -> int:
    """Return the frozen trailing-session window encoded in a candidate id."""
    try:
        value = int(str(candidate).rsplit("_", 1)[1])
    except (IndexError, ValueError) as exc:
        raise ValueError(f"candidate has no trailing integer lookback: {candidate}") from exc
    if value <= 0:
        raise ValueError(f"candidate lookback must be positive: {candidate}")
    return value


def open_halt_dates(minute: pd.DataFrame) -> pd.DatetimeIndex:
    """Identify dates with zero 513100 volume from 09:31 through 10:30.

    This is a diagnostic market-state flag, not a data-quality exclusion.
    """
    required = {"datetime", "volume"}
    missing = sorted(required - set(minute.columns))
    if missing:
        raise ValueError(f"halt diagnostic minute data missing: {missing}")
    frame = minute.loc[:, ["datetime", "volume"]].copy()
    frame["datetime"] = pd.to_datetime(frame["datetime"])
    if frame["datetime"].duplicated().any():
        raise ValueError("halt diagnostic minute data has duplicate timestamps")
    if not np.isfinite(frame["volume"].astype(float)).all() or frame["volume"].lt(0).any():
        raise ValueError("halt diagnostic minute volume must be finite and nonnegative")
    minute_of_day = frame["datetime"].dt.hour * 60 + frame["datetime"].dt.minute
    opening = frame.loc[minute_of_day.between(571, 630)].copy()
    opening["date"] = opening["datetime"].dt.normalize()
    counts = opening.groupby("date").size()
    volume = opening.groupby("date")["volume"].sum()
    return pd.DatetimeIndex(volume.index[(counts == 60) & volume.le(0.0)]).sort_values()


def candidate_halt_window_mask(
    calendar: pd.DatetimeIndex,
    candidates: list[str] | tuple[str, ...],
    halted_dates: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Flag candidate dates whose trailing lookback contains a halt date."""
    dates = pd.DatetimeIndex(calendar)
    event = pd.Series(dates.isin(pd.DatetimeIndex(halted_dates)), index=dates, dtype=float)
    result = {}
    for candidate in candidates:
        window = candidate_lookback(candidate)
        result[str(candidate)] = event.rolling(window, min_periods=1).max().gt(0)
    return pd.DataFrame(result, index=dates, dtype=bool)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def load_contract(path: str | Path) -> tuple[dict[str, Any], str]:
    source = Path(path)
    raw = yaml.safe_load(source.read_text())
    if not isinstance(raw, Mapping):
        raise ValueError("monthly factory contract must be a mapping")
    cfg = dict(raw)
    required = {
        "process_version", "project", "population_sha256", "population_file_sha256", "groups_sha256",
        "signal_time", "entry_lag", "horizon", "training_window_sessions",
        "evaluation_rule", "primary_metric", "candidate_catalog",
        "max_selected", "selection", "cost_policy",
    }
    missing = sorted(required - set(cfg))
    if missing:
        raise ValueError(f"monthly factory contract missing: {missing}")
    if cfg["project"] != "etf_rotation_fixed14_eight_groups":
        raise ValueError("monthly factory cannot cross into a stock project")
    if (cfg["entry_lag"], cfg["horizon"]) != (2, 5):
        raise ValueError("monthly factory fixes close(D), open(D+2), open(D+7)")
    if cfg["evaluation_rule"] != "next_calendar_month_signal_dates":
        raise ValueError("monthly evaluation must be the next calendar month")
    if cfg["primary_metric"] != "eight_group_daily_spearman_rank_ic":
        raise ValueError("monthly factory primary metric must be group Rank IC")
    if cfg["cost_policy"] != "record_turnover_only_not_a_factor_gate":
        raise ValueError("cost cannot silently become a factor-mining gate")
    catalog = cfg["candidate_catalog"]
    if not isinstance(catalog, list) or not catalog or len(catalog) != len(set(catalog)):
        raise ValueError("candidate_catalog must be a non-empty unique list")
    if int(cfg["training_window_sessions"]) < 120:
        raise ValueError("training_window_sessions is too short")
    if not 1 <= int(cfg["max_selected"]) <= len(catalog):
        raise ValueError("invalid max_selected")
    digest = sha256(_canonical_json(cfg).encode()).hexdigest()
    return cfg, digest


def verify_contract_files(contract: Mapping[str, Any], repo_root: str | Path) -> None:
    """Fail closed when the fixed ETF population or grouping has changed."""
    root = Path(repo_root).resolve()
    for path_key, hash_key in (("population", "population_file_sha256"), ("groups", "groups_sha256")):
        relative = str(contract[path_key]).split("#", 1)[0]
        source = (root / relative).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            raise ValueError(f"contract {path_key} is outside the repository or missing")
        actual = sha256(source.read_bytes()).hexdigest()
        if actual != contract[hash_key]:
            raise ValueError(f"contract {path_key} hash mismatch")
    universe_path = (root / str(contract["population"]).split("#", 1)[0]).resolve()
    universe = json.loads(universe_path.read_text())
    identities = sorted(
        str(row["ts_code"]) for row in universe["etfs"] if row.get("role") == "candidate"
    )
    identity_hash = sha256(_canonical_json(identities).encode()).hexdigest()
    if len(identities) != 14 or identity_hash != contract["population_sha256"]:
        raise ValueError("contract candidate identity population mismatch")


def _normalise_inputs(
    daily_ic: pd.DataFrame, label_dates: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ic = daily_ic.copy().astype(float)
    ic.index = pd.DatetimeIndex(ic.index)
    labels = label_dates.copy()
    labels.index = pd.DatetimeIndex(labels.index)
    for column in ("entry_date", "exit_date"):
        if column not in labels:
            raise ValueError(f"label_dates missing {column}")
        labels[column] = pd.to_datetime(labels[column])
    if not ic.index.is_unique or not labels.index.is_unique:
        raise ValueError("monthly inputs require unique signal dates")
    if not ic.index.sort_values().equals(labels.index.sort_values()):
        raise ValueError("daily_ic and label_dates must contain the same signal dates")
    common = ic.index.intersection(labels.index).sort_values()
    ic, labels = ic.reindex(common), labels.reindex(common)
    signal = common.to_series(index=common)
    valid = labels.entry_date.notna() & labels.exit_date.notna()
    if bool((valid & (labels.entry_date <= signal)).any()):
        raise ValueError("entry must be strictly after signal date")
    if bool((valid & (labels.exit_date <= labels.entry_date)).any()):
        raise ValueError("exit must be strictly after entry date")
    return ic, labels


def freeze_month(
    contract: Mapping[str, Any],
    contract_sha256: str,
    daily_ic: pd.DataFrame,
    label_dates: pd.DataFrame,
    freeze_month: str,
    *,
    halt_window_mask: pd.DataFrame | None = None,
    as_of: str | pd.Timestamp | None = None,
) -> tuple[MonthlyFreeze, pd.DataFrame]:
    """Freeze the candidates selected by the trailing, fully matured IC window."""
    ic, labels = _normalise_inputs(daily_ic, label_dates)
    catalog = [str(x) for x in contract["candidate_catalog"]]
    if set(catalog) - set(ic.columns):
        raise ValueError("daily_ic is missing frozen catalog candidates")
    period = pd.Period(freeze_month, freq="M")
    train_end = period.end_time.normalize()
    first_freeze = contract.get("first_freeze_month")
    if first_freeze is not None and period < pd.Period(str(first_freeze), freq="M"):
        raise ValueError("monthly process cannot be backdated before first_freeze_month")
    if contract.get("freeze_requires_month_closed"):
        if as_of is None or pd.Timestamp(as_of).normalize() < train_end:
            raise ValueError("monthly freeze cannot run before the frozen month has closed")
    evaluation_month = str(period + 1)
    eligible = (ic.index <= train_end) & labels.exit_date.le(train_end).to_numpy()
    matured_dates = ic.index[eligible]
    window = matured_dates[-int(contract["training_window_sessions"]):]
    if len(window) < int(contract["training_window_sessions"]):
        raise ValueError("insufficient fully matured training sessions")
    selection = contract["selection"]
    min_ic = float(selection["min_mean_ic"])
    min_t = float(selection["min_hac_t"])
    hac_lag = int(selection["hac_lag"])
    rows = []
    diagnostic = contract.get("halt_window_diagnostic", {})
    diagnostic_required = diagnostic.get("status") == "REPORT_ONLY_REQUIRED"
    if diagnostic_required and halt_window_mask is None:
        raise ValueError("monthly v3 requires the report-only halt-window diagnostic")
    if halt_window_mask is not None:
        halt_window_mask = halt_window_mask.reindex(index=ic.index, columns=catalog)
        if halt_window_mask.isna().any().any():
            raise ValueError("halt_window_mask must cover every IC date and catalog candidate")
        halt_window_mask = halt_window_mask.astype(bool)
    for candidate in catalog:
        values = ic.loc[window, candidate]
        row = {
            "candidate": candidate,
            "train_n": int(values.notna().sum()),
            "train_ic_mean": float(values.mean()),
            "train_ic_hac_t": newey_west_t_calendar(values, window, hac_lag),
        }
        if halt_window_mask is not None:
            excluded = halt_window_mask.loc[window, candidate]
            without_halt = values.where(~excluded)
            row.update({
                "halt_window_excluded_n": int((excluded & values.notna()).sum()),
                "without_halt_window_n": int(without_halt.notna().sum()),
                "without_halt_window_ic_mean": float(without_halt.mean()),
                "without_halt_window_ic_hac_t": newey_west_t_calendar(
                    without_halt, window, hac_lag
                ),
                "halt_window_diagnostic_only": True,
            })
        rows.append(row)
    table = pd.DataFrame(rows)
    table["selection_pass"] = (
        table.train_n.ge(int(contract["training_window_sessions"]))
        & table.train_ic_mean.ge(min_ic)
        & table.train_ic_hac_t.ge(min_t)
    )
    table = table.sort_values(
        ["selection_pass", "train_ic_hac_t", "train_ic_mean", "candidate"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    selected = tuple(
        table.loc[table.selection_pass, "candidate"].head(int(contract["max_selected"]))
    )
    catalog_hash = sha256(_canonical_json(catalog).encode()).hexdigest()
    frozen = MonthlyFreeze(
        process_version=str(contract["process_version"]),
        contract_sha256=contract_sha256,
        freeze_month=str(period),
        train_end=str(train_end.date()),
        evaluation_month=evaluation_month,
        selected_candidates=selected,
        candidate_catalog_sha256=catalog_hash,
    )
    return frozen, table


def evaluate_next_month(
    frozen: MonthlyFreeze,
    daily_ic: pd.DataFrame,
    label_dates: pd.DataFrame,
    *,
    as_of: str | pd.Timestamp,
    turnover: pd.DataFrame | None = None,
    hac_lag: int = 10,
) -> dict[str, Any]:
    """Evaluate one frozen monthly selection after all next-month labels mature."""
    ic, labels = _normalise_inputs(daily_ic, label_dates)
    month = pd.Period(frozen.evaluation_month, freq="M")
    mask = (ic.index >= month.start_time) & (ic.index <= month.end_time)
    dates = ic.index[mask]
    as_of_date = pd.Timestamp(as_of).normalize()
    if as_of_date < month.end_time.normalize():
        raise ValueError("evaluation calendar month has not closed by as_of")
    exits = labels.loc[dates, "exit_date"]
    if len(dates) and exits.isna().any():
        raise ValueError("evaluation labels have not all matured by as_of")
    if len(dates) and exits.max() > as_of_date:
        raise ValueError("evaluation labels have not all matured by as_of")
    if not frozen.selected_candidates:
        process_ic = pd.Series(np.nan, index=dates, dtype=float)
    else:
        process_ic = ic.loc[dates, list(frozen.selected_candidates)].mean(axis=1)
    mean_turnover = None
    if turnover is not None and frozen.selected_candidates:
        aligned = turnover.reindex(index=dates, columns=list(frozen.selected_candidates))
        mean_turnover = float(aligned.mean(axis=1).mean())
    return {
        **asdict(frozen),
        "evaluation_start": str(month.start_time.date()),
        "evaluation_end": str(month.end_time.date()),
        "as_of": str(as_of_date.date()),
        "ic_n": int(process_ic.notna().sum()),
        "ic_mean": float(process_ic.mean()) if process_ic.notna().any() else None,
        "ic_hac_t": newey_west_t_calendar(process_ic, dates, hac_lag),
        "mean_turnover": mean_turnover,
        "cost_gate_applied": False,
        "status": "EVALUATED" if process_ic.notna().any() else "NO_SELECTION_OR_SAMPLE",
    }


def append_ledger(path: str | Path, record: Mapping[str, Any]) -> None:
    """Append one immutable process-month result; duplicates fail closed."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    key_fields = ("process_version", "contract_sha256", "freeze_month", "evaluation_month")
    key = tuple(record.get(field) for field in key_fields)
    if None in key:
        raise ValueError("ledger record is missing its version/month key")
    if target.exists():
        for line in target.read_text().splitlines():
            previous = json.loads(line)
            if tuple(previous.get(field) for field in key_fields) == key:
                raise ValueError("monthly factory ledger key already exists")
    with target.open("a", encoding="utf-8") as handle:
        handle.write(_canonical_json(dict(record)) + "\n")


def read_version(path: str | Path, process_version: str, contract_sha256: str) -> list[dict[str, Any]]:
    """Read exactly one process version; cross-version aggregation is unavailable."""
    source = Path(path)
    if not source.exists():
        return []
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    return [row for row in rows if row.get("process_version") == process_version
            and row.get("contract_sha256") == contract_sha256]


__all__ = [
    "MonthlyFreeze", "append_ledger", "candidate_halt_window_mask",
    "candidate_lookback", "evaluate_next_month", "freeze_month", "load_contract",
    "open_halt_dates", "read_version", "verify_contract_files",
]
