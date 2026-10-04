"""Lossy prompt views for planning and proposing; source context stays immutable."""
from __future__ import annotations

from copy import deepcopy


def tabulate_history(result):
    """Remove repeated JSON keys in a private prompt view, preserving values."""
    for key in ('local_trial_definitions', 'local_completed_candidates'):
        rows = result.get(key, [])
        if not rows:
            continue
        columns = list(dict.fromkeys(field for row in rows for field in row))
        result[key + '_columns'] = columns
        result[key] = [[row.get(field) for field in columns] for row in rows]
    columns = ['candidate', 'definition_id', 'source_type', 'mechanism']
    result['historical_formal_definition_columns'] = columns
    for bucket in result.get('historical_formal_definitions', []):
        bucket['definitions'] = [[row.get(field) for field in columns]
                                 for row in bucket['definitions']]
    result['history_detail_note'] += (
        " Local history uses row arrays with explicit *_columns in matching order; "
        "null represents an absent/null field. Formal family buckets use definition arrays "
        "in historical_formal_definition_columns order. All exact identities, formulas, "
        "directions, required panels and recorded metrics are retained."
    )


def _compact_local_history(result):
    """Store each formula once; metrics and overlap refer to stable trial IDs."""
    if 'local_trial_definitions' in result:
        compact = []
        for row in result['local_trial_definitions']:
            item = {k: row[k] for k in ('run_id', 'candidate', 'family', 'canonical_family',
                    'status', 'input_profile', 'formula', 'direction', 'mechanism', 'required_panels',
                    'duplicate_of', 'reason_code') if k in row}
            # Formula and its signed direction are the exact dedup identity.
            # Mechanism prose is a retrieval hint, so cap only that repeated
            # descriptive field while retaining every historical identity.
            if isinstance(item.get('mechanism'), str):
                item['mechanism'] = item['mechanism'][:96]
            compact.append(item)
        result['local_trial_definitions'] = compact
    if 'local_completed_candidates' in result:
        result['local_completed_candidates'] = [
            {k: row[k] for k in ('run_id', 'candidate', 'family', 'ic', 'hac_t', 'n',
             'input_profile', 'parent_eligible') if k in row}
            for row in result['local_completed_candidates']]
    for bucket in result.get('diversity_memory', {}).get('family_evidence', {}).values():
        variants = bucket.get('variants', [])
        overlaps = bucket.get('overlap_observations', [])
        # Every local formula/run identity is already represented in
        # local_trial_definitions. Keep diversity counts and a small trace here
        # instead of repeating hundreds of those same identities in the prompt.
        bucket['variant_count'] = len(variants)
        bucket['variant_examples'] = [{k: row[k] for k in ('run_id', 'candidate', 'status') if k in row}
                                      for row in variants[-3:]]
        bucket['overlap_count'] = len(overlaps)
        bucket['overlap_exact_count'] = sum(bool(row.get('exact')) for row in overlaps)
        bucket['overlap_examples'] = [{
            'run_id': row.get('run_id'), 'exact': row.get('exact'),
            'nearest': {k: row.get('nearest', {}).get(k) for k in
                        ('candidate', 'run_id', 'mean_abs_daily_rank_corr')}}
            for row in overlaps[-3:]]
        bucket.pop('variants', None)
        bucket.pop('overlap_observations', None)


def compact_review_context(context):
    """Technical review needs formulas and timing, never historical outcome values."""
    result = compact_planning_context(context)
    for key in ('local_completed_candidates', 'recent_failures', 'diversity_memory'):
        result.pop(key, None)
    # Full definitions of the explicitly referenced factors accompany the index.
    plans = context.get('plans', context.get('slots', []))
    referenced = {p.get('nearest_existing_candidate') for p in plans}
    result['referenced_formal_definitions'] = [deepcopy(row) for row in
        context.get('historical_formal_definitions', []) if row.get('candidate') in referenced]
    return result


def _compact_definitions(rows):
    grouped = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        family = str(row.get("family") or row.get("canonical_family") or "(unknown)")
        item = grouped.setdefault(family, {"family": family, "definitions": []})
        definition = {
            "candidate": row.get("candidate"),
            "definition_id": row.get("definition_id"),
            "source_type": row.get("source_type"),
            "mechanism": str(row.get("description") or row.get("raw_formula") or "")[:500],
        }
        item["definitions"].append(definition)
    return list(grouped.values())


def _planner_profiles(profiles):
    result = deepcopy(profiles)
    if isinstance(result, dict):
        values = result.values()
    elif isinstance(result, list):
        values = result
    else:
        return result
    for profile in values:
        if isinstance(profile, dict):
            profile.pop("source_excerpt", None)
            contract = profile.get("review_contract")
            if isinstance(contract, dict):
                # Minute panels still share a generic prose description: their
                # actual equations live in this excerpt. Do not remove the only
                # source of semantics merely to shorten a planning prompt.
                generic = any('exact feature formulas' in str(panel.get('formula', ''))
                              for panel in contract.get('panels', {}).values() if isinstance(panel, dict))
                if not generic:
                    contract.pop("source_excerpt", None)
    return result


def compact_planning_context(context):
    """Keep every historical identity while reducing repeated definition detail."""
    result = deepcopy(context)
    rows = result.get("historical_formal_definitions", [])
    result["historical_formal_definitions"] = _compact_definitions(rows)
    result["allowed_profiles"] = _planner_profiles(result.get("allowed_profiles", {}))
    _compact_local_history(result)
    for diagnostic in result.get('feature_diagnostics', {}).values():
        for panel in diagnostic.get('panels', {}).values() if isinstance(diagnostic, dict) else []:
            availability = panel.pop('valid_days_by_etf', None)
            if isinstance(availability, dict) and availability:
                counts = {str(k): int(v) for k, v in availability.items()}
                values = set(counts.values())
                if len(values) == 1:
                    panel['valid_days_per_etf'] = next(iter(values))
                    panel['valid_etf_count'] = len(counts)
                else:
                    maximum = max(values)
                    panel['valid_days_min'] = min(values)
                    panel['valid_days_max'] = maximum
                    panel['etfs_below_max_coverage'] = {
                        ticker: days for ticker, days in counts.items() if days < maximum}
    result["history_detail_note"] = (
        "Compact retrieval aid: every historical family and definition_id is retained; "
        "mechanism text is truncated to 500 characters. Full contracts remain for review."
    )
    return result


def compact_proposal_context(context):
    """Retain all family/definition identities and expand only relevant definitions."""
    result = deepcopy(context)
    if result.get("assigned_family_plan"):
        # Implementation is already assigned; planning and review retain full history.
        for key in ("historical_formal_definitions", "local_completed_candidates",
                    "local_family_trial_counts", "recent_failures", "local_trial_definitions",
                    "diversity_memory"):
            result.pop(key, None)
        result["history_detail_note"] = (
            "Implement only the frozen assigned plan. Global novelty history stays in "
            "planning and review; do not use historical IC to change this formula."
        )
        return result
    rows = result.get("historical_formal_definitions", [])
    compact = _compact_definitions(rows)
    result["historical_formal_definitions"] = compact
    profile = str(result.get("input_profile") or "")
    plan = result.get("assigned_family_plan") or {}
    family = str(plan.get("family_key") or "")
    result["relevant_formal_definitions"] = [
        deepcopy(row) for row in rows if isinstance(row, dict) and
        (str(row.get("family") or row.get("canonical_family") or "") == family
         or (profile and str(row.get("source_type") or "") == profile))
    ]
    result["history_detail_note"] = (
        "Compact retrieval aid: all historical family keys and definition_ids are retained; "
        "relevant_formal_definitions expands the assigned family and matching source_type. "
        "Review still receives the full original evidence contract."
    )
    return result
