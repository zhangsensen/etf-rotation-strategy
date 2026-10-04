"""Mined 1d/1m families (round_018 era, directive 14): cost_distribution,
bar_size_order_flow, intraday_volume_profile_1m. Rebuilt faithfully from the
stage directives after the workspace-mirror loss; formulas follow the frozen
directive text (chips decay by window position, big bar = amount > 5x day
median, volume profile over 30-min edges)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..etf_intraday_factor_space import _read_complete_days
from ..family_provider import FamilyProvider
from ..family_registry import register_family


def _cost_atoms(close: pd.DataFrame, high, low, volume, amount) -> dict[str, pd.DataFrame]:
    typical = (high + low + close) / 3.0
    out: dict[str, pd.DataFrame] = {}

    profit = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    range90 = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    overhand = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    window = 60
    # chip decay: linear weight by recency within the window (turnover decay proxy)
    weights = np.arange(1, window + 1, dtype=float)
    weights /= weights.sum()
    cv = close.to_numpy(float)
    wv = volume.to_numpy(float)
    for j in range(close.shape[1]):
        for i in range(window, len(close)):
            c = cv[i : i + 1, j]
            prices = cv[i - window : i, j]
            vols = wv[i - window : i, j]
            ok = np.isfinite(prices) & np.isfinite(vols) & (vols > 0)
            if ok.sum() < window * 0.6:
                continue
            p, v, w = prices[ok], vols[ok], weights[ok]
            tot = float((v * w).sum())
            if tot <= 0:
                continue
            profit.iloc[i, j] = float((v * w * (p <= c[0])).sum() / tot)
            order = np.argsort(p)
            cum = np.cumsum(v[order] * w[order]) / tot
            p10 = float(p[order][np.searchsorted(cum, 0.10)])
            p90 = float(p[order][np.searchsorted(cum, 0.90)])
            med = float(p[order][np.searchsorted(cum, 0.50)])
            if med > 0:
                range90.iloc[i, j] = (p90 - p10) / med
            overhand.iloc[i, j] = float((v * w * (p > c[0] * 1.02)).sum() / tot)
    out["PROFIT_RATIO_60"] = profit
    out["CHIP_RANGE_90_60"] = range90
    out["OVERHAND_THICKNESS_60"] = overhand

    avg_cost = typical.rolling(20, min_periods=10).mean()
    out["PRICE_VS_AVGCOST_20"] = close / avg_cost - 1.0
    center = typical.rolling(60, min_periods=30).mean()
    out["COST_CENTER_SHIFT_20"] = center / center.shift(20) - 1.0
    return out


def _day_bar_features(day: pd.DataFrame) -> dict:
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
    direction = np.sign(ret)
    buy_vol = vol[ok][direction[ok] > 0].sum()
    sell_vol = vol[ok][direction[ok] < 0].sum()
    total = buy_vol + sell_vol
    tick_imb = (buy_vol - sell_vol) / total if total > 0 else np.nan
    med_amt = float(np.nanmedian(amt[ok]))
    big = ok & (amt > med_amt * 5.0)
    big_share = float(vol[big].sum() / vol[ok].sum()) if vol[ok].sum() > 0 else np.nan
    bb_buy = vol[big][direction[big] > 0].sum()
    bb_sell = vol[big][direction[big] < 0].sum()
    bb_tot = bb_buy + bb_sell
    big_skew = (bb_buy - bb_sell) / bb_tot if bb_tot > 0 else np.nan
    # tail-5-minute net direction vs full-day net direction
    idx_tail = np.where(ok)[0][-5:]
    tv, td = vol[idx_tail], direction[idx_tail]
    tail_net = np.sign(tv[td > 0].sum() - tv[td < 0].sum())
    day_net = np.sign(buy_vol - sell_vol)
    consist = 1.0 if tail_net != 0 and tail_net == day_net else 0.0
    # big-bar time concentration: share of big-bar volume in its modal 30-min slot
    if big.any() and big_share == big_share and big_share > 0:
        slots = np.minimum(np.arange(len(big)) // 30, 7)
        bslot = slots[big]
        counts = np.bincount(bslot, minlength=8).astype(float)
        conc = float(counts.max() / counts.sum()) if counts.sum() > 0 else np.nan
    else:
        conc = np.nan
    return {
        "tick_imb": tick_imb,
        "big_share": big_share,
        "big_skew": big_skew,
        "consist": consist,
        "conc": conc,
    }


def _bar_flow_atoms(data_root, symbols, frequency, as_of, dates) -> dict[str, pd.DataFrame]:
    out = {
        name: pd.DataFrame(np.nan, index=dates, columns=symbols)
        for name in (
            "TICK_IMBALANCE_20",
            "BIGBAR_VOL_SHARE_20",
            "BIGBAR_DIR_SKEW_20",
            "CLOSE5_DAY_CONSIST_20",
            "BIGBAR_EDGE_CONC_20",
        )
    }
    mapping = (
        ("tick_imb", "TICK_IMBALANCE_20"),
        ("big_share", "BIGBAR_VOL_SHARE_20"),
        ("big_skew", "BIGBAR_DIR_SKEW_20"),
        ("consist", "CLOSE5_DAY_CONSIST_20"),
        ("conc", "BIGBAR_EDGE_CONC_20"),
    )
    for sym in symbols:
        try:
            frame, _ = _read_complete_days(data_root, sym, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        frame = frame.copy()
        frame["date"] = frame["datetime"].dt.normalize()
        records = []
        for date, day in frame.groupby("date", sort=True):
            feats = _day_bar_features(day)
            if feats:
                feats["date"] = date
                records.append(feats)
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date")
        for feat, atom in mapping:
            out[atom][sym] = (
                daily[feat].rolling(20, min_periods=10).mean().reindex(dates)
            )
    return out


def _volume_profile_atoms(data_root, symbols, frequency, as_of, dates) -> dict[str, pd.DataFrame]:
    out = {
        name: pd.DataFrame(np.nan, index=dates, columns=symbols)
        for name in (
            "OPEN30_VOL_SHARE_20",
            "CLOSE30_VOL_SHARE_20",
            "VOL_AUTOCORR_20",
            "VOL_SPIKE_FREQ_20",
            "VOL_ENTROPY_20",
        )
    }
    for sym in symbols:
        try:
            frame, _ = _read_complete_days(data_root, sym, frequency, as_of)
        except Exception:  # noqa: BLE001
            continue
        if frame.empty:
            continue
        frame = frame.copy()
        frame["date"] = frame["datetime"].dt.normalize()
        records = []
        for date, day in frame.groupby("date", sort=True):
            vol = day["volume"].to_numpy(float)
            ok = np.isfinite(vol) & (vol > 0)
            if ok.sum() < 60:
                continue
            v = vol[ok]
            n = len(v)
            open30 = v[:30].sum() / v.sum()
            close30 = v[-30:].sum() / v.sum()
            lv = np.log(v)
            ac = float(np.corrcoef(lv[1:], lv[:-1])[0, 1]) if np.std(lv[1:]) > 0 and np.std(lv[:-1]) > 0 else np.nan
            med = float(np.median(v))
            spike = float((v > med * 5.0).mean())
            slots = np.minimum(np.arange(n) // 20, 11)
            counts = np.bincount(slots, minlength=12).astype(float)
            p = counts / counts.sum()
            p = p[p > 0]
            entropy = float(-(p * np.log(p)).sum() / np.log(len(p))) if len(p) > 1 else np.nan
            records.append(
                {
                    "date": date,
                    "open30": open30,
                    "close30": close30,
                    "ac": ac,
                    "spike": spike,
                    "entropy": entropy,
                }
            )
        if not records:
            continue
        daily = pd.DataFrame(records).set_index("date")
        for feat, atom in (
            ("open30", "OPEN30_VOL_SHARE_20"),
            ("close30", "CLOSE30_VOL_SHARE_20"),
            ("ac", "VOL_AUTOCORR_20"),
            ("spike", "VOL_SPIKE_FREQ_20"),
            ("entropy", "VOL_ENTROPY_20"),
        ):
            out[atom][sym] = (
                daily[feat].rolling(20, min_periods=10).mean().reindex(dates)
            )
    return out


def _build_cost(panels, eligibility, data_root, config):
    return _cost_atoms(
        panels["close"], panels["high"], panels["low"], panels["volume"], panels["amount"]
    )


def _build_bar_flow(panels, eligibility, data_root, config):
    frequency = str(config.get("frequency", "1m"))
    as_of = panels["close"].index.max()
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    return _bar_flow_atoms(data_root, symbols, frequency, as_of, dates)


def _build_volume_profile(panels, eligibility, data_root, config):
    frequency = str(config.get("frequency", "1m"))
    as_of = panels["close"].index.max()
    dates = panels["close"].index
    symbols = list(panels["close"].columns)
    return _volume_profile_atoms(data_root, symbols, frequency, as_of, dates)


register_family(FamilyProvider("cost_distribution", "cost_distribution", _build_cost))
register_family(FamilyProvider("bar_size_order_flow", "bar_size_order_flow", _build_bar_flow))
register_family(
    FamilyProvider("intraday_volume_profile_1m", "intraday_volume_profile_1m", _build_volume_profile)
)
