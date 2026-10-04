"""Proposed prelabel SOX-minus-Nasdaq100 transmission scores for fixed-14 ETF groups."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd

WINDOW = 60
BENCHMARKS = {"NASDAQSOX", "NASDAQ100"}
MECHANISMS = {
    "sox_specific_same_day_response_60": 1,
    "sox_specific_delayed_response_60": 1,
    "sox_specific_sign_asymmetry_60": 1,
}
CANDIDATES = {
    "159995.SZ", "159516.SZ", "515880.SH", "159852.SZ", "562500.SH",
    "159732.SZ", "513130.SH", "159992.SZ", "513120.SH", "518880.SH",
    "512400.SH", "512890.SH", "159611.SZ", "513100.SH",
}


def read_fred(path: Path, expected: str, expected_sha256: str, cutoff: pd.Timestamp) -> pd.Series:
    if sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError(f"source changed: {path}")
    frame = pd.read_csv(path, parse_dates=["observation_date"])
    if list(frame.columns) != ["observation_date", expected]:
        raise ValueError(f"unexpected FRED series: {path}")
    if (frame.observation_date.max() > cutoff or frame.observation_date.duplicated().any()
            or not frame.observation_date.is_monotonic_increasing):
        raise ValueError("source extends beyond cold cutoff or has invalid dates")
    series = frame.set_index("observation_date")[expected].astype(float)
    if series.dropna().le(0).any():
        raise ValueError("nonpositive SOX/NDX index level")
    return series


def align_specific_shock(sox: pd.Series, ndx: pd.Series,
                         china_calendar: pd.DatetimeIndex) -> pd.Series:
    """Use the last common valid US observation strictly before each China D."""
    if china_calendar.has_duplicates or not china_calendar.is_monotonic_increasing:
        raise ValueError("invalid China exchange calendar")
    common = pd.concat({"sox": sox, "ndx": ndx}, axis=1).dropna().sort_index()
    if common.index.has_duplicates:
        raise ValueError("duplicate US source date")
    us = common.pct_change(fill_method=None).dropna()
    us["shock"] = us.sox - us.ndx
    right = us[["shock"]].reset_index().rename(columns={us.index.name or "index": "us_date"})
    left = pd.DataFrame({"china_date": china_calendar})
    matched = pd.merge_asof(left, right, left_on="china_date", right_on="us_date",
                            direction="backward", allow_exact_matches=False)
    age = (matched.china_date - matched.us_date).dt.days
    shock = matched.shock.where(age.le(5) & age.gt(0))
    return pd.Series(shock.to_numpy(), index=china_calendar, name="sox_minus_ndx")


def score_atoms(close: pd.DataFrame, shock: pd.Series) -> dict[str, pd.DataFrame]:
    if (set(close.columns) != CANDIDATES or close.columns.has_duplicates or
            not close.index.equals(shock.index) or close.index.has_duplicates or
            not close.index.is_monotonic_increasing):
        raise ValueError("fixed ETF population or source calendar changed")
    returns = close.pct_change(fill_method=None)
    full = returns.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW)
    full &= shock.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW).to_numpy()[:, None]

    variance = shock.rolling(WINDOW, min_periods=WINDOW).var(ddof=0).where(lambda x: x.gt(0))
    same_beta = returns.rolling(WINDOW, min_periods=WINDOW).cov(shock, ddof=0).div(variance, axis=0)
    same = same_beta.where(full).shift(1).mul(shock, axis=0)

    lagged = shock.shift(1)
    lag_full = full & lagged.notna().rolling(WINDOW, min_periods=WINDOW).sum().eq(WINDOW).to_numpy()[:, None]
    lag_var = lagged.rolling(WINDOW, min_periods=WINDOW).var(ddof=0).where(lambda x: x.gt(0))
    lag_beta = returns.rolling(WINDOW, min_periods=WINDOW).cov(lagged, ddof=0).div(lag_var, axis=0)
    delayed = lag_beta.where(lag_full).shift(1).mul(shock, axis=0)

    plus = shock.where(shock.gt(0))
    minus = shock.where(shock.lt(0))
    enough = shock.gt(0).rolling(WINDOW, min_periods=WINDOW).sum().ge(10)
    enough &= shock.lt(0).rolling(WINDOW, min_periods=WINDOW).sum().ge(10)
    plus_beta = returns.where(shock.gt(0), axis=0).rolling(WINDOW, min_periods=10).cov(plus, ddof=0)
    plus_beta = plus_beta.div(plus.rolling(WINDOW, min_periods=10).var(ddof=0).where(lambda x: x.gt(0)), axis=0)
    minus_beta = returns.where(shock.lt(0), axis=0).rolling(WINDOW, min_periods=10).cov(minus, ddof=0)
    minus_beta = minus_beta.div(minus.rolling(WINDOW, min_periods=10).var(ddof=0).where(lambda x: x.gt(0)), axis=0)
    plus_beta = plus_beta.where(full & enough.to_numpy()[:, None]).shift(1)
    minus_beta = minus_beta.where(full & enough.to_numpy()[:, None]).shift(1)
    branch = plus_beta.where(shock.gt(0), minus_beta.where(shock.lt(0)))
    asymmetric = branch.mul(shock, axis=0)
    return {name: score.replace([np.inf, -np.inf], np.nan) for name, score in {
        "sox_specific_same_day_response_60": same,
        "sox_specific_delayed_response_60": delayed,
        "sox_specific_sign_asymmetry_60": asymmetric,
    }.items()}


def build_atoms(panels: dict, config: dict) -> dict[str, pd.DataFrame]:
    if (config.get("source_type") != "us_sector" or config.get("windows") != [WINDOW]
            or set(config.get("mechanisms", {})) != {
                "sox_specific_same_day_response", "sox_specific_delayed_response",
                "sox_specific_sign_asymmetry"}
            or any(row.get("direction") != 1 for row in config["mechanisms"].values())
            or set(panels) != {"close", "us_sector_shock"}):
        raise ValueError("frozen SOX-specific source contract changed")
    return score_atoms(panels["close"], panels["us_sector_shock"])


def leakage_checks(panels: dict, config: dict, cut: str | pd.Timestamp) -> dict[str, bool]:
    cut = pd.Timestamp(cut)
    full = build_atoms(panels, config)
    prefix = build_atoms({key: frame.loc[:cut].copy() for key, frame in panels.items()}, config)
    changed = {key: frame.copy() for key, frame in panels.items()}
    for frame in changed.values():
        frame.loc[frame.index > cut] *= 1.73
    perturbed = build_atoms(changed, config)
    for name, atom in full.items():
        pd.testing.assert_frame_equal(atom.loc[:cut], prefix[name], check_exact=False,
                                      rtol=1e-10, atol=1e-12)
        pd.testing.assert_frame_equal(atom.loc[:cut], perturbed[name].loc[:cut],
                                      check_exact=False, rtol=1e-10, atol=1e-12)
    return {f"{name}:prefix_and_future_perturbation": True for name in full}
