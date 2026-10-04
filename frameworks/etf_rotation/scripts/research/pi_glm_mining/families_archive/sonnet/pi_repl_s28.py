"""S28 stage (round_618, main controller directive, "第三批" cross-lane
reproduction of pi lane's remaining two-window-significant pairs): the
6 prescribed pairs reuse atoms this line already built independently in
earlier stages (LUNCH_GAP_20/LUNCH_POST_RUN_20 from S22 lunch_break_1m,
R_ULCER_20/R_LOG_AMOUNT_VOL_20 from S26R repl_volume_core, VT_BUCKET_GINI_20
from S24 volume_time_1m, PD_D1_CHG_20 from S14 pi_price_delay_1d -- that
atom's own docstring in price_delay.py already documents it as "reused
as-is, not rebuilt" for the S20 family, so it is reused here too rather
than rebuilt a third time -- and PV_ELASTICITY_20 from S14
pi_pv_elasticity_1m). Only 2 atoms in the directive's pair list have no
prior independent implementation on this line and are built fresh here:

  S28_PRICE_POSITION_20: (close_t - LLV(low, 20)) / (HHV(high, 20) -
    LLV(low, 20)) -- Stochastic-oscillator-style price-range position,
    20-day high/low computed from the daily OHLC panels (Lane 1984
    %K construction; used here only as a directive-specified pairing
    leg, pi's own reported number for CO09 is weak/non-significant
    and this atom is explicitly a magnitude contrast, not a discovery
    target).

  S28_VOV_HAR_RESID_20: Corsi (2009) HAR-RV residual as a
    volatility-of-volatility surprise measure. Per symbol: daily
    realized variance RV_t = sum of squared 1m log returns within day
    t (from the local 1m panel). HAR predictors are lagged (no same-day
    leakage): RV_{t-1}, RV5_{t-1} = mean(RV_{t-5..t-1}), RV22_{t-1} =
    mean(RV_{t-22..t-1}). A 60-day rolling OLS of RV_t on
    [1, RV_{t-1}, RV5_{t-1}, RV22_{t-1}] (window ending at t, the same
    in-sample-rolling-window convention this line's price_delay.py
    D1_LEVEL_60 already uses) gives a fitted value; the residual
    RV_t - fitted_t is the within-window HAR pricing error for day t.
    20-day rolling mean of that residual series.

Both are registered as a single new family (they never pair against
each other, only against pre-existing atoms from other families, so no
cross_family_only split is needed)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "S28_PRICE_POSITION_20",
    "S28_VOV_HAR_RESID_20",
)

_HAR_WINDOW = 60
_HAR_MIN_PERIODS = 45


def _daily_rv(data_root, sym, as_of) -> pd.Series:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)
    if frame.empty or "close" not in frame.columns:
        return pd.Series(dtype=float)
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()

    recs = []
    for date, day in frame.groupby("date", sort=True):
        close = day["close"].to_numpy(float)
        if len(close) < 10 or np.any(close <= 0):
            continue
        ret = np.diff(np.log(close))
        rv = float(np.sum(ret ** 2))
        recs.append({"date": date, "rv": rv})
    if not recs:
        return pd.Series(dtype=float)
    return pd.DataFrame(recs).set_index("date")["rv"].sort_index()


def _ols_resid(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    Xc = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(Xc, y, rcond=None)
    return y - Xc @ beta, beta


def _har_resid_series(rv: pd.Series) -> pd.Series:
    if rv.empty:
        return pd.Series(dtype=float)
    rv1 = rv.shift(1)
    rv5 = rv.shift(1).rolling(5, min_periods=5).mean()
    rv22 = rv.shift(1).rolling(22, min_periods=22).mean()
    df = pd.concat({"y": rv, "rv1": rv1, "rv5": rv5, "rv22": rv22}, axis=1).dropna()
    if len(df) < _HAR_MIN_PERIODS:
        return pd.Series(dtype=float)
    y = df["y"].to_numpy(float)
    X = df[["rv1", "rv5", "rv22"]].to_numpy(float)
    idx = df.index
    n = len(df)
    resid_at_t = np.full(n, np.nan)
    for i in range(_HAR_MIN_PERIODS, n + 1):
        start = max(0, i - _HAR_WINDOW)
        yi = y[start:i]
        Xi = X[start:i]
        resid, _ = _ols_resid(Xi, yi)
        resid_at_t[i - 1] = resid[-1]
    return pd.Series(resid_at_t, index=idx)


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    high_p = panels["high"]
    low_p = panels["low"]
    close_p = panels["close"]

    hhv_20 = high_p.rolling(20, min_periods=15).max()
    llv_20 = low_p.rolling(20, min_periods=15).min()
    rng = hhv_20 - llv_20
    position = (close_p - llv_20) / rng.where(rng > 0)
    out["S28_PRICE_POSITION_20"] = position.reindex(dates)

    for sym in symbols:
        rv = _daily_rv(data_root, sym, as_of)
        resid = _har_resid_series(rv)
        if resid.empty:
            continue
        resid_20 = resid.rolling(20, min_periods=12).mean()
        out["S28_VOV_HAR_RESID_20"][sym] = resid_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("pi_repl_s28", "pi_repl_s28", _build))
