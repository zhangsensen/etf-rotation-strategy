"""S32 stage (round_631, main controller directive): deepen S29's
REL_UNDERWATER_CATEGORY_20 mechanism -- category-relative (sleeve peer
group) versions of several already-validated absolute-level atoms.
S29P10 (rank(REL_UNDERWATER_CATEGORY_20) x rank(R_LOG_AMOUNT_VOL_20))
was S29's strongest admission (+66.8bp / t2.45), suggesting the
"relative to sleeve peers" reference frame carries information that the
absolute level or full-basket-relative (S15) versions do not.

Efficiency directive (main controller, 2026-09-21 00:40): prefer atom
reuse over re-derivation. 6 of this family's 7 atoms reuse already-built
atoms via resolve_family() calls inside _build() -- INTRADAY_MAXDD_20
(S7 intraday_drawdown_1m), RECOVERY_TIME_FRAC_20 (S12
intraday_pain_recovery_1m), YZ_OVERNIGHT_SHARE_20 (S9 range_based_vol_1m),
MFI_EXTREME_FRAC_20 (S10 accumulation_distribution_1m), LUNCH_POST_RUN_20
(S22 lunch_break_1m), REL_UNDERWATER_CATEGORY_20 (S29 mechanism_atoms_v2,
already category-relative, only needs a 20d-change derivation on top).
Only ON_PREM_20 (the raw 20d-mean overnight return level) has no prior
registered atom on this line -- S21's overnight_structure_1d family
built ON_PREM_SKEW_20, ON_PREM_CHG_20, ON_ABS_MEAN_20 etc. but never the
plain level -- so it is computed fresh here directly from daily
open/close panels (a one-line vectorized calculation, no 1m needed).

Sleeve grouping: config/etf_rotation_universe_v1.json's candidate-role
"sleeve" field (technology n=8, auxiliary_rotation n=6), same mapping
S29's REL_UNDERWATER_CATEGORY_20 used.

Atoms:
  REL_UNDERWATER_CATEGORY_CHG_20: 20d change of REL_UNDERWATER_CATEGORY_20.
  REL_MAXDD_CATEGORY_20: INTRADAY_MAXDD_20 minus sleeve-peer mean, 20d mean.
  REL_RECOVERY_TIME_CATEGORY_20: RECOVERY_TIME_FRAC_20 minus sleeve-peer
    mean, 20d mean.
  REL_ON_PREM_CATEGORY_20: ON_PREM_20 (built here) minus sleeve-peer
    mean, 20d mean.
  REL_ON_VAR_SHARE_CATEGORY_20: YZ_OVERNIGHT_SHARE_20 minus sleeve-peer
    mean, 20d mean.
  REL_MFI_EXTREME_CATEGORY_20: MFI_EXTREME_FRAC_20 minus sleeve-peer
    mean, 20d mean.
  REL_LUNCH_POSTRUN_CATEGORY_20: LUNCH_POST_RUN_20 minus sleeve-peer
    mean, 20d mean.

S54 stage (round_656, main controller directive): deepen the same
category-relative reference frame with two CHG (20d-change) variants
that were not built alongside the original S32 batch --
REL_UNDERWATER_CATEGORY_CHG_20 (S32's own atom) was already single-atom
gate-7 re-adjudicated once in round_631 as S32A1 (rejected:
rank_correlation_redundancy vs prior:round_545:QA8, corr 0.83), so it is
not re-registered here; only the two genuinely new atoms below are
added:
  REL_ULCER_CATEGORY_CHG_20: 20d change of (ULCER_INDEX_20 minus
    sleeve-peer mean) -- category-relative drawdown-magnitude
    trajectory, parallel to REL_UNDERWATER_CATEGORY_CHG_20 but using
    the RMS-drawdown (Ulcer Index) measure instead of underwater
    fraction.
  REL_RECOVERY_TIME_CATEGORY_CHG_20: 20d change of the already-built
    REL_RECOVERY_TIME_CATEGORY_20 level (that atom existed since S32 but
    only as a level, never differenced).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..family_provider import FamilyProvider
from ..family_registry import register_family, resolve_family

ATOM_NAMES = (
    "REL_UNDERWATER_CATEGORY_CHG_20",
    "REL_MAXDD_CATEGORY_20",
    "REL_RECOVERY_TIME_CATEGORY_20",
    "REL_ON_PREM_CATEGORY_20",
    "REL_ON_VAR_SHARE_CATEGORY_20",
    "REL_MFI_EXTREME_CATEGORY_20",
    "REL_LUNCH_POSTRUN_CATEGORY_20",
    "REL_ULCER_CATEGORY_CHG_20",
    "REL_RECOVERY_TIME_CATEGORY_CHG_20",
)

_DUMMY_CONFIG = {"frequency": "1m"}
_UNIVERSE_CONFIG = Path(str(Path(__file__).resolve().parents[7] / "config/etf_rotation_universe_v1.json"))


def _load_sleeve_map() -> dict:
    try:
        data = json.loads(_UNIVERSE_CONFIG.read_text())
    except Exception:  # noqa: BLE001
        return {}
    return {
        e["ts_code"]: e.get("sleeve", "unknown")
        for e in data.get("etfs", [])
        if e.get("role") == "candidate"
    }


def _resolved(source: str, panels, eligibility, data_root) -> dict:
    return resolve_family(source).builder(panels, eligibility, data_root, _DUMMY_CONFIG)


def _category_relative(level: pd.DataFrame, symbols: list, sleeve_map: dict) -> pd.DataFrame:
    out = pd.DataFrame(np.nan, index=level.index, columns=symbols)
    for sym in symbols:
        sleeve = sleeve_map.get(sym)
        if sleeve is None:
            continue
        peers = [s for s in symbols if s != sym and sleeve_map.get(s) == sleeve]
        if not peers:
            continue
        peer_mean = level[peers].mean(axis=1, skipna=True)
        out[sym] = level[sym] - peer_mean
    return out


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    sleeve_map = _load_sleeve_map()

    rel_uw_space = _resolved("mechanism_atoms_v2", panels, eligibility, data_root)
    rel_uw = rel_uw_space["REL_UNDERWATER_CATEGORY_20"]
    out["REL_UNDERWATER_CATEGORY_CHG_20"] = (rel_uw - rel_uw.shift(20)).reindex(dates)

    # Reference atoms below (INTRADAY_MAXDD_20, RECOVERY_TIME_FRAC_20,
    # YZ_OVERNIGHT_SHARE_20, MFI_EXTREME_FRAC_20, LUNCH_POST_RUN_20) are
    # already 20d-rolling-mean series; the category-relative diff of an
    # already-smoothed series is itself a legitimate daily-changing
    # series, so no second rolling-mean pass is applied on top (avoids
    # double-smoothing that would understate day-to-day variation).
    maxdd_space = _resolved("intraday_drawdown_1m", panels, eligibility, data_root)
    maxdd = maxdd_space["INTRADAY_MAXDD_20"][symbols]
    out["REL_MAXDD_CATEGORY_20"] = _category_relative(maxdd, symbols, sleeve_map).reindex(dates)

    recovery_space = _resolved("intraday_pain_recovery_1m", panels, eligibility, data_root)
    recovery = recovery_space["RECOVERY_TIME_FRAC_20"][symbols]
    out["REL_RECOVERY_TIME_CATEGORY_20"] = _category_relative(recovery, symbols, sleeve_map).reindex(dates)

    open_p = panels["open"]
    close_p = panels["close"]
    prev_close = close_p.shift(1)
    overnight_ret = open_p / prev_close.where(prev_close > 0) - 1.0
    on_prem_20 = overnight_ret.rolling(20, min_periods=12).mean()
    out["REL_ON_PREM_CATEGORY_20"] = _category_relative(on_prem_20[symbols], symbols, sleeve_map).reindex(dates)

    yz_space = _resolved("range_based_vol_1m", panels, eligibility, data_root)
    yz = yz_space["YZ_OVERNIGHT_SHARE_20"][symbols]
    out["REL_ON_VAR_SHARE_CATEGORY_20"] = _category_relative(yz, symbols, sleeve_map).reindex(dates)

    mfi_space = _resolved("accumulation_distribution_1m", panels, eligibility, data_root)
    mfi = mfi_space["MFI_EXTREME_FRAC_20"][symbols]
    out["REL_MFI_EXTREME_CATEGORY_20"] = _category_relative(mfi, symbols, sleeve_map).reindex(dates)

    lunch_space = _resolved("lunch_break_1m", panels, eligibility, data_root)
    lunch = lunch_space["LUNCH_POST_RUN_20"][symbols]
    out["REL_LUNCH_POSTRUN_CATEGORY_20"] = _category_relative(lunch, symbols, sleeve_map).reindex(dates)

    ulcer_space = _resolved("intraday_pain_recovery_1m", panels, eligibility, data_root)
    ulcer = ulcer_space["ULCER_INDEX_20"][symbols]
    rel_ulcer_category = _category_relative(ulcer, symbols, sleeve_map)
    out["REL_ULCER_CATEGORY_CHG_20"] = (rel_ulcer_category - rel_ulcer_category.shift(20)).reindex(dates)

    out["REL_RECOVERY_TIME_CATEGORY_CHG_20"] = (
        out["REL_RECOVERY_TIME_CATEGORY_20"] - out["REL_RECOVERY_TIME_CATEGORY_20"].shift(20)
    ).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("category_relative_geometry", "category_relative_geometry", _build))
