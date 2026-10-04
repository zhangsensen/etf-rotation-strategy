import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/research'))
from etf_autoresearch_plan_review import freeze_plan_review,admit_reviewed_plans


def specs():
    return [{'plan_id':'p1','family_key':'gold_alias','mode':'open'},
            {'plan_id':'p2','family_key':'fx_alias','mode':'open'},
            {'plan_id':'p3','family_key':'renamed_old','mode':'open'}]


def decisions():
    return {s['plan_id']:{'plan_id':s['plan_id'],'canonical_family':'recovery' if i<2 else 'old',
                         'kind':'NEW_FAMILY','math_kernel':'custom','reason':'same mechanism'}
            for i,s in enumerate(specs())}


def test_review_frozen_receipt_is_reused_and_context_drift_fails(tmp_path):
    calls=[]
    def reviewer(*_):calls.append(1);return decisions()
    ctx={'historical_formal_definitions':[{'family':'old'}]}
    first=freeze_plan_review(specs(),ctx,tmp_path,'gpt-6.1-sol',reviewer)
    assert freeze_plan_review(specs(),ctx,tmp_path,'gpt-6.1-sol',reviewer)==first and len(calls)==1
    with pytest.raises(ValueError,match='context changed'):
        freeze_plan_review(specs(),{},tmp_path,'gpt-6.1-sol',reviewer)


def test_open_classification_is_advisory_but_technical_invalid_still_rejects():
    rows=specs(); verdicts=decisions()
    verdicts['p1']['kind']='OLD_VARIANT';verdicts['p2']['kind']='BATCH_DUPLICATE'
    verdicts['p3']['kind']='INVALID'
    accepted,rejected=admit_reviewed_plans(rows,verdicts,{'mode':'open',
        'historical_formal_definitions':[{'family':'recovery'}], 'forbidden_family_keys':['recovery']})
    assert len(accepted)==2 and len(rejected)==1
    assert all(s['family_key']=='recovery' for s in accepted)
    assert rejected[0]['reason_code']=='INVALID'


def test_large_review_preserves_exact_history_without_outcomes(tmp_path, monkeypatch):
    import json
    from copy import deepcopy
    import run_etf_autoresearch_campaign as cli
    from etf_autoresearch_plan_review import review_plans
    rows = [{'run_id': f'r{i}', 'candidate': f'c{i}', 'family': 'historical',
             'formula': 'x' * 1077, 'direction': -1, 'required_panels': ['x'],
             'mechanism': 'retrieval hint ' * 10} for i in range(645)]
    context = {'local_trial_definitions': rows, 'local_completed_candidates': [{'ic': .9}],
               'historical_formal_definitions': [
                   {'candidate': f'formal{i}', 'definition_id': f'd{i}', 'family': 'f',
                    'source_type': 'daily', 'raw_formula': 'h' * 100} for i in range(540)]}
    original = deepcopy(context)
    calls = []
    def model(prompt, schema, directory, model_name, role):
        assert model_name == 'gpt-6.1-sol' and role == 'plan_review'
        assert len(prompt) < 900000
        view = json.loads(prompt[prompt.rfind('\n{') + 1:])
        restored = [dict(zip(view['local_trial_definitions_columns'], row))
                    for row in view['local_trial_definitions']]
        assert [(r['run_id'], r['formula'], r['direction']) for r in restored] == [
            (r['run_id'], r['formula'], r['direction']) for r in rows]
        assert 'local_completed_candidates' not in view
        assert all('ic' not in r for r in restored)
        calls.append(prompt)
        return {'decisions': list(decisions().values())}
    monkeypatch.setattr(cli, 'model_json', model)
    assert len(review_plans(specs(), context, tmp_path, 'gpt-6.1-sol')) == 3
    assert len(calls) == 1 and context == original
