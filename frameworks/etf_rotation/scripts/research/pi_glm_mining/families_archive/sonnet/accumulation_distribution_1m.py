"""Stage-S10 family: accumulation_distribution_1m -- close-location-value
weighted volume flow (accumulation/distribution), directive 2026-09-20
round_536 (S10 stage, main controller, pre-specified direction).

Literature anchors:
- Chaikin (1966/1982), Close Location Value (CLV) and the Accumulation/
  Distribution Line -- CLV = ((C-L)-(H-C))/(H-L), volume-weighted per bar,
  accumulated to gauge whether volume is concentrated on up-closes
  (accumulation) or down-closes (distribution) within the bar's range.
- Granville (1963), On Balance Volume (OBV) -- cumulative signed volume
  (added on up-closes, subtracted on down-closes), whose slope proxies
  buying/selling pressure independent of price level.
- Quong & Soudack (1989), Money Flow Index (MFI) -- a volume-weighted RSI
  analogue using typical price (H+L+C)/3, flagging overbought/oversold
  volume-flow extremes.
- Blume, Easley & O'Hara (1994), "Market Statistics and Technical
  Analysis: The Role of Volume", JF -- volume conveys information about
  the quality/conviction of a price move, motivating a direct
  flow-vs-return lead-lag check (AD_PRICE_CORR_20).

Implementation (practitioner proxy, consistent with this line's existing
1m conventions): within each trading day, using 1m OHLCV bars:
  CLV_bar = ((C-L)-(H-C))/(H-L), 0 if H==L
  daily_net_flow_pct = sum(CLV_bar * volume_bar) / sum(volume_bar)
  OBV_bar = +volume if close > prev close, -volume if close < prev close,
    0 otherwise (first bar of day contributes 0, matching this line's
    convention of using within-day-only bar sequences for these flow
    measures); cumulative OBV within the day, OBV slope = OLS slope of
    cumulative OBV against bar index, normalized by the day's total
    volume (so it is comparable in scale across symbols/days).
  MFI: typical price TP=(H+L+C)/3, raw money flow = TP*volume, positive
    if TP > previous-bar TP else negative; MFI(bar) = 100 - 100/(1 +
    trailing-14-bar positive-flow-sum / trailing-14-bar negative-flow-sum)
    computed within the day (bars before the 14th use whatever history is
    available that day); MFI_14_MEAN_20 uses the day's mean MFI.
All daily statistics are rolled to a 20-day mean (or 20-day slope/change
for four of them), never using same-day-or-later information beyond the
day itself.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "AD_NET_FLOW_20",
    "AD_NET_FLOW_SLOPE_20",
    "AD_NET_FLOW_CHG_20",
    "OBV_SLOPE_20",
    "OBV_SLOPE_CHG_20",
    "MFI_14_MEAN_20",
    "MFI_EXTREME_FRAC_20",
    "AD_PRICE_CORR_20",
)

_MFI_WINDOW = 14


def _daily_bar(frame: pd.DataFrame) -> dict:
    high = frame["high"].to_numpy(float)
    low = frame["low"].to_numpy(float)
    close = frame["close"].to_numpy(float)
    volume = frame["volume"].to_numpy(float)
    n = len(close)
    if n < 5:
        return {}

    hl_range = high - low
    clv = np.where(hl_range > 0, ((close - low) - (high - close)) / np.where(hl_range > 0, hl_range, 1.0), 0.0)
    total_vol = float(volume.sum())
    if total_vol <= 0:
        return {}
    net_flow_pct = float(np.sum(clv * volume) / total_vol)

    close_diff = np.diff(close)
    signed_vol = np.zeros(n)
    signed_vol[1:] = np.where(close_diff > 0, volume[1:], np.where(close_diff < 0, -volume[1:], 0.0))
    obv = np.cumsum(signed_vol)
    bar_idx = np.arange(n, dtype=float)
    obv_slope_raw = float(np.polyfit(bar_idx, obv, 1)[0])
    obv_slope = obv_slope_raw / total_vol

    typical = (high + low + close) / 3.0
    tp_diff = np.diff(typical)
    raw_flow = typical * volume
    pos_flow = np.zeros(n)
    neg_flow = np.zeros(n)
    pos_flow[1:] = np.where(tp_diff > 0, raw_flow[1:], 0.0)
    neg_flow[1:] = np.where(tp_diff < 0, raw_flow[1:], 0.0)
    mfi_vals = []
    for i in range(n):
        start = max(0, i - _MFI_WINDOW + 1)
        pos_sum = pos_flow[start : i + 1].sum()
        neg_sum = neg_flow[start : i + 1].sum()
        if neg_sum <= 0:
            mfi_vals.append(100.0 if pos_sum > 0 else 50.0)
            continue
        ratio = pos_sum / neg_sum
        mfi_vals.append(100.0 - 100.0 / (1.0 + ratio))
    mfi_arr = np.array(mfi_vals)
    mfi_mean = float(np.mean(mfi_arr))
    extreme_frac = float(np.mean((mfi_arr > 80.0) | (mfi_arr < 20.0)))

    return {
        "net_flow_pct": net_flow_pct,
        "obv_slope": obv_slope,
        "mfi_mean": mfi_mean,
        "extreme_frac": extreme_frac,
    }


def _daily_ad_frame(data_root, sym, as_of) -> pd.DataFrame:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if frame.empty:
        return pd.DataFrame()
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()

    recs = []
    for date, day in frame.groupby("date", sort=True):
        stats = _daily_bar(day)
        if not stats:
            continue
        stats["date"] = date
        recs.append(stats)
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs).set_index("date")


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}
    daily_close = panels["close"]

    for sym in symbols:
        daily = _daily_ad_frame(data_root, sym, as_of)
        if daily.empty:
            continue

        net_flow_20 = daily["net_flow_pct"].rolling(20, min_periods=12).mean()
        obv_slope_20 = daily["obv_slope"].rolling(20, min_periods=12).mean()
        mfi_mean_20 = daily["mfi_mean"].rolling(20, min_periods=12).mean()
        extreme_frac_20 = daily["extreme_frac"].rolling(20, min_periods=12).mean()

        bar_idx = np.arange(len(net_flow_20), dtype=float)
        net_flow_slope_20 = (
            net_flow_20.rolling(20, min_periods=12).apply(
                lambda s: np.polyfit(np.arange(len(s)), s, 1)[0] if np.isfinite(s).all() else np.nan,
                raw=True,
            )
        )

        ret = daily_close[sym].reindex(daily.index).pct_change()
        ad_price_corr_20 = daily["net_flow_pct"].rolling(20, min_periods=12).corr(ret)

        out["AD_NET_FLOW_20"][sym] = net_flow_20.reindex(dates)
        out["AD_NET_FLOW_SLOPE_20"][sym] = net_flow_slope_20.reindex(dates)
        out["AD_NET_FLOW_CHG_20"][sym] = (net_flow_20 - net_flow_20.shift(20)).reindex(dates)
        out["OBV_SLOPE_20"][sym] = obv_slope_20.reindex(dates)
        out["OBV_SLOPE_CHG_20"][sym] = (obv_slope_20 - obv_slope_20.shift(20)).reindex(dates)
        out["MFI_14_MEAN_20"][sym] = mfi_mean_20.reindex(dates)
        out["MFI_EXTREME_FRAC_20"][sym] = extreme_frac_20.reindex(dates)
        out["AD_PRICE_CORR_20"][sym] = ad_price_corr_20.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("accumulation_distribution_1m", "accumulation_distribution_1m", _build))
