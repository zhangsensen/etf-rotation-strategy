"""Tests for discover_longhistory_ic_20260924.py's Phase 2 label/IC/
selection logic (PREREG_LONGHISTORY_DISCOVERY_20260924.md §3-4)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/research"))
import discover_longhistory_ic_20260924 as phase2  # noqa: E402


def _tiny_close(n=20, k=4, seed=5):
    idx = pd.bdate_range("2020-01-01", periods=n)
    rng = np.random.default_rng(seed)
    names = [f"g{i}" for i in range(k)]
    returns = pd.DataFrame(rng.normal(0, 0.01, (n, k)), index=idx, columns=names)
    return (1 + returns).cumprod()


def test_build_label_purges_the_last_6_rows():
    close = _tiny_close(n=20)
    label = phase2.build_label(close)
    # Independent hand formula.
    expected = close.shift(-6) / close.shift(-1) - 1.0
    pd.testing.assert_frame_equal(label, expected, check_exact=False, rtol=1e-9, atol=1e-12)
    # The last 6 signal dates can never have a label (purge): D+1 or D+6
    # would need rows past the panel's own end.
    assert label.iloc[-6:].isna().all().all()
    # A date with enough room ahead DOES get a real label.
    assert label.iloc[0].notna().all()


def test_build_label_never_needs_data_past_the_panel_end():
    """The label at the very last in-range row equals close(D+6)/close(D+1)-1
    computed directly from ONLY the rows already in `close` -- confirms no
    implicit extension/lookup beyond the panel."""
    close = _tiny_close(n=20)
    label = phase2.build_label(close)
    d = 10
    expected_row = close.iloc[d + 6] / close.iloc[d + 1] - 1.0
    pd.testing.assert_series_equal(label.iloc[d], expected_row, check_names=False, rtol=1e-9)


def test_daily_spearman_ic_hand_formula():
    close = _tiny_close(n=30, seed=9)
    atom = close.pct_change(5)
    label = phase2.build_label(close)
    ic = phase2.daily_spearman_ic(atom, label)

    common_idx = atom.index.intersection(label.index)
    valid = atom.loc[common_idx].notna().all(axis=1) & label.loc[common_idx].notna().all(axis=1)
    d = common_idx[valid][3]
    expected = atom.loc[d].rank().corr(label.loc[d].rank())
    assert abs(ic.loc[d] - expected) < 1e-9


def test_mean_abs_daily_rank_corr_detects_identical_panels():
    close = _tiny_close(n=30, seed=15)
    atom = close.pct_change(5)
    corr = phase2.mean_abs_daily_rank_corr(atom, atom)
    assert corr is not None and abs(corr - 1.0) < 1e-9


def test_mean_abs_daily_rank_corr_flips_sign_but_stays_flagged():
    """A candidate and its own negative are perfectly ANTI-correlated in
    raw terms, but the ABS() convention (matching the campaign's
    established dedup metric) must still flag them as redundant -- this
    is exactly why momentum_5/reversal_5 (identical formula, opposite a
    priori label) collapse via this mechanism rather than a hand-picked
    exclusion."""
    close = _tiny_close(n=30, seed=21)
    atom = close.pct_change(5)
    corr = phase2.mean_abs_daily_rank_corr(atom, -atom)
    assert corr is not None and abs(corr - 1.0) < 1e-9
