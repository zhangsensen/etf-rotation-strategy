"""Tests for the H20 CATALOG addendum (PREREG_LONGHISTORY_DISCOVERY_
20260924.md §7, step 1): the 3 new library-HAS_IC additions dispatch
correctly and the frozen H5 CATALOG.csv's own 57 rows are untouched."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/research"))
import discover_longhistory_catalog_h20_20260924 as h20  # noqa: E402
import discover_longhistory_catalog_20260924 as phase1  # noqa: E402


def test_catalog_h20_is_frozen_57_plus_exactly_3_new():
    catalog_h20 = pd.read_csv(h20.CATALOG_H20_PATH)
    original = pd.read_csv(phase1.CATALOG_PATH)
    assert len(catalog_h20) == len(original) + 3
    assert set(original.name) <= set(catalog_h20.name)
    new_names = set(catalog_h20.name) - set(original.name)
    assert new_names == {"beta_asymmetry_60", "market_residual_abs_cluster_20", "market_coskewness_20"}


def test_original_57_rows_byte_identical_in_h20_catalog():
    """The frozen H5 CATALOG.csv rows must not be edited when building
    CATALOG_H20.csv -- only appended to."""
    catalog_h20 = pd.read_csv(h20.CATALOG_H20_PATH)
    original = pd.read_csv(phase1.CATALOG_PATH)
    merged = original.merge(catalog_h20, on="name", suffixes=("_orig", "_h20"))
    assert len(merged) == len(original)
    for col in ("formula", "window", "source", "created_after_viewing_2025"):
        assert (merged[f"{col}_orig"] == merged[f"{col}_h20"]).all()


def test_new_build_fns_are_close_only_and_dispatch():
    close = phase1.load_proxy_close()
    for name, fn in h20._NEW_BUILD_FNS.items():
        out = fn(close)
        assert isinstance(out, pd.DataFrame)
        assert out.shape[1] == 8
        assert out.index.equals(close.index)
