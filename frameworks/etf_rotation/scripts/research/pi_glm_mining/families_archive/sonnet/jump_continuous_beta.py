"""Stage-19 family: jump_continuous_beta -- systematic risk decomposed
into continuous (diffusive) and jump components, directive 2026-09-20
round_519 (S4 stage, main controller, pre-specified direction).

Literature anchors:
- Todorov & Bollerslev (2010), "Jumps and Betas: A New Framework for
  Disentangling and Estimating Systematic Risk", Journal of Econometrics
  -- decomposes an asset's market beta into a continuous-component beta
  (from the diffusive part of the price process) and a jump-component
  beta (from co-jumps with the market), using high-frequency data.
- Bollerslev, Li & Todorov (2016), "Roughing Up Beta: Continuous vs.
  Discontinuous Betas and the Cross Section of Expected Stock Returns",
  Journal of Financial Economics -- jump beta and continuous beta earn
  different cross-sectional risk premia; the gap between them is
  informative on its own.

Implementation (practitioner proxy, consistent with this line's existing
1m-jump conventions in cojump_1m/realized_measures_1m): within each
trading day, a 1-minute bar is classified as a "jump bar" if either the
asset's or the market's (mean of 510300.SH/510500.SH) absolute return
exceeds 4.5x the PREVIOUS day's robust sigma (1.4826*median|r|, PIT-safe).
Continuous beta = covariation over non-jump bars / market variance over
non-jump bars; jump beta = covariation over jump bars / market variance
over jump bars (only on days with >=1 jump bar).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "CONTINUOUS_BETA_20",
    "CONTINUOUS_BETA_60",
    "JUMP_BETA_20",
    "BETA_GAP_20",
    "JUMP_BETA_STABILITY_20",
)

JUMP_THRESHOLD = 4.5
MIN_BARS_PER_DAY = 30


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


def _daily_beta_decomposition(data_root, sym, market_ret, frequency, as_of) -> pd.DataFrame:
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
    prev_asset: np.ndarray | None = None
    prev_mkt: np.ndarray | None = None
    for date, day in frame.groupby("date", sort=True):
        r_i = day["ret"].to_numpy(float)
        r_m = day["mkt_ret"].to_numpy(float)
        finite = np.isfinite(r_i) & np.isfinite(r_m)
        r_i, r_m = r_i[finite], r_m[finite]
        n = len(r_i)
        if n < MIN_BARS_PER_DAY:
            if n > 0:
                prev_asset, prev_mkt = r_i, r_m
            continue
        if prev_asset is None or len(prev_asset) < MIN_BARS_PER_DAY:
            prev_asset, prev_mkt = r_i, r_m
            continue
        sigma_i = 1.4826 * float(np.median(np.abs(prev_asset)))
        sigma_m = 1.4826 * float(np.median(np.abs(prev_mkt)))
        jump_mask = (np.abs(r_i) > JUMP_THRESHOLD * sigma_i) | (
            np.abs(r_m) > JUMP_THRESHOLD * sigma_m
        )
        cont_mask = ~jump_mask
        cont_var = float(np.sum(r_m[cont_mask] ** 2))
        cont_beta = float(np.sum(r_i[cont_mask] * r_m[cont_mask]) / cont_var) if cont_var > 0 else np.nan
        n_jump = int(jump_mask.sum())
        jump_var = float(np.sum(r_m[jump_mask] ** 2)) if n_jump else 0.0
        jump_beta = (
            float(np.sum(r_i[jump_mask] * r_m[jump_mask]) / jump_var)
            if (n_jump >= 1 and jump_var > 0)
            else np.nan
        )
        recs.append({"date": date, "cont_beta": cont_beta, "jump_beta": jump_beta})
        prev_asset, prev_mkt = r_i, r_m
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _build(panels, eligibility, data_root, config):
    frequency = str(config.get("frequency", "1m"))
    benchmark_symbols = list(config["benchmark_symbols"])
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    market_ret = _market_return_series(data_root, benchmark_symbols, frequency, as_of)
    if market_ret.empty:
        return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}

    for sym in symbols:
        daily = _daily_beta_decomposition(data_root, sym, market_ret, frequency, as_of)
        if daily.empty:
            continue
        cont_beta = daily["cont_beta"]
        jump_beta = daily["jump_beta"]
        cont_beta_20 = cont_beta.rolling(20, min_periods=12).mean()
        cont_beta_60 = cont_beta.rolling(60, min_periods=36).mean()
        jump_beta_20 = jump_beta.rolling(20, min_periods=5).mean()
        jump_beta_stability_20 = jump_beta.rolling(20, min_periods=5).std(ddof=1)
        beta_gap_20 = jump_beta_20 - cont_beta_20

        out["CONTINUOUS_BETA_20"][sym] = cont_beta_20.reindex(dates)
        out["CONTINUOUS_BETA_60"][sym] = cont_beta_60.reindex(dates)
        out["JUMP_BETA_20"][sym] = jump_beta_20.reindex(dates)
        out["BETA_GAP_20"][sym] = beta_gap_20.reindex(dates)
        out["JUMP_BETA_STABILITY_20"][sym] = jump_beta_stability_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("jump_continuous_beta", "jump_continuous_beta", _build))
