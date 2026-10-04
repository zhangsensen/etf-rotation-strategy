"""ETF-local provider contract for independently registered information families."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

import pandas as pd


Builder = Callable[
    [Mapping[str, pd.DataFrame], pd.DataFrame, Path, Mapping[str, object]],
    dict[str, pd.DataFrame],
]


@dataclass(frozen=True)
class FamilyProvider:
    source_name: str
    information_family: str
    builder: Builder
