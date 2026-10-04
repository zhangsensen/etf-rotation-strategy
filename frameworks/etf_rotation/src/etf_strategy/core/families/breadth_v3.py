"""ETF-only v3 family registration; preserves previous catalog sources."""
from pathlib import Path
from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..etf_daily_breadth_v3 import build_daily_breadth_v3, build_macro_sensitivity, build_turnover_allocation
from ..etf_dependence_space import build_dependence_space, build_systemic_loading
from ..etf_intraday_breadth_v3 import build_intraday_breadth_v3


def daily(panels, eligibility, data_root, config):
    return build_daily_breadth_v3(panels)


# Five catalog sources expose disjoint subsets of the same daily space.  The
# evaluator may reuse one build inside a single materialization call.
daily.family_space_cache_key = "daily_breadth_v3"


def dependence(panels, eligibility, data_root, config):
    result = build_dependence_space(panels, eligibility, config['peer_symbols'])
    result.update(build_systemic_loading(panels, eligibility, config['peer_symbols']))
    return result


def macro(panels, eligibility, data_root, config):
    return build_macro_sensitivity(panels, eligibility, config)


def allocation(panels, eligibility, data_root, config):
    return build_turnover_allocation(panels, eligibility, config)


_INTRADAY_CACHE = {}


def intraday(panels, eligibility, data_root, config):
    # Eligibility fingerprint avoids cross-population reuse within a process.
    import hashlib
    import pandas as pd
    symbols = tuple(panels['close'].columns)
    peers = tuple(config['peer_symbols'])
    cutoff = panels['close'].index.max()
    digest = hashlib.sha256(pd.util.hash_pandas_object(eligibility,index=True).values.tobytes()).hexdigest()
    key = (str(Path(data_root).resolve()),symbols,peers,str(cutoff),digest)
    if key not in _INTRADAY_CACHE:
        _INTRADAY_CACHE[key] = build_intraday_breadth_v3(data_root,symbols,cutoff,peers,eligibility)
    return _INTRADAY_CACHE[key]


for name in ('volume_at_price_memory','drawdown_duration','swing_topology','volatility_feedback','gap_repair'):
    register_family(FamilyProvider(name,name,daily))
for name in ('dependence_structure','tail_dependence'):
    register_family(FamilyProvider(name,name,dependence))
register_family(FamilyProvider('macro_hedge_sensitivity','macro_hedge_sensitivity',macro))
register_family(FamilyProvider('pool_turnover_allocation','pool_turnover_allocation',allocation))
for name in ('intraday_systematic_share','jump_variation','intraday_profile_deviation','intraday_extremes_timing','intraday_volume_at_price'):
    register_family(FamilyProvider(name,name,intraday))
