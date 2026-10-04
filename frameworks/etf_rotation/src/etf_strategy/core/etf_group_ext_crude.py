"""Prelabel INE crude settlement transmission scores for fixed-14 ETF groups."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd

from . import etf_group_us_sector as sector

WINDOW = 60
CANDIDATES = sector.CANDIDATES
MECHANISMS = {
    "crude_same_day_response_60": 1,
    "crude_delayed_response_60": 1,
    "crude_sign_asymmetry_60": 1,
}


def read_crude(path: Path, expected_sha256: str, cutoff: pd.Timestamp) -> pd.Series:
    """INE crude front settlement from the pinned local parquet snapshot."""
    if sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("crude snapshot hash changed")
    frame = pd.read_parquet(path)
    if set(["ts_code", "trade_date", "settle"]) - set(frame.columns):
        raise ValueError("unexpected crude source columns")
    dates = pd.to_datetime(frame["trade_date"].astype(str))
    settle = pd.Series(frame["settle"].to_numpy(dtype=float), index=dates)
    if settle.index.duplicated().any():
        raise ValueError("duplicate crude source date")
    settle = settle.sort_index()
    if settle.index.max() > cutoff or not settle.index.is_monotonic_increasing:
        raise ValueError("crude source extends beyond cold cutoff or chronology invalid")
    if settle.dropna().le(0).any():
        raise ValueError("nonpositive crude settlement")
    return settle.rename("sc_settle")


def align_crude_shock(settle: pd.Series, china_calendar: pd.DatetimeIndex) -> pd.Series:
    """Same-calendar settlement log change, following the frozen close(D) rule.

    INE and SSE share the exchange-holiday calendar, so settlement at China
    date t is a close(D) input exactly like the domestic_benchmark auxiliary
    closes. The log change is differenced on the futures calendar first, so
    post-holiday sessions carry the cumulative settlement change; dates
    without a futures settlement stay missing instead of being filled.
    """
    if china_calendar.has_duplicates or not china_calendar.is_monotonic_increasing:
        raise ValueError("invalid China calendar")
    if settle.index.has_duplicates:
        raise ValueError("duplicate crude source date")
    shock = np.log(settle).diff().rename("crude_log_change").reindex(china_calendar)
    return shock


def score_atoms(close: pd.DataFrame, shock: pd.Series) -> dict[str, pd.DataFrame]:
    original = sector.score_atoms(close, shock)
    return {new: original[old] for new, old in zip(MECHANISMS, sector.MECHANISMS)}


def build_atoms(panels: dict, config: dict) -> dict[str, pd.DataFrame]:
    if (config.get("source_type") != "ext_crude" or config.get("windows") != [WINDOW]
            or set(config.get("mechanisms", {})) != {name.removesuffix("_60") for name in MECHANISMS}
            or any(item.get("direction") != 1 for item in config["mechanisms"].values())
            or set(panels) != {"close", "ext_crude_shock"}):
        raise ValueError("crude draft contract changed")
    return score_atoms(panels["close"], panels["ext_crude_shock"])


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
