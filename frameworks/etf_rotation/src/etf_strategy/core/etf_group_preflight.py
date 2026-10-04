"""Feature-only feasibility checks, independent of labels and IC acceptance."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .etf_group_discovery import aggregate
from .etf_rank_utils import stable_rank


def inspect_feature_coverage(atoms, groups, config, known=None):
    """Report fixed-group rankable dates whose calendar exit is within as_of.

    Uses only feature values and the trading calendar. One rankable date is
    sufficient to attempt IC; sample-size and significance diagnostics do not
    reject a candidate here. Missing members never receive replacements.
    """
    result = {}
    for name, atom in atoms.items():
        dates = pd.DatetimeIndex(atom.index)
        exit_dates = pd.Series(dates, index=dates).shift(
            -(int(config['entry_lag']) + int(config['horizon']))
        )
        eligible = ((dates >= pd.Timestamp(config['evaluation_start']))
                    & exit_dates.le(pd.Timestamp(config['as_of'])).to_numpy())
        scores = aggregate(atom.replace([np.inf, -np.inf], np.nan), groups).loc[eligible]
        complete = scores.notna().all(axis=1)
        if known is not None:
            complete &= known.reindex(scores.index, fill_value=False)
        rankable = complete & stable_rank(scores).nunique(axis=1).gt(1)
        result[name] = {
            'eligible_dates': len(scores),
            'complete_8group_dates': int(complete.sum()),
            'rankable_8group_dates': int(rankable.sum()),
            'structurally_eligible': bool(rankable.any()),
            'reason': 'RANKABLE_FEATURES' if rankable.any() else 'NO_COMMON_RANKABLE_DATES',
            'labels_read': False,
        }
    return result
