"""Stage-S66b family (round_680, main controller directive, 2026-09-21):
price-position / momentum control atoms for the S66 CGO admissions.

S66's 3 admissions (UW_SHARE_V2_250 x R2_VOL_SPIKE_FREQ_20, RP_CHANGE_V2_20
x R2_VOL_SPIKE_FREQ_20, GAIN_OVERHANG_V2_60 x VT_AUTOCORR_20) all have a
left leg with 0.49-0.71 rank corr against price-position/momentum series
(atom_health, round_678). This family builds the plain price-position and
momentum atoms needed to construct a "replace the CGO leg with plain
price position / return" control pair for each admission, so the
controller directive's 6 pairs can quantify whether the CGO accounting
adds anything beyond simple price position.

Atoms (6, matching exactly what the directive's 6 control pairs need --
NEG_ prefix atoms are pre-negated series, since the engine's rank_spread
operator has no leg-level sign flip; RET_60 was not in the directive's
named atom list (RET_20/RET_250/PRICE_POSITION_250) but is required by
control pair #6, so it is added here as a documented fix):
  RET_20, RET_60: close.pct_change(N).
  PRICE_POSITION_250: (close - 250d rolling min)/(250d rolling max - min).
  NEG_RET_20, NEG_RET_250: -1 * close.pct_change(N).
  NEG_PRICE_POSITION_250: -1 * PRICE_POSITION_250.
"""
from __future__ import annotations

import numpy as np

from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "RET_20",
    "RET_60",
    "PRICE_POSITION_250",
    "NEG_RET_20",
    "NEG_RET_250",
    "NEG_PRICE_POSITION_250",
)

_PP_WINDOW = 250
_PP_MIN_PERIODS = 120


def _build(panels, eligibility, data_root, config):
    del eligibility, data_root, config
    close = panels["close"]
    dates = close.index
    symbols = list(close.columns)
    out = {}

    ret20 = close.pct_change(20)
    ret60 = close.pct_change(60)
    ret250 = close.pct_change(250)
    roll_min = close.rolling(_PP_WINDOW, min_periods=_PP_MIN_PERIODS).min()
    roll_max = close.rolling(_PP_WINDOW, min_periods=_PP_MIN_PERIODS).max()
    price_position_250 = (close - roll_min) / (roll_max - roll_min).replace(0, np.nan)

    out["RET_20"] = ret20
    out["RET_60"] = ret60
    out["PRICE_POSITION_250"] = price_position_250
    out["NEG_RET_20"] = -ret20
    out["NEG_RET_250"] = -ret250
    out["NEG_PRICE_POSITION_250"] = -price_position_250

    aligned = {name: frame.reindex(index=dates, columns=symbols) for name, frame in out.items()}
    return {name: frame.where(np.isfinite(frame)) for name, frame in aligned.items()}


register_family(FamilyProvider("price_position_controls", "price_position_controls", _build))
