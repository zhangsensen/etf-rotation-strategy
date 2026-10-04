"""Bounded two-leg group interactions; no fitted weights or direction changes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import etf_group_sources as sources
from .etf_group_discovery import aggregate
from .etf_mining_referee import newey_west_t_calendar
from .etf_rank_utils import stable_rank


def parent_config(cfg):
    return {'mechanisms':{f'{m}__{side}':d[side] for m,d in cfg['mechanisms'].items()
                          for side in ('left','right')}}


def parent_artifacts(repo,cfg):
    return sources.parent_artifacts(repo,parent_config(cfg))


def load_parent_source(repo,groups,calendar,cfg):
    expanded,audits=sources.load_parent_source(repo,groups,calendar,parent_config(cfg))
    return {k:aggregate(v,groups) for k,v in expanded.items()},audits


def build_atoms(panels,cfg):
    if cfg['windows']!=[1]:
        raise ValueError('interaction has no new smoothing window')
    groups=cfg['_groups']
    atoms={}
    for name,d in cfg['mechanisms'].items():
        if d['direction']!=1:
            raise ValueError('parent directions may not be reversed')
        left=panels[name+'__left']
        right=panels[name+'__right'].reindex_like(left)
        if set(left.columns)!=set(groups):
            raise ValueError('interaction must rank groups, not repeated ETF members')
        complete=left.notna().all(axis=1)&right.notna().all(axis=1)
        result=(stable_rank(left,pct=True)*stable_rank(right,pct=True)).where(complete,axis=0)
        atoms[name+'_1']=pd.DataFrame({s:result[g] for g,v in groups.items() for s in v['members']})
    return atoms


def leakage_checks(panels,cfg,cut):
    full=build_atoms(panels,cfg)
    prefix=build_atoms({k:v.loc[:cut] for k,v in panels.items()},cfg)
    changed={k:v.copy() for k,v in panels.items()}
    for v in changed.values():
        v.loc[v.index>cut]*=-1.71
    perturbed=build_atoms(changed,cfg)
    for n in full:
        pd.testing.assert_frame_equal(full[n].loc[:cut],prefix[n])
        pd.testing.assert_frame_equal(full[n].loc[:cut],perturbed[n].loc[:cut])
    return {n:True for n in full}


def paired_increment(candidate,parent,calendar,lag):
    """Paired IC and return differences, never a subtraction of two t statistics."""
    result={}
    for metric in ('ic','excess8'):
        a=candidate[metric].reindex(calendar)
        b=parent[metric].reindex(calendar)
        diff=(a-b).where(np.isfinite(a)&np.isfinite(b))
        result[metric+'_n']=int(diff.notna().sum())
        result[metric+'_increment_mean']=float(diff.mean())
        result[metric+'_increment_hac_t']=newey_west_t_calendar(diff,calendar,lag)
    return result


def leave_group_score(panels,mechanism,omitted):
    """Remove identity before both rank operators, not after composing the score."""
    left=panels[mechanism+'__left'].drop(columns=omitted)
    right=panels[mechanism+'__right'].drop(columns=omitted).reindex_like(left)
    complete=left.notna().all(axis=1)&right.notna().all(axis=1)
    return (stable_rank(left,pct=True)*stable_rank(right,pct=True)).where(complete,axis=0)
