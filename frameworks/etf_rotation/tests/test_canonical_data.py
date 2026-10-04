"""Synthetic migration regressions; never copy market data into fixtures."""
import fcntl
import json

import numpy as np
import pandas as pd
import pytest

from etf_strategy.canonical_data import load_canonical_daily, reference_factors


@pytest.fixture
def store(tmp_path):
    dates = pd.bdate_range("2024-01-01", periods=140)
    symbols = ["510300.SH", "159995.SZ"]
    config = tmp_path / "universe.json"
    config.write_text(json.dumps({"etfs": [
        {"ts_code": symbols[0], "role": "benchmark"},
        {"ts_code": symbols[1], "role": "candidate"},
    ]}))
    for folder in ("1d", "adj_factor"):
        (tmp_path / folder).mkdir()
    for symbol, index in zip(symbols, [dates, dates[20:]]):
        close = 10 + np.arange(len(index)) / 10
        d = pd.DataFrame({"ts_code": symbol, "trade_date": index, "open": close,
                          "high": close + 1, "low": close - 1, "close": close,
                          "volume": 100., "turnover": 1000., "price_basis": "unadjusted"})
        d.to_parquet(tmp_path / "1d" / f"{symbol}.parquet", index=False)
        a = d[["ts_code", "trade_date"]].copy()
        a["adj_factor"] = 1.
        a.to_parquet(tmp_path / "adj_factor" / f"{symbol}.parquet", index=False)
    return tmp_path, config, dates


def test_adapter_preserves_missing_sessions_units_and_roles(store):
    root, config, dates = store
    p = load_canonical_daily(root, config, as_of=str(dates[-1].date()))
    assert p["close"]["159995.SZ"].iloc[:20].isna().all()
    assert p["amount"].iloc[-1].eq(1000).all()
    assert p["volume"].iloc[-1].eq(100).all()
    selected = load_canonical_daily(root, config, as_of=str(dates[-1].date()), roles=("candidate",))
    assert list(selected["close"].columns) == ["159995.SZ"]
    with pytest.raises(ValueError, match="Unknown universe role"):
        load_canonical_daily(root, config, as_of=str(dates[-1].date()), roles=("typo",))


def test_future_adjustment_does_not_change_cutoff_view(store):
    root, config, dates = store
    cutoff = str(dates[-2].date())
    before = load_canonical_daily(root, config, as_of=cutoff)
    path = root / "adj_factor/510300.SH.parquet"
    a = pd.read_parquet(path)
    a.loc[a.index[-1], "adj_factor"] = 10.
    a.to_parquet(path, index=False)
    after = load_canonical_daily(root, config, as_of=cutoff)
    pd.testing.assert_frame_equal(before["close"], after["close"])


def test_loader_filters_before_materializing_market_rows(store, monkeypatch):
    root, config, dates = store
    cutoff = dates[-20]
    original = pd.read_parquet
    seen = []
    def filtered_read(path, *args, **kwargs):
        assert kwargs.get('filters') == [('trade_date', '<=', cutoff)]
        result = original(path, *args, **kwargs)
        assert pd.to_datetime(result.trade_date).max() <= cutoff
        seen.append(path)
        return result
    monkeypatch.setattr(pd, 'read_parquet', filtered_read)
    load_canonical_daily(root, config, as_of=str(cutoff.date()))
    assert len(seen) == 4


def test_missing_adjustment_and_duplicate_dates_fail(store):
    root, config, dates = store
    path = root / "adj_factor/510300.SH.parquet"
    a = pd.read_parquet(path)
    a.iloc[1:].to_parquet(path, index=False)
    with pytest.raises(ValueError, match="adjustment"):
        load_canonical_daily(root, config, as_of=str(dates[-1].date()))
    pd.concat([a, a.iloc[:1]]).to_parquet(path, index=False)
    with pytest.raises(ValueError, match="duplicate"):
        load_canonical_daily(root, config, as_of=str(dates[-1].date()))


def test_stale_data_fails(store):
    root, config, dates = store
    with pytest.raises(ValueError, match="does not reach"):
        load_canonical_daily(root, config, as_of=str((dates[-1] + pd.Timedelta(days=1)).date()))


def test_update_lock_blocks_read(store):
    root, config, dates = store
    with (root / ".update.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="update in progress"):
            load_canonical_daily(root, config, as_of=str(dates[-1].date()))


def test_reference_factors_do_not_invent_warmup_or_prelisting_values(store):
    root, config, dates = store
    p = load_canonical_daily(root, config, as_of=str(dates[-1].date()))
    f = reference_factors(p)
    assert f["PRICE_POSITION_120D"]["510300.SH"].iloc[:119].isna().all()
    assert f["PRICE_POSITION_120D"]["159995.SZ"].iloc[:139].isna().all()
    assert f["PRICE_POSITION_120D"].iloc[-1].notna().all()
    assert f["BREAKOUT_20D"]["159995.SZ"].iloc[:40].isna().all()


def test_adjustment_changes_prices_but_not_volume_or_amount(store):
    root, config, dates = store
    path = root / "adj_factor/510300.SH.parquet"
    a = pd.read_parquet(path)
    a.loc[a.index[-1], "adj_factor"] = 2.
    a.to_parquet(path, index=False)
    p = load_canonical_daily(root, config, as_of=str(dates[-1].date()))
    assert p["close"]["510300.SH"].iloc[0] == 5.
    assert p["volume"]["510300.SH"].iloc[0] == 100.
    assert p["amount"]["510300.SH"].iloc[0] == 1000.
