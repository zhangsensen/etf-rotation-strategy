import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/etf_autoresearch_diversity.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("etf_autoresearch_diversity", SCRIPT)
diversity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diversity)


def _spec(key="flow_shock", profile="fixed14", why_distinct="It uses turnover imbalance to represent demand pressure."):
    return {"family_key": key, "mechanism": "Liquidity demand pressure",
            "distinct_from": "Price trend responds to direction, this measures trading pressure.",
            "why_distinct": why_distinct,
            "input_profile": profile, "formula": "rolling_zscore(amount / close)", "direction": 1,
            "required_panels": ["amount", "close"], "nearest_existing_candidate": "trend_v1",
            "novelty_basis": "new_mechanism", "new_information": "Demand intensity beyond price trend.", "math_kernel": "custom",
            "difference_from_existing": "Measures turnover intensity rather than price slope."}


def test_plan_validation_canonicalizes_and_allows_short_plan():
    profiles = [{"name": "fixed14", "panel_names": ["amount", "close"]}, {"name": "liquid8", "panel_names": ["amount"]}]
    result = diversity.validate_plan([_spec("Flow-Shock", "Fixed14")], 3, profiles, [])
    assert result[0]["family_key"] == "flow_shock"
    assert result[0]["input_profile"] == "fixed14"


def test_plan_validation_rejects_alias_duplicates_forbidden_and_bad_profiles():
    for specs, profiles, forbidden in (
        ([_spec("price-trend"), _spec("price_trend")], ["fixed14"], []),
        ([_spec("price-trend")], ["fixed14"], ["price_trend"]),
        ([_spec(profile="other")], ["fixed14"], []),
        ([_spec(why_distinct="")], ["fixed14"], []),
    ):
        try:
            diversity.validate_plan(specs, 4, [{"name": p, "panel_names": ["amount", "close"]} for p in profiles], forbidden)
        except ValueError:
            continue
        raise AssertionError("invalid plan accepted")


def test_plan_families_uses_local_model_and_validates_output(tmp_path, monkeypatch):
    called = {}

    def fake_model(prompt, schema, directory, model, role):
        called.update(prompt=prompt, schema=schema, directory=directory, model=model, role=role)
        return {"families": [_spec()]}

    campaign = ModuleType("run_etf_autoresearch_campaign")
    campaign.model_json = fake_model
    monkeypatch.setitem(sys.modules, "run_etf_autoresearch_campaign", campaign)
    context = {"requested_count": 2, "allowed_profiles": [{"name": "fixed14", "panel_names": ["amount", "close"]}],
               "forbidden_family_keys": [], "historical_formal_definitions": []}
    plan = diversity.plan_families(context, tmp_path, "gpt-6-luna")
    assert len(plan) == 1
    assert called["model"] == "gpt-6-luna"
    assert "Do not pad" in called["prompt"]


def test_plan_families_allows_reclassification_of_known_family(tmp_path, monkeypatch):
    campaign = ModuleType("run_etf_autoresearch_campaign")
    campaign.model_json = lambda *args: {"families": [
        _spec("known-formal"), _spec("known-local"), _spec("new-mechanism")
    ]}
    monkeypatch.setitem(sys.modules, "run_etf_autoresearch_campaign", campaign)
    context = {"requested_count": 4, "allowed_profiles": [{"name": "fixed14", "panel_names": ["amount", "close"]}],
               "forbidden_family_keys": [],
               "historical_formal_definitions": [{"family": "Known Formal"}],
               "local_family_trial_counts": {"known_local": 2},
               "local_completed_candidates": [{"family": "known_local", "canonical_family": "completed_parent"}],
               "aliases": {"old_alias": "completed_parent"}}
    plan = diversity.plan_families(context, tmp_path, "gpt-6-luna")
    assert [item["family_key"] for item in plan] == ["known_formal", "known_local", "new_mechanism"]


def test_family_history_canonicalizes_aliases_and_ignores_failed_refinements(tmp_path):
    campaigns = tmp_path / "campaigns"
    campaigns.mkdir()
    rows = [
        {"round": 1, "status": "COMPLETED", "family": "Liquidity-Flow", "canonical_family": "flow-pressure",
         "review": {"approved": True},
         "mode": "explore", "keep": True, "ic": 0.02},
        {"round": 1, "status": "FAILED", "family": "bad-refine", "mode": "refine", "keep": False},
        {"status": "COMPLETED", "family": "flow_pressure", "canonical_family": "flow_pressure",
         "round": 1, "mode": "refine", "keep": False, "ic": 0.01},
        {"status": "COMPLETED", "family": "trend", "round": 1, "mode": "refine", "keep": False, "ic": 0.01},
    ]
    (campaigns / "batch" ).mkdir()
    (campaigns / "batch" / "summary.json").write_text(json.dumps({"completed_rounds": 1, "rounds": rows}))
    (campaigns / "reference_seed").mkdir()
    (campaigns / "reference_seed" / "summary.json").write_text(json.dumps({"rounds": [
        {"status": "COMPLETED", "family": "ignored"}]}))
    history = diversity.family_history(tmp_path)
    assert history["family_attempt_counts"] == {"flow_pressure": 2, "bad_refine": 1, "trend": 1}
    assert history["aliases"]["liquidity_flow"] == "flow_pressure"
    assert history["recent_round_families"] == ["flow_pressure", "bad_refine", "trend"]
    assert history["unsuccessful_refinements"] == {"flow_pressure": 1, "trend": 1}


def test_family_history_supports_legacy_rows_without_canonical_family(tmp_path):
    campaign = tmp_path / "campaigns" / "old"
    campaign.mkdir(parents=True)
    (campaign / "summary.json").write_text(json.dumps({"rounds": [
        {"status": "COMPLETED", "family": "mean-reversion", "mode": "explore"}]}))
    history = diversity.family_history(tmp_path)
    assert history["family_attempt_counts"] == {"mean_reversion": 1}
    assert history["aliases"]["mean_reversion"] == "mean_reversion"


def test_successful_local_parent_resets_refinement_streak(tmp_path):
    campaign = tmp_path / "campaigns" / "batch"
    campaign.mkdir(parents=True)
    rows = [
        {"round": 1, "status": "COMPLETED", "family": "f", "mode": "refine", "keep": False, "ic": -0.01},
        {"round": 2, "status": "COMPLETED", "family": "f", "mode": "explore", "keep": True, "ic": 0.02},
    ]
    (campaign / "summary.json").write_text(json.dumps({"completed_rounds": 2, "rounds": rows}))
    assert diversity.family_history(tmp_path)["unsuccessful_refinements"] == {}


def test_family_history_cooldown_uses_last_two_rounds_without_rejected_family_drift(tmp_path):
    campaign = tmp_path / "campaigns" / "multi"
    campaign.mkdir(parents=True)
    rows = [
        {"round": 1, "status": "FAILED", "family": "old foo"},
        {"round": 2, "status": "REJECTED", "family": "middle"},
        {"round": 3, "status": "FAILED", "family": "old_foo", "canonical_family": "new foo"},
    ]
    (campaign / "summary.json").write_text(json.dumps({"completed_rounds": 3, "rounds": rows}))
    history = diversity.family_history(tmp_path)
    assert history["recent_round_families"] == ["middle", "new_foo"]
    assert history["family_attempt_counts"] == {"old_foo": 1, "middle": 1, "new_foo": 1}
    assert history["aliases"]["old_foo"] == "old_foo"
    assert diversity.normalize_family("  old  foo ") == "old_foo"


def test_family_history_uses_planned_family_when_validation_failed_early(tmp_path):
    campaign = tmp_path / "campaigns" / "failed_before_metadata"
    campaign.mkdir(parents=True)
    row = {"round": 1, "status": "FAILED", "planned_family": "flow-shock",
           "error": "static validation failed"}
    (campaign / "summary.json").write_text(json.dumps({"completed_rounds": 1, "rounds": [row]}))
    history = diversity.family_history(tmp_path)
    assert history["family_attempt_counts"] == {"flow_shock": 1}
    assert history["recent_round_families"] == ["flow_shock"]


def test_engineering_failure_is_not_permanent_family_exclusion():
    context = {"local_family_trial_counts": {"broken": 1},
               "aliases": {"broken": "broken"}, "local_completed_candidates": []}
    assert "broken" not in diversity.historical_family_keys(context)


def test_planner_schema_constrains_profile_identifiers(tmp_path, monkeypatch):
    campaign = ModuleType("run_etf_autoresearch_campaign")
    def reply(prompt, schema, *args):
        families = schema['properties']['families']
        assert families['maxItems'] == 2
        assert families['items']['properties']['input_profile']['enum'] == ['daily', 'minute']
        assert 'formula' in families['items']['required']
        assert families['items']['properties']['direction']['enum'] == [-1, 1]
        assert families['items']['properties']['required_panels']['items']['enum'] == ['close', 'open']
        return {'families': []}
    campaign.model_json = reply
    monkeypatch.setitem(sys.modules, 'run_etf_autoresearch_campaign', campaign)
    assert diversity.plan_families({'requested_count': 2, 'allowed_profiles': {'daily': {'panel_names': ['close']}, 'minute': {'panel_names': ['open']}},
                                   'forbidden_family_keys': []}, tmp_path, 'gpt-6-luna') == []


def test_plan_validation_rejects_unknown_panels_and_outcome_formula():
    profiles = [{"name": "fixed14", "panel_names": ["amount", "close"]}]
    for item in (_spec() | {"required_panels": ["future_return"]},
                 _spec() | {"formula": "target / close"}):
        try:
            diversity.validate_plan([item], 1, profiles, [])
        except ValueError:
            continue
        raise AssertionError("invalid formula plan accepted")


def test_empty_completed_rounds_age_family_cooldown(tmp_path):
    campaign = tmp_path / 'campaigns' / 'empty_tail'
    campaign.mkdir(parents=True)
    (campaign / 'summary.json').write_text(json.dumps({'completed_rounds': 3,
        'rounds': [{'round': 1, 'status': 'REJECTED', 'family': 'old'}],
        'round_records': [{'round': 2, 'status': 'EMPTY'}, {'round': 3, 'status': 'EMPTY'}]}))
    history = diversity.family_history(tmp_path)
    assert history['recent_round_families'] == []
    assert history['family_attempt_counts'] == {'old': 1}


def test_history_stable_under_mtime_changes(tmp_path):
    import os
    paths = []
    for name, sequence, keep in [('z_old_20260101', 0, False), ('a_new_20260102', 0, True), ('new_event', 1, False)]:
        directory = tmp_path / 'campaigns' / name; directory.mkdir(parents=True)
        path = directory / 'summary.json'; paths.append(path)
        path.write_text(json.dumps({'event_sequence': sequence, 'completed_rounds': 1, 'rounds': [
            {'round': 1, 'run_id': name, 'status': 'COMPLETED', 'family': 'f', 'mode': 'refine', 'keep': keep, 'ic': .01}]}))
    before = diversity.family_history(tmp_path)
    for i, path in enumerate(paths): os.utime(path, (900-i*100, 900-i*100))
    assert diversity.family_history(tmp_path) == before
    assert before['unsuccessful_refinements'] == {'f': 1}
    assert before['next_event_sequence'] == 2


def test_profile_lanes_rotate_without_losing_global_history(tmp_path, monkeypatch):
    calls = []
    profiles = {p: {'panel_names': ['close', 'amount']} for p in ['p1', 'p2', 'p3', 'p4']}
    history = [{'family': 'old', 'definition_id': 'old_definition'}]
    def planner(ctx, directory, model):
        profile = ctx['source_focus']
        assert ctx['historical_formal_definitions'] == history
        assert ctx['forbidden_family_keys'] == ['old']
        assert list(ctx['allowed_profiles']) == [profile]
        assert list(ctx['feature_diagnostics']) == [profile]
        assert ctx['requested_count'] == 1 and model == 'gpt-6-luna'
        calls.append(profile)
        return [_spec(key='new_'+profile, profile=profile)]
    monkeypatch.setattr(diversity, 'plan_families', planner)
    ctx = {'requested_count': 3, 'round': 1, 'planning_attempt': 1, 'allowed_profiles': profiles,
           'historical_formal_definitions': history, 'forbidden_family_keys': ['old']}
    first = tmp_path / 'first'; first.mkdir()
    assert len(diversity.plan_profile_lanes(ctx, first, 'gpt-6-luna')) == 3
    assert set(calls) == {'p1', 'p2', 'p3'}
    calls.clear(); second = tmp_path / 'second'; second.mkdir()
    diversity.plan_profile_lanes(dict(ctx, round=1, profile_search_counts={'p1': 1, 'p2': 1, 'p3': 1}), second, 'gpt-6-luna')
    assert set(calls) == {'p4', 'p1', 'p2'}
    assert json.loads((first / 'planning_lanes.json').read_text())['policy'] == 'source_mechanism_v3'


def test_profile_lanes_preserve_empty_and_partial_failures(tmp_path, monkeypatch):
    def planner(ctx, *args):
        if ctx['source_focus'] == 'broken': raise RuntimeError('service unavailable')
        return []
    monkeypatch.setattr(diversity, 'plan_families', planner)
    ctx = {'requested_count': 2, 'allowed_profiles': {'empty': {}, 'broken': {}}}
    assert diversity.plan_profile_lanes(ctx, tmp_path, 'gpt-6-luna') == []
    assert len(json.loads((tmp_path / 'planning_lanes.json').read_text())['lanes']) == 2


def test_search_counts_persist_empty_requests_and_rotate_mechanism_focus(tmp_path, monkeypatch):
    path = tmp_path / 'campaigns/previous/planning_r01_attempt1'
    path.mkdir(parents=True)
    (path / 'planning_lanes.json').write_text(json.dumps({'lanes': [
        {'profile': 'daily', 'mechanism_focus': 'demand_supply', 'specs': []}]}))
    history = diversity.family_history(tmp_path)
    assert history['profile_search_counts'] == {'daily': 1}
    calls = []
    def planner(ctx, *_):
        calls.append((ctx['source_focus'], ctx['mechanism_focus']['key']))
        return []
    monkeypatch.setattr(diversity, 'plan_families', planner)
    directory = tmp_path / 'new'; directory.mkdir()
    diversity.plan_profile_lanes({**history, 'requested_count': 2,
        'allowed_profiles': {'daily': {}, 'share': {}}}, directory, 'gpt-6-luna')
    assert calls[0][0] == 'share'
    assert {focus for _, focus in calls} == {'price_discovery', 'liquidity_capacity'}


def test_early_family_classification_resolves_aliases_without_merging_sources(tmp_path):
    ctx = {'aliases': {'old_alias': 'old'}, 'historical_formal_definitions': [{'family': 'old'}],
           'forbidden_family_keys': ['paused']}
    accepted, rejected = diversity.classify_plans([
        _spec('old_alias'), _spec('paused'), _spec('new'), _spec('new', 'other'), _spec('different')], ctx)
    assert [s['family_key'] for s in accepted] == ['new', 'different']
    assert [r['reason_code'] for r in rejected] == [
        'OLD_FAMILY_REQUIRES_PARENT_PLAN', 'RESERVED_OR_PAUSED_FAMILY', 'SAME_PLAN_FAMILY']


def test_partial_fill_does_not_requery_same_source(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(diversity, 'plan_families', lambda ctx, *_: calls.append(ctx['source_focus']) or [])
    diversity.plan_profile_lanes({'requested_count': 2, 'allowed_profiles': {'a': {}, 'b': {}, 'c': {}},
        'profiles_already_requested': ['a', 'b']}, tmp_path, 'gpt-6-luna')
    assert calls == ['c']


def test_redundancy_memory_is_bounded_and_does_not_use_ic():
    rows = [{'run_id': str(i), 'candidate': 'v'+str(i), 'family': 'pressure', 'status': 'COMPLETED',
             'input_profile': 'share', 'search_focus': 'demand_supply', 'ic': ic,
             'nearest': {'candidate': 'old', 'n': 80, 'mean_abs_daily_rank_corr': .85}}
            for i, ic in enumerate([-.02, .1])]
    first = diversity.diversity_memory({'local_trial_definitions': rows})
    assert first['profile_penalties']['share'] == 1
    assert first['family_penalties']['pressure'] == 1
    rows[0]['ic'] = 99
    assert diversity.diversity_memory({'local_trial_definitions': rows}) == first
    assert diversity.diversity_memory({'local_trial_definitions': rows[:1]})['family_penalties']['pressure'] == 0
    rows[0]['nearest']['n'] = 20
    assert diversity.diversity_memory({'local_trial_definitions': rows})['profile_penalties']['share'] == 0


def test_declared_variant_cannot_evade_history_by_new_name():
    variant = dict(_spec('invented_new_name'), novelty_basis='bounded_variant')
    accepted, skipped = diversity.classify_plans([variant], {})
    assert not accepted
    assert skipped[0]['reason_code'] == 'DECLARED_VARIANT_REQUIRES_PARENT_PLAN'


def test_unknown_nearest_reference_is_not_a_valid_novelty_comparison():
    ctx = {'historical_formal_definitions': [{'candidate': 'real', 'family': 'old'}]}
    accepted, skipped = diversity.classify_plans([_spec()], ctx)
    assert not accepted and skipped[0]['reason_code'] == 'UNRESOLVED_HISTORICAL_REFERENCE'
    accepted, _ = diversity.classify_plans([dict(_spec(), nearest_existing_candidate='real')], ctx)
    assert len(accepted) == 1


def test_repeated_overlap_changes_source_priority_without_exclusion(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(diversity, 'plan_families', lambda ctx, *_: calls.append(ctx['source_focus']) or [])
    ctx = {'requested_count': 1, 'allowed_profiles': {'crowded': {}, 'fresh': {}},
           'profile_search_counts': {'crowded': 2, 'fresh': 2},
           'diversity_memory': {'profile_penalties': {'crowded': 2}}}
    diversity.plan_profile_lanes(ctx, tmp_path, 'gpt-6-luna')
    assert calls == ['fresh']
    calls.clear();ctx['profile_search_counts']['fresh'] = 5
    diversity.plan_profile_lanes(ctx, tmp_path, 'gpt-6-luna')
    assert calls == ['crowded']  # More search elsewhere eventually restores priority.


def test_supported_questions_do_not_invent_input_panels():
    daily = {'panel_names': ['open', 'high', 'low', 'close', 'volume', 'amount']}
    allowed = diversity.eligible_foci(daily)
    assert 'liquidity_recovery' in allowed and 'participation_concentration' in allowed
    assert not {'flow_absorption', 'premium_resolution', 'shock_recovery'} & set(allowed)
    assert 'flow_absorption' in diversity.eligible_foci({'panel_names': daily['panel_names'] + ['shares']})
    assert 'premium_resolution' in diversity.eligible_foci({'panel_names': daily['panel_names'] + ['premium']})
    assert 'shock_recovery' in diversity.eligible_foci({'panel_names': daily['panel_names'] + ['ext_gold_shock']})


def test_distinct_questions_despite_different_source_history(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(diversity, 'plan_families', lambda ctx, *_: calls.append(ctx) or [])
    # Every source locally favours demand_supply: old source-first scheduling
    # would send all three lanes to that same question.
    counts = {p: {k: 10 for k in diversity.MECHANISM_FOCI if k != 'demand_supply'}
              for p in ('a', 'b', 'c')}
    diversity.plan_profile_lanes({'requested_count': 3, 'allowed_profiles': {p: {} for p in counts},
        'profile_focus_counts': counts}, tmp_path, 'gpt-6-luna')
    assert len({c['mechanism_focus']['key'] for c in calls}) == 3
    assert all('future recovery endpoint' in c['search_task'] for c in calls)


def test_undersearched_supported_question_gets_actual_planning_slot(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(diversity, 'plan_families', lambda ctx, *_: calls.append(ctx) or [])
    counts = {k: 5 for k in diversity.MECHANISM_FOCI if k not in diversity.FOCUS_PANELS}
    diversity.plan_profile_lanes({'requested_count': 1, 'allowed_profiles': {'share': {
        'panel_names': ['close', 'amount', 'shares']}}, 'profile_focus_counts': {'share': counts}},
        tmp_path, 'gpt-6-luna')
    assert calls[0]['mechanism_focus']['key'] == 'flow_absorption'
    assert 'premium_resolution' not in calls[0]['eligible_search_questions']


def test_open_plan_schema_allows_same_family_and_paused_variants():
    plans=[dict(_spec('old'),novelty_basis='bounded_variant'),dict(_spec('old'),formula='another formula')]
    allowed={'fixed14':{'panel_names':plans[0]['required_panels']}}
    validated=diversity.validate_plan(plans,2,allowed,['old'],open_search=True)
    accepted,rejected=diversity.classify_plans(validated,{'mode':'open','forbidden_family_keys':['old'],
        'historical_formal_definitions':[{'family':'old','candidate':'another'}]})
    assert len(accepted)==2 and rejected==[]
