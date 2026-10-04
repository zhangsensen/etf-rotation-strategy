import importlib.util
from pathlib import Path
import unittest

MODULE = (Path(__file__).resolve().parents[1] /
          "scripts/research/etf_autoresearch_context.py")
SPEC = importlib.util.spec_from_file_location("etf_autoresearch_context", MODULE)
context_tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(context_tools)
compact_planning_context = context_tools.compact_planning_context
compact_proposal_context = context_tools.compact_proposal_context


class AutoresearchContextTests(unittest.TestCase):
    def setUp(self):
        self.context = {
            "historical_formal_definitions": [
                {"family": "f1", "definition_id": "d1", "source_type": "minute",
                 "description": "x" * 700, "raw_formula": "duplicate", "candidate": "c1"},
                {"family": "f1", "definition_id": "d2", "source_type": "daily",
                 "description": "second", "raw_formula": "second", "candidate": "c2"},
                {"family": "f2", "definition_id": "d3", "source_type": "us_vix",
                 "description": "third", "raw_formula": "third", "candidate": "c3"},
            ],
            "allowed_profiles": {"minute": {"panel_names": ["x"],
                "review_contract": {"panels": {"x": {"formula": "known"}},
                                    "source_excerpt": "large"}}},
            "input_profile": "minute",
            "assigned_family_plan": {"family_key": "f2"},
            "current_source": "parent code",
            "parent_contract": {"source_code": "parent code"},
            "local_completed_candidates": [{"ic": 0.2}],
            "feature_diagnostics": {"missing": ["minute_turnover"]},
            "repair_feedback": {"cause": "previous source had invalid shape", "attempts": 2},
        }

    def test_planning_keeps_all_ids_and_contract_semantics_without_excerpt(self):
        compact = compact_planning_context(self.context)
        definitions = compact["historical_formal_definitions"]
        self.assertEqual({row["family"] for row in definitions}, {"f1", "f2"})
        self.assertEqual({d["definition_id"] for row in definitions
                          for d in row["definitions"]}, {"d1", "d2", "d3"})
        self.assertLessEqual(len(definitions[0]["definitions"][0]["mechanism"]), 500)
        contract = compact["allowed_profiles"]["minute"]["review_contract"]
        self.assertNotIn("source_excerpt", contract)
        self.assertEqual(contract["panels"]["x"]["formula"], "known")
        self.assertIn("source_excerpt", self.context["allowed_profiles"]["minute"]["review_contract"])
        self.assertEqual(compact["feature_diagnostics"], self.context["feature_diagnostics"])
        self.assertEqual(compact["repair_feedback"], self.context["repair_feedback"])

    def test_assigned_implementation_keeps_contract_without_unrelated_history(self):
        compact = compact_proposal_context(self.context)
        self.assertEqual(compact["current_source"], "parent code")
        self.assertEqual(compact["parent_contract"]["source_code"], "parent code")
        self.assertNotIn("historical_formal_definitions", compact)
        self.assertNotIn("local_completed_candidates", compact)
        self.assertEqual(compact["assigned_family_plan"], self.context["assigned_family_plan"])
        self.assertEqual(compact["feature_diagnostics"], self.context["feature_diagnostics"])
        self.assertEqual(compact["repair_feedback"], self.context["repair_feedback"])
        self.assertEqual(len(self.context["historical_formal_definitions"]), 3)


if __name__ == "__main__":
    unittest.main()


def test_planner_retains_source_when_panel_prose_is_generic():
    context = {'allowed_profiles': {'minute': {'review_contract': {
        'source_excerpt': 'u_shape = (opening + closing) / total',
        'panels': {'minute_u_shape': {'formula': 'exact feature formulas are in implementation'}}}}}}
    view = compact_planning_context(context)
    assert view['allowed_profiles']['minute']['review_contract']['source_excerpt'] == 'u_shape = (opening + closing) / total'


def test_growing_history_is_deduplicated_without_losing_formulas_or_signed_evidence():
    import json
    from copy import deepcopy
    rows = [{'run_id': f'r{i}', 'candidate': f'c{i}', 'family': 'f',
             'formula': 'mean(known_returns.shift(1), 60)', 'direction': -1,
             'nearest': {'score_path': 'x' * 3000}} for i in range(300)]
    context = {'local_trial_definitions': rows,
               'local_completed_candidates': [{**r, 'ic': -.02, 'hac_t': -2., 'n': 287} for r in rows],
               'diversity_memory': {'family_evidence': {'f': {'variants': rows}}}}
    original = deepcopy(context)
    packed = compact_planning_context(context)
    assert context == original
    assert len(json.dumps(packed)) < len(json.dumps(context)) / 5
    assert [r['formula'] for r in packed['local_trial_definitions']] == [r['formula'] for r in rows]
    assert {r['candidate'] for r in packed['local_trial_definitions']} == {r['candidate'] for r in rows}
    assert [r['direction'] for r in packed['local_trial_definitions']] == [-1] * len(rows)
    assert all(r['ic'] == -.02 and r['hac_t'] == -2. for r in packed['local_completed_candidates'])


def test_planning_prompt_capacity_keeps_exact_definition_identity_through_120_more_candidates():
    import json
    from copy import deepcopy
    import sys
    sys.path.insert(0, str(MODULE.parent))
    from etf_autoresearch_diversity import build_planning_prompt, MAX_PLANNING_PROMPT_CHARS

    row = {'run_id': 'seed', 'candidate': 'seed_factor', 'family': 'flow',
           'formula': 'rolling_cov(close.pct_change(1), amount.diff(1), 20)',
           'direction': -1, 'mechanism': 'long descriptive mechanism ' * 12,
           'required_panels': ['close', 'amount'], 'input_profile': 'daily'}
    context = {
        'local_trial_definitions': [deepcopy(row) for _ in range(200)],
        'local_completed_candidates': [{**deepcopy(row), 'ic': -.02, 'hac_t': -2.1,
                                        'n': 287, 'yearly': {'2025': {'ic': -.03}}}
                                       for _ in range(200)],
        'historical_formal_definitions': [],
        'allowed_profiles': {'daily': {'available': True,
            'review_contract': {'signal_time': 'D close', 'entry': 'D+2 open',
                                'exit': 'D+7 open', 'panels': {
                                    'close': {'formula': 'close'},
                                    'amount': {'formula': 'daily amount'}}}}},
        'diversity_memory': {'family_evidence': {'flow': {
            'attempts': 200, 'variants': [deepcopy(row) for _ in range(200)],
            'overlap_observations': [{'run_id': f'r{i}', 'exact': i % 2 == 0,
                'nearest': {'candidate': f'c{i}', 'run_id': f'r{i}',
                            'mean_abs_daily_rank_corr': .8}} for i in range(200)]}}},
    }
    # Simulate the remaining 15 campaign rounds at the maximum width of eight.
    for i in range(120):
        trial = {**deepcopy(row), 'run_id': f'future_r{i // 8 + 36}_c{i % 8 + 1}',
                 'candidate': f'future_factor_{i}',
                 'formula': f'rolling_cov(close.pct_change(1), amount.diff(1), {20 + i})'}
        context['local_trial_definitions'].append(trial)
        context['local_completed_candidates'].append({**trial, 'ic': -.01 if i % 2 else .02,
            'hac_t': 1.8, 'n': 250, 'yearly': {'2026': {'ic': .01}}})

    original = deepcopy(context)
    prompt = build_planning_prompt(context)
    assert len(prompt) < MAX_PLANNING_PROMPT_CHARS
    # The prompt's final JSON object still holds every exact ID/formula/direction.
    payload = json.loads(prompt[prompt.rfind('\n{') + 1:])
    definitions = payload['local_trial_definitions']
    assert len(definitions) == len(original['local_trial_definitions'])
    assert [(r['run_id'], r['candidate'], r['formula'], r['direction']) for r in definitions] == [
        (r['run_id'], r['candidate'], r['formula'], r['direction'])
        for r in original['local_trial_definitions']]
    assert payload['allowed_profiles']['daily']['review_contract']['entry'] == 'D+2 open'
    assert payload['allowed_profiles']['daily']['review_contract']['exit'] == 'D+7 open'
    assert context == original


def test_planning_prompt_tables_preserve_50_round_history_and_evidence():
    import json
    import sys
    from copy import deepcopy
    sys.path.insert(0, str(MODULE.parent))
    from etf_autoresearch_diversity import build_planning_prompt, MAX_PLANNING_PROMPT_CHARS

    # A real-sized prior inventory plus 50 rounds of four long formulas.
    trials = [{'run_id': f'campaign_r{i // 4}_c{i % 4}', 'candidate': f'factor_{i}',
               'family': 'open_family', 'canonical_family': 'open_family',
               'input_profile': 'minute', 'formula': 'x' * (480 if i < 445 else 1077),
               'direction': -1 if i % 2 else 1, 'status': 'COMPLETED',
               'mechanism': 'retrieval description ' * 10, 'required_panels': ['x']}
              for i in range(645)]
    context = {'local_trial_definitions': trials,
               'local_completed_candidates': [{**r, 'ic': -.02, 'hac_t': -2.1, 'n': 287}
                                               for r in trials],
               'historical_formal_definitions': [
                   {'candidate': f'formal_{i}', 'definition_id': f'd{i}',
                    'family': f'f{i // 10}', 'source_type': 'daily', 'description': 'h' * 100}
                   for i in range(540)],
               'allowed_profiles': {'minute': {'review_contract': {
                   'entry': 'D+2 open', 'exit': 'D+7 open',
                   'panels': {'x': {'formula': 'exact feature formulas in source'}},
                   'source_excerpt': 'contract semantics ' * 3400}}},
               'feature_diagnostics': {'minute': {'interpretation': 'coverage evidence ' * 3000}}}
    original = deepcopy(context)
    prompt = build_planning_prompt(context)
    assert len(prompt) < MAX_PLANNING_PROMPT_CHARS
    payload = json.loads(prompt[prompt.rfind('\n{') + 1:])
    columns = payload['local_trial_definitions_columns']
    definitions = [dict(zip(columns, r)) for r in payload['local_trial_definitions']]
    assert [(r['run_id'], r['candidate'], r['formula'], r['direction'], r['required_panels'])
            for r in definitions] == [
                (r['run_id'], r['candidate'], r['formula'], r['direction'], r['required_panels'])
                for r in trials]
    metrics = [dict(zip(payload['local_completed_candidates_columns'], r))
               for r in payload['local_completed_candidates']]
    assert [(r['ic'], r['hac_t'], r['n']) for r in metrics] == [(-.02, -2.1, 287)] * 645
    formal_columns = payload.get('historical_formal_definition_columns')
    formal = [dict(zip(formal_columns, row)) if formal_columns else row
              for bucket in payload['historical_formal_definitions'] for row in bucket['definitions']]
    assert {r['definition_id'] for r in formal} == {f'd{i}' for i in range(540)}
    assert payload['allowed_profiles']['minute']['review_contract']['entry'] == 'D+2 open'
    assert context == original
