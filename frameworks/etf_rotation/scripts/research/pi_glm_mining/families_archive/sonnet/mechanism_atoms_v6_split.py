"""Stage-S64 family (round_673, main controller directive): apply S60's
only productive construct this stage ("statistic X's mean on condition-A
days minus its mean on non-A days") to this line's no-volume representative
atoms -- S60 built the pattern for volume-spike/turnover/liquidity-shock
conditions on volume atoms (34 candidates, 5 admissions across two
rounds); this family reuses the exact same time-series-split helpers
(imported verbatim from overnight_conditioned_drawdown_volume.py, the S36
family that first established the pattern) but applies them to the
no-volume representatives: QA8's drawdown-geometry atom
(UNDERWATER_FRAC_CHG_20), PA1/MA27's PERM_ENTROPY_RET_20, CJ16/CK04's
lunch-volume atom (LUNCH_POST_RUN_20), ULCER_INDEX_20, and
YZ_OVERNIGHT_SHARE_20.

Split conditions (each already-established atom or a raw daily
statistic, no new arbitrary thresholds):
  - turnover high/low: daily amount vs its own 20-day trailing median
    (median split, no fixed multiplier).
  - overnight-gap positive/negative: sign of (open/prev_close - 1)
    (sign split, natural zero threshold).
  - Amihud-impact high/low: AMIHUD_1M_20 level (median split).
  - noise-variance-ratio rising/falling: sign of NOISE_VAR_CHG_20
    (sign split, natural zero threshold, already a validated atom).

Each base statistic gets at most 2 conditions (per the directive's
"避免穷举" instruction), totaling exactly 8 atoms:
  UWCHG_TURNOVER_SPLIT_20, UWCHG_ONGAP_SPLIT_20 (UNDERWATER_FRAC_CHG_20);
  PERMENT_TURNOVER_SPLIT_20, PERMENT_AMIHUD_SPLIT_20 (PERM_ENTROPY_RET_20);
  LUNCHPR_ONGAP_SPLIT_20 (LUNCH_POST_RUN_20);
  ULCER_NOISERATIO_SPLIT_20, ULCER_TURNOVER_SPLIT_20 (ULCER_INDEX_20);
  YZSHARE_AMIHUD_SPLIT_20 (YZ_OVERNIGHT_SHARE_20).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..family_provider import FamilyProvider
from ..family_registry import register_family, resolve_family
from .overnight_conditioned_drawdown_volume import (
    _rolling_median_split_diff,
    _rolling_sign_split_diff,
)

ATOM_NAMES = (
    "UWCHG_TURNOVER_SPLIT_20",
    "UWCHG_ONGAP_SPLIT_20",
    "PERMENT_TURNOVER_SPLIT_20",
    "PERMENT_AMIHUD_SPLIT_20",
    "LUNCHPR_ONGAP_SPLIT_20",
    "ULCER_NOISERATIO_SPLIT_20",
    "ULCER_TURNOVER_SPLIT_20",
    "YZSHARE_AMIHUD_SPLIT_20",
)

_DUMMY_CONFIG_1M = {"frequency": "1m"}
_MEDIAN_SPLIT_WINDOW = 20
_SIGN_SPLIT_WINDOW = 40
_TURNOVER_MEDIAN_WINDOW = 20


def _resolved(source: str, panels, eligibility, data_root) -> dict:
    return resolve_family(source).builder(panels, eligibility, data_root, _DUMMY_CONFIG_1M)


def _build(panels, eligibility, data_root, config):
    del config
    close = panels["close"]
    open_p = panels["open"]
    amount = panels["amount"]
    dates = close.index
    symbols = list(close.columns)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    uw_chg = _resolved("intraday_drawdown_1m", panels, eligibility, data_root)["UNDERWATER_FRAC_CHG_20"][symbols]
    perm_ent = _resolved("permutation_entropy_1m", panels, eligibility, data_root)["PERM_ENTROPY_RET_20"][symbols]
    lunch_post_run = _resolved("lunch_break_1m", panels, eligibility, data_root)["LUNCH_POST_RUN_20"][symbols]
    ulcer = _resolved("intraday_pain_recovery_1m", panels, eligibility, data_root)["ULCER_INDEX_20"][symbols]
    yz_share = _resolved("range_based_vol_1m", panels, eligibility, data_root)["YZ_OVERNIGHT_SHARE_20"][symbols]
    amihud = _resolved("microstructure_1m", panels, eligibility, data_root)["AMIHUD_1M_20"][symbols]
    noise_var_chg = _resolved("microstructure_noise_1m", panels, eligibility, data_root)["NOISE_VAR_CHG_20"][symbols]

    turnover_level = amount[symbols]
    overnight_ret = (open_p[symbols] / close[symbols].shift(1) - 1.0)

    for sym in symbols:
        out["UWCHG_TURNOVER_SPLIT_20"][sym] = _rolling_median_split_diff(
            turnover_level[sym], uw_chg[sym], _TURNOVER_MEDIAN_WINDOW
        ).reindex(dates)
        out["UWCHG_ONGAP_SPLIT_20"][sym] = _rolling_sign_split_diff(
            overnight_ret[sym], uw_chg[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)

        out["PERMENT_TURNOVER_SPLIT_20"][sym] = _rolling_median_split_diff(
            turnover_level[sym], perm_ent[sym], _TURNOVER_MEDIAN_WINDOW
        ).reindex(dates)
        out["PERMENT_AMIHUD_SPLIT_20"][sym] = _rolling_median_split_diff(
            amihud[sym], perm_ent[sym], _MEDIAN_SPLIT_WINDOW
        ).reindex(dates)

        out["LUNCHPR_ONGAP_SPLIT_20"][sym] = _rolling_sign_split_diff(
            overnight_ret[sym], lunch_post_run[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)

        out["ULCER_NOISERATIO_SPLIT_20"][sym] = _rolling_sign_split_diff(
            noise_var_chg[sym], ulcer[sym], _SIGN_SPLIT_WINDOW
        ).reindex(dates)
        out["ULCER_TURNOVER_SPLIT_20"][sym] = _rolling_median_split_diff(
            turnover_level[sym], ulcer[sym], _TURNOVER_MEDIAN_WINDOW
        ).reindex(dates)

        out["YZSHARE_AMIHUD_SPLIT_20"][sym] = _rolling_median_split_diff(
            amihud[sym], yz_share[sym], _MEDIAN_SPLIT_WINDOW
        ).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("mechanism_atoms_v6_split", "mechanism_atoms_v6_split", _build))
