"""Fixed-population group diagnostics. No strategy or certification authority."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .etf_mining_referee import (
    block_t_calendar, fractional_topk_weights, newey_west_t_calendar,
    one_sided_normal_pvalue,
)
from .etf_rank_utils import stable_rank


def validate_groups(groups, symbols):
    members = [s for g in groups.values() for s in g['members']]
    if len(symbols) != 14 or len(groups) != 8:
        raise ValueError('require fixed 14 ETFs and 8 groups')
    if len(members) != len(set(members)) or set(members) != set(symbols):
        raise ValueError('group population mismatch or duplicate membership')


def aggregate(panel, groups):
    """No available-member averaging: missing one member invalidates its group."""
    return pd.DataFrame({g: panel[v['members']].mean(axis=1).where(
        panel[v['members']].notna().all(axis=1)) for g, v in groups.items()})


def build_atoms(panels, config):
    c, o, h, l, a = [panels[k] for k in ('close', 'open', 'high', 'low', 'amount')]
    ret = c.pct_change(fill_method=None)
    daily_range = (h-l)/c
    location = ((c-l)/(h-l).replace(0, np.nan))
    atoms = {}
    for w in config['windows']:
        mean = lambda x: x.rolling(w, min_periods=w).mean()
        raw = {
            'momentum': c.pct_change(w, fill_method=None),
            'efficiency': c.diff(w)/c.diff().abs().rolling(w).sum().replace(0, np.nan),
            'reversal': c.pct_change(w, fill_method=None),
            'gap': mean(o/c.shift(1)-1),
            'volatility': ret.rolling(w).std(),
            'downside': np.sqrt(mean(ret.clip(upper=0)**2)),
            'range_expansion': mean(daily_range)/daily_range.rolling(3*w).mean(),
            'amount_expansion': mean(a)/a.rolling(3*w).mean().replace(0, np.nan),
            'price_volume_corr': ret.rolling(w).corr(a.pct_change(fill_method=None)),
            'illiquidity': mean(ret.abs()/a.replace(0, np.nan)),
            # Explicit post-reverse-watch alias. Direction is frozen in a
            # separate approval so the failed old hypothesis is not relabelled.
            'reverse_illiquidity': mean(ret.abs()/a.replace(0, np.nan)),
            'close_location': mean(location),
            'intraday_return': mean(c/o-1),
        }
        for mechanism, definition in config['mechanisms'].items():
            atoms[f'{mechanism}_{w}'] = (raw[mechanism]*definition['direction']).replace(
                [np.inf, -np.inf], np.nan)
    return atoms


def labels(panels, lag=2, horizon=5):
    """Adjusted open/open research returns, not a claim of achievable execution."""
    o = panels['open']
    dates = pd.Series(o.index, index=o.index)
    timing = pd.DataFrame({'signal_date': dates, 'entry_date': dates.shift(-lag),
                           'exit_date': dates.shift(-lag-horizon)})
    return o.shift(-lag-horizon)/o.shift(-lag)-1, timing


def evaluate(score, member_labels, groups, known, timing, k=2):
    group_labels = aggregate(member_labels, groups)
    # Decisions depend only on signals/known-D coverage, never on label presence.
    signal = score.where(known, axis=0)
    weights = fractional_topk_weights(signal, k, min_names=len(groups))/k
    complete = known & signal.notna().all(axis=1) & member_labels.notna().all(axis=1)
    ic = stable_rank(signal).corrwith(group_labels.rank(axis=1, method='average'), axis=1)
    out = timing.copy()
    out['known_complete'] = known
    out['labels_complete'] = member_labels.notna().all(axis=1)
    out['ic'] = ic.where(complete)
    out['selected'] = (group_labels.fillna(0)*weights).sum(axis=1).where(complete)
    out['b8'] = group_labels.mean(axis=1).where(complete)
    out['b14'] = member_labels.mean(axis=1).where(complete)
    out['excess8'] = out.selected-out.b8
    out['excess14'] = out.selected-out.b14
    out['allocation_effect'] = out.b8-out.b14
    return out, weights


def summarize(frame, calendar, lag):
    out = {'n': int(frame.ic.notna().sum())}
    for col in ('ic', 'excess8', 'excess14', 'allocation_effect'):
        x = frame[col]
        out[col+'_mean'] = float(x.mean())
        out[col+'_hac_t'] = newey_west_t_calendar(x, calendar, lag)
        out[col+'_block_t'], out[col+'_blocks'] = block_t_calendar(x, calendar, 5)
    out['ic_p_normal_one_sided'] = one_sided_normal_pvalue(out['ic_hac_t'])
    return out


def leakage_checks(panels, config, cut):
    """Dynamic prefix and future perturbation invariance for every feature."""
    full = build_atoms(panels, config)
    prefix = build_atoms({k: v.loc[:cut] for k, v in panels.items()}, config)
    changed = {k: v.copy() for k, v in panels.items()}
    for v in changed.values():
        v.loc[v.index > cut] *= 1.71
    perturbed = build_atoms(changed, config)
    results = {}
    for name, atom in full.items():
        for mode, other in [('prefix', prefix[name]), ('future_perturbation', perturbed[name])]:
            pd.testing.assert_frame_equal(atom.loc[:cut], other.loc[:cut], check_exact=False,
                                          rtol=1e-9, atol=1e-12)
            results[f'{name}:{mode}'] = True
    return results
