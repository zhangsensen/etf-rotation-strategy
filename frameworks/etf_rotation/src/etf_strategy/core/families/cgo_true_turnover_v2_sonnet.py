"""Stage-S66 family (round_678, main controller directive, 2026-09-21):
capital-gains overhang (CGO) 1d version, E30-corrected -- S63's original
implementation used the directive-specified turnover proxy V_t/Vbar_t
(Vbar_t = trailing 60d mean volume), which centers at ~1.0 and collapses
the Grinblatt-Han reference price to ~lag-1 close, making CGO_60/
GAIN_OVERHANG_60/LOSS_OVERHANG_60 a disguised same-day-return signal
(rank corr vs ret1 0.87-0.99, vs max(-ret1,0) 0.72-0.92 per the
controller's own recompute). All 5 of S63's admissions are voided
(DEGENERATE_RET1_SHADOW) and excluded from the forward ledger.

This family keeps S63's exact math (Grinblatt & Han 2005 eq.1-3,
survival-weighted reference price; An 2016 magnitude-weighted gain/loss
split) but replaces the turnover input with REAL PIT turnover, TO_t =
daily volume_t / PIT fund shares outstanding (fund_share/<sym>.parquet
'fund_shares', aligned by usable_from_date so only shares-outstanding
known as of <=D are used) -- reusing the same `_pit_fund_shares` helper
and `_cgo_stats` survival-weight recursion already built and verified in
`cost_distribution_1m_sonnet.py` / `capital_gains_overhang_1d.py`
(no average-volume proxy, no threshold).

Atoms (<=6 cap):
  CGO_60, CGO_250: (close - RP_N)/RP_N, N in {60, 250}.
  GAIN_OVERHANG_60 / LOSS_OVERHANG_60: An 2016 magnitude-weighted
    max(+-(close-P),0)/close split of the N=60 reference window.
  UW_SHARE_250: survival-weight share of the N=250 window sitting at a
    price above close_D (holders at an unrealized loss).
  RP_CHANGE_20: 20-day rate of change of RP_60 (slow-signal candidate).
GAIN_OVERHANG_250/LOSS_OVERHANG_250 and CGO_120 were dropped to stay
within the 6-atom cap (magnitude-weighted gain/loss legs are NOT simple
complements of each other under this construction -- both retained at
N=60 -- but the N=250 variants were not built this round)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .cgo_math import cgo_stats
from .cost_distribution_1m_sonnet import _pit_fund_shares
from ..family_provider import FamilyProvider
from ..family_registry import register_family

ATOM_NAMES = (
    "CGO_V2_60",
    "CGO_V2_250",
    "GAIN_OVERHANG_V2_60",
    "LOSS_OVERHANG_V2_60",
    "UW_SHARE_V2_250",
    "RP_CHANGE_V2_20",
)

_TURNOVER_CLIP = 0.99
_RP_CHANGE_LAG = 20


def _build(panels, eligibility, data_root, config):
    del eligibility, config
    close = panels["close"]
    volume = panels["volume"]
    dates = close.index
    symbols = list(close.columns)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    for sym in symbols:
        fund_shares = _pit_fund_shares(data_root, sym, dates)
        turnover = (volume[sym] / fund_shares.replace(0, np.nan)).to_numpy(float)
        turnover = np.where(np.isfinite(turnover) & (turnover >= 0), turnover, 0.0)
        turnover_c = np.clip(turnover, 0.0, _TURNOVER_CLIP)

        price = close[sym].to_numpy(float)
        if len(price) <= 260 or not np.isfinite(price).any():
            continue

        rp60, gain60, loss60 = cgo_stats(price, turnover_c, 60)
        rp250, _, _ = cgo_stats(price, turnover_c, 250)

        rp60_s = pd.Series(rp60, index=dates)
        rp250_s = pd.Series(rp250, index=dates)
        cgo60 = (close[sym] - rp60_s) / rp60_s.replace(0, np.nan)
        cgo250 = (close[sym] - rp250_s) / rp250_s.replace(0, np.nan)
        out["CGO_V2_60"][sym] = cgo60
        out["CGO_V2_250"][sym] = cgo250
        out["GAIN_OVERHANG_V2_60"][sym] = pd.Series(gain60, index=dates)
        out["LOSS_OVERHANG_V2_60"][sym] = pd.Series(loss60, index=dates)
        out["RP_CHANGE_V2_20"][sym] = (
            (rp60_s - rp60_s.shift(_RP_CHANGE_LAG)) / rp60_s.shift(_RP_CHANGE_LAG).replace(0, np.nan)
        )

        # UW_SHARE_250: survival-weight share of the N=250 window priced
        # above close_D, recomputed directly (needs per-day weight arrays,
        # not exposed by _cgo_stats' return signature).
        length = len(price)
        n_window = 250
        n_valid = length - n_window
        if n_valid > 0:
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
            w = np.where(np.isfinite(w), w, 0.0)
            cur_price = price[n_window:]
            uw_share = (w * (p > cur_price[:, None])).sum(axis=1)
            col = np.full(length, np.nan)
            col[n_window:] = uw_share
            out["UW_SHARE_V2_250"][sym] = pd.Series(col, index=dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("cgo_true_turnover_v2_sonnet", "cgo_true_turnover_v2_sonnet", _build))
