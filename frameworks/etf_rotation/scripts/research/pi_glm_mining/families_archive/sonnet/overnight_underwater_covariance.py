"""S48 stage (round_649, main controller directive, 2026-09-21):
overnight behavior vs intraday drawdown, written directly as a rolling
covariation statistic rather than a rank_spread pairing of two 20d-
smoothed atoms. S45's CZ01/CY07 showed overnight premium and big-bar
edge concentration carry no information alone -- the pairing is where
the signal lives; UE3/HB1/S42P10 are all variants of "overnight x
underwater". This family writes that relationship as a single rolling
correlation, at the RAW (not 20d-pre-smoothed) day level where the
directive's wording calls for "当日水下占比" (today's own underwater
fraction, not a 20d average of it).

Reuses `_daily_drawdown_frame` (module-level helper in
intraday_drawdown_1m.py, S7) directly for the raw daily underwater
fraction and max intraday drawdown series -- one 1m pass per symbol,
same cost class as that family's own build (no re-smoothing overhead
since the 20d rolling means computed by intraday_drawdown_1m._build are
not needed here). YZ_OVERNIGHT_SHARE_20 (Yang-Zhang overnight variance
share, S9) is reused via resolve_family() since it is inherently a
20-day rolling-variance ratio (no raw single-day version exists).
Overnight return and its 20d realized-vol denominator come from the
daily close/open panels (no 1m cost).

Atoms (only "strongest 2" per directive get a CHG_20 companion; picked
as OVERNIGHT_UNDERWATER_SPEARMAN_20 and OVERNIGHT_VARSHARE_UNDERWATER_CORR_60,
the two most directly tied to the already-established UE3/HB1
overnight-variance-share x underwater-drawdown channel):
  OVERNIGHT_UNDERWATER_SPEARMAN_20: 20d rolling Spearman correlation
    between the day's overnight return (open_t/close_{t-1} - 1) and the
    day's own raw intraday underwater fraction.
  OVERNIGHT_SIGN_UNDERWATERCHG_CORR_20: 20d rolling Pearson correlation
    between sign(overnight return) and the day-over-day change in raw
    underwater fraction.
  OVERNIGHT_VARSHARE_UNDERWATER_CORR_60: 60d rolling Pearson correlation
    between YZ_OVERNIGHT_SHARE_20 and the raw underwater fraction.
  GAP_SIGMA_MAXDD_SIGMA_CORR_20: 20d rolling Pearson correlation between
    |overnight return|/sigma20 (sigma20 = 20d rolling std of daily
    simple returns) and the day's raw max intraday drawdown / sigma20.
  OVERNIGHT_UNDERWATER_SPEARMAN_CHG_20 = 20d change of the first atom.
  OVERNIGHT_VARSHARE_UNDERWATER_CORR_CHG_20 = 20d change of the third
    atom."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .intraday_drawdown_1m import _daily_drawdown_frame
from ..family_provider import FamilyProvider
from ..family_registry import register_family, resolve_family

ATOM_NAMES = (
    "OVERNIGHT_UNDERWATER_SPEARMAN_20",
    "OVERNIGHT_SIGN_UNDERWATERCHG_CORR_20",
    "OVERNIGHT_VARSHARE_UNDERWATER_CORR_60",
    "GAP_SIGMA_MAXDD_SIGMA_CORR_20",
    "OVERNIGHT_UNDERWATER_SPEARMAN_CHG_20",
    "OVERNIGHT_VARSHARE_UNDERWATER_CORR_CHG_20",
)

_ROLL20 = 20
_ROLL60 = 60
_DUMMY_CONFIG = {"frequency": "1m"}


def _rolling_pearson(a: pd.Series, b: pd.Series, window: int, min_frac: float = 0.6) -> pd.Series:
    df = pd.concat({"a": a, "b": b}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    min_periods = max(5, int(window * min_frac))
    out = pd.Series(np.nan, index=df.index)
    av = df["a"].to_numpy(float)
    bv = df["b"].to_numpy(float)
    n = len(df)
    for i in range(min_periods - 1, n):
        start = max(0, i - window + 1)
        aw = av[start : i + 1]
        bw = bv[start : i + 1]
        if len(aw) < min_periods or np.std(aw) <= 0 or np.std(bw) <= 0:
            continue
        out.iloc[i] = float(np.corrcoef(aw, bw)[0, 1])
    return out


def _rolling_spearman(a: pd.Series, b: pd.Series, window: int, min_frac: float = 0.6) -> pd.Series:
    df = pd.concat({"a": a, "b": b}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    ra = df["a"].rank()
    rb = df["b"].rank()
    return _rolling_pearson(ra, rb, window, min_frac)


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    open_p = panels["open"]
    close_p = panels["close"]
    prev_close = close_p.shift(1)
    overnight_ret = (open_p / prev_close.where(prev_close > 0) - 1.0)
    daily_ret = close_p.pct_change()
    sigma20 = daily_ret.rolling(_ROLL20, min_periods=15).std()

    rbv_space = resolve_family("range_based_vol_1m").builder(panels, eligibility, data_root, _DUMMY_CONFIG)
    yz_overnight_share = rbv_space["YZ_OVERNIGHT_SHARE_20"]

    for sym in symbols:
        dd = _daily_drawdown_frame(data_root, sym, as_of)
        if dd.empty:
            continue
        underwater_raw = dd["underwater_frac"].reindex(dates)
        max_dd_raw = dd["max_dd"].reindex(dates)

        on_ret = overnight_ret[sym]
        sig = sigma20[sym]

        atom1 = _rolling_spearman(on_ret, underwater_raw, _ROLL20)
        out["OVERNIGHT_UNDERWATER_SPEARMAN_20"][sym] = atom1.reindex(dates)
        out["OVERNIGHT_UNDERWATER_SPEARMAN_CHG_20"][sym] = (
            atom1.reindex(dates) - atom1.reindex(dates).shift(_ROLL20)
        )

        underwater_chg = underwater_raw.diff()
        on_sign = np.sign(on_ret)
        atom2 = _rolling_pearson(on_sign, underwater_chg, _ROLL20)
        out["OVERNIGHT_SIGN_UNDERWATERCHG_CORR_20"][sym] = atom2.reindex(dates)

        atom3 = _rolling_pearson(yz_overnight_share[sym], underwater_raw, _ROLL60)
        out["OVERNIGHT_VARSHARE_UNDERWATER_CORR_60"][sym] = atom3.reindex(dates)
        out["OVERNIGHT_VARSHARE_UNDERWATER_CORR_CHG_20"][sym] = (
            atom3.reindex(dates) - atom3.reindex(dates).shift(_ROLL20)
        )

        gap_sigma = (on_ret.abs() / sig.where(sig > 0))
        maxdd_sigma = (max_dd_raw / sig.where(sig > 0))
        atom4 = _rolling_pearson(gap_sigma, maxdd_sigma, _ROLL20)
        out["GAP_SIGMA_MAXDD_SIGMA_CORR_20"][sym] = atom4.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("overnight_underwater_covariance", "overnight_underwater_covariance", _build))
