"""Stage-S62 family (round_668, main controller directive): threshold-free
volume-tail-shape statistics, replacing the "spike frequency" atom family
(VOL_SPIKE_FREQ_20 / R2_VOL_SPIKE_FREQ_20) whose arbitrary threshold
(mean+3sigma vs median*5x) drives the largest definition-sensitivity gap
found in this line (S39/S51: rank corr as low as 0.58 across rewrites of
the same "volume spike" concept). This family instead expresses the same
underlying phenomenon -- a fat right tail in the intraday volume
distribution -- using scale-free, threshold-free statistics from the
extreme-value / heavy-tail literature.

Literature anchors:
- Clark (1973) -- the mixture-of-distributions hypothesis: volume is a
  latent-information-arrival proxy with a heavy right tail, motivating
  tail-shape (not a fixed cutoff) as the natural summary statistic.
- Gabaix, Gopikrishnan, Plerou, Stanley (2003); Gopikrishnan, Plerou,
  Gabaix, Stanley (2000) -- power-law tails in trading volume and returns;
  the Hill estimator is the standard threshold-free tail-index estimator
  for this literature.

Atoms (all 20-day rolling means of a per-day intraday statistic, no
volume-magnitude threshold anywhere):
  VOL_Q95_MED_20: 1m volume 95th percentile / median (intraday), 20d mean
    -- a quantile-ratio tail-fatness proxy, no fixed multiplier.
  VOL_HILL_TAIL_20: Hill tail-index estimator on the top 10% of the day's
    1m volume sample (order statistics), 20d mean -- lower value = fatter
    tail (more spike-like), by Hill estimator convention.
  LOG_VOL_CV_20: intraday coefficient of variation of log(1m volume)
    (std/mean of log volume within the day), 20d mean.
  VOL_MAX_SHARE_20: single largest 1m volume bar's share of the day's
    total volume, 20d mean -- the only atom with an explicit "which bar"
    reference, but no magnitude threshold.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "VOL_Q95_MED_20",
    "VOL_HILL_TAIL_20",
    "LOG_VOL_CV_20",
    "VOL_MAX_SHARE_20",
)

_MIN_VALID_MINUTES = 60
_HILL_TOP_FRAC = 0.10
_ROLL_WINDOW = 20
_ROLL_MIN_PERIODS = 10


def _hill_tail_index(sorted_desc: np.ndarray) -> float:
    """Hill estimator on the top _HILL_TOP_FRAC of order statistics.
    sorted_desc must already be sorted descending, all > 0."""
    n = len(sorted_desc)
    k = max(int(np.ceil(_HILL_TOP_FRAC * n)), 5)
    if k >= n:
        return np.nan
    top = sorted_desc[:k]
    threshold = sorted_desc[k]
    if threshold <= 0:
        return np.nan
    log_ratios = np.log(top / threshold)
    mean_log_ratio = float(log_ratios.mean())
    if mean_log_ratio <= 0:
        return np.nan
    return 1.0 / mean_log_ratio


def _daily_tail_stats(data_root, symbols, frequency, as_of, dates) -> dict[str, pd.DataFrame]:
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}
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
            if ok.sum() < _MIN_VALID_MINUTES:
                continue
            v = vol[ok]
            med = float(np.median(v))
            q95 = float(np.percentile(v, 95))
            q95_med = q95 / med if med > 0 else np.nan
            v_desc = np.sort(v)[::-1]
            hill = _hill_tail_index(v_desc)
            log_v = np.log(v)
            log_cv = float(np.std(log_v) / np.mean(log_v)) if np.mean(log_v) != 0 else np.nan
            max_share = float(v.max() / v.sum())
            records.append(
                {
                    "date": date,
                    "q95_med": q95_med,
                    "hill": hill,
                    "log_cv": log_cv,
                    "max_share": max_share,
                }
            )
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date")
        for feat, atom in (
            ("q95_med", "VOL_Q95_MED_20"),
            ("hill", "VOL_HILL_TAIL_20"),
            ("log_cv", "LOG_VOL_CV_20"),
            ("max_share", "VOL_MAX_SHARE_20"),
        ):
            out[atom][sym] = (
                daily[feat].rolling(_ROLL_WINDOW, min_periods=_ROLL_MIN_PERIODS).mean().reindex(dates)
            )
    return out


def _build(panels, eligibility, data_root, config):
    frequency = str(config.get("frequency", "1m")) if config else "1m"
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = _daily_tail_stats(data_root, symbols, frequency, as_of, dates)
    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("volume_tail_shape_1m", "volume_tail_shape_1m", _build))
