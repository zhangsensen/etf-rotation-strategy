"""Stage-S14 family: pi_replication_s14 -- independent re-implementation
of 4 pi-lane non-volume-only candidates (DA57, CZ01, CA1, CK04), built
strictly from the literature definitions in the S14 directive
(2026-09-20 round_569), WITHOUT reading the pi workspace's code, to
cross-check the two lanes' independent engineering.

Literature anchors:
- Hou & Moskowitz (2005), "Market Frictions, Price Delay, and the
  Cross-Section of Expected Returns", RFS -- price delay D1 = 1 -
  R^2(restricted, contemporaneous-only market regression) /
  R^2(unrestricted, market + 4 lags), rolling 60-trading-day daily-
  frequency regression against the 14-ETF equal-weight basket.
- Amihud & Mendelson (1987), "Trading Mechanisms and Stock Returns: An
  Empirical Investigation", JF -- opening vs. closing volatility
  asymmetry; here proxied as the ratio of first-30-minute to
  last-30-minute 1m realized variance.
- Karpoff (1987), "The Relation Between Price Changes and Trading
  Volume: A Survey", JFQA -- volume-price elasticity, the regression
  slope of |return| on log(volume) across a day's 1m bars.
- Lou, Polk & Skouras (2019), "A Tug of War: Overnight versus Intraday
  Expected Returns", JFE -- overnight (close-to-open) return as a
  distinct return component from the intraday session (reused here via
  the pre-existing daily_candle:GAP_MEAN_20, which is textually
  identical: 20d mean of open/prev_close - 1).

Directive-specific atom naming: this line's PRE-EXISTING
`bar_size_order_flow:BIGBAR_EDGE_CONC_20` uses a DIFFERENT definition
(modal-30-min-slot concentration of amount>5x-median "big" bars) than
the S14 directive's pi-replication target (top-10%-by-volume-bar share
of TOTAL DAY VOLUME that additionally falls in the first/last 30
minutes). To avoid silently reusing the wrong formula under a
name collision, the correctly-matching construct is implemented here
under a new name, EDGE_BIGBAR_VOLSHARE_20, and used in place of pi's
BIGBAR_EDGE_CONC_20 in the DA57-analog pairing.
`bar_size_order_flow:CLOSE5_DAY_CONSIST_20` (tail-5-minute direction
matching full-day direction, 20d mean = fraction of matching days) DOES
match the directive's definition exactly and is reused as-is (not
rebuilt here). `daily_candle:GAP_MEAN_20` likewise already matches
ON_PREM_20's definition exactly and is reused as-is.

Implementation:
  PD_D1_CHG_20: for each symbol, daily simple returns r_i regressed
    (60-day rolling OLS, with intercept) on (a) contemporaneous 14-ETF
    equal-weight basket return r_m,t [restricted] and (b) r_m,t plus
    its 4 daily lags [unrestricted]; D1 = 1 - R2_restricted/R2_unrestricted;
    PD_D1_CHG_20 = D1 minus its value 20 trading days earlier.
  AUC_VARIANCE_RATIO_20: within each day, RV of the first 30 1m bars
    divided by RV of the last 30 1m bars (both close-to-close simple
    returns, PIT within the day), 20d mean.
  PV_ELASTICITY_20: within each day, OLS slope of |1m return| on
    log(1m volume) across the day's bars, 20d mean of the daily slope.
  EDGE_BIGBAR_VOLSHARE_20: within each day, the volume-weighted share of
    total day volume contributed by bars in the top decile of 1m volume
    AND located in the first or last 30 minutes of the session, 20d mean.
  LUNCH_PRE_RUN_20: within each day, the fraction of total day volume
    occurring in the 11:20-11:30 wall-clock window (last 10 minutes
    before the lunch break), 20d mean.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ROLL_WINDOW = 20
PD_WINDOW = 60
PD_MIN_PERIODS = 45
N_LAGS = 4

ATOM_NAMES = (
    "PD_D1_CHG_20",
    "AUC_VARIANCE_RATIO_20",
    "PV_ELASTICITY_20",
    "EDGE_BIGBAR_VOLSHARE_20",
    "LUNCH_PRE_RUN_20",
)


def _r2(X: np.ndarray, y: np.ndarray) -> float:
    Xc = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(Xc, y, rcond=None)
    resid = y - Xc @ beta
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    if ss_tot <= 0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def _rolling_price_delay_d1(r_i: pd.Series, r_m: pd.Series) -> pd.Series:
    lags = pd.concat([r_m.shift(k).rename(f"lag{k}") for k in range(N_LAGS + 1)], axis=1)
    df = pd.concat([r_i.rename("y"), lags], axis=1).dropna()
    if len(df) < PD_MIN_PERIODS:
        return pd.Series(dtype=float)
    y = df["y"].to_numpy(float)
    x_full = df[[f"lag{k}" for k in range(N_LAGS + 1)]].to_numpy(float)
    idx = df.index
    n = len(df)
    out = np.full(n, np.nan)
    for i in range(PD_MIN_PERIODS, n + 1):
        start = max(0, i - PD_WINDOW)
        yi = y[start:i]
        xi_full = x_full[start:i]
        xi_r = xi_full[:, :1]
        r2_u = _r2(xi_full, yi)
        r2_r = _r2(xi_r, yi)
        if np.isfinite(r2_u) and r2_u > 1e-8 and np.isfinite(r2_r):
            out[i - 1] = 1.0 - r2_r / r2_u
    return pd.Series(out, index=idx)


def _build_price_delay(panels) -> pd.DataFrame:
    close = panels["close"]
    dates = close.index
    symbols = list(close.columns)
    daily_ret = close.pct_change()
    basket_ret = daily_ret.mean(axis=1, skipna=True)
    out = pd.DataFrame(np.nan, index=dates, columns=symbols)
    for sym in symbols:
        d1 = _rolling_price_delay_d1(daily_ret[sym], basket_ret)
        if d1.empty:
            continue
        d1 = d1.reindex(dates)
        out[sym] = (d1 - d1.shift(ROLL_WINDOW)).to_numpy()
    return out


def _day_intraday_features(day: pd.DataFrame) -> dict | None:
    close = day["close"].to_numpy(float)
    open0 = float(day["open"].to_numpy(float)[0])
    volume = day["volume"].to_numpy(float)
    times = day["datetime"]
    prev = np.concatenate([[open0], close[:-1]])
    with np.errstate(all="ignore"):
        r = close / np.where(prev > 0, prev, np.nan) - 1.0
    ok = np.isfinite(r) & np.isfinite(volume) & (volume > 0)
    n_ok = int(ok.sum())
    if n_ok < 120:
        return None
    r_ok = r[ok]
    vol_ok = volume[ok]
    times_ok = times.to_numpy()[ok]

    n = len(r)
    first30 = np.zeros(n, dtype=bool)
    first30[:30] = True
    last30 = np.zeros(n, dtype=bool)
    last30[-30:] = True
    rv_open30 = float(np.sum(np.where(np.isfinite(r) & first30, r, 0.0) ** 2))
    rv_close30 = float(np.sum(np.where(np.isfinite(r) & last30, r, 0.0) ** 2))
    auc_ratio = rv_open30 / rv_close30 if rv_close30 > 0 else float("nan")

    abs_r = np.abs(r_ok)
    log_v = np.log(vol_ok)
    if len(log_v) >= 30 and np.std(log_v) > 0:
        slope = float(np.cov(log_v, abs_r, ddof=1)[0, 1] / np.var(log_v, ddof=1))
    else:
        slope = float("nan")

    total_vol = float(volume[np.isfinite(volume) & (volume > 0)].sum())
    decile_thresh = np.quantile(vol_ok, 0.90)
    edge_mask = np.zeros(n, dtype=bool)
    edge_mask[:30] = True
    edge_mask[-30:] = True
    big_edge_mask = (volume >= decile_thresh) & edge_mask & np.isfinite(volume)
    edge_bigbar_share = (
        float(volume[big_edge_mask].sum() / total_vol) if total_vol > 0 else float("nan")
    )

    ts = pd.to_datetime(times_ok)
    minutes_of_day = ts.hour * 60 + ts.minute
    lunch_mask = (minutes_of_day >= 11 * 60 + 20) & (minutes_of_day <= 11 * 60 + 30)
    lunch_vol = float(vol_ok[lunch_mask].sum())
    lunch_pre_run = lunch_vol / total_vol if total_vol > 0 else float("nan")

    return {
        "auc_ratio": auc_ratio,
        "pv_slope": slope,
        "edge_bigbar_share": edge_bigbar_share,
        "lunch_pre_run": lunch_pre_run,
    }


def _build_intraday(data_root, symbols, frequency, as_of, dates) -> dict[str, pd.DataFrame]:
    out = {
        name: pd.DataFrame(np.nan, index=dates, columns=symbols)
        for name in ("AUC_VARIANCE_RATIO_20", "PV_ELASTICITY_20", "EDGE_BIGBAR_VOLSHARE_20", "LUNCH_PRE_RUN_20")
    }
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
            feats = _day_intraday_features(day)
            if feats is not None:
                feats["date"] = date
                records.append(feats)
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date").sort_index()
        out["AUC_VARIANCE_RATIO_20"][sym] = (
            daily["auc_ratio"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["PV_ELASTICITY_20"][sym] = (
            daily["pv_slope"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["EDGE_BIGBAR_VOLSHARE_20"][sym] = (
            daily["edge_bigbar_share"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
        out["LUNCH_PRE_RUN_20"][sym] = (
            daily["lunch_pre_run"].rolling(ROLL_WINDOW, min_periods=10).mean().reindex(dates)
        )
    return out


def _build_pi_replication(panels, eligibility, data_root, config):
    frequency = str(config.get("frequency", "1m"))
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    root = Path(data_root)

    out: dict[str, pd.DataFrame] = {}
    out["PD_D1_CHG_20"] = _build_price_delay(panels)
    out.update(_build_intraday(root, symbols, frequency, as_of, dates))
    return out


# Registered as 5 distinct single-atom families (sharing one builder) so
# the engine's cross_family_only pairing grammar can combine them with
# each other (e.g. DA57 = PD_D1_CHG_20 x AUC_VARIANCE_RATIO_20), which a
# single grouped family would forbid.
register_family(FamilyProvider("pi_price_delay_1d", "pi_price_delay_1d", _build_pi_replication))
register_family(FamilyProvider("pi_auc_variance_ratio_1m", "pi_auc_variance_ratio_1m", _build_pi_replication))
register_family(FamilyProvider("pi_pv_elasticity_1m", "pi_pv_elasticity_1m", _build_pi_replication))
register_family(FamilyProvider("pi_edge_bigbar_volshare_1m", "pi_edge_bigbar_volshare_1m", _build_pi_replication))
register_family(FamilyProvider("pi_lunch_prerun_1m", "pi_lunch_prerun_1m", _build_pi_replication))
