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


def test_plan_validation_rejects_unapproved_profiles_and_missing_definition():
    for specs, profiles, forbidden in (
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
    assert "OPEN search" in called["prompt"]


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


def test_open_plan_schema_allows_same_family_and_paused_variants():
    plans=[dict(_spec('old'),novelty_basis='bounded_variant'),dict(_spec('old'),formula='another formula')]
    allowed={'fixed14':{'panel_names':plans[0]['required_panels']}}
    validated=diversity.validate_plan(plans,2,allowed,['old'],open_search=True)
    assert len(validated) == 2
