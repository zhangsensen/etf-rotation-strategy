from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from etf_strategy.core.etf_daily_breadth_v3 import build_daily_breadth_v3, build_macro_sensitivity, build_turnover_allocation
from etf_strategy.core.etf_dependence_space import build_dependence_space, build_systemic_loading
from etf_strategy.core.etf_intraday_breadth_v3 import day_mechanisms, build_intraday_breadth_v3
from etf_strategy.core.etf_intraday_factor_space import expected_intraday_times
from etf_strategy.core.family_registry import load_builtin_families
from etf_strategy.core.etf_family_catalog import load_family_catalog


def data(n=170):
    rng=np.random.default_rng(9901)
    idx=pd.bdate_range('2020-01-01',periods=n)
    cols=list('ABCDEFGH')
    c=pd.DataFrame(100*np.exp(np.cumsum(rng.normal(0,.02,(n,8)),axis=0)),index=idx,columns=cols)
    return dict(close=c,open=c*(1+rng.normal(0,.01,c.shape)),high=c*(1+rng.uniform(.02,.04,c.shape)),low=c*(1-rng.uniform(.02,.04,c.shape)),amount=pd.DataFrame(rng.lognormal(15,.6,c.shape),index=idx,columns=cols))


def test_daily_prefix_future_and_scale_invariance():
    p=data(); e=pd.DataFrame(True,index=p['close'].index,columns=p['close'].columns)
    config={'benchmark_symbols':['G','H'],'hedge_symbols':{'F':'GOLD','E':'BOND'},'peer_symbols':list('ABCDEFGH')}
    builders=[lambda p,e:build_daily_breadth_v3(p),lambda p,e:build_macro_sensitivity(p,e,config),lambda p,e:build_dependence_space(p,e,config['peer_symbols']),lambda p,e:build_systemic_loading(p,e,config['peer_symbols']),lambda p,e:build_turnover_allocation(p,e,config)]
    changed={k:v.copy() for k,v in p.items()}
    for v in changed.values():v.iloc[130:]*=19
    for builder in builders:
        first=builder(p,e); second=builder(changed,e)
        prefix=builder({k:v.iloc[:130] for k,v in p.items()},e.iloc[:130])
        scaled=builder({k:v*(10 if k!='amount' else 1) for k,v in p.items()},e)
        for name,v in first.items():
            pd.testing.assert_frame_equal(v.iloc[:130],second[name].iloc[:130])
            pd.testing.assert_frame_equal(v.iloc[:130],prefix[name])
            np.testing.assert_allclose(v,scaled[name],atol=1e-7,rtol=1e-6,equal_nan=True)


def test_ineligible_peer_has_no_effect():
    p=data();e=pd.DataFrame(True,index=p['close'].index,columns=p['close'].columns);e['H']=False
    a=build_dependence_space(p,e,list('ABCDEFGH'))
    p['close']['H']=np.arange(len(e))**3+1
    b=build_dependence_space(p,e,list('ABCDEFGH'))
    for k in a:pd.testing.assert_frame_equal(a[k],b[k])


def test_intraday_complete_day_and_cutoff(tmp_path):
    folder=tmp_path/'5m';folder.mkdir(); dates=pd.bdate_range('2024-01-02',periods=23)
    rng=np.random.default_rng(81)
    for symbol in list('ABCDEF'):
        rows=[]
        for d in dates:
            times=expected_intraday_times(d,'5m');c=100*np.exp(np.cumsum(rng.normal(0,.002,48)))
            for t,x in zip(times,c):rows.append(dict(datetime=t,open=x*.999,high=x*1.003,low=x*.997,close=x,volume=100,turnover=x*100))
        f=pd.DataFrame(rows)
        if symbol=='A':f=f.drop(index=48) # incomplete second day
        f.to_parquet(folder/f'{symbol}.parquet')
    eligibility=pd.DataFrame(True,index=dates,columns=list('ABCDEF'))
    result=build_intraday_breadth_v3(tmp_path,list('ABCDEF'),dates[-2],list('ABCDEF'),eligibility.loc[:dates[-2]])
    assert pd.isna(result['EXTREME_TIME_ORDER'].loc[dates[1],'A'])
    assert result['JUMP_VARIATION_SHARE'].index.max()==dates[-2]
    for s in list('ABCDEF'):
        f=pd.read_parquet(folder/f'{s}.parquet');f.loc[f.datetime.dt.normalize()==dates[-1],'close']*=8;f.to_parquet(folder/f'{s}.parquet')
    repeat=build_intraday_breadth_v3(tmp_path,list('ABCDEF'),dates[-2],list('ABCDEF'),eligibility.loc[:dates[-2]])
    for k in result:pd.testing.assert_frame_equal(result[k],repeat[k])


def test_v3_catalog_complete_and_unique():
    root=Path(__file__).resolve().parents[1];load_builtin_families()
    paths=load_family_catalog(root/'configs/family_catalog_v3.yaml',root)
    families={yaml.safe_load(p.read_text())['factor_source'] for p in paths}
    axes=yaml.safe_load((root/'configs/economic_axis_taxonomy_v3.yaml').read_text())['axes']
    members=[f for a in axes.values() for f in a['families']]
    assert set(members)==families and len(members)==len(set(members))
    assert len(families)>31


def test_missing_peer_history_and_invalid_ohlc(tmp_path):
    folder = tmp_path / '5m'
    folder.mkdir()
    dates = pd.bdate_range('2024-01-02', periods=3)
    symbols = list('ABCDEF')
    for symbol in symbols:
        rows = []
        for d in dates:
            for j, t in enumerate(expected_intraday_times(d, '5m')):
                price = 100 + np.sin(j) + j / 100
                rows.append(dict(datetime=t, open=price, high=price+1,
                                 low=price-1, close=price, volume=100,
                                 turnover=price*100))
        frame = pd.DataFrame(rows)
        if symbol == 'F':
            frame = frame.iloc[:0]  # entire peer has no observations
        if symbol == 'A':
            frame.loc[0, 'high'] = 1  # complete timestamps but invalid OHLC
        frame.to_parquet(folder / f'{symbol}.parquet')
    eligible = pd.DataFrame(True, index=dates, columns=symbols)
    out = build_intraday_breadth_v3(tmp_path, symbols, dates[-1], symbols, eligible)
    assert out['INTRADAY_PEER_R2']['F'].isna().all()
    assert pd.isna(out['EXTREME_TIME_ORDER'].loc[dates[0], 'A'])
    assert np.isfinite(out['INTRADAY_PEER_R2'].loc[dates[-1], 'A'])
    missing_daily = build_intraday_breadth_v3(
        tmp_path, symbols, dates[-1], symbols, eligible.drop(index=dates[1])
    )
    assert missing_daily['INTRADAY_PEER_R2'].index.equals(eligible.drop(index=dates[1]).index)


def test_invalid_turnover_does_not_enter_allocation():
    p = data()
    eligible = pd.DataFrame(True, index=p['close'].index, columns=p['close'].columns)
    p['amount']['H'] = -100
    cfg = {'peer_symbols': list('ABCDEFGH')}
    invalid = build_turnover_allocation(p, eligible, cfg)
    p['amount']['H'] = np.nan
    missing = build_turnover_allocation(p, eligible, cfg)
    for name in invalid:
        pd.testing.assert_frame_equal(invalid[name], missing[name])


def test_turnover_allocation_has_no_membership_entry_exit_spike():
    p = data()
    # Constant turnover per incumbent: adding/removing a large ETF must not
    # look like a transfer of activity to/from all the other names.
    p['amount'].iloc[:] = np.arange(1, 9) * 1_000_000
    e = pd.DataFrame(True, index=p['close'].index, columns=p['close'].columns)
    e.loc[e.index[:70], 'H'] = False
    e.loc[e.index[140:], 'G'] = False
    result = build_turnover_allocation(p, e, {'peer_symbols': list('ABCDEFGH')})
    for frame in result.values():
        finite = frame.to_numpy()[np.isfinite(frame.to_numpy())]
        assert len(finite) > 0
        np.testing.assert_allclose(finite, 0, atol=1e-14)


def test_gold_self_exclusion_uses_thirteen_common_ic_pairs():
    from etf_strategy.core.etf_family_referee import common_sample_spearman
    columns = list(range(14))
    signal = pd.DataFrame([np.arange(14, dtype=float)], columns=columns)
    signal[13] = np.nan
    outcome = pd.DataFrame([np.arange(14, dtype=float)], columns=columns)
    outcome[13] = -1000  # missing gold must not distort ranks of the other 13
    eligibility = pd.DataFrame(True, index=signal.index, columns=columns)
    ic, count = common_sample_spearman(signal, outcome, eligibility, 8)
    assert count.iloc[0] == 13
    np.testing.assert_allclose(ic.iloc[0], 1)
