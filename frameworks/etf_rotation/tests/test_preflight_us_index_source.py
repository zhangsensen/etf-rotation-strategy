"""US-index source preflight must not give a same-date US close to A-share D."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/preflight_us_index_source.py"
spec = importlib.util.spec_from_file_location("preflight_us_index_source", SCRIPT)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


def test_us_close_requires_a_later_a_share_date():
    source = pd.DataFrame({"source_date": pd.to_datetime(["2026-01-05", "2026-01-06"]),
                           "return": [0.01, -0.02]})
    calendar = pd.DatetimeIndex(pd.to_datetime(["2026-01-05", "2026-01-06", "2026-01-07"]))
    aligned = preflight.align_known_returns(source, calendar)
    assert not aligned.loc["2026-01-05", "available"]
    assert aligned.loc["2026-01-06", "return"] == pytest.approx(0.01)
    assert aligned.loc["2026-01-07", "return"] == pytest.approx(-0.02)


def test_us_close_is_not_carried_indefinitely():
    source = pd.DataFrame({"source_date": pd.to_datetime(["2026-01-05"]),
                           "return": [0.01]})
    calendar = pd.DatetimeIndex(pd.to_datetime(["2026-01-06", "2026-01-12"]))
    aligned = preflight.align_known_returns(source, calendar)
    assert aligned.loc["2026-01-06", "available"]
    assert not aligned.loc["2026-01-12", "available"]
    assert pd.isna(aligned.loc["2026-01-12", "return"])
