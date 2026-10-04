"""Synthetic-only coverage for the purged walk-forward robustness evaluator."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_factor_wfo import (
    STATUS_EVALUATED,
    STATUS_INSUFFICIENT_TRAIN,
    STATUS_MISSING_ATOM,
    STATUS_NO_TEST_SAMPLE,
    STATUS_ZERO_TRAIN_DIRECTION,
    evaluate_factor_wfo,
    normalize_folds,
)

ROOT = Path(__file__).resolve().parents[1]


def _labels(index: pd.DatetimeIndex, horizon: int) -> pd.DataFrame:
    """Signal date D -> entry D+1, exit D+1+horizon, in calendar days."""
    entry = index + pd.Timedelta(days=1)
    return pd.DataFrame(
        {"entry_date": entry, "exit_date": entry + pd.Timedelta(days=horizon)},
        index=index,
    )


def _panel(days: int = 120, start: str = "2024-01-01") -> pd.DatetimeIndex:
    return pd.date_range(start, periods=days, freq="D")


def _folds() -> list[dict[str, object]]:
    return [
        {
            "fold_id": "f1",
            "train_start": "2024-01-01",
            "train_end": "2024-02-19",
            "test_start": "2024-02-20",
            "test_end": "2024-03-10",
        },
        {
            "fold_id": "f2",
            "train_start": "2024-01-01",
            "train_end": "2024-03-10",
            "test_start": "2024-03-11",
            "test_end": "2024-04-29",
        },
    ]


def _eligible(index: pd.DatetimeIndex, value: float = 40.0) -> pd.Series:
    return pd.Series(value, index=index, name="eligible_count")


def test_training_purges_labels_that_exit_after_train_end() -> None:
    index = _panel(60)
    horizon = 5
    ic = pd.DataFrame({"atom": np.linspace(0.01, 0.06, len(index))}, index=index)
    labels = _labels(index, horizon)
    folds = [
        {
            "fold_id": "f1",
            "train_start": "2024-01-01",
            "train_end": "2024-01-31",
            "test_start": "2024-02-05",
            "test_end": "2024-02-29",
        }
    ]
    result = evaluate_factor_wfo({horizon: ic}, {horizon: labels}, _eligible(index), folds, min_train_days=1)
    row = result.iloc[0]
    train_end = pd.Timestamp("2024-01-31")
    # Last usable training signal is 2024-01-25: entry 01-26, exit 01-31.
    assert row["train_days"] == 25
    assert row["train_label_exit_max"] == train_end
    expected = float(ic.loc[index[:25], "atom"].mean())
    assert row["train_mean_ic"] == pytest.approx(expected)
    assert row["test_label_exit_max"] <= pd.Timestamp("2024-02-29")


def test_labels_with_missing_endpoints_cannot_train_or_test() -> None:
    index = _panel(40)
    horizon = 2
    ic = pd.DataFrame({"atom": np.full(len(index), 0.02)}, index=index)
    labels = _labels(index, horizon)
    labels.iloc[0:5, labels.columns.get_loc("exit_date")] = pd.NaT
    labels.iloc[20:23, labels.columns.get_loc("entry_date")] = pd.NaT
    folds = [
        {
            "fold_id": "f1",
            "train_start": "2024-01-01",
            "train_end": "2024-01-25",
            "test_start": "2024-01-27",
            "test_end": "2024-02-09",
        }
    ]
    result = evaluate_factor_wfo({horizon: ic}, {horizon: labels}, _eligible(index), folds, min_train_days=1)
    row = result.iloc[0]
    # Train: 2024-01-01..01-22 survives the purge (22 dates), minus 5 missing
    # exits and the 2 missing entries that fall inside the window.
    assert row["train_days"] == 15
    # Test: 2024-01-27..02-06 survives the purge; no missing endpoints land there.
    assert row["test_days"] == 11


def test_direction_is_train_only_and_test_mutation_leaves_earlier_folds_intact() -> None:
    index = _panel(120)
    horizon = 3
    rng = np.random.default_rng(11)
    ic = pd.DataFrame(
        {
            "up": 0.04 + rng.normal(0, 0.001, len(index)),
            "down": -0.04 + rng.normal(0, 0.001, len(index)),
        },
        index=index,
    )
    labels = _labels(index, horizon)
    folds = _folds()
    keys = ["fold_id", "horizon", "expression_key"]
    train_columns = ["train_days", "train_mean_ic", "train_direction"]

    def run(frame: pd.DataFrame) -> pd.DataFrame:
        return evaluate_factor_wfo(
            {horizon: frame}, {horizon: labels}, _eligible(index), folds, min_train_days=1
        )

    baseline = run(ic)
    assert set(baseline.loc[baseline["expression_key"] == "up", "train_direction"]) == {1.0}
    assert set(baseline.loc[baseline["expression_key"] == "down", "train_direction"]) == {-1.0}
    oriented = baseline["oriented_test_mean_ic"].to_numpy(dtype=float)
    raw = baseline["raw_test_mean_ic"].to_numpy(dtype=float)
    direction = baseline["train_direction"].to_numpy(dtype=float)
    assert np.allclose(oriented, direction * raw)

    # Flip the last fold's test window. Nothing in any training window changes,
    # and the earlier fold's row is byte-identical.
    mutated = ic.copy()
    last_test = mutated.index >= pd.Timestamp("2024-03-11")
    mutated.loc[last_test] = -10.0 * mutated.loc[last_test]
    after = run(mutated)

    merged = baseline.merge(after, on=keys, suffixes=("_base", "_mut"))
    for column in train_columns:
        assert np.allclose(merged[f"{column}_base"], merged[f"{column}_mut"])
    first_base = baseline[baseline["fold_id"] == "f1"].reset_index(drop=True)
    first_after = after[after["fold_id"] == "f1"].reset_index(drop=True)
    pd.testing.assert_frame_equal(first_base, first_after)
    second = merged[merged["fold_id"] == "f2"]
    assert not np.allclose(
        second["oriented_test_mean_ic_base"], second["oriented_test_mean_ic_mut"]
    )

    # Perturbing a fold's own test window never reaches its own training window,
    # even though an expanding later fold legitimately trains on that data.
    early = ic.copy()
    first_test = (early.index >= pd.Timestamp("2024-02-20")) & (early.index <= pd.Timestamp("2024-03-10"))
    early.loc[first_test] = -10.0 * early.loc[first_test]
    early_result = run(early)
    own = baseline.merge(early_result, on=keys, suffixes=("_base", "_mut"))
    own_first = own[own["fold_id"] == "f1"]
    for column in train_columns:
        assert np.allclose(own_first[f"{column}_base"], own_first[f"{column}_mut"])
    assert not np.allclose(
        own_first["oriented_test_mean_ic_base"], own_first["oriented_test_mean_ic_mut"]
    )


def test_short_history_reports_insufficient_train_without_lowering_the_floor() -> None:
    index = _panel(80)
    horizon = 2
    ic = pd.DataFrame({"atom": np.full(len(index), 0.03)}, index=index)
    labels = _labels(index, horizon)
    folds = [
        {
            "fold_id": "f1",
            "train_start": "2024-01-01",
            "train_end": "2024-02-19",
            "test_start": "2024-02-20",
            "test_end": "2024-03-20",
        }
    ]
    result = evaluate_factor_wfo(
        {horizon: ic}, {horizon: labels}, _eligible(index), folds, min_train_days=360
    )
    row = result.iloc[0]
    assert row["status"] == STATUS_INSUFFICIENT_TRAIN
    assert row["train_days"] < 360
    assert np.isnan(row["train_direction"])
    assert np.isnan(row["oriented_test_mean_ic"])
    # The raw descriptive test mean is still reported; only the orientation is withheld.
    assert np.isfinite(row["raw_test_mean_ic"])


def test_zero_train_direction_and_empty_test_sample_statuses() -> None:
    index = _panel(120)
    horizon = 3
    flat = np.zeros(len(index))
    ic = pd.DataFrame({"flat": flat, "late": flat + 0.02}, index=index)
    ic.loc[ic.index >= pd.Timestamp("2024-02-20"), "late"] = np.nan
    labels = _labels(index, horizon)
    result = evaluate_factor_wfo(
        {horizon: ic}, {horizon: labels}, _eligible(index), _folds()[:1], min_train_days=1
    )
    statuses = dict(zip(result["expression_key"], result["status"]))
    assert statuses["flat"] == STATUS_ZERO_TRAIN_DIRECTION
    assert statuses["late"] == STATUS_NO_TEST_SAMPLE
    assert result["oriented_test_mean_ic"].isna().all()


def test_catalog_is_never_prefiltered_by_test_results() -> None:
    index = _panel(120)
    labels_short = _labels(index, 1)
    labels_long = _labels(index, 5)
    common = pd.DataFrame(
        {"a": np.full(len(index), 0.02), "b": np.full(len(index), -0.02)}, index=index
    )
    # Horizon 5 is missing atom "b" entirely.
    daily_ic = {1: common, 5: common[["a"]]}
    result = evaluate_factor_wfo(
        daily_ic,
        {1: labels_short, 5: labels_long},
        _eligible(index),
        _folds(),
        min_train_days=1,
    )
    # 2 folds x 2 horizons x 2 catalog atoms, nothing dropped.
    assert len(result) == 8
    missing = result[result["status"] == STATUS_MISSING_ATOM]
    assert len(missing) == 2
    assert set(missing["horizon"]) == {5}
    assert set(missing["expression_key"]) == {"b"}
    assert missing["train_mean_ic"].isna().all()
    evaluated = result[result["status"] == STATUS_EVALUATED]
    assert len(evaluated) == 6
    # Every fold reports every catalog atom, including losers.
    for fold_id in ("f1", "f2"):
        block = result[result["fold_id"] == fold_id]
        assert set(block["expression_key"]) == {"a", "b"}


def test_invalid_fold_configurations_are_rejected() -> None:
    base = {
        "fold_id": "f1",
        "train_start": "2024-01-01",
        "train_end": "2024-02-19",
        "test_start": "2024-02-20",
        "test_end": "2024-03-10",
    }
    with pytest.raises(ValueError, match="strictly before test_start"):
        normalize_folds([{**base, "train_end": "2024-02-20"}])
    with pytest.raises(ValueError, match="overlapping test ranges"):
        normalize_folds(
            [
                base,
                {
                    "fold_id": "f2",
                    "train_start": "2024-01-01",
                    "train_end": "2024-02-25",
                    "test_start": "2024-03-01",
                    "test_end": "2024-04-01",
                },
            ]
        )
    with pytest.raises(ValueError, match="duplicate fold_id"):
        normalize_folds([base, dict(base)])
    with pytest.raises(ValueError, match="missing keys"):
        normalize_folds([{key: value for key, value in base.items() if key != "test_end"}])


def test_malformed_labels_and_horizons_are_rejected() -> None:
    index = _panel(40)
    ic = pd.DataFrame({"atom": np.full(len(index), 0.01)}, index=index)
    folds = _folds()[:1]

    inverted = _labels(index, 2)
    inverted.iloc[3, inverted.columns.get_loc("exit_date")] = index[0]
    with pytest.raises(ValueError, match="exit_date precedes entry_date"):
        evaluate_factor_wfo({2: ic}, {2: inverted}, _eligible(index), folds, min_train_days=1)

    same_day = _labels(index, 2)
    same_day.iloc[4, same_day.columns.get_loc("entry_date")] = index[4]
    with pytest.raises(ValueError, match="entry_date is not after its signal date"):
        evaluate_factor_wfo({2: ic}, {2: same_day}, _eligible(index), folds, min_train_days=1)

    with pytest.raises(ValueError, match="positive integer"):
        evaluate_factor_wfo({0: ic}, {0: _labels(index, 2)}, _eligible(index), folds, min_train_days=1)

    with pytest.raises(ValueError, match="do not match"):
        evaluate_factor_wfo({2: ic}, {3: _labels(index, 3)}, _eligible(index), folds, min_train_days=1)


def test_mean_test_eligible_count_is_a_generic_pool_count() -> None:
    index = _panel(120)
    horizon = 3
    ic = pd.DataFrame({"atom": np.full(len(index), 0.02)}, index=index)
    counts = pd.Series(np.arange(len(index), dtype=float) + 10.0, index=index)
    result = evaluate_factor_wfo(
        {horizon: ic}, {horizon: _labels(index, horizon)}, counts, _folds()[:1], min_train_days=1
    )
    row = result.iloc[0]
    test_dates = index[(index >= pd.Timestamp("2024-02-20")) & (index <= pd.Timestamp("2024-03-06"))]
    assert row["mean_test_eligible_count"] == pytest.approx(float(counts.loc[test_dates].mean()))


def test_no_significance_columns_are_emitted() -> None:
    index = _panel(60)
    result = evaluate_factor_wfo(
        {2: pd.DataFrame({"atom": np.full(len(index), 0.02)}, index=index)},
        {2: _labels(index, 2)},
        _eligible(index),
        _folds()[:1],
        min_train_days=1,
    )
    banned = {"pvalue", "p_value", "tstat", "t_stat", "pass", "verdict", "stderr", "se"}
    assert banned.isdisjoint({column.lower() for column in result.columns})


def test_cli_smoke_on_synthetic_fixture(tmp_path: Path) -> None:
    index = _panel(900, start="2022-01-01")
    horizon = 3
    rng = np.random.default_rng(5)
    ic_long = []
    for key, level in (("alpha_up", 0.03), ("alpha_down", -0.03)):
        ic_long.append(
            pd.DataFrame(
                {
                    "horizon": horizon,
                    "signal_date": index,
                    "expression_key": key,
                    "ic": level + rng.normal(0, 0.005, len(index)),
                }
            )
        )
    ic_path = tmp_path / "daily_ic.parquet"
    pd.concat(ic_long, ignore_index=True).to_parquet(ic_path)

    labels = _labels(index, horizon).reset_index(names="signal_date")
    labels.insert(0, "horizon", horizon)
    label_path = tmp_path / "label_dates.parquet"
    labels.to_parquet(label_path)

    eligible_path = tmp_path / "eligibility_counts.csv"
    pd.DataFrame({"signal_date": index, "eligible_count": 42}).to_csv(eligible_path, index=False)

    config_path = tmp_path / "folds.yaml"
    config_path.write_text(
        "min_train_days: 360\n"
        "folds:\n"
        "  - fold_id: f1\n"
        "    train_start: 2022-01-01\n"
        "    train_end: 2023-06-30\n"
        "    test_start: 2023-07-01\n"
        "    test_end: 2023-12-31\n"
        "  - fold_id: f2\n"
        "    train_start: 2022-01-01\n"
        "    train_end: 2023-12-31\n"
        "    test_start: 2024-01-01\n"
        "    test_end: 2024-06-18\n"
    )

    output = tmp_path / "run"
    command = [
        sys.executable,
        str(ROOT / "scripts" / "evaluate_factor_wfo.py"),
        "--daily-ic", str(ic_path),
        "--label-dates", str(label_path),
        "--fold-config", str(config_path),
        "--eligibility-counts", str(eligible_path),
        "--output", str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr

    metrics = pd.read_csv(output / "fold_metrics.csv")
    assert len(metrics) == 4
    assert set(metrics["status"]) == {"EVALUATED"}
    assert (metrics["train_days"] >= 360).all()

    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "protocol_robustness_seen_history_not_independent_oos"
    assert manifest["min_train_days"] == 360
    assert set(manifest["inputs"]) == {"daily_ic", "label_dates", "fold_config", "eligibility_counts"}
    assert all(len(entry["sha256"]) == 64 for entry in manifest["inputs"].values())
    assert manifest["command"][1:] == command[2:]

    # The output directory is immutable: a second run into it must refuse.
    rerun = subprocess.run(command, capture_output=True, text=True)
    assert rerun.returncode != 0
    assert "must be new and empty" in rerun.stderr


def test_cli_refuses_min_train_days_below_the_floor(tmp_path: Path) -> None:
    from evaluate_factor_wfo import load_fold_config

    config_path = tmp_path / "folds.yaml"
    config_path.write_text(
        "min_train_days: 30\n"
        "folds:\n"
        "  - fold_id: f1\n"
        "    train_start: 2022-01-01\n"
        "    train_end: 2023-06-30\n"
        "    test_start: 2023-07-01\n"
        "    test_end: 2023-12-31\n"
    )
    with pytest.raises(ValueError, match="min_train_days must be >= 360"):
        load_fold_config(config_path)


def test_reported_label_dates_and_counts_match_each_atoms_finite_rows():
    index=_panel(60)
    ic=pd.DataFrame({'dense':.1,'sparse':np.nan},index=index)
    ic.loc[index[:10],'sparse']=.2
    ic.loc[index[40:43],'sparse']=.3
    eligible=pd.Series(np.arange(60)+8,index=index)
    result=evaluate_factor_wfo({5:ic},{5:_labels(index,5)},eligible,[{
        'fold_id':'one','train_start':index[0],'train_end':index[29],
        'test_start':index[30],'test_end':index[-1]}],min_train_days=5)
    row=result.set_index('expression_key').loc['sparse']
    assert row.train_label_exit_max==index[15]
    assert row.test_label_exit_max==index[48]
    assert row.mean_test_eligible_count==eligible.loc[index[40:43]].mean()
