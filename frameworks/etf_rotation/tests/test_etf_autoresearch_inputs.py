from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
import yaml


MODULE_PATH = (Path(__file__).resolve().parents[3] /
               "frameworks/etf_rotation/scripts/research/etf_autoresearch_inputs.py")
SPEC = importlib.util.spec_from_file_location("etf_autoresearch_inputs", MODULE_PATH)
inputs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inputs)


def _panels():
    dates = pd.date_range("2026-03-20", periods=3)
    cols = ["A.SH", "B.SZ"]
    return {name: pd.DataFrame(1.0, index=dates, columns=cols)
            for name in inputs.BASE_FIELDS}


def test_daily_profile_returns_six_base_panels_without_market_reads(monkeypatch):
    monkeypatch.setattr(pd, "read_csv", lambda *a, **k: pytest.fail("market data read"))
    monkeypatch.setattr(pd, "read_parquet", lambda *a, **k: pytest.fail("market data read"))
    result, manifest = inputs.load_inputs("daily", _panels(), inputs.PINNED_CUTOFF)
    assert set(result) == set(inputs.BASE_FIELDS)
    assert manifest["profile"] == "daily"
    assert manifest["config_sha256"] is None
    assert set(manifest["prepared_panel_sha256"]) == set(inputs.BASE_FIELDS)


def test_approved_profile_uses_aligner_and_broadcasts_sparse_shock(tmp_path, monkeypatch):
    profile = "us_vix"
    inputs._CONFIGS[profile] = "pinned.yaml"
    cfg_dir = tmp_path / "frameworks/etf_rotation/configs"
    cfg_dir.mkdir(parents=True)
    source = tmp_path / "snapshot.csv"
    source.write_text("synthetic source bytes")
    monkeypatch.setitem(inputs._EXPECTED_FILES, "vix_file", "snapshot.csv")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    cfg = {"source_type": profile, "as_of": "2026-03-24",
           "vix_file": "snapshot.csv", "vix_sha256": digest}
    (cfg_dir / "pinned.yaml").write_text(yaml.safe_dump(cfg))

    expected_shock = pd.Series([0.1, float("nan"), -0.2], index=_panels()["close"].index)
    calls = []
    engine = SimpleNamespace(
        __file__=str(MODULE_PATH),
        read_vix=lambda path, sha, cutoff: calls.append((path, sha, cutoff)) or pd.Series([9.0]),
        align_vix_shock=lambda series, calendar: calls.append(("align", calendar)) or expected_shock,
    )
    monkeypatch.setattr(inputs, "_source_spec", lambda *a: (
        engine, "us_vix_shock", [("vix_file", "vix_sha256", None, "read_vix")], "align_vix_shock"))
    result, manifest = inputs.load_inputs(profile, _panels(), inputs.PINNED_CUTOFF, tmp_path)
    shock = result["us_vix_shock"]
    assert list(shock.columns) == ["A.SH", "B.SZ"]
    assert shock.iloc[0].tolist() == [0.1, 0.1]
    assert shock.iloc[1].isna().all()
    assert shock.iloc[2].tolist() == [-0.2, -0.2]
    assert len(calls) == 2 and calls[1][0] == "align"
    assert manifest["source_sha256"][str(source)] == digest
    assert manifest["config_sha256"] == hashlib.sha256((cfg_dir / "pinned.yaml").read_bytes()).hexdigest()
    assert set(manifest["prepared_panel_sha256"]) == set(result)


def test_profile_listing_does_not_read_source_data(tmp_path, monkeypatch):
    monkeypatch.setattr(pd, "read_csv", lambda *a, **k: pytest.fail("market data read"))
    monkeypatch.setattr(pd, "read_parquet", lambda *a, **k: pytest.fail("market data read"))
    listing = inputs.describe_profiles(tmp_path)
    assert listing["daily"]["available"] is True
    assert listing["daily"]["approved"] is True
    assert all(not listing[name]["available"] for name in inputs._CONFIGS)
    assert all(isinstance(item["review_contract"], dict) for item in listing.values())
    minute = listing["minute"]["review_contract"]
    assert "minute_late_return" in minute["panels"]
    assert "c[:,-1]/o[:,180]-1" in minute["source_excerpt"]
    assert "after the final 15:00 bar" in minute["panels"]["minute_late_return"]["availability"]
    share = listing["share"]["review_contract"]
    assert "backward as-of" in share["panels"]["shares"]["formula"]
    assert "not verified publication time" in share["panels"]["shares"]["availability"]
    nav = listing["nav"]["review_contract"]
    assert "close on nav_date divided by reported unit_nav minus 1" in nav["panels"]["premium"]["formula"]
    assert "source vintage is not certified" in nav["limitations"][0]
    assert "strict-prior" in listing["ext_hktech"]["review_contract"]["panels"]["ext_hktech_shock"]["formula"]
    assert all("sha256" in ref for item in listing.values()
               for ref in item["review_contract"]["source_implementation"])


def _source_profile_fixture(tmp_path, profile, monkeypatch):
    data_root = tmp_path / "data"
    config_root = tmp_path / "frameworks/etf_rotation/configs"
    config_root.mkdir(parents=True)
    universe_root = tmp_path / "config"
    universe_root.mkdir()
    (universe_root / "etf_rotation_universe_v1.json").write_text(
        '{"etfs": [{"ts_code":"A.SH","role":"candidate"},'
        '{"ts_code":"B.SZ","role":"candidate"}]}'
    )
    config = {"source_type": profile, "data_root": str(data_root),
              "as_of": "2026-09-17", "max_stale_calendar_days": 7}
    monkeypatch.setattr(inputs, "CANONICAL_DATA_ROOT", data_root)
    name = f"{profile}.yaml"
    (config_root / name).write_text(yaml.safe_dump(config))
    monkeypatch.setitem(inputs._CONFIGS, profile, name)
    dates = pd.to_datetime(["2024-12-31", "2025-12-31", "2026-03-23", "2026-03-24"])
    panels = {key: pd.DataFrame(1.0, index=dates, columns=["A.SH", "B.SZ"])
              for key in inputs.BASE_FIELDS}
    for symbol in panels["close"].columns:
        folder = inputs._DATA_FOLDER[profile]
        raw_path = data_root / folder / f"{symbol}.parquet"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"synthetic raw parquet placeholder")
        if profile == "nav":
            price_path = data_root / "1d" / f"{symbol}.parquet"
            price_path.parent.mkdir(parents=True, exist_ok=True)
            price_path.write_bytes(b"synthetic price parquet placeholder")

    source_days = pd.to_datetime(["2024-12-30", "2025-12-30", "2026-03-20", "2026-03-24"])
    usable_days = pd.to_datetime(["2024-12-31", "2025-12-31", "2026-03-23", "2026-03-25"])
    if profile == "minute":
        stamps = []
        for day in pd.to_datetime(["2024-12-31", "2025-12-31", "2026-03-23", "2026-03-24", "2026-03-25"]):
            stamps.extend(day + pd.to_timedelta(list(range(571, 691)) + list(range(781, 901)), unit="m"))
        minute_frame = pd.DataFrame({
            "datetime": stamps, "open": 10.0, "high": 10.1, "low": 9.9,
            "close": 10.0, "volume": 1.0, "turnover": 10.0,
            "ts_code": "", "price_basis": "unadjusted",
        })
    else:
        observations = pd.DataFrame({
            "trade_date": source_days, "usable_from_date": usable_days,
            "fund_shares": [100.0, 110.0, 120.0, 130.0], "nav_date": source_days,
            "ann_date": source_days, "unit_nav": [9.0, 9.5, 9.8, 9.9],
        })

    def fake_read_parquet(path, filters=None, **kwargs):
        path = Path(path)
        symbol = path.stem
        if profile == "minute":
            assert filters == [("datetime", "<", inputs.PINNED_CUTOFF + pd.Timedelta(days=1))]
            frame = minute_frame.copy()
            frame["ts_code"] = symbol
            if filters:
                field, op, value = filters[0]
                frame = frame.loc[frame[field] < value]
            return frame.reset_index(drop=True)
        if path.parent.name == "1d":
            assert filters == [("trade_date", "<=", inputs.PINNED_CUTOFF)]
            frame = pd.DataFrame({"ts_code": symbol,
                                  "trade_date": pd.to_datetime(["2024-12-30", "2025-12-30", "2026-03-20", "2026-03-24", "2026-03-25"]),
                                  "close": [10.0, 10.5, 11.0, 11.1, 11.2], "price_basis": "unadjusted"})
            if filters:
                field, op, value = filters[0]
                frame = frame.loc[frame[field] <= value]
            return frame.reset_index(drop=True)
        frame = observations.copy()
        frame["ts_code"] = symbol
        frame["usable_from_date"] = frame["usable_from_date"].astype("datetime64[ns]")
        if filters:
            assert filters == [("usable_from_date", "<=", inputs.PINNED_CUTOFF)]
            field, op, value = filters[0]
            if field == "usable_from_date":
                frame = frame.loc[frame[field] <= value]
        return frame.reset_index(drop=True)

    monkeypatch.setattr(pd, "read_parquet", fake_read_parquet)
    return config, panels


@pytest.mark.parametrize("profile", ["minute", "share", "nav"])
def test_source_profiles_cutoff_transform_and_prefix_contract(tmp_path, monkeypatch, profile):
    _source_profile_fixture(tmp_path, profile, monkeypatch)
    result, manifest = inputs.load_inputs(profile, _panels_for_source_profile(),
                                           inputs.PINNED_CUTOFF, tmp_path)
    expected = set(inputs.BASE_FIELDS) | set(inputs._PROFILE_PANELS[profile])
    assert set(result) == expected
    assert all(frame.index.equals(result["close"].index)
               and frame.columns.equals(result["close"].columns) for frame in result.values())
    assert manifest["source_sha256"]
    assert manifest["loader_sha256"]["etf_group_sources"]
    assert all(set(v["prefix_reconstruction"]) == {"2024-12-31", "2025-12-31"}
               for v in manifest["loader_diagnostics"]["by_symbol"].values())
    assert result[list(inputs._PROFILE_PANELS[profile])[0]].loc["2026-03-24"].notna().all()


def _panels_for_source_profile():
    dates = pd.to_datetime(["2024-12-31", "2025-12-31", "2026-03-23", "2026-03-24"])
    return {name: pd.DataFrame(1.0, index=dates, columns=["A.SH", "B.SZ"])
            for name in inputs.BASE_FIELDS}


def test_feature_diagnostics_preserve_missingness_and_separate_broadcast_from_time_variation():
    dates = pd.date_range('2026-03-20', periods=3)
    panels = {'broadcast': pd.DataFrame({'a': [1., 2., 2.], 'b': [1., 2., 2.]}, index=dates),
              'sparse': pd.DataFrame({'a': [1., float('nan'), 3.], 'b': [2., 2., 2.]}, index=dates)}
    report = inputs.summarize_feature_panels(panels)
    assert report['label_accessed'] is False
    assert report['panels']['broadcast']['nonconstant_cross_section_days'] == 0
    assert report['panels']['broadcast']['changed_pairs'] == 2
    assert report['panels']['sparse']['complete_population_days'] == 2
    assert report['panels']['sparse']['consecutive_valid_pairs'] == 2
    assert panels['sparse'].isna().sum().sum() == 1
    future = {'bad': pd.DataFrame({'a': [1.]}, index=pd.to_datetime(['2026-03-25']))}
    with pytest.raises(ValueError, match='cold cutoff'):
        inputs.summarize_feature_panels(future)
