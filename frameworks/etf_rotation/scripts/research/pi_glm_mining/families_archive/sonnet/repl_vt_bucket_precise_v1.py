"""S46 stage (main controller directive, 2026-09-21, round_646):
precise-definition reproduction of pi's VT_BUCKET_COUNT_SHIFT_20 leg of
CR08, distinct from this line's own S24 volume_time_1m implementation
of the SAME-NAMED atom.

S24 (round_603, family volume_time_1m) computed VT_BUCKET_COUNT_SHIFT_20
as a LEVEL-DIFFERENCE of a smoothed series: 20d-rolling-mean(bucket
count) today minus the same rolling mean 20 trading days ago. Tested
against OPEN30_VOL_SHARE_20 as XC1 in round_603: discovery t=1.79,
audit excess +44.3bp -- same sign as pi's own CR08 number (+36.5bp/
t2.02) but not a strict definition match (S24 built its own reasonable
formula, not pi's exact one).

The controller's S46 directive gives pi's own formula in different,
more precise terms: for day t, a RATIO of today's bucket count to the
trailing-20-day mean bucket count, minus 1 (a same-day relative
deviation, not a smoothed-level difference); then a 20-day mean of that
daily ratio series. This is a genuinely different statistic (relative
daily surprise, smoothed after transformation) from S24's (smoothed
level, differenced before transformation), so it is rebuilt here under
a new name (R2_ prefix) rather than reused, per the reproduction
convention established in S45/S26R2 (independent reproduction is not
"造轮子" -- reproduction rounds test literal definition fidelity).

Formula (literature: Ane & Geman 2000; Easley-Lopez de Prado-O'Hara
2012 volume clock; Clark 1973 subordinated process):
  ref_bucket_size(t) = mean(daily total volume[t-20..t-1]) / 50
    (trailing 20-day mean, excludes day t itself -- no lookahead; the
    /50 constant fixes a "50 buckets on an average day" baseline)
  bucket_count(t) = floor(daily total volume(t) / ref_bucket_size(t))
  baseline_count(t) = mean(bucket_count[t-20..t-1])  (trailing 20-day
    mean of the count series itself, also excludes day t)
  daily_ratio(t) = bucket_count(t) / baseline_count(t) - 1
  R2_VT_BUCKET_COUNT_SHIFT_20(t) = mean(daily_ratio[t-19..t])

Uses only the daily volume panel (panels["volume"], which is the exact
sum of the 1m volume series by construction of the data pipeline) --
no 1m re-read is needed for this atom, so no small-sample pilot timing
check applies (pure vectorized daily-panel arithmetic, no per-symbol
1m I/O loop)."""
from __future__ import annotations

import numpy as np

from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = ("R2_VT_BUCKET_COUNT_SHIFT_20",)

_REF_N_BUCKETS = 50
_ROLL = 20
_MIN_PERIODS = 15


def _build(panels, eligibility, data_root, config):
    volume = panels["volume"]
    dates = volume.index

    ref_size = volume.shift(1).rolling(_ROLL, min_periods=_MIN_PERIODS).mean() / _REF_N_BUCKETS
    count = np.floor(volume / ref_size.where(ref_size > 0))
    count = count.where(np.isfinite(count) & (count >= 0))

    baseline = count.shift(1).rolling(_ROLL, min_periods=_MIN_PERIODS).mean()
    daily_ratio = count / baseline.where(baseline > 0) - 1.0

    atom = daily_ratio.rolling(_ROLL, min_periods=_MIN_PERIODS).mean().reindex(dates)
    return {"R2_VT_BUCKET_COUNT_SHIFT_20": atom.where(np.isfinite(atom))}


register_family(FamilyProvider("repl_vt_bucket_precise_v1", "repl_vt_bucket_precise_v1", _build))
