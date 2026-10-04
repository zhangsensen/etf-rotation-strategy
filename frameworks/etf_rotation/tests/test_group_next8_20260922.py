from pathlib import Path
import importlib.util
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/research/run_group_next8_20260922.py'
spec = importlib.util.spec_from_file_location('group_next8', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_next8_plan_is_frozen_and_budgeted():
    cfg = yaml.safe_load((ROOT / 'configs/group_next8_20260922.yaml').read_text())
    ids = [f'{m}_{w}' for w in cfg['windows'] for m in cfg['mechanisms']]
    assert len(ids) == 8 and len(set(ids)) == 8
    assert cfg['prior_registered'] + cfg['new_definitions'] == 104
    assert cfg['entry_lag'] == 2 and cfg['horizon'] == 5 and cfg['top_k'] == 2
    assert cfg['evaluation_start'] == '2025-01-01'


def test_singleton_definitions_are_explicit_not_missing():
    idx = pd.date_range('2025-01-01', periods=6, freq='D')
    panels = {'close': pd.DataFrame({'one': [1., 2., 3., 4., 5., 6.]}, index=idx)}
    groups = {'singleton': {'members': ['one']}}
    out = mod.atoms(panels, groups, [5])
    assert out['breadth_5']['singleton'].iloc[:4].isna().all()
    # A singleton has an explicit neutral contribution-balance and entropy value
    assert out['contribution_balance_5']['singleton'].iloc[-1] == 0
    assert out['leader_entropy_5']['singleton'].iloc[-1] == 0
