"""Stage-S5 family: microstructure_noise_1m -- market microstructure noise
variance and the realized-variance signature plot, directive 2026-09-20
round_531 (S5 stage, main controller, pre-specified direction).

Literature anchors:
- Bandi & Russell (2008), "Microstructure Noise, Realized Variance, and
  Optimal Sampling", Review of Economic Studies -- noise variance
  estimated from the discrepancy between realized variance at a very fine
  sampling frequency and a coarser one.
- Zhang, Mykland & Ait-Sahalia (2005), "A Tale of Two Time Scales:
  Determining Integrated Volatility with Noisy High-Frequency Data",
  JASA -- the coarser-scale realized variance is a less noise-inflated,
  more consistent proxy for integrated variance (simplified single-scale
  proxy used here, consistent with this line's practitioner-proxy
  convention: RV at the slower 5m scale stands in for the two-scale
  estimator rather than the full multi-grid TSRV construction).
- Andersen, Bollerslev, Diebold & Labys (2000), "Great Realizations" /
  the realized-variance "signature plot" -- RV computed at increasingly
  fine sampling intervals rises as Delta -> 0 when microstructure noise is
  present; the slope of log(RV) on log(interval) summarizes noise
  intensity.
- Hansen & Lunde (2006), "Realized Variance and Market Microstructure
  Noise", JBES -- noise-to-signal ratio framing (noise variance relative
  to the integrated-variance proxy).
- Roll (1984) bid-ask bounce: negative first-order return autocovariance
  as a noise proxy, applied here to the full-day 1m return sequence
  (distinct from this line's earlier daily-close-to-close ROLL_SPREAD
  atoms in microstructure_1m, which use daily not intraday returns).

Implementation (practitioner proxy, consistent with this line's existing
1m conventions): within each trading day, using 1m/5m/15m close prices
(pct_change, overnight gap included in the first intraday bar exactly as
this line's other 1m families already do, e.g. jump_continuous_beta.py):
  RV_f = sum of squared returns at frequency f (f in {1m, 5m, 15m})
  noise_var = (RV_1m - RV_5m) / (2 * n_1m)          [Bandi-Russell form]
  tsrv_proxy = RV_5m                                 [coarse-scale proxy]
  noise_signal_ratio = noise_var / tsrv_proxy
  tsrv_rv1m_ratio = RV_5m / RV_1m
  sig_plot_slope = OLS slope of log(RV_f) on log(f) across f in {1,5,15}
  roll_noise_proxy = -autocov_lag1(1m returns within the day)
All daily statistics are then rolled to a 20-day mean (and 20-day change
for three of them), never using same-day-or-later information beyond the
day itself.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "NOISE_VAR_20",
    "NOISE_SIGNAL_RATIO_20",
    "SIG_PLOT_SLOPE_20",
    "TSRV_RV1M_RATIO_20",
    "ROLL_NOISE_PROXY_20",
    "NOISE_VAR_CHG_20",
    "NOISE_SIGNAL_RATIO_CHG_20",
    "ROLL_NOISE_PROXY_CHG_20",
)

_FREQ_MINUTES = {"1m": 1, "5m": 5, "15m": 15}


def _daily_returns_by_freq(data_root, sym, frequency, as_of) -> dict:
    try:
        frame, _ = _read_complete_days(data_root, sym, frequency, as_of)
    except Exception:  # noqa: BLE001
        return {}
    if frame.empty:
        return {}
    frame = frame.sort_values("datetime")[["datetime", "close"]].copy()
    frame["ret"] = frame["close"].pct_change()
    frame = frame.set_index("datetime")
    frame["date"] = frame.index.normalize()
    out = {}
    for date, day in frame.groupby("date", sort=True):
        r = day["ret"].to_numpy(float)
        r = r[np.isfinite(r)]
        if len(r) < 3:
            continue
        out[date] = r
    return out


def _daily_noise_frame(data_root, sym, as_of) -> pd.DataFrame:
    rets_1m = _daily_returns_by_freq(data_root, sym, "1m", as_of)
    rets_5m = _daily_returns_by_freq(data_root, sym, "5m", as_of)
    rets_15m = _daily_returns_by_freq(data_root, sym, "15m", as_of)
    if not rets_1m or not rets_5m or not rets_15m:
        return pd.DataFrame()

    common_dates = sorted(set(rets_1m) & set(rets_5m) & set(rets_15m))
    recs = []
    for date in common_dates:
        r1, r5, r15 = rets_1m[date], rets_5m[date], rets_15m[date]
        n1 = len(r1)
        rv1 = float(np.sum(r1**2))
        rv5 = float(np.sum(r5**2))
        rv15 = float(np.sum(r15**2))
        if rv1 <= 0 or rv5 <= 0 or rv15 <= 0 or n1 < 3:
            continue

        noise_var = (rv1 - rv5) / (2.0 * n1)
        tsrv_proxy = rv5
        noise_signal_ratio = noise_var / tsrv_proxy if tsrv_proxy > 0 else np.nan
        tsrv_rv1m_ratio = rv5 / rv1

        log_f = np.log(np.array([1.0, 5.0, 15.0]))
        log_rv = np.log(np.array([rv1, rv5, rv15]))
        slope = float(np.polyfit(log_f, log_rv, 1)[0])

        if n1 >= 4:
            r1_c = r1 - r1.mean()
            autocov1 = float(np.mean(r1_c[:-1] * r1_c[1:]))
            roll_noise = -autocov1
        else:
            roll_noise = np.nan

        recs.append(
            {
                "date": date,
                "noise_var": noise_var,
                "noise_signal_ratio": noise_signal_ratio,
                "sig_plot_slope": slope,
                "tsrv_rv1m_ratio": tsrv_rv1m_ratio,
                "roll_noise_proxy": roll_noise,
            }
        )
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    for sym in symbols:
        daily = _daily_noise_frame(data_root, sym, as_of)
        if daily.empty:
            continue

        noise_var_20 = daily["noise_var"].rolling(20, min_periods=12).mean()
        noise_signal_ratio_20 = daily["noise_signal_ratio"].rolling(20, min_periods=12).mean()
        sig_plot_slope_20 = daily["sig_plot_slope"].rolling(20, min_periods=12).mean()
        tsrv_rv1m_ratio_20 = daily["tsrv_rv1m_ratio"].rolling(20, min_periods=12).mean()
        roll_noise_proxy_20 = daily["roll_noise_proxy"].rolling(20, min_periods=12).mean()

        out["NOISE_VAR_20"][sym] = noise_var_20.reindex(dates)
        out["NOISE_SIGNAL_RATIO_20"][sym] = noise_signal_ratio_20.reindex(dates)
        out["SIG_PLOT_SLOPE_20"][sym] = sig_plot_slope_20.reindex(dates)
        out["TSRV_RV1M_RATIO_20"][sym] = tsrv_rv1m_ratio_20.reindex(dates)
        out["ROLL_NOISE_PROXY_20"][sym] = roll_noise_proxy_20.reindex(dates)
        out["NOISE_VAR_CHG_20"][sym] = (noise_var_20 - noise_var_20.shift(20)).reindex(dates)
        out["NOISE_SIGNAL_RATIO_CHG_20"][sym] = (
            noise_signal_ratio_20 - noise_signal_ratio_20.shift(20)
        ).reindex(dates)
        out["ROLL_NOISE_PROXY_CHG_20"][sym] = (
            roll_noise_proxy_20 - roll_noise_proxy_20.shift(20)
        ).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("microstructure_noise_1m", "microstructure_noise_1m", _build))
