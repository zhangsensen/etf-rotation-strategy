"""Stage-S71 family (round_687, main controller directive, 2026-09-21):
S64's strongest pair (PERMENT_TURNOVER_SPLIT_20 x UNDERWATER_FRAC_CHG_20,
round_675, audit +49.7bp/t2.45) only split the LEFT leg; UNDERWATER_FRAC_
CHG_20 stayed unsplit. This family splits the RIGHT-leg base statistics
of S64's three original unsplit right legs the same way (turnover/
overnight-gap two-way split, reusing the verbatim helpers from
overnight_conditioned_drawdown_volume.py), so left x right same-condition
vs different-condition contrasts can be tested. UNDERWATER_FRAC_CHG_20 was
already split in S64 itself (UWCHG_TURNOVER_SPLIT_20, UWCHG_ONGAP_SPLIT_20,
mechanism_atoms_v6_split) and GAP_DD_CONSUMPTION_RATIO_20's turnover split
already exists in S70 (GAPDD_TURNOVER_SPLIT_20, mechanism_atoms_v8_split_
tier2) -- both reused as-is, not rebuilt here. This family adds only the
3 atoms that don't exist yet: GAP_DD_CONSUMPTION_RATIO_20's overnight-gap
split, and CONTINUOUS_BETA_60's turnover and overnight-gap splits.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..family_provider import FamilyProvider
from ..family_registry import register_family, resolve_family
from .split_math import (
    rolling_median_split_diff,
    rolling_sign_split_diff,
)

ATOM_NAMES = (
    "GAPDD_ONGAP_SPLIT_20B",
    "CBETA_TURNOVER_SPLIT_20",
    "CBETA_ONGAP_SPLIT_20",
)

_DUMMY_CONFIG_1M = {"frequency": "1m"}
_DUMMY_CONFIG_1D = {"frequency": "1d"}
_SIGN_SPLIT_WINDOW = 40
_TURNOVER_MEDIAN_WINDOW = 20


def _resolved(source: str, panels, eligibility, data_root, config=None) -> dict:
    cfg = config if config is not None else _DUMMY_CONFIG_1M
    return resolve_family(source).builder(panels, eligibility, data_root, cfg)


def _build(panels, eligibility, data_root, config):
    del config
    close = panels["close"]
    open_p = panels["open"]
    amount = panels["amount"]
    dates = close.index
    symbols = list(close.columns)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    gap_dd_consumption = _resolved(
        "overnight_intraday_mismatch_v1", panels, eligibility, data_root, _DUMMY_CONFIG_1D
    )["GAP_DD_CONSUMPTION_RATIO_20"][symbols]
    continuous_beta = _resolved(
        "jump_continuous_beta", panels, eligibility, data_root,
        {"frequency": "1m", "benchmark_symbols": ["510300.SH", "510500.SH"]},
    )["CONTINUOUS_BETA_60"][symbols]

    turnover_level = amount[symbols]
    overnight_ret = (open_p[symbols] / close[symbols].shift(1) - 1.0)

    for sym in symbols:
        out["GAPDD_ONGAP_SPLIT_20B"][sym] = rolling_sign_split_diff(
            overnight_ret[sym], gap_dd_consumption[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)
        out["CBETA_TURNOVER_SPLIT_20"][sym] = rolling_median_split_diff(
            turnover_level[sym], continuous_beta[sym], _TURNOVER_MEDIAN_WINDOW
        ).reindex(dates)
        out["CBETA_ONGAP_SPLIT_20"][sym] = rolling_sign_split_diff(
            overnight_ret[sym], continuous_beta[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("mechanism_atoms_v9_split_right", "mechanism_atoms_v9_split_right", _build))
