"""The entry's source-version accounting uses synthetic plans only."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/research/discover_etf_groups.py'
spec=importlib.util.spec_from_file_location('group_entry_for_tests',SCRIPT)
entry=importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


def plan(code_hash='a',direction=1):
    return {'config':{'windows':[5],'mechanisms':{'synthetic':{'direction':direction}},'budget_cap':2},
            'source_hashes':{'synthetic/etf_group_discovery.py':code_hash}}


def test_duplicate_replay_not_new_formula_and_failed_versions_stay_counted(tmp_path):
    for name,p,expected in [('r1',plan(),1),('r2',plan(),1),('r3',plan('b'),2)]:
        out=tmp_path/name
        out.mkdir()
        entry.reserve_plan(out,p)
        assert p['cumulative_registered_definitions']==expected
    out=tmp_path/'r4'
    out.mkdir()
    with pytest.raises(ValueError,match='budget exceeded'):
        entry.reserve_plan(out,plan('c'))
    assert not (out/'PLAN.json').exists()


def test_direction_and_parent_change_are_new_hypotheses():
    assert entry.definition_keys(plan())!=entry.definition_keys(plan(direction=-1))
    p=plan()
    p['config']['source_type']='self_state'
    p['source_hashes']={'synthetic/etf_group_sources.py':'x'}
    p['config']['mechanisms']['synthetic'].update(parent_run='parent',parent_candidate='first')
    other=deepcopy(p)
    other['config']['mechanisms']['synthetic']['parent_candidate']='second'
    assert entry.definition_keys(p)!=entry.definition_keys(other)


def test_reviewed_external_attempts_remain_in_new_batch_count(tmp_path):
    p = plan()
    p['config'].update(source_type='daily_mechanisms', budget_cap=9,
                       external_registered_definitions=8)
    p['source_hashes'] = {'synthetic/etf_group_daily_mechanisms.py': 'new'}
    out = tmp_path / 'r1'
    out.mkdir()
    entry.reserve_plan(out, p)
    assert p['entry_registered_definitions'] == 1
    assert p['external_registered_definitions'] == 8
    assert p['cumulative_registered_definitions'] == 9
    second = deepcopy(p)
    second['source_hashes'] = {'synthetic/etf_group_daily_mechanisms.py': 'changed'}
    out = tmp_path / 'r2'
    out.mkdir()
    with pytest.raises(ValueError, match='budget exceeded'):
        entry.reserve_plan(out, second)


def test_new_round_prior_is_checked_against_disk(tmp_path):
    first = plan()
    first['config']['budget_cap'] = 9
    first['config']['external_registered_definitions'] = 8
    old = tmp_path / 'old'
    old.mkdir()
    entry.reserve_plan(old, first)
    new = plan()
    new['config'].update(source_type='daily_rounds', prior_registered=9,
                         external_registered_definitions=8, budget_cap=10)
    new['source_hashes'] = {'synthetic/etf_group_daily_rounds.py': 'new'}
    out = tmp_path / 'new'
    out.mkdir()
    entry.reserve_plan(out, new)
    assert new['cumulative_registered_definitions'] == 10
    stale = tmp_path / 'stale'
    stale.mkdir()
    with pytest.raises(ValueError, match='persistent ledger'):
        entry.reserve_plan(stale, deepcopy(new))


def test_campaign_extension_checks_persistent_ledger_for_any_source(tmp_path):
    first = plan()
    first['config'].update(budget_cap=9, external_registered_definitions=8)
    old = tmp_path / 'old'
    old.mkdir()
    entry.reserve_plan(old, first)
    extension = plan(code_hash='minute-source')
    extension['config'].update(source_type='minute', campaign_extension=True,
                               prior_registered=9, external_registered_definitions=8,
                               budget_cap=10)
    extension['source_hashes'] = {'synthetic/etf_group_sources.py': 'minute-source'}
    out = tmp_path / 'extension'
    out.mkdir()
    entry.reserve_plan(out, extension)
    assert extension['cumulative_registered_definitions'] == 10


def test_candidate_availability_is_not_intersected_across_batch():
    import pandas as pd
    idx = pd.date_range('2025-01-01', periods=4)
    base = pd.Series(True, index=idx)
    dense = pd.DataFrame(1.0, index=idx, columns=['a', 'b'])
    sparse = dense.copy()
    sparse.iloc[1] = float('nan')
    assert entry.candidate_known_mask(base, dense).sum() == 4
    assert entry.candidate_known_mask(base, sparse).sum() == 3
    # The sparse candidate cannot change the dense candidate mask.
    assert entry.candidate_known_mask(base, dense).all()


def test_rejudge_same_feature_definitions_does_not_add_budget(tmp_path):
    parent_plan = plan()
    parent_plan['config'].update(source_type='daily_outcome', campaign_extension=True,
                                 prior_registered=8, external_registered_definitions=8,
                                 budget_cap=9)
    parent_plan['source_hashes'] = {'synthetic/etf_group_daily_outcome.py': 'feature'}
    parent = tmp_path / 'parent'
    parent.mkdir()
    entry.reserve_plan(parent, parent_plan)
    rejudge = deepcopy(parent_plan)
    rejudge['config'].update(prior_registered=9, budget_cap=9, rejudge_of='parent')
    rejudge['source_hashes'] = {'synthetic/etf_group_daily_outcome.py': 'repaired-judge'}
    out = tmp_path / 'rejudge'
    out.mkdir()
    entry.reserve_plan(out, rejudge)
    assert rejudge['cumulative_registered_definitions'] == 9
    subsequent = plan(code_hash='next-feature')
    subsequent['config'].update(source_type='daily_rounds', prior_registered=9,
                                external_registered_definitions=8, budget_cap=10)
    subsequent['source_hashes'] = {'synthetic/etf_group_daily_rounds.py': 'next-feature'}
    later = tmp_path / 'later'
    later.mkdir()
    entry.reserve_plan(later, subsequent)
    assert subsequent['cumulative_registered_definitions'] == 10


def test_rejudge_cannot_change_semantic_definition(tmp_path):
    parent_plan = plan()
    parent_plan['config'].update(source_type='daily_outcome', campaign_extension=True,
                                 prior_registered=8, external_registered_definitions=8,
                                 budget_cap=9)
    parent_plan['source_hashes'] = {'synthetic/etf_group_daily_outcome.py': 'feature'}
    parent = tmp_path / 'parent'
    parent.mkdir()
    entry.reserve_plan(parent, parent_plan)
    rejudge = deepcopy(parent_plan)
    rejudge['config'].update(prior_registered=9, budget_cap=9, rejudge_of='parent')
    rejudge['config']['mechanisms']['synthetic']['direction'] = -1
    rejudge['source_hashes'] = {'synthetic/etf_group_daily_outcome.py': 'repaired-judge'}
    out = tmp_path / 'rejudge'
    out.mkdir()
    with pytest.raises(ValueError, match='definitions differ'):
        entry.reserve_plan(out, rejudge)


def test_unchanged_hashes_passes_when_nothing_changed(tmp_path):
    a = tmp_path / 'a.txt'
    a.write_text('alpha')
    b = tmp_path / 'b.txt'
    b.write_text('beta')
    expected = {str(a): entry.sha(a), str(b): entry.sha(b)}
    assert entry.unchanged_hashes([a, b], expected) is True


def test_unchanged_hashes_fails_when_a_hashed_file_actually_changed(tmp_path):
    a = tmp_path / 'a.txt'
    a.write_text('alpha')
    expected = {str(a): entry.sha(a)}
    a.write_text('alpha-mutated')
    assert entry.unchanged_hashes([a], expected) is False


def test_macro_inputs_end_of_run_integrity_check_covers_macro_files(tmp_path):
    """Regression guard for the round 11 macro_inputs bug (master, 2026-
    09-24): `inputs` (the value later checked against) was built from
    `files` PLUS `macro_files`, but the end-of-run re-hash only ever
    covered `files` -- guaranteed to fail every single time macro_inputs
    is true, regardless of whether anything actually changed (5 real runs
    all produced byte-identical IC numbers yet all failed this check).
    Directly reproduces that exact scenario against `unchanged_hashes`,
    the extracted function both real integrity checks now call: building
    `inputs` the way discover_etf_groups.py's main() does (files, THEN
    macro_files merged in) must pass when checked against the FULL
    combined path set, and must have FAILED the old (files-only) check --
    both assertions kept side by side so this test would have caught the
    original bug had it existed before the bug was introduced."""
    price_file = tmp_path / '510300.SH.parquet'
    price_file.write_bytes(b'fake-price-bytes')
    macro_file = tmp_path / 'USDCNH.parquet'
    macro_file.write_bytes(b'fake-macro-bytes')

    files = [price_file]
    macro_files = [macro_file]
    inputs = {str(f): entry.sha(f) for f in files}
    inputs.update({str(f): entry.sha(f) for f in macro_files})

    # The fix: check against the combined set.
    assert entry.unchanged_hashes([*files, *macro_files], inputs) is True
    # The original bug: checking against `files` alone can never match
    # `inputs`, which always has the extra macro_files keys once macro_
    # inputs is true -- not because anything changed, purely a key-set
    # mismatch. Confirms this would have failed identically to the 5 real
    # runs' "inputs changed during run" RuntimeError.
    assert entry.unchanged_hashes(files, inputs) is False
