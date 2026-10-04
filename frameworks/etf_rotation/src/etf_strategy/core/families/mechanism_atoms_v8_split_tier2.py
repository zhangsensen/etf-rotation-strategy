"""Stage-S70 family (round_685, main controller directive, 2026-09-21):
extend the split construct (S64/S67's "statistic X's mean on condition-A
days minus its mean on non-A days") to a second tier of no-volume
representative atoms that have not yet been split: LUNCH_PRE_RUN_20
(CJ16's lunch leg), R_VFP_ULCER_SHIFT_20 (DD48's leg), RESILIENCY_20,
GAP_DD_CONSUMPTION_RATIO_20, CLOSE5_DAY_CONSIST_20. Reuses the exact same
time-series-split helpers (imported verbatim from
overnight_conditioned_drawdown_volume.py, same as v6/v7).

Split conditions (per directive):
  - turnover high/low: daily amount vs its own 20-day trailing median.
  - overnight-gap positive/negative: sign of (open/prev_close - 1).
  - noise-variance-ratio rising/falling: sign of NOISE_VAR_CHG_20.
  - Amihud-impact high/low: AMIHUD_1M_20 level (median split).

Each base statistic gets at most 2 conditions, totaling exactly 8 atoms:
  LUNCHPR_TURNOVER_SPLIT_20, LUNCHPR_ONGAP_SPLIT_20B (LUNCH_PRE_RUN_20;
    the directive's own S64 family already built LUNCHPR_ONGAP_SPLIT_20
    off LUNCH_POST_RUN_20 -- this is a different base atom, PRE-run not
    POST-run, so the _B suffix marks it as a distinct construct, not a
    duplicate registration);
  VFPULCER_TURNOVER_SPLIT_20, VFPULCER_NOISECHG_SPLIT_20
    (R_VFP_ULCER_SHIFT_20);
  RESIL_ONGAP_SPLIT_20, RESIL_AMIHUD_SPLIT_20 (RESILIENCY_20);
  GAPDD_TURNOVER_SPLIT_20 (GAP_DD_CONSUMPTION_RATIO_20);
  CLOSE5_NOISECHG_SPLIT_20 (CLOSE5_DAY_CONSIST_20)."""
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
    "LUNCHPR_TURNOVER_SPLIT_20",
    "LUNCHPR_ONGAP_SPLIT_20B",
    "VFPULCER_TURNOVER_SPLIT_20",
    "VFPULCER_NOISECHG_SPLIT_20",
    "RESIL_ONGAP_SPLIT_20",
    "RESIL_AMIHUD_SPLIT_20",
    "GAPDD_TURNOVER_SPLIT_20",
    "CLOSE5_NOISECHG_SPLIT_20",
)

_DUMMY_CONFIG_1M = {"frequency": "1m"}
_DUMMY_CONFIG_1D = {"frequency": "1d"}
_MEDIAN_SPLIT_WINDOW = 20
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

    lunch_pre_run = _resolved("pi_lunch_prerun_1m", panels, eligibility, data_root)["LUNCH_PRE_RUN_20"][symbols]
    vfp_ulcer_shift = _resolved("repl_pi37_core_v1", panels, eligibility, data_root)["R_VFP_ULCER_SHIFT_20"][symbols]
    resiliency = _resolved("liquidity_commonality_1m", panels, eligibility, data_root)["RESILIENCY_20"][symbols]
    gap_dd_consumption = _resolved(
        "overnight_intraday_mismatch_v1", panels, eligibility, data_root, _DUMMY_CONFIG_1D
    )["GAP_DD_CONSUMPTION_RATIO_20"][symbols]
    close5_consist = _resolved("bar_size_order_flow", panels, eligibility, data_root)["CLOSE5_DAY_CONSIST_20"][symbols]
    amihud = _resolved("microstructure_1m", panels, eligibility, data_root)["AMIHUD_1M_20"][symbols]
    noise_var_chg = _resolved("microstructure_noise_1m", panels, eligibility, data_root)["NOISE_VAR_CHG_20"][symbols]

    turnover_level = amount[symbols]
    overnight_ret = (open_p[symbols] / close[symbols].shift(1) - 1.0)

    for sym in symbols:
        out["LUNCHPR_TURNOVER_SPLIT_20"][sym] = rolling_median_split_diff(
            turnover_level[sym], lunch_pre_run[sym], _TURNOVER_MEDIAN_WINDOW
        ).reindex(dates)
        out["LUNCHPR_ONGAP_SPLIT_20B"][sym] = rolling_sign_split_diff(
            overnight_ret[sym], lunch_pre_run[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)

        out["VFPULCER_TURNOVER_SPLIT_20"][sym] = rolling_median_split_diff(
            turnover_level[sym], vfp_ulcer_shift[sym], _TURNOVER_MEDIAN_WINDOW
        ).reindex(dates)
        out["VFPULCER_NOISECHG_SPLIT_20"][sym] = rolling_sign_split_diff(
            noise_var_chg[sym], vfp_ulcer_shift[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)

        out["RESIL_ONGAP_SPLIT_20"][sym] = rolling_sign_split_diff(
            overnight_ret[sym], resiliency[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)
        out["RESIL_AMIHUD_SPLIT_20"][sym] = rolling_median_split_diff(
            amihud[sym], resiliency[sym], _MEDIAN_SPLIT_WINDOW
        ).reindex(dates)

        out["GAPDD_TURNOVER_SPLIT_20"][sym] = rolling_median_split_diff(
            turnover_level[sym], gap_dd_consumption[sym], _TURNOVER_MEDIAN_WINDOW
        ).reindex(dates)

        out["CLOSE5_NOISECHG_SPLIT_20"][sym] = rolling_sign_split_diff(
            noise_var_chg[sym], close5_consist[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("mechanism_atoms_v8_split_tier2", "mechanism_atoms_v8_split_tier2", _build))
