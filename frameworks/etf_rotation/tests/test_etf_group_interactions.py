import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_group_interactions import build_atoms, leakage_checks, paired_increment, leave_group_score
from etf_strategy.core.etf_group_discovery import aggregate


def inputs():
    idx=pd.bdate_range('2024-01-01',periods=100)
    gs={f'g{i}':{'members':[f'e{i}']} for i in range(8)}
    gs['g0']['members']+=['e8','e9','e10','e11','e12']
    gs['g1']['members']+=['e13']
    rng=np.random.default_rng(24)
    left=pd.DataFrame(rng.normal(size=(100,8)),index=idx,columns=gs)
    right=pd.DataFrame(rng.normal(size=(100,8)),index=idx,columns=gs)
    cfg={'windows':[1],'_groups':gs,'mechanisms':{'pair':{'direction':1}}}
    return {'pair__left':left,'pair__right':right},cfg


def test_ranks_eight_groups_not_fourteen_duplicate_members():
    p,c=inputs()
    actual=aggregate(build_atoms(p,c)['pair_1'],c['_groups'])
    expected=p['pair__left'].rank(axis=1,pct=True)*p['pair__right'].rank(axis=1,pct=True)
    pd.testing.assert_frame_equal(actual,expected)
    assert build_atoms(p,c)['pair_1'].shape[1]==14


def test_incomplete_leg_drops_entire_score_date():
    p,c=inputs()
    p['pair__left'].iloc[2,1]=np.nan
    assert build_atoms(p,c)['pair_1'].iloc[2].isna().all()


def test_prefix_and_perturbation():
    p,c=inputs()
    assert all(leakage_checks(p,c,p['pair__left'].index[70]).values())
    c['mechanisms']['pair']['direction']=-1
    with pytest.raises(ValueError,match='reversed'):
        build_atoms(p,c)


def test_increment_is_paired_daily_difference_and_uses_common_dates():
    p,_=inputs()
    idx=p['pair__left'].index
    base=pd.DataFrame({'ic':np.sin(np.arange(100)), 'excess8':np.cos(np.arange(100))},index=idx)
    candidate=base+.1
    base.iloc[0,0]=np.nan
    r=paired_increment(candidate,base,idx,10)
    assert r['ic_n']==99
    assert r['excess8_n']==100
    assert r['ic_increment_mean']==pytest.approx(.1)
    assert r['excess8_increment_mean']==pytest.approx(.1)


def test_leave_group_recomputes_ranks_and_is_invariant_to_removed_identity():
    p,c=inputs()
    actual=leave_group_score(p,'pair','g0')
    expected=p['pair__left'].drop(columns='g0').rank(axis=1,pct=True)*p['pair__right'].drop(columns='g0').rank(axis=1,pct=True)
    pd.testing.assert_frame_equal(actual,expected)
    p['pair__left']['g0']=1e8
    p['pair__right']['g0']=-1e8
    pd.testing.assert_frame_equal(actual,leave_group_score(p,'pair','g0'))
