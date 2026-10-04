"""S47 stage (round_647, main controller directive, 2026-09-21): fifth
batch of mechanism atoms. Source = the head of S44's REJECTED_H20_PROFILE
list (candidates rejected by the H=5 topk_gate but two-window
significant at H=20, independent of already-admitted clusters, both
legs volume-free): PH1 (CEP_DISTANCE_20 x CLOSE5_DAY_CONSIST_20,
round_543, H20 discovery t=4.15/audit t=4.83), BA7 (BB_WIDTH_CHG_20 x
SAMPEN_RET_20, round_584, H20 discovery t=3.19/audit t=4.70), S30Q5
(YZ_OVERNIGHT_SHARE_20 x PM_POSTRUN_DAY_CONSIST_20, round_628, H20
discovery t=2.50/audit t=4.34).

Same mechanism-atom recipe as S27/S29/S30: replace a rank_spread pairing
of two full atoms with a single conditional statistic -- split one leg's
host days by the OTHER leg's day-level state, and report the difference
in the FIRST leg's underlying series between the two states. Directive
targets a signal that also stands up under the *current* H=5 gate (S44's
whole point was these three failed H=5), so the split target here is
always the higher-frequency, less-smoothed underlying series, not the
already-20d-smoothed rank_spread output.

Atoms (only "strongest 2" per H20 audit-t get a CHG_20 companion, per
directive -- PH1 audit_t=4.83 and BA7 audit_t=4.70, both ahead of
S30Q5's 4.34):
  CLOSE5_CONSIST_PERMENT_SPLIT_20 (from PH1): rolling-40d window, split
    days by whether the day's last-5-minute return sign matches the
    day's close-to-close return sign (the day-level boolean underlying
    CLOSE5_DAY_CONSIST_20, recomputed here at daily granularity rather
    than reusing the pre-smoothed 20d atom), mean(PERM_ENTROPY_RET_20 |
    consistent days) - mean(... | inconsistent days).
  BBWIDTH_CHG_SAMPEN_SPLIT_20 (from BA7): rolling-40d window, split days
    by sign of BB_WIDTH_CHG_20 (bandwidth contracting vs expanding),
    mean(SAMPEN_RET_20 | contracting) - mean(... | expanding).
  OVERNIGHT_SHARE_PMCONSIST_SPLIT_20 (from S30Q5): rolling-40d window,
    split days by median of YZ_OVERNIGHT_SHARE_20 (high vs low overnight
    variance share), mean(PM_POSTRUN_DAY_CONSIST_20 | high) - mean(... |
    low); both legs reused from range_based_vol_1m and S30's
    mechanism_atoms_v3 rather than rebuilt.
  CLOSE5_CONSIST_PERMENT_SPLIT_CHG_20 = 20d change of the first atom.
  BBWIDTH_CHG_SAMPEN_SPLIT_CHG_20 = 20d change of the second atom.

Reuses PERM_ENTROPY_RET_20 (permutation_entropy_1m), BB_WIDTH_CHG_20
(range_contraction_cycle), SAMPEN_RET_20 (complexity_measures_1m),
YZ_OVERNIGHT_SHARE_20 (range_based_vol_1m) via resolve_family().

PM_POSTRUN_DAY_CONSIST_20 is recomputed HERE locally from
lunch_break_1m:LUNCH_POST_RUN_20 (S30's exact formula: 20d-rolling-mean
deviation of LUNCH_POST_RUN_20, sign-matched against daily close-to-
close return, 20d mean of the match indicator) rather than resolving
S30's mechanism_atoms_v3 family -- a 3-symbol timing probe showed
mechanism_atoms_v3.builder() costs 28s (it internally re-resolves 5
unrelated families: volume_time_1m, pi_lunch_prerun_1m, lunch_break_1m,
pi_repl_s28, pi_pv_elasticity_1m, just to expose one atom this module
needs) versus 8s for lunch_break_1m alone -- pulling in only the
needed dependency cuts the dominant redundant-recompute cost by ~70%
for this one leg, consistent with the standing efficiency directive
(S29/S30) of not re-deriving expensive 1m statistics, extended here to
also avoid re-deriving statistics that aren't even needed. The two
genuinely expensive entropy families (permutation_entropy_1m 7.4s,
complexity_measures_1m 37s at 3-symbol scale) have no cheaper path --
SampEn/ApEn-style day loops are the atoms themselves, not a
byproduct of something larger. Only new 1m computation from scratch is
the single-pass day-groupby close5_ret extraction (cheap, same pattern
as mechanism_atoms_v3's _daily_bar_v3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family, resolve_family

ATOM_NAMES = (
    "CLOSE5_CONSIST_PERMENT_SPLIT_20",
    "BBWIDTH_CHG_SAMPEN_SPLIT_20",
    "OVERNIGHT_SHARE_PMCONSIST_SPLIT_20",
    "CLOSE5_CONSIST_PERMENT_SPLIT_CHG_20",
    "BBWIDTH_CHG_SAMPEN_SPLIT_CHG_20",
)

_SPLIT_WINDOW = 40
_ROLL = 20
_DUMMY_CONFIG = {"frequency": "1m"}


def _resolved(source: str, panels, eligibility, data_root) -> dict:
    return resolve_family(source).builder(panels, eligibility, data_root, _DUMMY_CONFIG)


def _daily_close5_ret(data_root, sym, as_of, dates) -> pd.Series:
    try:
        frame, _ = _read_complete_days(data_root, sym, "1m", as_of)
    except Exception:  # noqa: BLE001
        return pd.Series(np.nan, index=dates)
    if frame.empty or "close" not in frame.columns:
        return pd.Series(np.nan, index=dates)
    frame = frame.sort_values("datetime").copy()
    frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()

    recs = {}
    for date, day in frame.groupby("date", sort=True):
        close = day["close"].to_numpy(float)
        if len(close) < 5 or np.any(close[-5:] <= 0):
            continue
        recs[date] = float(close[-1] / close[-5] - 1.0)
    return pd.Series(recs).reindex(dates)


def _rolling_bool_split_diff(cond: pd.Series, target: pd.Series, window: int) -> pd.Series:
    df = pd.concat({"cond": cond, "target": target}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    cd = df["cond"].to_numpy(bool)
    tg = df["target"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        cd_w = cd[start : i + 1]
        tg_w = tg[start : i + 1]
        a = tg_w[cd_w]
        b = tg_w[~cd_w]
        if len(a) == 0 or len(b) == 0:
            continue
        out.iloc[i] = float(np.mean(a) - np.mean(b))
    return out


def _rolling_sign_split_diff(level: pd.Series, target: pd.Series, window: int) -> pd.Series:
    df = pd.concat({"level": level, "target": target}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    lv = df["level"].to_numpy(float)
    tg = df["target"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        lv_w = lv[start : i + 1]
        tg_w = tg[start : i + 1]
        pos = tg_w[lv_w > 0]
        neg = tg_w[lv_w < 0]
        if len(pos) == 0 or len(neg) == 0:
            continue
        out.iloc[i] = float(np.mean(pos) - np.mean(neg))
    return out


def _rolling_median_split_diff(level: pd.Series, target: pd.Series, window: int) -> pd.Series:
    df = pd.concat({"level": level, "target": target}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    out = pd.Series(np.nan, index=df.index)
    lv = df["level"].to_numpy(float)
    tg = df["target"].to_numpy(float)
    n = len(df)
    for i in range(window - 1, n):
        start = i - window + 1
        lv_w = lv[start : i + 1]
        tg_w = tg[start : i + 1]
        med = np.median(lv_w)
        upper = tg_w[lv_w >= med]
        lower = tg_w[lv_w < med]
        if len(upper) == 0 or len(lower) == 0:
            continue
        out.iloc[i] = float(np.mean(upper) - np.mean(lower))
    return out


def _build(panels, eligibility, data_root, config):
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    as_of = dates.max()
    out = {name: pd.DataFrame(np.nan, index=dates, columns=symbols) for name in ATOM_NAMES}

    close_p = panels["close"]
    daily_ret = close_p.pct_change()

    perment_space = _resolved("permutation_entropy_1m", panels, eligibility, data_root)
    perm_entropy = perment_space["PERM_ENTROPY_RET_20"]

    bbwidth_space = _resolved("range_contraction_cycle", panels, eligibility, data_root)
    bb_width_chg = bbwidth_space["BB_WIDTH_CHG_20"]

    complexity_space = _resolved("complexity_measures_1m", panels, eligibility, data_root)
    sampen_ret = complexity_space["SAMPEN_RET_20"]

    rbv_space = _resolved("range_based_vol_1m", panels, eligibility, data_root)
    overnight_share = rbv_space["YZ_OVERNIGHT_SHARE_20"]

    lunch_space = _resolved("lunch_break_1m", panels, eligibility, data_root)
    lunch_postrun = lunch_space["LUNCH_POST_RUN_20"]
    pm_postrun_consist = pd.DataFrame(np.nan, index=dates, columns=symbols)
    for sym in symbols:
        postrun_ref_20 = lunch_postrun[sym].rolling(_ROLL, min_periods=12).mean()
        postrun_dev = lunch_postrun[sym] - postrun_ref_20
        pm_consist = np.sign(postrun_dev) == np.sign(daily_ret[sym])
        pm_consist = pm_consist.where(postrun_dev.notna() & daily_ret[sym].notna())
        pm_postrun_consist[sym] = pm_consist.astype(float).rolling(_ROLL, min_periods=12).mean().reindex(dates)

    for sym in symbols:
        close5 = _daily_close5_ret(data_root, sym, as_of, dates)
        consist_cond = (np.sign(close5) == np.sign(daily_ret[sym]))
        consist_cond = consist_cond.where(close5.notna() & daily_ret[sym].notna())

        atom1 = _rolling_bool_split_diff(consist_cond, perm_entropy[sym], _SPLIT_WINDOW)
        out["CLOSE5_CONSIST_PERMENT_SPLIT_20"][sym] = atom1.reindex(dates)
        out["CLOSE5_CONSIST_PERMENT_SPLIT_CHG_20"][sym] = (
            atom1.reindex(dates) - atom1.reindex(dates).shift(_ROLL)
        )

        atom2 = _rolling_sign_split_diff(bb_width_chg[sym], sampen_ret[sym], _SPLIT_WINDOW)
        out["BBWIDTH_CHG_SAMPEN_SPLIT_20"][sym] = atom2.reindex(dates)
        out["BBWIDTH_CHG_SAMPEN_SPLIT_CHG_20"][sym] = (
            atom2.reindex(dates) - atom2.reindex(dates).shift(_ROLL)
        )

        atom3 = _rolling_median_split_diff(overnight_share[sym], pm_postrun_consist[sym], _SPLIT_WINDOW)
        out["OVERNIGHT_SHARE_PMCONSIST_SPLIT_20"][sym] = atom3.reindex(dates)

    return {name: frame.where(np.isfinite(frame)) for name, frame in out.items()}


register_family(FamilyProvider("mechanism_atoms_v4", "mechanism_atoms_v4", _build))
