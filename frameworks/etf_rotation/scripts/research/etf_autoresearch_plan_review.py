"""One semantic decision per frozen plan, before implementation or labels."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from etf_autoresearch_diversity import normalize_family, historical_family_keys
from etf_autoresearch_recovery import atomic
from etf_autoresearch_implementation import KERNEL_SELECTION_GUIDANCE


def review_plans(slots, context, directory, model):
    if model != 'gpt-6.1-sol':
        raise ValueError('plan review requires gpt-6.1-sol')
    from run_etf_autoresearch_campaign import model_json
    fields = {'plan_id': {'type': 'string'}, 'canonical_family': {'type': 'string'},
              'kind': {'type': 'string', 'enum': ['NEW_FAMILY','REFINEMENT','OLD_VARIANT','BATCH_DUPLICATE','INVALID']},
              'math_kernel': {'type': 'string', 'enum': ['custom','conditional_ols','rolling_spearman']},
              'reason': {'type': 'string'}}
    schema = {'type':'object','additionalProperties':False,'required':['decisions'],
              'properties':{'decisions':{'type':'array','items':{'type':'object',
                            'additionalProperties':False,'required':list(fields),'properties':fields}}}}
    # No historical IC, HAC or outcomes are necessary to decide mechanism identity.
    payload = {'plans': [{k:v for k,v in slot.items() if k != 'parent'} for slot in slots],
               'historical_formal_definitions': context.get('historical_formal_definitions', []),
               'local_trial_definitions': context.get('local_trial_definitions', []),
               'known_families': sorted(historical_family_keys(context)),
               'allowed_profiles': context.get('allowed_profiles', {})}
    from etf_autoresearch_context import compact_review_context, tabulate_history
    atomic(Path(directory) / 'review_context.json', payload)
    payload = compact_review_context(payload)
    prefix = (
        'Check frozen ETF plans for technical feasibility before implementation. This is OPEN search: '
        'family classification is descriptive only. OLD_VARIANT, BATCH_DUPLICATE and same-family '
        'siblings remain eligible; semantic similarity, rank overlap, historical weakness or absence '
        'of a prescribed parent are not rejection reasons. Use INVALID only for a concrete unavailable '
        'input, timing, algebra or frozen-direction inconsistency. Verify supplied panel semantics, '
        'including carried NAV premium versus current close. Do not calculate outcomes, judge expected '
        'IC or read market files. Assign canonical_family as an index label and choose the mathematical '
        'kernel matching the formula without changing it. No family quota or cooldown applies. Exact '
        'duplicates require the controller score/input-contract check. Return one decision per plan_id.\n')
    prefix = KERNEL_SELECTION_GUIDANCE + '\n' + prefix
    prompt = prefix + json.dumps(payload, ensure_ascii=False)
    if len(prompt) > 875000:
        tabulate_history(payload)
        prompt = prefix + json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    reply = model_json(prompt,schema,Path(directory),model,'plan_review')['decisions']
    if len(reply) != len(slots) or {d['plan_id'] for d in reply} != {s['plan_id'] for s in slots}:
        raise ValueError('plan review must cover each plan exactly once')
    return {d['plan_id']: {**d,'reviewer_model':model} for d in reply}


def admit_reviewed_plans(slots, decisions, context):
    accepted, rejected = [], []
    aliases = context.get('aliases', {})
    def canonical(value):
        key, visited = normalize_family(value), set()
        while key in aliases and key not in visited:
            visited.add(key);key=normalize_family(aliases[key])
        return key
    for slot in slots:
        decision = decisions[slot['plan_id']]
        family = canonical(decision['canonical_family'])
        reason = 'INVALID' if not family or decision['kind'] == 'INVALID' else None
        if reason:
            rejected.append({'spec':slot,'decision':decision,'reason_code':reason})
            continue
        item=deepcopy(slot)
        item.update(family_key=family, math_kernel=decision['math_kernel'], plan_review=decision)
        item.pop('parent_contract',None)
        accepted.append(item)
    return accepted,rejected


def freeze_plan_review(slots, context, directory, model, reviewer=review_plans):
    """Resumes reuse the immutable decision; changed context cannot silently reclassify."""
    directory=Path(directory);directory.mkdir(exist_ok=True)
    request={'slots':slots,'context':context,'model':model}
    fingerprint=sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
    path=directory/'decision.json'
    if path.exists():
        receipt=json.loads(path.read_text())
        if receipt['request_sha256'] != fingerprint:
            raise ValueError('plan review frozen context changed')
    else:
        decisions=reviewer(slots,context,directory,model) if slots else {}
        if len(decisions)!=len(slots) or set(decisions)!={s['plan_id'] for s in slots}:
            raise ValueError('plan review must cover each plan exactly once')
        receipt={'request_sha256':fingerprint,'decisions':decisions}
        atomic(path,receipt)
    return admit_reviewed_plans(slots,receipt['decisions'],context)
