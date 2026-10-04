"""Stage-S41 family: overnight_return_distribution -- deepens this
line's strongest no-volume dimension (overnight behavior: YZ_OVERNIGHT_
SHARE_20, ON_SIGN_STREAK_20, GAP_DD_CONSUMPTION_RATIO_20 are among the
strongest no-volume legs) beyond mean/variance-share/sign-streak into
distribution SHAPE. Directive 2026-09-21 round_640 (S41 stage, main
controller).

Literature anchors:
- Lou, Polk & Skouras (2019), "A Tug of War" -- overnight/intraday
  return clienteles differ; distributional asymmetry of overnight
  returns is a natural extension of the mean-level ON_PREM construct.
- Aboody, Even-Tov, Lehavy & Trueman (2018), "Overnight Returns and
  Firm-Specific Investor Sentiment" -- overnight return distribution
  shape as a sentiment proxy.
- Bollerslev, Li & Zhao (2020), "Good Volatility, Bad Volatility, and
  the Cross-Section of Stock Returns" -- downside/upside variance
  decomposition, applied here to the overnight (not intraday) return.

Implementation: entirely from DAILY panels (open, close) -- no 1m read
at all, unlike most of this line's recent families. overnight_ret(D) =
open(D)/close(D-1) - 1; prior_intraday_ret(D) = close(D-1)/open(D-1) - 1
(the day BEFORE D's own intraday return, i.e. shift(1) of the standard
intraday return series).

Atoms (all rolling, no fixed threshold beyond percentile/skew/kurtosis
definitions themselves):
  OVERNIGHT_SKEW_60 / OVERNIGHT_KURTOSIS_60: 60d rolling skew / excess
    kurtosis (pandas convention, already excess) of overnight_ret.
  OVERNIGHT_DOWNSIDE_VAR_SHARE_60: 60d rolling mean(overnight_ret^2 |
    overnight_ret<0) / 60d rolling mean(overnight_ret^2) (downside
    variance share of total overnight variance; NaN when no negative
    days in the window).
  OVERNIGHT_TAIL_RATIO_60: 60d rolling 5th percentile / 95th percentile
    of overnight_ret (as specified literally; typically both negative
    numerator and positive denominator, so the value itself is
    negative -- its MAGNITUDE still carries cross-sectional tail-
    asymmetry information after ranking).
  OVERNIGHT_ACTIVITY_RATIO_20_60: 20d rolling mean(|overnight_ret|) /
    60d rolling mean(|overnight_ret|).
  OVERNIGHT_PRIOR_INTRADAY_CORR_20: 20d rolling correlation between
    overnight_ret(D) and prior_intraday_ret(D) (does today's overnight
    gap continue yesterday's intraday move).
"""
from __future__ import annotations

import numpy as np

from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "OVERNIGHT_SKEW_60",
    "OVERNIGHT_KURTOSIS_60",
    "OVERNIGHT_DOWNSIDE_VAR_SHARE_60",
    "OVERNIGHT_TAIL_RATIO_60",
    "OVERNIGHT_ACTIVITY_RATIO_20_60",
    "OVERNIGHT_PRIOR_INTRADAY_CORR_20",
)


def _build(panels, eligibility, data_root, config):
    close = panels["close"]
    open_p = panels["open"]

    overnight_ret = open_p / close.shift(1) - 1.0
    intraday_ret = close / open_p - 1.0
    prior_intraday_ret = intraday_ret.shift(1)

    skew_60 = overnight_ret.rolling(60, min_periods=40).skew()
    kurt_60 = overnight_ret.rolling(60, min_periods=40).kurt()

    sq = overnight_ret**2
    downside_sq = sq.where(overnight_ret < 0)
    total_var_60 = sq.rolling(60, min_periods=40).mean()
    # downside_sq is NaN on ~half the days by construction (only negative-
    # overnight days survive the mask), so a 60-bar window has roughly 30
    # non-NaN entries even when fully populated; min_periods=40 (copied
    # from the unmasked total_var_60 window) was never satisfiable and
    # left this atom almost entirely NaN. Use a lower threshold matched
    # to the ~50% sparsity instead.
    downside_var_60 = downside_sq.rolling(60, min_periods=15).mean()
    downside_share_60 = (downside_var_60 / total_var_60).where(total_var_60 > 0)

    q05_60 = overnight_ret.rolling(60, min_periods=40).quantile(0.05)
    q95_60 = overnight_ret.rolling(60, min_periods=40).quantile(0.95)
    tail_ratio_60 = (q05_60 / q95_60).where(q95_60 != 0)

    abs_on = overnight_ret.abs()
    activity_20 = abs_on.rolling(20, min_periods=12).mean()
    activity_60 = abs_on.rolling(60, min_periods=40).mean()
    activity_ratio = (activity_20 / activity_60).where(activity_60 > 0)

    prior_corr_20 = overnight_ret.rolling(20, min_periods=12).corr(prior_intraday_ret)

    out = {
        "OVERNIGHT_SKEW_60": skew_60,
        "OVERNIGHT_KURTOSIS_60": kurt_60,
        "OVERNIGHT_DOWNSIDE_VAR_SHARE_60": downside_share_60,
        "OVERNIGHT_TAIL_RATIO_60": tail_ratio_60,
        "OVERNIGHT_ACTIVITY_RATIO_20_60": activity_ratio,
        "OVERNIGHT_PRIOR_INTRADAY_CORR_20": prior_corr_20,
    }
    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("overnight_return_distribution", "overnight_return_distribution", _build))
