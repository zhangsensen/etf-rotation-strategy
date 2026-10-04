from ..family_provider import FamilyProvider
from ..family_registry import register_family
from ..etf_intraday_factor_space import build_intraday_factor_space


def _build(panels, eligibility, data_root, config):
    return build_intraday_factor_space(
        data_root,
        list(panels["close"].columns),
        frequency=str(config["frequency"]),
        as_of=panels["close"].index.max(),
    )


# Retired compatibility builder intentionally has no registry side effect.
