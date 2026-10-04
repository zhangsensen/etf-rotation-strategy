import pandas as pd
import pytest
from etf_strategy.core.etf_research_contract import label_calendar, mature_surface, research_surfaces, consumption_contract, population_report


def test_maturity_uses_trading_sessions_and_rejects_cross_boundary():
    index = pd.bdate_range('2023-12-01', '2024-02-29').difference(pd.to_datetime(['2024-01-01']))
    dates = label_calendar(index, 20, 2)
    assert dates.loc['2023-12-29','entry_date'] == pd.Timestamp('2024-01-03')
    assert dates.loc['2023-12-29','exit_date'] == pd.Timestamp('2024-01-31')
    assert not mature_surface(dates,None,'2023-12-31').loc['2023-12-29']
    assert dates.loc[mature_surface(dates,None,'2023-12-31'),'exit_date'].le('2023-12-31').all()


def test_horizons_purge_separately_and_future_extension_does_not_change_valid_surface():
    index = pd.bdate_range('2022-01-01',periods=150)
    cfg={'discovery_end':str(index[70].date()),'seen_audit_start':str(index[71].date()),'seen_audit_end':str(index[120].date())}
    c,d,a=research_surfaces(index,[5,20],2,cfg)
    assert d[5].sum()-d[20].sum()==15
    assert not (d[5]&a[5]).any()
    assert a[20].sum()==28
    c2,d2,a2=research_surfaces(index[:121],[5,20],2,cfg)
    pd.testing.assert_series_equal(a[20].loc[index[:121]],a2[20])
    assert consumption_contract(c,d,a)['20']['seen_audit']['label_consumption_end']==str(index[120].date())


def test_population_reports_noncontributing_member_without_changing_pool():
    index=pd.bdate_range('2023-01-01',periods=10)
    e=pd.DataFrame({'A':True,'B':[False]*6+[True]*4},index=index)
    universe={'etfs':[{'ts_code':'A'},{'ts_code':'B'}],'classification_effective_from':'2026-09-18'}
    r=population_report(e,universe,pd.Series(index<index[5],index=index),pd.Series(index>=index[5],index=index))
    assert r['symbol_eligibility'][1]['discovery_eligible_days']==0
    assert r['ranking_symbol_count']==2
    assert r['historical_population_kind']=='current_pool_retrospective_not_pit_membership'


def test_bad_calendar_and_overlapping_surfaces_rejected():
    with pytest.raises(ValueError):label_calendar(pd.to_datetime(['2024-01-02','2024-01-01']),5,2)
    with pytest.raises(ValueError):research_surfaces(pd.bdate_range('2024-01-01',periods=20),[5],2,{'discovery_end':'2024-01-15','seen_audit_start':'2024-01-15','seen_audit_end':'2024-02-01'})
