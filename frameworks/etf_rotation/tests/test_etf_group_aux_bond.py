"""Timing and version boundaries for the domestic-bond auxiliary batch."""
import copy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from etf_strategy.core import etf_group_aux_bond as bond
from etf_strategy.core.etf_group_run_rules import validate_ic_discovery_config


CONFIG = Path(__file__).resolve().parents[1] / "configs/group_ic_bond_aux_20260925.yaml"


def test_bond_score_uses_only_information_through_signal_close():
    calendar = pd.bdate_range("2024-01-01", periods=150)
    returns = np.tile([0.001, -0.0008, 0.0006, -0.0005, 0.0009], 30)
    bond_close = pd.Series(100 * np.cumprod(1 + returns), index=calendar)
    etf_close = pd.DataFrame({
        "a": 100 * np.cumprod(1 + returns * 1.5),
        "b": 100 * np.cumprod(1 - returns * 0.5),
    }, index=calendar)
    config = yaml.safe_load(CONFIG.read_text())
    panels = {"close": etf_close, "bond_close": pd.DataFrame({"511010.SH": bond_close})}
    scores = bond.build_atoms(panels, config)
    assert list(scores) == ["bond_trend_exposure_60"]
    assert scores["bond_trend_exposure_60"].notna().all(axis=1).sum() > 50
    assert bond.leakage_checks(panels, config, str(calendar[100].date())) == {
        "bond_trend_exposure_60": True}


def test_250_day_screen_is_explicit_and_cannot_rejudge_old_definitions():
    config = yaml.safe_load(CONFIG.read_text())
    validate_ic_discovery_config(config)
    for changes in ({"as_of": "2026-09-17"}, {"rejudge_of": "old_batch"}):
        altered = {**config, **changes}
        with pytest.raises(ValueError):
            validate_ic_discovery_config(altered)
    altered = copy.deepcopy(config)
    altered["screens"]["min_days"] = 360
    with pytest.raises(ValueError, match="min_days"):
        validate_ic_discovery_config(altered)
