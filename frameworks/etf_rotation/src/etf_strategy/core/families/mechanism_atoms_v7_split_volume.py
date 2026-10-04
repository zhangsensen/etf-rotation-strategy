"""Stage-S67 family (round_681, main controller directive, 2026-09-21):
extend S64's productive split construct ("statistic X's mean on condition-
A days minus its mean on non-A days") from no-volume representatives to
volume-channel atoms. Reuses the exact same time-series-split helpers
(imported verbatim from overnight_conditioned_drawdown_volume.py, same as
mechanism_atoms_v6_split.py) applied to: VOL_SPIKE_FREQ_20, VT_AUTOCORR_20,
MFI_EXTREME_FRAC_20, BIGBAR_VOL_SHARE_20, R2_VOL_AUTOCORR_20.

Split conditions (per directive, turnover high/low excluded here since it
would be "volume splitting volume autocorrelation" -- too circular):
  - overnight-gap positive/negative: sign of (open/prev_close - 1).
  - intraday-drawdown large/small: INTRADAY_MAXDD_20 level (median split).
  - noise-variance-ratio rising/falling: sign of NOISE_VAR_CHG_20.
  - Amihud-impact high/low: AMIHUD_1M_20 level (median split).

Each base statistic gets at most 2 conditions, totaling exactly 8 atoms:
  VOLSPIKE_ONGAP_SPLIT_20, VOLSPIKE_MAXDD_SPLIT_20 (VOL_SPIKE_FREQ_20);
  VTAC_NOISECHG_SPLIT_20, VTAC_AMIHUD_SPLIT_20 (VT_AUTOCORR_20);
  MFIEXT_ONGAP_SPLIT_20, MFIEXT_MAXDD_SPLIT_20 (MFI_EXTREME_FRAC_20);
  BIGBARVOL_NOISECHG_SPLIT_20 (BIGBAR_VOL_SHARE_20);
  R2VOLAC_AMIHUD_SPLIT_20 (R2_VOL_AUTOCORR_20)."""
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
    "VOLSPIKE_ONGAP_SPLIT_20",
    "VOLSPIKE_MAXDD_SPLIT_20",
    "VTAC_NOISECHG_SPLIT_20",
    "VTAC_AMIHUD_SPLIT_20",
    "MFIEXT_ONGAP_SPLIT_20",
    "MFIEXT_MAXDD_SPLIT_20",
    "BIGBARVOL_NOISECHG_SPLIT_20",
    "R2VOLAC_AMIHUD_SPLIT_20",
)

_DUMMY_CONFIG_1M = {"frequency": "1m"}
_MEDIAN_SPLIT_WINDOW = 20
_SIGN_SPLIT_WINDOW = 40


def _resolved(source: str, panels, eligibility, data_root) -> dict:
    return resolve_family(source).builder(panels, eligibility, data_root, _DUMMY_CONFIG_1M)


def _build(panels, eligibility, data_root, config):
    del config
    close = panels["close"]
    open_p = panels["open"]
    dates = close.index
    symbols = list(close.columns)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    vol_spike = _resolved("intraday_volume_profile_1m", panels, eligibility, data_root)["VOL_SPIKE_FREQ_20"][symbols]
    vt_autocorr = _resolved("volume_time_1m", panels, eligibility, data_root)["VT_AUTOCORR_20"][symbols]
    mfi_extreme = _resolved("accumulation_distribution_1m", panels, eligibility, data_root)["MFI_EXTREME_FRAC_20"][symbols]
    bigbar_vol_share = _resolved("bar_size_order_flow", panels, eligibility, data_root)["BIGBAR_VOL_SHARE_20"][symbols]
    r2_vol_autocorr = _resolved("repl_volume_core_v2b", panels, eligibility, data_root)["R2_VOL_AUTOCORR_20"][symbols]
    intraday_maxdd = _resolved("intraday_drawdown_1m", panels, eligibility, data_root)["INTRADAY_MAXDD_20"][symbols]
    amihud = _resolved("microstructure_1m", panels, eligibility, data_root)["AMIHUD_1M_20"][symbols]
    noise_var_chg = _resolved("microstructure_noise_1m", panels, eligibility, data_root)["NOISE_VAR_CHG_20"][symbols]

    overnight_ret = (open_p[symbols] / close[symbols].shift(1) - 1.0)

    for sym in symbols:
        out["VOLSPIKE_ONGAP_SPLIT_20"][sym] = rolling_sign_split_diff(
            overnight_ret[sym], vol_spike[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)
        out["VOLSPIKE_MAXDD_SPLIT_20"][sym] = rolling_median_split_diff(
            intraday_maxdd[sym], vol_spike[sym], _MEDIAN_SPLIT_WINDOW
        ).reindex(dates)

        out["VTAC_NOISECHG_SPLIT_20"][sym] = rolling_sign_split_diff(
            noise_var_chg[sym], vt_autocorr[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)
        out["VTAC_AMIHUD_SPLIT_20"][sym] = rolling_median_split_diff(
            amihud[sym], vt_autocorr[sym], _MEDIAN_SPLIT_WINDOW
        ).reindex(dates)

        out["MFIEXT_ONGAP_SPLIT_20"][sym] = rolling_sign_split_diff(
            overnight_ret[sym], mfi_extreme[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)
        out["MFIEXT_MAXDD_SPLIT_20"][sym] = rolling_median_split_diff(
            intraday_maxdd[sym], mfi_extreme[sym], _MEDIAN_SPLIT_WINDOW
        ).reindex(dates)

        out["BIGBARVOL_NOISECHG_SPLIT_20"][sym] = rolling_sign_split_diff(
            noise_var_chg[sym], bigbar_vol_share[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)

        out["R2VOLAC_AMIHUD_SPLIT_20"][sym] = rolling_median_split_diff(
            amihud[sym], r2_vol_autocorr[sym], _MEDIAN_SPLIT_WINDOW
        ).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("mechanism_atoms_v7_split_volume", "mechanism_atoms_v7_split_volume", _build))
