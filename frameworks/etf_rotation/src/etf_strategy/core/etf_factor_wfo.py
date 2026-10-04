"""Purged walk-forward protocol robustness for frozen ETF atoms.

For each chronological fold the sign of every frozen atom is fixed from the
training window alone, and the test window reports the mean daily IC under that
frozen sign.  Training labels are purged: a training signal only counts when its
label has already exited by ``train_end``, so nothing that resolves inside the
test window can influence the direction.

This is a robustness read over history that has already been mined, not an
independent out-of-sample result.  The module therefore emits descriptive
numbers only: no pass/fail verdict, no p-value, no significance claim and no
standard error.  Every atom in the given catalog is reported in every fold;
atoms are never prefiltered by what their test windows turned out to show.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

DEFAULT_MIN_TRAIN_DAYS = 360

STATUS_EVALUATED = "EVALUATED"
STATUS_INSUFFICIENT_TRAIN = "INSUFFICIENT_TRAIN"
STATUS_ZERO_TRAIN_DIRECTION = "ZERO_TRAIN_DIRECTION"
STATUS_NO_TEST_SAMPLE = "NO_TEST_SAMPLE"
STATUS_MISSING_ATOM = "MISSING_ATOM"

FOLD_KEYS = ("fold_id", "train_start", "train_end", "test_start", "test_end")

OUTPUT_COLUMNS = (
    "fold_id",
    "horizon",
    "expression_key",
    "train_start",
    "train_end",
    "test_start",
    "test_end",
    "train_days",
    "test_days",
    "train_mean_ic",
    "train_direction",
    "raw_test_mean_ic",
    "oriented_test_mean_ic",
    "mean_test_eligible_count",
    "train_label_exit_max",
    "test_label_exit_min",
    "test_label_exit_max",
    "status",
)


@dataclass(frozen=True)
class Fold:
    """One chronological fold; training always ends strictly before the test window."""

    fold_id: str
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


def _timestamp(value: object, field: str, fold_id: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if pd.isna(stamp):
        raise ValueError(f"fold {fold_id!r}: {field} is not a valid timestamp")
    return stamp


def normalize_folds(folds: Iterable[Mapping[str, object]]) -> list[Fold]:
    """Validate fold specs and return them ordered by test window.

    Rejects duplicate ids, inverted windows, ``train_end >= test_start`` and any
    pair of folds whose test ranges overlap.
    """
    normalized: list[Fold] = []
    seen_ids: set[str] = set()
    for raw in folds:
        missing = [key for key in FOLD_KEYS if key not in raw]
        if missing:
            raise ValueError(f"fold spec missing keys: {missing}")
        fold_id = str(raw["fold_id"])
        if fold_id in seen_ids:
            raise ValueError(f"duplicate fold_id {fold_id!r}")
        seen_ids.add(fold_id)
        fold = Fold(
            fold_id=fold_id,
            train_start=_timestamp(raw["train_start"], "train_start", fold_id),
            train_end=_timestamp(raw["train_end"], "train_end", fold_id),
            test_start=_timestamp(raw["test_start"], "test_start", fold_id),
            test_end=_timestamp(raw["test_end"], "test_end", fold_id),
        )
        if fold.train_start > fold.train_end:
            raise ValueError(f"fold {fold_id!r}: train_start is after train_end")
        if fold.test_start > fold.test_end:
            raise ValueError(f"fold {fold_id!r}: test_start is after test_end")
        if fold.train_end >= fold.test_start:
            raise ValueError(
                f"fold {fold_id!r}: train_end {fold.train_end.date()} must be strictly "
                f"before test_start {fold.test_start.date()}"
            )
        normalized.append(fold)
    if not normalized:
        raise ValueError("at least one fold is required")
    normalized.sort(key=lambda item: (item.test_start, item.test_end, item.fold_id))
    for previous, current in zip(normalized, normalized[1:]):
        if current.test_start <= previous.test_end:
            raise ValueError(
                f"folds {previous.fold_id!r} and {current.fold_id!r} have overlapping test ranges"
            )
    return normalized


def _validate_horizons(keys: Iterable[int]) -> list[int]:
    horizons: list[int] = []
    for key in keys:
        horizon = int(key)
        if horizon != key or horizon <= 0:
            raise ValueError(f"horizon must be a positive integer, got {key!r}")
        horizons.append(horizon)
    if len(set(horizons)) != len(horizons):
        raise ValueError("duplicate horizons")
    return sorted(horizons)


def _normalize_ic(frame: pd.DataFrame, horizon: int) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"horizon {horizon}: daily_ic must be a DataFrame")
    index = pd.DatetimeIndex(frame.index)
    if index.hasnans:
        raise ValueError(f"horizon {horizon}: daily_ic has missing signal dates")
    if not index.is_unique:
        raise ValueError(f"horizon {horizon}: daily_ic has duplicate signal dates")
    if frame.columns.duplicated().any():
        raise ValueError(f"horizon {horizon}: daily_ic has duplicate expression keys")
    result = frame.copy()
    result.index = index
    result.columns = result.columns.map(str)
    if result.columns.duplicated().any():
        raise ValueError('expression keys collide after string normalization')
    return result.astype(float).sort_index()


def _normalize_labels(frame: pd.DataFrame, horizon: int) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"horizon {horizon}: label_dates must be a DataFrame")
    for column in ("entry_date", "exit_date"):
        if column not in frame.columns:
            raise ValueError(f"horizon {horizon}: label_dates is missing column {column!r}")
    index = pd.DatetimeIndex(frame.index)
    if index.hasnans:
        raise ValueError(f"horizon {horizon}: label_dates has missing signal dates")
    if not index.is_unique:
        raise ValueError(f"horizon {horizon}: label_dates has duplicate signal dates")
    labels = pd.DataFrame(
        {
            "entry_date": pd.to_datetime(frame["entry_date"]).to_numpy(),
            "exit_date": pd.to_datetime(frame["exit_date"]).to_numpy(),
        },
        index=index,
    ).sort_index()
    signal = labels.index.to_series()
    entry, exit_ = labels["entry_date"], labels["exit_date"]
    both = entry.notna() & exit_.notna()
    if bool((both & (exit_ < entry)).any()):
        raise ValueError(f"horizon {horizon}: label exit_date precedes entry_date")
    if bool((entry.notna() & (entry <= signal)).any()):
        raise ValueError(f"horizon {horizon}: label entry_date is not after its signal date")
    return labels


def _normalize_eligibility(counts: pd.Series) -> pd.Series:
    if not isinstance(counts, pd.Series):
        raise TypeError("eligibility_counts must be a Series")
    index = pd.DatetimeIndex(counts.index)
    if index.hasnans:
        raise ValueError("eligibility_counts has missing signal dates")
    if not index.is_unique:
        raise ValueError("eligibility_counts has duplicate signal dates")
    result = pd.Series(counts.to_numpy(dtype=float), index=index, name="eligible_count")
    return result.sort_index()


def _column_stats(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-column finite count and mean of a (dates x atoms) block."""
    if values.size == 0:
        width = values.shape[1] if values.ndim == 2 else 0
        return np.zeros(width, dtype=int), np.full(width, np.nan)
    finite = np.isfinite(values)
    counts = finite.sum(axis=0)
    totals = np.where(finite, values, 0.0).sum(axis=0)
    means = np.divide(totals, counts, out=np.full(counts.shape, np.nan), where=counts > 0)
    return counts.astype(int), means


def _missing_row(fold: Fold, horizon: int, key: str) -> dict[str, object]:
    return {
        "fold_id": fold.fold_id,
        "horizon": horizon,
        "expression_key": key,
        "train_start": fold.train_start,
        "train_end": fold.train_end,
        "test_start": fold.test_start,
        "test_end": fold.test_end,
        "train_days": 0,
        "test_days": 0,
        "train_mean_ic": np.nan,
        "train_direction": np.nan,
        "raw_test_mean_ic": np.nan,
        "oriented_test_mean_ic": np.nan,
        "mean_test_eligible_count": np.nan,
        "train_label_exit_max": pd.NaT,
        "test_label_exit_min": pd.NaT,
        "test_label_exit_max": pd.NaT,
        "status": STATUS_MISSING_ATOM,
    }


def evaluate_factor_wfo(
    daily_ic: Mapping[int, pd.DataFrame],
    label_dates: Mapping[int, pd.DataFrame],
    eligibility_counts: pd.Series,
    folds: Sequence[Mapping[str, object]],
    *,
    min_train_days: int = DEFAULT_MIN_TRAIN_DAYS,
) -> pd.DataFrame:
    """Evaluate every frozen atom in every fold under a train-only direction.

    ``daily_ic[h]`` is indexed by signal date with one column per frozen atom.
    ``label_dates[h]`` is indexed by signal date with ``entry_date`` and
    ``exit_date`` columns precomputed upstream.  Signals whose label endpoints
    are missing cannot train or test and are dropped from both windows.

    Returns one row per (fold, horizon, atom) with descriptive metrics only.
    """
    if int(min_train_days) != min_train_days or min_train_days <= 0:
        raise ValueError("min_train_days must be a positive integer")
    min_train_days = int(min_train_days)

    horizons = _validate_horizons(daily_ic.keys())
    label_horizons = _validate_horizons(label_dates.keys())
    if horizons != label_horizons:
        raise ValueError(
            f"daily_ic horizons {horizons} do not match label_dates horizons {label_horizons}"
        )

    ic_frames = {h: _normalize_ic(daily_ic[h], h) for h in horizons}
    label_frames = {h: _normalize_labels(label_dates[h], h) for h in horizons}
    eligible = _normalize_eligibility(eligibility_counts)
    ordered_folds = normalize_folds(folds)

    # The candidate catalog is fixed up front across all horizons, so an atom
    # that is absent for one horizon is still reported there as unestimable.
    catalog = sorted({str(key) for frame in ic_frames.values() for key in frame.columns})

    rows: list[dict[str, object]] = []
    for fold in ordered_folds:
        for horizon in horizons:
            ic = ic_frames[horizon]
            labels = label_frames[horizon]
            present = [key for key in catalog if key in ic.columns]
            for key in catalog:
                if key not in ic.columns:
                    rows.append(_missing_row(fold, horizon, key))
            if not present:
                continue

            usable = labels.loc[labels.index.intersection(ic.index)]
            usable = usable[usable["entry_date"].notna() & usable["exit_date"].notna()]
            exit_dates = usable["exit_date"]
            signal_dates = usable.index

            train_index = signal_dates[
                (signal_dates >= fold.train_start)
                & (signal_dates <= fold.train_end)
                & (exit_dates <= fold.train_end).to_numpy()
            ]
            test_index = signal_dates[
                (signal_dates >= fold.test_start)
                & (signal_dates <= fold.test_end)
                & (exit_dates <= fold.test_end).to_numpy()
            ]

            block = ic.loc[:, present]
            train_days, train_mean = _column_stats(block.loc[train_index].to_numpy(dtype=float))
            test_days, test_mean = _column_stats(block.loc[test_index].to_numpy(dtype=float))

            for position, key in enumerate(present):
                atom_train_index = train_index[np.isfinite(block.loc[train_index, key].to_numpy(dtype=float))]
                atom_test_index = test_index[np.isfinite(block.loc[test_index, key].to_numpy(dtype=float))]
                train_exit_max = exit_dates.reindex(atom_train_index).max()
                test_exits = exit_dates.reindex(atom_test_index)
                test_exit_min, test_exit_max = test_exits.min(), test_exits.max()
                mean_eligible = float(eligible.reindex(atom_test_index).mean())
                mean_ic = float(train_mean[position])
                direction = np.nan
                oriented = np.nan
                if int(train_days[position]) < min_train_days:
                    status = STATUS_INSUFFICIENT_TRAIN
                elif not np.isfinite(mean_ic) or mean_ic == 0.0:
                    status = STATUS_ZERO_TRAIN_DIRECTION
                else:
                    direction = 1.0 if mean_ic > 0.0 else -1.0
                    if int(test_days[position]) == 0:
                        status = STATUS_NO_TEST_SAMPLE
                    else:
                        status = STATUS_EVALUATED
                        oriented = direction * float(test_mean[position])
                rows.append(
                    {
                        "fold_id": fold.fold_id,
                        "horizon": horizon,
                        "expression_key": key,
                        "train_start": fold.train_start,
                        "train_end": fold.train_end,
                        "test_start": fold.test_start,
                        "test_end": fold.test_end,
                        "train_days": int(train_days[position]),
                        "test_days": int(test_days[position]),
                        "train_mean_ic": mean_ic,
                        "train_direction": direction,
                        "raw_test_mean_ic": float(test_mean[position]),
                        "oriented_test_mean_ic": oriented,
                        "mean_test_eligible_count": mean_eligible,
                        "train_label_exit_max": train_exit_max,
                        "test_label_exit_min": test_exit_min,
                        "test_label_exit_max": test_exit_max,
                        "status": status,
                    }
                )

    result = pd.DataFrame(rows, columns=list(OUTPUT_COLUMNS))
    fold_order = {fold.fold_id: rank for rank, fold in enumerate(ordered_folds)}
    result["_fold_rank"] = result["fold_id"].map(fold_order)
    result = result.sort_values(["_fold_rank", "horizon", "expression_key"], kind="stable")
    return result.drop(columns="_fold_rank").reset_index(drop=True)
