"""Stage-S13 family: frequency_domain_beta_1m -- systematic risk (beta to
the 510300.SH/510500.SH broad-market proxy) decomposed by frequency band
within the 1m intraday path, directive 2026-09-20 round_565 (S13 stage,
main controller, pre-specified direction).

Literature anchors:
- Engle (1974), "Band Spectrum Regression", International Economic
  Review -- OLS regression restricted to a frequency band via the
  discrete Fourier transform: within a band, beta = sum(co-spectrum) /
  sum(regressor power), the frequency-domain analog of time-domain OLS.
- Bandi & Perron (2008), "Long-Run Risk-Return Trade-Offs", Journal of
  Econometrics -- long-run (low-frequency) beta differs systematically
  from short-run (high-frequency) beta; the gap is itself informative.
- Dew-Becker & Giglio (2016), "Asset Pricing in the Frequency Domain:
  Theory and Empirics", Review of Financial Studies -- risk premia and
  factor loadings vary by frequency; low-frequency co-movement reflects
  persistent/fundamental risk, high-frequency co-movement reflects
  transient/microstructure-driven co-movement.
- Chaudhuri & Lo (2016), "Spectral Portfolio Theory", -- spectral
  (frequency-band) decomposition of portfolio risk exposures.

Implementation (practitioner proxy, consistent with this line's existing
1m-beta conventions in jump_continuous_beta.py, reusing its
510300.SH/510500.SH market-proxy convention): within each trading day,
using the day's 1m simple returns r_i (asset) and r_m (market proxy,
mean of the two benchmark ETFs' 1m returns), both demeaned, real FFT to
get complex Fourier coefficients R_i[k], R_m[k] at frequency bins
k=1..n/2 (k=0/DC excluded; n=240 bars/day). Period_k (minutes) = n/k.
Three bands (period-based, matching Bandi-Perron's short/long-run split
into three tiers): high frequency (period <15min, k>16), mid frequency
(15-60min, 4<=k<=16), low frequency (period >60min, k<4). Within each
band:
  BETA_band = Re(sum_k conj(R_m[k]) * R_i[k]) / sum_k |R_m[k]|^2
    (Engle 1974 band-spectrum regression coefficient)
  COHERENCE_band = |sum_k conj(R_m[k]) * R_i[k]|^2 /
    (sum_k |R_i[k]|^2 * sum_k |R_m[k]|^2)
    (bounded in [0,1] by Cauchy-Schwarz on the band's complex inner
    product; the frequency-domain analog of within-band R^2)
  BETA_HF_20 / BETA_MF_20 / BETA_LF_20 = 20d mean of the daily band beta.
  BETA_FREQ_SLOPE_20 = 20d mean of daily(BETA_LF - BETA_HF) (Bandi-Perron
    long-run-minus-short-run beta gap).
  COHERENCE_LF_HF_DIFF_20 = 20d mean of daily(COHERENCE_LF - COHERENCE_HF).
  BETA_HF_CHG_20 / BETA_LF_CHG_20 / BETA_FREQ_SLOPE_CHG_20 = 20-day change
    of the corresponding _20 atom.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ROLL_WINDOW = 20
MIN_BARS_PER_DAY = 120

ATOM_NAMES = (
    "BETA_HF_20",
    "BETA_MF_20",
    "BETA_LF_20",
    "BETA_FREQ_SLOPE_20",
    "COHERENCE_LF_HF_DIFF_20",
    "BETA_HF_CHG_20",
    "BETA_LF_CHG_20",
    "BETA_FREQ_SLOPE_CHG_20",
)


def _market_return_series(data_root, benchmark_symbols, frequency, as_of) -> pd.Series:
    legs = []
    for sym in benchmark_symbols:
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


def _band_indices(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    k = np.arange(1, n // 2 + 1)
    period = n / k
    hf = k[period < 15]
    mf = k[(period >= 15) & (period <= 60)]
    lf = k[period > 60]
    return hf, mf, lf


def _band_beta_coherence(r_i: np.ndarray, r_m: np.ndarray, idx: np.ndarray) -> tuple[float, float]:
    if len(idx) == 0:
        return float("nan"), float("nan")
    ri_f = np.fft.rfft(r_i - r_i.mean())
    rm_f = np.fft.rfft(r_m - r_m.mean())
    ci = ri_f[idx]
    cm = rm_f[idx]
    cross = np.sum(np.conj(cm) * ci)
    m_power = float(np.sum(np.abs(cm) ** 2))
    i_power = float(np.sum(np.abs(ci) ** 2))
    beta = float(np.real(cross) / m_power) if m_power > 0 else float("nan")
    coherence = (
        float((np.abs(cross) ** 2) / (i_power * m_power)) if i_power > 0 and m_power > 0 else float("nan")
    )
    return beta, coherence


def _daily_freq_beta(data_root, sym, market_ret, frequency, as_of) -> pd.DataFrame:
    try:
        frame, _ = _read_complete_days(data_root, sym, frequency, as_of)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if frame.empty:
        return pd.DataFrame()
    frame = frame.sort_values("datetime")[["datetime", "close"]].copy()
    frame["ret"] = frame["close"].pct_change()
    frame = frame.set_index("datetime")
    frame["mkt_ret"] = market_ret.reindex(frame.index)
    frame = frame.dropna(subset=["ret", "mkt_ret"])
    if frame.empty:
        return pd.DataFrame()
    frame["date"] = frame.index.normalize()

    recs = []
    for date, day in frame.groupby("date", sort=True):
        r_i = day["ret"].to_numpy(float)
        r_m = day["mkt_ret"].to_numpy(float)
        finite = np.isfinite(r_i) & np.isfinite(r_m)
        r_i, r_m = r_i[finite], r_m[finite]
        n = len(r_i)
        if n < MIN_BARS_PER_DAY:
            continue
        hf_idx, mf_idx, lf_idx = _band_indices(n)
        beta_hf, coh_hf = _band_beta_coherence(r_i, r_m, hf_idx)
        beta_mf, _ = _band_beta_coherence(r_i, r_m, mf_idx)
        beta_lf, coh_lf = _band_beta_coherence(r_i, r_m, lf_idx)
        recs.append(
            {
                "date": date,
                "beta_hf": beta_hf,
                "beta_mf": beta_mf,
                "beta_lf": beta_lf,
                "freq_slope": beta_lf - beta_hf if np.isfinite(beta_lf) and np.isfinite(beta_hf) else np.nan,
                "coh_diff": coh_lf - coh_hf if np.isfinite(coh_lf) and np.isfinite(coh_hf) else np.nan,
            }
        )
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _build_frequency_domain_beta(panels, eligibility, data_root, config):
    frequency = str(config.get("frequency", "1m"))
    benchmark_symbols = list(config["benchmark_symbols"])
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    market_ret = _market_return_series(data_root, benchmark_symbols, frequency, as_of)
    if market_ret.empty:
        return out

    for sym in symbols:
        daily = _daily_freq_beta(data_root, sym, market_ret, frequency, as_of)
        if daily.empty:
            continue
        beta_hf_20 = daily["beta_hf"].rolling(ROLL_WINDOW, min_periods=10).mean()
        beta_mf_20 = daily["beta_mf"].rolling(ROLL_WINDOW, min_periods=10).mean()
        beta_lf_20 = daily["beta_lf"].rolling(ROLL_WINDOW, min_periods=10).mean()
        freq_slope_20 = daily["freq_slope"].rolling(ROLL_WINDOW, min_periods=10).mean()
        coh_diff_20 = daily["coh_diff"].rolling(ROLL_WINDOW, min_periods=10).mean()

        out["BETA_HF_20"][sym] = beta_hf_20.reindex(dates)
        out["BETA_MF_20"][sym] = beta_mf_20.reindex(dates)
        out["BETA_LF_20"][sym] = beta_lf_20.reindex(dates)
        out["BETA_FREQ_SLOPE_20"][sym] = freq_slope_20.reindex(dates)
        out["COHERENCE_LF_HF_DIFF_20"][sym] = coh_diff_20.reindex(dates)
        out["BETA_HF_CHG_20"][sym] = (beta_hf_20 - beta_hf_20.shift(ROLL_WINDOW)).reindex(dates)
        out["BETA_LF_CHG_20"][sym] = (beta_lf_20 - beta_lf_20.shift(ROLL_WINDOW)).reindex(dates)
        out["BETA_FREQ_SLOPE_CHG_20"][sym] = (
            freq_slope_20 - freq_slope_20.shift(ROLL_WINDOW)
        ).reindex(dates)
    return out


register_family(
    FamilyProvider("frequency_domain_beta_1m", "frequency_domain_beta_1m", _build_frequency_domain_beta)
)
