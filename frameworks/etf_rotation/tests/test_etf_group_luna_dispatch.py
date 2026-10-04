"""The formal runner's atom entry must preserve signed delegated results."""
import numpy as np
import pandas as pd
from etf_strategy.core import etf_group_daily_rounds as daily
from etf_strategy.core import etf_group_luna_rounds_a as a
from etf_strategy.core import etf_group_luna_rounds_b as b
from etf_strategy.core import etf_group_luna_rounds_c as c


def test_mixed_legacy_and_luna_batch_preserves_all_outputs():
    rng = np.random.default_rng(314)
    idx = pd.date_range('2024-01-01', periods=80)
    cols = [f'ETF{i}' for i in range(14)]
    close = pd.DataFrame(np.exp(np.cumsum(rng.normal(0, .01, (80, 14)), axis=0)), index=idx, columns=cols)
    open_ = close * 1.002
    panels = {'close': close, 'open': open_, 'high': close*1.01, 'low': close*.99,
              'amount': pd.DataFrame(np.exp(rng.normal(10, .2, (80, 14))), index=idx, columns=cols)}
    names = {'underwater_time_share': -1, 'l36_max_close_drawdown_depth': -1,
             'l41_peer_amount_to_return_beta': 1, 'l46_prior_channel_close_position': 1}
    cfg = {'windows': [20], 'mechanisms': {n: {'direction': d} for n, d in names.items()}}
    actual = daily.build_atoms(panels, cfg)
    assert set(actual) == {n+'_20' for n in names}
    for module in (a, b, c):
        subset = {n: cfg['mechanisms'][n] for n in names if n in module.DIRECTIONS}
        expected = module.build_atoms(panels, {**cfg, 'mechanisms': subset})
        for name, frame in expected.items():
            pd.testing.assert_frame_equal(actual[name], frame)
    assert actual['underwater_time_share_20'].iloc[-1].notna().all()
