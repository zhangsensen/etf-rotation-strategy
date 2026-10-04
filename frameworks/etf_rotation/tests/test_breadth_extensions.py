from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from etf_strategy.core.etf_breadth_extensions import build_breadth_extensions
from etf_strategy.core.etf_family_catalog import load_family_catalog
from etf_strategy.core.family_registry import load_builtin_families


def panels():
    rng = np.random.default_rng(717)
    index = pd.bdate_range("2020-01-01", periods=180)
    close = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, .02, (180, 8)), axis=0)),
                         index=index)
    return dict(close=close, open=close * .999, high=close * (1 + rng.uniform(.005, .03, close.shape)),
                low=close * (1 - rng.uniform(.005, .03, close.shape)), amount=pd.DataFrame(
                    rng.lognormal(17, .7, close.shape), index=index))


def test_future_perturbation_and_prefix_invariance():
    p = panels()
    original = build_breadth_extensions(p)
    cut = 120
    truncated = build_breadth_extensions({k: v.iloc[:cut] for k, v in p.items()})
    changed = {k: v.copy() for k, v in p.items()}
    for v in changed.values():
        v.iloc[cut:] *= 37
    perturbed = build_breadth_extensions(changed)
    for name, frame in original.items():
        pd.testing.assert_frame_equal(frame.iloc[:cut], truncated[name])
        pd.testing.assert_frame_equal(frame.iloc[:cut], perturbed[name].iloc[:cut])
        assert frame.iloc[-20:].notna().all().all()


def test_undefined_and_scale_cases():
    p = panels()
    original = build_breadth_extensions(p)
    scaled = {k: v * (10 if k != "amount" else 1) for k, v in p.items()}
    for name, value in build_breadth_extensions(scaled).items():
        np.testing.assert_allclose(value, original[name], rtol=1e-7, atol=1e-10, equal_nan=True)
    p["amount"][:] = 0
    undefined = build_breadth_extensions(p)
    assert undefined["DOWN_UP_ACTIVITY_20"].isna().all().all()


def test_v2_catalog_and_axes_are_complete():
    root = Path(__file__).resolve().parents[1]
    load_builtin_families()
    paths = load_family_catalog(root / "configs/family_catalog_v2.yaml", root)
    configs = [yaml.safe_load(p.read_text()) for p in paths]
    families = {c["factor_source"] for c in configs}
    axes = yaml.safe_load((root / "configs/economic_axis_taxonomy_v2.yaml").read_text())
    assignments = [f for a in axes["axes"].values() for f in a["families"]]
    assert len(assignments) == len(set(assignments))
    assert set(assignments) == families
    assert len(families) == 31
    assert sum(len(c["atoms"]) for c in configs) == 147
