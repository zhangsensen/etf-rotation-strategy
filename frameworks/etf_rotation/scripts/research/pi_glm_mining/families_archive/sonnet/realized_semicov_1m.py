"""Stage-S8 family: realized_semicov_1m -- realized semicovariance
decomposition against the 14-ETF equal-weight basket, directive
2026-09-20 round_549 (S8 stage, main controller, pre-specified direction).

Literature anchors:
- Bollerslev, Li, Patton & Quaedvlieg (2020), "Realized Semicovariances",
  Econometrica -- decomposes the realized covariance between two assets
  into four components by the sign combination of their concurrent
  returns: both negative (N), both positive (P), and two "mixed" terms
  (asset up while market down, and asset down while market up). The N/P
  components carry most of the covariance risk premium in their finding;
  the mixed components are comparatively uninformative on their own but
  their net value captures directional decoupling.
- Ang, Chen & Xing (2006), "Downside Risk", Review of Financial Studies
  -- downside beta (covariation conditioned on market down-days) and
  upside beta (conditioned on market up-days) can differ meaningfully;
  the gap between them prices systematically.
- Patton & Sheppard (2015), "Good Volatility, Bad Volatility: Signed
  Jumps and the Persistence of Volatility", Review of Economics and
  Statistics -- motivates treating the sign-conditioned second moments
  (not just the unconditional beta) as separate, economically distinct
  quantities.

Implementation (practitioner proxy, consistent with this line's existing
1m conventions, reusing jump_continuous_beta.py's benchmark-basket
construction: the 1m return average of 510300.SH/510500.SH stands in for
the "14-ETF equal-weight basket"): within each trading day, for 1m
returns r_i (asset) and r_m (basket):
  N   = sum(r_i*r_m over bars where r_i<0 and r_m<0)
  P   = sum(r_i*r_m over bars where r_i>0 and r_m>0)
  Mix = sum(r_i*r_m over bars where sign(r_i) != sign(r_m))  [both mixed
        terms combined; BLPQ's M+ and M- are each individually negative
        in value since one factor is negative, so their sum is the net
        "directional decoupling" contribution]
  total = N + P + Mix  (the full realized covariance)
  downside_beta = sum(r_i*r_m over bars where r_m<0) / sum(r_m^2 over
    bars where r_m<0)   [Ang-Chen-Xing; conditions on market direction
    only, includes both N and the r_m<0 half of Mix]
  upside_beta   = sum(r_i*r_m over bars where r_m>0) / sum(r_m^2 over
    bars where r_m>0)
All daily statistics are rolled to a 20-day mean (or 20-day change for
two of them), never using same-day-or-later information beyond the day
itself.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "RCOV_N_SHARE_20",
    "RCOV_P_SHARE_20",
    "SEMICOV_DOWNSIDE_BETA_20",
    "SEMICOV_UPSIDE_BETA_20",
    "BETA_ASYM_20",
    "MIXED_NET_20",
    "RCOV_N_SHARE_CHG_20",
    "BETA_ASYM_CHG_20",
)

_BENCHMARK_SYMBOLS = ("510300.SH", "510500.SH")


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


def _daily_semicov_stats(r_i: np.ndarray, r_m: np.ndarray) -> dict:
    finite = np.isfinite(r_i) & np.isfinite(r_m)
    r_i, r_m = r_i[finite], r_m[finite]
    if len(r_i) < 10:
        return {}

    prod = r_i * r_m
    both_neg = (r_i < 0) & (r_m < 0)
    both_pos = (r_i > 0) & (r_m > 0)
    mixed = ~both_neg & ~both_pos & (r_i != 0) & (r_m != 0)

    n_comp = float(np.sum(prod[both_neg]))
    p_comp = float(np.sum(prod[both_pos]))
    mix_comp = float(np.sum(prod[mixed]))
    total_abs = abs(n_comp) + abs(p_comp) + abs(mix_comp)
    if total_abs <= 0:
        return {}

    down_mask = r_m < 0
    up_mask = r_m > 0
    down_var = float(np.sum(r_m[down_mask] ** 2))
    up_var = float(np.sum(r_m[up_mask] ** 2))
    downside_beta = float(np.sum(prod[down_mask]) / down_var) if down_var > 0 else np.nan
    upside_beta = float(np.sum(prod[up_mask]) / up_var) if up_var > 0 else np.nan

    return {
        "n_share": n_comp / total_abs,
        "p_share": p_comp / total_abs,
        "mixed_net_share": mix_comp / total_abs,
        "downside_beta": downside_beta,
        "upside_beta": upside_beta,
    }


def _daily_semicov_frame(data_root, sym, market_ret, as_of) -> pd.DataFrame:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
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
        stats = _daily_semicov_stats(day["ret"].to_numpy(float), day["mkt_ret"].to_numpy(float))
        if not stats:
            continue
        stats["date"] = date
        recs.append(stats)
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _build(panels, eligibility, data_root, config):
    frequency = str(config.get("frequency", "1m"))
    benchmark_symbols = list(config.get("benchmark_symbols", _BENCHMARK_SYMBOLS))
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    market_ret = _market_return_series(data_root, benchmark_symbols, frequency, as_of)
    if market_ret.empty:
        return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}

    for sym in symbols:
        daily = _daily_semicov_frame(data_root, sym, market_ret, as_of)
        if daily.empty:
            continue

        n_share_20 = daily["n_share"].rolling(20, min_periods=12).mean()
        p_share_20 = daily["p_share"].rolling(20, min_periods=12).mean()
        mixed_net_20 = daily["mixed_net_share"].rolling(20, min_periods=12).mean()
        downside_beta_20 = daily["downside_beta"].rolling(20, min_periods=12).mean()
        upside_beta_20 = daily["upside_beta"].rolling(20, min_periods=12).mean()
        beta_asym_20 = downside_beta_20 - upside_beta_20

        out["RCOV_N_SHARE_20"][sym] = n_share_20.reindex(dates)
        out["RCOV_P_SHARE_20"][sym] = p_share_20.reindex(dates)
        out["SEMICOV_DOWNSIDE_BETA_20"][sym] = downside_beta_20.reindex(dates)
        out["SEMICOV_UPSIDE_BETA_20"][sym] = upside_beta_20.reindex(dates)
        out["BETA_ASYM_20"][sym] = beta_asym_20.reindex(dates)
        out["MIXED_NET_20"][sym] = mixed_net_20.reindex(dates)
        out["RCOV_N_SHARE_CHG_20"][sym] = (n_share_20 - n_share_20.shift(20)).reindex(dates)
        out["BETA_ASYM_CHG_20"][sym] = (beta_asym_20 - beta_asym_20.shift(20)).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("realized_semicov_1m", "realized_semicov_1m", _build))
