"""ETF asset-class relation atoms for all-weather rotation research."""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def parse_asset_classes(
    raw_classes: Mapping[str, list[str]],
    symbols: list[str],
) -> dict[str, str]:
    symbol_to_class: dict[str, str] = {}
    for class_name, members in raw_classes.items():
        for raw_symbol in members:
            symbol = str(raw_symbol)
            if symbol in symbol_to_class:
                raise ValueError(f"ETF appears in multiple asset classes: {symbol}")
            symbol_to_class[symbol] = str(class_name)
    missing = sorted(set(symbols) - set(symbol_to_class))
    if missing:
        raise ValueError(f"ETF asset-class map missing symbols: {missing}")
    return {symbol: symbol_to_class[symbol] for symbol in symbols}


def _assign_series(
    target: pd.DataFrame,
    members: list[str],
    values: pd.Series,
) -> None:
    target.loc[:, members] = np.repeat(values.to_numpy()[:, None], len(members), axis=1)


def build_cross_asset_factor_space(
    close: pd.DataFrame,
    eligibility: pd.DataFrame,
    symbol_to_class: Mapping[str, str],
) -> dict[str, pd.DataFrame]:
    """Build category leadership and within-category selection atoms using D-or-earlier data."""
    close = close.astype(float)
    eligibility = eligibility.reindex_like(close).fillna(False)
    daily_return = close.pct_change(fill_method=None)
    templates = {
        name: pd.DataFrame(np.nan, index=close.index, columns=close.columns)
        for name in (
            "CATEGORY_MOM_5", "CATEGORY_MOM_20", "CATEGORY_MOM_60",
            "WITHIN_CATEGORY_MOM_5", "WITHIN_CATEGORY_MOM_20", "WITHIN_CATEGORY_MOM_60",
            "CATEGORY_CURRENT_DD_20", "CATEGORY_CURRENT_DD_60",
            "CATEGORY_VOL_20", "CATEGORY_VOL_60",
            "CATEGORY_BREADTH_MA20", "CATEGORY_BREADTH_MA60",
            "CATEGORY_DISPERSION_20", "CATEGORY_DISPERSION_60",
        )
    }
    classes = sorted(set(symbol_to_class.values()))
    for class_name in classes:
        members = [symbol for symbol in close.columns if symbol_to_class[symbol] == class_name]
        member_eligible = eligibility[members]
        member_returns = daily_return[members].where(member_eligible)
        category_return = member_returns.mean(axis=1, skipna=True)
        category_index = (1.0 + category_return.fillna(0.0)).cumprod().where(
            category_return.notna().cummax()
        )
        for window in (5, 20, 60):
            category_momentum = category_index / category_index.shift(window) - 1.0
            individual_momentum = close[members] / close[members].shift(window) - 1.0
            within = individual_momentum.sub(category_momentum, axis=0).where(member_eligible)
            _assign_series(templates[f"CATEGORY_MOM_{window}"], members, category_momentum)
            templates[f"WITHIN_CATEGORY_MOM_{window}"].loc[:, members] = within
        for window in (20, 60):
            drawdown = category_index / category_index.rolling(window, min_periods=window).max() - 1.0
            volatility = category_return.rolling(window, min_periods=window).std(ddof=1)
            dispersion = member_returns.std(axis=1, ddof=1).rolling(
                window, min_periods=window
            ).mean()
            moving_average = close[members].rolling(window, min_periods=window).mean()
            breadth = close[members].gt(moving_average).where(member_eligible).mean(axis=1)
            _assign_series(templates[f"CATEGORY_CURRENT_DD_{window}"], members, drawdown)
            _assign_series(templates[f"CATEGORY_VOL_{window}"], members, volatility)
            _assign_series(templates[f"CATEGORY_DISPERSION_{window}"], members, dispersion)
            _assign_series(templates[f"CATEGORY_BREADTH_MA{window}"], members, breadth)
    return templates
