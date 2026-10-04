"""Stage-16 family: upside_tail — lottery-demand / upside-tail mispricing,
directive 2026-09-20 round_504 (S2 stage, main controller).

Literature anchors (also recorded in family_upside_tail_v1.yaml):
- Bali, Cakici & Whitelaw (2011), "Maxing Out: Stocks as Lotteries and the
  Cross-Section of Expected Returns", Journal of Financial Economics — the
  MAX effect: assets with a high recent maximum daily return are overpriced
  by lottery-seeking demand and subsequently underperform.
- Barberis & Huang (2008), "Stocks as Lotteries: The Implications of
  Probability Weighting for Security Prices", American Economic Review —
  cumulative-prospect-theory investors overweight small probabilities of
  large gains, bidding up positively skewed/lottery-like assets.
- Kumar (2009), "Who Gambles in the Stock Market?", Journal of Finance —
  lottery-type assets (high idiosyncratic skewness, high volatility) are
  disproportionately demanded and subsequently mispriced.

return_tail_shape (daily_candle family group) already has the downside
counterpart (WORST_DAY_20/60); this family adds the symmetric upside side,
which was confirmed absent from all 62 pre-existing families in the
round_500 GAP_SCAN.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family, resolve_family

ATOM_NAMES = (
    "BEST_DAY_20",
    "BEST_DAY_60",
    "MAX5_MEAN_20",
    "TAIL_RATIO_20",
    "POS_DAY_FRAC_Z_20",
    "INTRADAY_MAXBAR_RET_20",
    "BEST_DAY_20_XVOL",
    "BEST_DAY_60_XVOL",
    "MAX5_MEAN_20_XVOL",
    "INTRADAY_MAXBAR_RET_20_XVOL",
)


def _safe_div(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    return left.div(right.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)


def _max5_mean(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if len(finite) < 5:
        return np.nan
    return float(np.sort(finite)[-5:].mean())


def _daily_atoms(close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    daily_return = close.pct_change(fill_method=None)
    factors: dict[str, pd.DataFrame] = {}
    factors["BEST_DAY_20"] = daily_return.rolling(20, min_periods=20).max()
    factors["BEST_DAY_60"] = daily_return.rolling(60, min_periods=60).max()
    factors["MAX5_MEAN_20"] = daily_return.rolling(20, min_periods=20).apply(
        _max5_mean, raw=True
    )
    worst_day_20 = daily_return.rolling(20, min_periods=20).min()
    factors["TAIL_RATIO_20"] = _safe_div(factors["BEST_DAY_20"], worst_day_20.abs())
    pos_frac_20 = daily_return.gt(0.0).rolling(20, min_periods=20).mean()
    baseline_mean = pos_frac_20.rolling(120, min_periods=60).mean()
    baseline_std = pos_frac_20.rolling(120, min_periods=60).std(ddof=1)
    factors["POS_DAY_FRAC_Z_20"] = _safe_div(pos_frac_20 - baseline_mean, baseline_std)
    return factors


def _cross_sectional_residual(y: pd.DataFrame, x: pd.DataFrame, min_pairs: int = 8) -> pd.DataFrame:
    """Fama-MacBeth-style cross-sectional residual of y on x, date by date
    (round_505 directive: orthogonalize the MAX-effect atoms against
    REALIZED_VOL_60 so the surviving signal is not just volatility level in
    disguise; round_504 atom_health traced 3/4 shadow flags to exactly this
    shelf factor)."""
    x_aligned = x.reindex_like(y)
    y_vals = y.to_numpy(float)
    x_vals = x_aligned.to_numpy(float)
    out = np.full(y_vals.shape, np.nan)
    for i in range(y_vals.shape[0]):
        yr, xr = y_vals[i], x_vals[i]
        mask = np.isfinite(yr) & np.isfinite(xr)
        if mask.sum() < min_pairs:
            continue
        xs, ys = xr[mask], yr[mask]
        xm, ym = xs.mean(), ys.mean()
        xd = xs - xm
        denom = float(np.sum(xd ** 2))
        if denom <= 0:
            continue
        b = float(np.sum(xd * (ys - ym)) / denom)
        a = ym - b * xm
        row = np.full(y_vals.shape[1], np.nan)
        row[mask] = ys - (a + b * xs)
        out[i] = row
    return pd.DataFrame(out, index=y.index, columns=y.columns)


def _intraday_maxbar_atom(data_root, symbols, frequency, as_of, dates) -> pd.DataFrame:
    out = pd.DataFrame(np.nan, index=dates, columns=symbols)
    for sym in symbols:
        try:
            frame, _ = _read_complete_days(data_root, sym, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        frame = frame.copy()
        frame["date"] = frame["datetime"].dt.normalize()
        recs = []
        for date, day in frame.groupby("date", sort=True):
            close = day["close"].to_numpy(float)
            if len(close) < 30:
                continue
            ret = close[1:] / np.where(close[:-1] > 0, close[:-1], np.nan) - 1.0
            ret = ret[np.isfinite(ret)]
            if not len(ret):
                continue
            recs.append({"date": date, "max_bar_ret": float(np.max(ret))})
        if not recs:
            continue
        daily = pd.DataFrame(recs).set_index("date")["max_bar_ret"]
        out[sym] = daily.rolling(20, min_periods=12).mean().reindex(dates)
    return out


def _build(panels, eligibility, data_root, config):
    close = panels["close"].astype(float)
    factors = _daily_atoms(close)
    frequency = str(config.get("frequency", "1m"))
    dates = close.index
    symbols = list(close.columns)
    as_of = dates.max()
    factors["INTRADAY_MAXBAR_RET_20"] = _intraday_maxbar_atom(
        data_root, symbols, frequency, as_of, dates
    )
    downside_space = resolve_family("downside_risk").builder(panels, eligibility, data_root, {})
    realized_vol_60 = downside_space["REALIZED_VOL_60"]
    for base_name in (
        "BEST_DAY_20",
        "BEST_DAY_60",
        "MAX5_MEAN_20",
        "INTRADAY_MAXBAR_RET_20",
    ):
        factors[f"{base_name}_XVOL"] = _cross_sectional_residual(
            factors[base_name], realized_vol_60
        )
    return {name: frame.where(np.isfinite(frame)) for name, frame in factors.items()}


register_family(FamilyProvider("upside_tail", "upside_tail", _build))
