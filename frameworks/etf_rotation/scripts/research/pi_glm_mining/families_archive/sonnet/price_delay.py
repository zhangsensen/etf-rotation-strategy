"""Stage-S20 family: price_delay -- daily and intraday price-delay
structure against the 14-ETF equal-weight basket, directive 2026-09-20
round_587 (S20 stage, main controller, pre-specified direction,
parallel independent implementation alongside pi lane's stage 29 -- NOT
built by reading pi's code).

Literature anchors:
- Hou & Moskowitz (2005), "Market Frictions, Price Delay, and the
  Cross-Section of Expected Returns", RFS -- price delay D1 (R^2 gain
  from adding lagged market returns to a contemporaneous regression)
  and D2 (share of total explanatory power carried by the lagged
  coefficients rather than the contemporaneous one).
- Mech (1993), "Portfolio Return Autocorrelation", JFE -- a simpler
  single-lag delay coefficient (here LAG1_COEF_60) as a distinct,
  less-aggregated delay proxy from the multi-lag D1/D2 measures.
- Brennan, Jegadeesh & Swaminathan (1993), "Investment Analysis and the
  Adjustment of Stock Prices to Common Information", RFS -- lead-lag
  structure against a common (basket) factor as the delay mechanism.
- Boehmer & Wu (2013), "Short Selling and the Price Discovery Process",
  RFS -- motivates comparing a delay measure across time scales (daily
  vs intraday) as a proxy for which frequency band price discovery is
  slower in.

Directive-compliance note: the directive's first bullet (D1, 60d
rolling daily regression vs the 14-ETF equal-weight basket at
contemporaneous + lags 1-4, and D1's 20d change) duplicates the
ALREADY-EXISTING S14 atom `pi_price_delay_1d:PD_D1_CHG_20` (built in
round_569 from the identical literature definition). Per the standing
"no reinventing the wheel" rule, that atom is reused as-is (available
as a pairing partner) and NOT rebuilt here. This family instead exposes
constructs the existing atom does NOT: the raw D1 level (not just its
change), D2 (the lagged-coefficient share Hou-Moskowitz separately
define), the single-lag Mech-style coefficient, and an intraday (1m)
analogue of D1 plus its daily-vs-intraday gap.

Implementation: for each symbol, daily_ret regressed (60d rolling OLS,
intercept + contemporaneous + lags 1-4 of the 14-ETF equal-weight daily
basket return) gives R2_full and R2_restricted (contemporaneous only)
and the 5 non-intercept coefficients [b0, b1..b4]:
  D1_LEVEL_60      = 1 - R2_restricted / R2_full
  D2_LAGSHARE_60   = sum(|b1..b4|) / sum(|b0..b4|)
  LAG1_COEF_60     = b1 (Mech 1993 single-lag coefficient)
  LAG_COEF_SIGN_FREQ_20 = 20d mean of 1{sign(b1+b2+b3+b4) > 0}
  D2_LAGSHARE_CHG_20    = D2_LAGSHARE_60_t - D2_LAGSHARE_60_{t-20}
The intraday analogue uses 1m returns regressed on the 14-ETF equal-
weight 1m basket return at contemporaneous + lags 1-5 bars, estimated
per day and rolled to a 20d mean:
  D1_1M_20         = 20d mean of the daily 1m-bar D1 estimate
  D1_1M_CHG_20     = D1_1M_20_t - D1_1M_20_{t-20}
  D1_DIFF_1D_1M_20 = D1_LEVEL_60_t - D1_1M_20_t
All daily-frequency computations use only data up to and including day
t (the 60d window ends at t); the 1m basket average is the same
PIT-safe equal-weight mean-of-14-symbols convention S14 used for the
daily basket, extended intraday.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "D1_LEVEL_60",
    "D2_LAGSHARE_60",
    "LAG1_COEF_60",
    "LAG_COEF_SIGN_FREQ_20",
    "D2_LAGSHARE_CHG_20",
    "D1_1M_20",
    "D1_1M_CHG_20",
    "D1_DIFF_1D_1M_20",
)

N_LAGS = 4
D_WINDOW = 60
D_MIN_PERIODS = 45
ROLL20 = 20

N_LAGS_1M = 5


def _r2(X: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray]:
    Xc = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(Xc, y, rcond=None)
    resid = y - Xc @ beta
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = float("nan") if ss_tot <= 0 else 1.0 - ss_res / ss_tot
    return r2, beta[1:]


def _rolling_daily_delay(r_i: pd.Series, r_m: pd.Series) -> pd.DataFrame:
    lags = pd.concat([r_m.shift(k).rename(f"lag{k}") for k in range(N_LAGS + 1)], axis=1)
    df = pd.concat([r_i.rename("y"), lags], axis=1).dropna()
    if len(df) < D_MIN_PERIODS:
        return pd.DataFrame()
    y = df["y"].to_numpy(float)
    x_full = df[[f"lag{k}" for k in range(N_LAGS + 1)]].to_numpy(float)
    idx = df.index
    n = len(df)
    d1 = np.full(n, np.nan)
    d2 = np.full(n, np.nan)
    lag1 = np.full(n, np.nan)
    lag_sign = np.full(n, np.nan)
    for i in range(D_MIN_PERIODS, n + 1):
        start = max(0, i - D_WINDOW)
        yi = y[start:i]
        xi_full = x_full[start:i]
        r2_u, coefs = _r2(xi_full, yi)
        r2_r, _ = _r2(xi_full[:, :1], yi)
        if np.isfinite(r2_u) and r2_u > 1e-8 and np.isfinite(r2_r):
            d1[i - 1] = 1.0 - r2_r / r2_u
        lag_coefs = coefs[1:]
        denom = np.sum(np.abs(coefs))
        if denom > 1e-12:
            d2[i - 1] = float(np.sum(np.abs(lag_coefs)) / denom)
        lag1[i - 1] = float(lag_coefs[0])
        lag_sum = float(np.sum(lag_coefs))
        lag_sign[i - 1] = 1.0 if lag_sum > 0 else 0.0
    return pd.DataFrame(
        {"d1": d1, "d2": d2, "lag1": lag1, "lag_sign": lag_sign}, index=idx
    )


def _daily_frame(panels) -> dict:
    close = panels["close"]
    dates = close.index
    symbols = list(close.columns)
    daily_ret = close.pct_change()
    basket_ret = daily_ret.mean(axis=1, skipna=True)
    per_symbol = {}
    for sym in symbols:
        stats = _rolling_daily_delay(daily_ret[sym], basket_ret)
        per_symbol[sym] = stats
    return per_symbol


def _basket_1m_return(data_root, symbols, frequency, as_of) -> pd.Series:
    legs = []
    for sym in symbols:
        try:
            frame, _ = _read_complete_days(data_root, sym, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        frame = frame.sort_values("datetime")[["datetime", "close"]].copy()
        frame["ret"] = frame["close"].pct_change()
        legs.append(frame.set_index("datetime")["ret"])
    if not legs:
        return pd.Series(dtype=float)
    return pd.concat(legs, axis=1).mean(axis=1, skipna=True)


def _day_1m_d1(day_ret: np.ndarray, mkt_ret: np.ndarray) -> float:
    n = len(day_ret)
    if n < 60:
        return float("nan")
    cols = [mkt_ret]
    for k in range(1, N_LAGS_1M + 1):
        shifted = np.full(n, np.nan)
        shifted[k:] = mkt_ret[:-k]
        cols.append(shifted)
    X = np.column_stack(cols)
    mask = np.isfinite(day_ret) & np.all(np.isfinite(X), axis=1)
    if mask.sum() < 60:
        return float("nan")
    y = day_ret[mask]
    Xm = X[mask]
    r2_u, _ = _r2(Xm, y)
    r2_r, _ = _r2(Xm[:, :1], y)
    if not (np.isfinite(r2_u) and r2_u > 1e-8 and np.isfinite(r2_r)):
        return float("nan")
    return 1.0 - r2_r / r2_u


def _intraday_d1_series(data_root, sym, mkt_ret_1m, frequency, as_of) -> pd.Series:
    try:
        frame, _ = _read_complete_days(data_root, sym, frequency, as_of)
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)
    if frame.empty:
        return pd.Series(dtype=float)
    frame = frame.sort_values("datetime")[["datetime", "close"]].copy()
    frame["ret"] = frame["close"].pct_change()
    frame = frame.set_index("datetime")
    frame["mkt_ret"] = mkt_ret_1m.reindex(frame.index)
    frame["date"] = frame.index.normalize()

    recs = []
    for date, day in frame.groupby("date", sort=True):
        d1 = _day_1m_d1(day["ret"].to_numpy(float), day["mkt_ret"].to_numpy(float))
        if np.isfinite(d1):
            recs.append({"date": date, "d1_1m": d1})
    if not recs:
        return pd.Series(dtype=float)
    daily = pd.DataFrame(recs).set_index("date")["d1_1m"].sort_index()
    return daily


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    frequency = str(config.get("frequency", "1m"))
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    daily_stats = _daily_frame(panels)
    mkt_ret_1m = _basket_1m_return(data_root, symbols, frequency, as_of)

    for sym in symbols:
        stats = daily_stats.get(sym, pd.DataFrame())
        if stats.empty:
            continue
        d1_60 = stats["d1"].reindex(dates)
        d2_60 = stats["d2"].reindex(dates)
        lag1_60 = stats["lag1"].reindex(dates)
        lag_sign = stats["lag_sign"]

        out["D1_LEVEL_60"][sym] = d1_60
        out["D2_LAGSHARE_60"][sym] = d2_60
        out["LAG1_COEF_60"][sym] = lag1_60
        out["LAG_COEF_SIGN_FREQ_20"][sym] = (
            lag_sign.rolling(ROLL20, min_periods=12).mean().reindex(dates)
        )
        out["D2_LAGSHARE_CHG_20"][sym] = (d2_60 - d2_60.shift(ROLL20))

        d1_1m_daily = _intraday_d1_series(data_root, sym, mkt_ret_1m, frequency, as_of)
        if not d1_1m_daily.empty:
            d1_1m_20 = d1_1m_daily.rolling(ROLL20, min_periods=10).mean().reindex(dates)
            out["D1_1M_20"][sym] = d1_1m_20
            out["D1_1M_CHG_20"][sym] = (d1_1m_20 - d1_1m_20.shift(ROLL20))
            out["D1_DIFF_1D_1M_20"][sym] = (d1_60 - d1_1m_20)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("price_delay", "price_delay", _build))
