import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/scripts/research"))
sys.path.insert(0, str(Path(__file__).resolve().parents[7] / "runtime_outputs/etf_sonnet_mining_20260920/workspace/frameworks/etf_rotation/src"))
import pi_round002_mine as base
from etf_strategy.core.family_registry import load_builtin_families, resolve_family
import pandas as pd

panels, eligibility_all, symbols, forward = base._load_context()
load_builtin_families()

v6_space = resolve_family("mechanism_atoms_v6_split").builder(
    panels, eligibility_all[symbols], base.CANONICAL_ROOT, {"frequency": "1m"}
)
ret1 = panels["close"][symbols].pct_change()


def rank_corr(a, b, stride=5):
    a2 = a.iloc[::stride].rank(axis=1, pct=True).stack()
    b2 = b.iloc[::stride].rank(axis=1, pct=True).stack()
    df = pd.concat({"a": a2, "b": b2}, axis=1).dropna()
    return df["a"].corr(df["b"]), len(df)


for name in v6_space:
    c, n = rank_corr(v6_space[name][symbols], ret1)
    print(name, "corr vs ret1(D) =", round(c, 4), "n=", n)
