"""Unified ETF discovery: batched exploration, parent refinement and persistent memory."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
import datetime
from pathlib import Path

from audit_etf_autoresearch_novelty import require_latest_inventory
from cycle_etf_autoresearch import cycle, compare
from etf_autoresearch_inputs import describe_profiles, describe_feature_diagnostics
from etf_autoresearch_diversity import plan_families, plan_profile_lanes, family_history, normalize_family, historical_family_keys, classify_plans, diversity_memory, PlannerResponseError
from etf_autoresearch_library import rebuild_library, context_for_proposer
from etf_autoresearch_score_preflight import check_exact_scores, CandidateScoreError
from etf_autoresearch_plan_review import review_plans, freeze_plan_review
from etf_autoresearch_implementation import embed_kernel, synthetic_check, kernel_binding, KERNEL_SELECTION_GUIDANCE
from run_etf_autoresearch_campaign import (campaign_lock, digest, validate_source,
                                         propose_with_codex, model_json, SCORE_CONTRACT)
from run_etf_autoresearch_ic import ROOT, CANDIDATE, run
from etf_autoresearch_recovery import (atomic, immutable_source, reference_id, evaluation_contract,
    validate_result, validate_preflight_result, seal_result, bounded_call, EvaluationTimeout)
from etf_autoresearch_status import campaign_progress

POLICY = 'workflow_v15_reliable_progress_20261003'


def write_json(path, payload):
    atomic(path, payload)


def progress_event(row):
    """Console/Dagu progress is an outcome summary; full evidence stays on disk."""
    return {key: row.get(key) for key in ('round', 'slot', 'run_id', 'candidate', 'status',
            'ic_recorded', 'ic', 'hac_t', 'n', 'reason_code', 'error') if key in row}


def review_payload(items):
    """Share identical history without truncating any review evidence."""
    shared = items[0].get('historical_formal_definitions', []) if items else []
    candidates = []
    for item in items:
        candidate = dict(item)
        if candidate.get('historical_formal_definitions') == shared:
            candidate.pop('historical_formal_definitions')
        candidates.append(candidate)
    payload = {'shared_historical_formal_definitions': shared, 'candidates': candidates}
    if items and all(item.get('family_history') == items[0].get('family_history') for item in items):
        payload['shared_family_history'] = items[0].get('family_history')
        for candidate in candidates:
            candidate.pop('family_history', None)
    # Old, full histories remain in the frozen plan review receipt. Technical
    # source review only needs the assigned plan, siblings and input contracts.
    if items and all(item.get('mode') == 'open' for item in items):
        for key in ('shared_historical_formal_definitions', 'shared_family_history'):
            payload.pop(key, None)
        for candidate in candidates:
            for key in ('historical_formal_definitions', 'family_history', 'ic', 'hac_t',
                        'n', 'yearly', 'decision', 'nearest', 'prelabel_overlap'):
                candidate.pop(key, None)
    return payload


def review_batch(items, directory, model):
    schema = {'type': 'object', 'additionalProperties': False, 'required': ['reviews'],
              'properties': {'reviews': {'type': 'array', 'items': {
                  'type': 'object', 'additionalProperties': False,
                  'required': ['run_id', 'approved', 'reason', 'canonical_family', 'reason_code', 'repairable'], 'properties': {
                      'canonical_family': {'type': 'string'},
                      'run_id': {'type': 'string'}, 'approved': {'type': 'boolean'},
                      'reason': {'type': 'string'}, 'reason_code': {'type': 'string', 'enum': ['approved', 'technical_mismatch', 'syntax', 'shape', 'field', 'economic_rationale', 'duplicate', 'other']}, 'repairable': {'type': 'boolean'}}}}}}
    prompt = ('Review this frozen ETF discovery batch before any outcome calculation. '
              'Review only provided source, rationale and declared panels. Do not read market files or run code. '
              'Approve technically valid causal scores using provided panels through D close, with no labels/I/O and fixed ex-ante direction. Weak economic plausibility or expected efficacy alone is advisory: approve it with reason_code=economic_rationale. Reject a concrete technical or direction mismatch. Refinements must preserve parent family '
              'and direction, comparing the supplied parent_contract source and metadata, not just family strings. '
              'Canonical labels describe the proposed source; a rejected child must not relabel its parent. '
              'Verify that RAW score multiplied once by DIRECTION expresses the declared hypothesis. Reject applying the predictive sign twice; a minus in the raw measurement is not itself a defect. '
              'Verify per-ETF DataFrame shape, not cross-column reduction. '
              'Use available_inputs.review_contract for input formulas and availability; do not infer semantics from names. IC is the objective; do not invent profitability or t-statistic gates. '
              'Economic family diversity is the first scheduling priority. Assign canonical_family by economic mechanism, '
              'reusing historical family keys when equivalent. Different windows, thresholds, weighting, names or '
              'data profiles or opposite signs alone do not establish a new family. Judge against the provided family plan and history. '
              'Reject cosmetic duplicates in this batch. Canonical family identification is a review judgment, '
              'not an empirical independence claim. If repair_original_source is provided, verify the same economic formula, window, direction and population; only an implementation defect may change. Weak economic conviction is advisory; technical mismatch rejects. Return reason_code and repairable, one decision per run_id.\n'
              'When family_plan.plan_review exists, family identity was frozen BEFORE implementation. '
              'For source implementing that plan, return its frozen family_key verbatim; do not redo semantic '
              'family selection. If source departs from that formula, reject technical_mismatch. '
              'synthetic_implementation_check is execution evidence, not economic evidence. '
              'Candidates without family_history inherit shared_family_history.\n'
              + 'Candidates without historical_formal_definitions inherit shared_historical_formal_definitions in full.\n'
              + json.dumps(review_payload(items), ensure_ascii=False))
    if items and all(item.get('mode') == 'open' for item in items):
        schema['properties']['reviews']['items']['properties']['reason_code']['enum'].remove('duplicate')
        prompt = (
            'Review candidate code against its frozen formula, direction and available_inputs.review_contract. '
            'This is OPEN search. Family labels, OLD_VARIANT/BATCH_DUPLICATE planning annotations, semantic '
            'similarity, rank overlap and historical weak/negative results are NOT rejection grounds. '
            'Do not require a new family or an improvement quota. Approve technically valid causal scores; '
            'reject only concrete syntax, shape, panel semantics, timing, formula or frozen-direction defects. '
            'Exact duplicate reuse belongs to the controller full-contract score check. Preserve frozen '
            'family_key as an index label. Verify RAW times DIRECTION expresses the predeclared hypothesis '
            'once. Read only provided code and input contracts, not market files or outcomes. Weak expected '
            'efficacy is advisory, not a gate. For repairs verify unchanged formula/window/direction and '
            'population, fixing implementation only. Shared histories apply to every candidate; return '
            'one verdict per run_id with reason_code and repairable.\n' +
            json.dumps(review_payload(items), ensure_ascii=False))
    prompt = KERNEL_SELECTION_GUIDANCE + '\n' + prompt
    if len(prompt) > 900000 and len(items) > 1:
        from copy import deepcopy
        merged = {}
        siblings = [{k: item.get(k) for k in ('run_id', 'planned_family', 'family_plan', 'rationale')}
                    for item in items]
        for index, item in enumerate(items):
            part = deepcopy(item)
            part['batch_siblings'] = siblings
            part_dir = directory / f'part_{index + 1}'
            part_dir.mkdir(exist_ok=True)
            merged.update(review_batch([part], part_dir, model))
        return merged
    reply = model_json(prompt, schema, directory, model, 'review')
    reviews = reply['reviews']
    if len(reviews) != len(items) or {r['run_id'] for r in reviews} != {r['run_id'] for r in items}:
        raise ValueError('review must cover every frozen proposal exactly once')
    if any(r['approved'] and not normalize_family(r['canonical_family']) for r in reviews):
        raise ValueError('approved proposals require a nonempty economic family')
    return {r['run_id']: {**r, 'reviewer_model': model} for r in reviews}


def parent_contract(source, spec):
    """Label-free frozen parent evidence for mechanical and economic review."""
    metadata = validate_source(source)
    return {'source_code': source, 'source_sha256': digest(source.encode()),
            'candidate': metadata['CANDIDATE_ID'], 'raw_family': metadata['FAMILY'],
            'planned_canonical_family': spec['family_key'],
            'direction': metadata['DIRECTION'], 'description': metadata['DESCRIPTION']}


def formula_hash(source):
    """Diagnostic signed formula identity; input/evaluation equivalence is checked separately."""
    import ast
    tree = ast.parse(source)
    tree.body = [n for n in tree.body if not (isinstance(n, ast.Assign) and
                 any(isinstance(t, ast.Name) and t.id in {'CANDIDATE_ID', 'DESCRIPTION', 'FAMILY'}
                     for t in n.targets)) and not (isinstance(n, ast.Expr) and
                 isinstance(n.value, ast.Constant) and isinstance(n.value.value, str))]
    return digest(ast.dump(tree, include_attributes=False).encode())


def validate_reopens(records, campaign_id, rounds):
    """A review grants one targeted trial, never a permanent streak reset."""
    if not isinstance(records, list):
        raise ValueError('reopen records must be a list')
    seen = set()
    for record in records:
        required = ('family', 'parent_run', 'new_evidence', 'review_record', 'reviewer')
        if (not isinstance(record, dict) or any(not isinstance(record.get(k), str) or not record[k].strip() for k in required)
                or record.get('approved') is not True or record.get('campaign_id') != campaign_id
                or type(record.get('round')) is not int or not 1 <= record['round'] <= rounds
                or record['family'] != normalize_family(record['family'])):
            raise ValueError('reopen requires targeted family/parent, new evidence and approved review record')
        review_path = Path(record['review_record'])
        if not review_path.is_file() or digest(review_path.read_bytes()) != record.get('review_sha256'):
            raise ValueError('reopen review record hash mismatch')
        key = (record['round'], record['family'])
        if key in seen:
            raise ValueError('duplicate reopen target')
        seen.add(key)
    return records


def workflow(campaign_id, rounds, width, profiles, output_root, inventory, runs_root,
             model='gpt-6-luna', reviewer='gpt-5.6-sol', mode='open',
             propose=propose_with_codex, review=review_batch, evaluate=cycle, seed_run=run, resume=False, planner=None, diagnostics=None, refinement_planner=None, score_check=None, reopen_records=None,
             plan_review=None, implementation_check=None):
    if not campaign_id.replace('_', '').replace('-', '').isalnum():
        raise ValueError('invalid campaign identifier')
    if not 1 <= rounds <= 100 or not 1 <= width <= 8:
        raise ValueError('rounds must be 1..100 and candidates per round 1..8')
    if model == reviewer:
        raise ValueError('proposer and master reviewer must be separate model roles')
    if review is review_batch and reviewer != 'gpt-5.6-sol':
        raise ValueError('new Codex reviews require gpt-5.6-sol')
    score_check = score_check or (check_exact_scores if evaluate is cycle else None)
    plan_review = plan_review or (review_plans if review is review_batch else None)
    implementation_check = implementation_check or (synthetic_check if propose is propose_with_codex else None)
    output_root, inventory, runs_root = map(lambda p: Path(p).resolve(), (output_root, inventory, runs_root))
    with campaign_lock(output_root):
        require_latest_inventory(inventory, runs_root)
        catalog = describe_profiles(ROOT)
        for profile in profiles:
            if profile not in catalog or not catalog[profile]['available'] or not catalog[profile].get('approved', True):
                raise ValueError(f'unavailable approved source profile: {profile}')
        directory = output_root / 'campaigns' / campaign_id
        directory.mkdir(parents=True, exist_ok=resume)
        rows = []
        summary = {'schema_version': 'unified_etf_autoresearch_v6', 'campaign_id': campaign_id,
                   'requested_rounds': rounds, 'candidates_per_round': width, 'profiles': profiles,
                   'mode': mode, 'model': model, 'reviewer': reviewer, 'rounds': rows, 'source_catalog': catalog,
                   'event_sequence': family_history(output_root).get('next_event_sequence', 1),
                   'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'reopen_records': validate_reopens(reopen_records or [], campaign_id, rounds),
                   'round_records': [], 'scheduling_policy': POLICY,
                   'formal_registration': False, 'evidence': 'adaptive seen-history discovery only',
                   'status': 'RUNNING', 'empty_rounds': 0, 'evaluated_rounds': 0,
                   'positive_ic_count': 0, 'diagnostics': diagnostics}
        if resume and (directory / 'summary.json').exists():
            previous = json.loads((directory / 'summary.json').read_text())
            for key in ('schema_version', 'scheduling_policy', 'requested_rounds', 'candidates_per_round', 'profiles', 'mode', 'model'):
                if previous[key] != summary[key]:
                    raise ValueError(f'resume contract changed: {key}')
            if reopen_records is not None and previous.get('reopen_records', []) != summary['reopen_records']:
                raise ValueError('resume reopening records changed')
            validate_reopens(previous.get('reopen_records', []), campaign_id, rounds)
            summary = previous
            if previous['reviewer'] != reviewer:
                summary.setdefault('reviewer_changes', []).append({'from': previous['reviewer'], 'to': reviewer,
                    'from_round': previous.get('completed_rounds', 0) + 1})
            summary['reviewer'] = reviewer
            summary['status'] = 'RUNNING'
            rows = summary['rounds']
            diagnostics = summary.get('diagnostics')
        def reopened(family, parent_run, number):
            return next((r for r in summary.get('reopen_records', []) if r['family'] == family
                         and r['parent_run'] == parent_run and r['round'] == number), None)

        def save():
            import datetime
            summary['last_progress_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            summary['proposed_count'] = sum(bool(r.get('source_path')) for r in rows)
            summary['evaluated_count'] = sum(r['status'] == 'COMPLETED' for r in rows)
            summary['rejected_count'] = sum(r['status'] == 'REJECTED' for r in rows)
            summary['distinct_evaluated_families'] = len({r.get('canonical_family', r.get('family')) for r in rows if r['status'] == 'COMPLETED'})
            summary['diversity_skipped_count'] = sum(r['status'] == 'DIVERSITY_SKIPPED' for r in rows)
            summary['failed_count'] = sum(r['status'] == 'FAILED' for r in rows)
            summary['empty_rounds'] = sum(r.get('status') == 'EMPTY' for r in summary.get('round_records', []))
            summary['evaluated_rounds'] = len({r['round'] for r in rows if r['status'] == 'COMPLETED'})
            summary['positive_ic_count'] = sum(r.get('ic', 0) > 0 for r in rows if r['status'] == 'COMPLETED')
            summary['numeric_ic_count'] = sum(isinstance(r.get('ic'), (int, float)) and math.isfinite(r['ic'])
                                              for r in rows if r.get('ic_recorded'))
            summary['exact_score_duplicates_skipped'] = sum(r.get('reason_code') == 'EXACT_SCORE_DUPLICATE' for r in rows)
            summary['evaluated_explorations'] = sum(r['status'] == 'COMPLETED' and r.get('mode') == 'explore' for r in rows)
            summary['evaluated_open_candidates'] = sum(r['status'] == 'COMPLETED' and r.get('mode') == 'open' for r in rows)
            summary['evaluated_refinements'] = sum(r['status'] == 'COMPLETED' and r.get('mode') == 'refine' for r in rows)
            summary['high_overlap_evaluated_count'] = sum(r['status'] == 'COMPLETED' and r.get('novelty_diagnostic') == 'HIGH_SCORE_OVERLAP' for r in rows)
            summary['diversity_note'] = 'Mechanism family counts are not independent signal counts; overlap is diagnostic, not an IC gate.'
            summary['refinements_improved'] = sum(r.get('mode') == 'refine' and r.get('keep') is True for r in rows)
            plans = [json.loads(p.read_text()) for p in sorted(directory.glob('plan_r*.json'))]
            lanes = [lane for p in sorted(directory.glob('planning_r*/planning_lanes.json'))
                     for lane in json.loads(p.read_text())['lanes']]
            summary['planning_diagnostics'] = {
                'open_batch_requests': sum(len(p.get('planning_attempts', [])) for p in plans) if mode == 'open' else 0,
                'source_requests': len(lanes),
                'empty_source_requests': sum(not l['specs'] and not l.get('error') for l in lanes),
                'source_request_errors': sum(bool(l.get('error')) for l in lanes),
                'profiles_requested': sorted({l['profile'] for l in lanes}),
                'search_foci_requested': sorted({l['mechanism_focus'] for l in lanes if l.get('mechanism_focus')}),
                'classified_before_implementation': sum(len(p.get('classified_before_implementation', [])) for p in plans),
                'note': 'Source/focus coverage is search effort, not independent factor or economic family count.'}
            progress = campaign_progress(summary, directory)
            summary['progress'] = progress
            summary['planning_diagnostics']['planning_error_rounds'] = progress['planning_error_rounds']
            evaluated = [r for r in rows if r['status'] == 'COMPLETED']
            summary['diversity_results'] = {
                'open_search_families': sorted({r.get('canonical_family', r['family']) for r in evaluated if r['mode'] == 'open'}),
                'exploration_families': sorted({r.get('canonical_family', r['family']) for r in evaluated if r['mode'] == 'explore'}),
                'refinement_families': sorted({r.get('canonical_family', r['family']) for r in evaluated if r['mode'] == 'refine'}),
                'prelabel_score_overlap': [{"run_id": r['run_id'], **r['prelabel_overlap']} for r in rows if r.get('prelabel_overlap')],
                'independent_signal_count': None,
                'note': 'New family labels and low pairwise overlap do not certify independent information.'}
            write_json(directory / 'summary.json', summary)
            rebuild_library(output_root, inventory)
        save()
        seeds = {}
        contract = evaluation_contract(diagnostics) if seed_run is run else {}
        reference_index_path = directory / 'reference_index.json'
        reference_index = json.loads(reference_index_path.read_text()) if reference_index_path.exists() else {}
        parents = {}
        seen = set()
        memory = context_for_proposer(output_root, inventory)
        for old in memory['local_completed_candidates']:
            path = Path(old['code_path']) if old.get('code_path') else None
            if path and path.is_file():
                saved = json.loads((output_root / old['run_id'] / 'result.json').read_text())
                if saved.get('candidate_sha256') and digest(path.read_bytes()) != saved['candidate_sha256']:
                    continue
                seen.add(formula_hash(path.read_text()))
                if old.get('ic', 0) > 0 and old.get('parent_eligible'):
                    profile = old.get('input_profile') or 'daily'
                    key = (profile, old['family'])
                    if key not in parents or old['ic'] > parents[key]['ic']:
                        parents[key] = old
        def reference(profile, source, identity):
            name = reference_id(campaign_id, profile, source, contract)
            if name in seeds:
                return seeds[name]
            source_hash = digest(source.encode())
            path = Path(reference_index[name]['result_dir']) if name in reference_index else output_root / name
            # Legacy sequential names are read-only and matched by content, never by ordinal.
            if name not in reference_index:
                for result_file in sorted(output_root.glob(f'{campaign_id}_seed_*/result.json')):
                    old = json.loads(result_file.read_text())
                    if old.get('candidate_sha256') == source_hash and old.get('input_profile', 'daily') == profile:
                        if seed_run is run:
                            validate_result(result_file.parent, source_hash, profile, ROOT, legacy=True)
                        path = result_file.parent
                        break
            snapshot = directory / f'{name}.py'
            immutable_source(snapshot, source)
            if (path / 'result.json').exists():
                if seed_run is run:
                    validate_result(path, source_hash, profile, ROOT, legacy=True)
                else:
                    result = json.loads((path / 'result.json').read_text())
                    if result.get('candidate_sha256', source_hash) != source_hash:
                        raise ValueError('reference source mismatch')
            else:
                if path.exists():
                    raise RuntimeError('incomplete reference evaluation; manual inspection required')
                if seed_run is run:
                    bounded_call(seed_run, name, output_root, snapshot, profile)
                    seal_result(path)
                else:
                    seed_run(name, output_root, snapshot, profile)
                write_json(path / 'reference_seed.json', {'parent_identity': identity})
            reference_index[name] = {'result_dir': str(path), 'source_path': str(snapshot),
                                     'source_sha256': source_hash, 'profile': profile}
            write_json(reference_index_path, reference_index)
            seeds[name] = path
            return path
        try:
            for number in range(summary.get('completed_rounds', 0) + 1, rounds + 1):
                require_latest_inventory(inventory, runs_root)
                memory = context_for_proposer(output_root, inventory)
                history = family_history(output_root)
                history['diversity_memory'] = diversity_memory(memory)
                recent = set(history['recent_round_families']) if mode not in {'refine', 'open'} else set()
                recent -= {r['family'] for r in summary.get('reopen_records', []) if r['round'] == number}
                plan_path = directory / f'plan_r{number:02d}.json'
                if plan_path.exists():
                    plan = json.loads(plan_path.read_text())
                else:
                    refinement_budget = width if mode == 'refine' else min(1, width // 4) if mode == 'mixed' else 0
                    refinements, reserved = [], set()
                    ordered_parents = sorted(parents.values(), key=lambda item: (
                        history['family_attempt_counts'].get(normalize_family(item['family']), 0) +
                        history['diversity_memory']['family_penalties'].get(normalize_family(item.get('canonical_family') or item['family']), 0),
                        -item['ic'], item['run_id']))
                    for parent in ordered_parents:
                        raw_family = normalize_family(parent['family'])
                        family = history['aliases'].get(raw_family, raw_family)
                        if (parent.get('input_profile', 'daily') not in profiles or family in recent or
                                family in reserved or (history['unsuccessful_refinements'].get(family, 0) >= 2
                                and not reopened(family, parent['run_id'], number))):
                            continue
                        if len(refinements) >= refinement_budget:
                            break
                        refinements.append({'family_key': family, 'mechanism': parent['family'],
                                            'distinct_from': 'own frozen parent',
                                            'why_distinct': 'refinement, not a new family claim',
                                            'input_profile': parent.get('input_profile') or 'daily',
                                            'mode': 'refine', 'parent': parent})
                        reserved.add(family)
                    request = {**memory, **history, 'campaign_id': campaign_id, 'round': number,
                               'requested_count': min(3, width - len(refinements)) if mode == 'mixed' else width if mode in {'explore', 'open'} else 0,
                               'allowed_profiles': {p: catalog[p] for p in profiles},
                               'mode': 'open' if mode == 'open' else 'explore',
                               'forbidden_family_keys': [] if mode == 'open' else sorted(recent | reserved | historical_family_keys(memory) |
                                                             {k for k, v in history['unsuccessful_refinements'].items() if v >= 2}),
                               'feature_diagnostics': {p: {k: v for k, v in d.items() if k != 'input_manifest'}
                                                       for p, d in (diagnostics or {}).items()}}
                    specs, attempts, classified_out, requested_profiles = [], [], [], []
                    for attempt_no in (1, 2):
                        if not request['requested_count']:
                            break
                        planning_dir = directory / f'planning_r{number:02d}_attempt{attempt_no}'
                        planning_dir.mkdir(exist_ok=True)
                        result_path = planning_dir / 'result.json'
                        marker = planning_dir / 'started.json'
                        if result_path.exists():
                            outcome = json.loads(result_path.read_text())
                        elif marker.exists():
                            outcome = {'specs': [], 'error': 'interrupted planning attempt; inspect saved request before retry',
                                       'service_error': True}
                            write_json(result_path, outcome)
                        else:
                            write_json(marker, {'attempt': attempt_no})
                            try:
                                call_context = {**request, 'planning_attempt': attempt_no,
                                                'requested_count': request['requested_count'] - len(specs),
                                                'profiles_already_requested': requested_profiles,
                                                'planning_feedback': attempts[-1] if attempts else None}
                                proposed = (planner or (plan_families if mode == 'open' else plan_profile_lanes))(call_context, planning_dir, model)
                                if planner is None and any(any(k not in item for k in ('formula', 'direction', 'required_panels')) for item in proposed):
                                    raise ValueError('production planner omitted frozen formula fields')
                                outcome = {'specs': proposed}
                            except Exception as exc:
                                outcome = {'specs': [], 'error': str(exc),
                                           'error_type': type(exc).__name__,
                                           'error_kind': 'INVALID_RESPONSE' if isinstance(exc, PlannerResponseError) else 'SYSTEM_ERROR',
                                           'service_error': not isinstance(exc, PlannerResponseError)}
                            write_json(result_path, outcome)
                        if outcome.get('error') and (outcome.get('error_kind') != 'INVALID_RESPONSE' or attempt_no == 2):
                            summary['status'] = 'PAUSED_SYSTEM_ERROR'
                            summary['system_error'] = f"planner failed in round {number}: {outcome['error']}"
                            summary['round_records'] = [r for r in summary['round_records'] if r['round'] != number]
                            summary['round_records'].append({'round': number, 'status': 'PLANNING_FAILED',
                                'attempt': attempt_no, 'error': outcome['error'], 'path': str(planning_dir),
                                'preserved_proposals': len(specs)})
                            raise RuntimeError('PAUSED_SYSTEM_ERROR: ' + summary['system_error'])
                        accepted, skipped = classify_plans(outcome['specs'], {
                            **request, 'forbidden_family_keys': request['forbidden_family_keys'] +
                            [s['family_key'] for s in specs]})
                        classified_out.extend(skipped)
                        specs.extend(accepted[:request['requested_count'] - len(specs)])
                        lane_path = planning_dir / 'planning_lanes.json'
                        if lane_path.exists():
                            requested_profiles.extend(l['profile'] for l in json.loads(lane_path.read_text())['lanes'])
                        attempts.append({'path': str(planning_dir), 'spec_count': len(outcome['specs']),
                                         'admitted_count': len(accepted), 'classified_out': skipped,
                                         'error': outcome.get('error'), 'error_kind': outcome.get('error_kind'),
                                         'service_error': outcome.get('service_error', False)})
                        if len(specs) >= request['requested_count']:
                            break
                    if len(attempts) == 2 and all(a['service_error'] for a in attempts):
                        summary['status'] = 'PAUSED_SYSTEM_ERROR'
                        summary['system_error'] = 'planner service failed twice; no candidate labels opened'
                        raise RuntimeError(summary['system_error'])
                    # Independently budgeted parent work never fills unused exploration slots.
                    frozen_refinements = []
                    for index, refinement in enumerate(refinements):
                        parent = refinement['parent']
                        parent_source = Path(parent['code_path']).read_text()
                        ref_dir = directory / f'refinement_plan_r{number:02d}_{index + 1}'
                        ref_dir.mkdir(exist_ok=True)
                        ref_result = ref_dir / 'result.json'
                        ref_marker = ref_dir / 'started.json'
                        if ref_result.exists():
                            outcome = json.loads(ref_result.read_text())
                        elif ref_marker.exists():
                            outcome = {'specs': [], 'error': 'interrupted refinement planning; not repeated'}
                            write_json(ref_result, outcome)
                        else:
                            write_json(ref_marker, {'parent_run': parent['run_id']})
                            ref_request = {**request, 'requested_count': 1, 'mode': 'refine',
                                           'forbidden_family_keys': [],
                                           'allowed_profiles': {refinement['input_profile']: catalog[refinement['input_profile']]},
                                           'assigned_family': refinement['family_key'],
                                           'reopen_record': reopened(refinement['family_key'], parent['run_id'], number),
                                           'parent_contract': parent_contract(parent_source, refinement)}
                            try:
                                planned = (refinement_planner or plan_families)(ref_request, ref_dir, model)
                                if len(planned) > 1:
                                    raise ValueError('only one refinement per assigned parent')
                                for item in planned:
                                    if (item.get('family_key') != refinement['family_key'] or
                                            item.get('input_profile') != refinement['input_profile'] or
                                            item.get('direction') != validate_source(parent_source)['DIRECTION']):
                                        raise ValueError('refinement plan changed assigned family, input or direction')
                                    if not item.get('formula') or not item.get('required_panels'):
                                        raise ValueError('refinement plan omitted formula or required panels')
                                outcome = {'specs': planned}
                            except ValueError as exc:
                                outcome = {'specs': [], 'error': str(exc)}
                            except (RuntimeError, TimeoutError) as exc:
                                summary['status'] = 'PAUSED_SYSTEM_ERROR'
                                raise RuntimeError(f'PAUSED_SYSTEM_ERROR: refinement planner unavailable: {exc}') from exc
                            write_json(ref_result, outcome)
                        frozen_refinements.extend({**item, 'mode': 'refine', 'parent': parent,
                                                   'reopen_record': reopened(refinement['family_key'], parent['run_id'], number)} for item in outcome['specs'])
                    refinements = frozen_refinements
                    plan = {'slots': [{**spec, 'mode': 'open' if mode == 'open' else 'explore', 'parent': None} for spec in specs] + refinements,
                            'mode': mode,
                            'planning_disposition': 'NO_ELIGIBLE_PARENT' if mode == 'refine' and not refinements else 'PLANNED',
                            'planning_attempts': attempts,
                            'classified_before_implementation': classified_out,
                            'forbidden_family_keys': sorted(recent), 'historical_family_keys': sorted(historical_family_keys(memory)),
                            'history': history}
                    if plan_review is not None:
                        review_context = {**memory, 'mode': mode, 'allowed_profiles': {p: catalog[p] for p in profiles},
                                          'aliases': history['aliases'], 'forbidden_family_keys': sorted(recent)}
                        # No IC/performance evidence is needed for plan classification.
                        review_context = {k: review_context[k] for k in
                                          ('mode', 'historical_formal_definitions', 'local_trial_definitions',
                                           'allowed_profiles', 'aliases', 'forbidden_family_keys') if k in review_context}
                        submitted = [{**spec, 'plan_id': f'p{i+1:02d}',
                                      'parent_contract': parent_contract(Path(spec['parent']['code_path']).read_text(), spec)
                                      if spec.get('parent') else None} for i, spec in enumerate(plan['slots'])]
                        try:
                            admitted, declined = freeze_plan_review(submitted, review_context,
                                directory / f'plan_review_r{number:02d}', reviewer, plan_review)
                        except Exception as exc:
                            summary['status'] = 'PAUSED_SYSTEM_ERROR'
                            raise RuntimeError(f'PAUSED_SYSTEM_ERROR: frozen plan review failed: {exc}') from exc
                        plan['slots'] = admitted
                        plan['classified_before_implementation'].extend(declined)
                    write_json(plan_path, plan)
                if not plan['slots']:
                    summary.setdefault('round_records', []).append({'round': number, 'status': 'EMPTY',
                                 'reason': plan.get('planning_disposition', 'no admitted proposals after saved planning and review')})
                    summary['completed_rounds'] = number
                    save()
                    continue
                jobs = []
                for slot, spec in enumerate(plan['slots']):
                    profile = spec['input_profile']
                    parent = spec['parent']
                    refine = spec['mode'] == 'refine'
                    source = Path(parent['code_path']).read_text() if parent else CANDIDATE.read_text()
                    run_id = f'{campaign_id}_r{number:02d}_c{slot + 1:02d}'
                    slot_dir = directory / run_id
                    slot_dir.mkdir(exist_ok=resume)
                    row = {'round': number, 'slot': slot + 1, 'run_id': run_id, 'status': 'PROPOSING',
                           'outcome_opened': False, 'ic_recorded': False, 'revisions': [],
                           'mode': spec['mode'], 'input_profile': profile,
                           'planned_family': spec['family_key'], 'family': spec['family_key'], 'family_plan': spec,
                           'parent_run': parent['run_id'] if parent else None,
                           'parent_candidate': parent['candidate'] if parent else None}
                    prior_row = next((r for r in rows if r['run_id'] == run_id), None)
                    if prior_row:
                        row = prior_row
                        spec = row['family_plan']
                        parent = spec.get('parent')
                        refine = row['mode'] == 'refine'
                        source_file = Path(row.get('baseline_source_path', slot_dir / 'parent.py'))
                        if source_file.exists():
                            source = source_file.read_text()
                        if row['status'] in {'BASELINE_PREPARING', 'BASELINE_READY'}:
                            row['status'] = 'FROZEN'
                        if row.get('repair_pending'):
                            row.update(status='FAILED', repair_pending=False, keep=False, reason_code='REPAIR_INTERRUPTED', error='repair interrupted; no second repair issued')
                        if row['status'] in {'OUTCOME_OPENED', 'EVALUATING', 'RESULT_READY'} or (row['status'] == 'PAUSED_SYSTEM_ERROR' and row.get('stage') == 'result_saved'):
                            result_dir = output_root / row['run_id']
                            if (result_dir / 'evaluation_complete.json').exists():
                                validate_result(result_dir, row['candidate_sha256'], row['input_profile'], ROOT)
                                row.update(status='FROZEN', resume_result=True)
                            else:
                                row.update(status='PAUSED_SYSTEM_ERROR', keep=False, error='interrupted after outcome_opened; retained and not replayed')
                        if row['status'] == 'PAUSED_SYSTEM_ERROR':
                            save()
                            raise RuntimeError(f"PAUSED_SYSTEM_ERROR: {row.get('error', 'outcome was already opened')}")
                    else:
                        rows.append(row)
                        (slot_dir / 'parent.py').write_text(source)
                    context = {**memory, 'mode': row['mode'], 'slot': slot + 1,
                               'input_profile': profile, 'available_inputs': catalog[profile],
                               'feature_diagnostics': {k: v for k, v in (diagnostics or {}).get(profile, {}).items() if k != 'input_manifest'},
                               'current_source': source if refine else None,
                               'parent': parent, 'parent_contract': parent_contract(source, spec) if refine else None,
                               'round': number, 'assigned_family_plan': spec,
                               'sibling_family_plans': [{k: v for k, v in item.items() if k != 'parent'} for item in plan['slots']],
                               'scope': '14 ETFs / 8 groups; D close -> D+2/D+7 open; cold cutoff 2026-03-24',
                               'task': 'implement assigned economic mechanism; FAMILY must equal assigned family_key' if not refine else
                                       'improve assigned parent while preserving its family and direction'}
                    jobs.append((row, slot_dir, context, source))
                save()
                # All proposals see the same pre-round evidence; labels open only after the whole review.
                with ThreadPoolExecutor(max_workers=min(width, 4)) as pool:
                    pending = [job for job in jobs if job[0]['status'] == 'PROPOSING']
                    futures = [pool.submit(propose, context, slot_dir, model)
                               for _, slot_dir, context, _ in pending]
                    for (row, slot_dir, context, source), future in zip(pending, futures):
                        checking_implementation = False
                        try:
                            proposal = future.result()
                            snapshot = slot_dir / 'candidate.py'
                            snapshot.write_text(proposal['source_code'])
                            row.update(source_path=str(snapshot), rationale=proposal['rationale'])
                            proposal['source_code'] = embed_kernel(proposal['source_code'], row['family_plan'].get('math_kernel', 'custom'))
                            snapshot.write_text(proposal['source_code'])
                            row['math_kernel_binding'] = kernel_binding(proposal['source_code'], row['family_plan'].get('math_kernel', 'custom'))
                            metadata = validate_source(proposal['source_code'])
                            if implementation_check is not None:
                                checking_implementation = True
                                row['synthetic_implementation_check'] = (
                                    bounded_call(implementation_check, proposal['source_code'], row['family_plan'].get('required_panels', []), timeout=20)
                                    if implementation_check is synthetic_check else implementation_check(proposal['source_code'], row['family_plan'].get('required_panels', [])))
                                checking_implementation = False
                            if row['mode'] in {'explore', 'open'} and normalize_family(metadata['FAMILY']) != row['planned_family']:
                                raise ValueError('candidate deviated from assigned family')
                            expected_direction = row['family_plan'].get('direction')
                            if expected_direction is not None and metadata['DIRECTION'] != expected_direction:
                                raise ValueError('candidate deviated from frozen planned direction')
                            if row['mode'] == 'refine':
                                old = validate_source(source)
                                if (normalize_family(metadata['FAMILY']) not in {normalize_family(old['FAMILY']), normalize_family(row['planned_family'])}
                                        or metadata['DIRECTION'] != old['DIRECTION']):
                                    raise ValueError('refinement changed family or frozen direction')
                            row.update(candidate=metadata['CANDIDATE_ID'], family=metadata['FAMILY'],
                                       candidate_sha256=digest(snapshot.read_bytes()))
                            fingerprint = formula_hash(proposal['source_code'])
                            row['source_formula_seen'] = fingerprint in seen
                            seen.add(fingerprint)
                            row.update(status='FROZEN', candidate=metadata['CANDIDATE_ID'],
                                       family=metadata['FAMILY'], candidate_sha256=digest(snapshot.read_bytes()))
                        except Exception as exc:
                            message = str(exc).lower()
                            if not row.get('source_path'):
                                row.update(status='PAUSED_SYSTEM_ERROR', stage='implementation', error=str(exc), keep=False)
                            elif checking_implementation or isinstance(exc, (SyntaxError, AssertionError, TimeoutError)) or any(token in message for token in ('syntax', 'score function', 'metadata', 'top-level assignment', 'shape', 'return a series', 'math kernel')):
                                row.update(status='FROZEN_WITH_DEFECT', error=str(exc), candidate_sha256=digest(Path(row['source_path']).read_bytes()))
                            else:
                                row.update(status='FAILED', error=str(exc), keep=False)
                save()
                if any(row['status'] == 'PAUSED_SYSTEM_ERROR' for row, *_ in jobs):
                    summary['status'] = 'PAUSED_SYSTEM_ERROR'
                    raise RuntimeError('PAUSED_SYSTEM_ERROR: implementation model failed; frozen peer proposals preserved')
                frozen = [{**row, 'source_code': Path(row['source_path']).read_text(),
                           'score_contract': SCORE_CONTRACT,
                           'family_history': plan['history'],
                           'available_inputs': context['available_inputs'],
                           'feature_diagnostics': context.get('feature_diagnostics'),
                           'parent_contract': context['parent_contract'],
                           'historical_formal_definitions': memory['historical_formal_definitions']}
                          for row, _, context, _ in jobs if row['status'] in {'FROZEN', 'FROZEN_WITH_DEFECT'}]
                batch_dir = directory / f'review_r{number:02d}'
                batch_dir.mkdir(exist_ok=resume)
                review_path = directory / f'review_r{number:02d}.json'
                initial_review_path = directory / f'review_r{number:02d}_initial.json'
                final_review_path = directory / f'review_r{number:02d}_final.json'
                approvals = (json.loads(final_review_path.read_text()) if resume and final_review_path.exists()
                             else json.loads(initial_review_path.read_text()) if resume and initial_review_path.exists()
                             else (review(frozen, batch_dir, reviewer) if frozen else {}))
                if not initial_review_path.exists():
                    write_json(initial_review_path, approvals)
                # Explore slots never backfill with old-family variants. Refinements
                # require their own frozen parent plan before implementation.
                refinement_quota = width if mode == 'refine' else min(1, width // 4) if mode == 'mixed' else 0
                repair_jobs = []
                for row, slot_dir, context, source in jobs:
                    approval = approvals.get(row['run_id'])
                    if row['status'] not in {'FROZEN', 'FROZEN_WITH_DEFECT'} or not approval:
                        continue
                    static_defect = row['status'] == 'FROZEN_WITH_DEFECT'
                    if not static_defect and (approval.get('approved') or not approval.get('repairable', False)):
                        continue
                    if row.get('outcome_opened') or row.get('repair_used'):
                        continue
                    repair_context = {**context, 'repair_only': True, 'original_source': Path(row['source_path']).read_text(),
                                      'original_sha256': row['candidate_sha256'],
                                      'repair_instruction': row.get('error') if static_defect else approval.get('reason'),
                                      'frozen_formula': context['assigned_family_plan'].get('formula'),
                                      'constraint': 'repair syntax/shape/field defect only; preserve formula, direction, family and population'}
                    repair_jobs.append((row, slot_dir, context, source, repair_context, approval))
                for row, slot_dir, context, source, repair_context, approval in repair_jobs:
                    original_path = Path(row['source_path'])
                    original_source = original_path.read_text()
                    row.update(repair_used=True, original_source_path=str(original_path),
                               original_candidate_sha256=row['candidate_sha256'], repair_pending=True)
                    save()
                    repair_dir = slot_dir / 'repair_attempt1'
                    repair_dir.mkdir(exist_ok=True)
                    repair_snapshot = repair_dir / 'proposal.json'
                    try:
                        if repair_snapshot.exists():
                            proposal = json.loads(repair_snapshot.read_text())
                        else:
                            proposal = propose(repair_context, repair_dir, model)
                            write_json(repair_snapshot, proposal)
                        repaired_source = proposal['source_code']
                        repaired_path = slot_dir / 'candidate_repaired.py'
                        repaired_path.write_text(repaired_source)
                        repaired_source = embed_kernel(repaired_source, context['assigned_family_plan'].get('math_kernel', 'custom'))
                        row['math_kernel_binding'] = kernel_binding(repaired_source, context['assigned_family_plan'].get('math_kernel', 'custom'))
                        repaired_path.write_text(repaired_source)
                        row['revisions'].append({'reason_code': approval.get('reason_code'),
                            'original_source_path': str(original_path),
                            'original_sha256': row['original_candidate_sha256'],
                            'repaired_source_path': str(repaired_path), 'repaired_sha256': digest(repaired_source.encode())})
                        repaired_meta = validate_source(repaired_source)
                        if implementation_check is not None:
                            row['synthetic_implementation_check'] = (
                                bounded_call(implementation_check, repaired_source, context['assigned_family_plan'].get('required_panels', []), timeout=20)
                                if implementation_check is synthetic_check else implementation_check(repaired_source, context['assigned_family_plan'].get('required_panels', [])))
                        import ast
                        try:
                            raw_tree = ast.parse(original_source)
                        except SyntaxError:
                            raw_tree = ast.parse(original_source.split("def score", 1)[0])
                        original_meta = {n.targets[0].id: ast.literal_eval(n.value) for n in raw_tree.body
                                         if isinstance(n, ast.Assign) and len(n.targets) == 1
                                         and isinstance(n.targets[0], ast.Name)
                                         and n.targets[0].id in {'FAMILY', 'DIRECTION'}}
                        expected_direction = context['assigned_family_plan'].get('direction', original_meta.get('DIRECTION'))
                        if (repaired_meta['DIRECTION'] != expected_direction or
                                normalize_family(repaired_meta['FAMILY']) != normalize_family(original_meta.get('FAMILY', row['planned_family']))):
                            raise ValueError('repair changed frozen direction or family')
                        fingerprint = formula_hash(repaired_source)
                        row['source_formula_seen'] = fingerprint in seen
                        seen.add(fingerprint)
                        row.update(source_path=str(repaired_path), candidate_sha256=digest(repaired_path.read_bytes()),
                                   candidate=repaired_meta['CANDIDATE_ID'], repaired_source_path=str(repaired_path),
                                   repaired_candidate_sha256=digest(repaired_path.read_bytes()),
                                   rationale=proposal.get('rationale', row.get('rationale')), status='FROZEN')
                    except Exception as exc:
                        row.update(status='FAILED', reason_code='REPAIR_FAILED', error=str(exc), keep=False)
                    finally:
                        row['repair_pending'] = False
                        save()
                needs_final_review = any(r.get('repair_used') and r['status'] == 'FROZEN' for r, *_ in jobs) and not final_review_path.exists()
                if repair_jobs or needs_final_review:
                    repaired_review_dir = directory / f'review_r{number:02d}_repaired'
                    repaired_review_dir.mkdir(exist_ok=True)
                    frozen = [{**row, 'source_code': Path(row['source_path']).read_text(),
                               'score_contract': SCORE_CONTRACT, 'family_history': plan['history'],
                               'repair_original_source': Path(row['original_source_path']).read_text() if row.get('original_source_path') else None,
                               'available_inputs': context['available_inputs'],
                           'feature_diagnostics': context.get('feature_diagnostics'), 'parent_contract': context['parent_contract'],
                               'historical_formal_definitions': memory['historical_formal_definitions']}
                              for row, _, context, _ in jobs if row['status'] == 'FROZEN' and row.get('repair_used')]
                    save()
                    revised_approvals = review(frozen, repaired_review_dir, reviewer) if frozen else {}
                    approvals.update(revised_approvals)
                    write_json(final_review_path, approvals)
                if not final_review_path.exists():
                    write_json(final_review_path, approvals)
                write_json(review_path, approvals)
                refined_admitted = sum(r.get('mode') == 'refine' and r.get('outcome_opened', False) for r, *_ in jobs)
                admitted_families = {r.get('canonical_family') for r, *_ in jobs if r['status'] == 'COMPLETED'}
                for row, slot_dir, context, source in jobs:
                    if row['status'] not in {'FROZEN', 'FROZEN_WITH_DEFECT'}:
                        continue
                    approval = approvals[row['run_id']]
                    row['review'] = approval
                    row['reason_code'] = approval.get('reason_code', 'approved' if approval.get('approved') else 'other')
                    canonical = normalize_family(approval['canonical_family'])
                    row['canonical_family'] = canonical
                    if row['family_plan'].get('plan_review') and approval['approved'] and canonical != row['planned_family']:
                        row.update(status='REJECTED', keep=False, reason_code='FAMILY_REVIEW_DRIFT',
                                   reason='technical reviewer changed the frozen pre-implementation family')
                        save()
                        continue
                    if not approval['approved']:
                        row.update(status='REJECTED', reason=approval['reason'], keep=False)
                        save()
                        continue
                    if row['status'] == 'FROZEN_WITH_DEFECT':
                        row.update(status='REJECTED', reason_code='STATIC_VALIDATION_FAILED',
                                   reason='static validation failed after bounded repair path', keep=False)
                        save()
                        continue
                    if mode != 'open' and (canonical in admitted_families or canonical in plan['forbidden_family_keys'] or
                            (row['mode'] == 'explore' and canonical in plan['historical_family_keys'])):
                        historical = row['mode'] == 'explore' and canonical in plan['historical_family_keys']
                        row.update(status='DIVERSITY_SKIPPED', keep=False,
                                   disposition='DEFERRED_VARIANT' if historical else 'DIVERSITY_SKIPPED',
                                   reason='old family variant deferred; no eligible frozen-parent refinement slot' if historical else
                                   'economic family already explored, reserved or in two-round cooldown')
                        save()
                        continue
                    if row['mode'] == 'refine' and not row.get('outcome_opened'):
                        if history['unsuccessful_refinements'].get(canonical, 0) >= 2 and not reopened(canonical, row.get('parent_run'), number):
                            row.update(status='DIVERSITY_SKIPPED', keep=False, reason_code='REFINEMENT_PAUSED',
                                       reason='two consecutive refinements without improvement; new plan required to reopen')
                            save()
                            continue
                        row['reopen_record'] = reopened(canonical, row.get('parent_run'), number)
                        if refined_admitted >= refinement_quota:
                            row.update(status='DIVERSITY_SKIPPED', keep=False, reason_code='REFINEMENT_QUOTA', reason='refinement evaluation quota already used')
                            save()
                            continue
                        refined_admitted += 1
                    admitted_families.add(canonical)
                    try:
                        path = Path(row['source_path'])
                        if digest(path.read_bytes()) != row['candidate_sha256']:
                            row.update(status='PAUSED_SYSTEM_ERROR', error='frozen source changed after review')
                            save()
                            raise RuntimeError('PAUSED_SYSTEM_ERROR: frozen source changed after review')
                        if score_check is not None and not row.get('resume_result'):
                            row['stage'] = 'score_preflight'
                            save()
                            # No result directory, attempt, baseline or label-open flag yet.
                            prior_scores = context_for_proposer(output_root, inventory)['local_completed_candidates']
                            try:
                                receipt = (bounded_call(score_check, path, row['input_profile'], output_root, prior_scores,
                                                        inventory=inventory, runs_root=runs_root, timeout=900)
                                           if score_check is check_exact_scores else
                                           score_check(path, row['input_profile'], output_root, prior_scores))
                            except CandidateScoreError as exc:
                                row.update(status='FAILED', stage='complete', keep=False,
                                           reason_code='CANDIDATE_SCORE_ERROR', error=str(exc))
                                save()
                                continue
                            except Exception as exc:
                                row.update(status='PAUSED_SYSTEM_ERROR', error=str(exc))
                                save()
                                raise
                            write_json(slot_dir / 'score_preflight.json', receipt)
                            row['score_preflight_path'] = str(slot_dir / 'score_preflight.json')
                            row['score_sha256'] = receipt.get('score_sha256')
                            row['prelabel_overlap'] = receipt.get('score_overlap')
                            if receipt.get('structural_failure'):
                                row.update(status='FAILED', stage='complete', keep=False,
                                           reason_code=receipt['structural_failure'],
                                           rankable_signal_days=receipt['rankable_signal_days'],
                                           reason='no complete rankable signal date; labels not opened')
                                save()
                                continue
                            if receipt.get('duplicate_of'):
                                row.update(status='DUPLICATE', stage='complete', keep=False,
                                           reason_code='EXACT_SCORE_DUPLICATE', duplicate_of=receipt['duplicate_of'],
                                           reason='identical signed scores under the same evaluation contract; see original result')
                                save()
                                continue
                        baseline = None
                        if row['mode'] != 'open':
                            row['status'] = 'BASELINE_PREPARING'
                            row['stage'] = 'baseline'
                            save()
                            try:
                                baseline = reference(row['input_profile'], source, row['parent_candidate'])
                            except Exception as exc:
                                row.update(status='PAUSED_SYSTEM_ERROR', error=f'baseline seed failed: {exc}')
                                save()
                                raise RuntimeError(f'PAUSED_SYSTEM_ERROR: baseline seed failed: {exc}') from exc
                            row.update(status='BASELINE_READY', baseline_path=str(baseline))
                            save()
                        row.update(status='EVALUATING', stage='candidate_evaluation',
                                   outcome_opened=True, candidate_evaluation_started=True)
                        save()
                        eval_error = None
                        try:
                            if row.get('resume_result'):
                                validate_result(output_root / row['run_id'], row['candidate_sha256'], row['input_profile'], ROOT)
                                decision_file = output_root / row['run_id'] / 'decision.json'
                                decision = json.loads(decision_file.read_text()) if decision_file.exists() else {'decision': 'diagnostics_unavailable'}
                            elif evaluate is cycle:
                                decision = bounded_call(evaluate, row['run_id'], output_root, baseline, inventory, runs_root,
                                                        candidate_path=path, input_profile=row['input_profile'])
                            else:
                                decision = evaluate(row['run_id'], output_root, baseline, inventory, runs_root,
                                                    candidate_path=path, input_profile=row['input_profile'])
                        except Exception as exc:
                            eval_error = exc
                            result_file = output_root / row['run_id'] / 'result.json'
                            if not result_file.exists():
                                text = str(exc).lower()
                                candidate_runtime = isinstance(exc, EvaluationTimeout) or any(token in text for token in ('candidate score', 'missing candidate', 'candidate key'))
                                row.update(status='FAILED' if candidate_runtime else 'PAUSED_SYSTEM_ERROR', error=str(exc), keep=False)
                                save()
                                if not candidate_runtime:
                                    raise RuntimeError(f'PAUSED_SYSTEM_ERROR: evaluator failed: {exc}') from exc
                                continue
                            integrity = any(k in str(exc).lower() for k in ('hash mismatch', 'source changed', 'cold cutoff', 'inventory', 'calendar', 'chronology', 'fixed evaluation inputs', 'different input profiles', 'contract mismatch'))
                            if integrity:
                                saved_result = json.loads(result_file.read_text())
                                row.update(ic=saved_result.get('ic'), hac_t=saved_result.get('hac_t'), n=saved_result.get('n'), ic_recorded=True, status='PAUSED_SYSTEM_ERROR', error=str(exc))
                                save()
                                raise RuntimeError(f'PAUSED_SYSTEM_ERROR: {exc}') from exc
                            decision = {'decision': 'diagnostics_unavailable', 'diagnostic_error': str(exc)}
                        result = (validate_result(output_root / row['run_id'], row['candidate_sha256'], row['input_profile'], ROOT)
                                  if evaluate is cycle else
                                  json.loads((output_root / row['run_id'] / 'result.json').read_text()))
                        if evaluate is cycle and row.get('score_preflight_path'):
                            validate_preflight_result(output_root / row['run_id'],
                                json.loads(Path(row['score_preflight_path']).read_text()))
                        row.update(status='RESULT_READY', stage='result_saved', ic_recorded=True, ic=result.get('ic'), hac_t=result.get('hac_t'), n=result.get('n'))
                        save()
                        keep = math.isfinite(result['ic']) and result['ic'] > 0
                        reason = ('positive signed IC retained independent of unrelated baseline' if keep else
                                  'nonpositive or uncomputable IC archived; not selected as a positive parent')
                        if row['mode'] == 'refine':
                            paired = compare(baseline, output_root / row['run_id'])
                            old = json.loads((baseline / 'result.json').read_text())
                            keep = keep and paired['n'] == result['n'] == old['n'] and paired['delta_ic'] > 1e-12
                            row['paired_to_parent'] = paired
                            reason = 'parent comparison improved' if keep else 'parent retained; trial remains in library'
                        row.update(status='COMPLETED', keep=keep, reason=reason,
                                   ic=result['ic'], hac_t=result['hac_t'], n=result['n'],
                                   stage='complete', yearly=result.get('yearly', {}), decision=decision.get('decision', 'diagnostics_unavailable'),
                                   nearest=decision.get('nearest'), novelty_diagnostic=decision.get('novelty_diagnostic'))
                        if eval_error:
                            row['diagnostics_unavailable'] = str(eval_error)
                        parent_key = (row['input_profile'], row['family'])
                        row['parent_replaced'] = False
                        if keep and (parent_key not in parents or result['ic'] > parents[parent_key]['ic']):
                            row['parent_replaced'] = row['mode'] == 'refine'
                            parents[(row['input_profile'], row['family'])] = {
                                **row, 'code_path': row['source_path'], 'parent_eligible': True}
                    except Exception as exc:
                        if row.get('status') in {'OUTCOME_OPENED', 'EVALUATING', 'RESULT_READY', 'PAUSED_SYSTEM_ERROR'}:
                            row.update(status='PAUSED_SYSTEM_ERROR', error=str(exc), keep=False)
                            save()
                            raise
                        row.update(status='FAILED', error=str(exc), keep=False)
                    save()
                    print(json.dumps(progress_event(row), ensure_ascii=False), flush=True)
                summary['completed_rounds'] = number
                save()
            summary['status'] = 'COMPLETED' if summary.get('completed_rounds', 0) >= rounds else 'STOPPED'
            if summary['status'] == 'COMPLETED' and not campaign_progress(summary, directory)['complete']:
                summary['status'] = 'PAUSED_SYSTEM_ERROR'
                raise RuntimeError('PAUSED_SYSTEM_ERROR: completed rounds disagree with saved evidence')
            summary.setdefault('stop_reason', 'requested rounds complete')
        except BaseException as exc:
            summary.setdefault('interruptions', []).append({'error_type': type(exc).__name__, 'error': str(exc)})
            summary['status'] = ('PAUSED_SYSTEM_ERROR' if summary.get('status') == 'PAUSED_SYSTEM_ERROR' or any(r.get('status') == 'PAUSED_SYSTEM_ERROR' for r in rows)
                                 else 'INTERRUPTED')
            save()
            raise
        save()
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign-id', required=True)
    parser.add_argument('--reopen-records', type=Path, help='reviewed, targeted family reopening records JSON')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--rounds', type=int, required=True)
    parser.add_argument('--candidates-per-round', type=int, default=4)
    parser.add_argument('--mode', choices=['open'], default='open')
    parser.add_argument('--profiles', default='all', help='all available approved profiles, or comma-separated subset')
    parser.add_argument('--model', default='gpt-6-luna')
    parser.add_argument('--reviewer', default='gpt-5.6-sol')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'runtime_outputs/etf_autoresearch_ic')
    parser.add_argument('--runs-root', type=Path, default=ROOT / 'runtime_outputs/etf_rotation_research/runs')
    parser.add_argument('--inventory', type=Path)
    args = parser.parse_args()
    inventory = args.inventory
    if inventory is None:
        pointer = json.loads((args.runs_root.parent / 'IC_INVENTORY_LATEST.json').read_text())
        inventory = Path(pointer['snapshot']) / 'all_factors.csv'
    catalog = describe_profiles(ROOT)
    profiles = ([name for name, item in catalog.items() if item['available'] and item.get('approved', True)]
                if args.profiles == 'all' else args.profiles.split(','))
    diagnostics = {profile: describe_feature_diagnostics(profile, ROOT) for profile in profiles}
    result = workflow(args.campaign_id, args.rounds, args.candidates_per_round,
                      profiles, args.output_root, inventory, args.runs_root,
                      args.model, args.reviewer, args.mode, resume=args.resume, diagnostics=diagnostics,
                      reopen_records=json.loads(args.reopen_records.read_text()) if args.reopen_records else None)
    fields = ('campaign_id', 'status', 'completed_rounds', 'evaluated_rounds', 'proposed_count',
              'evaluated_count', 'numeric_ic_count', 'positive_ic_count', 'failed_count',
              'rejected_count', 'empty_rounds', 'stop_reason')
    print(json.dumps({**{k: result.get(k) for k in fields},
        'summary_path': str(args.output_root / 'campaigns' / args.campaign_id / 'summary.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
