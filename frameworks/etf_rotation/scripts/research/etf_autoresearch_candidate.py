"""The one editable file in the ETF autoresearch discovery loop.

Return one 14-ETF score panel. The fixed evaluator applies the original
eight-group aggregation and signed Rank IC; this file must never read labels.
"""
from __future__ import annotations

import pandas as pd

CANDIDATE_ID = "autoresearch_momentum_20_baseline"
FAMILY = "price_trend"
DIRECTION = 1
DESCRIPTION = "Twenty-session adjusted-close return, fixed positive direction."


def score(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return panels["close"].pct_change(20, fill_method=None)
