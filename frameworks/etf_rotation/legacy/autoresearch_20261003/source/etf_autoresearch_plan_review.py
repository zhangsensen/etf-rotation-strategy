"""One semantic decision per frozen plan, before implementation or labels."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from etf_autoresearch_diversity import normalize_family, historical_family_keys
from etf_autoresearch_recovery import atomic
from etf_autoresearch_implementation import KERNEL_SELECTION_GUIDANCE


def review_plans(slots, context, directory, model):
    if model != 'gpt-5.6-sol':
        raise ValueError('plan review requires gpt-5.6-sol')
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
    from etf_autoresearch_context import compact_review_context
    atomic(Path(directory) / 'review_context.json', payload)
    payload = compact_review_context(payload)
    prompt = ('Classify these frozen ETF formulas BEFORE source implementation. Do not implement factors, '
              'read market files, compute outcomes or judge expected IC. Assign source-independent canonical '
              'families using the historical definitions and every sibling plan. Different profiles, windows, '
              'weights, absolute/squared transforms and sign conditioning alone are old-family variants. '
              'Use NEW_FAMILY only for a defensible distinct information channel; reuse known keys for old '
              'mechanisms even when the proposer invented a new name. Collapse same-channel batch siblings. '
              'REFINEMENT requires the assigned parent and preserves its effective raw-score * direction '
              'orientation; compare the supplied parent source, not just direction constants. Reject an '
              'inconsistent formula/hypothesis or unavailable input with INVALID; weak economic efficacy '
              'alone is not invalid. Select conditional_ols for a conditional population slope and '
              'rolling_spearman for ranks recomputed inside trailing windows; custom otherwise. Kernel '
              'selection must not change the declared formula. Return one decision per plan_id. No source '
              'exists yet: this decision freezes family identity for subsequent technical review.\n' +
              json.dumps(payload,ensure_ascii=False))
    if context.get('mode') == 'open':
        prompt = (
            'Check frozen ETF plans for technical feasibility before implementation. This is OPEN search: '
            'family classification is descriptive only. OLD_VARIANT, BATCH_DUPLICATE and same-family '
            'siblings remain eligible; semantic similarity, rank overlap, historical weakness or absence '
            'of a prescribed parent are not rejection reasons. Use INVALID only for a concrete unavailable '
            'input, timing, algebra or frozen-direction inconsistency. Verify supplied panel semantics, '
            'including carried NAV premium versus current close. Do not calculate outcomes, judge expected '
            'IC or read market files. Assign canonical_family as an index label and choose the mathematical '
            'kernel matching the formula without changing it. No family quota or cooldown applies. Exact '
            'duplicates require the controller score/input-contract check. Return one decision per plan_id.\n' +
            json.dumps(payload,ensure_ascii=False))
    prompt = KERNEL_SELECTION_GUIDANCE + '\n' + prompt
    reply = model_json(prompt,schema,Path(directory),model,'plan_review')['decisions']
    if len(reply) != len(slots) or {d['plan_id'] for d in reply} != {s['plan_id'] for s in slots}:
        raise ValueError('plan review must cover each plan exactly once')
    return {d['plan_id']: {**d,'reviewer_model':model} for d in reply}


def admit_reviewed_plans(slots, decisions, context):
    accepted, rejected, seen = [], [], set()
    old = historical_family_keys(context)
    old.update(normalize_family(row.get('canonical_family') or row.get('family') or row.get('family_key'))
               for row in context.get('local_trial_definitions', []) if row.get('status') == 'COMPLETED')
    blocked = {normalize_family(k) for k in context.get('forbidden_family_keys', [])}
    aliases = context.get('aliases', {})
    def canonical(value):
        key, visited = normalize_family(value), set()
        while key in aliases and key not in visited:
            visited.add(key);key=normalize_family(aliases[key])
        return key
    old, blocked = {canonical(k) for k in old}, {canonical(k) for k in blocked}
    for slot in slots:
        decision = decisions[slot['plan_id']]
        family = canonical(decision['canonical_family'])
        kind = decision['kind'];refine=slot.get('mode')=='refine'
        reason = None
        if context.get('mode') == 'open':
            if not family or kind == 'INVALID':
                reason = 'INVALID'
        elif not family or kind in {'OLD_VARIANT','BATCH_DUPLICATE','INVALID'}:
            reason = kind
        elif (refine and (kind!='REFINEMENT' or family!=canonical(slot['family_key']))) or (not refine and kind!='NEW_FAMILY'):
            reason = 'MODE_OR_PARENT_MISMATCH'
        elif family in seen or family in blocked:
            reason = 'RESERVED_OR_SAME_FAMILY'
        elif not refine and family in old:
            reason = 'OLD_VARIANT'
        if reason:
            rejected.append({'spec':slot,'decision':decision,'reason_code':reason})
            continue
        seen.add(family)
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
