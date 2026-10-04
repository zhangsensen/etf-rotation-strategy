"""Prelabel offshore USDCNH transmission scores for fixed-14 ETF groups."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd

from . import etf_group_us_sector as sector

WINDOW = 60
CANDIDATES = sector.CANDIDATES
MECHANISMS = {
    "cnh_same_day_response_60": 1,
    "cnh_delayed_response_60": 1,
    "cnh_sign_asymmetry_60": 1,
}


def read_cnh(path: Path, expected_sha256: str, cutoff: pd.Timestamp) -> pd.Series:
    """FXCM offshore USDCNH mid close from the pinned local parquet snapshot."""
    if sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("USDCNH snapshot hash changed")
    frame = pd.read_parquet(path)
    if set(["ts_code", "trade_date", "bid_close", "ask_close"]) - set(frame.columns):
        raise ValueError("unexpected USDCNH source columns")
    dates = pd.to_datetime(frame["trade_date"].astype(str))
    mid = pd.Series(((frame["bid_close"] + frame["ask_close"]) / 2).to_numpy(), index=dates)
    if mid.index.duplicated().any():
        raise ValueError("duplicate USDCNH source date")
    mid = mid.sort_index()
    if mid.index.max() > cutoff or not mid.index.is_monotonic_increasing:
        raise ValueError("USDCNH source extends beyond cold cutoff or chronology invalid")
    if mid.dropna().le(0).any():
        raise ValueError("nonpositive USDCNH mid close")
    return mid.rename("usdcnh_mid")


def align_cnh_shock(mid: pd.Series, china_calendar: pd.DatetimeIndex) -> pd.Series:
    """Use the last FXCM observation strictly before each China D, at most 5 days old."""
    if china_calendar.has_duplicates or not china_calendar.is_monotonic_increasing:
        raise ValueError("invalid China calendar")
    valid = mid.dropna().sort_index()
    if valid.index.has_duplicates:
        raise ValueError("duplicate USDCNH source date")
    us_shock = np.log(valid).diff().dropna().rename("shock")
    right = us_shock.reset_index().rename(columns={us_shock.index.name or "index": "us_date"})
    left = pd.DataFrame({"china_date": china_calendar})
    matched = pd.merge_asof(left, right, left_on="china_date", right_on="us_date",
                            direction="backward", allow_exact_matches=False)
    age = (matched.china_date - matched.us_date).dt.days
    shock = matched.shock.where(age.gt(0) & age.le(5))
    return pd.Series(shock.to_numpy(), index=china_calendar, name="cnh_log_change")


def score_atoms(close: pd.DataFrame, shock: pd.Series) -> dict[str, pd.DataFrame]:
    original = sector.score_atoms(close, shock)
    return {new: original[old] for new, old in zip(MECHANISMS, sector.MECHANISMS)}


def build_atoms(panels: dict, config: dict) -> dict[str, pd.DataFrame]:
    if (config.get("source_type") != "ext_cnh" or config.get("windows") != [WINDOW]
            or set(config.get("mechanisms", {})) != {name.removesuffix("_60") for name in MECHANISMS}
            or any(item.get("direction") != 1 for item in config["mechanisms"].values())
            or set(panels) != {"close", "ext_cnh_shock"}):
        raise ValueError("USDCNH draft contract changed")
    return score_atoms(panels["close"], panels["ext_cnh_shock"])


def leakage_checks(panels: dict, config: dict, cut: str | pd.Timestamp) -> dict[str, bool]:
    cut = pd.Timestamp(cut)
    full = build_atoms(panels, config)
    prefix = build_atoms({key: frame.loc[:cut].copy() for key, frame in panels.items()}, config)
    changed = {key: frame.copy() for key, frame in panels.items()}
    for frame in changed.values():
        frame.loc[frame.index > cut] *= 1.73
    perturbed = build_atoms(changed, config)
    for name, atom in full.items():
        pd.testing.assert_frame_equal(atom.loc[:cut], prefix[name], rtol=1e-10, atol=1e-12)
        pd.testing.assert_frame_equal(atom.loc[:cut], perturbed[name].loc[:cut],
                                      rtol=1e-10, atol=1e-12)
    return {f"{name}:prefix_and_future_perturbation": True for name in full}
