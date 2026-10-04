from __future__ import annotations

import json
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from etf_strategy.core.etf_all_daily_data import load_all_etf_daily
from etf_strategy.core.etf_all_daily_discovery import executable_forward_return
from etf_strategy.core.etf_all_daily_factor_engine import (
    ForwardGates,
    compose_candidate,
    evaluate_forward_candidate,
    top_fraction_excess,
)


def test_executable_label_starts_at_d_plus_2_and_exits_at_d_plus_7() -> None:
    dates = pd.bdate_range("2025-01-02", periods=10)
    opened = pd.DataFrame({"ETF": np.arange(10, 20, dtype=float)}, index=dates)
    result = executable_forward_return(opened, entry_lag=2, horizon=5)
    assert result.loc[dates[0], "ETF"] == 17.0 / 12.0 - 1.0
    assert result.iloc[-7:].isna().all().all()


def test_executable_h20_label_starts_at_d_plus_2_and_exits_at_d_plus_22() -> None:
    dates = pd.bdate_range("2025-01-02", periods=30)
    opened = pd.DataFrame({"STOCK": np.arange(100, 130, dtype=float)}, index=dates)
    result = executable_forward_return(opened, entry_lag=2, horizon=20)
    assert result.loc[dates[0], "STOCK"] == 122.0 / 102.0 - 1.0
    assert result.iloc[-22:].isna().all().all()


def test_executable_h1_label_starts_at_d_plus_2_and_exits_at_d_plus_3() -> None:
    dates = pd.bdate_range("2025-01-02", periods=8)
    opened = pd.DataFrame({"STOCK": np.arange(100, 108, dtype=float)}, index=dates)
    result = executable_forward_return(opened, entry_lag=2, horizon=1)
    assert result.loc[dates[0], "STOCK"] == 103.0 / 102.0 - 1.0
    assert result.iloc[-3:].isna().all().all()


def test_rank_spread_is_built_only_from_frozen_atom_ranks() -> None:
    dates = pd.DatetimeIndex(["2025-01-02"])
    eligibility = pd.DataFrame([[True, True, True]], index=dates, columns=list("ABC"))
    atoms = {
        "LEFT": pd.DataFrame([[0.2, 0.8, 0.5]], index=dates, columns=list("ABC")),
        "RIGHT": pd.DataFrame([[0.7, 0.1, 0.4]], index=dates, columns=list("ABC")),
    }
    spec = {
        "operator": "rank_spread",
        "left": {"name": "LEFT"},
        "right": {"name": "RIGHT"},
    }
    result = compose_candidate(spec, atoms, eligibility)
    assert result.loc[dates[0]].sort_values().index.tolist() == ["A", "C", "B"]


def test_missing_selected_label_is_zero_return_without_replacement() -> None:
    dates = pd.DatetimeIndex(["2025-01-02"])
    columns = [f"E{i:02d}" for i in range(10)]
    signal = pd.DataFrame([np.arange(10)], index=dates, columns=columns, dtype=float)
    outcome = pd.DataFrame([np.arange(10)], index=dates, columns=columns, dtype=float)
    outcome.loc[dates[0], "E09"] = np.nan
    eligible = pd.DataFrame(True, index=dates, columns=columns)
    excess, count, coverage = top_fraction_excess(
        signal,
        outcome,
        eligible,
        direction=1,
        fraction=0.1,
        min_names=10,
        min_label_coverage=0.9,
    )
    assert excess.iloc[0] == -3.6
    assert count.iloc[0] == 1
    assert coverage.iloc[0] == 0.9


def test_loader_applies_listing_lifecycle_and_never_uses_future_survival(tmp_path) -> None:
    root = tmp_path / "cache"
    (root / "metadata").mkdir(parents=True)
    (root / "raw/fund_daily").mkdir(parents=True)
    (root / "raw/fund_adj").mkdir(parents=True)
    dates = pd.bdate_range("2025-01-02", periods=5)
    keys = [date.strftime("%Y%m%d") for date in dates]
    basic = pd.DataFrame(
        {
            "ts_code": ["510001.SH", "159001.SZ", "160001.SZ", "510004.SH"],
            "name": ["ONE ETF", "TWO ETF", "THREE ETF", "NOT A FUND"],
            "list_date": [keys[0], keys[2], keys[0], keys[0]],
            "delist_date": [None, None, keys[3], None],
        }
    )
    basic.to_parquet(root / "metadata/fund_basic.parquet", index=False)
    pd.DataFrame({"trade_date": keys}).to_parquet(
        root / "metadata/trading_sessions.parquet", index=False
    )
    for date in keys:
        daily = pd.DataFrame(
            {
                "ts_code": basic["ts_code"],
                "trade_date": date,
                "open": 1.0,
                "high": 1.1,
                "low": 0.9,
                "close": 1.0,
                "vol": 100.0,
                "amount": 20_000.0,
            }
        )
        daily.to_parquet(root / f"raw/fund_daily/{date}.parquet", index=False)
        pd.DataFrame(
            {"ts_code": basic["ts_code"], "trade_date": date, "adj_factor": 1.0}
        ).to_parquet(root / f"raw/fund_adj/{date}.parquet", index=False)
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "all_exchange_etf_daily_cache_v1",
                "start": keys[0],
                "end": keys[-1],
            }
        )
    )
    context = load_all_etf_daily(
        root,
        start=str(dates[0].date()),
        as_of=str(dates[-1].date()),
        min_history_sessions=2,
        liquidity_window=2,
        min_median_amount_thousand=10_000.0,
    )
    assert set(context.symbols) == {"510001.SH", "159001.SZ", "160001.SZ"}
    assert context.eligibility.loc[dates[1], "510001.SH"]
    assert not context.eligibility.loc[dates[1], "159001.SZ"]
    assert context.eligibility.loc[dates[3], "160001.SZ"]
    assert not context.eligibility.loc[dates[4], "160001.SZ"]


def test_forward_referee_has_power_for_a_frozen_independent_signal() -> None:
    rng = np.random.default_rng(20260921)
    dates = pd.bdate_range("2025-01-02", periods=300)
    columns = [f"E{i:03d}" for i in range(120)]
    signal = pd.DataFrame(rng.normal(size=(300, 120)), index=dates, columns=columns)
    signal = signal.rank(axis=1, pct=True)
    control = pd.DataFrame(rng.normal(size=(300, 120)), index=dates, columns=columns)
    forward = 0.02 * (signal - 0.5) + pd.DataFrame(
        rng.normal(scale=0.002, size=signal.shape), index=dates, columns=columns
    )
    eligible = pd.DataFrame(True, index=dates, columns=columns)
    gates = ForwardGates(
        campaign_budget=64,
        alpha=0.05,
        min_names=100,
        min_days=250,
        min_signed_mean_ic=0.01,
        min_hac_t=2.0,
        top_fraction=0.1,
        min_top_label_coverage=0.95,
        min_top_excess_bp=5.0,
        min_top_excess_hac_t=1.5,
        max_abs_rank_corr=0.75,
        min_residual_mean_ic=0.005,
        min_residual_hac_t=1.5,
    )
    row, residual = evaluate_forward_candidate(
        signal,
        forward,
        eligible,
        {"CONTROL": control},
        candidate_id="SYNTHETIC",
        direction=1,
        start=str(dates[0].date()),
        end=str(dates[-1].date()),
        calendar=dates,
        entry_lag=2,
        horizon=5,
        gates=gates,
    )
    assert row["intrinsic_pass"]
    assert row["campaign_bonferroni_pass"]
    assert row["forward_days"] == 293
    assert residual.notna().any().any()


def test_downloader_extension_preserves_identity_and_unions_calendar(tmp_path, monkeypatch) -> None:
    entry = Path(__file__).parents[1] / "scripts/research/download_all_etf_daily.py"
    spec = importlib.util.spec_from_file_location("all_etf_downloader", entry)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    class Pro:
        sessions = ["20250102", "20250103"]
        identity = "ORIGINAL ETF"

        def fund_basic(self, **_kwargs):
            return pd.DataFrame(
                {"ts_code": ["510001.SH"], "name": [self.identity]}
            ).reindex(columns=module.FUND_BASIC_FIELDS.split(","))

        def trade_cal(self, **_kwargs):
            return pd.DataFrame({"cal_date": self.sessions, "is_open": 1})

        def fund_daily(self, trade_date):
            values = {column: 1.0 for column in module.DAILY_COLUMNS}
            values.update({"ts_code": "510001.SH", "trade_date": trade_date})
            return pd.DataFrame([values])

        def fund_adj(self, trade_date):
            return pd.DataFrame(
                [{"ts_code": "510001.SH", "trade_date": trade_date, "adj_factor": 1.0}]
            )

    pro = Pro()
    monkeypatch.setitem(__import__("sys").modules, "tushare", SimpleNamespace(pro_api=lambda _token: pro))
    monkeypatch.setenv("TUSHARE_TOKEN", "test-token")
    root = tmp_path / "cache"

    def args(start, end):
        return SimpleNamespace(
            data_root=root,
            source_project=tmp_path,
            start=start,
            end=end,
            attempts=1,
            rate_seconds=0.0,
            progress_every=10,
        )

    module.download(args("20250102", "20250103"))
    pro.sessions = ["20250106"]
    pro.identity = "MUTATED ETF"
    module.download(args("20250106", "20250106"))
    calendar = pd.read_parquet(root / "metadata/trading_sessions.parquet")
    basic = pd.read_parquet(root / "metadata/fund_basic.parquet")
    manifest = json.loads((root / "manifest.json").read_text())
    assert calendar["trade_date"].tolist() == ["20250102", "20250103", "20250106"]
    assert basic.loc[0, "name"] == "ORIGINAL ETF"
    assert manifest["start"] == "20250102"
    assert manifest["end"] == "20250106"
    assert manifest["session_count"] == 3
