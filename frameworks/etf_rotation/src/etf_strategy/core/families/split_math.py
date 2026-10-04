"""Shared causal rolling split statistics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_sign_split_diff(
    level: pd.Series,
    target: pd.Series,
    window: int,
    *,
    min_group: int = 5,
) -> pd.Series:
    frame = pd.concat({"level": level, "target": target}, axis=1).dropna()
    output = pd.Series(np.nan, index=frame.index)
    for end in range(window - 1, len(frame)):
        sample = frame.iloc[end - window + 1 : end + 1]
        positive = sample.loc[sample["level"] > 0, "target"]
        negative = sample.loc[sample["level"] < 0, "target"]
        if len(positive) >= min_group and len(negative) >= min_group:
            output.iloc[end] = float(positive.mean() - negative.mean())
    return output


def rolling_median_split_diff(
    level: pd.Series,
    target: pd.Series,
    window: int,
    min_group: int = 1,
) -> pd.Series:
    frame = pd.concat({"level": level, "target": target}, axis=1).dropna()
    output = pd.Series(np.nan, index=frame.index)
    for end in range(window - 1, len(frame)):
        sample = frame.iloc[end - window + 1 : end + 1]
        median = sample["level"].median()
        upper = sample.loc[sample["level"] >= median, "target"]
        lower = sample.loc[sample["level"] < median, "target"]
        if len(upper) >= max(1, min_group) and len(lower) >= max(1, min_group):
            output.iloc[end] = float(upper.mean() - lower.mean())
    return output
