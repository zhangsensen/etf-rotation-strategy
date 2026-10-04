"""Stage-S60 family (round_665, main controller directive): mechanism
atoms distilled from the S44 second-tier rejected list's volume-inclusive
combos -- MB2 (NOISE_VAR_CHG_20 x VOL_SPIKE_FREQ_20, H20 audit t 5.52),
PB5 (PERM_ENTROPY_RET_20 x LOG_AMOUNT_VOL_20, t 5.31), DA1 (SAMPEN_RET_20
x LOG_AMOUNT_VOL_20, t 5.09), NI5 (MFI_EXTREME_FRAC_20 x
IDIO_LIQ_SHOCK_Z_20, t 4.58) -- see outputs/round_644/rejected_h20_profile.csv.
All four were rank_spread cross-sectional constructs that never passed
gate 7 (cross-sectional top-k excess); this stage instead expresses each
pairing as a single time-series conditional-split statistic (the same
"contract forbids multi-atom products, permits one conditional statistic"
pattern established by S36's overnight_conditioned_drawdown_volume.py),
which is a per-symbol day-conditional-difference rather than a
cross-sectional rank interaction.

PB5 and DA1 share the LOG_AMOUNT_VOL_20 right leg (turnover-volatility
conditioning) and differ only in which complexity measure is the target
(entropy vs sample entropy); PB5 has the higher source H20 audit t
(5.31 vs 5.09), so only its target (PERM_ENTROPY_RET_20) is carried
forward here -- one mechanism atom covers both source candidates.

Implementation reuses helpers directly rather than re-deriving:
  - _rolling_median_split_diff / _rolling_sign_split_diff imported
    verbatim from overnight_conditioned_drawdown_volume.py (S36), same
    window constants (20 for median split, 40 for sign split) -- no new
    arbitrary thresholds introduced.
  - Source atoms (NOISE_VAR_CHG_20, PERM_ENTROPY_RET_20, LOG_AMOUNT_VOL_20,
    MFI_EXTREME_FRAC_20, IDIO_LIQ_SHOCK_Z_20) are resolved via
    resolve_family() against their native registered families
    (microstructure_noise_1m, permutation_entropy_1m,
    liquidity_variability, accumulation_distribution_1m,
    liquidity_commonality_1m) -- already-validated 20d-rolling atoms, not
    re-computed. liquidity_commonality_1m needs the cross-sectional
    Amihud pool (>=8 symbols) to build IDIO_LIQ_SHOCK_Z_20, so this
    family must always be built against the full candidate panel, never
    a symbol subset.
  - The raw per-day volume-spike fraction (needed for the MB2 split,
    since VOL_SPIKE_FREQ_20 itself is already a 20d rolling mean and
    would blur the day-level split) is recomputed with the identical
    formula etf_mined_families.py uses internally (spike minute = volume
    > 5x day median, min 60 valid minutes/day) -- same constant, just
    exposed at the daily grain instead of the 20d-smoothed grain.

Atoms:
  VOLSPIKE_NOISECHG_SPLIT_20: rolling 20-day median split of the raw
    daily volume-spike fraction; mean(NOISE_VAR_CHG_20 | spike-day >=
    trailing median) - mean(NOISE_VAR_CHG_20 | < median). Answers "does
    noise-variance change differently on volume-spike days vs quiet
    days" (MB2's mechanism, expressed as a split rather than a
    cross-sectional rank spread).
  TURNVOL_ENTROPY_SPLIT_20: rolling 20-day median split of
    LOG_AMOUNT_VOL_20 (turnover-volatility level); mean(PERM_ENTROPY_RET_20
    | high turnover-vol) - mean(PERM_ENTROPY_RET_20 | low). Covers both
    PB5 and DA1's shared right leg.
  LIQSHOCK_MFI_SPLIT_20: rolling 40-day sign split of IDIO_LIQ_SHOCK_Z_20
    (already z-scored, centered at 0 by construction, so sign is a
    natural shock/no-shock cut with no new threshold); mean(MFI_EXTREME_FRAC_20
    | shock-day, z>0) - mean(... | non-shock, z<=0) (NI5's mechanism).
  TURNVOL_ENTROPY_SPLIT_CHG_20: 20-day change of TURNVOL_ENTROPY_SPLIT_20
    -- added after round_665's single-atom batch: TURNVOL_ENTROPY_SPLIT_20
    was the only one of the three base atoms to gate-7 pass standalone
    (disc t 2.45, positive audit IC/excess; VOLSPIKE_NOISECHG_SPLIT_20
    and LIQSHOCK_MFI_SPLIT_20 both flipped sign discovery-to-audit and
    failed), so it is the "strongest" the S60 instruction asks to
    difference.
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
from ..etf_intraday_factor_space import _read_complete_days

ATOM_NAMES = (
    "VOLSPIKE_NOISECHG_SPLIT_20",
    "TURNVOL_ENTROPY_SPLIT_20",
    "LIQSHOCK_MFI_SPLIT_20",
    "TURNVOL_ENTROPY_SPLIT_CHG_20",
)

_DUMMY_CONFIG = {"frequency": "1m"}
_MEDIAN_SPLIT_WINDOW = 20
_SIGN_SPLIT_WINDOW = 40
_SPIKE_MEDIAN_MULT = 5.0
_SPIKE_MIN_MINUTES = 60


def _resolved(source: str, panels, eligibility, data_root) -> dict:
    return resolve_family(source).builder(panels, eligibility, data_root, _DUMMY_CONFIG)


def _daily_spike_frac(data_root, symbols, frequency, as_of, dates) -> pd.DataFrame:
    """Raw per-day volume-spike fraction (pre-rolling), identical formula
    to etf_mined_families.py's inline _volume_profile_atoms 'spike'
    column, exposed here at daily grain instead of a 20d rolling mean."""
    out = pd.DataFrame(np.nan, index=dates, columns=symbols)
    for sym in symbols:
        try:
            frame, _ = _read_complete_days(data_root, sym, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        frame = frame.copy()
        frame["date"] = frame["datetime"].dt.normalize()
        records = []
        for date, day in frame.groupby("date", sort=True):
            vol = day["volume"].to_numpy(float)
            ok = np.isfinite(vol) & (vol > 0)
            if ok.sum() < _SPIKE_MIN_MINUTES:
                continue
            v = vol[ok]
            med = float(np.median(v))
            spike = float((v > med * _SPIKE_MEDIAN_MULT).mean())
            records.append({"date": date, "spike": spike})
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date")
        out[sym] = daily["spike"].reindex(dates)
    return out


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    frequency = str(config.get("frequency", "1m")) if config else "1m"
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    noise_space = _resolved("microstructure_noise_1m", panels, eligibility, data_root)
    noise_chg = noise_space["NOISE_VAR_CHG_20"][symbols]

    entropy_space = _resolved("permutation_entropy_1m", panels, eligibility, data_root)
    perm_entropy = entropy_space["PERM_ENTROPY_RET_20"][symbols]

    liq_var_space = _resolved("liquidity_variability", panels, eligibility, data_root)
    log_amount_vol = liq_var_space["LOG_AMOUNT_VOL_20"][symbols]

    mfi_space = _resolved("accumulation_distribution_1m", panels, eligibility, data_root)
    mfi_extreme = mfi_space["MFI_EXTREME_FRAC_20"][symbols]

    liq_common_space = _resolved("liquidity_commonality_1m", panels, eligibility, data_root)
    idio_shock = liq_common_space["IDIO_LIQ_SHOCK_Z_20"][symbols]

    spike_daily = _daily_spike_frac(data_root, symbols, frequency, as_of, dates)

    for sym in symbols:
        vol_diff = _rolling_median_split_diff(spike_daily[sym], noise_chg[sym], _MEDIAN_SPLIT_WINDOW)
        out["VOLSPIKE_NOISECHG_SPLIT_20"][sym] = vol_diff.reindex(dates)

        turn_diff = _rolling_median_split_diff(log_amount_vol[sym], perm_entropy[sym], _MEDIAN_SPLIT_WINDOW)
        out["TURNVOL_ENTROPY_SPLIT_20"][sym] = turn_diff.reindex(dates)

        liq_diff = _rolling_sign_split_diff(idio_shock[sym], mfi_extreme[sym], _SIGN_SPLIT_WINDOW)
        out["LIQSHOCK_MFI_SPLIT_20"][sym] = liq_diff.reindex(dates)

    out["TURNVOL_ENTROPY_SPLIT_CHG_20"] = (
        out["TURNVOL_ENTROPY_SPLIT_20"] - out["TURNVOL_ENTROPY_SPLIT_20"].shift(20)
    ).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("mechanism_atoms_v5", "mechanism_atoms_v5", _build))
