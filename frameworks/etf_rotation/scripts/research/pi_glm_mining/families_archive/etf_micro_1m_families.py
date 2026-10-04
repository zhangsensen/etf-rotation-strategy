"""Stage-6 1m microstructure families (directive 6, literature-backed):
microstructure_1m and benchmark_leadlag_1m. Reference benchmarks
(510300.SH/510500.SH) are legs only, never in the candidate population.
All features use only bars of complete trading days <= as_of."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family

BENCHMARKS = ("510300.SH", "510500.SH")
ROLL_ATOM_WINDOW = 20
MICRO_ATOMS = (
    "VPIN_CLOSE_20",
    "KYLE_LAMBDA_20",
    "ROLL_SPREAD_20",
    "AMIHUD_1M_20",
    "OFI_AUTOCORR_20",
    "IMPACT_ASYM_20",
)
LEADLAG_ATOMS = (
    "LAG1_BENCH_CORR_20",
    "SYNC_BETA_20",
    "SYNC_R2_20",
    "BETA_CHG_20",
    "TAIL30_BETA_GAP_20",
)


def _day_micro_features(day: pd.DataFrame) -> dict:
    close = day["close"].to_numpy(float)
    open0 = float(day["open"].to_numpy(float)[0])
    prev = np.concatenate([[open0], close[:-1]])
    ret = close / np.where(prev > 0, prev, np.nan) - 1.0
    vol = day["volume"].to_numpy(float)
    amt_col = "turnover" if "turnover" in day.columns else "amount"
    amt = day[amt_col].to_numpy(float)
    ok = np.isfinite(ret) & (vol > 0)
    if ok.sum() < 60:
        return {}
    r = ret[ok]
    v = vol[ok]
    a = amt[ok]
    dp_all = np.abs(close - prev)
    dp = dp_all[ok]
    # BVC: split each minute's volume by normal CDF of the minute return z
    sd = float(np.std(r))
    p_buy = norm.cdf(r / sd) if sd > 0 else np.full(len(r), 0.5)
    vb = v * p_buy
    vs = v * (1.0 - p_buy)
    # VPIN over 50 volume buckets (bucket = day volume / 50 -> the whole day)
    day_v = float(v.sum())
    if day_v <= 0:
        return {}
    bucket = day_v / 50.0
    cum_b = np.concatenate([[0.0], np.cumsum(vb)])
    cum_s = np.concatenate([[0.0], np.cumsum(vs)])
    bounds = np.arange(1, 51) * bucket
    pos_b = np.clip(np.searchsorted(cum_b, bounds, side="left"), 0, len(cum_b) - 1)
    pos_s = np.clip(np.searchsorted(cum_s, bounds, side="left"), 0, len(cum_s) - 1)
    vb_b = np.diff(cum_b[np.concatenate([[0], pos_b])])
    vs_b = np.diff(cum_s[np.concatenate([[0], pos_s])])
    vpin = float(np.abs(vb_b - vs_b).sum() / vb_b.sum()) if vb_b.sum() > 0 else np.nan
    # Kyle lambda proxy: |dp| ~ signed volume daily OLS slope
    sv = v * np.sign(r)
    var_sv = float(np.var(sv))
    kyle = float(np.cov(dp, sv)[0, 1] / var_sv) if var_sv > 0 else np.nan
    # Roll effective spread with negative-cov truncation
    if len(r) > 2:
        cov = float(np.cov(r[1:], r[:-1])[0, 1])
        roll = 2.0 * np.sqrt(max(0.0, -cov))
    else:
        roll = np.nan
    amihud = float(np.mean(np.abs(r) / np.where(a > 0, a, np.nan)))
    # order-flow imbalance persistence: lag-1 autocorr of BVC net buy volume
    ofi = vb - vs
    if np.std(ofi[1:]) > 0 and np.std(ofi[:-1]) > 0:
        ofi_ac = float(np.corrcoef(ofi[1:], ofi[:-1])[0, 1])
    else:
        ofi_ac = np.nan
    # price-impact asymmetry: buy-bar vs sell-bar |dp|/volume ratio
    dr = np.sign(r)
    up = dp[dr > 0] / v[dr > 0]
    dn = dp[dr < 0] / v[dr < 0]
    if len(up) and len(dn):
        up_imp, dn_imp = float(np.nanmean(up)), float(np.nanmean(dn))
        asym = up_imp / dn_imp if dn_imp > 0 else np.nan
    else:
        asym = np.nan
    return {
        "vpin_close": vpin,
        "kyle_lambda": kyle,
        "roll_spread": roll,
        "amihud_1m": amihud,
        "ofi_autocorr": ofi_ac,
        "impact_asym": asym,
    }


def _build_micro(panels, eligibility, data_root, config):
    close = panels["close"]
    dates = close.index
    frequency = str(config.get("frequency", "1m"))
    as_of = dates.max()
    root = Path(data_root)
    out = {name: pd.DataFrame(np.nan, index=dates, columns=close.columns) for name in MICRO_ATOMS}
    for sym in close.columns:
        try:
            frame, _ = _read_complete_days(root, sym, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        frame = frame.copy()
        frame["date"] = frame["datetime"].dt.normalize()
        records = []
        for date, day in frame.groupby("date", sort=True):
            feats = _day_micro_features(day)
            if feats:
                feats["date"] = date
                records.append(feats)
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date")
        for feat, atom in (
            ("vpin_close", "VPIN_CLOSE_20"),
            ("kyle_lambda", "KYLE_LAMBDA_20"),
            ("roll_spread", "ROLL_SPREAD_20"),
            ("amihud_1m", "AMIHUD_1M_20"),
            ("ofi_autocorr", "OFI_AUTOCORR_20"),
            ("impact_asym", "IMPACT_ASYM_20"),
        ):
            out[atom][sym] = (
                daily[feat].rolling(ROLL_ATOM_WINDOW, min_periods=10).mean().reindex(dates)
            )
    return out


def _day_leadlag(own_day: pd.Series, bench_day: pd.Series) -> dict:
    j = pd.concat([own_day.rename("o"), bench_day.rename("b")], axis=1).dropna()
    if len(j) < 60:
        return {}
    r_o = j["o"].to_numpy()
    r_b = j["b"].to_numpy()
    var_b = float(np.var(r_b))
    beta = float(np.cov(r_o, r_b)[0, 1] / var_b) if var_b > 0 else np.nan
    sd_o, sd_b = float(np.std(r_o)), float(np.std(r_b))
    corr = float(np.corrcoef(r_o, r_b)[0, 1]) if sd_o > 0 and sd_b > 0 else np.nan
    r2 = corr * corr if np.isfinite(corr) else np.nan
    lag1 = (
        float(np.corrcoef(r_o[1:], r_b[:-1])[0, 1])
        if np.std(r_o[1:]) > 0 and np.std(r_b[:-1]) > 0
        else np.nan
    )
    k = max(0, len(j) - 30)
    var_bt = float(np.var(r_b[k:]))
    beta_tail = float(np.cov(r_o[k:], r_b[k:])[0, 1] / var_bt) if var_bt > 0 else np.nan
    gap = beta_tail - beta if np.isfinite(beta_tail) and np.isfinite(beta) else np.nan
    return {"lag1": lag1, "beta": beta, "r2": r2, "gap": gap}


def _build_bench_leadlag(panels, eligibility, data_root, config):
    close = panels["close"]
    dates = close.index
    frequency = str(config.get("frequency", "1m"))
    as_of = dates.max()
    benchmarks = tuple(str(b) for b in config.get("benchmark_symbols", BENCHMARKS))
    root = Path(data_root)
    bench_rets = []
    for bench in benchmarks:
        path = root / frequency / f"{bench}.parquet"
        if not path.exists():
            continue
        try:
            frame, _ = _read_complete_days(root, bench, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        bench_rets.append(
            pd.Series(_day_ret(frame), index=frame["datetime"].to_numpy(dtype="datetime64[ns]"))
        )
    out = {name: pd.DataFrame(np.nan, index=dates, columns=close.columns) for name in LEADLAG_ATOMS}
    if not bench_rets:
        return out
    bench_ret = pd.concat(bench_rets, axis=1).mean(axis=1)
    for sym in close.columns:
        try:
            frame, _ = _read_complete_days(root, sym, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        own = pd.Series(
            _day_ret(frame),
            index=frame["datetime"].to_numpy(dtype="datetime64[ns]"),
        )
        j = pd.concat([own.rename("o"), bench_ret.rename("b")], axis=1).dropna()
        if j.empty:
            continue
        j["date"] = j.index.normalize()
        records = []
        for date, day in j.groupby("date", sort=True):
            feats = _day_leadlag(day["o"], day["b"])
            if feats:
                feats["date"] = date
                records.append(feats)
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date")
        for feat, atom in (
            ("lag1", "LAG1_BENCH_CORR_20"),
            ("beta", "SYNC_BETA_20"),
            ("r2", "SYNC_R2_20"),
        ):
            out[atom][sym] = (
                daily[feat].rolling(ROLL_ATOM_WINDOW, min_periods=10).mean().reindex(dates)
            )
        out["BETA_CHG_20"][sym] = (
            daily["beta"].rolling(ROLL_ATOM_WINDOW, min_periods=10).mean().diff(ROLL_ATOM_WINDOW).reindex(dates)
        )
        out["TAIL30_BETA_GAP_20"][sym] = (
            daily["gap"].rolling(ROLL_ATOM_WINDOW, min_periods=10).mean().reindex(dates)
        )
    return out


def _day_ret(frame: pd.DataFrame) -> np.ndarray:
    close = frame["close"].to_numpy(float)
    open0 = float(close[0]) if len(close) else np.nan
    prev = np.concatenate([[open0], close[:-1]])
    with np.errstate(all="ignore"):
        ret = close / np.where(prev > 0, prev, np.nan) - 1.0
    return ret


register_family(FamilyProvider("microstructure_1m", "microstructure_1m", _build_micro))
register_family(
    FamilyProvider("benchmark_leadlag_1m", "benchmark_leadlag_1m", _build_bench_leadlag)
)
