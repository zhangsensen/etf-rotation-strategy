"""Load one immutable autoresearch candidate into the formal ETF IC runner."""
from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[5]
FROZEN = Path("frameworks/etf_rotation/src/etf_strategy/core/autoresearch_frozen")


def frozen_source(config: dict) -> Path:
    name = config.get("candidate_module")
    if not isinstance(name, str) or not name.endswith(".py"):
        raise ValueError("frozen candidate module missing")
    relative = Path(name)
    if relative.parent != FROZEN or relative.name.startswith("."):
        raise ValueError("candidate module must be directly inside autoresearch_frozen")
    path = ROOT / relative
    if not path.is_file() or path.is_symlink():
        raise ValueError("frozen candidate source missing or symlinked")
    expected = config.get("candidate_sha256")
    if not isinstance(expected, str) or sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("frozen candidate source hash changed")
    return path


def load_candidate(config: dict):
    path = frozen_source(config)
    spec = importlib.util.spec_from_file_location("frozen_" + path.stem, path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot import frozen candidate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    mechanisms = config.get("mechanisms", {})
    if (len(mechanisms) != 1 or list(mechanisms) != [module.CANDIDATE_ID]
            or module.DIRECTION not in (-1, 1)
            or mechanisms[module.CANDIDATE_ID].get("direction") != module.DIRECTION
            or config.get("windows") != [1]):
        raise ValueError("frozen candidate metadata differs from approved config")
    return module


def build_atoms(panels: dict, config: dict) -> dict[str, pd.DataFrame]:
    if config.get("source_type") != "autoresearch":
        raise ValueError("wrong autoresearch source type")
    module = load_candidate(config)
    result = module.score(panels)
    close = panels["close"]
    if (not isinstance(result, pd.DataFrame) or not result.index.equals(close.index)
            or not result.columns.equals(close.columns)
            or not all(pd.api.types.is_numeric_dtype(dtype) for dtype in result.dtypes)):
        raise ValueError("candidate score differs from fixed ETF panel")
    return {module.CANDIDATE_ID: (result * module.DIRECTION).replace([np.inf, -np.inf], np.nan)}


def leakage_checks(panels: dict, config: dict, cut: str | pd.Timestamp) -> dict[str, bool]:
    cut = pd.Timestamp(cut)
    full = build_atoms(panels, config)
    prefix = build_atoms({key: frame.loc[:cut].copy() for key, frame in panels.items()}, config)
    future = {key: frame.copy() for key, frame in panels.items()}
    for frame in future.values():
        frame.loc[frame.index > cut] *= 1.73
    altered = build_atoms(future, config)
    for name, atom in full.items():
        pd.testing.assert_frame_equal(atom.loc[:cut], prefix[name], rtol=1e-10, atol=1e-12)
        pd.testing.assert_frame_equal(atom.loc[:cut], altered[name].loc[:cut], rtol=1e-10, atol=1e-12)
    return {f"{name}:prefix_and_future_perturbation": True for name in full}
