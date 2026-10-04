"""ETF-only intraday atoms, all known after a complete close(D)."""
from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

import numpy as np
import pandas as pd


FREQUENCY_SPECS = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "60m": 60,
}

ATOM_NAMES = (
    "FIRST_HOUR_RET",
    "LAST_HOUR_RET",
    "MORNING_AFTERNOON_SPREAD",
    "INTRADAY_NET_RET",
    "INTRADAY_PATH_EFFICIENCY",
    "INTRADAY_REALIZED_VOL",
    "INTRADAY_RANGE",
    "CLOSE_LOCATION",
    "FIRST_HOUR_TURNOVER_SHARE",
    "LAST_HOUR_TURNOVER_SHARE",
    "CLOSE_VWAP_DEVIATION",
    "FIRST_HOUR_VWAP_DEVIATION",
    "VWAP_HALFDAY_SLOPE",
    "MORNING_VWAP_DEVIATION",
    "AFTERNOON_VWAP_DEVIATION",
    "MORNING_TURNOVER_SHARE",
    "AFTERNOON_TURNOVER_SHARE",
    "TURNOVER_CONCENTRATION",
    "INTRADAY_TREND_CONSISTENCY",
    "INTRADAY_SIGN_FLIP_RATE",
    "MORNING_VOL_SHARE",
    "AFTERNOON_VOL_SHARE",
    "VOL_CONCENTRATION",
    "INTRADAY_PV_RETURN_TURNOVER_CORR",
    "INTRADAY_MAX_RETURN_TURNOVER_IMPACT",
    # Minute mechanisms introduced for the independent breadth discovery pass.
    "INTRADAY_TAIL_REVERSAL",
    "INTRADAY_JUMP_INTENSITY",
    "INTRADAY_TAIL_JUMP_ASYMMETRY",
    "INTRADAY_RETURN_SKEW",
    "INTRADAY_DOWNSIDE_SKEW",
    "INTRADAY_RETURN_KURTOSIS",
    "UP_DOWN_TURNOVER_IMBALANCE",
    "SIGNED_TURNOVER_SHOCK",
    "TAIL_TURNOVER_PRICE_IMPACT",
)


def expected_intraday_times(date: pd.Timestamp | str, frequency: str) -> pd.DatetimeIndex:
    """Return the right-edge timestamps expected for a complete A-share ETF day."""
    if frequency not in FREQUENCY_SPECS:
        raise ValueError(f"unsupported intraday frequency: {frequency}")
    step = FREQUENCY_SPECS[frequency]
    day = pd.Timestamp(date).normalize()
    morning = pd.date_range(
        day + pd.Timedelta(hours=9, minutes=31) + pd.Timedelta(minutes=step - 1),
        day + pd.Timedelta(hours=11, minutes=30),
        freq=f"{step}min",
    )
    afternoon = pd.date_range(
        day + pd.Timedelta(hours=13, minutes=1) + pd.Timedelta(minutes=step - 1),
        day + pd.Timedelta(hours=15),
        freq=f"{step}min",
    )
    return morning.append(afternoon)


def _plausible_vwap(value: float, low: float, high: float) -> bool:
    """Reject source-unit breaks while tolerating small vendor rounding error."""
    return bool(np.isfinite(value) and low > 0 and low * 0.98 <= value <= high * 1.02)


def _read_complete_days(
    data_root: Path,
    symbol: str,
    frequency: str,
    as_of: pd.Timestamp | str | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read bars and return complete daily groups plus a coverage audit."""
    if frequency not in FREQUENCY_SPECS:
        raise ValueError(f"unsupported intraday frequency: {frequency}")
    path = Path(data_root) / frequency / f"{symbol}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_parquet(path).copy()
    required = {"datetime", "open", "high", "low", "close", "volume", "turnover"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{symbol} {frequency} missing columns: {missing}")
    if "price_basis" in frame and set(frame["price_basis"].dropna().astype(str)) != {"unadjusted"}:
        raise ValueError(f"{symbol} {frequency} price_basis must be uniformly unadjusted")
    frame["datetime"] = pd.to_datetime(frame["datetime"])
    frame = frame.sort_values("datetime")
    if frame["datetime"].duplicated().any():
        raise ValueError(f"{symbol} {frequency} contains duplicate timestamps")
    if as_of is not None:
        cutoff = pd.Timestamp(as_of).normalize() + pd.Timedelta(days=1)
        frame = frame.loc[frame["datetime"] < cutoff]
    frame["date"] = frame["datetime"].dt.normalize()
    expected_columns = ["open", "high", "low", "close", "volume", "turnover"]
    coverage_rows: list[dict[str, object]] = []
    complete_parts: list[pd.DataFrame] = []
    for date, day in frame.groupby("date", sort=True):
        expected = expected_intraday_times(date, frequency)
        actual = pd.DatetimeIndex(day["datetime"])
        finite = bool(np.isfinite(day[expected_columns].to_numpy(dtype=float)).all())
        positive_prices = bool((day[["open", "high", "low", "close"]] > 0).all().all())
        complete = bool(actual.equals(expected) and finite and positive_prices)
        coverage_rows.append(
            {
                "symbol": symbol,
                "frequency": frequency,
                "date": pd.Timestamp(date),
                "observed_bars": int(len(day)),
                "expected_bars": int(len(expected)),
                "complete": complete,
            }
        )
        if complete:
            complete_parts.append(day.drop(columns=["date"]))
    complete_frame = (
        pd.concat(complete_parts, ignore_index=True)
        if complete_parts
        else frame.iloc[0:0].drop(columns=["date"])
    )
    return complete_frame, pd.DataFrame(coverage_rows)


def inspect_intraday_coverage(
    data_root: Path,
    symbols: Sequence[str],
    frequencies: Sequence[str] = tuple(FREQUENCY_SPECS),
    as_of: pd.Timestamp | str | None = None,
) -> pd.DataFrame:
    """Summarize raw and complete-day coverage without changing research state."""
    rows: list[dict[str, object]] = []
    for frequency in frequencies:
        for symbol in symbols:
            _, coverage = _read_complete_days(data_root, symbol, frequency, as_of)
            if coverage.empty:
                rows.append(
                    {
                        "symbol": symbol,
                        "frequency": frequency,
                        "raw_days": 0,
                        "complete_days": 0,
                        "incomplete_days": 0,
                        "raw_bars": 0,
                        "expected_bars_per_day": len(expected_intraday_times(pd.Timestamp("2024-01-02"), frequency)),
                    }
                )
                continue
            rows.append(
                {
                    "symbol": symbol,
                    "frequency": frequency,
                    "raw_days": int(len(coverage)),
                    "complete_days": int(coverage["complete"].sum()),
                    "incomplete_days": int((~coverage["complete"]).sum()),
                    "raw_bars": int(coverage["observed_bars"].sum()),
                    "expected_bars_per_day": int(coverage["expected_bars"].iloc[0]),
                }
            )
    return pd.DataFrame(rows)


def build_intraday_factor_space(
    data_root: Path,
    symbols: Sequence[str],
    *,
    frequency: str = "60m",
    as_of: pd.Timestamp | str | None = None,
) -> dict[str, pd.DataFrame]:
    """Aggregate complete intraday bars to daily path features."""
    by_atom: dict[str, dict[str, pd.Series]] = {name: {} for name in ATOM_NAMES}
    for symbol in symbols:
        frame, _ = _read_complete_days(data_root, symbol, frequency, as_of)
        frame["date"] = pd.to_datetime(frame["datetime"]).dt.normalize()
        records: dict[str, dict[pd.Timestamp, float]] = {name: {} for name in ATOM_NAMES}
        for date, day in frame.groupby("date", sort=True):
            day = day.sort_values("datetime")
            first, last = day.iloc[0], day.iloc[-1]
            total_turnover = float(day["turnover"].sum())
            total_volume = float(day["volume"].sum())
            high, low = float(day["high"].max()), float(day["low"].min())
            opens = float(first["open"])
            closes = day["close"].astype(float)
            path = pd.concat([pd.Series([opens]), closes.reset_index(drop=True)], ignore_index=True)
            log_returns = np.log(path / path.shift(1)).dropna()
            return_values = log_returns.to_numpy(dtype=float)
            half = len(day) // 2
            morning_returns = return_values[:half]
            afternoon_returns = return_values[half:]
            total_abs_return = float(np.abs(return_values).sum())
            day_direction = float(np.sign(return_values.sum()))
            nonzero_signs = np.sign(return_values)
            nonzero_signs = nonzero_signs[nonzero_signs != 0]
            consistency = (
                float(np.mean(nonzero_signs == day_direction))
                if day_direction != 0 and len(nonzero_signs)
                else np.nan
            )
            sign_flip_rate = (
                float(np.mean(nonzero_signs[1:] != nonzero_signs[:-1]))
                if len(nonzero_signs) > 1
                else np.nan
            )
            morning_vol = float(np.sqrt(np.square(morning_returns).sum()))
            afternoon_vol = float(np.sqrt(np.square(afternoon_returns).sum()))
            total_vol = float(np.sqrt(np.square(return_values).sum()))
            turnover_shares = day["turnover"].astype(float).to_numpy() / total_turnover if total_turnover > 0 else np.full(len(day), np.nan)
            turnover_log = np.log1p(day["turnover"].astype(float).to_numpy())
            pv_corr = (
                float(np.corrcoef(return_values, turnover_log)[0, 1])
                if len(return_values) > 1 and np.std(return_values) > 0 and np.std(turnover_log) > 0
                else np.nan
            )
            impact = (
                float(np.max(np.abs(return_values) / np.sqrt(np.maximum(turnover_shares, 1e-12))))
                if np.isfinite(turnover_shares).all()
                else np.nan
            )
            # These atoms use only the complete D-day path.  ``tail`` is the
            # final quarter of bars and ``core`` is everything before it; the
            # split is deliberately path-relative so it works at every
            # supported minute frequency without adding a window parameter.
            tail_len = max(1, len(return_values) // 4)
            tail_returns = return_values[-tail_len:]
            core_returns = return_values[:-tail_len]
            core_move = float(core_returns.sum()) if len(core_returns) else 0.0
            tail_move = float(tail_returns.sum()) if len(tail_returns) else 0.0
            tail_reversal = (
                float(-np.sign(core_move) * tail_move)
                if core_move != 0.0
                else np.nan
            )
            max_abs_return = float(np.max(np.abs(return_values))) if len(return_values) else np.nan
            jump_intensity = (
                float(max_abs_return / total_abs_return)
                if total_abs_return > 0.0
                else np.nan
            )
            first_tail = return_values[:tail_len]
            first_tail_abs = float(np.abs(first_tail).sum())
            last_tail_abs = float(np.abs(tail_returns).sum())
            tail_jump_asymmetry = (
                float((last_tail_abs - first_tail_abs) / (last_tail_abs + first_tail_abs))
                if last_tail_abs + first_tail_abs > 0.0
                else np.nan
            )
            return_mean = float(np.mean(return_values)) if len(return_values) else np.nan
            return_std = float(np.std(return_values, ddof=0)) if len(return_values) else np.nan
            centered = return_values - return_mean if np.isfinite(return_mean) else np.array([])
            return_skew = (
                float(np.mean(centered ** 3) / return_std ** 3)
                if return_std > 0.0
                else np.nan
            )
            negative_returns = return_values[return_values < 0.0]
            downside_mean = float(np.mean(negative_returns)) if len(negative_returns) else np.nan
            downside_std = float(np.std(negative_returns, ddof=0)) if len(negative_returns) else np.nan
            downside_centered = negative_returns - downside_mean if np.isfinite(downside_mean) else np.array([])
            downside_skew = (
                float(np.mean(downside_centered ** 3) / downside_std ** 3)
                if downside_std > 0.0
                else np.nan
            )
            return_kurtosis = (
                float(np.mean(centered ** 4) / return_std ** 4 - 3.0)
                if return_std > 0.0
                else np.nan
            )
            positive_turnover = float(day.loc[return_values > 0.0, "turnover"].sum())
            negative_turnover = float(day.loc[return_values < 0.0, "turnover"].sum())
            up_down_turnover_imbalance = (
                float((positive_turnover - negative_turnover) / total_turnover)
                if total_turnover > 0.0
                else np.nan
            )
            signed_turnover_shock = (
                float(np.sum(return_values * turnover_shares))
                if np.isfinite(turnover_shares).all()
                else np.nan
            )
            tail_turnover = float(day.iloc[-tail_len:]["turnover"].sum())
            core_turnover = float(day.iloc[:-tail_len]["turnover"].sum())
            tail_turnover_price_impact = (
                float(
                    np.average(np.abs(tail_returns), weights=day.iloc[-tail_len:]["turnover"])
                    - np.average(np.abs(core_returns), weights=day.iloc[:-tail_len]["turnover"])
                )
                if tail_turnover > 0.0 and core_turnover > 0.0 and len(core_returns)
                else np.nan
            )
            afternoon_open = float(day.iloc[len(day) // 2]["open"])
            first_volume = float(first["volume"])
            first_vwap = (
                float(first["turnover"]) / first_volume if first_volume > 0 else np.nan
            )
            daily_vwap = total_turnover / total_volume if total_volume > 0 else np.nan
            morning = day.iloc[: len(day) // 2]
            afternoon = day.iloc[len(day) // 2 :]
            morning_volume = float(morning["volume"].sum())
            afternoon_volume = float(afternoon["volume"].sum())
            morning_vwap = (
                float(morning["turnover"].sum()) / morning_volume
                if morning_volume > 0 else np.nan
            )
            afternoon_vwap = (
                float(afternoon["turnover"].sum()) / afternoon_volume
                if afternoon_volume > 0 else np.nan
            )
            if not _plausible_vwap(daily_vwap, low, high):
                daily_vwap = np.nan
            if not _plausible_vwap(first_vwap, float(first["low"]), float(first["high"])):
                first_vwap = np.nan
            if not _plausible_vwap(
                morning_vwap, float(morning["low"].min()), float(morning["high"].max())
            ):
                morning_vwap = np.nan
            if not _plausible_vwap(
                afternoon_vwap,
                float(afternoon["low"].min()),
                float(afternoon["high"].max()),
            ):
                afternoon_vwap = np.nan
            values = {
                "FIRST_HOUR_RET": float(first["close"] / first["open"] - 1.0),
                "LAST_HOUR_RET": float(last["close"] / last["open"] - 1.0),
                "MORNING_AFTERNOON_SPREAD": float(
                    (first["close"] / first["open"] - 1.0)
                    - (last["close"] / afternoon_open - 1.0)
                ),
                "INTRADAY_NET_RET": float(last["close"] / opens - 1.0),
                "INTRADAY_PATH_EFFICIENCY": min(
                    1.0,
                    float(abs(np.log(float(last["close"]) / opens)) / total_abs_return),
                ) if total_abs_return > 0 else np.nan,
                "INTRADAY_REALIZED_VOL": float(np.sqrt(np.square(log_returns).sum())),
                "INTRADAY_RANGE": float(high / low - 1.0) if low > 0 else np.nan,
                "CLOSE_LOCATION": float((last["close"] - low) / (high - low)) if high > low else 0.5,
                "FIRST_HOUR_TURNOVER_SHARE": float(first["turnover"] / total_turnover) if total_turnover > 0 else np.nan,
                "LAST_HOUR_TURNOVER_SHARE": float(last["turnover"] / total_turnover) if total_turnover > 0 else np.nan,
                "CLOSE_VWAP_DEVIATION": float(last["close"] / daily_vwap - 1.0) if daily_vwap > 0 else np.nan,
                "FIRST_HOUR_VWAP_DEVIATION": float(first["close"] / first_vwap - 1.0) if first_vwap > 0 else np.nan,
                "VWAP_HALFDAY_SLOPE": float(afternoon_vwap / morning_vwap - 1.0) if morning_vwap > 0 and afternoon_vwap > 0 else np.nan,
                "MORNING_VWAP_DEVIATION": float(morning["close"].iloc[-1] / morning_vwap - 1.0) if morning_vwap > 0 else np.nan,
                "AFTERNOON_VWAP_DEVIATION": float(afternoon["close"].iloc[-1] / afternoon_vwap - 1.0) if afternoon_vwap > 0 else np.nan,
                "MORNING_TURNOVER_SHARE": float(morning["turnover"].sum() / total_turnover) if total_turnover > 0 else np.nan,
                "AFTERNOON_TURNOVER_SHARE": float(afternoon["turnover"].sum() / total_turnover) if total_turnover > 0 else np.nan,
                "TURNOVER_CONCENTRATION": float(np.square(turnover_shares).sum()) if np.isfinite(turnover_shares).all() else np.nan,
                "INTRADAY_TREND_CONSISTENCY": consistency,
                "INTRADAY_SIGN_FLIP_RATE": sign_flip_rate,
                "MORNING_VOL_SHARE": float(morning_vol / total_vol) if total_vol > 0 else np.nan,
                "AFTERNOON_VOL_SHARE": float(afternoon_vol / total_vol) if total_vol > 0 else np.nan,
                "VOL_CONCENTRATION": float(np.square(np.abs(return_values) / total_abs_return).sum()) if total_abs_return > 0 else np.nan,
                "INTRADAY_PV_RETURN_TURNOVER_CORR": pv_corr,
                "INTRADAY_MAX_RETURN_TURNOVER_IMPACT": impact,
                "INTRADAY_TAIL_REVERSAL": tail_reversal,
                "INTRADAY_JUMP_INTENSITY": jump_intensity,
                "INTRADAY_TAIL_JUMP_ASYMMETRY": tail_jump_asymmetry,
                "INTRADAY_RETURN_SKEW": return_skew,
                "INTRADAY_DOWNSIDE_SKEW": downside_skew,
                "INTRADAY_RETURN_KURTOSIS": return_kurtosis,
                "UP_DOWN_TURNOVER_IMBALANCE": up_down_turnover_imbalance,
                "SIGNED_TURNOVER_SHOCK": signed_turnover_shock,
                "TAIL_TURNOVER_PRICE_IMPACT": tail_turnover_price_impact,
            }
            for name, value in values.items():
                records[name][pd.Timestamp(date)] = value
        for name in ATOM_NAMES:
            by_atom[name][symbol] = pd.Series(records[name], dtype=float)
    factors = {}
    for name, columns in by_atom.items():
        factors[name] = pd.DataFrame(columns).sort_index().replace([np.inf, -np.inf], np.nan)
    first_share = factors["FIRST_HOUR_TURNOVER_SHARE"]
    for window in (20, 60):
        baseline = first_share.rolling(window, min_periods=window).mean()
        factors[f"FIRST_HOUR_SHARE_REL_{window}"] = (
            first_share / baseline.replace(0.0, np.nan) - 1.0
        )
        vwap_deviation = factors["CLOSE_VWAP_DEVIATION"]
        mean = vwap_deviation.rolling(window, min_periods=window).mean()
        std = vwap_deviation.rolling(window, min_periods=window).std(ddof=1)
        factors[f"CLOSE_VWAP_DEV_Z_{window}"] = (
            (vwap_deviation - mean) / std.replace(0.0, np.nan)
        )
    return factors
