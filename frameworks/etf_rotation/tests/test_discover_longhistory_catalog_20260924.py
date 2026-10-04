"""Tests for discover_longhistory_catalog_20260924.py's Phase 1/2 boundary
(PREREG_LONGHISTORY_DISCOVERY_20260924.md §1: discovery window signal
dates 2015-01-05..2024-12-31, never reading past that date here) and
CATALOG.csv dispatch coverage."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/research"))
import discover_longhistory_catalog_20260924 as driver  # noqa: E402


def test_proxy_close_never_reads_past_discovery_end():
    close = driver.load_proxy_close()
    assert close.index.max() <= pd.Timestamp(driver.DISCOVERY_END)
    assert close.index.min() >= pd.Timestamp("2015-01-05")
    assert close.shape[1] == 8
    assert set(close.columns) == {
        "cn_technology_manufacturing", "hk_technology", "us_large_growth",
        "innovative_pharma", "gold", "metals_equity", "dividend_low_vol",
        "electric_power",
    }


def test_catalog_every_row_has_a_dispatchable_builder():
    catalog = pd.read_csv(driver.CATALOG_PATH)
    assert len(catalog) == len(set(catalog.name)), "duplicate candidate names in CATALOG.csv"
    for _, row in catalog.iterrows():
        name, source = row["name"], row["source"]
        if source == "a":
            assert name in driver._A_BUILD_FNS or name in driver._A_MOMENTUM_SKIP, name
        elif source == "b":
            assert name in driver._B_BUILD_FNS or name in driver._B_TRAILING_RETURN, name
        else:
            pytest.fail(f"unknown source tag: {source}")


def test_catalog_columns_match_prereg_schema():
    catalog = pd.read_csv(driver.CATALOG_PATH)
    assert list(catalog.columns) == ["name", "formula", "window", "source", "created_after_viewing_2025"]
    assert set(catalog.source) <= {"a", "b"}
    assert set(catalog.created_after_viewing_2025) <= {"是", "否"}
    # (a) candidates are all pre-existing registered definitions -> always
    # created with knowledge of prior rounds' 2025-window IC results.
    assert (catalog.loc[catalog.source == "a", "created_after_viewing_2025"] == "是").all()
    # (b) candidates are textbook literature formulas, chosen without
    # reference to this campaign's own observed 2025 labels.
    assert (catalog.loc[catalog.source == "b", "created_after_viewing_2025"] == "否").all()


def test_no_label_columns_in_any_phase1_output():
    """Phase 1 must never read or emit a forward-return/label-derived
    column -- a structural guard, not just a promise in a docstring."""
    struct = pd.read_csv("runtime_outputs/etf_rotation_research/longhistory_discovery_20260924/structural_diagnostics.csv")
    dedup = pd.read_csv("runtime_outputs/etf_rotation_research/longhistory_discovery_20260924/dedup_precheck.csv")
    forbidden = {"ic", "ic_mean", "label", "forward_return", "hac_t", "return"}
    assert not (forbidden & set(c.lower() for c in struct.columns))
    assert not (forbidden & set(c.lower() for c in dedup.columns))
