"""Prelabel VIX risk-shock transmission scores for fixed-14 ETF groups."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd

from . import etf_group_us_sector as sector

WINDOW = 60
CANDIDATES = sector.CANDIDATES
MECHANISMS = {
    "vix_risk_same_day_response_60": 1,
    "vix_risk_delayed_response_60": 1,
    "vix_risk_sign_asymmetry_60": 1,
}


def read_vix(path: Path, expected_sha256: str, cutoff: pd.Timestamp) -> pd.Series:
    if sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("VIX snapshot hash changed")
    frame = pd.read_csv(path, parse_dates=["observation_date"])
    if (list(frame.columns) != ["observation_date", "VIXCLS"] or
            frame.observation_date.max() > cutoff or
            frame.observation_date.duplicated().any() or
            not frame.observation_date.is_monotonic_increasing):
        raise ValueError("VIX source chronology or cold cutoff changed")
    values = pd.to_numeric(frame.set_index("observation_date").VIXCLS, errors="coerce")
    if values.dropna().le(0).any():
        raise ValueError("nonpositive VIX close")
    return values


def align_vix_shock(vix: pd.Series, china_calendar: pd.DatetimeIndex) -> pd.Series:
    if china_calendar.has_duplicates or not china_calendar.is_monotonic_increasing:
        raise ValueError("invalid China calendar")
    valid = vix.dropna().sort_index()
    if valid.index.has_duplicates:
        raise ValueError("duplicate US source date")
    us_shock = np.log(valid).diff().dropna().rename("shock")
    right = us_shock.reset_index().rename(columns={us_shock.index.name or "index": "us_date"})
    left = pd.DataFrame({"china_date": china_calendar})
    matched = pd.merge_asof(left, right, left_on="china_date", right_on="us_date",
                            direction="backward", allow_exact_matches=False)
    age = (matched.china_date - matched.us_date).dt.days
    shock = matched.shock.where(age.gt(0) & age.le(5))
    return pd.Series(shock.to_numpy(), index=china_calendar, name="vix_log_change")


def score_atoms(close: pd.DataFrame, shock: pd.Series) -> dict[str, pd.DataFrame]:
    original = sector.score_atoms(close, shock)
    return {new: original[old] for new, old in zip(MECHANISMS, sector.MECHANISMS)}


def build_atoms(panels: dict, config: dict) -> dict[str, pd.DataFrame]:
    if (config.get("source_type") != "us_vix" or config.get("windows") != [WINDOW]
            or set(config.get("mechanisms", {})) != {name.removesuffix("_60") for name in MECHANISMS}
            or any(item.get("direction") != 1 for item in config["mechanisms"].values())
            or set(panels) != {"close", "us_vix_shock"}):
        raise ValueError("VIX draft contract changed")
    return score_atoms(panels["close"], panels["us_vix_shock"])


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
