"""Synthetic D-close and fixed-population checks; no ETF outcome labels."""
import numpy as np
import pandas as pd
import pytest
import yaml

from etf_strategy.core import etf_group_domestic_benchmark as source
from etf_strategy.core import etf_group_run_rules as run_rules


def fixture():
    dates = pd.bdate_range("2024-01-01", periods=110)
    wave = np.sin(np.arange(len(dates)) * .61) * .006
    large = 100 * np.cumprod(1 + wave)
    mid = 100 * np.cumprod(1 + wave + np.cos(np.arange(len(dates)) * .47) * .004)
    benchmark = pd.DataFrame({"510300.SH": large, "510500.SH": mid}, index=dates)
    close = pd.DataFrame({symbol: 100 * np.cumprod(1 + wave * (i + 1) / 15 +
                                                  np.sin(np.arange(len(dates)) * (.1 + i * .01)) * .002)
                          for i, symbol in enumerate(sorted(source.CANDIDATES))}, index=dates)
    cfg = yaml.safe_load(source_config().read_text())
    return {"close": close, "benchmark_close": benchmark}, cfg


def source_config():
    from pathlib import Path
    return Path(__file__).resolve().parents[1] / "configs/group_ic_cn_benchmark_aux_20260925.yaml"


def test_two_fixed_mechanisms_have_trailing_scores_and_no_future_dependence():
    panels, cfg = fixture()
    run_rules.validate_ic_discovery_config(cfg)
    assert run_rules.candidate_ids(cfg) == [f"{name}_60" for name in source.MECHANISMS]
    atoms = source.build_atoms(panels, cfg)
    assert set(atoms) == {f"{name}_60" for name in source.MECHANISMS}
    assert all(frame.iloc[-1].notna().all() for frame in atoms.values())
    assert all(frame.iloc[:60].isna().all().all() for frame in atoms.values())
    assert all(source.leakage_checks(panels, cfg, "2024-04-15").values())


def test_benchmark_order_and_window_are_frozen():
    panels, cfg = fixture()
    with pytest.raises(ValueError, match="purpose"):
        run_rules.validate_ic_discovery_config({**cfg, "source_type": "daily_rounds"})
    with pytest.raises(ValueError, match="benchmark calendar alignment"):
        source.build_atoms({**panels, "benchmark_close": panels["benchmark_close"].iloc[:, ::-1]}, cfg)
    with pytest.raises(ValueError, match="60-session"):
        source.build_atoms(panels, {**cfg, "windows": [20]})


def test_down_beta_requires_ten_down_days_and_complete_member_window():
    panels, cfg = fixture()
    changed = {key: frame.copy() for key, frame in panels.items()}
    changed["benchmark_close"].loc[:, "510300.SH"] = np.arange(len(changed["benchmark_close"])) + 100
    atoms = source.build_atoms(changed, cfg)
    assert atoms["cn_largecap_downside_resilience_60"].isna().all().all()
    changed = {key: frame.copy() for key, frame in panels.items()}
    changed["close"].iloc[-10, 0] = np.nan
    atoms = source.build_atoms(changed, cfg)
    assert pd.isna(atoms["cn_mid_large_style_transmission_60"].iloc[-1, 0])
    assert pd.isna(atoms["cn_largecap_downside_resilience_60"].iloc[-1, 0])
