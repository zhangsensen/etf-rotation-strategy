"""Synthetic end-to-end engineering contract; never opens a research data store."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import json
import sys
import numpy as np
import pandas as pd
import pytest
import yaml
from etf_strategy.core.etf_cumulative_ledger import ETFCumulativeLedger

ROOT = Path(__file__).resolve().parents[1]


def _module(filename):
    spec=importlib.util.spec_from_file_location('test_'+filename, ROOT/'scripts'/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('descriptive', [True, False])
def test_runner_contract_and_wfo_export_with_synthetic_store(tmp_path, monkeypatch, descriptive):
    runner=_module('run_family_adjudication.py')
    rng=np.random.default_rng(662)
    dates=pd.bdate_range('2021-01-01',periods=640)
    symbols=[f'51000{i}.SH' for i in range(10)]
    data=tmp_path/'data';(data/'1d').mkdir(parents=True);(data/'adj_factor').mkdir()
    # Persistent but noisy synthetic growth ordering exercises descriptive paths.
    for i,s in enumerate(symbols):
        p=100*np.exp(np.cumsum(rng.normal(0,.015,len(dates))+(i-4.5)*.002))
        f=pd.DataFrame({'ts_code':s,'trade_date':dates,'open':p,'high':p*1.01,'low':p*.99,
                        'close':p,'volume':rng.uniform(500,2000,len(dates)),
                        'turnover':rng.uniform(50000,200000,len(dates)),'price_basis':'unadjusted'})
        f.to_parquet(data/'1d'/f'{s}.parquet',index=False)
        pd.DataFrame({'ts_code':s,'trade_date':dates,'adj_factor':1.0}).to_parquet(data/'adj_factor'/f'{s}.parquet',index=False)
    # A maintained observation with only later history must stay empty at the
    # capped research date, rather than failing the entire current-pool loader.
    late_symbol='159999.SZ'
    for folder in ['1d','adj_factor']:
        late=pd.read_parquet(data/folder/f'{symbols[0]}.parquet')
        late=late.loc[late.trade_date>dates[590]].copy();late['ts_code']=late_symbol
        late.to_parquet(data/folder/f'{late_symbol}.parquet',index=False)
    universe=tmp_path/'universe.json';universe.write_text(json.dumps({'etfs':
        [{'ts_code':s,'role':'candidate'} for s in symbols]+[{'ts_code':late_symbol,'role':'observation'}]}))
    family=tmp_path/'family.yaml'
    family.write_text(yaml.safe_dump({'factor_source':'synthetic','atoms':[{'name':'LEVEL','family':'synthetic'}],
                     'grammar':{'operators':['atomic'],'pair_policy':'cross_family_only'}}))
    catalog=tmp_path/'catalog.yaml';catalog.write_text('available_families: []\n')
    taxonomy=tmp_path/'taxonomy.yaml';taxonomy.write_text('axes:\n  synthetic_axis:\n    families: [synthetic]\n')
    config=tmp_path/'run.yaml';cfg={
        'domain':'synthetic_etf_contract_test','generation':'synthetic_test',
        'family_catalog':str(catalog),'economic_axis_taxonomy':str(taxonomy),
        'ranking_roles':['candidate'],'expected_ranking_symbols':10,'min_history_sessions':20,'require_positive_volume':True,'min_pairs':8,
        'execution':{'signal_time':'D_CLOSE','entry_lag_sessions':2,'horizons':[5,10,20],'primary_horizon':5},
        'surfaces':{'discovery_end':str(dates[430].date()),'seen_audit_start':str(dates[431].date()),'seen_audit_end':str(dates[590].date())},
        'gates':{'min_discovery_days':360,'min_abs_ic':.001 if descriptive else 2.0,'min_abs_seen_audit_ic':.001,'maxstat_alpha':.05},
        'referee':{'block_sessions':20,'permutation_draws':99,'max_permutation_draws':500,'seed':5},
        'baseline_controls':[{'config':str(family),'atom':'CONTROL'}],
    };config.write_text(yaml.safe_dump(cfg))
    # A synthetic provider exercises real adapter, actual IC, ledger and output code.
    provider=SimpleNamespace(information_family='synthetic',builder=lambda p,e,d,c:{'LEVEL':p['close'],'CONTROL':p['volume']})
    monkeypatch.setattr(runner,'resolve_family',lambda source:provider)
    monkeypatch.setattr(runner,'load_family_catalog',lambda *args:[family])
    output=tmp_path/'run';ledger=tmp_path/'ledger.duckdb'
    monkeypatch.setattr(sys,'argv',['run_family_adjudication.py','--canonical-data-root',str(data),'--universe-config',str(universe),
       '--adjudication-config',str(config),'--as-of',str(dates[-1].date()),'--output',str(output),'--ledger',str(ledger)])
    runner.main()
    manifest=json.loads((output/'run_manifest.json').read_text())
    assert manifest['effective_data_as_of']==str(dates[590].date())
    assert manifest['population']['maintenance_count']==11
    assert late_symbol in manifest['population']['excluded_symbols']
    inspector=_module('inspect_pool_contract.py')
    with monkeypatch.context() as context:
        context.setattr(sys,'argv',['inspect_pool_contract.py','--canonical-data-root',str(data),
            '--universe-config',str(universe),'--adjudication-config',str(config),
            '--as-of',str(dates[-1].date()),'--output',str(tmp_path/'pool.json')])
        inspector.main()
    pool=json.loads((tmp_path/'pool.json').read_text())
    assert pool['ranking_symbol_count']==10 and pool['maintenance_count']==11
    late=next(r for r in pool['maintained_symbol_coverage'] if r['symbol']==late_symbol)
    assert late['observed_days']==0 and late['first_observed_date'] is None
    raw=pd.read_parquet(output/'daily_raw_ic.parquet')
    assert raw.index.max()==dates[590]
    for h,rows in manifest['label_consumption'].items():
        assert pd.Timestamp(rows['discovery']['label_consumption_end'])<=dates[430]
        assert pd.Timestamp(rows['seen_audit']['label_consumption_end'])<=dates[590]
    table=pd.read_csv(output/'expression_decomposition.csv')
    assert bool(table.descriptive_gate_pass.any()) == descriptive
    tested=table.loc[table.descriptive_gate_pass]
    assert tested.marginal_status.eq('NOT_APPLICABLE').all()
    assert tested.marginal_gate_pass.isna().all()
    baseline=pd.read_csv(output/'economic_baseline_ic.csv')
    assert baseline.report_only.all() and bool(len(baseline)>0) == descriptive
    paired=pd.read_csv(output/'identity_paired_dates.csv')
    assert {'discovery_days','audit_days','baseline_seen_audit_ic','audit_delta'}<=set(paired)
    shared=pd.read_csv(output/'identity_shared_dates.csv')
    assert shared.groupby('expression_key').discovery_days.nunique().eq(1).all()
    wfo=_module('evaluate_factor_wfo.py')
    ic=wfo.load_daily_ic(output/'wfo_daily_ic.parquet')
    endpoints=wfo.load_label_dates(output/'label_dates.parquet')
    counts=wfo.load_eligibility_counts(output/'wfo_eligibility_counts.csv')
    from etf_strategy.core.etf_factor_wfo import evaluate_factor_wfo
    result=evaluate_factor_wfo(ic,endpoints,counts,[{'fold_id':'synthetic', 'train_start':dates[0],
       'train_end':dates[430],'test_start':dates[431],'test_end':dates[590]}])
    assert len(result)==3 and result.status.eq('EVALUATED').all()
    assert result.train_label_exit_max.le(dates[430]).all()
    c=ETFCumulativeLedger(ledger)
    assert c.prior_generation_count()==1
    assert c.connection.execute('select run_kind from etf_family_run_provenance').fetchone()==('HYPOTHESIS',)
    c.close()
    # Future source rows can change, but the capped view and all IC must not.
    for s in symbols:
        path=data/'1d'/f'{s}.parquet';f=pd.read_parquet(path)
        f.loc[f.trade_date>dates[590],['open','high','low','close']]*=50
        f.to_parquet(path,index=False)
    cfg['generation']='synthetic_future_perturbation';config.write_text(yaml.safe_dump(cfg))
    output2=tmp_path/'run2'
    argv=list(sys.argv);argv[argv.index('--output')+1]=str(output2);monkeypatch.setattr(sys,'argv',argv)
    runner.main()
    pd.testing.assert_frame_equal(raw,pd.read_parquet(output2/'daily_raw_ic.parquet'))


def test_ledger_provenance_preserves_counts_and_rejects_fake_replay(tmp_path):
    ledger=ETFCumulativeLedger(tmp_path/'ledger.duckdb')
    row=pd.DataFrame([{'expression_key':'x','true_family':'s','expression':'X','pooled_maxstat_pvalue':.5,'family_gate_pass':False}])
    ledger.record('original','h1','local',.025,row)
    ledger.record('correction','h2','local2',.008,row,run_kind='CORRECTED_RERUN',replay_of='original',provenance={'code_hash':'new'})
    assert ledger.prior_generation_count()==2
    with pytest.raises(ValueError,match='REPLAY'):
        ledger.record('fake','h2','local2',0,row,run_kind='REPLAY',replay_of='original')
    assert ledger.prior_generation_count()==2
    assert ledger.connection.execute('select alpha_spent from etf_family_generations order by created_at').fetchall()==[(.025,),(.008,)]
    ledger.close()


def test_wfo_reader_rejects_fractional_horizon(tmp_path):
    module=_module('evaluate_factor_wfo.py')
    path=tmp_path/'ic.parquet'
    pd.DataFrame({'horizon':[5.5],'signal_date':[pd.Timestamp('2024-01-01')],
                  'expression_key':['A'],'ic':[.1]}).to_parquet(path,index=False)
    with pytest.raises(ValueError,match='positive integers'):
        module.load_daily_ic(path)
