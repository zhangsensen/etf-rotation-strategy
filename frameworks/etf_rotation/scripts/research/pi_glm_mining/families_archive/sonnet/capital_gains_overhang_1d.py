"""Stage-S63 family (round_670, main controller directive): capital-gains
overhang (CGO), the literature-original disposition-effect mechanism,
implemented in its 1d/volume-weighted-reference-price form -- distinct
from this line's price-path-only drawdown/underwater atoms (DD48, CR08,
UE3, CK04), which never weight by holding-period turnover.

Literature anchors:
- Grinblatt & Han (2005), "Prospect theory, mental accounting, and
  momentum" -- eq. (1)-(3): reference price RP_t = sum_n w_n P_{t-n},
  w_n proportional to turnover_{t-n} times the probability the shares
  bought at t-n were never turned over since (survival weight); CGO_t =
  (P_t - RP_t) / RP_t.
- Frazzini (2006), "The disposition effect and underreaction to news" --
  CGO as a proxy for the unrealized-gain overhang driving reluctance to
  sell losers / eagerness to sell winners.
- Wang, Yan & Yu (2017), "Reference prices and cryptocurrency" and An
  (2016), "Asset pricing when traders sell extreme winners and losers" --
  V-shaped disposition: separately signed gain-overhang and loss-overhang
  legs carry independent information beyond the net CGO.

Turnover proxy: V_t / Vbar_t, Vbar_t = trailing 60-day mean volume
(matches the directive's "滚动60日均量作换手率代理"); clipped to [0, 0.99]
purely as a numerical safeguard so (1 - turnover) never goes negative --
this is not an economic threshold on the signal, the same class of
numerical clip already used elsewhere in this line (e.g.
GAP_DD_CONSUMPTION_RATIO's [0,3] clip).

Atoms (all rolling, no economic threshold, 1d-only, no 1m read):
  CGO_60 / CGO_120 / CGO_250: (close - RP_N) / RP_N for N in {60,120,250}.
  GAIN_OVERHANG_60: turnover-weighted average of max(close - P_{t-n}, 0)/close
    over the N=60 reference window (An 2016 positive leg).
  LOSS_OVERHANG_60: turnover-weighted average of max(P_{t-n} - close, 0)/close
    over the same N=60 window (negative leg).
  RP_CHANGE_20: 20-day rate of change of the N=60 reference price itself
    -- the slow-signal candidate the directive asks to track at H=20.

LOSS_VOL_SHARE_N (volume-weighted fraction of the reference window at a
loss) was in the directive's idea list but dropped to stay within the
<=6-atom cap; GAIN_OVERHANG_60/LOSS_OVERHANG_60 already capture the same
V-shaped-disposition information from the positive/negative split.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "CGO_60",
    "CGO_120",
    "CGO_250",
    "GAIN_OVERHANG_60",
    "LOSS_OVERHANG_60",
    "RP_CHANGE_20",
)

_VBAR_WINDOW = 60
_VBAR_MIN_PERIODS = 30
_TURNOVER_CLIP = 0.99
_RP_CHANGE_LAG = 20


def _cgo_stats(price: np.ndarray, turnover: np.ndarray, n_window: int):
    """Vectorized Grinblatt-Han reference price + gain/loss overhang for
    one window length. Returns three arrays (RP, gain_overhang,
    loss_overhang), each length T, NaN for the first n_window days."""
    length = len(price)
    out_rp = np.full(length, np.nan)
    out_gain = np.full(length, np.nan)
    out_loss = np.full(length, np.nan)
    if length <= n_window:
        return out_rp, out_gain, out_loss

    turnover_c = np.clip(turnover, 0.0, _TURNOVER_CLIP)
    n_valid = length - n_window
    a = np.empty((n_valid, n_window))
    p = np.empty((n_valid, n_window))
    for i in range(n_window):
        a[:, i] = turnover_c[n_window - 1 - i : length - 1 - i]
        p[:, i] = price[n_window - 1 - i : length - 1 - i]

    b = 1.0 - a
    cumprod_b = np.cumprod(b, axis=1)
    weight = np.empty_like(a)
    weight[:, 0] = a[:, 0]
    weight[:, 1:] = a[:, 1:] * cumprod_b[:, :-1]
    wsum = weight.sum(axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        w = weight / wsum
    w = np.where(np.isfinite(w), w, np.nan)

    rp_valid = np.nansum(w * p, axis=1)
    cur_price = price[n_window:]
    diff = cur_price[:, None] - p
    gain = np.where(diff > 0, diff, 0.0)
    loss = np.where(diff < 0, -diff, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        gain_overhang = np.nansum(w * gain, axis=1) / cur_price
        loss_overhang = np.nansum(w * loss, axis=1) / cur_price

    out_rp[n_window:] = rp_valid
    out_gain[n_window:] = gain_overhang
    out_loss[n_window:] = loss_overhang
    return out_rp, out_gain, out_loss


def _build(panels, eligibility, data_root, config):
    del eligibility, data_root, config
    close = panels["close"]
    volume = panels["volume"]
    dates = close.index
    symbols = list(close.columns)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    vbar = volume.rolling(_VBAR_WINDOW, min_periods=_VBAR_MIN_PERIODS).mean()
    turnover_panel = (volume / vbar.replace(0, np.nan)).clip(lower=0.0)

    rp60_by_sym: dict[str, pd.Series] = {}
    for sym in symbols:
        price = close[sym].to_numpy(float)
        turnover = turnover_panel[sym].to_numpy(float)
        valid = np.isfinite(price) & np.isfinite(turnover)
        if valid.sum() < _VBAR_WINDOW + 30:
            continue
        price_filled = np.where(np.isfinite(price), price, np.nan)
        turnover_filled = np.where(np.isfinite(turnover), turnover, 0.0)

        for n_window, cgo_name, gain_name, loss_name in (
            (60, "CGO_60", "GAIN_OVERHANG_60", "LOSS_OVERHANG_60"),
            (120, "CGO_120", None, None),
            (250, "CGO_250", None, None),
        ):
            rp, gain, loss = _cgo_stats(price_filled, turnover_filled, n_window)
            rp_series = pd.Series(rp, index=dates)
            cgo = (close[sym] - rp_series) / rp_series.replace(0, np.nan)
            out[cgo_name][sym] = cgo.reindex(dates)
            if gain_name is not None:
                out[gain_name][sym] = pd.Series(gain, index=dates).reindex(dates)
                out[loss_name][sym] = pd.Series(loss, index=dates).reindex(dates)
            if n_window == 60:
                rp60_by_sym[sym] = rp_series

    for sym, rp60 in rp60_by_sym.items():
        out["RP_CHANGE_20"][sym] = (
            (rp60 - rp60.shift(_RP_CHANGE_LAG)) / rp60.shift(_RP_CHANGE_LAG).replace(0, np.nan)
        ).reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("capital_gains_overhang_1d", "capital_gains_overhang_1d", _build))
