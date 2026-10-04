"""Tests for the H20 step 2 script's label/purge logic
(PREREG_LONGHISTORY_DISCOVERY_20260924.md §7)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/research"))
import discover_longhistory_ic_h20_20260924 as h20ic  # noqa: E402


def _tiny_close(n=40, k=4, seed=7):
    idx = pd.bdate_range("2020-01-01", periods=n)
    rng = np.random.default_rng(seed)
    names = [f"g{i}" for i in range(k)]
    returns = pd.DataFrame(rng.normal(0, 0.01, (n, k)), index=idx, columns=names)
    return (1 + returns).cumprod()


def test_build_label_h20_purges_the_last_21_rows():
    close = _tiny_close(n=40)
    label = h20ic.build_label_h20(close)
    expected = close.shift(-21) / close.shift(-1) - 1.0
    pd.testing.assert_frame_equal(label, expected, check_exact=False, rtol=1e-9, atol=1e-12)
    assert label.iloc[-21:].isna().all().all()
    assert label.iloc[0].notna().all()


def test_build_label_h20_never_needs_data_past_the_panel_end():
    close = _tiny_close(n=40)
    label = h20ic.build_label_h20(close)
    d = 15
    expected_row = close.iloc[d + 21] / close.iloc[d + 1] - 1.0
    pd.testing.assert_series_equal(label.iloc[d], expected_row, check_names=False, rtol=1e-9)


def test_h20_constants_match_prereg():
    assert h20ic.HORIZON_H20 == 21
    assert h20ic.HAC_LAG_H20 == 30
    assert h20ic.SELECT_T == 3.0
    assert h20ic.DEDUP_THRESHOLD == 0.7
    assert h20ic.K_MAX == 10
