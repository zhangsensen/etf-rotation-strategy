import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/research'))
from etf_autoresearch_implementation import etf_conditional_ols, etf_rolling_spearman, embed_kernel, synthetic_check, kernel_binding, editable_candidate_source
from run_etf_autoresearch_campaign import validate_source


def data():
    rng=np.random.default_rng(31)
    x=pd.DataFrame(rng.integers(-3,4,(90,3)).astype(float),index=pd.date_range('2024-01-01',periods=90))
    y=pd.DataFrame(rng.normal(size=(90,3)),index=x.index)
    x.iloc[24,0]=np.nan;y.iloc[33,1]=np.nan
    return x,y


@pytest.mark.parametrize('require_complete',[False,True])
def test_conditional_ols_matches_window_lstsq(require_complete):
    x,y=data();condition=x.gt(0);actual=etf_conditional_ols(x,y,condition,20,5,require_complete)
    expected=x*float('nan')
    for end in range(19,len(x)):
        for col in x:
            a,b=x[col].iloc[end-19:end+1],y[col].iloc[end-19:end+1]
            valid=a.notna() & b.notna();selected=valid & (a>0)
            if require_complete and not valid.all():continue
            if selected.sum()<5 or a[selected].var(ddof=0)<=0:continue
            expected.iloc[end,col]=np.linalg.lstsq(np.column_stack([np.ones(selected.sum()),a[selected]]),b[selected],rcond=None)[0][1]
    pd.testing.assert_frame_equal(actual,expected,rtol=1e-10,atol=1e-12)


def test_spearman_matches_direct_window_rank_with_ties_and_missing_pairs():
    x,y=data();actual=etf_rolling_spearman(x,y,20,10);expected=x*float('nan')
    for end in range(19,len(x)):
        for col in x:
            a,b=x[col].iloc[end-19:end+1],y[col].iloc[end-19:end+1]
            valid=a.notna() & b.notna()
            if valid.sum()>=10:
                expected.iloc[end,col]=a[valid].rank().corr(b[valid].rank())
    pd.testing.assert_frame_equal(actual,expected,rtol=1e-10,atol=1e-12)
    pd.testing.assert_frame_equal(actual.iloc[:70],etf_rolling_spearman(x.iloc[:70],y.iloc[:70],20,10))


def candidate(body):
    return 'import pandas as pd\nCANDIDATE_ID="autoresearch_check"\nFAMILY="test"\nDIRECTION=1\nDESCRIPTION="test"\ndef score(panels):\n'+body+'\n'


def test_kernel_embedding_is_sealed_source_and_not_mutable_import():
    source=candidate('    x=panels["close"]\n    return etf_conditional_ols(x, x, x.gt(0), 20, 10)')
    sealed=embed_kernel(source,'conditional_ols');validate_source(sealed)
    assert embed_kernel(sealed,'conditional_ols')==sealed
    assert synthetic_check(sealed,['close'])['status']=='PASS'
    with pytest.raises(ValueError,match='differs'):
        embed_kernel(sealed.replace('n.ge(min_pairs)','n.ge(1)'),'conditional_ols')
    custom = candidate('    return panels["close"]')
    assert embed_kernel(custom,'conditional_ols') == custom
    assert kernel_binding(custom,'conditional_ols')['effective'] == 'custom'
    assert kernel_binding(sealed,'conditional_ols')['template_called']


def test_synthetic_catches_broadcast_hidden_by_final_reindex():
    source=candidate('    x=panels["close"]\n    bad=x.sum(axis=1).sub(x,axis=0)\n    return bad.reindex(index=x.index,columns=x.columns)')
    with pytest.raises(ValueError,match='expanded axes'):synthetic_check(source,['close'])


@pytest.mark.parametrize('kind,expression', [
    ('conditional_ols', 'etf_conditional_ols(x, x, x.gt(0), 20, 10)'),
    ('rolling_spearman', 'etf_rolling_spearman(x, x, 20, 10)'),
])
def test_repair_view_omits_owned_helper_and_reembeds_identical_sealed_program(kind, expression):
    source = candidate('    x=panels["close"]\n    return ' + expression)
    sealed = embed_kernel(source, kind)
    view = editable_candidate_source(sealed, kind)
    assert 'def etf_' not in view
    assert expression in view
    assert ast_identity(embed_kernel(view, kind)) == ast_identity(sealed)
    assert synthetic_check(embed_kernel(view, kind), ['close'])['status'] == 'PASS'
    altered = sealed.replace('    import numpy as np\n', '')
    with pytest.raises(ValueError, match='differs'):
        editable_candidate_source(altered, kind)
    with pytest.raises(ValueError, match='differs'):
        embed_kernel(altered, kind)


def ast_identity(source):
    import ast
    return ast.dump(ast.parse(source), include_attributes=False)


def test_repair_request_keeps_owned_kernel_out_of_editable_original(monkeypatch, tmp_path):
    import json
    import run_etf_autoresearch_campaign as campaign
    source = candidate('    x=panels["close"]\n    return etf_conditional_ols(x, x, x.gt(0), 20, 10)')
    sealed = embed_kernel(source, 'conditional_ols')
    context = {'repair_only': True, 'original_source': sealed,
               'assigned_family_plan': {'math_kernel': 'conditional_ols', 'direction': 1}}
    def model(prompt, schema, directory, model, role):
        payload = json.loads(prompt.split('\n\n', 1)[1])
        assert 'def etf_conditional_ols' not in payload['original_source']
        assert 'def etf_conditional_ols' in payload['math_kernel_contract']['source']
        assert payload['assigned_family_plan']['direction'] == 1
        return {'rationale': 'unchanged statistic', 'source_code': payload['original_source']}
    monkeypatch.setattr(campaign, 'model_json', model)
    response = campaign.propose_with_codex(context, tmp_path, 'gpt-6-luna')
    assert context['original_source'] == sealed
    assert ast_identity(embed_kernel(response['source_code'], 'conditional_ols')) == ast_identity(sealed)


def test_synthetic_catches_global_ranks_and_preserves_sparse_candidates():
    with pytest.raises(AssertionError):synthetic_check(candidate('    return panels["close"].rank(axis=0)'),['close'])
    sparse=candidate('    return panels["close"].rolling(250,min_periods=250).mean()')
    result=synthetic_check(sparse,['close'])
    assert result['status']=='PASS' and result['finite_cells']==0
