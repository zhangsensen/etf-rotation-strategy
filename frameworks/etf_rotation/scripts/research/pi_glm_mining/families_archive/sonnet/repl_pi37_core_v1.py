"""S50 stage (round_652, main controller directive, 2026-09-21):
independent reproduction of pi lane's stage-37 mechanism atoms and
their pairings (MA27/MA14/DD48/DD49), per the standing reproduction
discipline (new family file, R_ prefix, no reading of pi's code, no
approximate substitution). Only the two atoms pi's directive specifies
that this line has NOT already built under a matching definition are
implemented fresh here:

  R_LUNCH_DIR_BET_20 = (13:00-13:10 1m volume share of the day's total
    volume) * sign(intraday return = close/open - 1), 20-day mean. A
    single functional composition per day (one number per day, not a
    two-atom product construct), same convention as this line's other
    "quantity x sign" mechanism atoms (S30's AM_PRERUN_CLOSE5_CONSIST
    etc.).
  R_VFP_ULCER_SHIFT_20 = 20-day change of the 20-day mean of a
    FIXED-OPEN-BASE ulcer index: for each 1m close price c_t within the
    day, downside_t = max(0, open - c_t) / open (only counts excursions
    BELOW the day's open; a positive excursion contributes 0); ulcer_t
    (per day) = sqrt(mean(downside_t^2)) over the day's bars. This is
    deliberately NOT the same statistic as this line's existing
    ULCER_INDEX_20 (S12, intraday_pain_recovery_1m), which uses a
    RUNNING PEAK (cummax of the price path) as the drawdown reference,
    not the fixed opening price -- the S50 directive's wording ("以开盘
    为基") specifies a different, fixed base, so this is a genuinely
    distinct construct worth an independent implementation rather than
    a reuse.

The directive's other three referenced atoms (PERM_ENTROPY_RET_20,
UNDERWATER_FRAC_CHG_20, LUNCH_PRE_RUN_20) are reused as-is from their
existing families (permutation_entropy_1m, intraday_drawdown_1m,
pi_lunch_prerun_1m respectively) -- their definitions already match the
directive's wording exactly, so rebuilding them a second/third time
would be pure duplication, not reproduction. RESILIENCY_20
(liquidity_commonality_1m) is likewise reused as-is as a pairing right
leg. The directive explicitly forbids reusing this line's S30
PM_POSTRUN_DAY_CONSIST_20 (mechanism_atoms_v3) as a substitute for
R_LUNCH_DIR_BET_20 -- they are related but not identical constructs
(PM_POSTRUN_DAY_CONSIST_20 splits by deviation-from-own-20d-mean and
correlates with daily return sign via a 20d rolling match-rate, not a
same-day volume-share-times-sign product); this module's atom_health
reports their correlation for transparency."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "R_LUNCH_DIR_BET_20",
    "R_VFP_ULCER_SHIFT_20",
)

_ROLL = 20


def _daily_features(day: pd.DataFrame) -> dict | None:
    day = day.sort_values("datetime")
    ts = pd.to_datetime(day["datetime"])
    minutes = ts.dt.hour * 60 + ts.dt.minute
    volume = day["volume"].to_numpy(float)
    close = day["close"].to_numpy(float)
    open0 = float(day["open"].to_numpy(float)[0])

    total_vol = float(volume[np.isfinite(volume) & (volume > 0)].sum())
    if total_vol <= 0 or not np.isfinite(open0) or open0 <= 0:
        return None

    lunch_mask = (minutes >= 13 * 60) & (minutes <= 13 * 60 + 10)
    lunch_vol = float(volume[lunch_mask.to_numpy()].sum())
    lunch_share = lunch_vol / total_vol

    close_ok = close[np.isfinite(close) & (close > 0)]
    if len(close_ok) < 30:
        return None
    day_ret = float(close_ok[-1] / open0 - 1.0)
    day_sign = float(np.sign(day_ret))

    downside = np.maximum(0.0, (open0 - close_ok)) / open0
    ulcer = float(np.sqrt(np.mean(downside**2)))

    return {"lunch_dir_bet": lunch_share * day_sign, "ulcer_open": ulcer}


def _daily_frame(data_root, sym, as_of) -> pd.DataFrame:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if frame.empty or "close" not in frame.columns:
        return pd.DataFrame()
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()

    recs = []
    for date, day in frame.groupby("date", sort=True):
        feat = _daily_features(day)
        if feat is None:
            continue
        feat["date"] = date
        recs.append(feat)
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    for sym in symbols:
        daily = _daily_frame(data_root, sym, as_of)
        if daily.empty:
            continue

        lunch_dir_bet_20 = daily["lunch_dir_bet"].rolling(_ROLL, min_periods=15).mean()
        out["R_LUNCH_DIR_BET_20"][sym] = lunch_dir_bet_20.reindex(dates)

        ulcer_20 = daily["ulcer_open"].rolling(_ROLL, min_periods=15).mean()
        ulcer_shift_20 = ulcer_20 - ulcer_20.shift(_ROLL)
        out["R_VFP_ULCER_SHIFT_20"][sym] = ulcer_shift_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("repl_pi37_core_v1", "repl_pi37_core_v1", _build))
