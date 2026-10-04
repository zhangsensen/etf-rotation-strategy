"""ETF cross-asset delayed-transmission family."""
from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..etf_lead_lag_factor_space import build_lead_lag_factor_space


def _build(panels, eligibility, data_root, config):
    return build_lead_lag_factor_space(
        panels["close"],
        tuple(config["benchmark_symbols"]),
        tuple(config["peer_symbols"]),
    )


register_family(FamilyProvider("cross_etf_lead_lag", "cross_etf_lead_lag", _build))
