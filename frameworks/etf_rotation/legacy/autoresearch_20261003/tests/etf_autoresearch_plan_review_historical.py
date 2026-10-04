import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/research'))
from etf_autoresearch_plan_review import freeze_plan_review,admit_reviewed_plans


def specs():
    return [{'plan_id':'p1','family_key':'gold_alias','mode':'explore'},
            {'plan_id':'p2','family_key':'fx_alias','mode':'explore'},
            {'plan_id':'p3','family_key':'renamed_old','mode':'explore'}]


def decisions():
    return {s['plan_id']:{'plan_id':s['plan_id'],'canonical_family':'recovery' if i<2 else 'old',
                         'kind':'NEW_FAMILY','math_kernel':'custom','reason':'same mechanism'}
            for i,s in enumerate(specs())}


def test_family_identity_collapses_aliases_before_source_generation():
    admitted,skipped=admit_reviewed_plans(specs(),decisions(),{'historical_formal_definitions':[{'family':'old'}]})
    assert [s['family_key'] for s in admitted]==['recovery']
    assert [s['reason_code'] for s in skipped]==['RESERVED_OR_SAME_FAMILY','OLD_VARIANT']


def test_review_frozen_receipt_is_reused_and_context_drift_fails(tmp_path):
    calls=[]
    def reviewer(*_):calls.append(1);return decisions()
    ctx={'historical_formal_definitions':[{'family':'old'}]}
    first=freeze_plan_review(specs(),ctx,tmp_path,'gpt-5.6-sol',reviewer)
    assert freeze_plan_review(specs(),ctx,tmp_path,'gpt-5.6-sol',reviewer)==first and len(calls)==1
    with pytest.raises(ValueError,match='context changed'):
        freeze_plan_review(specs(),{},tmp_path,'gpt-5.6-sol',reviewer)


def test_completed_local_family_cannot_be_renamed_as_new():
    admitted, skipped = admit_reviewed_plans(specs()[2:], {'p3': decisions()['p3']},
        {'local_trial_definitions': [{'family': 'old', 'status': 'COMPLETED'}]})
    assert not admitted and skipped[0]['reason_code'] == 'OLD_VARIANT'


def test_open_classification_is_advisory_but_technical_invalid_still_rejects():
    rows=specs(); verdicts=decisions()
    verdicts['p1']['kind']='OLD_VARIANT';verdicts['p2']['kind']='BATCH_DUPLICATE'
    verdicts['p3']['kind']='INVALID'
    accepted,rejected=admit_reviewed_plans(rows,verdicts,{'mode':'open',
        'historical_formal_definitions':[{'family':'recovery'}], 'forbidden_family_keys':['recovery']})
    assert len(accepted)==2 and len(rejected)==1
    assert all(s['family_key']=='recovery' for s in accepted)
    assert rejected[0]['reason_code']=='INVALID'
