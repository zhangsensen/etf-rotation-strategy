"""Prelabel US large-cap value-minus-growth transmission scores for ETF groups."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from . import etf_group_us_sector as sector

WINDOW = 60
CANDIDATES = sector.CANDIDATES
MECHANISMS = {
    "us_style_same_day_response_60": 1,
    "us_style_delayed_response_60": 1,
    "us_style_sign_asymmetry_60": 1,
}


def read_style(path: Path, series: str, expected_sha256: str, cutoff: pd.Timestamp) -> pd.Series:
    if series not in {"NASDAQNQUSLV", "NASDAQNQUSLG"}:
        raise ValueError("unapproved US style index")
    return sector.read_fred(path, series, expected_sha256, cutoff)


def align_style_shock(value: pd.Series, growth: pd.Series,
                      china_calendar: pd.DatetimeIndex) -> pd.Series:
    return sector.align_specific_shock(value, growth, china_calendar).rename("us_value_minus_growth")


def score_atoms(close: pd.DataFrame, shock: pd.Series) -> dict[str, pd.DataFrame]:
    original = sector.score_atoms(close, shock)
    return {new: original[old] for new, old in zip(MECHANISMS, sector.MECHANISMS)}


def build_atoms(panels: dict, config: dict) -> dict[str, pd.DataFrame]:
    if (config.get("source_type") != "us_style" or config.get("windows") != [WINDOW]
            or set(config.get("mechanisms", {})) != {name.removesuffix("_60") for name in MECHANISMS}
            or any(item.get("direction") != 1 for item in config["mechanisms"].values())
            or set(panels) != {"close", "us_style_shock"}):
        raise ValueError("US style draft contract changed")
    return score_atoms(panels["close"], panels["us_style_shock"])


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
